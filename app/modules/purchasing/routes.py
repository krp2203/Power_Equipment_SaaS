from flask import render_template, g, redirect, url_for, flash, request
from flask_login import login_required
from . import purchasing_bp
from app.core.models import (Vendor, VendorManufacturer, PurchaseOrder, PurchaseOrderLineItem,
                             PartInventory, Unit)
from app.core.extensions import db
from app.core.invoicing_service import next_po_number
from .forms import VendorForm, PurchaseOrderForm


@purchasing_bp.route('/')
@login_required
def hub():
    open_pos = PurchaseOrder.query.filter_by(organization_id=g.current_org.id).filter(
        PurchaseOrder.status.in_(['draft', 'ordered', 'partially_received'])
    ).order_by(PurchaseOrder.created_at.desc()).all()
    vendor_count = Vendor.query.filter_by(organization_id=g.current_org.id).count()
    return render_template('purchasing/hub.html', open_pos=open_pos, vendor_count=vendor_count)


# ====== VENDORS ======

@purchasing_bp.route('/vendors')
@login_required
def vendors():
    all_vendors = Vendor.query.filter_by(organization_id=g.current_org.id).order_by(Vendor.name).all()
    form = VendorForm()
    return render_template('purchasing/vendors.html', vendors=all_vendors, form=form)


@purchasing_bp.route('/vendors/add', methods=['POST'])
@login_required
def add_vendor():
    form = VendorForm()
    if form.validate_on_submit():
        vendor = Vendor(
            organization_id=g.current_org.id,
            name=form.name.data,
            account_number=form.account_number.data,
            contact_name=form.contact_name.data,
            phone=form.phone.data,
            email=form.email.data,
            address=form.address.data,
            notes=form.notes.data,
        )
        db.session.add(vendor)
        db.session.commit()
        flash(f"Vendor '{vendor.name}' added.", "success")
    else:
        flash("Please correct the errors and try again.", "danger")
    return redirect(url_for('purchasing.vendors'))


@purchasing_bp.route('/vendors/<int:vendor_id>/edit', methods=['POST'])
@login_required
def edit_vendor(vendor_id):
    vendor = Vendor.query.filter_by(id=vendor_id, organization_id=g.current_org.id).first_or_404()
    form = VendorForm()
    if form.validate_on_submit():
        vendor.name = form.name.data
        vendor.account_number = form.account_number.data
        vendor.contact_name = form.contact_name.data
        vendor.phone = form.phone.data
        vendor.email = form.email.data
        vendor.address = form.address.data
        vendor.notes = form.notes.data
        db.session.commit()
        flash(f"Vendor '{vendor.name}' updated.", "success")
    else:
        flash("Please correct the errors and try again.", "danger")
    return redirect(url_for('purchasing.vendors'))


@purchasing_bp.route('/vendors/<int:vendor_id>')
@login_required
def vendor_detail(vendor_id):
    vendor = Vendor.query.filter_by(id=vendor_id, organization_id=g.current_org.id).first_or_404()
    mfgs = VendorManufacturer.query.filter_by(vendor_id=vendor.id).order_by(VendorManufacturer.manufacturer).all()
    # For each manufacturer, is another vendor already primary?
    claimed_primary = {
        vm.manufacturer: vm.vendor_id
        for vm in VendorManufacturer.query.filter(
            VendorManufacturer.organization_id == g.current_org.id,
            VendorManufacturer.is_primary.is_(True),
        ).all()
    }
    all_mfgs = [row[0] for row in db.session.query(PartInventory.manufacturer)
               .filter(PartInventory.organization_id == g.current_org.id,
                       PartInventory.manufacturer.isnot(None), PartInventory.manufacturer != '')
               .distinct().order_by(PartInventory.manufacturer).all()]
    open_po_count = PurchaseOrder.query.filter_by(organization_id=g.current_org.id, vendor_id=vendor.id).filter(
        PurchaseOrder.status.in_(['draft', 'ordered', 'partially_received'])).count()
    return render_template('purchasing/vendor_detail.html', vendor=vendor, mfgs=mfgs,
                           claimed_primary=claimed_primary, all_mfgs=all_mfgs, open_po_count=open_po_count)


