"use client";

import { useFinancingLenders } from '@/lib/useFinancingLenders';

export default function FinancingPage() {
    const { lenders, loaded } = useFinancingLenders();

    return (
        <div className="max-w-5xl mx-auto px-4 py-12">
            <h1 className="text-3xl font-bold mb-3 text-center">Financing Options</h1>
            <p className="text-gray-500 text-center max-w-2xl mx-auto mb-10">
                We work with several financing partners - here are your options. Pick the one that fits
                your purchase, then click through to apply.
            </p>

            {!loaded ? (
                <div className="text-center text-gray-400 py-12">Loading...</div>
            ) : lenders.length === 0 ? (
                <div className="text-center py-24 bg-gray-50 rounded-3xl border-2 border-dashed border-gray-200">
                    <p className="text-gray-500 text-xl font-medium">No financing partners listed yet.</p>
                </div>
            ) : (
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
                    {lenders.map(lender => (
                        <div key={lender.id} className="bg-white border border-gray-100 rounded-2xl shadow-sm p-6 flex flex-col">
                            {lender.logo_url && (
                                <img src={lender.logo_url} alt={lender.name} className="h-12 object-contain mb-4" />
                            )}
                            <h2 className="text-lg font-bold text-gray-900 mb-1">{lender.name}</h2>
                            {lender.description && (
                                <p className="text-gray-500 text-sm mb-4 flex-grow">{lender.description}</p>
                            )}
                            <a
                                href={lender.url}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="mt-auto bg-gray-900 hover:bg-blue-600 text-white font-bold py-3 rounded-xl text-center transition-colors"
                            >
                                Apply Now
                            </a>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}
