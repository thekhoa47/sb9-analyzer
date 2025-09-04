'use client';
// components/PageShell.tsx
import { Footer } from '@/components/footer';
import { Button } from '../button';
import { FaArrowLeft } from 'react-icons/fa6';
import { useRouter } from 'next/navigation';
import { usePathname } from 'next/navigation';

export default function PageShell({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  const router = useRouter();
  const pathname = usePathname();

  // Normalize and split path
  const cleaned = (pathname || '/').replace(/\/+$/, '') || '/';
  const segments = cleaned.split('/').filter(Boolean); // e.g. "/admin/clients" -> ["admin","clients"]

  // Rule: show back button only when path depth >= 2 (i.e., nested)
  const isNested = segments.length >= 2;

  return (
    <div className="font-sans grid grid-rows-[20px_1fr_20px] items-center justify-items-center min-h-screen p-8 pb-20 gap-16 sm:p-20">
      <div className="inline-flex items-baseline">
        {isNested && (
          <Button variant="text" onClick={() => router.back()}>
            <FaArrowLeft />
          </Button>
        )}
        <h1 className="font-semibold text-2xl">{title}</h1>
      </div>
      <main className="flex flex-col gap-[32px] row-start-2 items-center justify-items-center md:w-[600px] sm:w-full">
        {children}
      </main>
      <Footer />
    </div>
  );
}