@purchasing_bp.route('/vendors/<int:vendor_id>/manufacturers/add', methods=['POST'])
@login_required
def add_vendor_manufacturer(vendor_id):
    vendor = Vendor.query.filter_by(id=vendor_id, organization_id=g.current_org.id).first_or_404()
    name = request.form.get('manufacturer', '').strip()
    if not name:
        flash("Enter a manufacturer name.", "danger")
        return redirect(url_for('purchasing.vendor_detail', vendor_id=vendor.id))
    if VendorManufacturer.query.filter_by(vendor_id=vendor.id, manufacturer=name).first():
        flash(f"{vendor.name} already lists {name}.", "info")
        return redirect(url_for('purchasing.vendor_detail', vendor_id=vendor.id))

    # First vendor to claim a manufacturer becomes its primary automatically.
    others = VendorManufacturer.query.filter_by(organization_id=g.current_org.id, manufacturer=name).count()
    db.session.add(VendorManufacturer(
        organization_id=g.current_org.id, vendor_id=vendor.id,
        manufacturer=name, is_primary=(others == 0),
    ))
    db.session.commit()
    flash(f"Added {name} to {vendor.name}.", "success")
    return redirect(url_for('purchasing.vendor_detail', vendor_id=vendor.id))


@purchasing_bp.route('/vendors/<int:vendor_id>/manufacturers/<int:vm_id>/primary', methods=['POST'])
@login_required
def set_primary_vendor_manufacturer(vendor_id, vm_id):
    vendor = Vendor.query.filter_by(id=vendor_id, organization_id=g.current_org.id).first_or_404()
    vm = VendorManufacturer.query.filter_by(id=vm_id, vendor_id=vendor.id).first_or_404()
    # Clear primary on every other vendor for this manufacturer, set it here.
    for other in VendorManufacturer.query.filter_by(
            organization_id=g.current_org.id, manufacturer=vm.manufacturer).all():
        other.is_primary = (other.id == vm.id)
    db.session.commit()
    flash(f"{vendor.name} is now the primary supplier for {vm.manufacturer}.", "success")
    return redirect(url_for('purchasing.vendor_detail', vendor_id=vendor.id))


@purchasing_bp.route('/vendors/<int:vendor_id>/manufacturers/<int:vm_id>/delete', methods=['POST'])
@login_required
def delete_vendor_manufacturer(vendor_id, vm_id):
    vendor = Vendor.query.filter_by(id=vendor_id, organization_id=g.current_org.id).first_or_404()
    vm = VendorManufacturer.query.filter_by(id=vm_id, vendor_id=vendor.id).first_or_404()
    mfg, was_primary = vm.manufacturer, vm.is_primary
    db.session.delete(vm)
    db.session.flush()
    # If we removed the primary, promote another vendor for that manufacturer.
    if was_primary:
        nxt = VendorManufacturer.query.filter_by(
            organization_id=g.current_org.id, manufacturer=mfg).first()
        if nxt:
            nxt.is_primary = True
    db.session.commit()
    flash(f"Removed {mfg} from {vendor.name}.", "success")
    return redirect(url_for('purchasing.vendor_detail', vendor_id=vendor.id))


@purchasing_bp.route('/vendors/<int:vendor_id>/delete', methods=['POST'])
@login_required
def delete_vendor(vendor_id):
    vendor = Vendor.query.filter_by(id=vendor_id, organization_id=g.current_org.id).first_or_404()
    if vendor.purchase_orders:
        flash(f"Can't delete '{vendor.name}' - they have purchase orders on file.", "danger")
        return redirect(url_for('purchasing.vendors'))
    db.session.delete(vendor)
    db.session.commit()
    flash("Vendor removed.", "success")
    return redirect(url_for('purchasing.vendors'))


# ====== PURCHASE ORDERS ======

@purchasing_bp.route('/pos')
@login_required
def purchase_orders():
    all_pos = PurchaseOrder.query.filter_by(organization_id=g.current_org.id).order_by(PurchaseOrder.created_at.desc()).all()
    return render_template('purchasing/po_list.html', purchase_orders=all_pos)


