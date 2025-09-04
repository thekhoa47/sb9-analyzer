'use client';

import { Footer } from '@/components/footer';
import { useDebounce } from '@/hooks/useDebounce';
import { useResult } from '@/hooks/useResults';
import { useUrlStateGroup } from '@/hooks/useUrlState';
import Image from 'next/image';
import { useEffect, useMemo, useState } from 'react';

export default function ResultsPageInner() {
  const { query, updateQuery } = useUrlStateGroup({
    page: { fromUrl: Number, defaultValue: 1 },
    size: { fromUrl: Number, defaultValue: 10 },
    sortBy: { defaultValue: '' },
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

  const { isPending, isError, isSuccess, data, error } = useResult(filteredParams);

  return (
    <div className="flex flex-col gap-4 p-6 w-full md:w-[600px]">
      <div className="relative">
        {/* example: icon-in-input prefix (optional) */}
        <input
          type="text"
          placeholder="Search property address"
          onChange={(e) => setSearchTerm(e.target.value)}
          value={searchTerm}
          className="w-full border-b-gray-400 border-b p-2 text-md focus:outline-none focus:bg-white/20 focus:rounded-sm focus:border-b-white"
        />
      </div>

      {isPending && <div className="text-foreground/80">Loading please wait...</div>}
      {isError && <p className="text-sm text-red-600">{(error as Error)?.message}</p>}
      {isSuccess && data && (
        <>
          {data.items.map((item) => (
            <div key={item.id} className="flex gap-2 items-center border p-2 rounded">
              <div style={{ width: 180, height: 180, position: 'relative' }}>
                <Image
                  src={item.property.image_url ?? '/fallback.png'}
                  alt="Property image"
                  fill
                  style={{ objectFit: 'cover', objectPosition: 'center' }}
                />
              </div>

              <div>
                <address>
                  {item.property.address}, {item.property.city}, {item.property.state}{' '}
                  {item.property.zip}
                </address>
                <span className="font-weight">{item.predicted_label}</span>
              </div>
            </div>
          ))}
        </>
      )}
    </div>
  );
}
