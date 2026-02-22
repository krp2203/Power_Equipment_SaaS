'use client';

import { useEffect, useState } from 'react';

interface BrandCarouselProps {
    logos: string[];
}

export default function BrandCarousel({ logos }: BrandCarouselProps) {
    // If no logos, don't render anything
    if (!logos || logos.length === 0) return null;

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
                    {[...logos, ...logos].map((logo, index) => (
                        <div key={index} className="flex-shrink-0 h-16 w-32 flex items-center justify-center grayscale hover:grayscale-0 transition-all duration-300 opacity-60 hover:opacity-100">
                            <img
                                src={logo}
                                alt={`Brand ${index}`}
                                className="h-full w-full object-contain"
                            />
                        </div>
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
