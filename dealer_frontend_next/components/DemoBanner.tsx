import Link from 'next/link';

export default function DemoBanner() {
    return (
        <div className="bg-gradient-to-r from-blue-600 via-blue-700 to-blue-800 text-white">
            <div className="container mx-auto px-4 py-6">
                <div className="flex flex-col md:flex-row items-center justify-between gap-4">
                    <div className="flex items-center gap-4">
                        <span className="bg-yellow-400 text-blue-900 px-4 py-2 rounded-full font-bold text-sm uppercase tracking-wide shadow-lg">
                            Demo Site
                        </span>
                        <div className="text-center md:text-left">
                            <p className="text-lg md:text-xl font-semibold">
                                This is a demonstration of our Power Equipment Dealer Platform
                            </p>
                            <p className="text-sm md:text-base text-blue-100 mt-1">
                                Explore the features and see how we can help your dealership grow
                            </p>
                        </div>
                    </div>
                    <div className="flex gap-3">
                        <Link
                            href="/contact"
                            className="bg-white text-blue-700 px-6 py-3 rounded-lg font-semibold hover:bg-blue-50 transition-colors shadow-lg whitespace-nowrap"
                        >
                            Request Demo
                        </Link>
                        <a
                            href="/marketing/dashboard"
                            className="bg-blue-900 text-white px-6 py-3 rounded-lg font-semibold hover:bg-blue-950 transition-colors shadow-lg whitespace-nowrap border-2 border-blue-400"
                        >
                            Dealer Portal Login
                        </a>
                    </div>
                </div>
            </div>
        </div>
    );
}
