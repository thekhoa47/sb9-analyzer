'use client';

import { useDebounce } from '@/hooks/useDebounce';
import { useResult } from '@/hooks/useResults';
import { useUrlStateGroup } from '@/hooks/useUrlState';
import Image from 'next/image';
import Link from 'next/link';
import { useEffect, useMemo, useState } from 'react';
import { FaBlog, FaMicrochip } from 'react-icons/fa6';

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
          .filter(([_, v]) => v !== '' && v != null)
          .map(([k, v]) => [k, v.toString()])
      ),
    [query, debouncedSearchTerm]
  );

  const { isPending, isError, isSuccess, data, error } = useResult(filteredParams);

  return (
    <div className="font-sans grid grid-rows-[20px_1fr_20px] items-center justify-items-center min-h-screen p-8 pb-20 gap-16 sm:p-20">
      <h1 className="font-semibold text-2xl ">Past Analyses</h1>
      <main className="flex flex-col gap-[32px] row-start-2 items-center justify-items-center md:w-[600px] sm:w-full">
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
      </main>

      <footer className="row-start-3 flex gap-8 flex-wrap items-center justify-center">
        <a
          className="flex items-center gap-2 hover:underline hover:underline-offset-4"
          href="https://anhdaorealtor.vercel.app/"
          target="_blank"
          rel="noopener noreferrer"
        >
          <FaBlog />
          Go to my blog →
        </a>
        <Link className="flex items-center gap-2 hover:underline hover:underline-offset-4" href="/">
          <FaMicrochip />
          Back to tool →
        </Link>
      </footer>
    </div>
  );
}
