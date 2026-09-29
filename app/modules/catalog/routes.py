import os
import re
from io import BytesIO

from flask import render_template, g, redirect, url_for, flash, request, send_file, abort
from flask_login import login_required

from . import catalog_bp
from app.core.extensions import db
from app.core.models import ManufacturerBrand, ManufacturerCatalogItem
from app.core.uploads import save_image_upload, save_image_from_url, UploadError, MAX_SPREADSHEET_BYTES


def _slugify(name):
    slug = re.sub(r'[^a-z0-9]+', '-', name.strip().lower()).strip('-')
    return slug or 'brand'


def _unique_slug(org_id, name, exclude_id=None):
    base = _slugify(name)
    slug = base
    n = 2
    while True:
        query = ManufacturerBrand.query.filter_by(organization_id=org_id, slug=slug)
        if exclude_id:
            query = query.filter(ManufacturerBrand.id != exclude_id)
        if not query.first():
            return slug
        slug = f"{base}-{n}"
        n += 1


def _save_upload(file_storage, org_id):
    return save_image_upload(file_storage, 'manufacturer_catalog', org_id)


@catalog_bp.route('/admin/manufacturer-catalog', methods=['GET'])
@login_required
def index():
    org = g.current_org
    brands = ManufacturerBrand.query.filter_by(organization_id=org.id).order_by(
        ManufacturerBrand.display_order, ManufacturerBrand.name).all()
    return render_template('catalog/index.html', brands=brands)


@catalog_bp.route('/admin/manufacturer-catalog/add', methods=['POST'])
@login_required
def add_brand():
    org = g.current_org
    name = (request.form.get('name') or '').strip()
    if not name:
        flash('Brand name is required.', 'danger')
        return redirect(url_for('catalog.index'))

    brand = ManufacturerBrand(
        organization_id=org.id,
        name=name,
        slug=_unique_slug(org.id, name),
        intro_text=(request.form.get('intro_text') or '').strip() or None,
    )

    logo = request.files.get('logo')
    if logo and logo.filename:
        try:
            brand.logo_url = _save_upload(logo, org.id)
        except UploadError as e:
            flash(str(e), 'danger')
            return redirect(url_for('catalog.index'))

    db.session.add(brand)
    db.session.commit()
    flash(f'"{brand.name}" brand page created.', 'success')
    return redirect(url_for('catalog.manage_brand', brand_id=brand.id))


@catalog_bp.route('/admin/manufacturer-catalog/<int:brand_id>', methods=['GET'])
@login_required
def manage_brand(brand_id):
    from app.core.models import Unit
    org = g.current_org
    brand = ManufacturerBrand.query.filter_by(id=brand_id, organization_id=org.id).first_or_404()
    items = ManufacturerCatalogItem.query.filter_by(brand_id=brand.id).order_by(
        ManufacturerCatalogItem.display_order, ManufacturerCatalogItem.id).all()

    # Suggest existing catalog categories AND real inventory's Unit.type values,
    # so a dealer typing "Stand-On Mowers" sees that "Stand On Mowers" already
    # exists elsewhere and can reuse the exact spelling instead of creating a
    # near-duplicate that won't merge in the /inventory filter.
    existing_categories = {item.category for item in
        ManufacturerCatalogItem.query.filter_by(organization_id=org.id).all() if item.category}
    existing_unit_types = {row[0] for row in
        db.session.query(Unit.type).filter_by(organization_id=org.id).distinct().all() if row[0]}
    categories = sorted(existing_categories | existing_unit_types)

    grouped = {}
    for item in items:
        grouped.setdefault(item.category or 'Uncategorized', []).append(item)
    # Uncategorized last, everything else alphabetical
    grouped_items = sorted(grouped.items(), key=lambda kv: (kv[0] == 'Uncategorized', kv[0]))

    return render_template('catalog/manage_brand.html', brand=brand, grouped_items=grouped_items, categories=categories)


@catalog_bp.route('/admin/manufacturer-catalog/<int:brand_id>/edit', methods=['POST'])
@login_required
def edit_brand(brand_id):
    org = g.current_org
    brand = ManufacturerBrand.query.filter_by(id=brand_id, organization_id=org.id).first_or_404()

    name = (request.form.get('name') or '').strip()
    if not name:
        flash('Brand name is required.', 'danger')
        return redirect(url_for('catalog.manage_brand', brand_id=brand.id))

    if name != brand.name:
        brand.slug = _unique_slug(org.id, name, exclude_id=brand.id)
    brand.name = name
    brand.intro_text = (request.form.get('intro_text') or '').strip() or None

    logo = request.files.get('logo')
    if logo and logo.filename:
        try:
            brand.logo_url = _save_upload(logo, org.id)
        except UploadError as e:
            flash(str(e), 'danger')
            return redirect(url_for('catalog.manage_brand', brand_id=brand.id))

    db.session.commit()
    flash('Brand updated.', 'success')
    return redirect(url_for('catalog.manage_brand', brand_id=brand.id))


