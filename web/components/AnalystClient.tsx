'use client';

import React, { useEffect, useMemo, useState } from 'react';
import { useSearchParams } from 'next/navigation';
import Link from 'next/link';
import { API, j } from '@/lib/api';

function Spinner({ size = 'sm' }: { size?: 'sm' | 'md' | 'lg' }) {
  const sizes = { sm: 'w-4 h-4', md: 'w-6 h-6', lg: 'w-8 h-8' };
  return (
    <svg className={`animate-spin ${sizes[size]}`} xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
    </svg>
  );
}

type Bar = { ts: string; o:number; h:number; l:number; c:number; v:number };

type Analyze = {
  decision: 'BUY'|'SELL'|'WAIT';
  confidence: number;
  bands: number[];
  action: { trigger:number; entry_range:[number,number]; stop:number; tp1:number; tp2:number; invalid_if:string; };
  risk: { atr:number; rr:number; delta_trigger_bps:number; };
  why: { trend:number; pullback:number; vwap:number; breakout:number; volume:number; checks:Record<string,boolean> };
  meta: { age_s:number; regime:string; source:string };
} | null;

function HHMM(ts: string){ const d = new Date(ts); const h = d.getHours().toString().padStart(2,'0'); const m = d.getMinutes().toString().padStart(2,'0'); return `${h}:${m}`; }
function fmt(n?:number){ return (n===undefined||Number.isNaN(n)) ? '—' : n.toFixed(2); }

