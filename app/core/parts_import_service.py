"""
Parses vendor/manufacturer part price files (CSV or Excel) for bulk import
into PartInventory. Every vendor names its columns differently (confirmed
against real Briggs & Stratton, Scag, Wright, and Kubota price files), so
this never assumes a fixed header set — callers always supply an explicit
column mapping (auto-suggested, but user-confirmed) before rows are used
for anything beyond a raw preview.
"""
import os
import re
import pandas as pd
from decimal import Decimal, InvalidOperation

# Target PartInventory fields a column can be mapped to.
IMPORT_FIELDS = {
    'manufacturer': 'Manufacturer',
    'part_number': 'Part Number',
    'description': 'Description',
    'dealer_cost': 'Dealer Cost',
    'retail_price': 'Retail / List Price',
    'upc': 'UPC / Barcode',
    'superseded_to': 'Superseded / Replaced By',
}
REQUIRED_FIELDS = ('part_number', 'dealer_cost')

# Header text -> target field, for auto-suggesting a mapping. Checked as a
# case-insensitive substring/exact match against each source column header.
HEADER_HINTS = {
    'manufacturer': ['mfg', 'manufacturer', 'brand', 'vendor'],
    'part_number': ['part number', 'part #', 'part no', 'partnumber', 'sku'],
    'description': ['description', 'desc'],
    'dealer_cost': ['dealer cost', 'dealer price', 'cost', 'your price', 'net price'],
    'retail_price': ['list price', 'retail price', 'msrp', 'list'],
    'upc': ['upc', 'barcode'],
    'superseded_to': ['replaced by', 'superseded to', 'replacement'],
}

EXCEL_FORMULA_WRAP = re.compile(r'^="(.*)"$')


def _read_dataframe(file_path, filename):
    ext = os.path.splitext(filename)[1].lower()
    if ext in ('.xlsx', '.xls'):
        df = pd.read_excel(file_path, dtype=str, engine='openpyxl' if ext == '.xlsx' else None)
    else:
        try:
            df = pd.read_csv(file_path, dtype=str, encoding='utf-8-sig')
        except UnicodeDecodeError:
            df = pd.read_csv(file_path, dtype=str, encoding='latin-1')
    df = df.fillna('')
    # Strip Excel's ="..." formula wrapper some vendors use on codes/barcodes
    # to preserve leading zeros, and normalize whitespace.
    for col in df.columns:
        df[col] = df[col].astype(str).map(lambda v: EXCEL_FORMULA_WRAP.sub(r'\1', v.strip()))
    return df


def get_headers_and_sample(file_path, filename, sample_rows=5):
    """Returns (headers: list[str], sample: list[dict], row_count: int)."""
    df = _read_dataframe(file_path, filename)
    headers = list(df.columns)
    sample = df.head(sample_rows).to_dict(orient='records')
    return headers, sample, len(df)


def suggest_mapping(headers):
    """Best-effort auto-mapping of source headers -> target fields."""
    mapping = {}
    used_headers = set()
    for field, hints in HEADER_HINTS.items():
        best = None
        for header in headers:
            if header in used_headers:
                continue
            h = header.strip().lower()
            if h in hints or any(hint in h for hint in hints):
                best = header
                break
        if best:
            mapping[field] = best
            used_headers.add(best)
    return mapping


def _clean_part_number(value):
    value = str(value).strip()
    if value.endswith('.0') and value[:-2].isdigit():
        value = value[:-2]
    return value


def _parse_money(value):
    value = str(value).strip().replace('$', '').replace(',', '')
    if value == '':
        return None
    try:
        return Decimal(value)
    except InvalidOperation:
        return None


def parse_rows(file_path, filename, column_mapping, manufacturer_default=None):
    """
    column_mapping: {target_field: source_header_or_''}
    manufacturer_default: applied to any row whose mapped manufacturer cell is
        blank (or when no manufacturer column is mapped at all) - for vendor
        files that don't name the manufacturer anywhere in the data.
    Returns a list of dicts, each either:
      {'row_num': int, 'error': str, 'raw': {...}}
    or:
      {'row_num': int, 'part_number': str, 'manufacturer': str|None,
       'description': str|None, 'dealer_cost': Decimal|None,
       'retail_price': Decimal|None, 'upc': str|None, 'superseded_to': str|None}
    """
    df = _read_dataframe(file_path, filename)
    results = []
    manufacturer_default = (manufacturer_default or '').strip() or None

    for i, row in enumerate(df.to_dict(orient='records')):
        row_num = i + 2  # +1 for header row, +1 for 1-indexing

        def get(field):
            header = column_mapping.get(field)
            if not header:
                return ''
            return str(row.get(header, '')).strip()

        part_number = _clean_part_number(get('part_number'))
        if not part_number:
            results.append({'row_num': row_num, 'error': 'Missing part number', 'raw': row})
            continue

        dealer_cost_raw = get('dealer_cost')
        dealer_cost = _parse_money(dealer_cost_raw) if dealer_cost_raw else None
        if dealer_cost_raw and dealer_cost is None:
            results.append({'row_num': row_num, 'error': f"Invalid dealer cost: '{dealer_cost_raw}'", 'raw': row})
            continue

        retail_price = _parse_money(get('retail_price')) if column_mapping.get('retail_price') else None

        results.append({
            'row_num': row_num,
            'part_number': part_number,
            'manufacturer': get('manufacturer') or manufacturer_default,
            'description': get('description') or None,
            'dealer_cost': dealer_cost,
            'retail_price': retail_price,
            'upc': get('upc') or None,
            'superseded_to': get('superseded_to') or None,
        })

    return results