@catalog_bp.route('/admin/manufacturer-catalog/<int:brand_id>/delete', methods=['POST'])
@login_required
def delete_brand(brand_id):
    org = g.current_org
    brand = ManufacturerBrand.query.filter_by(id=brand_id, organization_id=org.id).first_or_404()
    name = brand.name
    db.session.delete(brand)
    db.session.commit()
    flash(f'"{name}" brand page deleted.', 'success')
    return redirect(url_for('catalog.index'))


@catalog_bp.route('/admin/manufacturer-catalog/<int:brand_id>/items/add', methods=['POST'])
@login_required
def add_item(brand_id):
    org = g.current_org
    brand = ManufacturerBrand.query.filter_by(id=brand_id, organization_id=org.id).first_or_404()

    model_name = (request.form.get('model_name') or '').strip()
    if not model_name:
        flash('Model name is required.', 'danger')
        return redirect(url_for('catalog.manage_brand', brand_id=brand.id))

    item = ManufacturerCatalogItem(
        organization_id=org.id,
        brand_id=brand.id,
        model_name=model_name,
        category=(request.form.get('category') or '').strip() or None,
        description=(request.form.get('description') or '').strip() or None,
    )

    photo = request.files.get('photo')
    if photo and photo.filename:
        try:
            item.image_url = _save_upload(photo, org.id)
        except UploadError as e:
            flash(str(e), 'danger')
            return redirect(url_for('catalog.manage_brand', brand_id=brand.id))

    db.session.add(item)
    db.session.commit()
    flash(f'"{item.model_name}" added.', 'success')
    return redirect(url_for('catalog.manage_brand', brand_id=brand.id))


@catalog_bp.route('/admin/manufacturer-catalog/<int:brand_id>/items/<int:item_id>/edit', methods=['POST'])
@login_required
def edit_item(brand_id, item_id):
    org = g.current_org
    brand = ManufacturerBrand.query.filter_by(id=brand_id, organization_id=org.id).first_or_404()
    item = ManufacturerCatalogItem.query.filter_by(id=item_id, brand_id=brand.id).first_or_404()

    model_name = (request.form.get('model_name') or '').strip()
    if not model_name:
        flash('Model name is required.', 'danger')
        return redirect(url_for('catalog.manage_brand', brand_id=brand.id))

    item.model_name = model_name
    item.category = (request.form.get('category') or '').strip() or None
    item.description = (request.form.get('description') or '').strip() or None
    item.is_active = request.form.get('is_active') == 'on'

    photo = request.files.get('photo')
    if photo and photo.filename:
        try:
            item.image_url = _save_upload(photo, org.id)
        except UploadError as e:
            flash(str(e), 'danger')
            return redirect(url_for('catalog.manage_brand', brand_id=brand.id))

    db.session.commit()
    flash('Model updated.', 'success')
    return redirect(url_for('catalog.manage_brand', brand_id=brand.id))


