from flask import render_template, request, flash, redirect, url_for, g, jsonify
from flask_login import login_required
from app.core.extensions import db
from app.core.models import Unit
from app.core.constants import ALL_MANUFACTURERS
from app.integrations.facebook import get_facebook_service
from . import units_bp

@units_bp.route('/units')
@login_required
def index():
    search = request.args.get('search', '').strip()
    query = Unit.query.filter_by(organization_id=g.current_org_id)
    if search:
        query = query.filter(
            (Unit.serial_number.ilike(f'%{search}%')) |
            (Unit.owner_name.ilike(f'%{search}%')) |
            (Unit.owner_company.ilike(f'%{search}%'))
        )
    units = query.order_by(Unit.id.desc()).limit(50).all() # Limit for performance
    return render_template('units/index.html', units=units, search=search)

@units_bp.route('/units/add', methods=['GET', 'POST'])
@login_required
def add():
    if request.method == 'POST':
        # Check specific constraints if needed, e.g. serial uniqueness per org
        serial = request.form.get('serial_number', '').strip()
        
        # Check duplicate serial in current org
        if serial:
            existing = Unit.query.filter_by(serial_number=serial, organization_id=g.current_org_id).first()
            if existing:
                flash(f'Unit with serial "{serial}" already exists.', 'warning')
                return redirect(url_for('units.index', search=serial))

        new_unit = Unit(
            organization_id=g.current_org_id,
            manufacturer=request.form.get('manufacturer'),
            model_number=request.form.get('model_number'),
            serial_number=serial,
            engine_model=request.form.get('engine_model'),
            engine_serial=request.form.get('engine_serial'),
            owner_name=request.form.get('owner_name'),
            owner_company=request.form.get('owner_company'),
            owner_address=request.form.get('owner_address'),
            owner_phone=request.form.get('owner_phone'),
            owner_email=request.form.get('owner_email'),
            unit_hours=request.form.get('unit_hours')
        )
        db.session.add(new_unit)
        db.session.commit()
        
        flash('Unit added successfully.', 'success')
        return redirect(url_for('units.view', unit_id=new_unit.id))
        
    return render_template('units/add.html', manufacturers=ALL_MANUFACTURERS)

@units_bp.route('/units/<int:unit_id>', methods=['GET', 'POST'])
@login_required
def view(unit_id):
    unit = Unit.query.get_or_404(unit_id)
    if unit.organization_id != g.current_org_id:
        return redirect(url_for('units.index'))

    
    if request.method == 'POST':
        unit.manufacturer = request.form.get('manufacturer')
        unit.model_number = request.form.get('model_number')
        # Handle serial change carefully (check unique)
        new_serial = request.form.get('serial_number', '').strip()
        if new_serial != unit.serial_number:
            existing = Unit.query.filter_by(serial_number=new_serial, organization_id=g.current_org_id).first()
            if existing:
                flash(f'Cannot update: Serial "{new_serial}" already exists on another unit.', 'danger')
                return redirect(url_for('units.view', unit_id=unit.id))
            unit.serial_number = new_serial
            
        unit.engine_model = request.form.get('engine_model')
        unit.engine_serial = request.form.get('engine_serial')
        unit.owner_name = request.form.get('owner_name')
        unit.owner_company = request.form.get('owner_company')
        unit.owner_address = request.form.get('owner_address')
        unit.owner_phone = request.form.get('owner_phone')
        unit.owner_email = request.form.get('owner_email')
        unit.unit_hours = request.form.get('unit_hours')
        
        # Marketing Fields
        unit.price = request.form.get('price') if request.form.get('price') else None
        unit.condition = request.form.get('condition', 'New')
        unit.description = request.form.get('description')
        unit.is_inventory = 'is_inventory' in request.form
        unit.display_on_web = 'display_on_web' in request.form
        
        db.session.commit()
        flash('Unit and marketing details updated.', 'success')
        return redirect(url_for('units.view', unit_id=unit.id))

    return render_template('units/detail.html', unit=unit, manufacturers=ALL_MANUFACTURERS)

@units_bp.route('/units/<int:unit_id>/facebook_post', methods=['POST'])
@login_required
def facebook_post(unit_id):
    unit = Unit.query.get_or_404(unit_id)
    if unit.organization_id != g.current_org_id:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
    
    fb_service = get_facebook_service(g.current_org)
    if not fb_service:
        return jsonify({'success': False, 'error': 'Facebook not connected in settings.'}), 400
    
    # Prepare the data for the post
    # Note: Using the dealer's specific subdomain for the link
    base_domain = "bentcrankshaft.com"
    dealer_url = f"https://{g.current_org.slug}.{base_domain}/inventory/{unit.id}"
    
    # Handle Image URL (GCS vs Local)
    image_url = None
    if unit.images:
        primary_img = unit.images[0]
        if primary_img.image_url.startswith('http'):
            image_url = primary_img.image_url
        else:
            bucket_name = current_app.config.get('GCS_BUCKET')
            if bucket_name:
                image_url = f"https://storage.googleapis.com/{bucket_name}/{primary_img.image_url}"
            else:
                # Fallback to local static hosting
                image_url = f"https://{g.current_org.slug}.{base_domain}{primary_img.image_url}"

    unit_data = {
        'name': f"{unit.manufacturer} {unit.model_number}",
        'description': unit.description,
        'price': float(unit.price) if unit.price else 0,
        'dealer_url': dealer_url,
        'image_url': image_url
    }
    
    success, post_id, error = fb_service.post_unit(unit_data)
    
    if success:
        return jsonify({'success': True, 'post_id': post_id})
    else:
        return jsonify({'success': False, 'error': error})

@units_bp.route('/api/units/check_serial/<serial>')
@login_required
def check_serial(serial):
    """API to lookup unit details by serial number for Autocomplete."""
    unit = Unit.query.filter_by(serial_number=serial, organization_id=g.current_org_id).first()
    if unit:
        return jsonify({
            'exists': True,
            'id': unit.id,
            'manufacturer': unit.manufacturer,
            'model_number': unit.model_number,
            'owner_name': unit.owner_name or '',
            'owner_company': unit.owner_company or ''
        })
    return jsonify({'exists': False})
