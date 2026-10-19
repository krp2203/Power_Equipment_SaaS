"use client";

import { useEffect, useState } from 'react';
import { DealerConfig, DealerRentalItem } from '@/lib/types';
import { genericEquipmentIcon } from '@/lib/equipmentIcons';
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

export default function RentalCatalog({ initialConfig }: RentalCatalogProps) {
    const [config, setConfig] = useState<DealerConfig | null>(initialConfig || null);
    const [items, setItems] = useState<DealerRentalItem[]>([]);
    const [loaded, setLoaded] = useState(false);
    const [requestItem, setRequestItem] = useState<DealerRentalItem | null>(null);
    const [requestingGeneric, setRequestingGeneric] = useState(false);

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

    return (
        <div className="max-w-2xl mx-auto">
            <h2 className="text-2xl font-bold mb-2 text-center">Equipment Rentals</h2>
            <p className="text-gray-600 mb-6 text-center">Browse our rental equipment and request a time that works for you</p>
            <div className="grid gap-4 sm:grid-cols-2">
                {items.map((item) => (
                    <div key={item.id} className="bg-white p-5 rounded shadow border flex flex-col justify-between">
                        <div className="flex items-start gap-4">
                            {item.image_url ? (
                                // eslint-disable-next-line @next/next/no-img-element
                                <img
                                    src={item.image_url}
                                    alt={item.name}
                                    className="w-14 h-14 rounded object-cover border flex-shrink-0"
                                />
                            ) : (
                                <div className="w-14 h-14 rounded border bg-gray-50 flex items-center justify-center text-2xl flex-shrink-0">
                                    {genericEquipmentIcon(item.name)}
                                </div>
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
            {requestModal}
        </div>
    );
}
