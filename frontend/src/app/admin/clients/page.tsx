'use client';
import { Suspense } from 'react';
import PageShell from '@/components/layout';
import ClientsPageInner from './ClientsPageInner';

export default function Clients() {
  return (
    <Suspense fallback={<div className="p-8">Loading…</div>}>
        <ClientsPageInner />
    </Suspense>
  );
}
