'use client';

import { useEffect, useState } from 'react';

interface BrandLogoItem {
    id: string | number;
    logo: string;
    url?: string;
}

interface BrandCarouselProps {
    logos?: string[] | Record<string, string>; // Support old format (array) and new format (object)
    logoUrls?: Record<string, string>; // Separate URLs for each logo
}

export default function BrandCarousel({ logos, logoUrls }: BrandCarouselProps) {
    // If no logos, don't render anything
    if (!logos || (Array.isArray(logos) && logos.length === 0) || (typeof logos === 'object' && !Array.isArray(logos) && Object.keys(logos).length === 0)) {
        return null;
    }

    // Convert logos to array of objects with URL support
    let brandItems: BrandLogoItem[] = [];

    if (Array.isArray(logos)) {
        // Old format: array of URLs
        brandItems = logos.map((logo, index) => ({
            id: index,
            logo,
            url: undefined,
        }));
    } else if (typeof logos === 'object') {
        // New format: object with index keys
        brandItems = Object.entries(logos).map(([id, logo]) => ({
            id,
            logo,
            url: logoUrls?.[id],
        }));
    }

    const handleLogoClick = (url?: string) => {
        if (url) {
            window.open(url, '_blank', 'noopener,noreferrer');
        }
    };

    return (
        <section className="py-8 bg-white overflow-hidden border-t border-gray-100">
            <div className="container mx-auto px-4 mb-6 text-center">
                <h3 className="text-xl font-semibold text-gray-400 uppercase tracking-widest">Our Brands</h3>
            </div>

            <div className="relative w-full overflow-hidden">
                {/* Gradient Masks */}
                <div className="absolute top-0 left-0 w-32 h-full bg-gradient-to-r from-white to-transparent z-10"></div>
                <div className="absolute top-0 right-0 w-32 h-full bg-gradient-to-l from-white to-transparent z-10"></div>

                {/* Scrolling Track */}
                <div className="flex gap-16 animate-scroll whitespace-nowrap py-4">
                    {/* Double the logos to create seamless loop */}
                    {[...brandItems, ...brandItems].map((item, index) => (
                        <button
                            key={index}
                            onClick={() => handleLogoClick(item.url)}
                            className="flex-shrink-0 h-16 w-32 flex items-center justify-center grayscale hover:grayscale-0 transition-all duration-300 opacity-60 hover:opacity-100"
                            style={{ cursor: item.url ? 'pointer' : 'default' }}
                            title={item.url ? 'Click to visit' : ''}
                        >
                            <img
                                src={item.logo}
                                alt={`Brand ${item.id}`}
                                className="h-full w-full object-contain"
                            />
                        </button>
                    ))}
                </div>
            </div>

            <style jsx>{`
                @keyframes scroll {
                    0% { transform: translateX(0); }
                    100% { transform: translateX(-50%); }
                }
                .animate-scroll {
                    animation: scroll 30s linear infinite;
                }
                .animate-scroll:hover {
                    animation-play-state: paused;
                }
            `}</style>
        </section>
    );
}
