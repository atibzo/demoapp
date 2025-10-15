'use client';

import React, { useEffect, useMemo, useRef, useState } from 'react';
import Link from 'next/link';
import { API, j } from '@/lib/api';
import ErrorBoundary from './ErrorBoundary';
import AnalystClient from './AnalystClient';

/* ------------------------------------------------------------------ *
 * Types & helpers
 * ------------------------------------------------------------------ */

type Mode = 'LIVE' | 'WAITING' | 'HISTORICAL';

type SessionV2 = {
  zerodha: boolean;
  llm: boolean;
  ticker: boolean;
  logged_in: boolean;
  market_open: boolean;
  window_status: 'ok' | 'early' | 'closed';
  degraded: boolean;
  snapshot_p95_age_s: number;
  time_ist: string;
  rev: number;
};

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
};

function v2ToMode(s: SessionV2): Mode {
  if (!s.market_open) return 'HISTORICAL';
  if (s.window_status !== 'ok') return 'WAITING';
  return s.ticker ? 'LIVE' : 'WAITING';
}

/* ---------- v2→v1 fallbacks (single place) ---------- */

async function fetchSession(): Promise<Session> {
  try {
    const response = await fetch(`${API}/api/v2/session`, { cache: 'no-store' });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const s: SessionV2 = await response.json();
    const cfg = await j(await fetch(`${API}/api/config`)).catch(() => ({ universe_limit: 0, pinned: [] }));
    return {
      zerodha: !!s.zerodha,
      llm: !!s.llm,
      ticker: !!s.ticker,
      stale_count: s.snapshot_p95_age_s > 10 ? 1 : 0,
      subscribed_count: 0,
      universe_limit: cfg?.universe_limit ?? 0,
      market_open: !!s.market_open,
      server_time_ist: s.time_ist,
      mode: v2ToMode(s),
      rev: s.rev ?? 0
    };
  } catch (error) {
    console.warn('v2 session failed, falling back to v1:', error);
    try {
      const s = await j(await fetch(`${API}/api/session`));
      return {
        zerodha: !!s.zerodha, llm: !!s.llm, ticker: !!s.ticker,
        stale_count: s.stale_count ?? 0, subscribed_count: s.subscribed_count ?? 0, universe_limit: s.universe_limit ?? 0,
        market_open: !!s.market_open, server_time_ist: s.server_time_ist ?? '',
        mode: (s.mode as Mode) ?? 'HISTORICAL', rev: 0
      };
    } catch (fallbackError) {
      console.error('Both session endpoints failed:', fallbackError);
      throw fallbackError;
    }
  }
}

async function fetchPlanRows(): Promise<any[]> {
  try {
    const r = await fetch(`${API}/api/v2/plan?top=10`, { cache: 'no-store' });
    if (r.ok) {
      const arr = await r.json();
      if (Array.isArray(arr)) return arr;
    }
  } catch {}
  const v1 = await j(await fetch(`${API}/api/plan?top=10`));
  return v1.data || [];
}

async function loadPolicy(): Promise<{ rev: number|null; body: any }> {
  try {
    const res = await fetch(`${API}/api/v2/policy`, { cache: 'no-store' });
    if (res.ok) {
      const p = await res.json();
      if (p && typeof p === 'object' && 'body' in p) return { rev: p.rev ?? null, body: p.body ?? {} };
    }
  } catch {}
  const v1 = await j(await fetch(`${API}/api/policy`));
  return { rev: null, body: v1 ?? {} };
}

async function savePolicy(body: any): Promise<{ rev: number|null; body: any }> {
  try {
    const res = await fetch(`${API}/api/v2/policy`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body)
    });
    if (res.ok) {
      const p = await res.json();
      if (p && typeof p === 'object' && 'body' in p) return { rev: p.rev ?? null, body: p.body ?? body };
    }
  } catch {}
  await fetch(`${API}/api/policy`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body)
  });
  return { rev: null, body };
}

/* ------------------------------------------------------------------ *
 * UI atoms
 * ------------------------------------------------------------------ */

