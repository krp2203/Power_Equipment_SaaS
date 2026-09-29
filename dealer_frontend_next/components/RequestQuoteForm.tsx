'use client';

import { useState } from 'react';

interface RequestQuoteFormProps {
    // What's being asked about - sent as a single free-text line item, same
    // shape the Parts page cart already posts to /api/v1/quote-request (no
    // part_id, since this isn't a real PartInventory/Unit row).
    itemLabel: string;
    itemDescription?: string | null;
    onClose: () => void;
}

export default function RequestQuoteForm({ itemLabel, itemDescription, onClose }: RequestQuoteFormProps) {
    const [name, setName] = useState('');
    const [email, setEmail] = useState('');
    const [phone, setPhone] = useState('');
    const [message, setMessage] = useState('');
    const [submitting, setSubmitting] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [done, setDone] = useState(false);

    const submit = async (e: React.FormEvent) => {
        e.preventDefault();
        setSubmitting(true);
        setError(null);
        try {
            const res = await fetch('/api/v1/quote-request', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    customer_name: name,
                    customer_email: email || undefined,
                    customer_phone: phone || undefined,
                    notes: message || undefined,
                    request_type: 'equipment',
                    items: [{
                        part_number: itemLabel,
                        description: itemDescription || undefined,
                        quantity: 1,
                    }],
                }),
            });
            if (!res.ok) {
                const data = await res.json().catch(() => ({}));
                throw new Error(data.error || 'Failed to submit request');
            }
            setDone(true);
        } catch (err: any) {
            setError(err.message || 'Something went wrong. Please try again.');
        } finally {
            setSubmitting(false);
        }
    };

    return (
        <div
            className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4"
            onClick={onClose}
        >
            <div
                className="bg-white rounded-2xl shadow-xl max-w-md w-full p-6"
                onClick={(e) => e.stopPropagation()}
            >
                {done ? (
                    <div className="text-center py-6">
                        <div className="text-4xl mb-3">✅</div>
                        <h3 className="text-xl font-bold text-gray-900 mb-2">Request Sent</h3>
                        <p className="text-gray-500 mb-6">The dealer will be in touch about the {itemLabel} soon.</p>
                        <button
                            onClick={onClose}
                            className="bg-gray-900 hover:bg-blue-600 text-white px-6 py-2 rounded-xl font-bold transition-colors"
                        >
                            Close
                        </button>
                    </div>
                ) : (
                    <form onSubmit={submit}>
                        <h3 className="text-xl font-bold text-gray-900 mb-1">Request a Quote</h3>
                        <p className="text-gray-500 text-sm mb-4">{itemLabel}</p>

                        {error && (
                            <div className="bg-red-50 text-red-700 text-sm rounded-lg px-3 py-2 mb-4">{error}</div>
                        )}

                        <div className="space-y-3">
                            <input
                                type="text"
                                placeholder="Your Name"
                                required
                                value={name}
                                onChange={(e) => setName(e.target.value)}
                                className="w-full h-11 rounded-lg border-gray-200 bg-gray-50 focus:ring-2 focus:ring-blue-500 focus:bg-white transition-all px-3"
                            />
                            <input
                                type="email"
                                placeholder="Email"
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                                className="w-full h-11 rounded-lg border-gray-200 bg-gray-50 focus:ring-2 focus:ring-blue-500 focus:bg-white transition-all px-3"
                            />
                            <input
                                type="tel"
                                placeholder="Phone"
                                value={phone}
                                onChange={(e) => setPhone(e.target.value)}
                                className="w-full h-11 rounded-lg border-gray-200 bg-gray-50 focus:ring-2 focus:ring-blue-500 focus:bg-white transition-all px-3"
                            />
                            <textarea
                                placeholder="Anything else we should know? (optional)"
                                value={message}
                                onChange={(e) => setMessage(e.target.value)}
                                rows={3}
                                className="w-full rounded-lg border-gray-200 bg-gray-50 focus:ring-2 focus:ring-blue-500 focus:bg-white transition-all px-3 py-2"
                            />
                        </div>

                        <div className="flex gap-3 mt-6">
                            <button
                                type="button"
                                onClick={onClose}
                                className="flex-1 border border-gray-200 text-gray-700 py-3 rounded-xl font-bold hover:bg-gray-50 transition-colors"
                            >
                                Cancel
                            </button>
                            <button
                                type="submit"
                                disabled={submitting}
                                className="flex-1 bg-gray-900 hover:bg-blue-600 disabled:opacity-50 text-white py-3 rounded-xl font-bold transition-colors"
                            >
                                {submitting ? 'Sending...' : 'Send Request'}
                            </button>
                        </div>
                    </form>
                )}
            </div>
        </div>
    );
}
