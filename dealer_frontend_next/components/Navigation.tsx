'use client';

import Link from 'next/link';
import { DealerConfig } from '@/lib/types';

export default function Navigation({ config }: { config: DealerConfig }) {
  const primaryColor = config.theme.primaryColor || '#2563EB';
  const phoneNumber = config.theme.contact_phone || '';
  const address = config.theme.contact_address || '';

  // Create Google Maps URL from address
  const mapsUrl = address
    ? `https://maps.google.com/?q=${encodeURIComponent(address)}`
    : '';

  return (
    <nav className="w-full py-3 text-white" style={{ backgroundColor: primaryColor }}>
      <div className="w-full px-4" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', alignItems: 'center', gap: '16px' }}>
        {/* Left column - empty for balance */}
        <div></div>

        {/* Center column - Nav items centered as a group */}
        <div className="flex items-center justify-center gap-12" style={{ gridColumn: '2', justifySelf: 'center' }}>
          <Link
            href="/"
            className="text-2xl font-bold text-white hover:opacity-80 transition-opacity whitespace-nowrap"
          >
            Home
          </Link>
          <Link
            href="/inventory"
            className="text-2xl font-bold text-white hover:opacity-80 transition-opacity whitespace-nowrap"
          >
            Inventory
          </Link>
          <Link
            href="/parts"
            className="text-2xl font-bold text-white hover:opacity-80 transition-opacity whitespace-nowrap"
          >
            Parts
          </Link>
          <Link
            href="/service"
            className="text-2xl font-bold text-white hover:opacity-80 transition-opacity whitespace-nowrap"
          >
            Service
          </Link>
          <Link
            href="/contact"
            className="text-2xl font-bold text-white hover:opacity-80 transition-opacity whitespace-nowrap"
          >
            Contact
          </Link>
        </div>

        {/* Right column - Contact links right-aligned */}
        <div className="flex gap-6 justify-end">
          {phoneNumber && (
            <a
              href={`tel:${phoneNumber}`}
              className="text-lg font-semibold text-white hover:opacity-80 transition-opacity whitespace-nowrap flex items-center gap-2"
            >
              <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                <path d="M20.01 15.38c-1.23 0-2.42-.2-3.53-.56-.35-.12-.74-.03-1.01.24l-1.57 1.97c-2.83-1.35-5.48-3.9-6.89-6.83l1.95-1.66c.27-.28.35-.67.24-1.02-.37-1.11-.56-2.3-.56-3.53 0-.54-.45-.99-.99-.99H4.19C3.65 3 3 3.24 3 3.99 3 13.28 10.73 21 20.01 21c.71 0 .99-.63.99-1.18v-3.45c0-.54-.45-.99-.99-.99z"/>
              </svg>
              {phoneNumber}
            </a>
          )}
          {mapsUrl && (
            <a
              href={mapsUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="text-lg font-semibold text-white hover:opacity-80 transition-opacity whitespace-nowrap flex items-center gap-2"
            >
              <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                <path d="M12 2C6.48 2 2 6.48 2 12c0 7 10 13 10 13s10-6 10-13c0-5.52-4.48-10-10-10zm0 15c-2.76 0-5-2.24-5-5s2.24-5 5-5 5 2.24 5 5-2.24 5-5 5z"/>
              </svg>
              Directions
            </a>
          )}
        </div>
      </div>
    </nav>
  );
}
