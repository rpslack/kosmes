import { useEffect, useMemo, useState } from "react";
import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import "./App.css";
import { fetchFromFirestore } from "./fetchFirestore";
import type { RawRow } from "./parseCsv";
import { buildSeries, type Series } from "./series";

function formatTick(iso: string): string {
  if (iso.length >= 16) return iso.slice(5, 16).replace("T", " ");
  return iso;
}

function ChartCard({ s }: { s: Series }) {
  const last = s.points[s.points.length - 1];
  const first = s.points[0];
  const delta =
    first && last && first.price !== 0 ? ((last.price - first.price) / first.price) * 100 : null;

  return (
    <article className="card">
      <div className="card-head">
        <div style={{ minWidth: 0 }}>
          <h2 className="card-title" title={`${s.name} (${s.symbol})`}>
            {s.name}
          </h2>
          {s.category !== "—" ? <span className="badge">{s.category}</span> : null}
        </div>
        <div className="card-meta">
          {s.unit ? `${s.unit} · ` : null}
          {s.symbol}
        </div>
      </div>
      <div className="chart-wrap">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={s.points} margin={{ top: 6, right: 8, left: 0, bottom: 0 }}>
            <CartesianGrid stroke="#2a3142" strokeDasharray="3 3" />
            <XAxis
              dataKey="t"
              tick={{ fill: "#8b95a8", fontSize: 10 }}
              tickFormatter={formatTick}
              interval="preserveStartEnd"
              minTickGap={24}
            />
            <YAxis
              domain={["auto", "auto"]}
              tick={{ fill: "#8b95a8", fontSize: 10 }}
              width={44}
              tickFormatter={(v) => (Math.abs(v) >= 1000 ? `${(v / 1000).toFixed(1)}k` : String(v))}
            />
            <Tooltip
              contentStyle={{
                background: "#171c27",
                border: "1px solid #2a3142",
                borderRadius: 8,
                fontSize: 12,
              }}
              labelFormatter={formatTick}
              formatter={(value: number, name: string) => {
                if (name === "price") return [value.toLocaleString(undefined, { maximumFractionDigits: 4 }), "가격"];
                return [value, name];
              }}
            />
            <Line type="monotone" dataKey="price" stroke="#5b8def" strokeWidth={2} dot={false} name="price" />
          </LineChart>
        </ResponsiveContainer>
      </div>
      <div className="card-meta" style={{ marginTop: "0.35rem" }}>
        구간: {s.points.length}개 시점
        {delta != null && Number.isFinite(delta) ? (
          <>
            {" · "}
            <span style={{ color: delta >= 0 ? "var(--positive)" : "var(--negative)" }}>
              {delta >= 0 ? "+" : ""}
              {delta.toFixed(2)}%
            </span>
          </>
        ) : null}
        {last ? (
          <>
            {" · "}
            최신 {last.price.toLocaleString(undefined, { maximumFractionDigits: 4 })}
          </>
        ) : null}
      </div>
    </article>
  );
}

export default function App() {
  const [rows, setRows] = useState<RawRow[] | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [q, setQ] = useState("");
  const [cat, setCat] = useState<string>("all");

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const data = await fetchFromFirestore(48);
        if (cancelled) return;
        if (data.length === 0) {
          setErr("Firestore에 데이터가 없습니다. save_commodities.py 를 먼저 실행해 주세요.");
          return;
        }
        setRows(data);
        setErr(null);
      } catch (e) {
        if (!cancelled) {
          const msg = e instanceof Error ? e.message : String(e);
          if (msg.includes("Missing or insufficient permissions")) {
            setErr("Firestore 읽기 권한이 없습니다. Firebase 콘솔에서 보안 규칙을 확인해 주세요.");
          } else {
            setErr(msg);
          }
        }
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  const series = useMemo(() => (rows ? buildSeries(rows) : []), [rows]);

  const categories = useMemo(() => {
    const s = new Set<string>();
    for (const x of series) {
      if (x.category && x.category !== "—") s.add(x.category);
    }
    return Array.from(s).sort();
  }, [series]);

  const filtered = useMemo(() => {
    const qq = q.trim().toLowerCase();
    return series.filter((s) => {
      if (cat !== "all" && s.category !== cat) return false;
      if (!qq) return true;
      return (
        s.name.toLowerCase().includes(qq) ||
        s.symbol.toLowerCase().includes(qq) ||
        s.slug.toLowerCase().includes(qq)
      );
    });
  }, [series, q, cat]);

  const maxPoints = useMemo(
    () => series.reduce((m, s) => Math.max(m, s.points.length), 0),
    [series],
  );

  return (
    <div className="shell">
      <header className="top">
        <div>
          <h1>원자재 시세 대시보드</h1>
          <p className="sub">
            Firestore · 최근 48시간 · 1시간 스냅샷 누적
          </p>
        </div>
        <div className="controls">
          <label>
            검색
            <input
              type="search"
              placeholder="이름, 심볼, slug…"
              value={q}
              onChange={(e) => setQ(e.target.value)}
              autoComplete="off"
            />
          </label>
          <label>
            구분
            <select value={cat} onChange={(e) => setCat(e.target.value)}>
              <option value="all">전체</option>
              {categories.map((c) => (
                <option key={c} value={c}>
                  {c}
                </option>
              ))}
            </select>
          </label>
        </div>
      </header>

      {err ? <div className="error">{err}</div> : null}

      {rows == null && !err ? <p className="loading">Firestore에서 불러오는 중…</p> : null}

      {rows != null ? (
        <p className="stats">
          총 <strong>{series.length}</strong>개 상품 · 표시 <strong>{filtered.length}</strong>개
          {maxPoints > 0 ? (
            <>
              {" "}
              · 최대 시점 수: <strong>{maxPoints}</strong>
            </>
          ) : null}
        </p>
      ) : null}

      <div className="grid">
        {filtered.map((s) => (
          <ChartCard key={s.symbol} s={s} />
        ))}
      </div>
    </div>
  );
}
