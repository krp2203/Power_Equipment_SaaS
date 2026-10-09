'use client';

import { useEffect, useState } from 'react';
import { DealerConfig, CatalogBrandSummary } from '@/lib/types';

export default function Footer({ config }: { config: DealerConfig }) {
    const primaryColor = config.theme.primaryColor || '#2563EB';
    const [brands, setBrands] = useState<CatalogBrandSummary[]>([]);

    useEffect(() => {
        fetch('/api/v1/manufacturer-catalog/brands')
            .then(res => res.json())
            .then(setBrands)
            .catch(() => setBrands([]));
    }, []);

    return (
        <footer className="bg-gray-800 text-white mt-auto">
            <div className="container mx-auto px-4 py-8">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
                    <div>
                        <h3 className="text-xl font-bold mb-4">{config.name}</h3>
                        <p className="text-gray-400 mb-4">Your trusted power equipment dealer.</p>
                        {config.modules.facebook && config.facebook_page_id && (
                            <a
                                href={`https://facebook.com/${config.facebook_page_id}`}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="inline-flex items-center text-blue-400 hover:text-blue-300 transition-colors"
                            >
                                <svg className="w-6 h-6 mr-2" fill="currentColor" viewBox="0 0 24 24">
                                    <path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z" />
                                </svg>
                                Follow us on Facebook
                            </a>
                        )}
                    </div>
                    <div>
                        <h3 className="text-lg font-semibold mb-4 text-gray-300">Quick Links</h3>
                        <ul className="space-y-2 text-gray-400">
                            <li><a href="/inventory" className="hover:text-white">New Inventory</a></li>
                            <li><a href="/parts" className="hover:text-white">Parts</a></li>
                            <li><a href="/service" className="hover:text-white">Service Department</a></li>
                            {brands.map(b => (
                                <li key={b.slug}>
                                    <a href={`/brands/${b.slug}`} className="hover:text-white">{b.name}</a>
                                </li>
                            ))}
                            <li><hr className="border-gray-700 my-2" /></li>
                            <li><a href="/marketing/dashboard" target="_blank" rel="noopener noreferrer" className="hover:text-white text-xs opacity-50">Dealer Portal</a></li>
                        </ul>
                    </div>
                    <div id="contact">
                        <h3 className="text-lg font-semibold mb-4 text-gray-300">Contact</h3>
                        <ul className="space-y-1 text-gray-400">
                            {config.theme.contact_phone && (
                                <li>
                                    <a href={`tel:${config.theme.contact_phone.replace(/\D/g, '')}`} className="hover:text-white">
                                        {config.theme.contact_phone}
                                    </a>
                                </li>
                            )}
                            {config.theme.contact_email && (
                                <li>
                                    <a href={`mailto:${config.theme.contact_email}`} className="hover:text-white">
                                        {config.theme.contact_email}
                                    </a>
                                </li>
                            )}
                            <li className="whitespace-pre-wrap">{config.theme.contact_address || 'Contact us for more information'}</li>
                        </ul>
                    </div>
                </div>
                <div className="border-t border-gray-700 mt-8 pt-4 text-center text-sm text-gray-500">
                    &copy; {new Date().getFullYear()} {config.name}. Powered by bentcrankshaft.com
                </div>
            </div>
        </footer>
    );
}