function Chip({ label, tone }:{label:string; tone:'ok'|'warn'|'error'|'neutral'}) {
  const t:any={
    ok:'bg-emerald-100 text-emerald-700 ring-1 ring-emerald-300',
    warn:'bg-amber-100 text-amber-700 ring-1 ring-amber-300',
    error:'bg-rose-100 text-rose-700 ring-1 ring-rose-300',
    neutral:'bg-zinc-100 text-zinc-700 ring-1 ring-zinc-300'
  };
  return <span className={`inline-flex items-center gap-1 rounded-full px-2 py-1 text-xs font-medium ${t[tone]}`}>{label}</span>;
}

function ModeBanner({ mode }:{mode:Mode}) {
  if (mode==='LIVE') return null;
  const txt = mode==='HISTORICAL'
    ? 'Market is closed (IST). Showing recent historical data; advice is disabled.'
    : 'Market is open but no live ticks yet; advice is disabled.';
  const cls = mode==='HISTORICAL' ? 'bg-zinc-100 text-zinc-700' : 'bg-amber-100 text-amber-800';
  return <div className={`${cls} border-y border-zinc-200`}>
    <div className="mx-auto max-w-[1200px] px-3 md:px-6 py-2 text-xs font-medium flex items-center gap-2">
      <span className="rounded-full px-2 py-0.5 ring-1 ring-current">{mode}</span><span>{txt}</span>
    </div>
  </div>;
}

function Hint({ metric, context }:{metric:string; context:any}) {
  const [text,setText]=useState(''); const [loading,setLoading]=useState(false);
  useEffect(()=>{
    let cancelled = false;
    const timeoutId = setTimeout(async()=>{
      if (cancelled) return;
      try{
        setLoading(true);
        const r=await fetch(`${API}/api/hint`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({metric,context})});
        if (cancelled) return;
        const x=await j(r);
        setText(x.data?.hint||'');
      }catch{ 
        if (!cancelled) setText(''); 
      }finally{ 
        if (!cancelled) setLoading(false); 
      }
    }, 500); // Debounce by 500ms
    return () => { cancelled = true; clearTimeout(timeoutId); };
  },[metric, JSON.stringify(context)]);
  if (loading && !text) return <span className="ml-1 text-[11px] text-zinc-400">…</span>;
  return text ? <span className="ml-1 text-[11px] text-zinc-400">✦ {text}</span> : null;
}

/* ------------------------------------------------------------------ *
 * Header / Tabs
 * ------------------------------------------------------------------ */

function Header({ session, onLogin }:{session:Session|null; onLogin:()=>void}) {
  return <header className="sticky top-0 z-50 border-b border-zinc-200 bg-white/90">
    <div className="mx-auto max-w-[1200px] px-3 md:px-6">
      <div className="flex h-14 items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-zinc-900 text-white text-sm font-bold">IC</div>
          <div className="hidden md:block">
            <div className="text-sm font-semibold tracking-tight">Intraday Co-Pilot</div>
            <div className="text-[10px] text-zinc-500">Live-only • KiteTicker • NSE+BSE</div>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Chip label={`Zerodha ${session?.zerodha ? 'connected' : 'offline'}`} tone={session?.zerodha ? 'ok' : 'error'} />
          <Chip label="LLM ready" tone="ok" />
          <Chip label={`Ticker ${session?.ticker ? 'live' : 'stopped'}`} tone={session?.ticker ? 'ok' : 'warn'} />
          <Chip label={`Market ${session?.market_open ? 'open' : 'closed'} (IST)`} tone={session?.market_open ? 'ok' : 'neutral'} />
          {session?.zerodha ? (
            <Chip label="Logged in" tone="ok" />
          ) : (
            <button onClick={onLogin} className="rounded-xl bg-zinc-900 px-3 py-2 text-xs font-semibold text-white">Login with Zerodha</button>
          )}
        </div>
      </div>
    </div>
  </header>;
}

