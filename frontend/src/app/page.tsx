'use client';
import Image from 'next/image';
import { useState } from 'react';
import { usePrepImage } from './hooks/usePrepImage';
import { Button } from './components/button';

export default function Home() {
  const [address, setAddress] = useState<string>('');
  const { mutate, data, error, isError, isPending, isSuccess, reset } = usePrepImage();

  const handleClick = () => {
    if (!address.trim()) return;
    reset(); // clear previous error/success
    mutate(address.trim()); // or: await mutateAsync(address.trim())
  };

  return (
    <div className="font-sans grid grid-rows-[20px_1fr_20px] items-center justify-items-center min-h-screen p-8 pb-20 gap-16 sm:p-20">
      <main className="flex flex-col gap-[32px] row-start-2 items-center justify-items-center md:w-[600px] sm:w-full">
        <div className="font-mono w-full text-sm/6 text-center">
          <label>
            <span className="text-foreground/80">Enter your address:</span>
            <input
              name="addressInput"
              value={address}
              onChange={(e) => {
                setAddress(e.target.value);
                if (isError || isSuccess) reset(); // clear inline state while typing
              }}
              type="text"
              placeholder="e.g. 123 Main St, Springfield, IL 62701"
              className={`${isError ? 'border-red-500/80 focus:ring-red-500' : 'border-white focus:ring-white'} border w-full p-2 text-lg rounded-sm caret-white focus:outline-none focus:ring-1 `}
            />
          </label>
        </div>
        {isPending && <div className="text-foreground/80">Preparing image, please wait...</div>}
        {isError && <p className="text-sm text-red-600">{(error as Error).message}</p>}
        {isSuccess && data && (
          <div className="text-sm text-green-600">
            Parcel image ready!
            <a
              className="p-2 underline hover:text-green-400"
              href={data.image_url}
              target="_blank"
              rel="noreferrer noopener"
            >
              Click to see your image!{' '}
            </a>
          </div>
        )}
        <div className="flex gap-4 items-center flex-col sm:flex-row w-full sm:w-auto">
          <Button disabled type="button" onClick={() => console.log('Analyze Now clicked')}>
            <Image
              className="dark:invert"
              src="/vercel.svg"
              alt="Vercel logomark"
              width={20}
              height={20}
            />
            Analyzer Now!
          </Button>
          <Button
            type="button"
            variant="outlined"
            disabled={isPending || !address.trim()}
            onClick={handleClick}
          >
            {isPending ? 'Preparing…' : 'Prepare image'}
          </Button>
        </div>
      </main>
      <footer className="row-start-3 flex gap-[24px] flex-wrap items-center justify-center">
        <a
          className="flex items-center gap-2 hover:underline hover:underline-offset-4"
          href="https://anhdaorealtor.vercel.app/"
          target="_blank"
          rel="noopener noreferrer"
        >
          <Image aria-hidden src="/globe.svg" alt="Globe icon" width={16} height={16} />
          Go to my blog →
        </a>
      </footer>
    </div>
  );
}
