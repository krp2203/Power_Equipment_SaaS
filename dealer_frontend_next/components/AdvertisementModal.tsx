'use client';

import { Advertisement } from '@/lib/types';

interface AdvertisementModalProps {
  advertisement: Advertisement | null;
  isOpen: boolean;
  onClose: () => void;
}

export default function AdvertisementModal({
  advertisement,
  isOpen,
  onClose,
}: AdvertisementModalProps) {
  if (!isOpen || !advertisement) {
    return null;
  }

  return (
    <div
      className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4 overflow-y-auto"
      onClick={onClose}
    >
      <div
        className="bg-white rounded-lg shadow-2xl w-full max-w-[90vw] h-auto overflow-hidden my-auto relative"
        onClick={(e) => e.stopPropagation()}
        style={{
          maxHeight: '90vh',
          display: 'flex',
          flexDirection: 'column',
        }}
      >
        {/* Close Button */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 z-10 bg-gray-800 hover:bg-gray-900 text-white rounded-full p-2 transition-colors shadow-lg"
          aria-label="Close modal"
        >
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>

        {/* Media - Image or Video - Auto-sizing container */}
        <div
          className="bg-gray-900 flex items-center justify-center overflow-hidden"
          style={{
            flex: '1 1 auto',
            maxHeight: '60vh',
            minHeight: '300px',
          }}
        >
          {advertisement.media_type === 'video' ? (
            <video
              src={advertisement.image}
              poster={advertisement.thumbnail}
              className="w-full h-full object-contain"
              controls={true}
              autoPlay={true}
            />
          ) : (
            <img
              src={advertisement.image}
              alt={advertisement.title}
              className="w-full h-full object-contain"
            />
          )}
        </div>

        {/* Content - Scrollable if needed */}
        <div
          className="p-6 bg-white overflow-y-auto"
          style={{
            flex: '0 1 auto',
            maxHeight: '30vh',
          }}
        >
          <h2 className="text-2xl font-bold mb-2">{advertisement.title}</h2>
          <p className="text-gray-600 mb-4">{advertisement.description}</p>

          {/* Link Button */}
          {advertisement.link_url && (
            <a
              href={advertisement.link_url}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-block px-6 py-2 bg-blue-600 text-white rounded-md font-semibold hover:bg-blue-700 transition-colors"
            >
              Learn More →
            </a>
          )}
        </div>
      </div>
    </div>
  );
}
