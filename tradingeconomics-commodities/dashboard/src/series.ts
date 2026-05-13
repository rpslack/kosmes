import type { RawRow } from "./parseCsv";

export type Point = {
  t: string;
  price: number;
  pctDay: number | null;
};

export type Series = {
  symbol: string;
  slug: string;
  name: string;
  unit: string;
  category: string;
  points: Point[];
};

function num(s: string | undefined): number | null {
  if (s == null || s === "") return null;
  const n = Number(String(s).replace(/,/g, ""));
  return Number.isFinite(n) ? n : null;
}

export function buildSeries(rows: RawRow[]): Series[] {
  type Acc = {
    slug: string;
    name: string;
    unit: string;
    category: string;
    points: Map<string, Point>;
  };
  const bySymbol = new Map<string, Acc>();

  for (const r of rows) {
    const symbol = (r.symbol ?? "").trim();
    if (!symbol) continue;
    const t = (r.fetched_at_utc ?? "").trim();
    if (!t) continue;
    const price = num(r.price);
    if (price == null) continue;

    let acc = bySymbol.get(symbol);
    if (!acc) {
      acc = {
        slug: (r.slug ?? "").trim(),
        name: (r.name ?? symbol).trim() || symbol,
        unit: (r.unit ?? "").trim(),
        category: (r.category ?? "").trim(),
        points: new Map(),
      };
      bySymbol.set(symbol, acc);
    }
    if (!acc.slug && r.slug) acc.slug = (r.slug ?? "").trim();
    if (!acc.unit && r.unit) acc.unit = (r.unit ?? "").trim();
    if (!acc.category && r.category) acc.category = (r.category ?? "").trim();
    if (acc.name === symbol && r.name) acc.name = (r.name ?? "").trim() || acc.name;

    const pct = num(r.pct_change_day);
    acc.points.set(t, { t, price, pctDay: pct });
  }

  const out: Series[] = [];
  for (const [symbol, acc] of bySymbol) {
    const points = Array.from(acc.points.values()).sort((a, b) => a.t.localeCompare(b.t));
    if (points.length === 0) continue;
    out.push({
      symbol,
      slug: acc.slug,
      name: acc.name,
      unit: acc.unit,
      category: acc.category || "—",
      points,
    });
  }
  out.sort((a, b) => a.name.localeCompare(b.name));
  return out;
}
