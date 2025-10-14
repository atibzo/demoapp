'use client';
import { useEffect, useState } from 'react';
import { API, j } from '@/lib/api';

export type Session = {
  zerodha: boolean;
  llm: boolean;
  ticker: boolean;
  stale_count: number;
  subscribed_count: number;
  universe_limit: number;
  market_open: boolean;
  server_time_ist: string;
  mode: 'LIVE' | 'WAITING' | 'HISTORICAL';
  rev: number;
};

export function useSession(pollMs = 5000) {
  const [session, setSession] = useState<Session | null>(null);

  async function refresh() {
    try {
      const s = await j(await fetch(`${API}/api/session`));
      setSession(s);
    } catch {
      // ignore transient fetch errors
    }
  }

  useEffect(() => {
    refresh(); // initial
    const id = setInterval(refresh, pollMs);
    return () => clearInterval(id);
  }, [pollMs]);

  return { session, refresh };
}
