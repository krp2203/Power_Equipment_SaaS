#!/usr/bin/env python3
"""Fix theme_config for all organizations - add brand_logos and primaryColor."""
import json
import psycopg2

conn = psycopg2.connect("postgresql://user:password@db:5432/dealer_dashboard")
cur = conn.cursor()

# Brand logos for org 1 (Demo Dealer / Master)
org1_brands = {
    "1": "/static/uploads/brands/1_brand_1_little_wonder_logo.jpg",
    "2": "/static/uploads/brands/1_brand_1_redmax_logo.png",
    "3": "/static/uploads/brands/1_brand_1_ryan_logo.jpg",
    "4": "/static/uploads/brands/1_brand_4_bluebird_logo.png",
    "5": "/static/uploads/brands/1_brand_5_Logo.png",
    "6": "/static/uploads/brands/1_brand_6_Briggs_Logo.png",
    "7": "/static/uploads/brands/1_brand_7_Kohler_logo.png",
    "8": "/static/uploads/brands/1_brand_8_SCAG_LOGO.jpg",
}

# Brand logos for org 3 (Ken's Mowers) - same brand pool as org 1
org3_brands = {
    "1": "/static/uploads/brands/1_brand_1_little_wonder_logo.jpg",
    "2": "/static/uploads/brands/1_brand_1_redmax_logo.png",
    "3": "/static/uploads/brands/1_brand_1_ryan_logo.jpg",
    "4": "/static/uploads/brands/1_brand_4_bluebird_logo.png",
    "5": "/static/uploads/brands/1_brand_5_Logo.png",
    "6": "/static/uploads/brands/1_brand_6_Briggs_Logo.png",
    "7": "/static/uploads/brands/1_brand_7_Kohler_logo.png",
}

# Brand logos for org 5 (NC Power Equipment)
org5_brands = {
    "1": "/static/uploads/brands/10_brand_1_NewBBLogo_Blue_100_85_5_22.jpg",
    "2": "/static/uploads/brands/10_brand_2_briggs-stratton_logo_transparent.png",
    "3": "/static/uploads/brands/10_brand_3_Kohler.jpg",
    "4": "/static/uploads/brands/10_brand_5_STIHL_LOGO.png",
    "5": "/static/uploads/brands/10_brand_6_TORO_LOGO.png",
    "6": "/static/uploads/brands/10_brand_7_WALKER_LOGO.png",
}

updates = [
    (1, {"primaryColor": "#2563eb", "brand_logos": org1_brands}),
    (3, {"primaryColor": "#16a34a", "brand_logos": org3_brands}),  # Ken's Mowers GREEN (was incorrectly BLUE)
    (5, {"primaryColor": "#ea580c", "brand_logos": org5_brands}),  # NC Power ORANGE
]

for org_id, patch in updates:
    cur.execute("SELECT theme_config FROM organization WHERE id = %s", (org_id,))
    row = cur.fetchone()
    if not row:
        print(f"Org {org_id} not found")
        continue
    current = row[0] or {}
    if isinstance(current, str):
        current = json.loads(current)
    current.update(patch)
    cur.execute(
        "UPDATE organization SET theme_config = %s WHERE id = %s",
        (json.dumps(current), org_id)
    )
    print(f"Updated org {org_id}: brand_logos count = {len(current.get('brand_logos', {}))}, primaryColor = {current.get('primaryColor')}")

conn.commit()
cur.close()
conn.close()
print("Done!")
