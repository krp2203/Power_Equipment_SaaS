from flask import render_template, request, flash, redirect, url_for, g
from flask_login import login_required, current_user
from datetime import datetime
from . import service_tickets_bp
from app.core.extensions import db
from app.core.models import (ServiceTicket, ServiceTicketPart, ServiceTicketLabor, ServiceTicketNote,
                             Customer, Unit, User, PartInventory)

STATUSES = ['Received', 'In Progress', 'Waiting on Parts', 'Ready for Pickup', 'Closed']


@service_tickets_bp.route('/')
@login_required
def index():
    status_filter = request.args.get('status', 'Open')
    query = ServiceTicket.query.filter_by(organization_id=g.current_org_id)
    if status_filter == 'Open':
        query = query.filter(ServiceTicket.status != 'Closed')
    elif status_filter != 'All':
        query = query.filter_by(status=status_filter)
    tickets = query.order_by(ServiceTicket.intake_date.desc()).limit(200).all()
    return render_template('service_tickets/index.html', tickets=tickets, status_filter=status_filter, statuses=STATUSES)


@service_tickets_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    org_id = g.current_org_id
    if request.method == 'POST':
        customer_id = request.form.get('customer_id', '').strip()
        unit_id = request.form.get('unit_id', '').strip()
        technician_id = request.form.get('technician_id', '').strip()

        ticket = ServiceTicket(
            organization_id=org_id,
            customer_id=int(customer_id) if customer_id else None,
            unit_id=int(unit_id) if unit_id else None,
            technician_id=int(technician_id) if technician_id else None,
            reported_issue=request.form.get('reported_issue', '').strip(),
            status='Received',
        )
        db.session.add(ticket)
        db.session.commit()
        flash(f"Service Ticket #{ticket.id} created.", "success")
        return redirect(url_for('service_tickets.view', ticket_id=ticket.id))

    customers = Customer.query.filter_by(organization_id=org_id).order_by(Customer.last_name, Customer.first_name).all()
    technicians = _technicians(org_id)
    # Equipment is loaded on demand once a customer is picked (equipment.for_customer).
    return render_template('service_tickets/create.html', customers=customers, technicians=technicians)


def _technicians(org_id):
    """Users eligible to be assigned a ticket: anyone tagged Technician, plus Admins."""
    return (User.query
            .filter(User.organization_id == org_id, User.role.in_(['technician', 'admin']))
            .order_by(User.last_name, User.first_name, User.username)
            .all())


def _service_units(org_id, customer_id=None):
    """Equipment eligible to attach to a service ticket: customer-owned machines,
    NOT the dealer's for-sale whole-goods inventory. Scoped to one customer when given."""
    q = Unit.query.filter(Unit.organization_id == org_id, Unit.is_inventory.isnot(True))
    if customer_id:
        q = q.filter(Unit.customer_id == customer_id)
    return q.order_by(Unit.manufacturer, Unit.model_number).all()


@service_tickets_bp.route('/<int:ticket_id>')
@login_required
def view(ticket_id):
    ticket = ServiceTicket.query.filter_by(id=ticket_id, organization_id=g.current_org_id).first_or_404()
    uninvoiced_parts = [p for p in ticket.parts_used if not p.invoiced]
    uninvoiced_labor = [l for l in ticket.labor_entries if not l.invoiced]
    technicians = _technicians(g.current_org_id)
    # Change-equipment dropdown: scope to the ticket's customer when it has one.
    units = _service_units(g.current_org_id, customer_id=ticket.customer_id)
    # Keep the ticket's current equipment in the list even if it's owned by
    # someone else or since moved into for-sale inventory.
    if ticket.unit and ticket.unit not in units:
        units = [ticket.unit] + units
    return render_template('service_tickets/detail.html', ticket=ticket, statuses=STATUSES,
                            technicians=technicians, units=units,
                            uninvoiced_parts=uninvoiced_parts, uninvoiced_labor=uninvoiced_labor)


@service_tickets_bp.route('/<int:ticket_id>/status', methods=['POST'])
@login_required
def update_status(ticket_id):
    ticket = ServiceTicket.query.filter_by(id=ticket_id, organization_id=g.current_org_id).first_or_404()
    new_status = request.form.get('status')
    if new_status in STATUSES:
        ticket.status = new_status
        if new_status == 'Closed':
            ticket.closed_date = datetime.utcnow()
        db.session.commit()
        flash(f"Status updated to {new_status}.", "success")
    return redirect(url_for('service_tickets.view', ticket_id=ticket.id))


@service_tickets_bp.route('/<int:ticket_id>/technician', methods=['POST'])
@login_required
def update_technician(ticket_id):
    ticket = ServiceTicket.query.filter_by(id=ticket_id, organization_id=g.current_org_id).first_or_404()
    tech_id = request.form.get('technician_id', '').strip()
    if tech_id:
        tech = User.query.filter_by(id=int(tech_id), organization_id=g.current_org_id).first()
        if not tech:
            flash('Technician not found.', 'danger')
            return redirect(url_for('service_tickets.view', ticket_id=ticket.id))
        ticket.technician_id = tech.id
        tech_name = " ".join(p for p in [tech.first_name, tech.last_name] if p) or tech.username
        flash(f"Assigned to {tech_name}.", 'success')
    else:
        ticket.technician_id = None
        flash('Ticket unassigned.', 'success')
    db.session.commit()
    return redirect(url_for('service_tickets.view', ticket_id=ticket.id))


