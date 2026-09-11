from flask import render_template, g, redirect, url_for, flash, request, current_app
from flask_login import login_required
from . import inventory_bp
from app.core.models import Unit, UnitImage, PartInventory
from app.core.extensions import db
from .forms import InventoryItemForm, PartInventoryForm
from app.core.pricing_service import compute_extended_price, effective_unit_price, recalculate_extended_prices
import os
from werkzeug.utils import secure_filename


def _org_markup_tiers(org_id):
    from app.core.models import MarkupTier
    return MarkupTier.query.filter_by(organization_id=org_id).order_by(MarkupTier.min_cost).all()

@inventory_bp.route('/parts', methods=['GET'])
@login_required
def index():
    org_id = g.current_org.id
    q = request.args.get('q', '').strip()
    mfg = request.args.get('mfg', '').strip()
    neg = request.args.get('neg') == '1'
    web = request.args.get('web') == '1'
    page = request.args.get('page', 1, type=int)

    query = PartInventory.query.filter_by(organization_id=org_id)
    if q:
        like = f'%{q}%'
        query = query.filter(db.or_(
            PartInventory.part_number.ilike(like),
            PartInventory.description.ilike(like),
        ))
    if mfg:
        query = query.filter(PartInventory.manufacturer == mfg)
    if neg:
        query = query.filter(PartInventory.stock_on_hand < 0)
    if web:
        query = query.filter(PartInventory.display_on_web.is_(True))

    if neg:
        query = query.order_by(PartInventory.stock_on_hand.asc())
    elif q or mfg or web:
        query = query.order_by(PartInventory.part_number.asc())
    else:
        query = query.order_by(PartInventory.updated_at.desc())
    pagination = query.paginate(page=page, per_page=50, error_out=False)

    negative_count = PartInventory.query.filter(
        PartInventory.organization_id == org_id, PartInventory.stock_on_hand < 0).count()
    web_count = PartInventory.query.filter(
        PartInventory.organization_id == org_id, PartInventory.display_on_web.is_(True)).count()

    manufacturers = [row[0] for row in db.session.query(PartInventory.manufacturer)
                     .filter(PartInventory.organization_id == org_id,
                             PartInventory.manufacturer.isnot(None),
                             PartInventory.manufacturer != '')
                     .distinct().order_by(PartInventory.manufacturer).all()]

    form = PartInventoryForm()
    return render_template('inventory/index.html', parts=pagination.items, pagination=pagination,
                           manufacturers=manufacturers, q=q, mfg=mfg, neg=neg, web=web,
                           negative_count=negative_count, web_count=web_count, form=form)

@inventory_bp.route('/parts/add', methods=['POST'])
@login_required
def add_part():
    form = PartInventoryForm()
    if form.validate_on_submit():
        part = PartInventory(
            organization_id=g.current_org.id,
            part_number=form.part_number.data,
            manufacturer=form.manufacturer.data,
            description=form.description.data,
            stock_on_hand=form.stock_on_hand.data,
            bin_location=form.bin_location.data,
            dealer_cost=form.dealer_cost.data,
            retail_price=form.retail_price.data,
            display_on_web=form.display_on_web.data,
        )
        part.extended_price = compute_extended_price(part.dealer_cost, _org_markup_tiers(g.current_org.id))

        # Handle Image Upload
        if form.image.data:
            f = form.image.data
            filename = secure_filename(f"{part.part_number}_{f.filename}")
            upload_dir = os.path.join(current_app.root_path, 'static', 'uploads', 'parts', str(g.current_org.id))
            os.makedirs(upload_dir, exist_ok=True)
            
            import uuid
            ext = os.path.splitext(filename)[1]
            unique_filename = f"{uuid.uuid4().hex}{ext}"
            f.save(os.path.join(upload_dir, unique_filename))
            part.image_url = f"/static/uploads/parts/{g.current_org.id}/{unique_filename}"

        try:
            db.session.add(part)
            db.session.commit()
            flash('Part added successfully.', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding part: {str(e)}', 'danger')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"Error in {getattr(form, field).label.text}: {error}", 'danger')
    
    return redirect(url_for('inventory.index'))

@inventory_bp.route('/parts/edit/<int:id>', methods=['POST'])
@login_required
def edit_part(id):
    part = PartInventory.query.get_or_404(id)
    if part.organization_id != g.current_org.id:
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('inventory.index'))
    
    form = PartInventoryForm()
    if form.validate_on_submit():
        part.part_number = form.part_number.data
        part.manufacturer = form.manufacturer.data
        part.description = form.description.data
        part.stock_on_hand = form.stock_on_hand.data
        part.bin_location = form.bin_location.data
        part.dealer_cost = form.dealer_cost.data
        part.retail_price = form.retail_price.data
        part.extended_price = compute_extended_price(part.dealer_cost, _org_markup_tiers(g.current_org.id))
        part.display_on_web = form.display_on_web.data

        # Handle Image Upload
        if form.image.data:
            f = form.image.data
            filename = secure_filename(f"{part.part_number}_{f.filename}")
            upload_dir = os.path.join(current_app.root_path, 'static', 'uploads', 'parts', str(g.current_org.id))
            os.makedirs(upload_dir, exist_ok=True)

            import uuid
            ext = os.path.splitext(filename)[1]
            unique_filename = f"{uuid.uuid4().hex}{ext}"
            f.save(os.path.join(upload_dir, unique_filename))
            part.image_url = f"/static/uploads/parts/{g.current_org.id}/{unique_filename}"

        db.session.commit()
        flash('Part updated successfully.', 'success')
    
    return redirect(url_for('inventory.index'))