function Tabs({tab,setTab}:{tab:string; setTab:(t:string)=>void}) {
  const items=['Top Algos','Watch','Analyst','Journal','Policy','Config'];
  return <nav className="border-b border-zinc-200 bg-white">
    <div className="mx-auto max-w-[1200px] px-3 md:px-6">
      <div className="flex flex-wrap gap-2 py-2">
        {items.map(t=>(
          <button key={t} onClick={()=>setTab(t)} className={`px-3 py-2 rounded-xl text-sm ${tab===t?'bg-zinc-900 text-white':'text-zinc-700 hover:bg-zinc-100'}`}>{t}</button>
        ))}
      </div>
    </div>
  </nav>;
}

/* ------------------------------------------------------------------ *
 * Top Algos
 * ------------------------------------------------------------------ */

function ToDControl({
  value, onChange, onSaveDefault, defaultLabel
}:{ value:{kind:'post11'|'allday'|'custom'; start?:string; end?:string}, onChange:(v:any)=>void, onSaveDefault:(v:any)=>void, defaultLabel:string }) {
  const [open, setOpen] = useState(false);
  const label = value.kind==='post11' ? 'Post-11 (default)' : value.kind==='allday' ? 'All day (09:15–15:10)' : `Custom (${value.start||'11:00'}–${value.end||'15:10'})`;
  const changed = !(value.kind==='post11' && defaultLabel==='Post-11') && !(value.kind==='allday' && defaultLabel==='All day') && !(value.kind==='custom' && defaultLabel.startsWith('Custom'));
  const [ask, setAsk] = useState(false);
  const [custom] = useState({ start: value.start || '11:00', end: value.end || '15:10' });

  return <div className="flex items-center gap-2">
    <div className="text-xs text-zinc-600">Time filter:</div>
    <div className="relative inline-block">
      <button className="rounded-xl ring-1 ring-zinc-300 px-3 py-1.5 text-xs bg-white hover:bg-zinc-50" onClick={()=>setOpen(x=>!x)}>{label}</button>
      {open && <div className="absolute z-50 mt-1 w-56 rounded-xl border border-zinc-200 bg-white shadow-sm">
        <button className="block w-full px-3 py-2 text-left text-xs hover:bg-zinc-50" onClick={()=>{onChange({kind:'post11'}); setOpen(false);}}>Post-11 (11:00–15:10)</button>
        <button className="block w-full px-3 py-2 text-left text-xs hover:bg-zinc-50" onClick={()=>{onChange({kind:'allday'}); setOpen(false);}}>All day (09:15–15:10)</button>
        <button className="block w-full px-3 py-2 text-left text-xs hover:bg-zinc-50" onClick={()=>{onChange({kind:'custom',start:custom.start,end:custom.end}); setOpen(false);}}>Custom…</button>
      </div>}
    </div>
    {changed && <button className="rounded-xl bg-white px-3 py-1.5 text-xs font-semibold ring-1 ring-zinc-300" onClick={()=>setAsk(true)}>Save as default</button>}
    {ask && <div className="fixed inset-0 bg-black/20 flex items-center justify-center">
      <div className="w-[420px] rounded-2xl bg-white p-4 border border-zinc-200">
        <div className="text-sm font-semibold mb-1">Save time filter as default?</div>
        <div className="text-xs text-zinc-600 mb-3">Current selection: <span className="font-medium">{label}</span></div>
        <div className="flex justify-end gap-2">
          <button className="rounded-xl px-3 py-1.5 text-xs ring-1 ring-zinc-300" onClick={()=>setAsk(false)}>Cancel</button>
          <button className="rounded-xl bg-zinc-900 px-3 py-1.5 text-xs text-white" onClick={()=>{onSaveDefault(value); setAsk(false);}}>Save as default</button>
        </div>
      </div>
    </div>}
  </div>;
}