export default function AnalystClient(){
  const sp = useSearchParams();
  const sym0 = sp.get('symbol') || 'NSE:INFY';
  const date0 = sp.get('date') || '';

  const [mode, setMode] = useState<'LIVE'|'HIST'>(date0 ? 'HIST' : 'HIST');
  const [symbol, setSymbol] = useState(sym0);
  const [date, setDate] = useState<string>(date0);    // yyyy-mm-dd
  const [bars, setBars] = useState<Bar[]>([]);
  const [ix, setIx] = useState<number>(0);
  const [az, setAz] = useState<Analyze>(null);
  const [riskAmt, setRiskAmt] = useState<number>(1500);
  const [whatif, setWhatif] = useState<any>(null);
  const [loadingDay, setLoadingDay] = useState(false);
  const [loadingAnalysis, setLoadingAnalysis] = useState(false);
  const [loadingWhatif, setLoadingWhatif] = useState(false);
  const [error, setError] = useState<string|null>(null);
  const [liveData, setLiveData] = useState<any>(null);

  const curBar = bars[ix];

  async function loadDay(){
    if(!symbol || !date) return;
    try{
      setLoadingDay(true);
      setError(null);
      const r = await fetch(`${API}/api/v2/hist/bars?symbol=${encodeURIComponent(symbol)}&date=${date}`, { cache: 'no-store' });
      if(!r.ok){ 
        setError('No recorded bars for this date. Make sure ticker persisted minute bars.'); 
        setBars([]); 
        return; 
      }
      const x = await r.json();
      const b:Bar[] = (x.bars||[]).map((z:any)=>({ ts:z.ts, o:+z.o, h:+z.h, l:+z.l, c:+z.c, v:+z.v }));
      if (b.length === 0) {
        setError('No bars found for this symbol and date.');
        setBars([]);
        return;
      }
      setBars(b);
      const mid = Math.min(Math.floor(b.length*0.5), Math.max(0,b.length-1));
      setIx(mid);
      setError(null);
    } catch(e: any) {
      setError(e?.message || 'Failed to load historical data');
      setBars([]);
    } finally {
      setLoadingDay(false);
    }
  }

  async function loadLive(){
    if(!symbol) return;
    try{
      setLoadingAnalysis(true);
      setError(null);
      const r = await fetch(`${API}/api/v2/analyze?symbol=${encodeURIComponent(symbol)}`, { cache: 'no-store' });
      if(!r.ok){ 
        setError('Failed to fetch live analysis'); 
        setLiveData(null);
        return; 
      }
      const data = await r.json();
      setLiveData(data);
      setAz(data);
    } catch(e: any) {
      setError(e?.message || 'Failed to load live data');
    } finally {
      setLoadingAnalysis(false);
    }
  }

  // Auto-load if date is provided in URL
  useEffect(() => {
    if (date0 && sym0) {
      loadDay();
    }
  }, []);

  // Auto-refresh for live mode
  useEffect(() => {
    if (mode === 'LIVE') {
      loadLive();
      const interval = setInterval(loadLive, 10000); // Refresh every 10s
      return () => clearInterval(interval);
    }
  }, [mode, symbol]);

  useEffect(()=>{ (async ()=>{
    if(mode!=='HIST' || bars.length===0) return;
    try {
      setLoadingAnalysis(true);
      const t = HHMM(bars[ix].ts);
      const r = await fetch(`${API}/api/v2/hist/analyze?symbol=${encodeURIComponent(symbol)}&date=${date}&time=${t}`, { cache:'no-store' });
      if(!r.ok){ setAz(null); return; }
      const a = await r.json();
      setAz(a);
    } finally {
      setLoadingAnalysis(false);
    }
  })(); }, [mode, symbol, date, ix, bars.length]);

  useEffect(()=>{ (async()=>{
    if(!az) { setWhatif(null); return; }
    try {
      setLoadingWhatif(true);
      const entry = az.action.entry_range[1];
      const stop  = az.action.stop;
      const tp2   = az.action.tp2;
      const url = `${API}/api/v2/hist/whatif?symbol=${encodeURIComponent(symbol)}&date=${date}&time=${HHMM(bars[ix].ts)}&entry=${entry}&stop=${stop}&tp2=${tp2}&risk_amt=${riskAmt}`;
      const r = await fetch(url, { cache:'no-store' });
      if(!r.ok){ setWhatif(null); return; }
      setWhatif(await r.json());
    } finally {
      setLoadingWhatif(false);
    }
  })(); }, [az, riskAmt, ix, symbol, date, bars.length]);

  const svg = useMemo(()=>{
    if(bars.length===0) return null;
    const W = 860, H = 340, pad = 16;
    const view = bars.slice(Math.max(0, ix-120), ix+1);
    const maxH = Math.max(...view.map(b=>b.h));
    const minL = Math.min(...view.map(b=>b.l));
    const xw = (W - 2*pad) / view.length;
    const scaleY = (v:number)=> {
      const t = (v - minL) / Math.max(1e-9, (maxH - minL));
      return (H - pad) - t*(H - 2*pad);
    };
    const closes = view.map(b=>b.c);
    function ema(data:number[], len:number){
      const k = 2/(len+1); let out:number[] = []; let e = data[0]||0;
      data.forEach((v,i)=>{ e = i? (v*k + e*(1-k)) : v; out.push(e); });
      return out;
    }
    const e9  = ema(closes, 9);
    const e21 = ema(closes, 21);
    let cpv = 0, cv = 0; const vwap:number[]=[];
    view.forEach(b=>{ const tp = (b.h+b.l+b.c)/3; cpv+=tp*b.v; cv+=b.v; vwap.push(cv?cpv/cv:b.c); });
    const tr = az?.action?.trigger, st = az?.action?.stop, t1 = az?.action?.tp1, t2 = az?.action?.tp2;
    const er = az?.action?.entry_range;

    return (
      <svg width="100%" viewBox={`0 0 ${W} ${H}`} className="w-full h-[340px] bg-white rounded-xl border border-zinc-200">
        {[0,1,2,3,4].map(i=>{
          const y = pad + i*(H-2*pad)/4;
          return <line key={i} x1={pad} x2={W-pad} y1={y} y2={y} stroke="#eee" strokeWidth="1"/>;
        })}
        {view.map((b, i)=>{
          const x = pad + i*xw;
          const up = b.c >= b.o;
          const yO = scaleY(b.o), yC = scaleY(b.c), yH = scaleY(b.h), yL = scaleY(b.l);
          const top = Math.min(yO, yC), bot = Math.max(yO, yC);
          const bodyH = Math.max(1, bot-top);
          return (
            <g key={i}>
              <line x1={x+xw*0.5} x2={x+xw*0.5} y1={yH} y2={yL} stroke="#999" />
              <rect x={x + xw*0.15} y={top} width={xw*0.7} height={bodyH} fill={up?"#16a34a":"#dc2626"} />
            </g>
          );
        })}
        <polyline fill="none" stroke="#0ea5e9" strokeWidth="1.5"
          points={e9.map((v,i)=>`${pad+i*xw},${scaleY(v)}`).join(' ')} />
        <polyline fill="none" stroke="#6366f1" strokeWidth="1.2"
          points={e21.map((v,i)=>`${pad+i*xw},${scaleY(v)}`).join(' ')} />
        <polyline fill="none" stroke="#f59e0b" strokeWidth="1"
          points={vwap.map((v,i)=>`${pad+i*xw},${scaleY(v)}`).join(' ')} />
        {typeof tr==='number' && <line x1={pad} x2={W-pad} y1={scaleY(tr)} y2={scaleY(tr)} stroke="#111" strokeDasharray="4 2" />}
        {er && <rect x={pad} width={W-2*pad} y={scaleY(er[1])} height={Math.abs(scaleY(er[0])-scaleY(er[1]))}
                     fill="#0ea5e922" stroke="#0ea5e9" />}
        {typeof st==='number' && <line x1={pad} x2={W-pad} y1={scaleY(st)} y2={scaleY(st)} stroke="#dc2626" strokeWidth="1.5" />}
        {typeof t1==='number' && <line x1={pad} x2={W-pad} y1={scaleY(t1)} y2={scaleY(t1)} stroke="#16a34a" strokeDasharray="3 2" />}
        {typeof t2==='number' && <line x1={pad} x2={W-pad} y1={scaleY(t2)} y2={scaleY(t2)} stroke="#16a34a" strokeWidth="1.5" />}
        {typeof tr==='number' && <text x={W-pad} y={scaleY(tr)-2} textAnchor="end" fontSize="10" fill="#111">Trigger {fmt(tr)}</text>}
        {typeof st==='number' && <text x={W-pad} y={scaleY(st)-2} textAnchor="end" fontSize="10" fill="#dc2626">Stop {fmt(st)}</text>}
        {typeof t1==='number' && <text x={W-pad} y={scaleY(t1)-2} textAnchor="end" fontSize="10" fill="#16a34a">TP1 {fmt(t1)}</text>}
        {typeof t2==='number' && <text x={W-pad} y={scaleY(t2)-2} textAnchor="end" fontSize="10" fill="#16a34a">TP2 {fmt(t2)}</text>}
      </svg>
    );
  }, [bars, ix, az?.action]);

  return (
    <div className="mx-auto max-w-[1200px] px-3 md:px-6 py-4 md:py-6">
      <div className="flex items-center gap-2">
        <Link href="/" className="text-sm underline">← Home</Link>
        <div className="text-sm font-semibold ml-2">Analyst</div>
      </div>

      <div className="mt-3 flex flex-wrap items-center gap-3">
        <input 
          value={symbol} 
          onChange={e=>setSymbol(e.target.value)} 
          placeholder="Enter symbol (e.g., NSE:INFY)"
          className="rounded-xl border border-zinc-300 px-3 py-2 text-sm w-56 focus:ring-2 focus:ring-zinc-900 focus:border-transparent" />
        <div className="flex items-center gap-2 text-sm">
          <label className="inline-flex items-center gap-1.5 cursor-pointer">
            <input type="radio" checked={mode==='LIVE'} onChange={()=>{setMode('LIVE'); setBars([]); setAz(null);}} className="cursor-pointer" />
            <span>Live</span>
          </label>
          <label className="inline-flex items-center gap-1.5 cursor-pointer">
            <input type="radio" checked={mode==='HIST'} onChange={()=>{setMode('HIST'); setLiveData(null);}} className="cursor-pointer" />
            <span>Historical</span>
          </label>
        </div>
        {mode==='HIST' && (
          <>
            <input 
              type="date" 
              value={date} 
              onChange={e=>setDate(e.target.value)}
              max={new Date().toISOString().split('T')[0]}
              className="rounded-xl border border-zinc-300 px-3 py-2 text-sm focus:ring-2 focus:ring-zinc-900 focus:border-transparent" />
            <button 
              onClick={loadDay} 
              disabled={!date||loadingDay} 
              className="rounded-xl bg-zinc-900 px-3 py-2 text-xs font-semibold text-white disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 transition-all hover:bg-zinc-800">
              {loadingDay && <Spinner size="sm" />}
              {loadingDay ? 'Loading...' : 'Load Day'}
            </button>
          </>
        )}
        {mode==='LIVE' && (
          <div className="flex items-center gap-2 text-xs text-zinc-500">
            <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
              <circle cx="10" cy="10" r="10" className="text-emerald-500 animate-pulse"/>
            </svg>
            <span>Auto-refreshing every 10s</span>
          </div>
        )}
      </div>

      {error && (
        <div className="mt-3 rounded-xl bg-red-50 border border-red-200 text-red-800 px-4 py-3 text-sm animate-fadeIn">
          <div className="flex items-center gap-2">
            <svg className="w-5 h-5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
            </svg>
            <span>{error}</span>
          </div>
        </div>
      )}

      {mode==='HIST' && !date && !bars.length && (
        <div className="mt-3 rounded-xl bg-blue-50 border border-blue-200 text-blue-800 px-4 py-3 text-sm animate-fadeIn">
          <div className="flex items-center gap-2">
            <svg className="w-5 h-5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
            </svg>
            <span>Select a date and click "Load Day" to analyze historical data</span>
          </div>
        </div>
      )}

      {mode==='HIST' && bars.length>0 && (
        <div className="mt-3 rounded-xl border border-zinc-200 p-3">
          <div className="flex items-center justify-between text-xs text-zinc-600">
            <span>{HHMM(bars[0].ts)}</span>
            <span className="font-mono">{HHMM(bars[ix].ts)}</span>
            <span>{HHMM(bars[bars.length-1].ts)}</span>
          </div>
          <input type="range" min={0} max={Math.max(0,bars.length-1)} value={ix}
                 onChange={e=>setIx(parseInt(e.target.value))}
                 className="w-full mt-1" />
        </div>
      )}

      {(mode === 'HIST' && bars.length > 0) || (mode === 'LIVE' && az) ? (
      <div className="mt-3 grid gap-3 md:grid-cols-[1fr_360px]">
        <div>
          {mode === 'HIST' && svg}
          {mode === 'LIVE' && (
            <div className="rounded-xl border border-zinc-200 bg-white p-8 text-center">
              <div className="flex flex-col items-center gap-3">
                <svg className="w-16 h-16 text-zinc-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
                <div className="text-sm text-zinc-600">Live chart coming soon</div>
                <div className="text-xs text-zinc-400">Currently showing analysis data only</div>
              </div>
            </div>
          )}
          {mode === 'HIST' && (
            <div className="mt-2 flex items-center gap-4 text-xs text-zinc-600">
              <div className="flex items-center gap-1.5">
                <div className="w-6 h-0.5 bg-sky-500"></div>
                <span>EMA 9</span>
              </div>
              <div className="flex items-center gap-1.5">
                <div className="w-6 h-0.5 bg-indigo-500"></div>
                <span>EMA 21</span>
              </div>
              <div className="flex items-center gap-1.5">
                <div className="w-6 h-0.5 bg-amber-500"></div>
                <span>VWAP</span>
              </div>
              <div className="flex items-center gap-1.5">
                <div className="w-6 h-0.5 bg-zinc-900 border-dashed border-t-2"></div>
                <span>Trigger</span>
              </div>
              <div className="flex items-center gap-1.5">
                <div className="w-6 h-0.5 bg-red-600"></div>
                <span>Stop</span>
              </div>
              <div className="flex items-center gap-1.5">
                <div className="w-6 h-0.5 bg-emerald-600"></div>
                <span>TP1/TP2</span>
              </div>
            </div>
          )}
        </div>
        <div className="space-y-3">
          <div className="rounded-xl border border-zinc-200 p-3 relative">
            {loadingAnalysis && (
              <div className="absolute inset-0 bg-white/80 flex items-center justify-center rounded-xl">
                <Spinner size="md" />
              </div>
            )}
            <div className="text-[11px] text-zinc-500">Decision</div>
            <div className="mt-1 flex items-baseline gap-2">
              <div className={`text-xl font-bold ${az?.decision==='BUY'?'text-emerald-700': az?.decision==='SELL'?'text-rose-700':'text-zinc-800'}`}>{az?.decision || '—'}</div>
              <div className="text-xs text-zinc-500">conf {az?.confidence ?? '—'}</div>
            </div>
            <div className="mt-1 grid grid-cols-2 gap-2 text-xs">
              <div className="rounded bg-zinc-50 p-2">ΔTrigger {az? `${Number(az.risk.delta_trigger_bps).toFixed(0)} bps` : '—'}</div>
              <div className="rounded bg-zinc-50 p-2">R:R {az? Number(az.risk.rr).toFixed(2) : '—'}</div>
              <div className="rounded bg-zinc-50 p-2">ATR {az? Number(az.risk.atr).toFixed(2) : '—'}</div>
              <div className="rounded bg-zinc-50 p-2">Regime {az?.meta?.regime ?? '—'}</div>
            </div>
          </div>

          <div className="rounded-xl border border-zinc-200 p-3">
            <div className="text-[11px] text-zinc-500">Trade Bracket</div>
            <div className="mt-1 text-sm grid gap-1">
              <div>Trigger: <span className="font-mono">{fmt(az?.action?.trigger)}</span></div>
              <div>Entry:   <span className="font-mono">{az? `${fmt(az.action.entry_range[0])} – ${fmt(az.action.entry_range[1])}`:'—'}</span></div>
              <div>Stop:    <span className="font-mono">{fmt(az?.action?.stop)}</span></div>
              <div>TP1/TP2: <span className="font-mono">{az? `${fmt(az.action.tp1)} / ${fmt(az.action.tp2)}`:'—'}</span></div>
              <div className="text-[11px] text-zinc-500">Invalid: {az?.action?.invalid_if || '—'}</div>
            </div>
          </div>

          <div className="rounded-xl border border-zinc-200 p-3 relative">
            {loadingWhatif && (
              <div className="absolute inset-0 bg-white/80 flex items-center justify-center rounded-xl">
                <Spinner size="md" />
              </div>
            )}
            <div className="text-[11px] text-zinc-500">Position Size</div>
            <div className="mt-2 flex items-center gap-2">
              <span className="text-xs">Risk ₹</span>
              <input type="number" value={riskAmt} onChange={e=>setRiskAmt(parseFloat(e.target.value||'0'))}
                     className="w-28 rounded border border-zinc-300 px-2 py-1 text-sm" />
            </div>
            <div className="mt-2 grid grid-cols-2 gap-2 text-sm">
              <div className="rounded bg-zinc-50 p-2">Qty <div className="font-mono">{whatif?.qty ?? '—'}</div></div>
              <div className="rounded bg-zinc-50 p-2">Notional <div className="font-mono">₹ {whatif?.notional ?? '—'}</div></div>
              <div className="rounded bg-zinc-50 p-2">RR <div className="font-mono">{whatif?.rr ?? '—'}</div></div>
              <div className="rounded bg-zinc-50 p-2">Fees <div className="font-mono">₹ {whatif?.fees ?? 0}</div></div>
            </div>
          </div>

          <div className="rounded-xl border border-zinc-200 p-3">
            <div className="text-[11px] text-zinc-500">Checklist</div>
            <ul className="mt-1 text-sm space-y-1">
              <li>VWAPΔ {az?.why?.checks?.['VWAPΔ'] ? '✓' : '✗'}</li>
              <li>VolX {az?.why?.checks?.['VolX'] ? '✓' : '✗'}</li>
            </ul>
          </div>
        </div>
      </div>
      ) : null}
    </div>
  );
}