@purchasing_bp.route('/pos/new', methods=['GET', 'POST'])
@login_required
def new_purchase_order():
    org = g.current_org
    form = PurchaseOrderForm()
    form.vendor_id.choices = [(v.id, v.name) for v in Vendor.query.filter_by(organization_id=org.id).order_by(Vendor.name).all()]

    if not form.vendor_id.choices:
        flash("Add a vendor first before creating a purchase order.", "warning")
        return redirect(url_for('purchasing.vendors'))

    if form.validate_on_submit():
        po = PurchaseOrder(
            organization_id=org.id,
            vendor_id=form.vendor_id.data,
            po_number=next_po_number(org.id),
            order_date=form.order_date.data,
            expected_date=form.expected_date.data,
            notes=form.notes.data,
        )
        db.session.add(po)
        db.session.commit()
        flash(f"Purchase Order #{po.po_number} created. Add line items below.", "success")
        return redirect(url_for('purchasing.view_purchase_order', po_id=po.id))

    return render_template('purchasing/po_new.html', form=form)


@purchasing_bp.route('/pos/<int:po_id>')
@login_required
def view_purchase_order(po_id):
    po = PurchaseOrder.query.filter_by(id=po_id, organization_id=g.current_org.id).first_or_404()
    return render_template('purchasing/po_detail.html', po=po)


@purchasing_bp.route('/pos/<int:po_id>/add-line', methods=['POST'])
@login_required
def add_po_line(po_id):
    po = PurchaseOrder.query.filter_by(id=po_id, organization_id=g.current_org.id).first_or_404()
    if po.status not in ('draft', 'ordered'):
        flash("Can't add lines to a closed/received purchase order.", "danger")
        return redirect(url_for('purchasing.view_purchase_order', po_id=po.id))

    line_type = request.form.get('line_type', 'part')

    try:
        quantity_ordered = int(request.form.get('quantity_ordered', 1))
        unit_cost = request.form.get('unit_cost', '').strip()
        unit_cost = float(unit_cost) if unit_cost else None
    except ValueError:
        flash("Quantity and cost must be numbers.", "danger")
        return redirect(url_for('purchasing.view_purchase_order', po_id=po.id))

    line = PurchaseOrderLineItem(
        purchase_order_id=po.id,
        line_type=line_type,
        quantity_ordered=quantity_ordered,
        unit_cost=unit_cost,
    )

    if line_type == 'part':
        part_inventory_id = request.form.get('part_inventory_id', '').strip()
        if part_inventory_id:
            part = PartInventory.query.filter_by(id=int(part_inventory_id), organization_id=g.current_org.id).first()
            if part:
                line.part_inventory_id = part.id
                line.part_number = part.part_number
                line.manufacturer = part.manufacturer
                line.description = part.description
        else:
            line.part_number = request.form.get('part_number', '').strip() or None
            line.manufacturer = request.form.get('manufacturer', '').strip() or None
            line.description = request.form.get('description', '').strip() or None
    else:  # whole_good
        line.manufacturer = request.form.get('manufacturer', '').strip() or None
        line.description = request.form.get('description', '').strip() or None
        line.quantity_ordered = 1  # each whole-good line represents one serialized unit

    db.session.add(line)
    db.session.commit()
    flash("Line item added.", "success")
    return redirect(url_for('purchasing.view_purchase_order', po_id=po.id))


@purchasing_bp.route('/pos/<int:po_id>/line/<int:line_id>/delete', methods=['POST'])
@login_required
def delete_po_line(po_id, line_id):
    po = PurchaseOrder.query.filter_by(id=po_id, organization_id=g.current_org.id).first_or_404()
    line = PurchaseOrderLineItem.query.filter_by(id=line_id, purchase_order_id=po.id).first_or_404()
    if line.quantity_received > 0:
        flash("Can't delete a line that's already been received.", "danger")
        return redirect(url_for('purchasing.view_purchase_order', po_id=po.id))
    db.session.delete(line)
    db.session.commit()
    flash("Line item removed.", "success")
    return redirect(url_for('purchasing.view_purchase_order', po_id=po.id))


