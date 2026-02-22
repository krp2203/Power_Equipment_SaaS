import { DealerConfig } from './types';

const API_BASE = typeof window === 'undefined'
    ? 'http://web:5000/api/v1'  // Server-side (Internal Docker network)
    : '/api/v1'; // Client-side (Relative -> Proxied by Next.js)

import { cookies, headers } from 'next/headers';

export async function getDealerConfig(): Promise<DealerConfig> {
    const cookieStore = await cookies();
    const headersList = await headers();
    const host = headersList.get('host') || 'localhost:3000';

    const cookieHeader = cookieStore.getAll().map((c: any) => `${c.name}=${c.value}`).join('; ');

    // In a real multi-tenant app, we'd pass the Host header or use a specific subdomain.
    // For dev, we'll hit the localhost API directly AND forward cookies (for impersonation).

    // Map root domain to master organization (slug: pes)
    let targetHost = host;
    if (host === 'bentcrankshaft.com' || host === 'www.bentcrankshaft.com') {
        targetHost = 'pes.bentcrankshaft.com';
    } else if (host.match(/^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}/)) {
        // If accessing via IP (local dev), pretend to be localhost so Backend loads Org 1
        targetHost = 'localhost';
    }

    try {
        const res = await fetch(`${API_BASE}/site-info`, {
            cache: 'no-store',
            headers: {
                'Cookie': cookieHeader,
                'X-Forwarded-Host': targetHost,
                'Host': targetHost // Ensure Flask sees the original host if possible
            }
        });
        if (!res.ok) throw new Error('Failed to fetch config');

        const data = await res.json();

        // Adapt Flask API response (v1/site-info) to Frontend Type (DealerConfig)
        return {
            name: data.identity?.name || 'Dealer Site',
            slug: data.identity?.slug || '',
            modules: {
                ari: data.integrations?.ari?.enabled || false,
                pos: data.integrations?.pos?.provider || 'none',
                facebook: data.integrations?.facebook?.enabled || false
            },
            facebook_page_id: data.integrations?.facebook?.page_id,
            theme: {
                primaryColor: data.theme?.primaryColor || data.theme?.primary_color || '#3B82F6',
                logoUrl: data.theme?.logoUrl,

                // Hero
                hero_title: data.theme?.hero_title,
                hero_tagline: data.theme?.hero_tagline,
                hero_show_logo: true, // Default to true if not specified

                // Features
                feat_inventory_title: data.theme?.feat_inventory_title,
                feat_inventory_text: data.theme?.feat_inventory_text,
                feat_parts_title: data.theme?.feat_parts_title,
                feat_parts_text: data.theme?.feat_parts_text,
                feat_service_title: data.theme?.feat_service_title,
                feat_service_text: data.theme?.feat_service_text,

                // Contact
                contact_phone: data.theme?.contact_phone,
                contact_email: data.theme?.contact_email,
                contact_address: data.theme?.contact_address,
                contact_text: data.theme?.contact_text,

                // Brands
                brand_logos: data.theme?.brand_logos
            }
        };
    } catch (err) {
        console.error("API Fetch Error:", err);
        if (err instanceof TypeError) {
            console.error("Likely network issue. API_BASE:", API_BASE);
        }
        // Fallback for demo if backend is down or no tenant context
        return {
            name: 'Demo Dealer',
            slug: 'demo',
            modules: { ari: true, pos: 'ideal' },
            theme: { primaryColor: '#DC2626' } // Red
        };
    }
}
