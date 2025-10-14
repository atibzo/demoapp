import { Suspense } from 'react';
import AnalystClient from '@/components/AnalystClient';

// Avoid static prerender + CSR bailout complaint
export const dynamic = 'force-dynamic';

export default function AnalystPage() {
  return (
    <Suspense fallback={<div className="p-4 text-sm text-zinc-500">Loading…</div>}>
      <AnalystClient />
    </Suspense>
  );
}
