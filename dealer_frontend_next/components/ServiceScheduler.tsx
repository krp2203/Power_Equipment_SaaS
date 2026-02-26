"use client";

import { useEffect, useState } from 'react';
import { DealerConfig } from '@/lib/types';

interface ServiceSchedulerProps {
    initialConfig?: DealerConfig;
}

export default function ServiceScheduler({ initialConfig }: ServiceSchedulerProps) {
    const [config, setConfig] = useState<DealerConfig | null>(initialConfig || null);

    useEffect(() => {
        // If we already have config from SSR, use it
        if (initialConfig?.theme?.contact_phone) {
            return;
        }

        // Otherwise fetch dealer config for contact phone
        const fetchConfig = async () => {
            try {
                const res = await fetch('/api/v1/site-info', {
                    headers: {
                        'X-Environment': 'local',
                    }
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
    }, [initialConfig]);

    const phoneNumber = config?.theme?.contact_phone || '1-800-000-0000';
    const phoneLink = `tel:${phoneNumber.replace(/\D/g, '')}`;

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
