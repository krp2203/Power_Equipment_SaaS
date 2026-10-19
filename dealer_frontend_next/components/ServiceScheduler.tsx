"use client";

import { useEffect, useState } from 'react';
import { DealerConfig, DealerServiceItem } from '@/lib/types';
import { genericEquipmentIcon } from '@/lib/equipmentIcons';

interface ServiceSchedulerProps {
    initialConfig?: DealerConfig;
}

export default function ServiceScheduler({ initialConfig }: ServiceSchedulerProps) {
    const [config, setConfig] = useState<DealerConfig | null>(initialConfig || null);
    const [services, setServices] = useState<DealerServiceItem[]>([]);
    const [loaded, setLoaded] = useState(false);

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

        const fetchServices = async () => {
            try {
                const res = await fetch('/api/v1/services');
                const data = await res.json();
                setServices(Array.isArray(data) ? data : []);
            } catch (err) {
                console.error("Failed to load services", err);
            } finally {
                setLoaded(true);
            }
        };
        fetchServices();
    }, [initialConfig]);

    const phoneNumber = config?.theme?.contact_phone || '1-800-000-0000';
    const phoneLink = `tel:${phoneNumber.replace(/\D/g, '')}`;

    // Graceful fallback while loading, and when a dealer hasn't configured
    // any services yet - the original phone-only card.
    if (!loaded || services.length === 0) {
        return (
            <div className="max-w-lg mx-auto bg-white p-8 rounded shadow border text-center">
                <h2 className="text-2xl font-bold mb-4">Request Service</h2>
                <p className="text-gray-600 mb-6">Call us to schedule your service appointment</p>
                <a
                    href={phoneLink}
                    className="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-4 px-6 rounded-lg shadow-lg transition-transform active:scale-[0.98] text-center block"
                >
                    📞 Call Us: {phoneNumber}
                </a>
            </div>
        );
    }

    return (
        <div className="max-w-2xl mx-auto">
            <h2 className="text-2xl font-bold mb-2 text-center">Our Services</h2>
            <p className="text-gray-600 mb-6 text-center">Call us to request a service or schedule an appointment</p>
            <div className="grid gap-4 sm:grid-cols-2">
                {services.map((svc) => (
                    <div key={svc.id} className="bg-white p-5 rounded shadow border flex flex-col justify-between">
                        <div className="flex items-start gap-4">
                            {svc.image_url ? (
                                // eslint-disable-next-line @next/next/no-img-element
                                <img
                                    src={svc.image_url}
                                    alt={svc.name}
                                    className="w-14 h-14 rounded object-cover border flex-shrink-0"
                                />
                            ) : (
                                <div className="w-14 h-14 rounded border bg-gray-50 flex items-center justify-center text-2xl flex-shrink-0">
                                    {genericEquipmentIcon(svc.name)}
                                </div>
                            )}
                            <div>
                                <h3 className="text-lg font-semibold">{svc.name}</h3>
                                {svc.price !== null && (
                                    <p className="text-gray-600 mt-1">Starting at ${svc.price.toFixed(2)}</p>
                                )}
                            </div>
                        </div>
                        <a
                            href={phoneLink}
                            className="mt-4 bg-blue-600 hover:bg-blue-700 text-white font-semibold py-2 px-4 rounded-lg text-center transition-transform active:scale-[0.98]"
                        >
                            {svc.allow_web_scheduling ? 'Request This Service' : 'Call to Schedule'}
                        </a>
                    </div>
                ))}
            </div>
        </div>
    );
}
