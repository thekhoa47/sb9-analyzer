'use client';
import Image from 'next/image';
import { useState } from 'react';
import { usePrepImage } from './hooks/usePrepImage';

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
      <main className="flex flex-col gap-[32px] row-start-2 items-center justify-items-center w-[600px]">
        <div className="font-mono w-full text-sm/6 text-center sm:text-left">
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
              className={`${isError ? 'border-red-500/80 focus:ring-red-500' : 'border-foreground/80 focus:ring-white'} border w-full p-2 text-lg rounded-sm caret-white focus:outline-none focus:ring-1 `}
            />
          </label>
        </div>
        {isPending && <div className="text-foreground/80">Preparing image, please wait...</div>}
        {isError && <p className="text-sm text-red-600">{(error as Error).message}</p>}
        {isSuccess && data && (
          <div className="text-sm text-green-600">
            Parcel image ready!
            <a className='p-2 underline hover:text-green-400' href={data.image_url} target="_blank" rel="noreferrer noopener">
              Click to see your image!{' '}
            </a>
          </div>
        )}
        <div className="flex gap-4 items-center flex-col sm:flex-row">
          <button
            className="cursor-pointer rounded-sm border border-solid border-transparent transition-colors flex items-center justify-center bg-foreground text-background gap-2 hover:bg-[#383838] dark:hover:bg-[#ccc] font-medium text-sm sm:text-base h-10 sm:h-12 px-4 sm:px-5 sm:w-auto"
            onClick={() => console.log('Analyze Now clicked')}
            aria-label="Analyze Now"
          >
            <Image
              className="dark:invert"
              src="/vercel.svg"
              alt="Vercel logomark"
              width={20}
              height={20}
            />
            Analyzer Now!
          </button>
          <button
            type="button"
            className="cursor-pointer rounded-sm border border-solid border-black/[.08] dark:border-white/[.145] transition-colors flex items-center justify-center hover:bg-[#f2f2f2] dark:hover:bg-[#1a1a1a] hover:border-transparent font-medium text-sm sm:text-base h-10 sm:h-12 px-4 sm:px-5 w-full sm:w-auto md:w-[158px] disabled:opacity-60"
            onClick={handleClick}
            disabled={isPending || !address.trim()}
            aria-label="Prep Image"
          >
            {isPending ? 'Preparing…' : 'Prepare image'}
          </button>
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