@inventory_bp.route('/parts/delete/<int:id>', methods=['POST'])
@login_required
def delete_part(id):
    part = PartInventory.query.get_or_404(id)
    if part.organization_id != g.current_org.id:
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('inventory.index'))

    db.session.delete(part)
    db.session.commit()
    flash('Part deleted successfully.', 'success')
    return redirect(url_for('inventory.index'))


@inventory_bp.route('/parts/<int:id>/toggle-web', methods=['POST'])
@login_required
def toggle_part_web(id):
    """AJAX: flip a single part's 'show on website' flag from the Parts list."""
    part = PartInventory.query.filter_by(id=id, organization_id=g.current_org.id).first()
    if not part:
        return {'error': 'Part not found'}, 404
    part.display_on_web = not part.display_on_web
    db.session.commit()
    return {'id': part.id, 'display_on_web': part.display_on_web}


@inventory_bp.route('/parts/search')
@login_required
def search_parts():
    """AJAX type-ahead used by the POS 'New Sale' and service-ticket part pickers.
    Searches part number / description / manufacturer; returns the dealer's selling
    price (extended_price, falling back to retail then cost)."""
    from sqlalchemy import or_, case

    q = request.args.get('q', '').strip()
    if len(q) < 2:
        return {'results': []}

    like = f'%{q}%'
    prefix = f'{q}%'
    rows = (PartInventory.query
            .filter_by(organization_id=g.current_org.id)
            .filter(or_(
                PartInventory.part_number.ilike(like),
                PartInventory.description.ilike(like),
                PartInventory.manufacturer.ilike(like),
            ))
            .order_by(
                case((PartInventory.part_number.ilike(prefix), 0), else_=1),
                PartInventory.part_number,
            )
            .limit(25)
            .all())

    return {'results': [{
        'id': p.id,
        'part_number': p.part_number,
        'manufacturer': p.manufacturer or '',
        'description': p.description or '',
        'price': float(effective_unit_price(p)),
        'stock': p.stock_on_hand or 0,
    } for p in rows]}


@inventory_bp.route('/parts/recalculate-prices', methods=['POST'])
@login_required
def recalculate_prices():
    """Recomputes every part's Extended Price from its current Dealer Cost and
    the org's Markup Tiers. Use after bulk-editing costs, or if a tier change
    doesn't seem to have taken effect on older parts."""
    changed = recalculate_extended_prices(g.current_org.id)
    flash(f"Recalculated prices for {changed} part(s).", 'success')
    return redirect(request.referrer or url_for('inventory.index'))


@inventory_bp.route('/units')
@login_required
def manage():
    sort = request.args.get('sort', 'id')
    order = request.args.get('order', 'desc')
    
    query = Unit.query.filter_by(organization_id=g.current_org.id, is_inventory=True)
    
    # Sorting logic
    if sort == 'manufacturer':
        query = query.order_by(Unit.manufacturer.asc() if order == 'asc' else Unit.manufacturer.desc())
    elif sort == 'model':
        query = query.order_by(Unit.model_number.asc() if order == 'asc' else Unit.model_number.desc())
    elif sort == 'type':
        query = query.order_by(Unit.type.asc() if order == 'asc' else Unit.type.desc())
    elif sort == 'price':
        query = query.order_by(Unit.price.asc() if order == 'asc' else Unit.price.desc())
    elif sort == 'year':
        query = query.order_by(Unit.year.asc() if order == 'asc' else Unit.year.desc())
    else:
        query = query.order_by(Unit.id.desc())
        
    units = query.all()
    return render_template('inventory/manage.html', units=units, current_sort=sort, current_order=order)

