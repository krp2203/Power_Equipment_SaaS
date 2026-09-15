"use client";

import { useEffect, useState } from 'react';
import PartSmartFrame from '@/components/PartSmartFrame';
import { PartItem, DealerConfig } from '@/lib/types';

interface QuoteLine {
    part_id: number;
    part_number: string;
    description?: string;
    quantity: number;
}

const QUOTE_STORAGE_KEY = 'parts_quote_list';

export default function PartsPage() {
    const [parts, setParts] = useState<PartItem[]>([]);
    const [config, setConfig] = useState<DealerConfig | null>(null);
    const [loading, setLoading] = useState(true);

    // Quote list ("cart" stand-in until there's real checkout) - kept in
    // localStorage so it survives a reload/navigation while browsing parts.
    const [quoteLines, setQuoteLines] = useState<QuoteLine[]>([]);
    const [showQuoteModal, setShowQuoteModal] = useState(false);
    const [submitting, setSubmitting] = useState(false);
    const [submitError, setSubmitError] = useState('');
    const [submitted, setSubmitted] = useState(false);
    const [customerName, setCustomerName] = useState('');
    const [customerEmail, setCustomerEmail] = useState('');
    const [customerPhone, setCustomerPhone] = useState('');
    const [notes, setNotes] = useState('');

    useEffect(() => {
        try {
            const saved = localStorage.getItem(QUOTE_STORAGE_KEY);
            if (saved) setQuoteLines(JSON.parse(saved));
        } catch {
            // ignore - private browsing / storage disabled
        }

        // Fetch local parts inventory (only parts the dealer flagged for the web)
        fetch('/api/v1/parts', { cache: 'no-store' })
            .then(res => res.json())
            .then(data => {
                setParts(data);
                setLoading(false);
            })
            .catch(err => {
                console.error("Failed to load parts inventory", err);
                setLoading(false);
            });

        // Fetch dealer config to check if ARI is enabled, and for contact info
        // used by the "Call for Pricing" CTA below.
        fetch('/api/v1/site-info', { cache: 'no-store' })
            .then(res => res.json())
            .then(data => {
                const adapted: DealerConfig = {
                    name: data.identity?.name,
                    slug: data.identity?.slug,
                    modules: {
                        ari: data.integrations?.ari?.enabled || false,
                        pos: data.integrations?.pos?.provider || 'none',
                        facebook: data.integrations?.facebook?.enabled || false
                    },
                    theme: {
                        contact_phone: data.theme?.contactPhone
                    }
                };
                setConfig(adapted);
            })
            .catch(err => console.error("Failed to load site info", err));
    }, []);

    const persistQuoteLines = (lines: QuoteLine[]) => {
        setQuoteLines(lines);
        try {
            localStorage.setItem(QUOTE_STORAGE_KEY, JSON.stringify(lines));
        } catch {
            // ignore
        }
    };

    const addToQuote = (part: PartItem) => {
        const existing = quoteLines.find(l => l.part_id === part.id);
        if (existing) {
            persistQuoteLines(quoteLines.map(l => l.part_id === part.id ? { ...l, quantity: l.quantity + 1 } : l));
        } else {
            persistQuoteLines([...quoteLines, {
                part_id: part.id, part_number: part.part_number, description: part.description, quantity: 1
            }]);
        }
    };

    const updateQuantity = (partId: number, quantity: number) => {
        if (quantity <= 0) {
            persistQuoteLines(quoteLines.filter(l => l.part_id !== partId));
        } else {
            persistQuoteLines(quoteLines.map(l => l.part_id === partId ? { ...l, quantity } : l));
        }
    };

    const removeLine = (partId: number) => persistQuoteLines(quoteLines.filter(l => l.part_id !== partId));

    const submitQuote = async () => {
        if (!customerName.trim()) {
            setSubmitError('Please enter your name.');
            return;
        }
        setSubmitting(true);
        setSubmitError('');
        try {
            const res = await fetch('/api/v1/quote-request', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    customer_name: customerName,
                    customer_email: customerEmail,
                    customer_phone: customerPhone,
                    notes,
                    items: quoteLines.map(l => ({
                        part_id: l.part_id, part_number: l.part_number, description: l.description, quantity: l.quantity
                    })),
                }),
            });
            const data = await res.json();
            if (!res.ok) {
                setSubmitError(data.error || 'Something went wrong. Please try again.');
                return;
            }
            persistQuoteLines([]);
            setSubmitted(true);
        } catch {
            setSubmitError('Something went wrong. Please try again.');
        } finally {
            setSubmitting(false);
        }
    };

    const closeModal = () => {
        setShowQuoteModal(false);
        setSubmitted(false);
        setSubmitError('');
    };

    const contactPhone = config?.theme?.contact_phone || '';
    const phoneLink = contactPhone ? `tel:${contactPhone.replace(/\D/g, '')}` : '/contact';
    const ctaLabel = contactPhone ? `Call for Pricing: ${contactPhone}` : 'Contact Us for Pricing';
    const totalQuoteQty = quoteLines.reduce((sum, l) => sum + l.quantity, 0);

    return (
        <div className="max-w-7xl mx-auto px-4 py-12">
            <div className="space-y-12">
                <section>
                    <div className="flex justify-between items-center mb-6">
                        <h1 className="text-3xl font-bold">In-Stock Parts</h1>
                        <div className="text-sm text-gray-500">
                            {parts.length} items found
                        </div>
                    </div>

                    {loading ? (
                        <div className="text-center py-12">Loading local inventory...</div>
                    ) : parts.length === 0 ? (
                        <div className="text-center py-12 bg-gray-50 rounded-lg border border-dashed">
                            <p className="text-gray-500">No local parts currently listed in inventory.</p>
                        </div>
                    ) : (
                        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
                            {parts.map(part => {
                                const inQuote = quoteLines.find(l => l.part_id === part.id);
                                return (
                                    <div key={part.id} className="border rounded-lg bg-white overflow-hidden shadow-sm flex flex-col">
                                        <div className="aspect-square bg-gray-50 relative border-b">
                                            {part.image ? (
                                                <img
                                                    src={part.image}
                                                    alt={part.part_number}
                                                    className="object-cover w-full h-full"
                                                />
                                            ) : (
                                                <div className="flex items-center justify-center h-full text-gray-300">
                                                    <svg className="w-12 h-12" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                                                    </svg>
                                                </div>
                                            )}
                                            <div className="absolute bottom-2 right-2">
                                                <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${part.stock > 0 ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
                                                    {part.stock > 0 ? `In Stock: ${part.stock}` : 'Out of Stock'}
                                                </span>
                                            </div>
                                        </div>
                                        <div className="p-3 flex flex-col flex-grow">
                                            <div className="text-xs font-bold text-blue-600 mb-1">{part.manufacturer}</div>
                                            <div className="font-mono font-bold text-sm mb-1">{part.part_number}</div>
                                            <div className="text-xs text-gray-600 line-clamp-2 flex-grow mb-2">{part.description}</div>
                                            <div className="pt-2 border-t border-gray-100 space-y-2">
                                                {part.price && part.price > 0 ? (
                                                    <div className="text-lg font-black text-gray-900">${part.price.toLocaleString()}</div>
                                                ) : (
                                                    <a
                                                        href={phoneLink}
                                                        className="block text-center bg-gray-900 hover:bg-blue-600 text-white text-xs font-bold uppercase tracking-wide py-2 rounded-lg transition-colors"
                                                    >
                                                        📞 {ctaLabel}
                                                    </a>
                                                )}
                                                <button
                                                    onClick={() => addToQuote(part)}
                                                    className={`w-full text-xs font-bold uppercase tracking-wide py-2 rounded-lg transition-colors ${inQuote ? 'bg-green-50 text-green-700 border border-green-200' : 'bg-blue-50 text-blue-700 hover:bg-blue-100 border border-blue-100'}`}
                                                >
                                                    {inQuote ? `✓ In Quote (${inQuote.quantity})` : '+ Add to Quote'}
                                                </button>
                                            </div>
                                        </div>
                                    </div>
                                );
                            })}
                        </div>
                    )}
                </section>

                {config?.modules.ari && (
                    <>
                        <hr className="border-gray-200" />

                        <section>
                            <h1 className="text-3xl font-bold mb-6">Parts Lookup</h1>
                            <PartSmartFrame />
                        </section>
                    </>
                )}
            </div>

            {/* Floating quote button */}
            {quoteLines.length > 0 && !showQuoteModal && (
                <button
                    onClick={() => setShowQuoteModal(true)}
                    className="fixed bottom-6 right-6 bg-blue-600 hover:bg-blue-700 text-white font-bold px-5 py-3 rounded-full shadow-xl flex items-center gap-2 z-40"
                >
                    <span className="text-lg">📝</span>
                    Request Quote ({totalQuoteQty})
                </button>
            )}

            {/* Quote modal */}
            {showQuoteModal && (
                <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4" onClick={closeModal}>
                    <div className="bg-white rounded-2xl shadow-2xl max-w-lg w-full max-h-[90vh] overflow-y-auto" onClick={e => e.stopPropagation()}>
                        <div className="p-6">
                            {submitted ? (
                                <div className="text-center py-8">
                                    <div className="text-5xl mb-4">✅</div>
                                    <h2 className="text-2xl font-bold mb-2">Quote Request Sent</h2>
                                    <p className="text-gray-500 mb-6">We&apos;ll be in touch shortly with pricing.</p>
                                    <button onClick={closeModal} className="bg-gray-900 text-white font-bold px-6 py-3 rounded-xl">
                                        Close
                                    </button>
                                </div>
                            ) : (
                                <>
                                    <div className="flex justify-between items-center mb-4">
                                        <h2 className="text-xl font-bold">Request a Quote</h2>
                                        <button onClick={closeModal} className="text-gray-400 hover:text-gray-700 text-2xl leading-none">&times;</button>
                                    </div>

                                    <div className="space-y-2 mb-4 max-h-48 overflow-y-auto">
                                        {quoteLines.map(line => (
                                            <div key={line.part_id} className="flex items-center justify-between gap-2 border-b pb-2">
                                                <div className="min-w-0">
                                                    <div className="font-mono font-bold text-sm truncate">{line.part_number}</div>
                                                    {line.description && <div className="text-xs text-gray-500 truncate">{line.description}</div>}
                                                </div>
                                                <div className="flex items-center gap-2 shrink-0">
                                                    <input
                                                        type="number"
                                                        min={1}
                                                        value={line.quantity}
                                                        onChange={e => updateQuantity(line.part_id, parseInt(e.target.value) || 0)}
                                                        className="w-14 border rounded-lg text-center py-1"
                                                    />
                                                    <button onClick={() => removeLine(line.part_id)} className="text-red-500 hover:text-red-700 text-sm">
                                                        Remove
                                                    </button>
                                                </div>
                                            </div>
                                        ))}
                                        {quoteLines.length === 0 && (
                                            <p className="text-gray-400 text-sm text-center py-4">Your quote list is empty.</p>
                                        )}
                                    </div>

                                    <div className="space-y-3">
                                        <input
                                            type="text" placeholder="Your Name *" value={customerName}
                                            onChange={e => setCustomerName(e.target.value)}
                                            className="w-full border rounded-xl px-4 py-2.5"
                                        />
                                        <input
                                            type="email" placeholder="Email" value={customerEmail}
                                            onChange={e => setCustomerEmail(e.target.value)}
                                            className="w-full border rounded-xl px-4 py-2.5"
                                        />
                                        <input
                                            type="tel" placeholder="Phone" value={customerPhone}
                                            onChange={e => setCustomerPhone(e.target.value)}
                                            className="w-full border rounded-xl px-4 py-2.5"
                                        />
                                        <textarea
                                            placeholder="Anything else we should know? (optional)" value={notes}
                                            onChange={e => setNotes(e.target.value)}
                                            rows={2}
                                            className="w-full border rounded-xl px-4 py-2.5"
                                        />
                                    </div>

                                    {submitError && <p className="text-red-600 text-sm mt-3">{submitError}</p>}

                                    <button
                                        onClick={submitQuote}
                                        disabled={submitting || quoteLines.length === 0}
                                        className="w-full mt-4 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-300 text-white font-bold py-3 rounded-xl transition-colors"
                                    >
                                        {submitting ? 'Sending...' : 'Send Quote Request'}
                                    </button>
                                </>
                            )}
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