@service_tickets_bp.route('/<int:ticket_id>/unit', methods=['POST'])
@login_required
def update_unit(ticket_id):
    ticket = ServiceTicket.query.filter_by(id=ticket_id, organization_id=g.current_org_id).first_or_404()
    unit_id = request.form.get('unit_id', '').strip()
    if unit_id:
        unit = Unit.query.filter_by(id=int(unit_id), organization_id=g.current_org_id).first()
        if not unit:
            flash('Equipment not found.', 'danger')
            return redirect(url_for('service_tickets.view', ticket_id=ticket.id))
        ticket.unit_id = unit.id
        # Keep the equipment tied to this ticket's customer if it isn't already.
        if ticket.customer_id and not unit.customer_id:
            unit.customer_id = ticket.customer_id
        flash('Equipment attached to ticket.', 'success')
    else:
        ticket.unit_id = None
        flash('Equipment detached from ticket.', 'success')
    db.session.commit()
    return redirect(url_for('service_tickets.view', ticket_id=ticket.id))


@service_tickets_bp.route('/equipment/quick-add', methods=['POST'])
@login_required
def equipment_quick_add():
    """AJAX inline-add of a new Unit/equipment from the service-ticket screens."""
    manufacturer = request.form.get('manufacturer', '').strip()
    model_number = request.form.get('model_number', '').strip()
    serial_number = request.form.get('serial_number', '').strip()
    if not manufacturer and not model_number and not serial_number:
        return {'error': 'Enter at least a manufacturer, model, or serial number.'}, 400

    customer_id = request.form.get('customer_id', '').strip()
    customer = None
    if customer_id:
        customer = Customer.query.filter_by(id=int(customer_id), organization_id=g.current_org_id).first()

    if serial_number:
        existing = Unit.query.filter_by(serial_number=serial_number, organization_id=g.current_org_id).first()
        if existing:
            return {'error': f'Equipment with serial "{serial_number}" already exists.'}, 400

    unit = Unit(
        organization_id=g.current_org_id,
        manufacturer=manufacturer or None,
        model_number=model_number or None,
        serial_number=serial_number or None,
        type=request.form.get('type', '').strip() or None,
        unit_hours=request.form.get('unit_hours', '').strip() or None,
        customer_id=customer.id if customer else None,
        is_owned=True,
    )
    if customer:
        unit.owner_name = customer.name
        unit.owner_company = customer.company
        unit.owner_phone = customer.phone
        unit.owner_email = customer.email
    db.session.add(unit)
    db.session.commit()

    label_bits = [b for b in [unit.manufacturer, unit.model_number] if b]
    label = ' '.join(label_bits) or 'Equipment'
    if unit.serial_number:
        label += f' - SN {unit.serial_number}'
    return {'id': unit.id, 'label': label}


@service_tickets_bp.route('/<int:ticket_id>/notes', methods=['POST'])
@login_required
def add_note(ticket_id):
    ticket = ServiceTicket.query.filter_by(id=ticket_id, organization_id=g.current_org_id).first_or_404()
    body = request.form.get('body', '').strip()
    if not body:
        flash("Type a note before saving.", "warning")
        return redirect(url_for('service_tickets.view', ticket_id=ticket.id))
    db.session.add(ServiceTicketNote(
        organization_id=g.current_org_id, service_ticket_id=ticket.id,
        user_id=current_user.id, body=body,
    ))
    db.session.commit()
    flash("Note added.", "success")
    return redirect(url_for('service_tickets.view', ticket_id=ticket.id) + '#notes')


