'use client';
import { Button } from '@/components/button';
import { Modal } from '@/components/modal';
import { NewClientForm } from './newClientForm';
import { useEffect, useMemo, useState } from 'react';
import { FormValues } from './formSchema';
import { useOnboardNewClient } from '@/hooks/useOnboardNewClient';
import PageShell from '@/components/layout';
import { useUrlStateGroup } from '@/hooks/useUrlState';
import { useDebounce } from '@/hooks/useDebounce';
import { useClients } from '@/hooks/useClients';

export default function ClientsPageInner() {
  const [open, setOpen] = useState(false);
  const [formInstance, setFormInstance] = useState(0); // forces form reset on reopen
  const { query, updateQuery } = useUrlStateGroup({
    page: { fromUrl: Number, defaultValue: 1 },
    size: { fromUrl: Number, defaultValue: 10 },
    search: { fromUrl: String, defaultValue: '' },
  });

  const [searchTerm, setSearchTerm] = useState(query.search);
  const debouncedSearchTerm = useDebounce(searchTerm, 1000);

  // ❗️ DO NOT call updateQuery during render.
  useEffect(() => {
    if (debouncedSearchTerm !== query.search) {
      // consider router.replace inside the hook if you don't want history spam
      updateQuery({ search: debouncedSearchTerm, page: 1 });
    }
  }, [debouncedSearchTerm, query.search, updateQuery]);

  const filteredParams = useMemo(
    () =>
      Object.fromEntries(
        Object.entries({
          ...query,
          searchTerm: debouncedSearchTerm, // (if your API expects "search", use that key instead)
        })
          .filter(([, v]) => v !== '' && v != null)
          .map(([k, v]) => [k, v.toString()])
      ),
    [query, debouncedSearchTerm]
  );

  const {
    isPending: isPendingClients,
    isError: isErrorClients,
    isSuccess: isSuccessClients,
    data: dataClients,
    error: errorClients,
  } = useClients(filteredParams);

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
      setOpen(false); // close **only** on success
      resetMutation(); // clear mutation state for next time
      setFormInstance((n) => n + 1); // remount form → clear fields
    } catch {
      // isError + error are already set by React Query
      // leave modal open so user can see the error and fix it
    }
  };

  const handleCancel = () => {
    setOpen(false);
    resetMutation();
    setFormInstance((n) => n + 1); // also clear form when cancelling
  };

  return (
    <PageShell title="Clients">
      <Button variant="outlined" onClick={() => setOpen(true)}>
        + New Client
      </Button>
      <div className="relative">
        {/* example: icon-in-input prefix (optional) */}
        <input
          type="text"
          placeholder="Search by name/email/phone"
          onChange={(e) => setSearchTerm(e.target.value)}
          value={searchTerm}
          className="w-full border-b-gray-400 border-b p-2 text-md focus:outline-none focus:bg-white/20 focus:rounded-sm focus:border-b-white"
        />
      </div>
      {isPendingClients && <div className="text-foreground/80">Loading please wait...</div>}
      {isErrorClients && <p className="text-sm text-red-600">{(errorClients as Error)?.message}</p>}
      {isSuccessClients && dataClients && (
        <>
          {dataClients.items.map((client) => (
            <div key={client.id} className="flex gap-2 items-center border p-2 rounded">
              <span className="font-bold">{client.name}</span>
              <span className="text-amber-300">{client.email}</span>
              <span className="text-cyan-300">{client.phone}</span>
            </div>
          ))}
        </>
      )}

      <Modal
        open={open}
        title="Add New Client"
        onClose={() => {
          if (!isPending) handleCancel(); // prevent closing while submitting
        }}
        // If your <Modal> supports it, also disable backdrop/escape close while pending
        // disableBackdropClose={isPending}
        // disableEscapeKeyDown={isPending}
      >
        {/* Show mutation errors at the top */}
        {isError && (
          <p className="mb-2 text-sm text-red-600">
            {(error as Error)?.message ?? 'Something went wrong. Please try again.'}
          </p>
        )}

        <NewClientForm
          key={formInstance} // remount to reset fields
          onSubmit={handleSubmit}
          onCancel={handleCancel}
        />
      </Modal>
    </PageShell>
  );
}
