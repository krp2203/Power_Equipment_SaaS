'use client';

import { useEffect, useState } from 'react';
import { InventoryHighlight } from '@/lib/types';
import RequestQuoteForm from '@/components/RequestQuoteForm';

const REASON_BADGES: Record<string, { label: string; className: string }> = {
    closeout: { label: 'Close Out', className: 'bg-red-600' },
    special_price: { label: 'Special Price', className: 'bg-purple-600' },
    new_arrival: { label: 'New Arrival', className: 'bg-emerald-600' },
};

export default function FeaturedInventory() {
    const [items, setItems] = useState<InventoryHighlight[]>([]);
    const [quoteItem, setQuoteItem] = useState<InventoryHighlight | null>(null);

    useEffect(() => {
        fetch('/api/v1/inventory/highlights')
            .then(res => res.json())
            .then(setItems)
            .catch(() => setItems([]));
    }, []);

    if (items.length === 0) return null;

    return (
        <section className="py-8 bg-gray-50 border-t border-gray-100">
            <div className="container mx-auto px-4">
                <h3 className="text-xl font-semibold text-gray-700 mb-6 text-center">Featured Inventory</h3>
                {/* flex + justify-center (not a fixed grid) so a row with fewer
                    than the max per row - e.g. a dealer with only 3 qualifying
                    units - centers as a group instead of left-aligning with
                    empty space trailing on the right. */}
                <div className="flex flex-wrap justify-center gap-4">
                    {items.map(item => {
                        const badge = item.reasons[0] ? REASON_BADGES[item.reasons[0]] : null;
                        return (
                            <div
                                key={item.id}
                                className="w-[calc((100%-1rem)/2)] sm:w-[calc((100%-2rem)/3)] lg:w-[calc((100%-5rem)/6)] bg-white border border-gray-100 rounded-xl shadow-sm overflow-hidden hover:shadow-md transition-shadow flex flex-col"
                            >
                                <div className="relative aspect-[4/3] bg-gray-50 border-b overflow-hidden">
                                    {item.image ? (
                                        <img src={item.image} alt={item.name} className="object-cover w-full h-full" />
                                    ) : (
                                        <div className="flex items-center justify-center h-full text-gray-300">
                                            <i className="bi bi-image text-2xl"></i>
                                        </div>
                                    )}
                                    {badge && (
                                        <span className={`absolute top-2 right-2 px-2 py-0.5 rounded-full text-[10px] font-bold uppercase text-white shadow-sm ${badge.className}`}>
                                            {badge.label}
                                        </span>
                                    )}
                                </div>
                                <div className="p-3 flex flex-col flex-grow">
                                    <h4 className="text-sm font-bold text-gray-900 mb-1 line-clamp-2 leading-tight">
                                        {item.name}
                                    </h4>
                                    <div className="text-base font-black text-gray-900 mb-2">
                                        {item.price > 0 ? `$${item.price.toLocaleString()}` : 'Call for Price'}
                                    </div>
                                    <button
                                        onClick={() => setQuoteItem(item)}
                                        className="mt-auto bg-gray-900 hover:bg-blue-600 text-white px-3 py-1.5 rounded-lg text-xs font-bold transition-colors"
                                    >
                                        Request a Quote
                                    </button>
                                </div>
                            </div>
                        );
                    })}
                </div>
            </div>

            {quoteItem && (
                <RequestQuoteForm
                    itemLabel={quoteItem.name}
                    onClose={() => setQuoteItem(null)}
                />
            )}
        </section>
    );
}
