"use client";

import { useEffect, useState } from 'react';
import { DealerConfig } from '@/lib/types';

export default function ServiceScheduler() {
    const [config, setConfig] = useState<DealerConfig | null>(null);

    useEffect(() => {
        // Fetch dealer config for contact phone
        fetch('/api/v1/site-info')
            .then(res => res.json())
            .then(data => {
                const adapted: DealerConfig = {
                    name: data.identity?.name,
                    slug: data.identity?.slug,
                    modules: {},
                    theme: {
                        contact_phone: data.theme?.contact_phone
                    }
                };
                setConfig(adapted);
            })
            .catch(err => console.error("Failed to load site info", err));
    }, []);

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
