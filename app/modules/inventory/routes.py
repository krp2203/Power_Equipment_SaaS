from flask import render_template, g, redirect, url_for, flash, request, current_app
from flask_login import login_required
from . import inventory_bp
from app.core.models import Unit, UnitImage, PartInventory
from app.core.extensions import db
from .forms import InventoryItemForm, PartInventoryForm
import os
from werkzeug.utils import secure_filename

@inventory_bp.route('/parts', methods=['GET'])
@login_required
def index():
    # Restore Parts Inventory View
    parts = PartInventory.query.filter_by(organization_id=g.current_org.id).order_by(PartInventory.updated_at.desc()).all()
    form = PartInventoryForm()
    return render_template('inventory/index.html', parts=parts, form=form)

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
            bin_location=form.bin_location.data
        )
        
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

@inventory_bp.route('/units')
@login_required
def manage():
    # Move Whole Goods to /units
    units = Unit.query.filter_by(organization_id=g.current_org.id, is_inventory=True).order_by(Unit.id.desc()).all()
    return render_template('inventory/manage.html', units=units)

@inventory_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    form = InventoryItemForm()
    if form.validate_on_submit():
        unit = Unit(
            organization_id=g.current_org.id,
            manufacturer=form.manufacturer.data,
            model_number=form.model_number.data,
            serial_number=form.serial_number.data,
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
        unit.serial_number = form.serial_number.data
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
