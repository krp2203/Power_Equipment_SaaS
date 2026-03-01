import ServiceScheduler from '@/components/ServiceScheduler';
import { getDealerConfig } from '@/lib/api';

export default async function ServicePage() {
    const config = await getDealerConfig();

    return (
        <div className="max-w-7xl mx-auto px-4 py-12">
            <h1 className="text-3xl font-bold mb-6 text-center">Service Department</h1>
            <ServiceScheduler initialConfig={config} />
        </div>
    );
}
