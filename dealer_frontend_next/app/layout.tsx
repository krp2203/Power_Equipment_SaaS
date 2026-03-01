import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';
import Header from '@/components/Header';
import Navigation from '@/components/Navigation';
import Footer from '@/components/Footer';
import { getDealerConfig } from '@/lib/api';
import { headers } from 'next/headers';
import DemoBanner from '@/components/DemoBanner';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: 'Power Equipment Dealer',
  description: 'Your local power equipment expert',
};

export default async function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  // Check if this is an admin route via middleware header
  const headersList = await headers();
  const isAdminRoute = headersList.get('x-is-admin-route') === 'true';

  // Only fetch dealer config for non-admin routes
  const config = isAdminRoute ? null : await getDealerConfig();

  return (
    <html lang="en">
      <body className={`${inter.className} min-h-screen flex flex-col`}>
        {!isAdminRoute && config && (
          <>
            {config.slug === 'pes' && <DemoBanner />}
            <Header config={config} heroTitle={config.theme.hero_title} heroTagline={config.theme.hero_tagline} />
            <Navigation config={config} />
            {children}
            <Footer config={config} />
          </>
        )}
        {isAdminRoute && children}
      </body>
    </html>
  );
}
