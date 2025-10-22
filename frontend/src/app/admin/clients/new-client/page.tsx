import { Suspense } from 'react';
import NewClientPageInner from './NewClientPageInner';

export default function NewClients() {
  return (
    <Suspense fallback={<div className="p-8">Loading…</div>}>
        <NewClientPageInner />
    </Suspense>
  );
}