@inventory_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    form = InventoryItemForm()
    if form.validate_on_submit():
        unit = Unit(
            organization_id=g.current_org.id,
            manufacturer=form.manufacturer.data,
            model_number=form.model_number.data,
            type=form.type.data,
            serial_number=form.serial_number.data if form.condition.data != 'New' and form.serial_number.data else None,
            year=form.year.data,
            condition=form.condition.data,
            price=form.price.data,
            unit_hours=form.hours.data,
            description=form.description.data,
            status=form.status.data,
            display_on_web=form.display_on_web.data,
            is_inventory=True
        )
        db.session.add(unit)
        db.session.commit() # Commit to get ID for image association
        
        # Handle Image Upload
        if form.primary_image.data:
            f = form.primary_image.data
            filename = secure_filename(f.filename)
            # Save to static/uploads/inventory/{org_id}/
            upload_dir = os.path.join(current_app.root_path, 'static', 'uploads', 'inventory', str(g.current_org.id))
            os.makedirs(upload_dir, exist_ok=True)
            
            # Make unique filename
            import uuid
            ext = os.path.splitext(filename)[1]
            unique_filename = f"{uuid.uuid4().hex}{ext}"
            f.save(os.path.join(upload_dir, unique_filename))
            
            # Create UnitImage
            image_url = f"/static/uploads/inventory/{g.current_org.id}/{unique_filename}"
            image = UnitImage(unit_id=unit.id, image_url=image_url, is_primary=True)
            db.session.add(image)
            db.session.commit()
            
        flash('Unit added successfully.', 'success')
        return redirect(url_for('inventory.manage'))
        
    return render_template('inventory/form.html', form=form, title="Add Inventory Unit")

@inventory_bp.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    unit = Unit.query.get_or_404(id)
    # Security check using organization_id (assuming simple tenancy)
    if unit.organization_id != g.current_org.id:
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('inventory.manage'))
        
    form = InventoryItemForm(obj=unit)
    
    # Pre-populate specific fields that map differently or need care
    if request.method == 'GET':
        form.hours.data = unit.unit_hours
    
    if form.validate_on_submit():
        unit.manufacturer = form.manufacturer.data
        unit.model_number = form.model_number.data
        unit.type = form.type.data
        unit.serial_number = form.serial_number.data if form.condition.data != 'New' and form.serial_number.data else None
        unit.year = form.year.data
        unit.condition = form.condition.data
        unit.price = form.price.data
        unit.unit_hours = form.hours.data
        unit.description = form.description.data
        unit.status = form.status.data
        unit.display_on_web = form.display_on_web.data
        
        # Handle Image Upload (Replace Primary or Add)
        if form.primary_image.data:
            f = form.primary_image.data
            filename = secure_filename(f.filename)
            upload_dir = os.path.join(current_app.root_path, 'static', 'uploads', 'inventory', str(g.current_org.id))
            os.makedirs(upload_dir, exist_ok=True)
            
            import uuid
            ext = os.path.splitext(filename)[1]
            unique_filename = f"{uuid.uuid4().hex}{ext}"
            f.save(os.path.join(upload_dir, unique_filename))
            
            image_url = f"/static/uploads/inventory/{g.current_org.id}/{unique_filename}"
            
            # Check existing primary
            existing_primary = UnitImage.query.filter_by(unit_id=unit.id, is_primary=True).first()
            if existing_primary:
                existing_primary.image_url = image_url # Update existing
            else:
                image = UnitImage(unit_id=unit.id, image_url=image_url, is_primary=True)
                db.session.add(image)
        
        db.session.commit()
        flash('Unit updated successfully.', 'success')
        return redirect(url_for('inventory.manage'))
        
    return render_template('inventory/form.html', form=form, title="Edit Inventory Unit", unit=unit)

@inventory_bp.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete(id):
    unit = Unit.query.get_or_404(id)
    if unit.organization_id != g.current_org.id:
        flash('Unauthorized.', 'danger')
        return redirect(url_for('inventory.manage'))
        
    db.session.delete(unit)
    db.session.commit()
    flash('Unit deleted.', 'success')
    return redirect(url_for('inventory.manage'))

