from flask import render_template, request, redirect, url_for, flash, g
from flask_login import login_required
from sqlalchemy import or_

from . import equipment_bp
from app.core.extensions import db
from app.core.models import (Unit, UnitComponent, Customer, ServiceTicket,
                             InvoiceLineItem, PurchaseOrderLineItem)

TYPES = ['Mower', 'Zero-Turn', 'Tractor', 'Chainsaw', 'Trimmer', 'Blower', 'Edger',
         'Generator', 'Pressure Washer', 'Snow Blower', 'Tiller', 'Other']

COMPONENT_TYPES = ['Engine', 'Transmission', 'Deck', 'PTO', 'Hydraulic Pump',
                   'Cutter Deck', 'Attachment', 'Other']


def _customer_label(cust):
    if not cust:
        return None
    return cust.name or cust.company or f"Customer #{cust.id}"


def _apply_form(unit, org_id):
    """Populate a Unit from the equipment form. Returns an error string or None."""
    f = request.form
    serial = (f.get('serial_number') or '').strip() or None
    if serial:
        clash = (Unit.query
                 .filter(Unit.organization_id == org_id,
                         Unit.serial_number == serial,
                         Unit.id != (unit.id or 0))
                 .first())
        if clash:
            return f'Serial "{serial}" is already on another equipment record.'

    unit.manufacturer = (f.get('manufacturer') or '').strip() or None
    unit.model_number = (f.get('model_number') or '').strip() or None
    unit.serial_number = serial
    unit.type = (f.get('type') or '').strip() or None
    unit.unit_hours = (f.get('unit_hours') or '').strip() or None
    unit.description = (f.get('description') or '').strip() or None

    cid = (f.get('customer_id') or '').strip()
    if cid:
        cust = Customer.query.filter_by(id=int(cid), organization_id=org_id).first()
        if not cust:
            return "That customer could not be found."
        unit.customer_id = cust.id
        # keep the legacy owner_* snapshot roughly in step for older screens
        unit.owner_name = cust.name
        unit.owner_company = cust.company
        unit.owner_phone = cust.phone
        unit.owner_email = cust.email
    else:
        unit.customer_id = None
    return None


def _unit_label(u):
    bits = [b for b in [u.manufacturer, u.model_number] if b]
    label = ' '.join(bits) or 'Equipment'
    if u.serial_number:
        label += f" - SN {u.serial_number}"
    return label


@equipment_bp.route('/for-customer/<int:customer_id>')
@login_required
def for_customer(customer_id):
    """JSON: a customer's equipment, for the service-ticket equipment dropdown."""
    org_id = g.current_org_id
    units = (Unit.query
             .filter(Unit.organization_id == org_id, Unit.customer_id == customer_id,
                     Unit.is_inventory.isnot(True))
             .order_by(Unit.manufacturer, Unit.model_number).all())
    return {'results': [{'id': u.id, 'label': _unit_label(u)} for u in units]}


@equipment_bp.route('/')
@login_required
def index():
    org_id = g.current_org_id
    q = request.args.get('q', '').strip()
    customer_id = request.args.get('customer_id', type=int)
    page = request.args.get('page', 1, type=int)

    query = (Unit.query
             .filter(Unit.organization_id == org_id, Unit.is_inventory.isnot(True)))

    focus_customer = None
    if customer_id:
        focus_customer = Customer.query.filter_by(id=customer_id, organization_id=org_id).first()
        query = query.filter(Unit.customer_id == customer_id)

    if q:
        like = f'%{q}%'
        query = (query.outerjoin(Customer, Unit.customer_id == Customer.id)
                 .filter(or_(
                     Unit.serial_number.ilike(like),
                     Unit.manufacturer.ilike(like),
                     Unit.model_number.ilike(like),
                     Unit.owner_name.ilike(like),
                     Customer.first_name.ilike(like),
                     Customer.last_name.ilike(like),
                     Customer.company.ilike(like),
                 )))

    query = query.order_by(Unit.manufacturer.asc(), Unit.model_number.asc(), Unit.id.desc())
    pagination = query.paginate(page=page, per_page=50, error_out=False)

    return render_template('equipment/index.html', units=pagination.items, pagination=pagination,
                           q=q, focus_customer=focus_customer)


@equipment_bp.route('/new', methods=['GET', 'POST'])
@login_required
def new():
    org_id = g.current_org_id
    unit = Unit(organization_id=org_id, is_owned=True, is_inventory=False, status='Available')

    if request.method == 'POST':
        err = _apply_form(unit, org_id)
        if err:
            flash(err, 'danger')
        else:
            db.session.add(unit)
            db.session.commit()
            flash('Equipment added.', 'success')
            return redirect(url_for('equipment.edit', unit_id=unit.id))
        # fall through to re-render with entered values
    else:
        cid = request.args.get('customer_id', type=int)
        if cid:
            unit.customer_id = cid

    customer = Customer.query.get(unit.customer_id) if unit.customer_id else None
    return render_template('equipment/form.html', unit=unit, customer=customer, types=TYPES, is_new=True)