function TopAlgos({session}:{session:Session|null}) {
  const [rows,setRows]=useState<any[]>([]);
  const [loading,setLoading]=useState(false);
  const [error,setError]=useState<string|null>(null);
  const [tod,setTod]=useState<{kind:'post11'|'allday'|'custom'; start?:string; end?:string}>({kind:'post11'});
  const defaultLabel='Post-11';

  useEffect(()=>{
    const onStorage = (e: StorageEvent) => { if (e.key==='policy_rev_hint') refresh(); };
    window.addEventListener('storage', onStorage);
    return ()=>window.removeEventListener('storage', onStorage);
  },[]);

  async function saveTodDefault(v:any){
    try{
      const p = await loadPolicy();
      const nf = { ...(p.body?.time_filters||{}) };
      nf.default = v.kind==='post11'
        ? {kind:'post11', start:'11:00', end:'15:10'}
        : v.kind==='allday'
          ? {kind:'allday', start:'09:15', end:'15:10'}
          : {kind:'custom', start:v.start||'11:00', end:v.end||'15:10'};
      const saved = await savePolicy({ ...(p.body||{}), time_filters: nf });
      localStorage.setItem('policy_rev_hint', String(saved.rev ?? Date.now()));
      alert('Saved ToD as default');
    }catch{ alert('Failed to save default'); }
  }

  async function refresh(){
    try{
      setLoading(true); setError(null);
      const arr = await fetchPlanRows();
      setRows(arr);
    }catch(e:any){
      setError(e?.message||'Load error');
    }finally{ setLoading(false); }
  }

  useEffect(()=>{ 
    refresh(); 
    const id=setInterval(refresh, session?.mode === 'LIVE' ? 8000 : 15000); // Slower polling when not live
    return ()=>clearInterval(id); 
  },[session?.mode]);

  return <section className="mx-auto max-w-[1200px] px-3 md:px-6 py-4 md:py-6">
    <div className="mb-2 flex items-center justify-between">
      <div className="flex items-center gap-2">
        <div className="text-sm font-semibold">Top Algos</div>
        <Chip label={session?.mode||'HISTORICAL'} tone={session?.mode==='LIVE'?'ok':session?.mode==='WAITING'?'warn':'neutral'} />
      </div>
      <div className="flex items-center gap-3">
        <ToDControl value={tod} onChange={setTod} onSaveDefault={saveTodDefault} defaultLabel={defaultLabel} />
        <button onClick={refresh} disabled={loading} className="rounded-xl bg-zinc-900 px-3 py-2 text-xs font-semibold text-white">{loading?'Refreshing…':'Run Scan'}</button>
      </div>
    </div>

    {error && <div className="mb-2 rounded-xl bg-amber-100 text-amber-800 px-3 py-2 text-sm">{error}</div>}

    <div className="overflow-hidden rounded-2xl border border-zinc-200">
      <table className="min-w-full text-sm">
        <thead className="bg-zinc-50 text-left text-xs text-zinc-600">
          <tr>
            <th className="px-3 py-2">#</th>
            <th className="px-3 py-2">Symbol</th>
            <th className="px-3 py-2">Side</th>
            <th className="px-3 py-2">Score</th>
            <th className="px-3 py-2">Conf.</th>
            <th className="px-3 py-2">Age(s)</th>
            <th className="px-3 py-2">ΔTrigger (bps)</th>
            <th className="px-3 py-2">Regime</th>
            <th className="px-3 py-2">Readiness</th>
            <th className="px-3 py-2">Checks / ✦</th>
            <th className="px-3 py-2"></th>
          </tr>
        </thead>
        <tbody>
          {rows.map((r:any,i:number)=>(
            <tr key={r.symbol||i} className={`border-t border-zinc-100 ${r.readiness==='Stale'?'opacity-50':''}`}>
              <td className="px-3 py-2">{i+1}</td>
              <td className="px-3 py-2 font-semibold">{r.symbol}</td>
              <td className={`px-3 py-2 ${r.side==='long'?'text-emerald-700':'text-rose-700'}`}>{r.side}</td>
              <td className="px-3 py-2 font-mono">{Number(r.score).toFixed(1)}</td>
              <td className="px-3 py-2 font-mono">{Number(r.confidence).toFixed(2)}</td>
              <td className="px-3 py-2">{Number(r.age_s).toFixed(1)}</td>
              <td className="px-3 py-2">{r.delta_trigger_bps ?? '—'}</td>
              <td className="px-3 py-2">{r.regime}</td>
              <td className="px-3 py-2 capitalize">{r.readiness}</td>
              <td className="px-3 py-2 text-xs">
                <div className="flex flex-wrap gap-3 items-center">
                  <span>VWAPΔ {r?.checks?.['VWAPΔ']?'✓':'✗'}</span><Hint metric="vwap_delta" context={{symbol:r.symbol, ...r, mode:session?.mode}}/>
                  <span>VolX {r?.checks?.VolX?'✓':'✗'}</span><Hint metric="volx" context={{symbol:r.symbol, ...r, mode:session?.mode}}/>
                </div>
              </td>
              <td className="px-3 py-2">
                <Link className="underline text-blue-600" href={`/analyst?symbol=${encodeURIComponent(r.symbol)}`}>Open</Link>
              </td>
            </tr>
          ))}
          {rows.length===0 && (
            <tr><td className="px-3 py-4 text-zinc-500" colSpan={11}>
              No picks yet. If market is closed, charts will still render from historical data.
            </td></tr>
          )}
        </tbody>
      </table>
    </div>
  </section>;
}

