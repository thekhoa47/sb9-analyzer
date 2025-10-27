'use client';
import Image from 'next/image';
import { useState } from 'react';
import { Button } from '../components/button';
import { usePropertyAnalysisFromAddress } from '../hooks/usePropertyAnalysisFromAddress';
import PageShell from '@/components/layout';

export default function Home() {
  const [address, setAddress] = useState<string>('');
  const { mutate, data, error, isError, isPending, isSuccess, reset } =
    usePropertyAnalysisFromAddress();

  const handleAnalyzeClick = () => {
    const trimmedAddress = address.trim();
    if (!trimmedAddress) return;
    reset();
    mutate(trimmedAddress);
  };

  return (
    <PageShell title="Hannah Anh Dao">
      <div className="font-mono w-full text-sm/6 text-center">
        <label>
          <span className="text-foreground/80">Enter an address:</span>
          <input
            name="addressInput"
            value={address}
            onChange={(e) => {
              setAddress(e.target.value);
              if (isError || isSuccess) reset(); // clear inline state while typing
            }}
            type="text"
            placeholder="e.g. 123 Example St, Garden Grove, CA 92843"
            className={`${isError ? 'border-red-500/80 focus:ring-red-500' : 'border-white focus:ring-white'} text-center border w-full p-2 text-lg rounded-sm caret-white focus:outline-none focus:ring-1 `}
          />
        </label>
      </div>
      {isPending && (
        <div className="text-foreground/80">Analyzing the property, please wait...</div>
      )}
      {isError && <p className="text-sm text-red-600">{(error as Error)?.message}</p>}
      {isSuccess && data && (
        <div className="text-sm text-foreground/80 flex flex-col items-center gap-4">
          Analysis Complete!
          {data?.image_url && (
            <Image src={data?.image_url} alt="Split result" width={400} height={400} />
          )}
          <div className="text-sm font-medium">
            <p>{JSON.stringify(data)}</p>
          </div>
        </div>
      )}
      <div className="flex gap-4 items-center flex-col sm:flex-row w-full sm:w-auto">
        <Button type="button" onClick={handleAnalyzeClick} disabled={isPending || !address.trim()}>
          {isPending ? 'Analyzing…' : 'Analyze The Lot'}
        </Button>
      </div>
    </PageShell>
  );
}
