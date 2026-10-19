"""
Parses a dealer-uploaded Excel file of rental items (Name + rate/deposit/
minimum columns) for bulk import into RentalItem. Still no user-confirmed
column-mapping step (unlike parts_import_service.py, built for genuinely
arbitrary vendor layouts) - a rental price list is assumed to be close to
the template this app provides (see the rental.import_sample route) - but
header matching is substring-based like Parts import, not exact-match, so
headers like "Dealer Cost (USD)"-style variants with extra text still
match automatically.
"""
import pandas as pd
from decimal import Decimal, InvalidOperation

HEADER_ALIASES = {
    'name': ['name', 'item', 'item name', 'equipment', 'equipment name'],
    'rate_hourly': ['hourly rate', 'hour rate', 'hr rate', 'per hour', 'per hour rate'],
    'rate_4hr': ['4 hour rate', '4hr rate', '4 hr rate', '4hour rate', '4-hour rate'],
    'rate_8hr': ['8 hour rate', '8hr rate', '8 hr rate', '8hour rate', '8-hour rate'],
    'rate_24hr': ['24 hour rate', '24hr rate', '24 hr rate', '24hour rate', '24-hour rate', 'daily rate', 'day rate'],
    'rate_weekly': ['weekly rate', 'week rate', 'wk rate'],
    'deposit': ['deposit', 'deposit cost', 'deposit amount'],
    'minimum_rental_price': ['minimum rental price', 'minimum rental', 'minimum price', 'min rental price', 'min price'],
    'minimum_rental_hours': ['minimum rental hours', 'minimum hours', 'min rental hours', 'min hours'],
}

MONEY_FIELDS = ('rate_hourly', 'rate_4hr', 'rate_8hr', 'rate_24hr', 'rate_weekly', 'deposit', 'minimum_rental_price')

SAMPLE_HEADERS = ['Name', 'Hourly Rate', '4 Hour Rate', '8 Hour Rate', '24 Hour Rate', 'Weekly Rate',
                   'Deposit', 'Minimum Rental Price', 'Minimum Rental Hours']
SAMPLE_ROWS = [
    {'Name': 'Mini Excavator', 'Hourly Rate': '', '4 Hour Rate': '', '8 Hour Rate': '', '24 Hour Rate': '275.00',
     'Weekly Rate': '950.00', 'Deposit': '500.00', 'Minimum Rental Price': '', 'Minimum Rental Hours': ''},
    {'Name': 'Push Mower', 'Hourly Rate': '15.00', '4 Hour Rate': '35.00', '8 Hour Rate': '55.00', '24 Hour Rate': '75.00',
     'Weekly Rate': '225.00', 'Deposit': '', 'Minimum Rental Price': '48.00', 'Minimum Rental Hours': '2'},
]


def _build_column_map(headers):
    """Maps each HEADER_ALIASES field to the best-matching header, using
    substring containment like the Parts importer (so "Dealer Cost (USD)"-
    style headers with extra text still match) - but resolved via a
    longest-alias-wins greedy assignment across all fields at once, not
    matched per-field in isolation. That's needed because naive per-field
    substring matching has real collisions here: "24 Hour Rate" literally
    contains "4 Hour Rate" as a substring, and "8 Hour Rate" contains
    "Hour Rate" (the Hourly Rate field's alias). Scoring every (header,
    field, alias) match by alias length and assigning longest-first means
    the more specific match always wins each header, so a 24hr column can
    never be misclaimed by the 4hr field, etc."""
    candidates = []
    for header in headers:
        h = header.strip().lower()
        for field, aliases in HEADER_ALIASES.items():
            for alias in aliases:
                if alias in h:
                    candidates.append((len(alias), header, field))

    candidates.sort(key=lambda c: c[0], reverse=True)

    col_map = {}
    used_headers = set()
    used_fields = set()
    for _, header, field in candidates:
        if header in used_headers or field in used_fields:
            continue
        col_map[field] = header
        used_headers.add(header)
        used_fields.add(field)

    for field in HEADER_ALIASES:
        col_map.setdefault(field, None)

    return col_map


def parse_rental_file(file_path):
    """Returns (rows, errors). Each valid row is a dict with keys name,
    rate_hourly, rate_4hr, rate_8hr, rate_24hr, rate_weekly, deposit,
    minimum_rental_price (Decimal or None), and minimum_rental_hours (int
    or None). Each error is {'row_num': int, 'error': str}. Raises
    ValueError if no Name column can be matched at all (nothing usable to
    preview)."""
    df = pd.read_excel(file_path, dtype=str, engine='openpyxl')
    df = df.fillna('')
    headers = list(df.columns)
    col_map = _build_column_map(headers)

    if not col_map['name']:
        raise ValueError(
            "Couldn't find a 'Name' column in that file. "
            "Download the sample template for the expected format."
        )

    rows, errors = [], []
    for i, raw in df.iterrows():
        row_num = i + 2  # header is row 1
        name = str(raw[col_map['name']]).strip()
        if not name:
            errors.append({'row_num': row_num, 'error': 'Missing name'})
            continue

        parsed = {'name': name[:150]}
        bad = False
        for field in MONEY_FIELDS:
            col = col_map[field]
            raw_val = str(raw[col]).strip() if col else ''
            if not raw_val:
                parsed[field] = None
                continue
            try:
                parsed[field] = Decimal(raw_val.replace('$', '').replace(',', ''))
            except (InvalidOperation, ValueError):
                errors.append({'row_num': row_num, 'error': f"'{field.replace('_', ' ')}' value '{raw_val}' isn't a number"})
                bad = True
                break
        if bad:
            continue

        hours_col = col_map['minimum_rental_hours']
        raw_hours = str(raw[hours_col]).strip() if hours_col else ''
        if not raw_hours:
            parsed['minimum_rental_hours'] = None
        else:
            try:
                parsed['minimum_rental_hours'] = int(float(raw_hours))
            except ValueError:
                errors.append({'row_num': row_num, 'error': f"'minimum rental hours' value '{raw_hours}' isn't a whole number"})
                continue

        rows.append(parsed)

    return rows, errors
