'use client';

import { useEffect, useMemo, useState } from 'react';
import { API, j } from '@/lib/api';

type PolicyShape = { rev?: number|null; body: any };

// --- helpers: v2 first, then v1 fallback ---
async function loadPolicy(): Promise<PolicyShape> {
  // v2: {rev, body}
  try {
    const res = await fetch(`${API}/api/v2/policy`, { cache: 'no-store' });
    if (res.ok) {
      const p = await res.json();
      // sanity: v2 payload
      if (p && typeof p === 'object' && 'body' in p) return { rev: p.rev ?? null, body: p.body ?? {} };
    }
  } catch {}
  // v1: raw JSON policy object
  const v1 = await j(await fetch(`${API}/api/policy`));
  return { rev: null, body: v1 ?? {} };
}

async function savePolicy(body: any): Promise<PolicyShape> {
  // v2 first
  try {
    const res = await fetch(`${API}/api/v2/policy`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    if (res.ok) {
      const p = await res.json();
      if (p && typeof p === 'object' && 'body' in p) return { rev: p.rev ?? null, body: p.body ?? body };
    }
  } catch {}
  // v1 fallback (assume it either echoes or just 200 OK)
  await fetch(`${API}/api/policy`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body),
  });
  return { rev: null, body };
}

export default function PolicyEditor() {
  const [policy, setPolicy] = useState<PolicyShape | null>(null);
  const [dirty, setDirty] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      try {
        const p = await loadPolicy();
        setPolicy(p);
      } catch (e: any) {
        setError('Failed to load policy');
      }
    })();
  }, []);

  const body = useMemo(() => policy?.body ?? {}, [policy]);

  function update(path: string[], value: any) {
    setPolicy(prev => {
      if (!prev) return prev;
      const next = { ...prev, body: structuredClone(prev.body ?? {}) };
      let cur: any = next.body;
      for (let i = 0; i < path.length - 1; i++) {
        const k = path[i];
        cur[k] = cur[k] ?? {};
        cur = cur[k];
      }
      cur[path[path.length - 1]] = value;
      return next;
    });
    setDirty(true);
  }

  async function onSave() {
    if (!policy) return;
    try {
      setSaving(true);
      const saved = await savePolicy(policy.body);
      setPolicy(saved);
      setDirty(false);
      // notify other tabs / TopAlgos to refresh
      localStorage.setItem('policy_rev_hint', String(saved.rev ?? Date.now()));
    } catch (e: any) {
      setError(e?.message || 'Save failed');
    } finally {
      setSaving(false);
    }
  }

  if (error) return <div className="text-red-600">{error}</div>;
  if (!policy) return <div>Loading…</div>;

  // helpers for list inputs
  const list = (v: any) =>
    Array.isArray(v) ? v : typeof v === 'string' && v.length ? v.split(',').map((s: string) => s.trim()).filter(Boolean) : [];
  const str = (v: any) => (Array.isArray(v) ? v.join(', ') : v ?? '');

  return (
    <div className="space-y-6">
      {/* Toolbar */}
      <div className="flex items-center gap-3">
        <button
          className={`px-3 py-1 rounded ${dirty ? 'bg-black text-white' : 'bg-gray-200 text-gray-700'}`}
          onClick={onSave}
          disabled={!dirty || saving}
        >
          {saving ? 'Saving…' : dirty ? 'Save' : 'Saved'}
        </button>
      </div>

      {/* Universe */}
      <section className="border rounded p-4 space-y-3">
        <div className="font-medium">Universe</div>
        <div className="grid grid-cols-2 gap-3">
          <L label="Exchange">
            <input className="input" value={body.universe?.exchange ?? 'NSE'} onChange={e => update(['universe', 'exchange'], e.target.value)} />
          </L>
          <L label="Prefer exchange when duplicate">
            <input className="input" value={body.universe?.prefer_exchange ?? 'NSE'} onChange={e => update(['universe', 'prefer_exchange'], e.target.value)} />
          </L>
          <L label="Series allowlist (comma)">
            <input className="input" value={str(body.universe?.allow_series ?? ['EQ'])} onChange={e => update(['universe', 'allow_series'], list(e.target.value))} />
          </L>
          <L label="Exclude patterns (comma)">
            <input className="input" value={str(body.universe?.exclude_patterns ?? [])} onChange={e => update(['universe', 'exclude_patterns'], list(e.target.value))} />
          </L>
          <L label="Universe mode">
            <select className="input" value={body.universe?.mode ?? 'strict'} onChange={e => update(['universe', 'mode'], e.target.value)}>
              <option value="strict">strict (drop non-intraday)</option>
              <option value="soft">soft (show but Blocked)</option>
              <option value="off">off (treat same as others)</option>
            </select>
          </L>
          <L label="Min price">
            <Num value={body.universe?.min_price ?? 20} onChange={v => update(['universe', 'min_price'], v)} />
          </L>
          <L label="Min median 1-min volume">
            <Num value={body.universe?.min_median_1m_vol ?? 20000} onChange={v => update(['universe', 'min_median_1m_vol'], v)} />
          </L>
          <L label="Max spread (bps)">
            <Num value={body.universe?.max_spread_bps ?? 20} onChange={v => update(['universe', 'max_spread_bps'], v)} />
          </L>
        </div>
      </section>

      {/* Entry & Freshness */}
      <section className="border rounded p-4 space-y-3">
        <div className="font-medium">Entry & Freshness</div>
        <div className="grid grid-cols-3 gap-3">
          <L label="Entry start (HH:MM)">
            <input className="input" value={body.entry_window?.start ?? '11:00'} onChange={e => update(['entry_window', 'start'], e.target.value)} />
          </L>
          <L label="Entry end (HH:MM)">
            <input className="input" value={body.entry_window?.end ?? '15:10'} onChange={e => update(['entry_window', 'end'], e.target.value)} />
          </L>
          <L label="Staleness (seconds)">
            <Num value={body.staleness_s ?? 10} onChange={v => update(['staleness_s'], v)} />
          </L>
        </div>
      </section>

      {/* Factor weights */}
      <section className="border rounded p-4 space-y-3">
        <div className="font-medium">Scoring weights</div>
        <div className="grid grid-cols-5 gap-3">
          {(['trend', 'pullback', 'vwap', 'breakout', 'volume'] as const).map(k => (
            <L key={k} label={k}>
              <Num value={body.weights?.[k] ?? 1.0} step={0.1} onChange={v => update(['weights', k], v)} />
            </L>
          ))}
        </div>
      </section>

      {/* Bracket */}
      <section className="border rounded p-4 space-y-3">
        <div className="font-medium">Bracket tuning (ATR-based)</div>
        <div className="grid grid-cols-4 gap-3">
          <L label="Entry chase max (ATR)"><Num value={body.bracket?.entry_chase_atr ?? 0.15} step={0.05} onChange={v => update(['bracket', 'entry_chase_atr'], v)} /></L>
          <L label="TP1 (ATR)"><Num value={body.bracket?.tp1_atr ?? 0.75} step={0.05} onChange={v => update(['bracket', 'tp1_atr'], v)} /></L>
          <L label="TP2 (ATR)"><Num value={body.bracket?.tp2_atr ?? 1.5} step={0.05} onChange={v => update(['bracket', 'tp2_atr'], v)} /></L>
          <L label="Stop offset vs VWAP (ATR)"><Num value={body.bracket?.stop_vwap_offset_atr ?? 0.5} step={0.05} onChange={v => update(['bracket', 'stop_vwap_offset_atr'], v)} /></L>
        </div>
      </section>

      {/* Legacy thresholds editor */}
      <section className="border rounded p-4 space-y-3">
        <div className="font-medium">Thresholds (legacy)</div>
        <textarea
          className="input h-48 font-mono"
          value={JSON.stringify(body.thresholds ?? {}, null, 2)}
          onChange={e => {
            try { update(['thresholds'], JSON.parse(e.target.value || '{}')); setError(null); }
            catch { setError('Invalid JSON in thresholds'); }
          }}
        />
        {error && <div className="text-red-600 text-sm">{error}</div>}
      </section>
    </div>
  );
}

function L({ label, children }: { label: string; children: any }) {
  return (
    <label className="flex flex-col gap-1">
      <span className="text-xs text-zinc-600">{label}</span>
      {children}
    </label>
  );
}

function Num({ value, onChange, step = 1 }: { value: number; onChange: (v: number) => void; step?: number }) {
  return <input type="number" className="input" value={value} step={step} onChange={e => onChange(Number(e.target.value))} />;
}
