import Link from 'next/link';
import { headers } from 'next/headers';
import { getDealerConfig } from '@/lib/api';
import BrandCarousel from '@/components/BrandCarousel';
import AdvertisementCarousel from '@/components/AdvertisementCarousel';

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

  const featInvTitle = config.theme.feat_inventory_title || "Huge Selection";
  const featInvText = config.theme.feat_inventory_text || "Browse our wide range of mowers, chainsaws, and blowers from top brands.";

  const featPartsTitle = config.theme.feat_parts_title || "Genuine Parts";
  const featPartsText = config.theme.feat_parts_text || "Find the exact part you need with our detailed diagrams.";

  const featServiceTitle = config.theme.feat_service_title || "Expert Service";
  const featServiceText = config.theme.feat_service_text || "Our certified technicians are ready to keep your equipment running like new.";

  return (
    <div className="flex flex-col min-h-screen">
      {/* Advertisement Carousel */}
      {advertisements && advertisements.length > 0 && (
        <AdvertisementCarousel advertisements={advertisements} />
      )}

      {/* Features Grid */}
      <section className="py-8 bg-white">
        <div className="container mx-auto px-4">
          <div className={`grid grid-cols-1 ${config.modules.ari ? 'md:grid-cols-3' : 'md:grid-cols-2 max-w-4xl mx-auto'} gap-8 text-center`}>

            {/* Feature 1: Inventory */}
            <div className="p-6 border rounded-lg shadow-sm hover:shadow-md transition-shadow">
              <h3 className="text-xl font-bold mb-3">{featInvTitle}</h3>
              <p className="text-gray-600 mb-4 whitespace-pre-wrap">
                {featInvText}
              </p>
              <Link href="/inventory" className="text-blue-600 font-medium hover:underline">
                View Inventory &rarr;
              </Link>
            </div>

            {/* Feature 2: Parts (Conditional) */}
            {config.modules.ari && (
              <div className="p-6 border rounded-lg shadow-sm hover:shadow-md transition-shadow">
                <h3 className="text-xl font-bold mb-3">{featPartsTitle}</h3>
                <p className="text-gray-600 mb-4 whitespace-pre-wrap">
                  {featPartsText}
                </p>
                <Link href="/parts" className="text-blue-600 font-medium hover:underline">
                  Lookup Parts &rarr;
                </Link>
              </div>
            )}

            {/* Feature 3: Service */}
            <div className="p-6 border rounded-lg shadow-sm hover:shadow-md transition-shadow">
              <h3 className="text-xl font-bold mb-3">{featServiceTitle}</h3>
              <p className="text-gray-600 mb-4 whitespace-pre-wrap">
                {featServiceText}
              </p>
              <Link href="/service" className="text-blue-600 font-medium hover:underline">
                Book Appointment &rarr;
              </Link>
            </div>

          </div>
        </div>
      </section>

      {/* Brand Carousel */}
      {(config.theme.brandLogos || config.theme.brand_logos) && Object.keys(config.theme.brandLogos || config.theme.brand_logos || {}).length > 0 && (
        <BrandCarousel logos={config.theme.brandLogos || config.theme.brand_logos} logoUrls={config.theme.brandLogoUrls} />
      )}
    </div>
  );
}
