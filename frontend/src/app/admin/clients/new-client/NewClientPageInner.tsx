'use client';
import PageShell from '@/components/layout';
import { NewClientForm } from '../newClientForm';
import { useOnboardNewClient } from '@/hooks/useOnboardNewClient';
import { useState } from 'react';
import { FormValues } from '../formSchema';

export default function NewClientPageInner() {
  const [formInstance, setFormInstance] = useState(0); // forces form reset on reopen
  const {
    mutateAsync, // ← use the async variant
    isPending,
    isError,
    error,
    reset: resetMutation, // clears mutation state (optional)
  } = useOnboardNewClient();
  const handleSubmit = async (data: FormValues) => {
    try {
      await mutateAsync(data); // await server result
      resetMutation(); // clear mutation state for next time
      setFormInstance((n) => n + 1); // remount form → clear fields
    } catch {
      // isError + error are already set by React Query
      // leave modal open so user can see the error and fix it
    }
  };

  const handleCancel = () => {
    resetMutation();
    setFormInstance((n) => n + 1); // also clear form when cancelling
  };

  return (
    <PageShell title="Onboard New Client">
      {isPending && <p> Loading... </p>}
      <NewClientForm
        key={formInstance} // remount to reset fields
        onSubmit={handleSubmit}
        onCancel={handleCancel}
      />
      {isError && (
        <p className="mt-2 text-sm text-red-600">
          {(error as Error)?.message ?? 'Something went wrong. Please try again.'}
        </p>
      )}
    </PageShell>
  );
}