/* ------------------------------------------------------------------ *
 * Watch
 * ------------------------------------------------------------------ */

function Watch({session}:{session:Session|null}) {
  const [symbols,setSymbols]=useState<string[]>([]);
  const [snaps,setSnaps]=useState<any>({});
  function add(s:string){ s=s.trim(); if(!s) return; if(!symbols.includes(s)) setSymbols([...symbols,s]); }
  useEffect(()=>{
    if(symbols.length===0) return;
    const pollInterval = session?.mode === 'LIVE' ? 3000 : 10000; // Slower when not live
    const id=setInterval(async()=>{
      try {
        const r=await j(await fetch(`${API}/api/live?symbols=${encodeURIComponent(symbols.join(','))}`));
        setSnaps(r.data||{});
      } catch (error) {
        console.error('Watch polling error:', error);
      }
    }, pollInterval);
    return ()=>clearInterval(id);
  },[symbols, session?.mode]);
  return <section className="mx-auto max-w-[1200px] px-3 md:px-6 py-4 md:py-6">
    <div className="mb-2 flex gap-2 items-center">
      <input placeholder="Add EXCH:SYMBOL (e.g., NSE:INFY)" onKeyDown={e=>{ if(e.key==='Enter'){ add((e.target as any).value); (e.target as any).value=''; } }} className="w-72 rounded-xl border border-zinc-300 px-3 py-2 text-sm" />
      <span className="text-xs text-zinc-500">Polling every 3 s</span>
    </div>
    <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
      {symbols.map(s=>(
        <div key={s} className="rounded-xl border border-zinc-200 p-3">
          <div className="text-sm font-semibold">{s}</div>
          <div className="grid grid-cols-2 gap-2 text-xs mt-2">
            <div className="rounded-lg bg-zinc-50 p-2">
              <div className="text-[10px] text-zinc-500">VWAPΔ</div>
              <span className="font-mono">{snaps[s]?.vwap_delta_pct ?? '—'}%</span>
              <Hint metric="vwap_delta" context={{symbol:s, ...snaps[s], mode:session?.mode}}/>
            </div>
            <div className="rounded-lg bg-zinc-50 p-2">
              <div className="text-[10px] text-zinc-500">VolX</div>
              <span className="font-mono">{snaps[s]?.minute_vol_multiple ?? '—'}×</span>
              <Hint metric="volx" context={{symbol:s, ...snaps[s], mode:session?.mode}}/>
            </div>
            <div className="rounded-lg bg-zinc-50 p-2">
              <div className="text-[10px] text-zinc-500">EMA9/21</div>
              <span className="font-mono">
                {snaps[s]? (snaps[s].ema9>snaps[s].ema21?'↑':'↓') : '—'} {snaps[s]?.ema9 ?? '—'} / {snaps[s]?.ema21 ?? '—'}
              </span>
              <Hint metric="ema" context={{symbol:s, ema9:snaps[s]?.ema9, ema21:snaps[s]?.ema21, mode:session?.mode}}/>
            </div>
            <div className="rounded-lg bg-zinc-50 p-2">
              <div className="text-[10px] text-zinc-500">RSI14</div>
              <span className="font-mono">{snaps[s]?.rsi14 ?? '—'}</span>
              <Hint metric="rsi" context={{symbol:s, rsi14:snaps[s]?.rsi14, mode:session?.mode}}/>
            </div>
          </div>
        </div>
      ))}
    </div>
  </section>;
}

