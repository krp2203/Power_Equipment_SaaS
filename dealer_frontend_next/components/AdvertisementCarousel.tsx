'use client';

import { useState, useEffect } from 'react';
import { Advertisement } from '@/lib/types';
import AdvertisementModal from './AdvertisementModal';

interface AdvertisementCarouselProps {
  advertisements: Advertisement[];
}

export default function AdvertisementCarousel({
  advertisements,
}: AdvertisementCarouselProps) {
  const [currentIndex, setCurrentIndex] = useState(0);
  const [selectedAd, setSelectedAd] = useState<Advertisement | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);

  // Auto-rotate every 5 seconds
  useEffect(() => {
    if (advertisements.length <= 1) return;

    const interval = setInterval(() => {
      setCurrentIndex((prev) => (prev + 1) % advertisements.length);
    }, 5000);

    return () => clearInterval(interval);
  }, [advertisements.length]);

  if (!advertisements || advertisements.length === 0) {
    return null;
  }

  const currentAd = advertisements[currentIndex];

  const handleThumbnailClick = (ad: Advertisement) => {
    setSelectedAd(ad);
    setIsModalOpen(true);
  };

  const handleNextSlide = () => {
    setCurrentIndex((prev) => (prev + 1) % advertisements.length);
  };

  const handlePrevSlide = () => {
    setCurrentIndex((prev) => (prev - 1 + advertisements.length) % advertisements.length);
  };

  return (
    <>
      {/* Advertisement Carousel - Constrained Width with Border */}
      <div className="w-full bg-white pb-6 pt-2">
        <div className="w-full px-4" style={{ display: 'grid', gridTemplateColumns: '1fr 5fr 1fr', alignItems: 'center', gap: '16px' }}>
          {/* Spacer Left */}
          <div className="hidden md:block"></div>

          {/* Carousel Content - Center Column */}
          <div className="relative group">
            {/* Left Arrow - Positioned locally within center column */}
            {advertisements.length > 1 && (
              <button
                onClick={handlePrevSlide}
                className="absolute left-4 top-1/2 -translate-y-1/2 z-10 p-2 rounded-full bg-gray-900/50 hover:bg-gray-900 text-white transition-all opacity-0 group-hover:opacity-100"
                aria-label="Previous advertisement"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                </svg>
              </button>
            )}

            {/* Ad Container with Border */}
            <div className="flex justify-center w-full border-2 border-gray-300 rounded-xl overflow-hidden shadow-sm hover:shadow-md transition-shadow bg-white">
              <button
                onClick={() => handleThumbnailClick(currentAd)}
                className="w-full flex justify-center focus:outline-none"
              >
                {currentAd.media_type === 'video' ? (
                  <video
                    src={currentAd.image}
                    poster={currentAd.thumbnail}
                    className="h-80 w-auto object-cover hover:opacity-90 transition-opacity"
                    controls={false}
                    preload="none"
                  />
                ) : (
                  <img
                    src={currentAd.thumbnail || currentAd.image}
                    alt={currentAd.title}
                    className="h-80 w-auto object-cover hover:opacity-90 transition-opacity"
                  />
                )}
              </button>
            </div>

            {/* Right Arrow - Positioned locally within center column */}
            {advertisements.length > 1 && (
              <button
                onClick={handleNextSlide}
                className="absolute right-4 top-1/2 -translate-y-1/2 z-10 p-2 rounded-full bg-gray-900/50 hover:bg-gray-900 text-white transition-all opacity-0 group-hover:opacity-100"
                aria-label="Next advertisement"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                </svg>
              </button>
            )}

            {/* Ad Indicators - Compact */}
            {advertisements.length > 1 && (
              <div className="absolute bottom-4 left-1/2 -translate-x-1/2 flex gap-1.5 px-2 py-1 rounded-full bg-black/10 backdrop-blur-sm">
                {advertisements.map((_, index) => (
                  <button
                    key={index}
                    onClick={() => setCurrentIndex(index)}
                    className={`h-1.5 rounded-full transition-all ${index === currentIndex
                      ? 'bg-gray-800 w-4'
                      : 'bg-gray-400 hover:bg-gray-600 w-1.5'
                      }`}
                    aria-label={`Go to ad ${index + 1}`}
                  />
                ))}
              </div>
            )}
          </div>

          {/* Spacer Right */}
          <div className="hidden md:block"></div>
        </div>
      </div>

      {/* Modal */}
      <AdvertisementModal
        advertisement={selectedAd}
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
      />
    </>
  );
}
