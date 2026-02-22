"use client";

import { useEffect, useState } from 'react';
import { InventoryItem } from '@/lib/types';
import Link from 'next/link';

export default function InventoryPage() {
    const [items, setItems] = useState<InventoryItem[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        // Fetch from relative path (Proxied by Next.js)
        fetch('/api/v1/inventory')
            .then(res => res.json())
            .then(data => {
                setItems(data);
                setLoading(false);
            })
            .catch(err => {
                console.error("Failed to load inventory", err);
                setLoading(false);
            });
    }, []);

    if (loading) return <div>Loading Inventory...</div>;

    return (
        <div>
            <h1 className="text-3xl font-bold mb-6">New Inventory</h1>
            {items.length === 0 ? (
                <div className="text-center py-12 bg-gray-50 rounded-lg">
                    <p className="text-gray-500 text-lg">No inventory currently available. Please check back soon.</p>
                </div>
            ) : (
                <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
                    {items.map(item => (
                        <div key={item.id} className="border rounded-lg bg-white shadow-sm overflow-hidden hover:shadow-md transition-shadow flex flex-col">
                            {/* Image Aspect Ratio Container 4:3 */}
                            <div className="relative aspect-[4/3] bg-gray-100 border-b">
                                {item.image ? (
                                    <img
                                        src={item.image}
                                        alt={item.name}
                                        className="object-cover w-full h-full"
                                    />
                                ) : (
                                    <div className="flex items-center justify-center h-full text-gray-400">
                                        <span>No Image</span>
                                    </div>
                                )}
                                <div className="absolute top-2 right-2 flex flex-col gap-2 items-end">
                                    {item.status !== 'Available' && (
                                        <span className={`px-2 py-1 rounded text-[10px] font-bold uppercase text-white ${item.status === 'Sold' ? 'bg-red-500' : 'bg-yellow-500'}`}>
                                            {item.status}
                                        </span>
                                    )}
                                    <span className={`px-2 py-1 rounded text-[10px] font-bold uppercase text-white ${item.condition === 'Used' ? 'bg-amber-600' : 'bg-blue-600'}`}>
                                        {item.condition || 'New'}
                                    </span>
                                </div>
                            </div>

                            <div className="p-4 flex flex-col flex-grow">
                                <h2 className="text-xl font-bold mb-2 line-clamp-2">{item.name}</h2>
                                {item.description && (
                                    <p className="text-gray-600 mb-4 text-sm line-clamp-3 flex-grow">
                                        {item.description}
                                    </p>
                                )}

                                <div className="mt-auto pt-4 border-t flex justify-between items-center">
                                    <span className="text-2xl font-bold text-green-700">
                                        {item.price > 0 ? `$${item.price.toLocaleString()}` : 'Call for Price'}
                                    </span>
                                    <Link
                                        href={`/inventory/${item.id}`}
                                        className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded text-sm font-semibold transition-colors"
                                    >
                                        View Details
                                    </Link>
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}
