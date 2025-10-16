"use client";

import React, { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { API, j } from "@/lib/api";
import Link from "next/link";
import { IndicatorInfo } from "./ContextualTips";

type Mode = "LIVE" | "WAITING" | "HISTORICAL";

type Session = {
  zerodha: boolean;
  llm: boolean;
  ticker: boolean;
  stale_count: number;
  subscribed_count: number;
  universe_limit: number;
  market_open: boolean;
  server_time_ist: string;
  mode: Mode;
  rev: number;
} | null;

type PlanRow = {
  symbol: string;
  side: "long" | "short" | string;
  score: number;
  confidence: number;
  age_s?: number;
  delta_trigger_bps?: number;
  regime?: string;
  readiness?: string;
  checks?: Record<string, boolean>;
};

type Bar = { ts: string; o: number; h: number; l: number; c: number; v: number };

function Spinner({ size = "sm" }: { size?: "sm" | "md" | "lg" }) {
  const sizes = { sm: "w-4 h-4", md: "w-6 h-6", lg: "w-8 h-8" } as const;
  return (
    <svg className={`animate-spin ${sizes[size]}`} xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
    </svg>
  );
}

function HHMM(ts: string) {
  const d = new Date(ts);
  const h = d.getHours().toString().padStart(2, "0");
  const m = d.getMinutes().toString().padStart(2, "0");
  return `${h}:${m}`;
}

function fmt(n?: number) {
  return n === undefined || Number.isNaN(n) ? "—" : n.toFixed(2);
}

export default function TradeRoom({ session }: { session: Session }) {
  const [loadingPlan, setLoadingPlan] = useState(false);
  const [planRows, setPlanRows] = useState<PlanRow[]>([]);
  const [selected, setSelected] = useState<string | null>(null);

  const [bars, setBars] = useState<Bar[]>([]);
  const [loadingBars, setLoadingBars] = useState(false);

  const [explainLoading, setExplainLoading] = useState(false);
  const [explainText, setExplainText] = useState<string>("");

  const [eventLog, setEventLog] = useState<string[]>([]);
  const [lastPlanRefresh, setLastPlanRefresh] = useState<number>(0);

  const planIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const barsIntervalRef = useRef<NodeJS.Timeout | null>(null);

  function log(msg: string) {
    setEventLog((prev) => [
      `[${new Date().toLocaleTimeString("en-IN", { hour12: false })}] ${msg}`,
      ...prev,
    ].slice(0, 200));
  }

  const fetchPlan = useCallback(async () => {
    const now = Date.now();
    if (now - lastPlanRefresh < 1500) return; // debounce
    try {
      setLoadingPlan(true);
      // Try v2, fallback to v1
      let rows: PlanRow[] = [];
      try {
        const r = await fetch(`${API}/api/v2/plan?top=10`, { cache: "no-store" });
        if (r.ok) rows = await r.json();
      } catch {}
      if (!Array.isArray(rows) || rows.length === 0) {
        const v1 = await j(await fetch(`${API}/api/plan?top=10`, { cache: "no-store" }));
        rows = (v1.data || []) as PlanRow[];
      }
      setPlanRows(rows || []);
      setLastPlanRefresh(Date.now());
      log(`Plan loaded (${rows?.length || 0} items)`);
      if (!selected && rows && rows[0]) {
        setSelected(rows[0].symbol);
      }
    } catch (e) {
      // swallow
    } finally {
      setLoadingPlan(false);
    }
  }, [lastPlanRefresh, selected]);

  const fetchBars = useCallback(async (symbol: string) => {
    if (!symbol) return;
    try {
      setLoadingBars(true);
      const r = await fetch(`${API}/api/bars?symbol=${encodeURIComponent(symbol)}&limit=180`, { cache: "no-store" });
      if (r.ok) {
        const x = await r.json();
        const arr: any[] = x?.data?.bars || [];
        const b: Bar[] = arr.map((z: any) => ({ ts: z.ts, o: +z.o, h: +z.h, l: +z.l, c: +z.c, v: +z.v }));
        setBars(b);
        log(`Bars loaded for ${symbol} (${b.length})`);
      } else {
        setBars([]);
      }
    } catch {
      setBars([]);
    } finally {
      setLoadingBars(false);
    }
  }, []);

  const requestExplain = useCallback(async () => {
    const row = planRows.find((r) => r.symbol === selected);
    if (!row) return;
    try {
      setExplainLoading(true);
      setExplainText("");
      const r = await fetch(`${API}/api/contextual/smart-explain`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          query: `Why is ${row.symbol} ranked here and what should I watch?`,
          context: {
            symbol: row.symbol,
            side: row.side,
            score: row.score,
            confidence: row.confidence,
            checks: row.checks,
            mode: session?.mode,
          },
        }),
      });
      if (r.ok) {
        const x = await r.json();
        setExplainText(x?.data?.answer || "");
      } else {
        setExplainText("");
      }
    } catch {
      setExplainText("");
    } finally {
      setExplainLoading(false);
    }
  }, [planRows, selected, session?.mode]);

  useEffect(() => {
    // Initial loads
    fetchPlan();
  }, [fetchPlan]);

  useEffect(() => {
    if (!selected) return;
    fetchBars(selected);
    // poll bars frequently when LIVE
    if (barsIntervalRef.current) clearInterval(barsIntervalRef.current);
    const intervalMs = session?.mode === "LIVE" ? 5000 : 12000;
    barsIntervalRef.current = setInterval(() => fetchBars(selected), intervalMs);
    return () => {
      if (barsIntervalRef.current) clearInterval(barsIntervalRef.current);
    };
  }, [selected, session?.mode, fetchBars]);

  useEffect(() => {
    // plan auto-refresh
    if (planIntervalRef.current) clearInterval(planIntervalRef.current);
    const refreshMs = session?.mode === "LIVE" ? 10000 : 20000;
    planIntervalRef.current = setInterval(fetchPlan, refreshMs);
    return () => {
      if (planIntervalRef.current) clearInterval(planIntervalRef.current);
    };
  }, [session?.mode, fetchPlan]);

  const chartSvg = useMemo(() => {
    if (!bars.length) return null;
    const W = 820,
      H = 300,
      pad = 14;
    const view = bars.slice(-150);
    const maxH = Math.max(...view.map((b) => b.h));
    const minL = Math.min(...view.map((b) => b.l));
    const xw = (W - 2 * pad) / Math.max(1, view.length);
    const scaleY = (v: number) => {
      const t = (v - minL) / Math.max(1e-9, maxH - minL);
      return H - pad - t * (H - 2 * pad);
    };
    const closes = view.map((b) => b.c);
    function ema(data: number[], len: number) {
      const k = 2 / (len + 1);
      let out: number[] = [];
      let e = data[0] || 0;
      data.forEach((v, i) => {
        e = i ? v * k + e * (1 - k) : v;
        out.push(e);
      });
      return out;
    }
    const e9 = ema(closes, 9);
    const e21 = ema(closes, 21);
    let cpv = 0,
      cv = 0;
    const vwap: number[] = [];
    view.forEach((b) => {
      const tp = (b.h + b.l + b.c) / 3;
      cpv += tp * b.v;
      cv += b.v;
      vwap.push(cv ? cpv / cv : b.c);
    });
    return (
      <svg
        width="100%"
        viewBox={`0 0 ${W} ${H}`}
        className="w-full h-[300px] bg-gradient-to-br from-white to-slate-50 rounded-2xl border border-slate-200 shadow-card"
      >
        {[0, 1, 2, 3].map((i) => {
          const y = pad + i * ((H - 2 * pad) / 3);
          return <line key={i} x1={pad} x2={W - pad} y1={y} y2={y} stroke="#e2e8f0" strokeWidth="1" opacity="0.5" />;
        })}
        {view.map((b, i) => {
          const x = pad + i * xw;
          const up = b.c >= b.o;
          const yO = scaleY(b.o),
            yC = scaleY(b.c),
            yH = scaleY(b.h),
            yL = scaleY(b.l);
          const top = Math.min(yO, yC);
          const bot = Math.max(yO, yC);
          const bodyH = Math.max(1, bot - top);
          return (
            <g key={i}>
              <line x1={x + xw * 0.5} x2={x + xw * 0.5} y1={yH} y2={yL} stroke="#94a3b8" strokeWidth="1.2" />
              <rect x={x + xw * 0.15} y={top} width={xw * 0.7} height={bodyH} fill={up ? "#10b981" : "#ef4444"} opacity="0.9" />
            </g>
          );
        })}
        <polyline fill="none" stroke="#06b6d4" strokeWidth="2" points={e9.map((v, i) => `${pad + i * xw},${scaleY(v)}`).join(" ")} opacity="0.9" />
        <polyline fill="none" stroke="#6366f1" strokeWidth="2" points={e21.map((v, i) => `${pad + i * xw},${scaleY(v)}`).join(" ")} opacity="0.8" />
        <polyline fill="none" stroke="#f59e0b" strokeWidth="2" points={vwap.map((v, i) => `${pad + i * xw},${scaleY(v)}`).join(" ")} opacity="0.85" />
      </svg>
    );
  }, [bars]);

  const selectedRow = planRows.find((r) => r.symbol === selected) || null;

  return (
    <section className="mx-auto max-w-[1200px] px-3 md:px-6 py-6 md:py-8">
      <div className="mb-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="text-xl font-bold bg-gradient-to-r from-slate-800 to-slate-600 bg-clip-text text-transparent">Trade Room</div>
          <span className="text-xs text-slate-500">Mode: {session?.mode ?? "HISTORICAL"}</span>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={fetchPlan}
            disabled={loadingPlan}
            className="rounded-xl bg-gradient-primary px-4 py-2.5 text-xs font-bold text-white disabled:opacity-50 flex items-center gap-2 transition-all-smooth shadow-card hover-lift"
          >
            {loadingPlan && <Spinner size="sm" />} Refresh Signals
          </button>
          <Link href="/analyst" className="rounded-xl bg-white px-4 py-2.5 text-xs font-bold border border-slate-300 text-slate-700 shadow-sm hover-lift">Open Analyst</Link>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-[360px_1fr_320px]">
        {/* A) Top Signals */}
        <div className="rounded-2xl border border-slate-200 bg-white shadow-card p-3">
          <div className="flex items-center justify-between mb-2">
            <div className="text-xs font-semibold text-slate-600 uppercase tracking-wide">Top Signals</div>
            {loadingPlan && <Spinner size="sm" />}
          </div>
          <div className="max-h-[420px] overflow-y-auto">
            <table className="w-full text-xs">
              <thead className="sticky top-0 bg-slate-50 text-left">
                <tr>
                  <th className="px-2 py-2">#</th>
                  <th className="px-2 py-2">Symbol</th>
                  <th className="px-2 py-2">Score</th>
                  <th className="px-2 py-2">Conf</th>
                </tr>
              </thead>
              <tbody>
                {planRows.map((r, i) => (
                  <tr
                    key={r.symbol || i}
                    className={`border-t border-slate-100 hover:bg-slate-50 cursor-pointer ${selected === r.symbol ? "bg-slate-50" : ""}`}
                    onClick={() => {
                      setSelected(r.symbol);
                      log(`Selected ${r.symbol}`);
                    }}
                  >
                    <td className="px-2 py-2">{i + 1}</td>
                    <td className="px-2 py-2 font-semibold">{r.symbol}</td>
                    <td className="px-2 py-2 font-mono">{Number(r.score).toFixed(1)}</td>
                    <td className="px-2 py-2 font-mono">{Number(r.confidence).toFixed(2)}</td>
                  </tr>
                ))}
                {planRows.length === 0 && !loadingPlan && (
                  <tr>
                    <td className="px-2 py-3 text-zinc-500" colSpan={4}>
                      No signals yet.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* B) Chart + Indicators */}
        <div className="space-y-3">
          <div className="rounded-2xl border border-slate-200 bg-white shadow-card p-3">
            <div className="flex items-center justify-between mb-2">
              <div className="text-xs font-semibold text-slate-600 uppercase tracking-wide">{selected || "Select a symbol"}</div>
              {loadingBars && <Spinner size="sm" />}
            </div>
            {chartSvg || (
              <div className="h-[300px] grid place-items-center text-sm text-zinc-500">No data</div>
            )}
            {selected && (
              <div className="mt-2 flex items-center gap-4 text-[11px] text-zinc-600">
                <div className="flex items-center gap-1.5">
                  <div className="w-5 h-0.5 bg-sky-500"></div>
                  <span>EMA 9</span>
                  <IndicatorInfo indicator="EMA" simple={true} />
                </div>
                <div className="flex items-center gap-1.5">
                  <div className="w-5 h-0.5 bg-indigo-500"></div>
                  <span>EMA 21</span>
                </div>
                <div className="flex items-center gap-1.5">
                  <div className="w-5 h-0.5 bg-amber-500"></div>
                  <span>VWAP</span>
                  <IndicatorInfo indicator="VWAP" simple={true} />
                </div>
              </div>
            )}
          </div>

          {/* E) Event Log */}
          <div className="rounded-2xl border border-slate-200 bg-white shadow-card p-3">
            <div className="text-xs font-semibold text-slate-600 uppercase tracking-wide mb-1">Event Log</div>
            <div className="h-[140px] overflow-y-auto font-mono text-[11px] text-slate-700">
              {eventLog.length === 0 ? (
                <div className="text-zinc-400">(empty)</div>
              ) : (
                <ul className="space-y-1">
                  {eventLog.map((line, i) => (
                    <li key={i}>{line}</li>
                  ))}
                </ul>
              )}
            </div>
          </div>
        </div>

        {/* D/F) Risk & PnL + Explain */}
        <div className="space-y-3">
          <div className="rounded-2xl border border-slate-200 bg-white shadow-card p-3">
            <div className="text-xs font-semibold text-slate-600 uppercase tracking-wide">Risk & PnL</div>
            <div className="mt-2 grid grid-cols-2 gap-2 text-xs">
              <div className="rounded-xl bg-gradient-to-br from-slate-50 to-slate-100 p-3 border border-slate-200">
                <div className="text-slate-500">Exposure</div>
                <div className="text-sm font-bold text-slate-800">₹ 0</div>
              </div>
              <div className="rounded-xl bg-gradient-to-br from-slate-50 to-slate-100 p-3 border border-slate-200">
                <div className="text-slate-500">PnL Today</div>
                <div className="text-sm font-bold text-slate-800">₹ 0</div>
              </div>
              <div className="rounded-xl bg-gradient-to-br from-slate-50 to-slate-100 p-3 border border-slate-200">
                <div className="text-slate-500">Max Positions</div>
                <div className="text-sm font-bold text-slate-800">—</div>
              </div>
              <div className="rounded-xl bg-gradient-to-br from-slate-50 to-slate-100 p-3 border border-slate-200">
                <div className="text-slate-500">Drawdown</div>
                <div className="text-sm font-bold text-slate-800">—</div>
              </div>
            </div>
          </div>

          <div className="rounded-2xl border border-slate-200 bg-white shadow-card p-3">
            <div className="flex items-center justify-between">
              <div className="text-xs font-semibold text-slate-600 uppercase tracking-wide">Explain Panel</div>
              <button
                onClick={requestExplain}
                disabled={!selectedRow || explainLoading}
                className="rounded-lg px-3 py-1.5 text-xs bg-blue-50 text-blue-700 hover:bg-blue-100 disabled:opacity-50"
              >
                {explainLoading ? "Explaining…" : "Explain"}
              </button>
            </div>
            <div className="mt-2 text-sm text-slate-700 min-h-[80px] whitespace-pre-line">
              {explainText || "Ask for an explanation to see guidance and caveats."}
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
