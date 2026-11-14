"use client";

import { FinancingLenderItem } from '@/lib/types';
import { useFinancingLenders } from '@/lib/useFinancingLenders';

function LenderLink({ lender }: { lender: FinancingLenderItem }) {
    return (
        <a
            href={lender.url}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-2 hover:opacity-80 transition-opacity whitespace-nowrap"
        >
            {lender.logo_url ? (
                // White backing so logos with dark/transparent artwork stay
                // readable against the dark bar, regardless of each lender's
                // own color scheme.
                <span className="bg-white rounded-md px-3 py-1.5 inline-flex items-center">
                    <img src={lender.logo_url} alt={lender.name} className="h-10 object-contain" />
                </span>
            ) : (
                <span className="underline underline-offset-2">{lender.name}</span>
            )}
        </a>
    );
}

export default function FinancingBar() {
    const { lenders } = useFinancingLenders();

    if (lenders.length === 0) return null;

    // Split alternately rather than into two contiguous halves, so the
    // "Flexible Financing Available" text stays centered and lenders fill
    // in evenly on both sides of it as more are added, instead of piling up
    // on one side.
    const left = lenders.filter((_, i) => i % 2 === 0);
    const right = lenders.filter((_, i) => i % 2 === 1);

    return (
        <div className="bg-gray-900 text-white py-5">
            <div className="container mx-auto px-4 flex flex-wrap items-center justify-center gap-x-8 gap-y-3">
                {left.map(lender => <LenderLink key={lender.id} lender={lender} />)}
                <span className="font-semibold whitespace-nowrap">Flexible Financing Available</span>
                {right.map(lender => <LenderLink key={lender.id} lender={lender} />)}
            </div>
        </div>
    );
}