@equipment_bp.route('/<int:unit_id>', methods=['GET', 'POST'])
@login_required
def edit(unit_id):
    org_id = g.current_org_id
    unit = Unit.query.filter_by(id=unit_id, organization_id=org_id).first_or_404()

    if request.method == 'POST':
        err = _apply_form(unit, org_id)
        if err:
            flash(err, 'danger')
        else:
            db.session.commit()
            flash('Equipment updated.', 'success')
            return redirect(url_for('equipment.edit', unit_id=unit.id))

    customer = Customer.query.get(unit.customer_id) if unit.customer_id else None
    tickets = (ServiceTicket.query.filter_by(organization_id=org_id, unit_id=unit.id)
               .order_by(ServiceTicket.intake_date.desc()).all())
    return render_template('equipment/form.html', unit=unit, customer=customer, types=TYPES,
                           component_types=COMPONENT_TYPES, is_new=False, tickets=tickets)


def _apply_component(comp, org_id):
    f = request.form
    ctype = (f.get('component_type') or '').strip()
    if not ctype:
        return "Choose a component type."
    comp.component_type = ctype
    comp.manufacturer = (f.get('c_manufacturer') or '').strip() or None
    comp.model_number = (f.get('c_model_number') or '').strip() or None
    comp.serial_number = (f.get('c_serial_number') or '').strip() or None
    comp.notes = (f.get('c_notes') or '').strip() or None
    return None


@equipment_bp.route('/<int:unit_id>/components/add', methods=['POST'])
@login_required
def add_component(unit_id):
    org_id = g.current_org_id
    unit = Unit.query.filter_by(id=unit_id, organization_id=org_id).first_or_404()
    comp = UnitComponent(organization_id=org_id, unit_id=unit.id, component_type='Other')
    err = _apply_component(comp, org_id)
    if err:
        flash(err, 'danger')
    else:
        db.session.add(comp)
        db.session.commit()
        flash(f"{comp.component_type} info added.", 'success')
    return redirect(url_for('equipment.edit', unit_id=unit.id) + '#components')


@equipment_bp.route('/<int:unit_id>/components/<int:comp_id>/edit', methods=['POST'])
@login_required
def edit_component(unit_id, comp_id):
    org_id = g.current_org_id
    comp = UnitComponent.query.filter_by(id=comp_id, unit_id=unit_id, organization_id=org_id).first_or_404()
    err = _apply_component(comp, org_id)
    if err:
        flash(err, 'danger')
    else:
        db.session.commit()
        flash("Component updated.", 'success')
    return redirect(url_for('equipment.edit', unit_id=unit_id) + '#components')


@equipment_bp.route('/<int:unit_id>/components/<int:comp_id>/delete', methods=['POST'])
@login_required
def delete_component(unit_id, comp_id):
    org_id = g.current_org_id
    comp = UnitComponent.query.filter_by(id=comp_id, unit_id=unit_id, organization_id=org_id).first_or_404()
    db.session.delete(comp)
    db.session.commit()
    flash("Component removed.", 'success')
    return redirect(url_for('equipment.edit', unit_id=unit_id) + '#components')


@equipment_bp.route('/<int:unit_id>/delete', methods=['POST'])
@login_required
def delete(unit_id):
    org_id = g.current_org_id
    unit = Unit.query.filter_by(id=unit_id, organization_id=org_id).first_or_404()

    if ServiceTicket.query.filter_by(organization_id=org_id, unit_id=unit.id).count():
        flash("Can't delete equipment that's on a service ticket.", 'danger')
        return redirect(url_for('equipment.edit', unit_id=unit.id))
    if InvoiceLineItem.query.filter_by(unit_id=unit.id).count() or \
       PurchaseOrderLineItem.query.filter_by(unit_id=unit.id).count():
        flash("Can't delete equipment that's referenced on an invoice or purchase order.", 'danger')
        return redirect(url_for('equipment.edit', unit_id=unit.id))
    if unit.is_inventory:
        flash("This is a for-sale unit - manage it under Inventory › Whole Goods.", 'warning')
        return redirect(url_for('equipment.edit', unit_id=unit.id))

    db.session.delete(unit)
    db.session.commit()
    flash('Equipment deleted.', 'success')
    return redirect(url_for('equipment.index'))
