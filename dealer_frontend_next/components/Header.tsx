'use client';

import Link from 'next/link';
import { DealerConfig } from '@/lib/types';
import { useState, useEffect } from 'react';

export default function Header({ config }: { config: DealerConfig }) {
    const primaryColor = config.theme.primaryColor || '#2563EB'; // Default blue
    const [isImpersonating, setIsImpersonating] = useState(false);

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
                <div className="container mx-auto px-4 py-2 flex flex-col lg:flex-row justify-between items-center gap-4">
                    <Link href="/" className="text-2xl font-bold flex items-center mb-2 lg:mb-0 whitespace-nowrap">
                        <span>{config.name}</span>
                    </Link>

                    <nav className="flex space-x-6 overflow-x-auto w-full lg:w-auto pb-2 lg:pb-0 whitespace-nowrap">
                        <Link href="/" className="hover:text-gray-200">Home</Link>
                        <Link href="/inventory" className="hover:text-gray-200">Inventory</Link>
                        <Link href="/parts" className="hover:text-gray-200">Parts</Link>
                        <Link href="/service" className="hover:text-gray-200">Service</Link>
                        <Link href="/contact" className="hover:text-gray-200">Contact</Link>
                    </nav>
                </div>
            </div>
        </header>
    );
}