@purchasing_bp.route('/pos/<int:po_id>/mark-ordered', methods=['POST'])
@login_required
def mark_ordered(po_id):
    po = PurchaseOrder.query.filter_by(id=po_id, organization_id=g.current_org.id).first_or_404()
    if not po.line_items:
        flash("Add at least one line item before marking this as ordered.", "danger")
        return redirect(url_for('purchasing.view_purchase_order', po_id=po.id))
    po.status = 'ordered'
    db.session.commit()
    flash(f"Purchase Order #{po.po_number} marked as ordered.", "success")
    return redirect(url_for('purchasing.view_purchase_order', po_id=po.id))


def _update_po_status(po):
    """Recomputes a PO's overall status from its line items' receiving progress."""
    if not po.line_items:
        return
    total_ordered = sum(li.quantity_ordered for li in po.line_items)
    total_received = sum(li.quantity_received for li in po.line_items)
    if total_received == 0:
        if po.status not in ('draft',):
            po.status = 'ordered'
    elif total_received < total_ordered:
        po.status = 'partially_received'
    else:
        po.status = 'received'


@purchasing_bp.route('/pos/<int:po_id>/line/<int:line_id>/receive', methods=['POST'])
@login_required
def receive_po_line(po_id, line_id):
    org = g.current_org
    po = PurchaseOrder.query.filter_by(id=po_id, organization_id=org.id).first_or_404()
    line = PurchaseOrderLineItem.query.filter_by(id=line_id, purchase_order_id=po.id).first_or_404()

    if line.line_type == 'part':
        try:
            qty = int(request.form.get('quantity_received', 0))
        except ValueError:
            flash("Enter a valid quantity.", "danger")
            return redirect(url_for('purchasing.view_purchase_order', po_id=po.id))

        remaining = line.quantity_ordered - line.quantity_received
        if qty <= 0 or qty > remaining:
            flash(f"Enter a quantity between 1 and {remaining}.", "danger")
            return redirect(url_for('purchasing.view_purchase_order', po_id=po.id))

        part = PartInventory.query.get(line.part_inventory_id) if line.part_inventory_id else None
        if not part and line.part_number:
            part = PartInventory.query.filter_by(
                organization_id=org.id, part_number=line.part_number, manufacturer=line.manufacturer
            ).first()
            if not part:
                part = PartInventory(
                    organization_id=org.id,
                    part_number=line.part_number,
                    manufacturer=line.manufacturer,
                    description=line.description,
                    dealer_cost=line.unit_cost,
                    vendor_id=po.vendor_id,
                    stock_on_hand=0,
                )
                db.session.add(part)
                db.session.flush()
            line.part_inventory_id = part.id

        if part:
            part.stock_on_hand = (part.stock_on_hand or 0) + qty

        line.quantity_received += qty
        _update_po_status(po)
        db.session.commit()
        flash(f"Received {qty} of {line.part_number or line.description}.", "success")

    else:  # whole_good
        serial_number = request.form.get('serial_number', '').strip()
        if not serial_number:
            flash("Serial number is required to receive a whole good.", "danger")
            return redirect(url_for('purchasing.view_purchase_order', po_id=po.id))
        if line.quantity_received >= line.quantity_ordered:
            flash("This unit has already been received.", "warning")
            return redirect(url_for('purchasing.view_purchase_order', po_id=po.id))

        unit = Unit(
            organization_id=org.id,
            manufacturer=line.manufacturer,
            model_number=line.description,
            serial_number=serial_number,
            price=None,
            condition='New',
            status='Available',
            is_inventory=True,
            is_owned=True,
        )
        db.session.add(unit)
        db.session.flush()

        line.unit_id = unit.id
        line.quantity_received = 1
        _update_po_status(po)
        db.session.commit()
        flash(f"Received unit, serial {serial_number}. Added to Inventory.", "success")

    return redirect(url_for('purchasing.view_purchase_order', po_id=po.id))
