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
        hero_show_logo?: boolean;

        // Features
        feat_inventory_title?: string;
        feat_inventory_text?: string;
        feat_parts_title?: string;
        feat_parts_text?: string;
        feat_service_title?: string;
        feat_service_text?: string;

        // Contact
        contact_phone?: string;
        contact_email?: string;
        contact_address?: string;
        contact_text?: string;

        // Brands
        brand_logos?: Record<string, string>;
    };
}

export interface InventoryItem {
    id: number;
    name: string;
    price: number;
    stock: number;
    status: string;
    image?: string;
    description?: string;
    manufacturer?: string;
    model_number?: string;
    serial_number?: string;
    year?: number;
    condition?: string;
    unit_hours?: string;
}

export interface PartItem {
    id: number;
    part_number: string;
    manufacturer?: string;
    description?: string;
    stock: number;
    image?: string;
}

export interface Advertisement {
    id: number;
    title: string;
    description?: string;
    image: string;
    thumbnail?: string;
    link_url?: string;
}