/* ------------------------------------------------------------------ *
 * Analyst
 * ------------------------------------------------------------------ */

function Analyst({session}:{session:Session|null}) {
  return <AnalystClient />;
}

/* ------------------------------------------------------------------ *
 * Journal + Config
 * ------------------------------------------------------------------ */

function Journal(){
  const [rows,setRows]=useState<any[]>([]);
  async function refresh(){ try{ setRows(await j(await fetch(`${API}/api/journal`))); }catch{ setRows([]);} }
  useEffect(()=>{ refresh(); },[]);
  return <section className="mx-auto max-w-[1200px] px-3 md:px-6 py-4 md:py-6">
    <button className="rounded-xl bg-zinc-900 px-3 py-2 text-xs font-semibold text-white" onClick={refresh}>Refresh</button>
    <div className="overflow-hidden rounded-xl border border-zinc-200 mt-3">
      <table className="min-w-full text-sm">
        <thead className="bg-zinc-50 text-left text-xs text-zinc-600">
          <tr><th className="px-3 py-2">Symbol</th><th className="px-3 py-2">Action</th><th className="px-3 py-2">Note</th></tr>
        </thead>
        <tbody>{rows.map((r:any,i:number)=>
          <tr key={i} className="border-t border-zinc-100">
            <td className="px-3 py-2">{r.symbol}</td>
            <td className="px-3 py-2">{r.action}</td>
            <td className="px-3 py-2">{r.note}</td>
          </tr>)}
        </tbody>
      </table>
    </div>
  </section>;
}

function Config() {
  const [cfg,setCfg]=useState<{pinned:string[]; universe_limit:number}|null>(null);
  const [pinText,setPinText]=useState(''); const [limit,setLimit]=useState(300);
  async function load(){ const c=await j(await fetch(`${API}/api/config`)); setCfg(c); setPinText((c.pinned||[]).join(',')); setLimit(c.universe_limit||300); }
  async function save(){
    await fetch(`${API}/api/config`, { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ pinned: pinText.split(',').map(s=>s.trim()).filter(Boolean), universe_limit: limit })});
    await load(); alert('Saved');
  }
  useEffect(()=>{ load(); },[]);
  return <section className="mx-auto max-w-[1200px] px-3 md:px-6 py-4 md:py-6">
    <div className="grid gap-3 max-w-xl">
      <div>
        <div className="text-sm font-semibold">Pinned symbols</div>
        <input value={pinText} onChange={e=>setPinText(e.target.value)} placeholder="RELIANCE,INFY,ICICIBANK or EXCH:SYMBOL" className="w-full rounded-xl border border-zinc-300 px-3 py-2 text-sm" />
        <div className="text-xs text-zinc-500 mt-1">Use EXCH:SYMBOL when ambiguous across exchanges.</div>
      </div>
      <div>
        <div className="text-sm font-semibold">Active universe limit</div>
        <input type="number" value={limit} onChange={e=>setLimit(parseInt(e.target.value||'300'))} className="w-32 rounded-xl border border-zinc-300 px-3 py-2 text-sm" />
      </div>
      <div className="flex gap-2">
        <button onClick={save} className="rounded-xl bg-zinc-900 px-3 py-2 text-xs font-semibold text-white">Save</button>
        <button onClick={load} className="rounded-xl bg-white px-3 py-2 text-xs font-semibold ring-1 ring-zinc-300">Reload</button>
      </div>
    </div>
  </section>;
}

/* ------------------------------------------------------------------ *
 * Policy (form UI) — uses v2 if present, else v1; triggers refresh
 * ------------------------------------------------------------------ */

