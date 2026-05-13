import {
  Timestamp,
  collection,
  getDocs,
  orderBy,
  query,
  where,
} from "firebase/firestore";
import { db } from "./firebase";
import type { RawRow } from "./parseCsv";

const COLLECTION = "te_commodity_quotes";

export async function fetchFromFirestore(hours = 48): Promise<RawRow[]> {
  const since = new Date(Date.now() - hours * 60 * 60 * 1000);
  const q = query(
    collection(db, COLLECTION),
    where("fetched_at", ">=", Timestamp.fromDate(since)),
    orderBy("fetched_at", "asc"),
  );

  const snap = await getDocs(q);
  return snap.docs.map((doc) => {
    const d = doc.data();
    const ts = d.fetched_at as Timestamp;
    const fetched_at_utc = ts.toDate().toISOString().slice(0, 19) + "Z";
    return {
      fetched_at_utc,
      category: String(d.category ?? ""),
      symbol: String(d.symbol ?? ""),
      slug: String(d.slug ?? ""),
      name: String(d.name ?? ""),
      unit: String(d.unit ?? ""),
      price: String(d.price ?? ""),
      day_change_abs: String(d.day_change_abs ?? ""),
      pct_change_day: String(d.pct_change_day ?? ""),
      pct_weekly: String(d.pct_weekly ?? ""),
      pct_monthly: String(d.pct_monthly ?? ""),
      pct_ytd: String(d.pct_ytd ?? ""),
      pct_yoy: String(d.pct_yoy ?? ""),
      te_date: String(d.te_date ?? ""),
    } satisfies RawRow;
  });
}
