import Link from 'next/link';
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
    const response = await fetch(`http://web:5000/api/v1/advertisements?slug=${config.slug}`, {
      headers: {
        'X-Dealer-Slug': config.slug || '',
        'X-Environment': 'local',  // Tell backend we're in test environment
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
      {/* Hero Section */}
      <section className="mt-2 mb-4">
        <div className="hidden md:flex container mx-auto px-4 items-center gap-0 bg-gradient-to-b from-gray-900 to-gray-800 text-white py-2 md:py-3 rounded-xl shadow-lg">
          {/* Logo (Left) - stays left justified */}
          {config.theme.hero_show_logo && config.theme.logoUrl && (
            <div className="flex-shrink-0">
              <img
                src={config.theme.logoUrl}
                alt={config.name}
                className="h-40 w-auto object-contain bg-white/10 p-1 rounded-lg backdrop-blur-sm shadow-lg hover:shadow-xl transition-shadow"
              />
            </div>
          )}

          {/* Left Gap with Inventory Button centered */}
          <div className="flex-1 flex items-center justify-center">
            <Link
              href="/inventory"
              className="px-8 py-4 rounded-lg font-bold text-base text-white transition-all hover:shadow-lg transform hover:scale-105 shadow-lg whitespace-nowrap"
              style={{ backgroundColor: primaryColor }}
            >
              Shop Inventory
            </Link>
          </div>

          {/* Center Content - Title and Tagline */}
          <div className="flex-1 flex flex-col items-center text-center">
            <h1 className="text-3xl md:text-4xl font-bold mb-2 drop-shadow-lg leading-tight">
              {heroTitle}
            </h1>
            <p className="text-base md:text-lg text-gray-200 drop-shadow-md">
              {heroTagline}
            </p>
          </div>

          {/* Right Gap with Service Button centered (mirrors left) */}
          <div className="flex-1 flex items-center justify-center">
            <Link
              href="/service"
              className="px-8 py-4 rounded-lg font-bold text-base bg-white text-gray-900 hover:bg-gray-100 shadow-lg transition-all hover:shadow-lg transform hover:scale-105 whitespace-nowrap"
            >
              Schedule Service
            </Link>
          </div>
        </div>

        {/* Mobile Layout: Stacked */}
        <div className="md:hidden container mx-auto px-4 flex flex-col items-center gap-4 py-6">
          {/* Mobile Logo */}
          {config.theme.hero_show_logo && config.theme.logoUrl && (
            <img
              src={config.theme.logoUrl}
              alt={config.name}
              className="h-40 w-auto object-contain bg-white/10 p-4 rounded-lg backdrop-blur-sm shadow-lg"
            />
          )}

          {/* Mobile Content */}
          <div className="flex flex-col items-center text-center">
            <h1 className="text-3xl font-bold mb-2 drop-shadow-lg leading-tight">
              {heroTitle}
            </h1>
            <p className="text-sm mb-4 text-gray-200 drop-shadow-md">
              {heroTagline}
            </p>
            <div className="flex flex-col gap-2 w-full">
              <Link
                href="/inventory"
                className="px-6 py-2 rounded-lg font-bold text-sm text-white transition-all hover:shadow-lg text-center shadow-lg"
                style={{ backgroundColor: primaryColor }}
              >
                Shop Inventory
              </Link>
              <Link
                href="/service"
                className="px-6 py-2 rounded-lg font-bold text-sm bg-white text-gray-900 hover:bg-gray-100 text-center shadow-lg transition-all hover:shadow-lg"
              >
                Schedule Service
              </Link>
            </div>
          </div>
        </div>
      </section>

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
