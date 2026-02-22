"use client";

import { useEffect, useState, use } from 'react';
import { InventoryItem, DealerConfig } from '@/lib/types';
import Link from 'next/link';

export default function InventoryDetailPage({ params }: { params: Promise<{ id: string }> }) {
    const { id } = use(params);
    const [item, setItem] = useState<InventoryItem | null>(null);
    const [config, setConfig] = useState<DealerConfig | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        // Fetch Unit Details
        fetch(`/api/v1/inventory/${id}`)
            .then(res => {
                if (!res.ok) throw new Error('Unit not found');
                return res.json();
            })
            .then(data => {
                setItem(data);
                setLoading(false);
            })
            .catch(err => {
                console.error("Failed to load unit", err);
                setError(err.message);
                setLoading(false);
            });

        // Fetch Site Info for Contact Info
        fetch('/api/v1/site-info')
            .then(res => res.json())
            .then(data => {
                // Quick adaptation
                const adapted: DealerConfig = {
                    name: data.identity?.name,
                    slug: data.identity?.slug,
                    modules: {},
                    theme: {
                        contact_email: data.theme?.contact_email,
                        contact_phone: data.theme?.contact_phone
                    }
                };
                setConfig(adapted);
            })
            .catch(err => console.error("Failed to load site info", err));
    }, [id]);

    if (loading) return <div className="p-8 text-center text-gray-500">Loading Unit Details...</div>;
    if (error || !item) return (
        <div className="p-8 text-center">
            <h2 className="text-2xl font-bold text-red-600 mb-4">Unit Not Found</h2>
            <Link href="/inventory" className="text-blue-600 hover:underline">
                &larr; Back to Inventory
            </Link>
        </div>
    );

    const contactPhone = config?.theme?.contact_phone || '1-800-000-0000';
    const phoneLink = `tel:${contactPhone.replace(/\D/g, '')}`;

    return (
        <div className="container mx-auto px-4 py-8">
            <div className="mb-6">
                <Link href="/inventory" className="text-gray-500 hover:text-gray-900 font-medium">
                    &larr; Back to Inventory
                </Link>
            </div>

            <div className="bg-white rounded-xl shadow-lg overflow-hidden border">
                <div className="grid grid-cols-1 md:grid-cols-2">
                    {/* Image Section */}
                    <div className="bg-gray-100 p-4 flex items-center justify-center min-h-[400px]">
                        {item.image ? (
                            <img
                                src={item.image}
                                alt={item.name}
                                className="max-w-full max-h-[600px] object-contain rounded shadow-sm"
                            />
                        ) : (
                            <div className="text-gray-400 flex flex-col items-center">
                                <span className="text-6xl mb-4">📷</span>
                                <span>No Image Available</span>
                            </div>
                        )}
                    </div>

                    {/* Details Section */}
                    <div className="p-8 flex flex-col">
                        <div className="mb-6">
                            <h1 className="text-4xl font-bold text-gray-900 mb-2">{item.name}</h1>
                            <div className="flex items-center gap-3 mb-4">
                                <span className={`px-3 py-1 rounded-full text-sm font-bold uppercase text-white ${item.status === 'Sold' ? 'bg-red-500' : 'bg-green-600'}`}>
                                    {item.status}
                                </span>
                                <span className="text-gray-500 text-sm">Stock #{item.id}</span>
                            </div>
                            <div className="text-4xl font-bold text-blue-600 mb-4">
                                {item.price > 0 ? `$${item.price.toLocaleString()}` : 'Call for Price'}
                            </div>
                        </div>

                        <div className="prose max-w-none text-gray-600 mb-8 border-t pt-6">
                            <h3 className="text-lg font-semibold text-gray-900 mb-2">Description</h3>
                            <p className="whitespace-pre-wrap">{item.description || "No description available."}</p>
                        </div>

                        <div className="grid grid-cols-2 gap-4 bg-gray-50 p-6 rounded-lg mb-8">
                            <div>
                                <span className="block text-xs font-bold text-gray-400 uppercase">Make</span>
                                <span className="font-medium">{item.manufacturer}</span>
                            </div>
                            <div>
                                <span className="block text-xs font-bold text-gray-400 uppercase">Model</span>
                                <span className="font-medium">{item.model_number}</span>
                            </div>
                            <div>
                                <span className="block text-xs font-bold text-gray-400 uppercase">Year</span>
                                <span className="font-medium">{item.year || 'N/A'}</span>
                            </div>
                            <div>
                                <span className="block text-xs font-bold text-gray-400 uppercase">Condition</span>
                                <span className="font-medium">{item.condition}</span>
                            </div>
                            {item.unit_hours && (
                                <div>
                                    <span className="block text-xs font-bold text-gray-400 uppercase">Hours</span>
                                    <span className="font-medium">{item.unit_hours}</span>
                                </div>
                            )}
                            {item.serial_number && (
                                <div>
                                    <span className="block text-xs font-bold text-gray-400 uppercase">Serial</span>
                                    <span className="font-medium text-sm text-gray-600">{item.serial_number}</span>
                                </div>
                            )}
                        </div>

                        <div className="mt-auto">
                            <a
                                href={phoneLink}
                                className="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-4 rounded-lg shadow-lg transition-transform active:scale-[0.98] text-center block"
                            >
                                📞 Call Us About This Unit
                            </a>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
