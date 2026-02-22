import Link from 'next/link';
import { getDealerConfig } from '@/lib/api';
import BrandCarousel from '@/components/BrandCarousel';
import AdvertisementCarousel from '@/components/AdvertisementCarousel';

export default async function Home() {
  const config = await getDealerConfig();
  const primaryColor = config.theme.primaryColor || '#2563EB';

  // Fetch advertisements from API
  let advertisements = [];
  try {
    const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/advertisements`, {
      headers: {
        'Host': config.slug ? `${config.slug}.bentcrankshaft.com` : 'localhost',
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
      <section className="bg-gray-900 text-white py-8">
        <div className="container mx-auto px-4 relative min-h-[300px] flex flex-col justify-center">
          <div className="flex flex-col items-center justify-center w-full">
            {config.theme.hero_show_logo && config.theme.logoUrl && (
              <div className="flex-shrink-0 mb-8 md:mb-0 md:absolute md:left-4 md:top-1/2 md:-translate-y-1/2">
                <img
                  src={config.theme.logoUrl}
                  alt={config.name}
                  className="h-48 md:h-64 w-auto object-contain bg-white/10 p-4 rounded-lg backdrop-blur-sm shadow-xl"
                />
              </div>
            )}
            <div className="flex flex-col items-center text-center max-w-3xl mx-auto z-10 px-4">
              <h1 className="text-4xl md:text-6xl font-bold mb-6 drop-shadow-lg">
                {heroTitle}
              </h1>
              <p className="text-xl md:text-2xl mb-8 text-gray-300 max-w-2xl drop-shadow-md">
                {heroTagline}
              </p>
              <div className="flex flex-col sm:flex-row gap-4 justify-center">
                <Link
                  href="/inventory"
                  className="px-8 py-3 rounded-md font-semibold text-white transition-opacity hover:opacity-90 text-center shadow-lg"
                  style={{ backgroundColor: primaryColor }}
                >
                  Shop Inventory
                </Link>
                <Link
                  href="/service"
                  className="px-8 py-3 rounded-md font-semibold bg-white text-gray-900 hover:bg-gray-100 text-center shadow-lg"
                >
                  Schedule Service
                </Link>
              </div>
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
