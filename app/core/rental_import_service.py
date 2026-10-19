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
import re
import pandas as pd
from decimal import Decimal, InvalidOperation

HEADER_ALIASES = {
    'name': ['name', 'item', 'item name', 'equipment', 'equipment name'],
    'category': ['category', 'section', 'group', 'type'],
    # Bare forms ('hourly', '4 hour', etc., with no "Rate" suffix) are
    # listed alongside the "...Rate" forms since real dealer sheets often
    # omit the word "Rate" entirely (column just says "Hourly", "4 Hour").
    # 'hourly' (not bare 'hour') and the digit-prefixed bare forms are
    # chosen specifically so they can't collide with each other - see
    # _build_column_map's longest-match-wins resolution for how "24 Hour"
    # vs "4 Hour" is still disambiguated correctly either way.
    'rate_hourly': ['hourly rate', 'hour rate', 'hr rate', 'per hour', 'per hour rate', 'hourly'],
    'rate_4hr': ['4 hour rate', '4hr rate', '4 hr rate', '4hour rate', '4-hour rate', '4 hour', '4hr', '4 hr'],
    'rate_8hr': ['8 hour rate', '8hr rate', '8 hr rate', '8hour rate', '8-hour rate', '8 hour', '8hr', '8 hr'],
    'rate_24hr': ['24 hour rate', '24hr rate', '24 hr rate', '24hour rate', '24-hour rate', 'daily rate', 'day rate',
                  '24 hour', '24hr', '24 hr', 'daily'],
    'rate_weekly': ['weekly rate', 'week rate', 'wk rate', 'weekly'],
    'deposit': ['deposit', 'deposit cost', 'deposit amount'],
    'minimum_rental_price': ['minimum rental price', 'minimum rental', 'minimum price', 'min rental price', 'min price'],
    # Bare 'minimum' included for sheets with just a "Minimum" column
    # holding a duration like "2 Hours" (text, not a plain number - see the
    # dedicated parsing below) rather than a separate price+hours pair.
    # Deliberately not 'min' alone - too short, risks matching inside an
    # unrelated word (e.g. "Admin").
    'minimum_rental_hours': ['minimum rental hours', 'minimum hours', 'min rental hours', 'min hours', 'minimum'],
}

MONEY_FIELDS = ('rate_hourly', 'rate_4hr', 'rate_8hr', 'rate_24hr', 'rate_weekly', 'deposit', 'minimum_rental_price')

SAMPLE_HEADERS = ['Name', 'Category', 'Hourly Rate', '4 Hour Rate', '8 Hour Rate', '24 Hour Rate', 'Weekly Rate',
                   'Deposit', 'Minimum Rental Price', 'Minimum Rental Hours']
SAMPLE_ROWS = [
    {'Name': 'Mini Excavator', 'Category': 'Construction Equipment', 'Hourly Rate': '', '4 Hour Rate': '',
     '8 Hour Rate': '', '24 Hour Rate': '275.00', 'Weekly Rate': '950.00', 'Deposit': '500.00',
     'Minimum Rental Price': '', 'Minimum Rental Hours': ''},
    {'Name': 'Push Mower', 'Category': 'Lawn and Garden', 'Hourly Rate': '15.00', '4 Hour Rate': '35.00',
     '8 Hour Rate': '55.00', '24 Hour Rate': '75.00', 'Weekly Rate': '225.00', 'Deposit': '',
     'Minimum Rental Price': '48.00', 'Minimum Rental Hours': '2'},
]

# Some dealer price sheets repeat a category heading on continuation pages
# as e.g. "Lawn and Garden Cont." - strip that suffix so it doesn't create
# a separate, duplicate category from the real one.
_CONT_SUFFIX_RE = re.compile(r'\s+cont(?:inued)?\.?\s*$', re.IGNORECASE)

# Pulls the leading number out of a minimum-hours cell that spells out the
# unit, e.g. "2 Hours" or "1 Hour", not just a bare "2".
_LEADING_NUMBER_RE = re.compile(r'(\d+(?:\.\d+)?)')


def _normalize_category(raw):
    value = raw.strip()
    if not value:
        return None
    value = _CONT_SUFFIX_RE.sub('', value).strip()
    return value[:100] or None


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
    category (str or None - a trailing "Cont."/"Continued" suffix some
    price sheets repeat on later pages is stripped automatically),
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

        category_col = col_map['category']
        raw_category = str(raw[category_col]).strip() if category_col else ''
        parsed = {'name': name[:150], 'category': _normalize_category(raw_category)}
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
            # Tolerates both a bare number ("2") and a dealer writing the
            # unit out ("2 Hours", "1 Hour") - pulls the leading number
            # either way rather than requiring an exact numeric cell.
            m = _LEADING_NUMBER_RE.search(raw_hours)
            if not m:
                errors.append({'row_num': row_num, 'error': f"'minimum rental hours' value '{raw_hours}' isn't a whole number"})
                continue
            parsed['minimum_rental_hours'] = int(float(m.group(1)))

        rows.append(parsed)

    return rows, errors
