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

    // Extract slug from host (e.g., 'demo.bentcrankshaft.com' -> 'demo')
    let targetHost = host;
    let slug = '';

    if (host.match(/^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}/)) {
        // If accessing via IP (local dev), use localhost
        targetHost = 'localhost';
        slug = '';
    } else {
        // Extract slug from subdomain (e.g., 'kens-mowers.bentcrankshaft.com' -> 'kens-mowers')
        const hostParts = host.split('.');
        if (hostParts.length > 1 && !host.includes('localhost')) {
            slug = hostParts[0]; // First part is the slug
        }
    }

    try {
        const res = await fetch(`${API_BASE}/site-info${slug ? `?slug=${slug}` : ''}`, {
            cache: 'no-store',
            headers: {
                'Cookie': cookieHeader,
                'X-Forwarded-Host': targetHost,
                'Host': targetHost // Pass the actual host for consistent behavior
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
                hero_title: data.theme?.heroTitle,
                hero_tagline: data.theme?.heroTagline,
                hero_show_logo: data.theme?.heroShowLogo !== undefined ? data.theme.heroShowLogo : true, // Use API value or default to true

                // Features (API returns camelCase)
                feat_inventory_title: data.theme?.featInventoryTitle,
                feat_inventory_text: data.theme?.featInventoryText,
                feat_parts_title: data.theme?.featPartsTitle,
                feat_parts_text: data.theme?.featPartsText,
                feat_service_title: data.theme?.featServiceTitle,
                feat_service_text: data.theme?.featServiceText,

                // Contact (API returns camelCase)
                contact_phone: data.theme?.contactPhone,
                contact_email: data.theme?.contactEmail,
                contact_address: data.theme?.contactAddress,
                contact_text: data.theme?.contactText,

                // Brands (API returns camelCase)
                brand_logos: data.theme?.brandLogos, // Fallback for snake_case
                brandLogos: data.theme?.brandLogos, // Use camelCase from API
                brandLogoUrls: data.theme?.brandLogoUrls
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
