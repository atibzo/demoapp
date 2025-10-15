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

function Spinner({ size = 'sm' }: { size?: 'sm' | 'md' | 'lg' }) {
  const sizes = { sm: 'w-4 h-4', md: 'w-6 h-6', lg: 'w-8 h-8' };
  return (
    <svg className={`animate-spin ${sizes[size]}`} xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
    </svg>
  );
}

function Chip({ label, tone }:{label:string; tone:'ok'|'warn'|'error'|'neutral'}) {
  const t:any={
    ok:'bg-gradient-to-r from-emerald-50 to-emerald-100 text-emerald-700 ring-1 ring-emerald-200 shadow-sm',
    warn:'bg-gradient-to-r from-amber-50 to-amber-100 text-amber-700 ring-1 ring-amber-200 shadow-sm',
    error:'bg-gradient-to-r from-rose-50 to-rose-100 text-rose-700 ring-1 ring-rose-200 shadow-sm',
    neutral:'bg-gradient-to-r from-slate-50 to-slate-100 text-slate-700 ring-1 ring-slate-200 shadow-sm'
  };
  return <span className={`inline-flex items-center gap-1.5 rounded-full px-3 py-1.5 text-xs font-semibold transition-all-smooth hover:scale-105 ${t[tone]}`}>{label}</span>;
}

function ModeBanner({ mode }:{mode:Mode}) {
  if (mode==='LIVE') return null;
  const txt = mode==='HISTORICAL'
    ? 'Market is closed (IST). Showing recent historical data; advice is disabled.'
    : 'Market is open but no live ticks yet; advice is disabled.';
  const cls = mode==='HISTORICAL' 
    ? 'bg-gradient-to-r from-slate-100 to-slate-50 text-slate-800 border-slate-200' 
    : 'bg-gradient-to-r from-amber-100 to-amber-50 text-amber-900 border-amber-200';
  return <div className={`${cls} border-y shadow-sm`}>
    <div className="mx-auto max-w-[1200px] px-3 md:px-6 py-3 text-xs font-semibold flex items-center gap-3">
      <span className="rounded-full px-3 py-1 ring-2 ring-current bg-white/50 backdrop-blur-sm">{mode}</span>
      <span>{txt}</span>
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
  return <header className="sticky top-0 z-50 glass border-b border-white/20 shadow-soft backdrop-blur-xl">
    <div className="mx-auto max-w-[1200px] px-3 md:px-6">
      <div className="flex h-16 items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-gradient-primary text-white text-base font-bold shadow-elevated hover-lift cursor-pointer">IC</div>
          <div className="hidden md:block">
            <div className="text-base font-bold tracking-tight bg-gradient-to-r from-slate-800 to-slate-600 bg-clip-text text-transparent">Intraday Co-Pilot</div>
            <div className="text-[11px] text-slate-500 font-medium">Live Trading • KiteTicker • NSE+BSE</div>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Chip label={`Zerodha ${session?.zerodha ? 'connected' : 'offline'}`} tone={session?.zerodha ? 'ok' : 'error'} />
          <Chip label="LLM ready" tone="ok" />
          <Chip label={`Ticker ${session?.ticker ? 'live' : 'stopped'}`} tone={session?.ticker ? 'ok' : 'warn'} />
          <Chip label={`Market ${session?.market_open ? 'open' : 'closed'}`} tone={session?.market_open ? 'ok' : 'neutral'} />
          {session?.zerodha ? (
            <Chip label="Logged in" tone="ok" />
          ) : (
            <button onClick={onLogin} className="rounded-xl bg-gradient-primary px-4 py-2 text-xs font-bold text-white shadow-elevated hover-lift transition-all-smooth">Login with Zerodha</button>
          )}
        </div>
      </div>
    </div>
  </header>;
}