function PolicyForm() {
  const [body, setBody] = useState<any>(null);
  const [rev, setRev] = useState<number|undefined>(undefined);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string|null>(null);

  useEffect(()=>{(async()=>{
    try{
      const p = await loadPolicy();
      setBody(p.body || {});
      setRev(p.rev ?? undefined);
    }catch(e:any){ setError(e?.message||'Failed to load policy'); }
  })();},[]);

  function upd(path: string[], value: any) {
    setBody((prev:any)=>{
      const next = structuredClone(prev||{});
      let cur:any = next;
      for(let i=0;i<path.length-1;i++){ const k=path[i]; cur[k] = cur[k] ?? {}; cur = cur[k]; }
      cur[path[path.length-1]] = value;
      return next;
    });
  }

  async function save() {
    try{
      setSaving(true);
      const res = await savePolicy(body);
      setRev(res.rev ?? undefined);
      setBody(res.body || body);
      localStorage.setItem('policy_rev_hint', String(res.rev ?? Date.now()));
    }catch(e:any){
      setError(e?.message||'Save failed');
    }finally{ setSaving(false); }
  }

  if (error) return <div className="text-red-600">{error}</div>;
  if (!body) return <div>Loading…</div>;

  const list = (v:any)=> Array.isArray(v)? v : (typeof v==='string' && v.length ? v.split(',').map((s:string)=>s.trim()).filter(Boolean) : []);
  const str  = (v:any)=> Array.isArray(v)? v.join(', ') : (v ?? '');

  return (
    <section className="mx-auto max-w-[1200px] px-3 md:px-6 py-4 md:py-6 space-y-6">
      <div className="flex items-center gap-3">
        <button onClick={save} disabled={saving} className="rounded-xl bg-zinc-900 px-3 py-2 text-xs font-semibold text-white">
          {saving? 'Saving…' : 'Save'}
        </button>
        {typeof rev === 'number' && <div className="text-xs text-zinc-500">rev {rev}</div>}
      </div>

      <div className="border rounded p-4 space-y-3">
        <div className="font-medium">Universe</div>
        <div className="grid grid-cols-2 gap-3">
          <L label="Exchange"><input className="input" value={body.universe?.exchange ?? 'NSE'} onChange={e=>upd(['universe','exchange'], e.target.value)} /></L>
          <L label="Prefer exchange when duplicate"><input className="input" value={body.universe?.prefer_exchange ?? 'NSE'} onChange={e=>upd(['universe','prefer_exchange'], e.target.value)} /></L>
          <L label="Series allowlist (comma)"><input className="input" value={str(body.universe?.allow_series ?? ['EQ'])} onChange={e=>upd(['universe','allow_series'], list(e.target.value))} /></L>
          <L label="Exclude patterns (comma)"><input className="input" value={str(body.universe?.exclude_patterns ?? [])} onChange={e=>upd(['universe','exclude_patterns'], list(e.target.value))} /></L>
          <L label="Universe mode">
            <select className="input" value={body.universe?.mode ?? 'strict'} onChange={e=>upd(['universe','mode'], e.target.value)}>
              <option value="strict">strict (drop non-intraday)</option>
              <option value="soft">soft (show but Blocked)</option>
              <option value="off">off (treat same as others)</option>
            </select>
          </L>
          <L label="Min price"><Num value={body.universe?.min_price ?? 20} onChange={v=>upd(['universe','min_price'], v)} /></L>
          <L label="Min median 1-min volume"><Num value={body.universe?.min_median_1m_vol ?? 20000} onChange={v=>upd(['universe','min_median_1m_vol'], v)} /></L>
          <L label="Max spread (bps)"><Num value={body.universe?.max_spread_bps ?? 20} onChange={v=>upd(['universe','max_spread_bps'], v)} /></L>
        </div>
      </div>

      <div className="border rounded p-4 space-y-3">
        <div className="font-medium">Entry & Freshness</div>
        <div className="grid grid-cols-3 gap-3">
          <L label="Entry start (HH:MM)"><input className="input" value={body.entry_window?.start ?? '11:00'} onChange={e=>upd(['entry_window','start'], e.target.value)} /></L>
          <L label="Entry end (HH:MM)"><input className="input" value={body.entry_window?.end ?? '15:10'} onChange={e=>upd(['entry_window','end'], e.target.value)} /></L>
          <L label="Staleness (seconds)"><Num value={body.staleness_s ?? 10} onChange={v=>upd(['staleness_s'], v)} /></L>
        </div>
      </div>

      <div className="border rounded p-4 space-y-3">
        <div className="font-medium">Scoring weights</div>
        <div className="grid grid-cols-5 gap-3">
          {(['trend','pullback','vwap','breakout','volume'] as const).map(k=>(
            <L key={k} label={k}><Num value={body.weights?.[k] ?? 1.0} step={0.1} onChange={v=>upd(['weights',k], v)} /></L>
          ))}
        </div>
      </div>

      <div className="border rounded p-4 space-y-3">
        <div className="font-medium">Bracket tuning (ATR-based)</div>
        <div className="grid grid-cols-4 gap-3">
          <L label="Entry chase max (ATR)"><Num value={body.bracket?.entry_chase_atr ?? 0.15} step={0.05} onChange={v=>upd(['bracket','entry_chase_atr'], v)} /></L>
          <L label="TP1 (ATR)"><Num value={body.bracket?.tp1_atr ?? 0.75} step={0.05} onChange={v=>upd(['bracket','tp1_atr'], v)} /></L>
          <L label="TP2 (ATR)"><Num value={body.bracket?.tp2_atr ?? 1.5} step={0.05} onChange={v=>upd(['bracket','tp2_atr'], v)} /></L>
          <L label="Stop offset vs VWAP (ATR)"><Num value={body.bracket?.stop_vwap_offset_atr ?? 0.5} step={0.05} onChange={v=>upd(['bracket','stop_vwap_offset_atr'], v)} /></L>
        </div>
      </div>

      <div className="border rounded p-4 space-y-2">
        <div className="font-medium">Thresholds (legacy JSON)</div>
        <textarea
          className="input h-48 font-mono"
          value={JSON.stringify(body.thresholds ?? {}, null, 2)}
          onChange={e=>{
            try { upd(['thresholds'], JSON.parse(e.target.value||'{}')); setError(null); }
            catch { setError('Invalid JSON in thresholds'); }
          }}
        />
        {error && <div className="text-red-600 text-sm">{error}</div>}
      </div>
    </section>
  );
}

