import { headers } from 'next/headers';
import { getDealerConfig } from '@/lib/api';
import BrandCarousel from '@/components/BrandCarousel';
import AdvertisementCarousel from '@/components/AdvertisementCarousel';
import FeaturedInventory from '@/components/FeaturedInventory';

export const dynamic = 'force-dynamic';

export default async function Home() {
  const config = await getDealerConfig();
  const primaryColor = config.theme.primaryColor || '#2563EB';

  // Fetch advertisements from API
  let advertisements = [];
  try {
    // Determine if we're in a .local (test) environment by checking the request host
    const headersList = await headers();
    const requestHost = headersList.get('host') || '';
    const isTestEnv = requestHost.includes('.local') || requestHost.includes('localhost');

    const response = await fetch(`http://web:5000/api/v1/advertisements?slug=${config.slug}`, {
      headers: {
        'Host': config.slug ? `${config.slug}.bentcrankshaft.${isTestEnv ? 'local' : 'com'}` : 'localhost',
        'X-Dealer-Slug': config.slug || '',
        'X-Environment': isTestEnv ? 'local' : 'production',
      },
    });
    if (response.ok) {
      advertisements = await response.json();
    }
  } catch (error) {
    console.error('Failed to fetch advertisements:', error);
  }

  // Fallbacks for customization
  const heroTitle = config.theme.hero_title || `Welcome to ${config.name}`;
  const heroTagline = config.theme.hero_tagline || "Your Premium Destination for Power Equipment, Parts, and Service.";

  return (
    <div className="flex flex-col min-h-screen">
      {/* Brand Carousel */}
      {(config.theme.brandLogos || config.theme.brand_logos) && Object.keys(config.theme.brandLogos || config.theme.brand_logos || {}).length > 0 && (
        <BrandCarousel logos={config.theme.brandLogos || config.theme.brand_logos} logoUrls={config.theme.brandLogoUrls} />
      )}

      {/* Advertisement Carousel */}
      {advertisements && advertisements.length > 0 && (
        <AdvertisementCarousel advertisements={advertisements} />
      )}

      {/* Featured Inventory (closeout / special price / new arrivals) */}
      <FeaturedInventory />
    </div>
  );
}
