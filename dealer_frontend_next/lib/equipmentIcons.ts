// Generic clipart for services/rental items that don't have a dealer-
// uploaded image - matched by keyword against the item name so the
// Service Manager's preloaded starter catalog (and most custom names, in
// both Service Manager and the Rental catalog) get a sensible icon for
// free. Shared between ServiceScheduler.tsx and RentalCatalog.tsx since
// the two catalogs plausibly overlap (mowers, generators, chainsaws,
// tillers are both serviceable and rentable).
const ICON_KEYWORDS: Array<[string, string]> = [
    ['chainsaw', '🪚'],
    ['generator', '🔌'],
    ['leaf blower', '🍃'],
    ['power washer', '🚿'],
    ['pressure washer', '🚿'],
    ['snowthrower', '❄️'],
    ['snow blower', '❄️'],
    ['trimmer', '✂️'],
    ['edger', '✂️'],
    ['tiller', '🌱'],
    ['cultivator', '🌱'],
    ['excavator', '🚧'],
    ['tractor', '🚜'],
    ['zero-turn', '🚜'],
    ['riding mower', '🚜'],
    ['mower', '🌿'],
    ['utv', '🛻'],
    ['atv', '🛻'],
];

export function genericEquipmentIcon(name: string): string {
    const lower = name.toLowerCase();
    for (const [keyword, icon] of ICON_KEYWORDS) {
        if (lower.includes(keyword)) return icon;
    }
    return '🛠️';
}
