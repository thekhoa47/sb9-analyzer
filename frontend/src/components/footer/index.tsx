'use client';
import clsx from 'clsx';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { FaBlog, FaList, FaMicrochip, FaUserShield } from 'react-icons/fa6';

const appLinks = [
  { href: '/', label: 'Tool', icon: <FaMicrochip /> },
  { href: '/results', label: 'Past Analyses', icon: <FaList /> },
  { href: '/admin', label: 'Admin Panel', icon: <FaUserShield /> },
];

export const Footer = () => {
  const pathname = usePathname();
  return (
    <footer className="row-start-3 flex gap-[24px] flex-wrap items-center justify-center">
      <a
        className="flex items-center gap-2 hover:underline hover:underline-offset-4"
        href="https://anhdaorealtor.vercel.app/"
        target="_blank"
        rel="noopener noreferrer"
      >
        <FaBlog />
        Go to my blog →
      </a>
      {appLinks.map((link) => {
        const isActive =
          link.href === '/'
            ? pathname === '/' // homepage exact match
            : pathname.startsWith(link.href); // prefix match
        return (
          <Link
            key={link.href}
            className={clsx(
              'flex items-center gap-2 hover:underline hover:underline-offset-8',
              isActive && 'underline underline-offset-8 text-gray-400'
            )}
            href={link.href}
          >
            {link.icon}
            {link.label}
          </Link>
        );
      })}
    </footer>
  );
};