function Tabs({tab,setTab}:{tab:string; setTab:(t:string)=>void}) {
  const items=['Top Algos','Watch','Analyst','Journal','Policy','Config'];
  return <nav className="border-b border-slate-200 bg-white/60 backdrop-blur-sm">
    <div className="mx-auto max-w-[1200px] px-3 md:px-6">
      <div className="flex flex-wrap gap-2 py-3">
        {items.map(t=>(
          <button 
            key={t} 
            onClick={()=>setTab(t)} 
            className={`px-4 py-2.5 rounded-xl text-sm font-semibold transition-all-smooth ${
              tab===t
                ? 'bg-gradient-primary text-white shadow-card hover-lift'
                : 'text-slate-700 hover:bg-white hover:shadow-soft'
            }`}>
            {t}
          </button>
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
  const [dataMode,setDataMode]=useState<'LIVE'|'HISTORICAL'>('LIVE');
  const [historicalDate,setHistoricalDate]=useState<string>('');
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
      let arr: any[];
      if (dataMode === 'HISTORICAL' && historicalDate) {
        // Fetch historical data for specific date
        const r = await fetch(`${API}/api/v2/hist/plan?date=${historicalDate}&top=10`, { cache: 'no-store' });
        if (r.ok) {
          arr = await r.json();
          if (!Array.isArray(arr)) arr = [];
        } else {
          throw new Error('Failed to fetch historical data');
        }
      } else {
        // Fetch live/current data
        arr = await fetchPlanRows();
      }
      setRows(arr);
    }catch(e:any){
      setError(e?.message||'Load error');
    }finally{ setLoading(false); }
  }

  useEffect(()=>{ 
    if (dataMode === 'LIVE') {
      refresh(); 
      const id=setInterval(refresh, session?.mode === 'LIVE' ? 8000 : 15000); // Slower polling when not live
      return ()=>clearInterval(id);
    }
    // Don't auto-refresh for historical mode
  },[session?.mode, dataMode]);

  return <section className="mx-auto max-w-[1200px] px-3 md:px-6 py-6 md:py-8">
    <div className="mb-4 flex items-center justify-between">
      <div className="flex items-center gap-3">
        <div className="text-xl font-bold bg-gradient-to-r from-slate-800 to-slate-600 bg-clip-text text-transparent">Top Algos</div>
        <Chip label={dataMode === 'HISTORICAL' && historicalDate ? `Historical (${historicalDate})` : session?.mode||'HISTORICAL'} 
              tone={dataMode === 'HISTORICAL' ? 'neutral' : session?.mode==='LIVE'?'ok':session?.mode==='WAITING'?'warn':'neutral'} />
      </div>
      <div className="flex items-center gap-3">
        <ToDControl value={tod} onChange={setTod} onSaveDefault={saveTodDefault} defaultLabel={defaultLabel} />
        <button 
          onClick={refresh} 
          disabled={loading || (dataMode === 'HISTORICAL' && !historicalDate)} 
          className="rounded-xl bg-gradient-primary px-4 py-2.5 text-xs font-bold text-white disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 transition-all-smooth shadow-card hover-lift">
          {loading && <Spinner size="sm" />}
          {loading ? 'Scanning...' : 'Run Scan'}
        </button>
      </div>
    </div>

    <div className="mb-4 rounded-2xl border border-slate-200 bg-white shadow-card p-4">
      <div className="flex flex-wrap items-center gap-3">
        <div className="flex items-center gap-2 text-sm">
          <label className="inline-flex items-center gap-1.5 cursor-pointer">
            <input 
              type="radio" 
              checked={dataMode==='LIVE'} 
              onChange={()=>{setDataMode('LIVE'); setHistoricalDate('');}}
              className="cursor-pointer" />
            <span>Live Data</span>
          </label>
          <label className="inline-flex items-center gap-1.5 cursor-pointer">
            <input 
              type="radio" 
              checked={dataMode==='HISTORICAL'} 
              onChange={()=>setDataMode('HISTORICAL')}
              className="cursor-pointer" />
            <span>Historical Data</span>
          </label>
        </div>
        
        {dataMode === 'HISTORICAL' && (
          <div className="flex items-center gap-2 animate-fadeIn">
            <label className="text-xs text-zinc-600">Select Date:</label>
            <input 
              type="date" 
              value={historicalDate} 
              onChange={e=>setHistoricalDate(e.target.value)}
              max={new Date().toISOString().split('T')[0]}
              className="rounded-xl border border-zinc-300 px-3 py-1.5 text-sm focus:ring-2 focus:ring-zinc-900 focus:border-transparent" />
            {historicalDate && (
              <span className="text-xs text-zinc-500">
                Data from {new Date(historicalDate).toLocaleDateString('en-IN', { weekday: 'short', year: 'numeric', month: 'short', day: 'numeric' })}
              </span>
            )}
          </div>
        )}
        
        {dataMode === 'LIVE' && (
          <div className="text-xs text-zinc-500 flex items-center gap-1.5">
            <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
              <circle cx="10" cy="10" r="10" className="text-emerald-500 animate-pulse"/>
            </svg>
            <span>Auto-refreshing every {session?.mode === 'LIVE' ? '8' : '15'}s</span>
          </div>
        )}
      </div>
    </div>

    {error && <div className="mb-4 rounded-2xl bg-gradient-to-r from-amber-50 to-amber-100 border border-amber-200 text-amber-900 px-4 py-3 text-sm font-medium shadow-sm animate-fadeIn flex items-center gap-2">
      <svg className="w-5 h-5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
        <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
      </svg>
      {error}
    </div>}

    {dataMode === 'HISTORICAL' && !historicalDate && (
      <div className="mb-4 rounded-2xl bg-gradient-to-r from-blue-50 to-cyan-50 border border-blue-200 text-blue-900 px-4 py-3 text-sm font-medium shadow-sm animate-fadeIn">
        <div className="flex items-center gap-3">
          <svg className="w-5 h-5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
          </svg>
          <span>Select a date above and click "Run Scan" to view historical trading opportunities</span>
        </div>
      </div>
    )}

    {loading && rows.length === 0 && (
      <div className="rounded-2xl border border-slate-200 bg-white shadow-card p-12 text-center animate-fadeIn">
        <div className="flex flex-col items-center gap-4">
          <Spinner size="lg" />
          <div className="text-base font-semibold text-slate-700">{dataMode === 'HISTORICAL' ? 'Loading historical data...' : 'Scanning for opportunities...'}</div>
          <div className="text-xs text-slate-500">Please wait while we analyze the market</div>
        </div>
      </div>
    )}

    {(!loading || rows.length > 0) && (
    <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-card transition-opacity duration-300 animate-fadeIn">
      <table className="min-w-full text-sm">
        <thead className="bg-gradient-to-r from-slate-50 to-slate-100 text-left text-xs font-semibold text-slate-700">
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
            <tr key={r.symbol||i} className={`border-t border-slate-100 transition-all-smooth hover:bg-slate-50/50 ${r.readiness==='Stale'?'opacity-50':''}`}>
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
                <Link 
                  className="inline-flex items-center gap-1 px-3 py-1.5 rounded-lg bg-blue-50 text-blue-700 hover:bg-blue-100 font-semibold text-xs transition-all-smooth hover-lift" 
                  href={`/analyst?symbol=${encodeURIComponent(r.symbol)}${dataMode === 'HISTORICAL' && historicalDate ? `&date=${historicalDate}` : ''}`}>
                  <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>
                  Open
                </Link>
              </td>
            </tr>
          ))}
          {rows.length===0 && !loading && (
            <tr><td className="px-3 py-4 text-zinc-500" colSpan={11}>
              {dataMode === 'HISTORICAL' 
                ? `No trading opportunities found for ${historicalDate ? new Date(historicalDate).toLocaleDateString('en-IN', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' }) : 'the selected date'}. Try a different date or check if data is available.`
                : 'No picks yet. If market is closed, charts will still render from historical data.'}
            </td></tr>
          )}
        </tbody>
      </table>
    </div>
    )}
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
  return <section className="mx-auto max-w-[1200px] px-3 md:px-6 py-6 md:py-8">
    <div className="mb-4 flex gap-3 items-center">
      <input placeholder="Add EXCH:SYMBOL (e.g., NSE:INFY)" onKeyDown={e=>{ if(e.key==='Enter'){ add((e.target as any).value); (e.target as any).value=''; } }} className="w-80 rounded-xl border border-slate-300 px-4 py-2.5 text-sm shadow-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent" />
      <span className="flex items-center gap-2 text-xs text-slate-500">
        <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
          <circle cx="10" cy="10" r="10" className="text-emerald-500 animate-pulse"/>
        </svg>
        Polling every 3s
      </span>
    </div>
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
      {symbols.map(s=>(
        <div key={s} className="rounded-2xl border border-slate-200 bg-white shadow-card p-4 hover-lift transition-all-smooth animate-scaleIn">
          <div className="text-base font-bold text-slate-800">{s}</div>
          <div className="grid grid-cols-2 gap-2 text-xs mt-3">
            <div className="rounded-xl bg-gradient-to-br from-slate-50 to-slate-100 p-3 border border-slate-200">
              <div className="text-[10px] text-slate-500 font-semibold uppercase tracking-wide">VWAPΔ</div>
              <span className="font-mono text-sm font-bold text-slate-800">{snaps[s]?.vwap_delta_pct ?? '—'}%</span>
              <Hint metric="vwap_delta" context={{symbol:s, ...snaps[s], mode:session?.mode}}/>
            </div>
            <div className="rounded-xl bg-gradient-to-br from-slate-50 to-slate-100 p-3 border border-slate-200">
              <div className="text-[10px] text-slate-500 font-semibold uppercase tracking-wide">VolX</div>
              <span className="font-mono text-sm font-bold text-slate-800">{snaps[s]?.minute_vol_multiple ?? '—'}×</span>
              <Hint metric="volx" context={{symbol:s, ...snaps[s], mode:session?.mode}}/>
            </div>
            <div className="rounded-xl bg-gradient-to-br from-slate-50 to-slate-100 p-3 border border-slate-200">
              <div className="text-[10px] text-slate-500 font-semibold uppercase tracking-wide">EMA9/21</div>
              <span className="font-mono text-sm font-bold text-slate-800">
                {snaps[s]? (snaps[s].ema9>snaps[s].ema21?'↑':'↓') : '—'} {snaps[s]?.ema9 ?? '—'} / {snaps[s]?.ema21 ?? '—'}
              </span>
              <Hint metric="ema" context={{symbol:s, ema9:snaps[s]?.ema9, ema21:snaps[s]?.ema21, mode:session?.mode}}/>
            </div>
            <div className="rounded-xl bg-gradient-to-br from-slate-50 to-slate-100 p-3 border border-slate-200">
              <div className="text-[10px] text-slate-500 font-semibold uppercase tracking-wide">RSI14</div>
              <span className="font-mono text-sm font-bold text-slate-800">{snaps[s]?.rsi14 ?? '—'}</span>
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
  const [loading,setLoading]=useState(false);
  async function refresh(){ 
    try{ 
      setLoading(true);
      const response = await j(await fetch(`${API}/api/journal`));
      setRows(response.data || []); 
    }catch{ 
      setRows([]);
    }finally{
      setLoading(false);
    }
  }
  useEffect(()=>{ refresh(); },[]);
  return <section className="mx-auto max-w-[1200px] px-3 md:px-6 py-6 md:py-8">
    <button 
      className="rounded-xl bg-gradient-primary px-4 py-2.5 text-xs font-bold text-white disabled:opacity-50 flex items-center gap-2 transition-all-smooth shadow-card hover-lift" 
      onClick={refresh}
      disabled={loading}>
      {loading && <Spinner size="sm" />}
      {loading ? 'Refreshing...' : 'Refresh'}
    </button>
    <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-card mt-4 animate-fadeIn">
      <table className="min-w-full text-sm">
        <thead className="bg-gradient-to-r from-slate-50 to-slate-100 text-left text-xs font-semibold text-slate-700">
          <tr><th className="px-4 py-3">Symbol</th><th className="px-4 py-3">Action</th><th className="px-4 py-3">Note</th></tr>
        </thead>
        <tbody>{rows.map((r:any,i:number)=>
          <tr key={i} className="border-t border-slate-100 transition-all-smooth hover:bg-slate-50/50">
            <td className="px-4 py-3 font-semibold">{r.symbol}</td>
            <td className="px-4 py-3">{r.action}</td>
            <td className="px-4 py-3">{r.note}</td>
          </tr>)}
        </tbody>
      </table>
    </div>
  </section>;
}

function Config() {
  const [cfg,setCfg]=useState<{pinned:string[]; universe_limit:number}|null>(null);
  const [pinText,setPinText]=useState(''); const [limit,setLimit]=useState(300);
  const [loading,setLoading]=useState(false);
  const [saving,setSaving]=useState(false);
  async function load(){ 
    try{
      setLoading(true);
      const c=await j(await fetch(`${API}/api/config`)); 
      setCfg(c); 
      setPinText((c.pinned||[]).join(',')); 
      setLimit(c.universe_limit||300);
    }finally{
      setLoading(false);
    }
  }
  async function save(){
    try{
      setSaving(true);
      await fetch(`${API}/api/config`, { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ pinned: pinText.split(',').map(s=>s.trim()).filter(Boolean), universe_limit: limit })});
      await load(); 
      alert('Saved');
    }finally{
      setSaving(false);
    }
  }
  useEffect(()=>{ load(); },[]);
  return <section className="mx-auto max-w-[1200px] px-3 md:px-6 py-6 md:py-8">
    <div className="grid gap-4 max-w-2xl">
      <div className="rounded-2xl border border-slate-200 bg-white shadow-card p-5">
        <div className="text-sm font-bold text-slate-800 mb-2">Pinned symbols</div>
        <input value={pinText} onChange={e=>setPinText(e.target.value)} placeholder="RELIANCE,INFY,ICICIBANK or EXCH:SYMBOL" className="w-full rounded-xl border border-slate-300 px-4 py-2.5 text-sm shadow-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent" />
        <div className="text-xs text-slate-500 mt-2">Use EXCH:SYMBOL when ambiguous across exchanges.</div>
      </div>
      <div className="rounded-2xl border border-slate-200 bg-white shadow-card p-5">
        <div className="text-sm font-bold text-slate-800 mb-2">Active universe limit</div>
        <input type="number" value={limit} onChange={e=>setLimit(parseInt(e.target.value||'300'))} className="w-40 rounded-xl border border-slate-300 px-4 py-2.5 text-sm shadow-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent" />
      </div>
      <div className="flex gap-3">
        <button 
          onClick={save} 
          disabled={saving}
          className="rounded-xl bg-gradient-primary px-4 py-2.5 text-xs font-bold text-white disabled:opacity-50 flex items-center gap-2 transition-all-smooth shadow-card hover-lift">
          {saving && <Spinner size="sm" />}
          {saving ? 'Saving...' : 'Save'}
        </button>
        <button 
          onClick={load} 
          disabled={loading}
          className="rounded-xl bg-white px-4 py-2.5 text-xs font-bold border border-slate-300 text-slate-700 disabled:opacity-50 flex items-center gap-2 transition-all-smooth shadow-sm hover-lift">
          {loading && <Spinner size="sm" />}
          {loading ? 'Loading...' : 'Reload'}
        </button>
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
    <section className="mx-auto max-w-[1200px] px-3 md:px-6 py-6 md:py-8 space-y-6">
      <div className="flex items-center gap-3">
        <button 
          onClick={save} 
          disabled={saving} 
          className="rounded-xl bg-gradient-primary px-4 py-2.5 text-xs font-bold text-white disabled:opacity-50 flex items-center gap-2 transition-all-smooth shadow-card hover-lift">
          {saving && <Spinner size="sm" />}
          {saving ? 'Saving...' : 'Save'}
        </button>
        {typeof rev === 'number' && <div className="text-sm font-semibold text-slate-600">rev {rev}</div>}
      </div>

      <div className="border border-slate-200 rounded-2xl bg-white shadow-card p-5 space-y-4">
        <div className="text-lg font-bold bg-gradient-to-r from-slate-800 to-slate-600 bg-clip-text text-transparent">Universe</div>
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

      <div className="border border-slate-200 rounded-2xl bg-white shadow-card p-5 space-y-4">
        <div className="text-lg font-bold bg-gradient-to-r from-slate-800 to-slate-600 bg-clip-text text-transparent">Entry & Freshness</div>
        <div className="grid grid-cols-3 gap-3">
          <L label="Entry start (HH:MM)"><input className="input" value={body.entry_window?.start ?? '11:00'} onChange={e=>upd(['entry_window','start'], e.target.value)} /></L>
          <L label="Entry end (HH:MM)"><input className="input" value={body.entry_window?.end ?? '15:10'} onChange={e=>upd(['entry_window','end'], e.target.value)} /></L>
          <L label="Staleness (seconds)"><Num value={body.staleness_s ?? 10} onChange={v=>upd(['staleness_s'], v)} /></L>
        </div>
      </div>

      <div className="border border-slate-200 rounded-2xl bg-white shadow-card p-5 space-y-4">
        <div className="text-lg font-bold bg-gradient-to-r from-slate-800 to-slate-600 bg-clip-text text-transparent">Scoring weights</div>
        <div className="grid grid-cols-5 gap-3">
          {(['trend','pullback','vwap','breakout','volume'] as const).map(k=>(
            <L key={k} label={k}><Num value={body.weights?.[k] ?? 1.0} step={0.1} onChange={v=>upd(['weights',k], v)} /></L>
          ))}
        </div>
      </div>

      <div className="border border-slate-200 rounded-2xl bg-white shadow-card p-5 space-y-4">
        <div className="text-lg font-bold bg-gradient-to-r from-slate-800 to-slate-600 bg-clip-text text-transparent">Bracket tuning (ATR-based)</div>
        <div className="grid grid-cols-4 gap-3">
          <L label="Entry chase max (ATR)"><Num value={body.bracket?.entry_chase_atr ?? 0.15} step={0.05} onChange={v=>upd(['bracket','entry_chase_atr'], v)} /></L>
          <L label="TP1 (ATR)"><Num value={body.bracket?.tp1_atr ?? 0.75} step={0.05} onChange={v=>upd(['bracket','tp1_atr'], v)} /></L>
          <L label="TP2 (ATR)"><Num value={body.bracket?.tp2_atr ?? 1.5} step={0.05} onChange={v=>upd(['bracket','tp2_atr'], v)} /></L>
          <L label="Stop offset vs VWAP (ATR)"><Num value={body.bracket?.stop_vwap_offset_atr ?? 0.5} step={0.05} onChange={v=>upd(['bracket','stop_vwap_offset_atr'], v)} /></L>
        </div>
      </div>

      <div className="border border-slate-200 rounded-2xl bg-white shadow-card p-5 space-y-3">
        <div className="text-lg font-bold bg-gradient-to-r from-slate-800 to-slate-600 bg-clip-text text-transparent">Thresholds (legacy JSON)</div>
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
    <label className="flex flex-col gap-2">
      <span className="text-xs font-semibold text-slate-600 uppercase tracking-wide">{label}</span>
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
    <div className="min-h-screen w-full">
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