@service_tickets_bp.route('/<int:ticket_id>/parts/add', methods=['POST'])
@login_required
def add_part(ticket_id):
    ticket = ServiceTicket.query.filter_by(id=ticket_id, organization_id=g.current_org_id).first_or_404()

    part_inventory_id = request.form.get('part_inventory_id', '').strip()
    force = request.form.get('force_in_hand') in ('1', 'on', 'true', 'yes')
    try:
        quantity = int(request.form.get('quantity', 1))
    except ValueError:
        flash('Quantity must be a number.', 'danger')
        return redirect(url_for('service_tickets.view', ticket_id=ticket_id))

    stp = ServiceTicketPart(
        organization_id=g.current_org_id, service_ticket_id=ticket.id,
        quantity=quantity,
    )

    if part_inventory_id:
        part = PartInventory.query.filter_by(id=int(part_inventory_id), organization_id=g.current_org_id).first()
        if not part:
            flash('Part not found.', 'danger')
            return redirect(url_for('service_tickets.view', ticket_id=ticket_id))
        stp.part_number = part.part_number
        stp.cost_at_time_of_use = part.extended_price if part.extended_price is not None else (part.dealer_cost or 0)
        stp.description_at_time_of_use = part.description or part.part_number
        stp.part_inventory_id = part.id
        db.session.add(stp)

        from app.core.purchasing_service import apply_part_sale
        po_line, vendor, short, _taken = apply_part_sale(
            g.current_org_id, part, quantity, force=force, service_ticket_id=ticket.id)

        if force:
            db.session.commit()
            neg = (part.stock_on_hand or 0) < 0
            flash(f"Part added (forced sale). {part.part_number} stock is now {part.stock_on_hand}."
                  + (" It's on the Negative Stock report to reconcile." if neg else ""),
                  'warning' if neg else 'success')
        elif po_line:
            db.session.flush()
            stp.po_line_item_id = po_line.id
            if ticket.status in ('Received', 'In Progress'):
                ticket.status = 'Waiting on Parts'
            db.session.commit()
            flash(f"Part added. {short} special-ordered from {vendor.name} "
                  f"(draft PO #{po_line.purchase_order.po_number}).", 'info')
        elif short > 0:
            db.session.commit()
            flash(f"Part added, but {short} short on stock and no vendor is set for "
                  f"'{part.manufacturer or 'this manufacturer'}'. Map one under Purchasing › Vendors, "
                  f"or tick 'have it in hand' to sell without ordering.", 'warning')
        else:
            db.session.commit()
            flash('Part added.', 'success')
        return redirect(url_for('service_tickets.view', ticket_id=ticket_id))

    # Manual write-in: not in inventory, no stock movement, no special order.
    stp.part_number = request.form.get('part_number', '').strip()
    cost = request.form.get('cost', '0').strip() or '0'
    stp.description_at_time_of_use = request.form.get('description', '').strip()
    if not stp.part_number:
        flash('Part number is required.', 'danger')
        return redirect(url_for('service_tickets.view', ticket_id=ticket_id))
    try:
        stp.cost_at_time_of_use = float(cost)
    except ValueError:
        flash('Cost must be a number.', 'danger')
        return redirect(url_for('service_tickets.view', ticket_id=ticket_id))

    db.session.add(stp)
    db.session.commit()
    flash('Part added.', 'success')
    return redirect(url_for('service_tickets.view', ticket_id=ticket_id))


@service_tickets_bp.route('/<int:ticket_id>/parts/<int:part_id>/delete', methods=['POST'])
@login_required
def delete_part(ticket_id, part_id):
    ticket = ServiceTicket.query.filter_by(id=ticket_id, organization_id=g.current_org_id).first_or_404()
    part = ServiceTicketPart.query.filter_by(id=part_id, service_ticket_id=ticket.id).first_or_404()
    if part.invoiced:
        flash("Can't remove a part that's already been invoiced.", 'danger')
        return redirect(url_for('service_tickets.view', ticket_id=ticket_id))
    if part.part_inventory_id:
        from app.core.purchasing_service import reverse_part_sale
        reverse_part_sale(part.part, part.quantity, part.po_line_item)
    db.session.delete(part)
    db.session.commit()
    flash('Part removed.', 'success')
    return redirect(url_for('service_tickets.view', ticket_id=ticket_id))


@service_tickets_bp.route('/<int:ticket_id>/labor/add', methods=['POST'])
@login_required
def add_labor(ticket_id):
    ticket = ServiceTicket.query.filter_by(id=ticket_id, organization_id=g.current_org_id).first_or_404()

    rate_raw = request.form.get('rate', '').strip()
    try:
        hours = float(request.form.get('hours_spent', '0'))
        if rate_raw:
            rate = float(rate_raw)
        else:
            rate = float(current_user.labor_rate or g.current_org.default_labor_rate or 0)
    except (ValueError, TypeError):
        flash('Hours and rate must be numbers.', 'danger')
        return redirect(url_for('service_tickets.view', ticket_id=ticket_id))

    if hours <= 0:
        flash('Hours must be greater than 0.', 'danger')
        return redirect(url_for('service_tickets.view', ticket_id=ticket_id))

    db.session.add(ServiceTicketLabor(
        organization_id=g.current_org_id, service_ticket_id=ticket.id, user_id=current_user.id,
        hours_spent=hours, rate_at_time_of_log=rate, description=request.form.get('description', '').strip(),
    ))
    db.session.commit()
    flash('Labor entry added.', 'success')
    return redirect(url_for('service_tickets.view', ticket_id=ticket_id))


@service_tickets_bp.route('/<int:ticket_id>/labor/<int:labor_id>/delete', methods=['POST'])
@login_required
def delete_labor(ticket_id, labor_id):
    ticket = ServiceTicket.query.filter_by(id=ticket_id, organization_id=g.current_org_id).first_or_404()
    labor = ServiceTicketLabor.query.filter_by(id=labor_id, service_ticket_id=ticket.id).first_or_404()
    if labor.invoiced:
        flash("Can't remove labor that's already been invoiced.", 'danger')
        return redirect(url_for('service_tickets.view', ticket_id=ticket_id))
    db.session.delete(labor)
    db.session.commit()
    flash('Labor entry removed.', 'success')
    return redirect(url_for('service_tickets.view', ticket_id=ticket_id))