@inventory_bp.route('/<int:id>/social-share', methods=['POST'])
@login_required
def social_share(id):
    from app.integrations.facebook import get_facebook_service
    try:
        unit = Unit.query.get_or_404(id)
        if unit.organization_id != g.current_org.id:
            flash('Unauthorized.', 'danger')
            return redirect(url_for('inventory.manage'))
        
        print(f"DEBUG: social_share for unit {id}, org {g.current_org.id}", flush=True)
        
        fb_service = get_facebook_service(g.current_org)
        if not fb_service:
            flash('Facebook is not connected. Go to Platform Settings to connect.', 'warning')
            return redirect(url_for('inventory.manage'))
        
        # Prepare data for post
        primary_img = UnitImage.query.filter_by(unit_id=unit.id, is_primary=True).first()
        if not primary_img and unit.images:
            primary_img = unit.images[0]
            
        print(f"DEBUG: primary_img found: {primary_img is not None}", flush=True)
        
        image_url = None
        if primary_img:
            image_url = f"https://{g.current_org.slug}.bentcrankshaft.com{primary_img.image_url}"
        
        dealer_url = f"https://{g.current_org.slug}.bentcrankshaft.com/inventory/{unit.id}"
        
        unit_data = {
            'name': f"{unit.year or ''} {unit.manufacturer} {unit.model_number}".strip(),
            'description': unit.description,
            'price': float(unit.price) if unit.price else 0.0,
            'image_url': image_url,
            'dealer_url': dealer_url
        }
        
        print(f"DEBUG: prepared unit_data: {unit_data}", flush=True)
        
        success, post_id, error = fb_service.post_unit(unit_data)
        
        if success:
            flash(f'Successfully posted to Facebook!', 'success')
        else:
            print(f"DEBUG: FB Error: {error}", flush=True)
            flash(f'Facebook error: {error}', 'danger')
            
    except Exception as e:
        import traceback
        print(f"CRASH in social_share: {str(e)}", flush=True)
        print(traceback.format_exc(), flush=True)
        flash(f'Internal Error: {str(e)}', 'danger')
        
    return redirect(url_for('inventory.manage'))


# ====== BULK PARTS PRICE IMPORT ======

import tempfile
import uuid as uuid_lib

def _import_dir(org_id):
    d = os.path.join(tempfile.gettempdir(), 'parts_import', str(org_id))
    os.makedirs(d, exist_ok=True)
    return d


def _existing_parts_by_key(org_id, part_numbers):
    """{(part_number, manufacturer): PartInventory} for just the part numbers in
    the import file, fetched in chunks. Avoids loading a 100k+ row catalog into
    memory to decide new-vs-update."""
    existing = {}
    pns = list(part_numbers)
    for i in range(0, len(pns), 1000):
        chunk = pns[i:i + 1000]
        for p in (PartInventory.query
                  .filter(PartInventory.organization_id == org_id,
                          PartInventory.part_number.in_(chunk))
                  .all()):
            existing[(p.part_number, p.manufacturer)] = p
    return existing

@inventory_bp.route('/parts/import', methods=['GET'])
@login_required
def import_parts():
    return render_template('inventory/import_start.html')

@inventory_bp.route('/parts/import/upload', methods=['POST'])
@login_required
def import_parts_upload():
    from app.core.parts_import_service import get_headers_and_sample, suggest_mapping, IMPORT_FIELDS

    file = request.files.get('price_file')
    if not file or not file.filename:
        flash('Please choose a CSV or Excel file to upload.', 'danger')
        return redirect(url_for('inventory.import_parts'))

    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ('.csv', '.xlsx', '.xls'):
        flash('File must be a .csv, .xlsx, or .xls file.', 'danger')
        return redirect(url_for('inventory.import_parts'))

    upload_id = uuid_lib.uuid4().hex
    saved_name = f"{upload_id}{ext}"
    saved_path = os.path.join(_import_dir(g.current_org.id), saved_name)
    file.save(saved_path)

    try:
        headers, sample, row_count = get_headers_and_sample(saved_path, saved_name)
    except Exception as e:
        os.remove(saved_path)
        flash(f'Could not read that file: {e}', 'danger')
        return redirect(url_for('inventory.import_parts'))

    suggested = suggest_mapping(headers)

    return render_template(
        'inventory/import_map.html',
        upload_id=saved_name,
        headers=headers,
        sample=sample,
        row_count=row_count,
        fields=IMPORT_FIELDS,
        suggested=suggested,
    )