@catalog_bp.route('/admin/manufacturer-catalog/<int:brand_id>/items/import', methods=['POST'])
@login_required
def import_items(brand_id):
    """
    Bulk create/update this brand's models from an uploaded .xlsx/.csv, so a
    whole manufacturer lineup can be loaded in one shot instead of the
    one-model-at-a-time form. Expected columns (case-insensitive, a few
    common aliases accepted): Model Name (required), Category, Description,
    Image URL. Matches existing items by model name (case-insensitive) within
    this brand and updates them instead of duplicating, so the same file can
    be re-uploaded after edits without piling up duplicates.
    """
    import pandas as pd

    org = g.current_org
    brand = ManufacturerBrand.query.filter_by(id=brand_id, organization_id=org.id).first_or_404()

    file = request.files.get('spreadsheet')
    if not file or not file.filename:
        flash('Choose a .xlsx or .csv file first.', 'danger')
        return redirect(url_for('catalog.manage_brand', brand_id=brand.id))

    file.stream.seek(0, os.SEEK_END)
    size = file.stream.tell()
    file.stream.seek(0)
    if size > MAX_SPREADSHEET_BYTES:
        flash(f"File is too large ({size // (1024 * 1024)}MB). "
              f"Max size is {MAX_SPREADSHEET_BYTES // (1024 * 1024)}MB.", 'danger')
        return redirect(url_for('catalog.manage_brand', brand_id=brand.id))

    ext = os.path.splitext(file.filename)[1].lower()
    try:
        if ext == '.csv':
            df = pd.read_csv(file)
        elif ext in ('.xlsx', '.xls'):
            df = pd.read_excel(file)
        else:
            flash(f"Unsupported file type '{ext}'. Upload a .xlsx or .csv file.", 'danger')
            return redirect(url_for('catalog.manage_brand', brand_id=brand.id))
    except Exception as e:
        flash(f"Couldn't read that file: {e}", 'danger')
        return redirect(url_for('catalog.manage_brand', brand_id=brand.id))

    col_map = {}
    for col in df.columns:
        key = str(col).strip().lower()
        if key in ('model name', 'model', 'name'):
            col_map['model_name'] = col
        elif key in ('category', 'type'):
            col_map['category'] = col
        elif key in ('description', 'desc'):
            col_map['description'] = col
        elif key in ('image url', 'image', 'photo url', 'photo'):
            col_map['image_url'] = col

    if 'model_name' not in col_map:
        flash('Spreadsheet needs a "Model Name" column.', 'danger')
        return redirect(url_for('catalog.manage_brand', brand_id=brand.id))

    def cell(row, key):
        if key not in col_map:
            return None
        val = row.get(col_map[key])
        if val is None:
            return None
        text = str(val).strip()
        return text if text and text.lower() != 'nan' else None

    existing_by_name = {
        item.model_name.strip().lower(): item
        for item in ManufacturerCatalogItem.query.filter_by(brand_id=brand.id).all()
    }

    created = updated = skipped = image_failures = 0

    for _, row in df.iterrows():
        model_name = cell(row, 'model_name')
        if not model_name:
            skipped += 1
            continue

        existing = existing_by_name.get(model_name.lower())
        if existing:
            item = existing
            updated += 1
        else:
            item = ManufacturerCatalogItem(organization_id=org.id, brand_id=brand.id, model_name=model_name)
            db.session.add(item)
            existing_by_name[model_name.lower()] = item
            created += 1

        item.model_name = model_name
        item.category = cell(row, 'category')
        item.description = cell(row, 'description')

        image_url_value = cell(row, 'image_url')
        if image_url_value:
            try:
                item.image_url = save_image_from_url(image_url_value, 'manufacturer_catalog', org.id)
            except UploadError:
                image_failures += 1

    db.session.commit()

    summary = f"Imported: {created} new, {updated} updated"
    if skipped:
        summary += f", {skipped} row(s) skipped (no model name)"
    if image_failures:
        summary += f", {image_failures} image(s) couldn't be fetched"
    flash(summary, 'warning' if image_failures else 'success')
    return redirect(url_for('catalog.manage_brand', brand_id=brand.id))


@catalog_bp.route('/admin/manufacturer-catalog/<int:brand_id>/export', methods=['GET'])
@login_required
def export_items(brand_id):
    """
    Super Admin only: exports a brand's models in the exact column format
    import_items() reads, so a brand built once on one dealer's site can be
    downloaded and re-uploaded onto another's (typically while impersonating
    it) instead of re-entering it or juggling a spreadsheet kept elsewhere.
    Deliberately not offered to dealers - g.is_superuser stays true for the
    whole time a Super Admin is impersonating a dealer, so this works the
    same way from an impersonated session as from their own.
    """
    import pandas as pd

    if not g.is_superuser:
        abort(403)

    org = g.current_org
    brand = ManufacturerBrand.query.filter_by(id=brand_id, organization_id=org.id).first_or_404()
    items = ManufacturerCatalogItem.query.filter_by(brand_id=brand.id).order_by(
        ManufacturerCatalogItem.display_order, ManufacturerCatalogItem.id).all()

    # image_url is stored relative (e.g. /static/uploads/...) - has to be
    # made absolute against *this* org's own public domain, since importing
    # it elsewhere means fetching it back over the network from wherever it
    # actually lives, not from the destination site.
    def _absolute_image_url(url):
        if not url:
            return ''
        return f"https://{org.slug}.bentcrankshaft.com{url}"

    df = pd.DataFrame([{
        'Model Name': item.model_name,
        'Category': item.category or '',
        'Description': item.description or '',
        'Image URL': _absolute_image_url(item.image_url),
    } for item in items])

    file_format = request.args.get('format', 'xlsx')
    buffer = BytesIO()
    if file_format == 'csv':
        df.to_csv(buffer, index=False)
        mimetype = 'text/csv'
        ext = 'csv'
    else:
        df.to_excel(buffer, index=False)
        mimetype = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        ext = 'xlsx'
    buffer.seek(0)

    download_name = f"{brand.slug}-catalog.{ext}"
    return send_file(buffer, mimetype=mimetype, as_attachment=True, download_name=download_name)


@catalog_bp.route('/admin/manufacturer-catalog/<int:brand_id>/items/<int:item_id>/delete', methods=['POST'])
@login_required
def delete_item(brand_id, item_id):
    org = g.current_org
    brand = ManufacturerBrand.query.filter_by(id=brand_id, organization_id=org.id).first_or_404()
    item = ManufacturerCatalogItem.query.filter_by(id=item_id, brand_id=brand.id).first_or_404()
    db.session.delete(item)
    db.session.commit()
    flash('Model removed.', 'success')
    return redirect(url_for('catalog.manage_brand', brand_id=brand.id))
