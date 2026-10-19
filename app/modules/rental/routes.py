import os
import tempfile
import uuid
from io import BytesIO

from flask import render_template, request, flash, redirect, url_for, g, jsonify, send_file
from flask_login import login_required
from sqlalchemy import func as sa_func

from app.core.extensions import db
from app.core.models import RentalItem
from app.core.uploads import save_image_upload, UploadError
from . import rental_bp
from .forms import RentalItemForm


def _flash_form_errors(form):
    """Flashes each field's validation error by name, same helper used in
    app/modules/settings/routes.py for other dealer-configurable lists."""
    for field_name, errors in form.errors.items():
        label = getattr(form, field_name).label.text
        for error in errors:
            flash(f"{label}: {error}", "danger")


# ====== RENTAL ITEM CRUD ======

@rental_bp.route('/', methods=['GET'])
@login_required
def index():
    org = g.current_org
    items = (RentalItem.query.filter_by(organization_id=org.id)
             .order_by(RentalItem.sort_order, RentalItem.id).all())
    form = RentalItemForm()
    # Distinct categories in display order (not alphabetical), for the
    # category filter dropdown - matches how the public page orders its
    # category filter boxes.
    categories = []
    for item in items:
        if item.category and item.category not in categories:
            categories.append(item.category)
    return render_template('rental/index.html', items=items, form=form, categories=categories)


@rental_bp.route('/add', methods=['POST'])
@login_required
def add_item():
    org = g.current_org
    form = RentalItemForm()

    if form.validate_on_submit():
        max_sort = db.session.query(sa_func.max(RentalItem.sort_order)).filter_by(
            organization_id=org.id).scalar() or 0
        item = RentalItem(
            organization_id=org.id,
            name=form.name.data,
            category=(form.category.data or '').strip() or None,
            rate_hourly=form.rate_hourly.data,
            rate_4hr=form.rate_4hr.data,
            rate_8hr=form.rate_8hr.data,
            rate_24hr=form.rate_24hr.data,
            rate_weekly=form.rate_weekly.data,
            deposit=form.deposit.data,
            minimum_rental_price=form.minimum_rental_price.data,
            minimum_rental_hours=form.minimum_rental_hours.data,
            sort_order=max_sort + 1,
        )
        if form.image.data:
            try:
                item.image_url = save_image_upload(form.image.data, 'rentals', org.id)
            except UploadError as e:
                flash(str(e), "danger")
                return redirect(url_for('rental.index'))
        db.session.add(item)
        db.session.commit()
        flash("Rental item added.", "success")
    else:
        _flash_form_errors(form)

    return redirect(url_for('rental.index'))


@rental_bp.route('/<int:item_id>/edit', methods=['POST'])
@login_required
def edit_item(item_id):
    org = g.current_org
    item = RentalItem.query.filter_by(id=item_id, organization_id=org.id).first_or_404()
    form = RentalItemForm()

    if form.validate_on_submit():
        item.name = form.name.data
        item.category = (form.category.data or '').strip() or None
        item.rate_hourly = form.rate_hourly.data
        item.rate_4hr = form.rate_4hr.data
        item.rate_8hr = form.rate_8hr.data
        item.rate_24hr = form.rate_24hr.data
        item.rate_weekly = form.rate_weekly.data
        item.deposit = form.deposit.data
        item.minimum_rental_price = form.minimum_rental_price.data
        item.minimum_rental_hours = form.minimum_rental_hours.data
        if form.image.data:
            try:
                item.image_url = save_image_upload(form.image.data, 'rentals', org.id)
            except UploadError as e:
                flash(str(e), "danger")
                return redirect(url_for('rental.index'))
        elif request.form.get('remove_image'):
            item.image_url = None
        db.session.commit()
        flash("Rental item updated.", "success")
    else:
        _flash_form_errors(form)

    return redirect(url_for('rental.index'))


@rental_bp.route('/<int:item_id>/delete', methods=['POST'])
@login_required
def delete_item(item_id):
    org = g.current_org
    item = RentalItem.query.filter_by(id=item_id, organization_id=org.id).first_or_404()
    db.session.delete(item)
    db.session.commit()
    flash("Rental item removed.", "success")
    return redirect(url_for('rental.index'))


@rental_bp.route('/<int:item_id>/toggle-active', methods=['POST'])
@login_required
def toggle_item_active(item_id):
    """AJAX: flip a single item's active flag from the Rental Manager list."""
    item = RentalItem.query.filter_by(id=item_id, organization_id=g.current_org.id).first()
    if not item:
        return jsonify({'error': 'Rental item not found'}), 404
    item.is_active = not item.is_active
    db.session.commit()
    return jsonify({'id': item.id, 'is_active': item.is_active})


