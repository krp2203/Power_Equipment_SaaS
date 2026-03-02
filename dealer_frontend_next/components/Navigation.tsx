'use client';

import Link from 'next/link';
import { DealerConfig } from '@/lib/types';

const mobileStyles = `
  @media (max-width: 768px) {
    .nav-grid {
      display: flex !important;
      flex-direction: column !important;
      gap: 4px !important;
    }
    .social-links {
      display: flex !important;
      flex-wrap: wrap !important;
      justify-content: center !important;
      gap: 8px !important;
    }
    .social-links a {
      font-size: 16px !important;
    }
    .nav-items {
      display: flex !important;
      flex-wrap: wrap !important;
      justify-content: center !important;
      gap: 4px !important;
      font-size: 14px !important;
    }
    .nav-items a {
      font-size: 14px !important;
      padding: 4px 8px !important;
    }
    .contact-links {
      display: flex !important;
      flex-wrap: wrap !important;
      justify-content: center !important;
      gap: 4px !important;
      font-size: 12px !important;
    }
    .contact-links a {
      font-size: 12px !important;
    }
  }
`;

export default function Navigation({ config }: { config: DealerConfig }) {
  const primaryColor = config.theme.primaryColor || '#2563EB';
  const phoneNumber = config.theme.contact_phone || '';
  const address = config.theme.contact_address || '';

  // Create Google Maps URL from address
  const mapsUrl = address
    ? `https://maps.google.com/?q=${encodeURIComponent(address)}`
    : '';

  // Social media links from config
  const socialLinks = [
    {
      name: 'Facebook',
      url: config.theme.socialFacebook,
      icon: (
        <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 24 24">
          <path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z"/>
        </svg>
      ),
    },
    {
      name: 'Instagram',
      url: config.theme.socialInstagram,
      icon: (
        <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 24 24">
          <path d="M12 0C5.373 0 0 5.373 0 12s5.373 12 12 12 12-5.373 12-12S18.627 0 12 0m0 22C6.477 22 2 17.523 2 12S6.477 2 12 2s10 4.477 10 10-4.477 10-10 10m3.5-10c0 1.933-1.567 3.5-3.5 3.5S8 13.933 8 12s1.567-3.5 3.5-3.5 3.5 1.567 3.5 3.5m2.5-8h-12c-.55 0-1 .45-1 1v12c0 .55.45 1 1 1h12c.55 0 1-.45 1-1V5c0-.55-.45-1-1-1m-1 12h-10V5h10v12m2.5-13.5c0 .828-.672 1.5-1.5 1.5s-1.5-.672-1.5-1.5.672-1.5 1.5-1.5 1.5.672 1.5 1.5"/>
        </svg>
      ),
    },
    {
      name: 'Twitter',
      url: config.theme.socialTwitter,
      icon: (
        <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 24 24">
          <path d="M23.953 4.57a10 10 0 01-2.825.775 4.958 4.958 0 002.163-2.723c-.951.555-2.005.959-3.127 1.184a4.92 4.92 0 00-8.384 4.482C7.69 8.095 4.067 6.13 1.64 3.162a4.822 4.822 0 00-.666 2.475c0 1.71.87 3.213 2.188 4.096a4.904 4.904 0 01-2.228-.616v.06a4.923 4.923 0 003.946 4.827 4.996 4.996 0 01-2.212.085 4.936 4.936 0 004.604 3.417 9.867 9.867 0 01-6.102 2.105c-.39 0-.779-.023-1.17-.067a13.995 13.995 0 007.557 2.209c9.053 0 13.998-7.496 13.998-13.985 0-.21 0-.42-.015-.63A9.935 9.935 0 0024 4.59z"/>
        </svg>
      ),
    },
    {
      name: 'YouTube',
      url: config.theme.socialYoutube,
      icon: (
        <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 24 24">
          <path d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z"/>
        </svg>
      ),
    },
    {
      name: 'LinkedIn',
      url: config.theme.socialLinkedin,
      icon: (
        <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 24 24">
          <path d="M20.447 20.452h-3.554v-5.569c0-1.328-.475-2.236-1.986-2.236-1.081 0-1.722.722-2.004 1.418-.103.249-.129.597-.129.946v5.441h-3.554s.05-8.736 0-9.646h3.554v1.364c.425-.654 1.185-1.586 2.882-1.586 2.105 0 3.684 1.375 3.684 4.331v5.537zM5.337 8.855c-1.144 0-1.915-.762-1.915-1.715 0-.955.77-1.715 1.948-1.715 1.178 0 1.915.76 1.948 1.715 0 .953-.77 1.715-1.981 1.715zm1.946 11.597H3.392V9.142h3.891v11.31zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.225 0z"/>
        </svg>
      ),
    },
    {
      name: 'Bluesky',
      url: config.theme.socialBluesky,
      icon: (
        <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 24 24">
          <path d="M12 0c6.627 0 12 5.373 12 12s-5.373 12-12 12S0 18.627 0 12 5.373 0 12 0zm0 1.5c-5.799 0-10.5 4.701-10.5 10.5S6.201 22.5 12 22.5s10.5-4.701 10.5-10.5S17.799 1.5 12 1.5zm3.5 7.5c.828 0 1.5.672 1.5 1.5s-.672 1.5-1.5 1.5-1.5-.672-1.5-1.5.672-1.5 1.5-1.5zm-7 0c.828 0 1.5.672 1.5 1.5s-.672 1.5-1.5 1.5-1.5-.672-1.5-1.5.672-1.5 1.5-1.5zm3.5 6c1.657 0 3 1.343 3 3h-6c0-1.657 1.343-3 3-3z"/>
        </svg>
      ),
    },
  ];

  return (
    <nav className="w-full py-3 text-white" style={{ backgroundColor: primaryColor }}>
      <style>{mobileStyles}</style>
      <div className="nav-grid w-full px-4" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', alignItems: 'center', gap: '16px', height: '100%' }}>
        {/* Left column - Social media links */}
        <div className="social-links flex gap-4 justify-center items-center h-full">
          {socialLinks.map((link) =>
            link.url ? (
              <a
                key={link.name}
                href={link.url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-white hover:opacity-80 transition-opacity flex items-center justify-center"
                aria-label={link.name}
                title={link.name}
              >
                {link.icon}
              </a>
            ) : null
          )}
        </div>

        {/* Center column - Nav items centered as a group */}
        <div className="nav-items flex items-center justify-center gap-12" style={{ gridColumn: '2', justifySelf: 'center' }}>
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
        <div className="contact-links flex gap-6 justify-end">
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
