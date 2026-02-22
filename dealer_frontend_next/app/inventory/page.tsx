"use client";

import { useEffect, useState } from 'react';
import { InventoryItem } from '@/lib/types';
import Link from 'next/link';

export default function InventoryPage() {
    const [items, setItems] = useState<InventoryItem[]>([]);
    const [loading, setLoading] = useState(true);
    const [filterOptions, setFilterOptions] = useState<{ manufacturers: string[], types: string[] }>({ manufacturers: [], types: [] });

    // Filter State
    const [filterType, setFilterType] = useState('manufacturer'); // 'manufacturer' or 'type'
    const [filterValue, setFilterValue] = useState('');
    const [sortBy, setSortBy] = useState('price');
    const [sortOrder, setSortOrder] = useState('desc');

    useEffect(() => {
        // Fetch Filter Options
        fetch('/api/v1/inventory/filters')
            .then(res => res.json())
            .then(data => setFilterOptions(data))
            .catch(err => console.error("Failed to load filters", err));
    }, []);

    useEffect(() => {
        setLoading(true);
        const params = new URLSearchParams();
        if (filterValue) {
            params.append(filterType, filterValue);
        }
        params.append('sort', sortBy);
        params.append('order', sortOrder);

        fetch(`/api/v1/inventory?${params.toString()}`)
            .then(res => res.json())
            .then(data => {
                setItems(data);
                setLoading(false);
            })
            .catch(err => {
                console.error("Failed to load inventory", err);
                setLoading(false);
            });
    }, [filterType, filterValue, sortBy, sortOrder]);

    const handleFilterTypeChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
        setFilterType(e.target.value);
        setFilterValue(''); // Reset value when type changes
    };

    return (
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
            <h1 className="text-4xl font-extrabold text-gray-900 mb-8 border-b pb-4">New Inventory</h1>

            {/* Filter Bar */}
            <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100 mb-10">
                <div className="grid grid-cols-1 md:grid-cols-4 gap-6 items-end">
                    {/* Select Filter Category */}
                    <div>
                        <label className="block text-sm font-semibold text-gray-700 mb-2">Filter By</label>
                        <select
                            value={filterType}
                            onChange={handleFilterTypeChange}
                            className="w-full h-12 rounded-xl border-gray-200 bg-gray-50 focus:ring-2 focus:ring-blue-500 focus:bg-white transition-all text-gray-900"
                        >
                            <option value="manufacturer">Manufacturer</option>
                            <option value="type">Unit Type</option>
                        </select>
                    </div>

                    {/* Select Value */}
                    <div>
                        <label className="block text-sm font-semibold text-gray-700 mb-2">
                            Select {filterType === 'manufacturer' ? 'Manufacturer' : 'Type'}
                        </label>
                        <select
                            value={filterValue}
                            onChange={(e) => setFilterValue(e.target.value)}
                            className="w-full h-12 rounded-xl border-gray-200 bg-gray-50 focus:ring-2 focus:ring-blue-500 focus:bg-white transition-all text-gray-900"
                        >
                            <option value="">All {filterType === 'manufacturer' ? 'Manufacturers' : 'Equipment'}</option>
                            {(filterType === 'manufacturer' ? filterOptions.manufacturers : filterOptions.types).map(opt => (
                                <option key={opt} value={opt}>{opt}</option>
                            ))}
                        </select>
                    </div>

                    {/* Sort By */}
                    <div>
                        <label className="block text-sm font-semibold text-gray-700 mb-2">Sort By</label>
                        <select
                            value={`${sortBy}-${sortOrder}`}
                            onChange={(e) => {
                                const [s, o] = e.target.value.split('-');
                                setSortBy(s);
                                setSortOrder(o);
                            }}
                            className="w-full h-12 rounded-xl border-gray-200 bg-gray-50 focus:ring-2 focus:ring-blue-500 focus:bg-white transition-all text-gray-900"
                        >
                            <option value="price-desc">Price: High to Low</option>
                            <option value="price-asc">Price: Low to High</option>
                            <option value="year-desc">Year: Newest First</option>
                            <option value="year-asc">Year: Oldest First</option>
                            <option value="manufacturer-asc">Manufacturer: A-Z</option>
                        </select>
                    </div>

                    {/* Results Count/Clear */}
                    <div className="flex items-center justify-between md:justify-end gap-4 h-12">
                        <span className="text-sm text-gray-500 font-medium">
                            {loading ? '...' : items.length} Units Found
                        </span>
                        {filterValue && (
                            <button
                                onClick={() => setFilterValue('')}
                                className="text-sm font-bold text-blue-600 hover:text-blue-800"
                            >
                                Clear Filters X
                            </button>
                        )}
                    </div>
                </div>
            </div>

            {loading ? (
                <div className="flex justify-center py-20">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
                </div>
            ) : items.length === 0 ? (
                <div className="text-center py-24 bg-gray-50 rounded-3xl border-2 border-dashed border-gray-200">
                    <p className="text-gray-500 text-xl font-medium">No results match your current filters.</p>
                    <button
                        onClick={() => { setFilterValue(''); setFilterType('manufacturer'); }}
                        className="mt-4 text-blue-600 font-bold underline"
                    >
                        View all inventory
                    </button>
                </div>
            ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-10">
                    {items.map(item => (
                        <div key={item.id} className="group border border-gray-100 rounded-3xl bg-white shadow-sm overflow-hidden hover:shadow-xl transition-all duration-300 flex flex-col transform hover:-translate-y-1">
                            {/* Image Aspect Ratio Container 4:3 */}
                            <div className="relative aspect-[4/3] bg-gray-50 border-b overflow-hidden">
                                {item.image ? (
                                    <img
                                        src={item.image}
                                        alt={item.name}
                                        className="object-cover w-full h-full group-hover:scale-110 transition-transform duration-500"
                                    />
                                ) : (
                                    <div className="flex items-center justify-center h-full text-gray-300">
                                        <i className="bi bi-image text-4xl"></i>
                                    </div>
                                )}
                                <div className="absolute top-4 right-4 flex flex-col gap-2 items-end">
                                    {item.status !== 'Available' && (
                                        <span className={`px-3 py-1 rounded-full text-[12px] font-bold uppercase text-white shadow-sm ${item.status === 'Sold' ? 'bg-red-500' : 'bg-orange-500'}`}>
                                            {item.status}
                                        </span>
                                    )}
                                    <span className={`px-3 py-1 rounded-full text-[12px] font-bold uppercase text-white shadow-sm ${item.condition === 'Used' ? 'bg-amber-600' : 'bg-blue-600'}`}>
                                        {item.condition || 'New'}
                                    </span>
                                </div>
                                {item.type && (
                                    <div className="absolute bottom-4 left-4">
                                        <span className="bg-black/60 backdrop-blur-md text-white px-3 py-1 rounded-lg text-xs font-semibold">
                                            {item.type}
                                        </span>
                                    </div>
                                )}
                            </div>

                            <div className="p-6 flex flex-col flex-grow">
                                <div className="mb-2">
                                    <span className="text-xs font-bold text-blue-600 uppercase tracking-widest">{item.manufacturer}</span>
                                </div>
                                <h2 className="text-2xl font-bold mb-3 text-gray-900 group-hover:text-blue-600 transition-colors line-clamp-2 leading-tight">
                                    {item.name}
                                </h2>

                                {item.description && (
                                    <p className="text-gray-500 mb-6 text-sm line-clamp-2 flex-grow leading-relaxed">
                                        {item.description}
                                    </p>
                                )}

                                <div className="mt-auto pt-6 border-t border-gray-50 flex justify-between items-center">
                                    <div className="flex flex-col">
                                        <span className="text-xs text-gray-400 font-bold uppercase">Price</span>
                                        <span className="text-2xl font-black text-gray-900">
                                            {item.price > 0 ? `$${item.price.toLocaleString()}` : 'Call for Price'}
                                        </span>
                                    </div>
                                    <Link
                                        href={`/inventory/${item.id}`}
                                        className="bg-gray-900 hover:bg-blue-600 text-white px-6 py-3 rounded-2xl text-sm font-bold transition-all duration-300 shadow-lg hover:shadow-blue-200"
                                    >
                                        Details
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
