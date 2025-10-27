'use client';
import clsx from 'clsx';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { FaUserShield, FaHouseFlag, FaChartPie } from 'react-icons/fa6';
import { TbTools } from "react-icons/tb";

const appLinks = [
  { href: '/', label: 'Tool', icon: < TbTools/> },
  { href: '/properties', label: 'Analyzed Properties', icon: <FaChartPie /> },
  // { href: '/listings', label: 'Active Listings', icon: <FaHouseFlag /> },
  { href: '/admin', label: 'Admin Panel', icon: <FaUserShield /> },
];

export const Footer = () => {
  const pathname = usePathname();
  return (
    <footer className="row-start-3 flex gap-[32px] flex-wrap items-center justify-center">
      {appLinks.map((link) => {
        const isActive =
          link.href === '/'
            ? pathname === '/' // homepage exact match
            : pathname.startsWith(link.href); // prefix match
        return (
          <Link
            key={link.href}
            className={clsx(
              'flex items-center gap-2 text-lg hover:underline hover:underline-offset-8',
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