@inventory_bp.route('/parts/import/preview', methods=['POST'])
@login_required
def import_parts_preview():
    from app.core.parts_import_service import parse_rows, REQUIRED_FIELDS, IMPORT_FIELDS
    from app.core.pricing_service import compute_extended_price
    from app.core.models import MarkupTier

    upload_id = request.form.get('upload_id', '')
    saved_path = os.path.join(_import_dir(g.current_org.id), upload_id)
    if not upload_id or not os.path.isfile(saved_path):
        flash('That upload has expired. Please upload the file again.', 'danger')
        return redirect(url_for('inventory.import_parts'))

    mapping = {field: request.form.get(f'map_{field}', '') for field in IMPORT_FIELDS}
    manufacturer_default = request.form.get('manufacturer_default', '').strip()

    missing_required = [IMPORT_FIELDS[f] for f in REQUIRED_FIELDS if not mapping.get(f)]
    if missing_required:
        flash(f"Please map: {', '.join(missing_required)}", 'danger')
        return redirect(url_for('inventory.import_parts'))

    rows = parse_rows(saved_path, upload_id, mapping, manufacturer_default)
    tiers = MarkupTier.query.filter_by(organization_id=g.current_org.id).all()

    # Look up only the part numbers present in this file (batched) rather than
    # the whole catalog - a dealer can have 100k+ parts.
    file_part_numbers = {r['part_number'] for r in rows if 'error' not in r}
    existing = _existing_parts_by_key(g.current_org.id, file_part_numbers)

    valid_rows, error_rows = [], []
    new_count, update_count = 0, 0
    for row in rows:
        if 'error' in row:
            error_rows.append(row)
            continue
        row['extended_price'] = compute_extended_price(row['dealer_cost'], tiers)
        key = (row['part_number'], row['manufacturer'])
        if key in existing:
            row['action'] = 'update'
            update_count += 1
        else:
            row['action'] = 'new'
            new_count += 1
        valid_rows.append(row)

    return render_template(
        'inventory/import_preview.html',
        upload_id=upload_id,
        mapping=mapping,
        manufacturer_default=manufacturer_default,
        fields=IMPORT_FIELDS,
        preview_rows=valid_rows[:100],
        error_rows=error_rows[:100],
        total_rows=len(rows),
        new_count=new_count,
        update_count=update_count,
        error_count=len(error_rows),
        has_tiers=len(tiers) > 0,
    )

@inventory_bp.route('/parts/import/confirm', methods=['POST'])
@login_required
def import_parts_confirm():
    from app.core.parts_import_service import parse_rows, IMPORT_FIELDS
    from app.core.pricing_service import compute_extended_price
    from app.core.models import MarkupTier
    from datetime import datetime

    upload_id = request.form.get('upload_id', '')
    saved_path = os.path.join(_import_dir(g.current_org.id), upload_id)
    if not upload_id or not os.path.isfile(saved_path):
        flash('That upload has expired. Please upload the file again.', 'danger')
        return redirect(url_for('inventory.import_parts'))

    mapping = {field: request.form.get(f'map_{field}', '') for field in IMPORT_FIELDS}
    manufacturer_default = request.form.get('manufacturer_default', '').strip()
    org_id = g.current_org.id

    rows = parse_rows(saved_path, upload_id, mapping, manufacturer_default)
    tiers = MarkupTier.query.filter_by(organization_id=org_id).all()
    file_part_numbers = {r['part_number'] for r in rows if 'error' not in r}
    existing = _existing_parts_by_key(org_id, file_part_numbers)

    created, updated, skipped = 0, 0, 0
    try:
        for i, row in enumerate(rows):
            if 'error' in row:
                skipped += 1
                continue

            key = (row['part_number'], row['manufacturer'])
            extended_price = compute_extended_price(row['dealer_cost'], tiers)
            part = existing.get(key)

            if part:
                part.description = row['description'] or part.description
                part.dealer_cost = row['dealer_cost']
                part.retail_price = row['retail_price']
                part.extended_price = extended_price
                part.upc = row['upc'] or part.upc
                part.superseded_to = row['superseded_to'] or part.superseded_to
                part.updated_at = datetime.utcnow()
                updated += 1
            else:
                part = PartInventory(
                    organization_id=org_id,
                    part_number=row['part_number'],
                    manufacturer=row['manufacturer'],
                    description=row['description'],
                    dealer_cost=row['dealer_cost'],
                    retail_price=row['retail_price'],
                    extended_price=extended_price,
                    upc=row['upc'],
                    superseded_to=row['superseded_to'],
                )
                db.session.add(part)
                existing[key] = part
                created += 1

            if (i + 1) % 500 == 0:
                db.session.flush()

        db.session.commit()
    except Exception as e:
        db.session.rollback()
        flash(f'Import failed, no changes were saved: {e}', 'danger')
        return redirect(url_for('inventory.import_parts'))
    finally:
        try:
            os.remove(saved_path)
        except OSError:
            pass

    flash(f"Import complete: {created} new part(s), {updated} updated, {skipped} skipped due to errors.", 'success')
    return redirect(url_for('inventory.index'))
