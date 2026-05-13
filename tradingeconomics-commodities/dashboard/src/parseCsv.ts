import Papa from "papaparse";

export type RawRow = Record<string, string | undefined>;

export function parseCommodityCsv(text: string): RawRow[] {
  const res = Papa.parse<RawRow>(text, {
    header: true,
    skipEmptyLines: true,
    transformHeader: (h) => h.trim(),
  });
  if (res.errors.length) {
    console.warn("CSV parse warnings:", res.errors);
  }
  return (res.data ?? []).filter((r) => (r.symbol ?? "").trim() && (r.fetched_at_utc ?? "").trim());
}
