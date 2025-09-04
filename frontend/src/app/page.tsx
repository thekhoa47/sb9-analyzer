'use client';
import Image from 'next/image';
import { useState } from 'react';
import { usePrepImage } from '../hooks/usePrepImage';
import { Button } from '../components/button';
import { useAnalyze } from '../hooks/useAnalyze';
import { Footer } from '@/components/footer';
import PageShell from '@/components/layout';

export default function Home() {
  const [address, setAddress] = useState<string>('');
  const { mutate, data, error, isError, isPending, isSuccess, reset } = usePrepImage();
  const {
    mutate: mutateAnalyze,
    data: dataAnalyze,
    error: errorAnalyze,
    isError: isErrorAnalyze,
    isPending: isPendingAnalyze,
    isSuccess: isSuccessAnalyze,
    reset: resetAnalyze,
  } = useAnalyze();

  const handlePrepImageClick = () => {
    if (!address.trim()) return;
    reset(); // clear previous error/success
    resetAnalyze(); // clear previous error/success
    mutate(address.trim()); // or: await mutateAsync(address.trim())
  };

  const handleAnalyzeClick = () => {
    if (!address.trim()) return;
    reset(); // clear previous error/success
    resetAnalyze(); // clear previous error/success
    mutateAnalyze(address.trim()); // or: await mutateAsync(address.trim())
  };

  return (
    <PageShell title="SB9 Parcel Analyzer">
      <div className="font-mono w-full text-sm/6 text-center">
        <label>
          <span className="text-foreground/80">Enter your address:</span>
          <input
            name="addressInput"
            value={address}
            onChange={(e) => {
              setAddress(e.target.value);
              if (isError || isSuccess) reset(); // clear inline state while typing
              if (isErrorAnalyze || isSuccessAnalyze) resetAnalyze(); // clear inline state while typing
            }}
            type="text"
            placeholder="e.g. 123 Main St, Springfield, IL 62701"
            className={`${isError ? 'border-red-500/80 focus:ring-red-500' : 'border-white focus:ring-white'} border w-full p-2 text-lg rounded-sm caret-white focus:outline-none focus:ring-1 `}
          />
        </label>
      </div>
      {(isPending || isPendingAnalyze) && (
        <div className="text-foreground/80">Preparing image, please wait...</div>
      )}
      {(isError || isErrorAnalyze) && (
        <p className="text-sm text-red-600">
          {(error as Error)?.message || (errorAnalyze as Error)?.message}
        </p>
      )}
      {((isSuccess && data) || (isSuccessAnalyze && dataAnalyze)) && (
        <div className="text-sm text-foreground/80 flex flex-col items-center gap-4">
          {isSuccess ? 'Parcel image ready!' : 'Analysis Complete!'}
          <Image
            src={data?.image_url || dataAnalyze?.image_url || ''}
            alt="Parcel"
            width={400}
            height={400}
          />
        </div>
      )}
      {isSuccessAnalyze && dataAnalyze && (
        <div className="text-sm font-medium">
          <p>Good for SB9: {dataAnalyze.predicted_label}</p>
          <p>
            Address: {dataAnalyze.address}, {dataAnalyze.city}, {dataAnalyze.state}{' '}
            {dataAnalyze.zip}
          </p>
        </div>
      )}
      <div className="flex gap-4 items-center flex-col sm:flex-row w-full sm:w-auto">
        <Button type="button" onClick={handleAnalyzeClick} disabled={isPending || !address.trim()}>
          <Image
            className="dark:invert"
            src="/vercel.svg"
            alt="Vercel logomark"
            width={20}
            height={20}
          />
          {isPendingAnalyze ? 'Analyzing…' : 'Analyzer Now!'}
        </Button>
        <Button
          type="button"
          variant="outlined"
          disabled={isPending || !address.trim()}
          onClick={handlePrepImageClick}
        >
          {isPending ? 'Preparing…' : 'Prepare image'}
        </Button>
      </div>
    </PageShell>
  );
}
