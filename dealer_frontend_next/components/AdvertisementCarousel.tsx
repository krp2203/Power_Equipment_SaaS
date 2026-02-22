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
      {/* Advertisement Carousel - Single Ad at a Time */}
      <div className="w-full bg-gray-100 py-16 px-4">
        <div className="container mx-auto flex justify-center relative">
          {/* Left Arrow */}
          {advertisements.length > 1 && (
            <button
              onClick={handlePrevSlide}
              className="absolute left-0 top-1/2 -translate-y-1/2 z-10 p-3 rounded-full bg-gray-800 hover:bg-gray-900 text-white transition-colors"
              aria-label="Previous advertisement"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
              </svg>
            </button>
          )}

          {/* Current Ad - Centered */}
          <div className="flex justify-center max-w-5xl">
            <button
              onClick={() => handleThumbnailClick(currentAd)}
              className="overflow-hidden rounded-lg hover:shadow-lg transition-shadow"
            >
              <img
                src={currentAd.thumbnail || currentAd.image}
                alt={currentAd.title}
                className="h-96 w-auto object-cover hover:opacity-80 transition-opacity"
              />
            </button>
          </div>

          {/* Right Arrow */}
          {advertisements.length > 1 && (
            <button
              onClick={handleNextSlide}
              className="absolute right-0 top-1/2 -translate-y-1/2 z-10 p-3 rounded-full bg-gray-800 hover:bg-gray-900 text-white transition-colors"
              aria-label="Next advertisement"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
            </button>
          )}

          {/* Ad Indicators */}
          {advertisements.length > 1 && (
            <div className="absolute bottom-0 left-1/2 -translate-x-1/2 flex gap-2">
              {advertisements.map((_, index) => (
                <button
                  key={index}
                  onClick={() => setCurrentIndex(index)}
                  className={`h-2 w-2 rounded-full transition-all ${
                    index === currentIndex
                      ? 'bg-gray-800 w-6'
                      : 'bg-gray-400 hover:bg-gray-600'
                  }`}
                  aria-label={`Go to ad ${index + 1}`}
                />
              ))}
            </div>
          )}
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
