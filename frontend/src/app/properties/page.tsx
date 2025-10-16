'use client';

import { Suspense } from 'react';
import AnalyzedPropertiesPageInner from './AnalyzedPropertiesPageInner';
import PageShell from '@/components/layout';

export default function AnalyzedPropertiesPage() {
  return (
    <Suspense fallback={<div className="p-8">Loading…</div>}>
      <PageShell title="Analyzed Properties">
        <AnalyzedPropertiesPageInner />
      </PageShell>
    </Suspense>
  );
}
