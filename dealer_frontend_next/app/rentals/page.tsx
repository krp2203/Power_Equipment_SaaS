import RentalCatalog from '@/components/RentalCatalog';
import { getDealerConfig } from '@/lib/api';

export default async function RentalsPage() {
    const config = await getDealerConfig();

    return (
        <div className="max-w-7xl mx-auto px-4 py-12">
            <h1 className="text-3xl font-bold mb-6 text-center">Equipment Rentals</h1>
            <RentalCatalog initialConfig={config} />
        </div>
    );
}
