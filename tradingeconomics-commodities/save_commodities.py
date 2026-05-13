#!/usr/bin/env python3
"""
Fetch commodity rows from https://tradingeconomics.com/commodities and append to
CSV and/or Google Cloud Firestore.

Targets (default *auto*): Firestore if credentials / FIRESTORE_ENABLED, else CSV.

  export GOOGLE_APPLICATION_CREDENTIALS=/path/to/serviceAccount.json
  python save_commodities.py

  # Or Application Default Credentials (e.g. GCE / Cloud Run):
  export FIRESTORE_ENABLED=1
  python save_commodities.py

Cron / launchd (hourly):
  0 * * * * cd /path/to/tradingeconomics-commodities && .venv/bin/python save_commodities.py

Daemon:
  python save_commodities.py --daemon --interval-hours 1

Firestore: documents in collection `te_commodity_quotes` (override with FIRESTORE_COLLECTION).
Composite index hints: firestore.indexes.json (Firebase CLI).

Note: Automated scraping may conflict with Trading Economics terms of use.
"""

from __future__ import annotations

import argparse
import csv
import os
import sys
import time
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

import requests
from bs4 import BeautifulSoup

try:
    import firebase_admin
    from firebase_admin import credentials, firestore
except ImportError:
    firebase_admin = None  # type: ignore[misc, assignment]
    credentials = None  # type: ignore[misc, assignment]
    firestore = None  # type: ignore[misc, assignment]

URL = "https://tradingeconomics.com/commodities"
DEFAULT_OUT = Path(__file__).resolve().parent / "data" / "commodities_hourly.csv"
DEFAULT_COLLECTION = "te_commodity_quotes"
DEFAULT_DATABASE = "kosmes"
USER_AGENT = (
    "Mozilla/5.0 (compatible; TECommoditySnapshot/1.0; +https://example.local)"
)

KNOWN_CATEGORIES = frozenset(
    {
        "Energy",
        "Metals",
        "Agricultural",
        "Industrial",
        "Livestock",
        "Index",
        "Electricity",
    }
)


def parse_number(text: str) -> str:
    """Normalize numeric cell for CSV; empty if not parseable."""
    t = text.strip().replace(",", "").replace("%", "")
    if not t or t == "—" or t == "-":
        return ""
    return t


def to_decimal(s: str) -> Decimal | None:
    if not s or not str(s).strip():
        return None
    try:
        return Decimal(str(s).strip())
    except InvalidOperation:
        return None


def to_float(s: str | None) -> float | None:
    d = to_decimal(s or "")
    return float(d) if d is not None else None


def _parse_data_row(tr: Any) -> dict[str, str] | None:
    symbol = (tr.get("data-symbol") or "").strip()
    first = tr.find("td", class_="datatable-item-first")
    if not first:
        return None
    link = first.find("a", href=True)
    href = (link.get("href") or "").strip() if link else ""
    slug = href.rstrip("/").split("/")[-1] if href else ""
    b = first.find("b")
    name = b.get_text(strip=True) if b else ""
    div = first.find("div")
    unit = div.get_text(strip=True) if div else ""

    tds = tr.find_all("td")
    if len(tds) < 9:
        return None

    price = parse_number(tds[1].get_text())
    day_td = tds[2]
    day_abs = ""
    if day_td.get("data-value") is not None:
        day_abs = parse_number(str(day_td.get("data-value")))
    if not day_abs:
        day_abs = parse_number(day_td.get_text())
    pct_td = tds[3]
    pct = ""
    if pct_td.get("data-value") is not None:
        pct = str(pct_td.get("data-value")).strip()
    if not pct:
        pct = parse_number(pct_td.get_text())

    weekly = parse_number(tds[4].get_text())
    monthly = parse_number(tds[5].get_text())
    ytd = parse_number(tds[6].get_text())
    yoy = parse_number(tds[7].get_text())
    te_date = tds[8].get_text(strip=True)

    return {
        "symbol": symbol,
        "slug": slug,
        "name": name,
        "unit": unit,
        "price": price,
        "day_change_abs": day_abs,
        "pct_change_day": pct,
        "pct_weekly": weekly,
        "pct_monthly": monthly,
        "pct_ytd": ytd,
        "pct_yoy": yoy,
        "te_date": te_date,
    }


