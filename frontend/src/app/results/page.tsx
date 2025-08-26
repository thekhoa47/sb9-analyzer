'use client';

import { Suspense } from 'react';
import ResultsPageInner from './ResultsPageInner';

export default function ResultsPage() {
  return (
    <Suspense fallback={<div className="p-8">Loading…</div>}>
      <ResultsPageInner />
    </Suspense>
  );
}
