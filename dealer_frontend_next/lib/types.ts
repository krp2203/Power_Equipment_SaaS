export interface DealerConfig {
    name: string;
    slug: string;
    modules: {
        ari?: boolean;
        pos?: string;
        facebook?: boolean;
    };
    facebook_page_id?: string;
    theme: {
        primaryColor?: string;
        logoUrl?: string;

        // Hero
        hero_title?: string;
        hero_tagline?: string;

        // Footer
        footer_tagline?: string;

        // Contact
        contact_phone?: string;
        contact_email?: string;
        contact_address?: string;
        contact_text?: string;

        // Social Media
        socialFacebook?: string;
        socialInstagram?: string;
        socialTwitter?: string;
        socialLinkedin?: string;
        socialYoutube?: string;
        socialBluesky?: string;

        // Brands
        brand_logos?: Record<string, string>;
        brandLogos?: Record<string, string>;
        brandLogoUrls?: Record<string, string>;
    };
}

export interface InventoryItem {
    id: number | string;
    name: string;
    price: number | null;
    stock: number | null;
    status: string;
    image?: string;
    description?: string;
    manufacturer?: string;
    model_number?: string;
    serial_number?: string;
    year?: number;
    condition?: string;
    unit_hours?: string;
    type?: string;
    is_closeout?: boolean;
    is_special_price?: boolean;
    // Present on catalog (special-order, not real stock) entries mixed into
    // /api/v1/inventory - real Unit rows come back with source: "inventory".
    source?: 'inventory' | 'catalog';
    // Catalog entries only - lets the inventory grid link back to the brand page.
    brand_slug?: string;
    category?: string | null;
}

export interface CatalogBrandSummary {
    name: string;
    slug: string;
    logo_url?: string | null;
}

export interface CatalogItem {
    id: number;
    model_name: string;
    category?: string | null;
    description?: string | null;
    image_url?: string | null;
}

export interface CatalogBrandDetail {
    brand: {
        name: string;
        logo_url?: string | null;
        intro_text?: string | null;
    };
    items: CatalogItem[];
}

export interface PartItem {
    id: number;
    part_number: string;
    manufacturer?: string;
    description?: string;
    stock: number;
    image?: string;
    price?: number;
}

export interface Advertisement {
    id: number;
    title: string;
    description?: string;
    image: string;
    thumbnail?: string;
    link_url?: string;
    media_type?: 'image' | 'video';
}

export interface InventoryHighlight {
    id: number;
    name: string;
    manufacturer?: string;
    price: number;
    image?: string;
    condition?: string;
    reasons: ('closeout' | 'special_price' | 'new_arrival')[];
}
