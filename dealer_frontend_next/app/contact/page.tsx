import { getDealerConfig } from '@/lib/api';

export default async function ContactPage() {
    const config = await getDealerConfig();

    // Fallbacks
    const contactPhone = config.theme.contact_phone || "(555) 123-4567";
    const contactEmail = config.theme.contact_email || "sales@example.com";
    const contactAddress = config.theme.contact_address || "1234 Equipment Lane, Mower City, ST 12345";
    const contactText = config.theme.contact_text || "We are here to help you with all your power equipment needs.";

    return (
        <div className="max-w-2xl mx-auto">
            <h1 className="text-3xl font-bold mb-6">Contact Us</h1>
            <div className="bg-white p-6 rounded shadow border">
                <p className="mb-4 whitespace-pre-wrap">{contactText}</p>
                <div className="space-y-4">
                    <p><strong>Phone:</strong> {contactPhone}</p>
                    <p><strong>Email:</strong> <a href={`mailto:${contactEmail}`} className="text-blue-600 hover:underline">{contactEmail}</a></p>
                    <p><strong>Address:</strong> <span className="whitespace-pre-wrap">{contactAddress}</span></p>

                    {config.modules.facebook && config.facebook_page_id && (
                        <div className="pt-4 border-t">
                            <p className="font-bold mb-2">Social Media</p>
                            <a
                                href={`https://facebook.com/${config.facebook_page_id}`}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="flex items-center text-blue-600 hover:underline"
                            >
                                <svg className="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 24 24">
                                    <path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z" />
                                </svg>
                                Find us on Facebook
                            </a>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