def fetch_rows(session: requests.Session) -> list[dict[str, str]]:
    r = session.get(URL, timeout=60)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    out: list[dict[str, str]] = []
    for table in soup.find_all("table"):
        rows = table.find_all("tr")
        if not any(tr.get("data-symbol") for tr in rows):
            continue
        cat: str | None = None
        for tr in rows:
            if tr.get("data-symbol"):
                row = _parse_data_row(tr)
                if row:
                    row["category"] = cat or ""
                    out.append(row)
            else:
                ths = tr.find_all("th")
                if ths:
                    t0 = ths[0].get_text(strip=True)
                    if t0 in KNOWN_CATEGORIES:
                        cat = t0
                tds = tr.find_all("td", colspan=True)
                if len(tds) == 1:
                    t = tds[0].get_text(strip=True)
                    if t in KNOWN_CATEGORIES:
                        cat = t
    return out


def append_csv(path: Path, fetched_at_iso: str, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.stat().st_size > 0:
        with path.open("r", encoding="utf-8", newline="") as f:
            r = csv.reader(f)
            header = next(r, None)
        if header is not None and "category" not in header:
            print(
                "Existing CSV was created without a 'category' column. "
                "Use a new --out path or archive/remove the old file.",
                file=sys.stderr,
            )
            raise SystemExit(3)
    new_file = not path.exists() or path.stat().st_size == 0
    fieldnames = [
        "fetched_at_utc",
        "category",
        "symbol",
        "slug",
        "name",
        "unit",
        "price",
        "day_change_abs",
        "pct_change_day",
        "pct_weekly",
        "pct_monthly",
        "pct_ytd",
        "pct_yoy",
        "te_date",
    ]
    with path.open("a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        if new_file:
            w.writeheader()
        for row in rows:
            w.writerow({"fetched_at_utc": fetched_at_iso, **row})


def firestore_should_auto() -> bool:
    flag = os.environ.get("FIRESTORE_ENABLED", "").strip().lower()
    if flag in ("1", "true", "yes", "on"):
        return True
    cred = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", "").strip()
    if cred and Path(cred).expanduser().is_file():
        return True
    return False


def firestore_explicit_ok() -> bool:
    """Explicit --target firestore: need cred file or FIRESTORE_ENABLED for ADC."""
    if firestore_should_auto():
        return True
    return os.environ.get("FIRESTORE_ENABLED", "").strip().lower() in ("1", "true", "yes", "on")


def get_firestore_client(database_id: str | None = None) -> Any:
    if firebase_admin is None or firestore is None:
        raise RuntimeError("firebase-admin is not installed. pip install -r requirements.txt")
    if not firebase_admin._apps:
        cred_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", "").strip()
        if cred_path and Path(cred_path).expanduser().is_file():
            firebase_admin.initialize_app(
                credentials.Certificate(str(Path(cred_path).expanduser()))
            )
        else:
            firebase_admin.initialize_app()
    db_id = database_id or os.environ.get("FIRESTORE_DATABASE_ID", DEFAULT_DATABASE) or None
    return firestore.client(database_id=db_id)


def row_to_firestore_doc(fetched_at: datetime, row: dict[str, str]) -> dict[str, Any]:
    return {
        "fetched_at": fetched_at,
        "category": row.get("category") or None,
        "symbol": row["symbol"],
        "slug": row.get("slug") or None,
        "name": row.get("name") or None,
        "unit": row.get("unit") or None,
        "price": to_float(row.get("price")),
        "day_change_abs": to_float(row.get("day_change_abs")),
        "pct_change_day": to_float(row.get("pct_change_day")),
        "pct_weekly": to_float(row.get("pct_weekly")),
        "pct_monthly": to_float(row.get("pct_monthly")),
        "pct_ytd": to_float(row.get("pct_ytd")),
        "pct_yoy": to_float(row.get("pct_yoy")),
        "te_date": row.get("te_date") or None,
    }


def insert_firestore(
    db: Any,
    collection: str,
    fetched_at: datetime,
    rows: list[dict[str, str]],
) -> None:
    col = db.collection(collection)
    batch = db.batch()
    n = 0
    for row in rows:
        ref = col.document()
        batch.set(ref, row_to_firestore_doc(fetched_at, row))
        n += 1
        if n >= 450:
            batch.commit()
            batch = db.batch()
            n = 0
    if n:
        batch.commit()


def resolve_target(choice: str, save_csv_env: bool) -> str:
    if choice != "auto":
        return choice
    if firestore_should_auto():
        return "both" if save_csv_env else "firestore"
    return "csv"


def run_once(
    out: Path,
    session: requests.Session,
    *,
    target: str,
    collection: str,
    database_id: str | None = None,
) -> int:
    fetched_at = datetime.now(timezone.utc)
    fetched_at_iso = fetched_at.strftime("%Y-%m-%dT%H:%M:%SZ")
    rows = fetch_rows(session)
    if not rows:
        print("No commodity rows parsed; page structure may have changed.", file=sys.stderr)
        return 2

    if target in ("csv", "both"):
        append_csv(out, fetched_at_iso, rows)
        print(f"CSV: appended {len(rows)} rows → {out} ({fetched_at_iso})")

    if target in ("firestore", "both"):
        try:
            db = get_firestore_client(database_id=database_id)
        except Exception as e:
            print(f"Firestore init error: {e}", file=sys.stderr)
            return 1
        try:
            insert_firestore(db, collection, fetched_at, rows)
        except Exception as e:
            print(f"Firestore write error: {e}", file=sys.stderr)
            return 1
        print(f"Firestore: wrote {len(rows)} docs to {collection!r} at {fetched_at_iso}")

    return 0


def main() -> int:
    p = argparse.ArgumentParser(
        description="Save TradingEconomics commodities to CSV and/or Firestore."
    )
    p.add_argument(
        "--out",
        type=Path,
        default=DEFAULT_OUT,
        help=f"CSV path when target includes csv (default: {DEFAULT_OUT})",
    )
    p.add_argument(
        "--collection",
        default=os.environ.get("FIRESTORE_COLLECTION", DEFAULT_COLLECTION),
        help=f"Firestore collection (default: env FIRESTORE_COLLECTION or {DEFAULT_COLLECTION})",
    )
    p.add_argument(
        "--database",
        default=os.environ.get("FIRESTORE_DATABASE_ID", DEFAULT_DATABASE),
        help=f"Firestore database ID (default: env FIRESTORE_DATABASE_ID or {DEFAULT_DATABASE})",
    )
    p.add_argument(
        "--target",
        choices=("auto", "csv", "firestore", "both"),
        default="auto",
        help="auto: firestore if credentials file or FIRESTORE_ENABLED; else csv",
    )
    p.add_argument(
        "--daemon",
        action="store_true",
        help="Run forever, sleeping --interval-hours between successful runs.",
    )
    p.add_argument(
        "--interval-hours",
        type=float,
        default=1.0,
        help="Hours between runs when --daemon (default: 1).",
    )
    args = p.parse_args()

    save_csv_env = os.environ.get("SAVE_CSV", "").strip() in ("1", "true", "yes")
    target = resolve_target(args.target, save_csv_env)

    if target in ("firestore", "both"):
        if firebase_admin is None:
            print("firebase-admin is not installed. pip install -r requirements.txt", file=sys.stderr)
            return 1
        if args.target != "auto" and not firestore_explicit_ok():
            print(
                "Firestore requires GOOGLE_APPLICATION_CREDENTIALS pointing to a JSON key file, "
                "or FIRESTORE_ENABLED=1 with Application Default Credentials (e.g. Cloud Run).",
                file=sys.stderr,
            )
            return 1
        if args.target == "auto" and not firestore_should_auto():
            return 1

    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT, "Accept-Language": "en-US,en;q=0.9"})

    if not args.daemon:
        try:
            return run_once(
                args.out,
                session,
                target=target,
                collection=args.collection,
                database_id=args.database,
            )
        except requests.RequestException as e:
            print(f"HTTP error: {e}", file=sys.stderr)
            return 1
        except SystemExit as e:
            return int(e.code) if isinstance(e.code, int) else 1

    while True:
        try:
            run_once(
                args.out,
                session,
                target=target,
                collection=args.collection,
                database_id=args.database,
            )
        except SystemExit:
            raise
        except requests.RequestException as e:
            print(f"HTTP error: {e}", file=sys.stderr)
        delay = max(60.0, float(args.interval_hours) * 3600.0)
        time.sleep(delay)


if __name__ == "__main__":
    raise SystemExit(main())
