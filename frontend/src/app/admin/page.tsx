import PageShell from '@/components/layout';
import Link from 'next/link';

const adminPanels = [
  { label: 'My Clients', href: '/admin/clients' },
  { label: 'Saved Searches', href: '/admin/searches' },
];

export default function Admin() {
  return (
    <PageShell title="Admin Panel">
      <div className="flex flex-col gap-6">
        {adminPanels.map((panel) => {
          return (
            <Link
              key={panel.href}
              href={panel.href}
              className="flex items-center gap-2 hover:underline hover:underline-offset-8"
            >
              {panel.label}
            </Link>
          );
        })}
      </div>
    </PageShell>
  );
}
