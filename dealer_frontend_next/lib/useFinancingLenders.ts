"use client";

import { useEffect, useState } from 'react';
import { FinancingLenderItem } from './types';

// Shared by every "Click here to get approved" surface (Navigation,
// FinancingBar, the inventory detail page, FeaturedInventory, and the
// Request-a-Quote modal's "Send & Apply") so they all agree on where a CTA
// should point, since they're all reading the same /api/v1/financing
// response rather than each computing their own answer.
export function useFinancingLenders() {
    const [lenders, setLenders] = useState<FinancingLenderItem[]>([]);
    const [loaded, setLoaded] = useState(false);

    useEffect(() => {
        fetch('/api/v1/financing')
            .then(res => res.json())
            .then(data => setLenders(Array.isArray(data) ? data : []))
            .catch(() => setLenders([]))
            .finally(() => setLoaded(true));
    }, []);

    const preferred = lenders.find(l => l.is_preferred) || null;
    // null = no active lenders at all, so callers should render no CTA.
    // Otherwise: the preferred lender's own link, or the /financing page
    // listing every active lender when none is marked preferred.
    const ctaHref = lenders.length === 0 ? null : (preferred ? preferred.url : '/financing');

    return { lenders, loaded, preferred, ctaHref };
}
