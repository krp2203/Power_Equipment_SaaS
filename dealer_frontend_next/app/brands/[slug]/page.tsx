"use client";

import { useEffect, useState, use } from 'react';
import { CatalogBrandDetail, CatalogItem } from '@/lib/types';
import Link from 'next/link';
import RequestQuoteForm from '@/components/RequestQuoteForm';

export default function BrandCatalogPage({ params }: { params: Promise<{ slug: string }> }) {
    const { slug } = use(params);
    const [data, setData] = useState<CatalogBrandDetail | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [quoteItem, setQuoteItem] = useState<CatalogItem | null>(null);
    const [categoryFilter, setCategoryFilter] = useState<string>('');

    useEffect(() => {
        fetch(`/api/v1/manufacturer-catalog/${slug}`)
            .then(res => {
                if (!res.ok) throw new Error('Brand not found');
                return res.json();
            })
            .then(setData)
            .catch(err => setError(err.message))
            .finally(() => setLoading(false));
    }, [slug]);

    if (loading) return <div className="p-8 text-center text-gray-500">Loading...</div>;
    if (error || !data) return (
        <div className="p-8 text-center">
            <h2 className="text-2xl font-bold text-red-600 mb-4">Brand Not Found</h2>
            <Link href="/inventory" className="text-blue-600 hover:underline">&larr; Back to Inventory</Link>
        </div>
    );

    const { brand, items } = data;

    // Group by category, preserving first-seen order; uncategorized last.
    const groups = new Map<string, CatalogItem[]>();
    for (const item of items) {
        const key = item.category || 'Other';
        if (!groups.has(key)) groups.set(key, []);
        groups.get(key)!.push(item);
    }
    const orderedGroups = [...groups.entries()].sort((a, b) => {
        if (a[0] === 'Other') return 1;
        if (b[0] === 'Other') return -1;
        return a[0].localeCompare(b[0]);
    });
    const visibleGroups = categoryFilter
        ? orderedGroups.filter(([category]) => category === categoryFilter)
        : orderedGroups;

    return (
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
            <div className="text-center mb-12">
                {brand.logo_url && (
                    <img src={brand.logo_url} alt={brand.name} className="h-20 mx-auto mb-4 object-contain" />
                )}
                <h1 className="text-4xl font-extrabold text-gray-900">{brand.name}</h1>
                {brand.intro_text && (
                    <p className="text-gray-500 max-w-2xl mx-auto mt-3">{brand.intro_text}</p>
                )}
            </div>

            {items.length === 0 ? (
                <div className="text-center py-24 bg-gray-50 rounded-3xl border-2 border-dashed border-gray-200">
                    <p className="text-gray-500 text-xl font-medium">No models listed yet.</p>
                </div>
            ) : (
                <>
                {orderedGroups.length > 1 && (
                    <div className="flex flex-wrap justify-center gap-2 mb-10">
                        <button
                            onClick={() => setCategoryFilter('')}
                            className={`px-4 py-2 rounded-full text-sm font-bold transition-colors ${
                                categoryFilter === '' ? 'bg-gray-900 text-white' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                            }`}
                        >
                            All
                        </button>
                        {orderedGroups.map(([category]) => (
                            <button
                                key={category}
                                onClick={() => setCategoryFilter(category)}
                                className={`px-4 py-2 rounded-full text-sm font-bold transition-colors ${
                                    categoryFilter === category ? 'bg-gray-900 text-white' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                                }`}
                            >
                                {category}
                            </button>
                        ))}
                    </div>
                )}
                {visibleGroups.map(([category, groupItems]) => (
                    <div key={category} className="mb-12">
                        <h2 className="text-sm font-bold text-gray-400 uppercase tracking-widest mb-4 border-b pb-2">
                            {category}
                        </h2>
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
                            {groupItems.map(item => (
                                <div key={item.id} className="border border-gray-100 rounded-3xl bg-white shadow-sm overflow-hidden hover:shadow-xl transition-all duration-300 flex flex-col">
                                    <div className="relative aspect-[4/3] bg-gray-50 border-b overflow-hidden">
                                        {item.image_url ? (
                                            <img src={item.image_url} alt={item.model_name} className="object-cover w-full h-full" />
                                        ) : (
                                            <div className="flex items-center justify-center h-full text-gray-300">
                                                <i className="bi bi-image text-4xl"></i>
                                            </div>
                                        )}
                                    </div>
                                    <div className="p-6 flex flex-col flex-grow">
                                        <h3 className="text-xl font-bold mb-2 text-gray-900">{item.model_name}</h3>
                                        {item.description && (
                                            <p className="text-gray-500 mb-6 text-sm flex-grow leading-relaxed">{item.description}</p>
                                        )}
                                        <button
                                            onClick={() => setQuoteItem(item)}
                                            className="mt-auto bg-gray-900 hover:bg-blue-600 text-white px-6 py-3 rounded-2xl text-sm font-bold transition-all duration-300"
                                        >
                                            Request a Quote
                                        </button>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                ))}
                </>
            )}

            {quoteItem && (
                <RequestQuoteForm
                    itemLabel={`${brand.name} ${quoteItem.model_name}`}
                    itemDescription={quoteItem.description}
                    onClose={() => setQuoteItem(null)}
                />
            )}
        </div>
    );
}