@rental_bp.route('/<int:item_id>/move/<direction>', methods=['POST'])
@login_required
def move_item(item_id, direction):
    org = g.current_org
    item = RentalItem.query.filter_by(id=item_id, organization_id=org.id).first_or_404()

    items = (RentalItem.query.filter_by(organization_id=org.id)
             .order_by(RentalItem.sort_order, RentalItem.id).all())
    idx = next((i for i, r in enumerate(items) if r.id == item.id), None)
    if idx is None:
        return redirect(url_for('rental.index'))

    swap_idx = idx - 1 if direction == 'up' else idx + 1 if direction == 'down' else None
    if swap_idx is not None and 0 <= swap_idx < len(items):
        other = items[swap_idx]
        item.sort_order, other.sort_order = other.sort_order, item.sort_order
        db.session.commit()

    return redirect(url_for('rental.index'))


# ====== EXCEL BULK IMPORT ======

RENTAL_UPLOAD_EXTS = ('.xlsx', '.xls')


def _rental_import_dir(org_id):
    d = os.path.join(tempfile.gettempdir(), 'rental_import', str(org_id))
    os.makedirs(d, exist_ok=True)
    return d


@rental_bp.route('/import', methods=['GET'])
@login_required
def import_start():
    return render_template('rental/import_start.html')


@rental_bp.route('/import/sample', methods=['GET'])
@login_required
def import_sample():
    import pandas as pd
    from app.core.rental_import_service import SAMPLE_HEADERS, SAMPLE_ROWS

    df = pd.DataFrame(SAMPLE_ROWS, columns=SAMPLE_HEADERS)
    buffer = BytesIO()
    df.to_excel(buffer, index=False)
    buffer.seek(0)
    return send_file(
        buffer,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name='rental_items_template.xlsx',
    )


@rental_bp.route('/import/upload', methods=['POST'])
@login_required
def import_upload():
    from app.core.rental_import_service import parse_rental_file

    file = request.files.get('rental_file')
    if not file or not file.filename:
        flash('Please choose an Excel file to upload.', 'danger')
        return redirect(url_for('rental.import_start'))

    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in RENTAL_UPLOAD_EXTS:
        flash('File must be a .xlsx or .xls file.', 'danger')
        return redirect(url_for('rental.import_start'))

    upload_id = f"{uuid.uuid4().hex}{ext}"
    saved_path = os.path.join(_rental_import_dir(g.current_org.id), upload_id)
    file.save(saved_path)

    try:
        rows, errors = parse_rental_file(saved_path)
    except ValueError as e:
        os.remove(saved_path)
        flash(str(e), 'danger')
        return redirect(url_for('rental.import_start'))

    return render_template(
        'rental/import_preview.html',
        upload_id=upload_id,
        preview_rows=rows[:100],
        error_rows=errors[:100],
        total_rows=len(rows) + len(errors),
        valid_count=len(rows),
        error_count=len(errors),
    )


@rental_bp.route('/import/confirm', methods=['POST'])
@login_required
def import_confirm():
    from app.core.rental_import_service import parse_rental_file

    org = g.current_org
    upload_id = request.form.get('upload_id', '')
    saved_path = os.path.join(_rental_import_dir(org.id), upload_id)
    if not upload_id or not os.path.isfile(saved_path):
        flash('That upload has expired. Please upload the file again.', 'danger')
        return redirect(url_for('rental.import_start'))

    try:
        rows, errors = parse_rental_file(saved_path)
    except ValueError as e:
        flash(str(e), 'danger')
        return redirect(url_for('rental.import_start'))
    finally:
        try:
            os.remove(saved_path)
        except OSError:
            pass

    max_sort = db.session.query(sa_func.max(RentalItem.sort_order)).filter_by(
        organization_id=org.id).scalar() or 0

    for row in rows:
        max_sort += 1
        db.session.add(RentalItem(
            organization_id=org.id,
            name=row['name'],
            category=row['category'],
            rate_hourly=row['rate_hourly'],
            rate_4hr=row['rate_4hr'],
            rate_8hr=row['rate_8hr'],
            rate_24hr=row['rate_24hr'],
            rate_weekly=row['rate_weekly'],
            deposit=row['deposit'],
            minimum_rental_price=row['minimum_rental_price'],
            minimum_rental_hours=row['minimum_rental_hours'],
            sort_order=max_sort,
            is_active=True,
        ))
    db.session.commit()

    flash(f"Import complete: {len(rows)} rental item(s) added, {len(errors)} row(s) skipped due to errors.", 'success')
    return redirect(url_for('rental.index'))
