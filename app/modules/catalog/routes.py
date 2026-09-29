import os
import re
import uuid

from flask import render_template, g, redirect, url_for, flash, request, current_app
from flask_login import login_required
from werkzeug.utils import secure_filename

from . import catalog_bp
from app.core.extensions import db
from app.core.models import ManufacturerBrand, ManufacturerCatalogItem


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
    filename = secure_filename(file_storage.filename)
    ext = os.path.splitext(filename)[1]
    upload_dir = os.path.join(current_app.root_path, 'static', 'uploads', 'manufacturer_catalog', str(org_id))
    os.makedirs(upload_dir, exist_ok=True)
    unique_filename = f"{uuid.uuid4().hex}{ext}"
    file_storage.save(os.path.join(upload_dir, unique_filename))
    return f"/static/uploads/manufacturer_catalog/{org_id}/{unique_filename}"


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
        brand.logo_url = _save_upload(logo, org.id)

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
        brand.logo_url = _save_upload(logo, org.id)

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
        item.image_url = _save_upload(photo, org.id)

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
        item.image_url = _save_upload(photo, org.id)

    db.session.commit()
    flash('Model updated.', 'success')
    return redirect(url_for('catalog.manage_brand', brand_id=brand.id))


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