function L({label, children}:{label:string; children:any}) {
  return (
    <label className="flex flex-col gap-1">
      <span className="text-xs text-zinc-600">{label}</span>
      {children}
    </label>
  );
}
function Num({value, onChange, step=1}:{value:number; onChange:(v:number)=>void; step?:number}) {
  return <input type="number" className="input" value={value} step={step} onChange={e=>onChange(Number(e.target.value))} />;
}

/* ------------------------------------------------------------------ *
 * App shell
 * ------------------------------------------------------------------ */

export default function App() {
  const [session, setSession] = useState<Session | null>(null);
  const [tab, setTab] = useState('Top Algos');
  const lastRevRef = useRef<number | null>(null);

  async function login() {
    const r = await j(await fetch(`${API}/kite/login_url`));
    location.href = r.login_url;
  }

  async function pullSession() {
    try {
      const s = await fetchSession();
      setSession(s);
      if (lastRevRef.current === null) lastRevRef.current = s.rev;
      if (s.rev !== lastRevRef.current) {
        lastRevRef.current = s.rev;
        localStorage.setItem('policy_rev_hint', String(s.rev));
      }
    } catch {}
  }

  useEffect(()=>{ pullSession(); }, []);
  useEffect(()=>{ 
    const pollInterval = session?.mode === 'LIVE' ? 5000 : 10000; // Slower polling when not live
    const id=setInterval(pullSession, pollInterval); 
    return ()=>clearInterval(id); 
  }, [session?.mode]);

  return (
    <div className="min-h-screen w-full bg-zinc-50">
      <Header session={session} onLogin={login} />
      {session && <ModeBanner mode={session.mode} />}
      <Tabs tab={tab} setTab={setTab} />
      <ErrorBoundary>
        {tab === 'Top Algos' && <TopAlgos session={session} />}
        {tab === 'Watch' && <Watch session={session} />}
        {tab === 'Analyst' && <Analyst session={session} />}
        {tab === 'Journal' && <Journal />}
        {tab === 'Policy' && <PolicyForm />}
        {tab === 'Config' && <Config />}
      </ErrorBoundary>
    </div>
  );
}

/* util: in globals.css
.input { @apply border rounded px-2 py-1; }
*/
