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
        'Host': config.slug ? `${config.slug}.bentcrankshaft.com` : 'localhost',
        'X-Dealer-Slug': config.slug || '',
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
      <section className="bg-gradient-to-b from-gray-900 to-gray-800 text-white py-6 md:py-8">
        <div className="container mx-auto px-4 relative min-h-[240px] md:min-h-[280px] flex items-center">
          {/* Logo (Absolute Left Positioning) */}
          {config.theme.hero_show_logo && config.theme.logoUrl && (
            <div className="hidden md:flex absolute left-4 top-1/2 -translate-y-1/2">
              <img
                src={config.theme.logoUrl}
                alt={config.name}
                className="h-48 md:h-64 w-auto object-contain bg-white/10 p-6 rounded-lg backdrop-blur-sm shadow-xl hover:shadow-2xl transition-shadow"
              />
            </div>
          )}

          {/* Mobile Logo - Centered above text */}
          {config.theme.hero_show_logo && config.theme.logoUrl && (
            <div className="md:hidden flex justify-center mb-6 w-full">
              <img
                src={config.theme.logoUrl}
                alt={config.name}
                className="h-40 w-auto object-contain bg-white/10 p-4 rounded-lg backdrop-blur-sm shadow-lg"
              />
            </div>
          )}

          {/* Content - Centered */}
          <div className="flex flex-col items-center text-center w-full z-10">
            <h1 className="text-4xl md:text-5xl font-bold mb-4 drop-shadow-lg leading-tight">
              {heroTitle}
            </h1>
            <p className="text-lg md:text-xl mb-6 text-gray-200 drop-shadow-md">
              {heroTagline}
            </p>
              <div className="flex flex-col sm:flex-row gap-4 justify-center w-full">
                <Link
                  href="/inventory"
                  className="px-10 py-4 rounded-lg font-bold text-lg text-white transition-all hover:shadow-lg transform hover:scale-105 text-center shadow-xl"
                  style={{ backgroundColor: primaryColor }}
                >
                  Shop Inventory
                </Link>
                <Link
                  href="/service"
                  className="px-10 py-4 rounded-lg font-bold text-lg bg-white text-gray-900 hover:bg-gray-100 text-center shadow-xl transition-all hover:shadow-lg transform hover:scale-105"
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
      {config.theme.brand_logos && Object.keys(config.theme.brand_logos).length > 0 && (
        <BrandCarousel logos={Object.values(config.theme.brand_logos)} />
      )}
    </div>
  );
}
