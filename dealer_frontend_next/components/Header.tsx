'use client';

import Link from 'next/link';
import { DealerConfig } from '@/lib/types';
import { useState, useEffect } from 'react';

export default function Header({ config, heroTitle, heroTagline }: { config: DealerConfig; heroTitle?: string; heroTagline?: string }) {
    const primaryColor = config.theme.primaryColor || '#2563EB'; // Default blue
    const [isImpersonating, setIsImpersonating] = useState(false);

    const displayHeroTitle = heroTitle || config.theme.hero_title || `Welcome to ${config.name}`;
    const displayHeroTagline = heroTagline || config.theme.hero_tagline || "Your Premium Destination for Power Equipment, Parts, and Service.";

    useEffect(() => {
        const cookies = document.cookie.split('; ');
        const isImp = cookies.some(c => c.startsWith('is_impersonating=true'));
        setIsImpersonating(isImp);
    }, []);

    const handleExitImpersonation = async () => {
        try {
            const res = await fetch('/api/v1/super_admin/exit_impersonation', {
                method: 'POST',
                credentials: 'include',
            });
            if (res.ok) {
                window.location.href = '/marketing/dashboard';
            } else {
                const data = await res.json();
                console.error('Failed to exit impersonation:', data.message);
                alert('Error exiting impersonation: ' + data.message);
            }
        } catch (err) {
            console.error('Failed to exit impersonation:', err);
        }
    };

    return (
        <header className="flex flex-col shadow-md">
            {isImpersonating && (
                <div className="bg-yellow-100 border-b border-yellow-200 px-4 py-2 flex justify-between items-center text-sm">
                    <div className="flex items-center space-x-4">
                        <span className="text-yellow-800 font-medium">
                            Viewing site as administrator
                        </span>
                        <a
                            href="/marketing/dashboard"
                            className="text-blue-600 hover:text-blue-800 underline font-medium"
                        >
                            Open Backend Dashboard
                        </a>
                    </div>
                    <button
                        onClick={handleExitImpersonation}
                        className="bg-yellow-800 text-white px-3 py-1 rounded hover:bg-yellow-900 transition-colors"
                    >
                        Exit Impersonation
                    </button>
                </div>
            )}
            <div className="text-white w-full" style={{ backgroundColor: primaryColor }}>
                <div className="w-full px-4 py-1" style={{ display: 'grid', gridTemplateColumns: '1fr 5fr 1fr', alignItems: 'center', gap: '16px', minHeight: '170px' }}>
                    {/* Logo Section - Left Column */}
                    <div className="flex items-center justify-start">
                        {config.theme.hero_show_logo && config.theme.logoUrl && (
                            <img
                                src={config.theme.logoUrl}
                                alt={config.name}
                                className="h-40 w-auto object-contain"
                            />
                        )}
                    </div>

                    {/* Hero Section - Center Column */}
                    <div className="flex items-center justify-center w-full">
                        <div className="bg-gradient-to-b from-gray-900 to-gray-800 rounded-lg px-12 py-8 shadow-lg flex items-center justify-center w-full" style={{ minHeight: '160px', maxHeight: '160px' }}>
                            {/* Center Content - Text naturally centered in middle column */}
                            <div className="flex flex-col items-center text-center">
                                <h2 className="text-4xl font-bold drop-shadow-lg leading-tight text-white">
                                    {displayHeroTitle}
                                </h2>
                                <p className="text-xl text-gray-200 drop-shadow-md hidden md:block">
                                    {displayHeroTagline}
                                </p>
                            </div>
                        </div>
                    </div>

                    {/* Buttons - Right Column */}
                    <div className="flex flex-col gap-3 justify-center items-end w-full h-full">
                        <button
                            onClick={() => window.location.href = '/inventory'}
                            className="px-8 py-4 rounded-lg font-bold text-lg text-gray-900 transition-all hover:shadow-lg transform hover:scale-105 shadow-lg bg-white hover:bg-gray-100 w-full whitespace-nowrap"
                        >
                            Shop Inventory
                        </button>
                        <button
                            onClick={() => window.location.href = '/service'}
                            className="px-8 py-4 rounded-lg font-bold text-lg bg-white text-gray-900 hover:bg-gray-100 shadow-lg transition-all hover:shadow-lg transform hover:scale-105 w-full whitespace-nowrap"
                        >
                            Schedule Service
                        </button>
                    </div>
                </div>
            </div>
        </header>
    );
}
