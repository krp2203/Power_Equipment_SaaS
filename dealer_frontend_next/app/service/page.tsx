import ServiceScheduler from '@/components/ServiceScheduler';
import { getDealerConfig } from '@/lib/api';

export default async function ServicePage() {
    const config = await getDealerConfig();

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
                            {parts.map(part => (
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
                                        <div className="text-xs text-gray-600 line-clamp-2 flex-grow">{part.description}</div>
                                    </div>
                                </div>
                            ))}
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
        </div>
    );
}
