"use client";

import { useEffect, useState } from 'react';
import { DealerConfig, DealerRentalItem } from '@/lib/types';
import RequestQuoteForm from './RequestQuoteForm';

interface RentalCatalogProps {
    initialConfig?: DealerConfig;
}

function formatRate(label: string, value: number | null) {
    if (value === null) return null;
    return (
        <span key={label} className="inline-block mr-3">
            <span className="text-gray-500">{label}:</span> ${value.toFixed(2)}
        </span>
    );
}

const OTHER_CATEGORY = 'Other Equipment';

// Not a typo-tolerant fuzzy match (e.g. Levenshtein) - a lighter, dependency-
// free version: every word in the search box must appear somewhere in the
// item name, in any order, case-insensitive. Handles "excavator mini"
// matching "Mini Excavator" and partial words, without pulling in a search
// library for what's ultimately a client-side filter over at most a few
// hundred items.
function matchesSearch(name: string, query: string): boolean {
    const q = query.trim().toLowerCase();
    if (!q) return true;
    const lowerName = name.toLowerCase();
    return q.split(/\s+/).every((token) => lowerName.includes(token));
}

export default function RentalCatalog({ initialConfig }: RentalCatalogProps) {
    const [config, setConfig] = useState<DealerConfig | null>(initialConfig || null);
    const [items, setItems] = useState<DealerRentalItem[]>([]);
    const [loaded, setLoaded] = useState(false);
    const [requestItem, setRequestItem] = useState<DealerRentalItem | null>(null);
    const [requestingGeneric, setRequestingGeneric] = useState(false);
    const [search, setSearch] = useState('');
    const [activeCategory, setActiveCategory] = useState<string | null>(null);

    useEffect(() => {
        if (!initialConfig?.theme?.contact_phone) {
            const fetchConfig = async () => {
                try {
                    const res = await fetch('/api/v1/site-info', {
                        headers: { 'X-Environment': 'local' }
                    });
                    const data = await res.json();

                    const adapted: DealerConfig = {
                        name: data.identity?.name,
                        slug: data.identity?.slug,
                        modules: {},
                        theme: {
                            contact_phone: data.theme?.contactPhone
                        }
                    };
                    setConfig(adapted);
                } catch (err) {
                    console.error("Failed to load site info", err);
                }
            };
            fetchConfig();
        }

        const fetchRentals = async () => {
            try {
                const res = await fetch('/api/v1/rentals');
                const data = await res.json();
                setItems(Array.isArray(data) ? data : []);
            } catch (err) {
                console.error("Failed to load rental items", err);
            } finally {
                setLoaded(true);
            }
        };
        fetchRentals();
    }, [initialConfig]);

    const requestModal = requestItem ? (
        <RequestQuoteForm
            itemLabel={requestItem.name}
            requestType="rental"
            title="Request to Rent"
            messagePlaceholder="What dates/times would you like to rent this? (optional)"
            onClose={() => setRequestItem(null)}
        />
    ) : requestingGeneric ? (
        <RequestQuoteForm
            itemLabel="Rental Inquiry"
            requestType="rental"
            title="Request to Rent"
            messagePlaceholder="What would you like to rent, and when? (optional)"
            onClose={() => setRequestingGeneric(false)}
        />
    ) : null;

    // Graceful fallback while loading, and when a dealer hasn't configured
    // any rental items yet.
    if (!loaded || items.length === 0) {
        return (
            <div className="max-w-lg mx-auto bg-white p-8 rounded shadow border text-center">
                <h2 className="text-2xl font-bold mb-4">Equipment Rentals</h2>
                <p className="text-gray-600 mb-6">Interested in renting equipment? Let us know what you need.</p>
                <button
                    onClick={() => setRequestingGeneric(true)}
                    className="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-4 px-6 rounded-lg shadow-lg transition-transform active:scale-[0.98]"
                >
                    Request to Rent
                </button>
                {requestModal}
            </div>
        );
    }

    // Full category list (from ALL items, not the filtered set) so the
    // filter boxes themselves don't disappear as a search narrows things
    // down - order follows first appearance in sort_order, matching how
    // the dealer ordered their own price sheet, not alphabetical.
    const allCategories: string[] = [];
    for (const item of items) {
        const key = item.category || OTHER_CATEGORY;
        if (!allCategories.includes(key)) allCategories.push(key);
    }
    if (allCategories.includes(OTHER_CATEGORY) && allCategories.length > 1) {
        allCategories.splice(allCategories.indexOf(OTHER_CATEGORY), 1);
        allCategories.push(OTHER_CATEGORY);
    }

    const filteredItems = items.filter((item) => {
        const key = item.category || OTHER_CATEGORY;
        if (activeCategory && key !== activeCategory) return false;
        return matchesSearch(item.name, search);
    });

    // Group the filtered items by category, same ordering rule as above.
    const groups: Array<[string, DealerRentalItem[]]> = [];
    const groupIndex: Record<string, number> = {};
    for (const item of filteredItems) {
        const key = item.category || OTHER_CATEGORY;
        if (!(key in groupIndex)) {
            groupIndex[key] = groups.length;
            groups.push([key, []]);
        }
        groups[groupIndex[key]][1].push(item);
    }
    if (OTHER_CATEGORY in groupIndex && groups.length > 1) {
        const idx = groupIndex[OTHER_CATEGORY];
        const [other] = groups.splice(idx, 1);
        groups.push(other);
    }

    return (
        <div className="max-w-5xl mx-auto">
            <h2 className="text-2xl font-bold mb-2 text-center">Equipment Rentals</h2>
            <p className="text-gray-600 mb-6 text-center">Browse our rental equipment and request a time that works for you</p>

            <div className="mb-6">
                <input
                    type="text"
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                    placeholder="Search equipment..."
                    className="w-full max-w-md mx-auto block h-11 rounded-lg border border-gray-200 bg-white focus:ring-2 focus:ring-blue-500 focus:outline-none px-4 mb-4"
                />
                {allCategories.length > 1 && (
                    <div className="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-6 gap-2">
                        <button
                            onClick={() => setActiveCategory(null)}
                            className={`bg-white p-3 rounded shadow border text-center text-sm font-semibold transition-colors ${
                                activeCategory === null ? 'border-blue-600 text-blue-600' : 'border-gray-200 text-gray-700 hover:border-gray-300'
                            }`}
                        >
                            All
                        </button>
                        {allCategories.map((category) => (
                            <button
                                key={category}
                                onClick={() => setActiveCategory(category)}
                                className={`bg-white p-3 rounded shadow border text-center text-sm font-semibold transition-colors ${
                                    activeCategory === category ? 'border-blue-600 text-blue-600' : 'border-gray-200 text-gray-700 hover:border-gray-300'
                                }`}
                            >
                                {category}
                            </button>
                        ))}
                    </div>
                )}
            </div>

            {filteredItems.length === 0 && (
                <div className="text-center text-gray-500 py-12">
                    <p className="mb-3">No equipment matches your search.</p>
                    <button
                        onClick={() => { setSearch(''); setActiveCategory(null); }}
                        className="text-blue-600 hover:text-blue-700 font-semibold"
                    >
                        Clear filters
                    </button>
                </div>
            )}

            {groups.map(([category, categoryItems]) => (
                <div key={category} className="mb-8">
                    {groups.length > 1 && (
                        <h3 className="text-xl font-bold mb-3 border-b pb-2">{category}</h3>
                    )}
                    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                        {categoryItems.map((item) => (
                            <div key={item.id} className="bg-white p-5 rounded shadow border flex flex-col justify-between">
                                <div className="flex items-start gap-4">
                                    {item.image_url && (
                                        // eslint-disable-next-line @next/next/no-img-element
                                        <img
                                            src={item.image_url}
                                            alt={item.name}
                                            className="w-14 h-14 rounded object-cover border flex-shrink-0"
                                        />
                                    )}
                                    <div>
                                        <h3 className="text-lg font-semibold">{item.name}</h3>
                                        <div className="text-gray-600 mt-1 text-sm">
                                            {formatRate('Hourly', item.rate_hourly)}
                                            {formatRate('4 Hr', item.rate_4hr)}
                                            {formatRate('8 Hr', item.rate_8hr)}
                                            {formatRate('24 Hr', item.rate_24hr)}
                                            {formatRate('Weekly', item.rate_weekly)}
                                        </div>
                                        {item.minimum_rental_price !== null && (
                                            <div className="text-gray-500 text-xs mt-1">
                                                Minimum: ${item.minimum_rental_price.toFixed(2)}
                                                {item.minimum_rental_hours !== null && ` / ${item.minimum_rental_hours} hr${item.minimum_rental_hours === 1 ? '' : 's'}`}
                                            </div>
                                        )}
                                        {item.deposit !== null && (
                                            <div className="text-gray-500 text-xs mt-1">
                                                Deposit required: ${item.deposit.toFixed(2)}
                                            </div>
                                        )}
                                    </div>
                                </div>
                                <button
                                    onClick={() => setRequestItem(item)}
                                    className="mt-4 bg-blue-600 hover:bg-blue-700 text-white font-semibold py-2 px-4 rounded-lg text-center transition-transform active:scale-[0.98]"
                                >
                                    Request to Rent
                                </button>
                            </div>
                        ))}
                    </div>
                </div>
            ))}
            {requestModal}
        </div>
    );
}
