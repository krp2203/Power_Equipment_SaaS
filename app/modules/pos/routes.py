from flask import render_template, g, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from datetime import datetime
from decimal import Decimal, InvalidOperation
from . import pos_bp
from app.core.models import (Customer, Invoice, InvoiceLineItem, ServiceTicket, ServiceTicketPart,
                             ServiceTicketLabor, PartInventory, Unit, PurchaseOrderLineItem)
from app.core.extensions import db
from app.core.invoicing_service import next_invoice_number, recalculate_invoice_totals
from app.core.purchasing_service import apply_part_sale, reverse_part_sale
from .forms import CustomerForm


@pos_bp.route('/')
@login_required
def hub():
    recent_invoices = Invoice.query.filter_by(organization_id=g.current_org.id).order_by(Invoice.created_at.desc()).limit(10).all()
    return render_template('pos/hub.html', recent_invoices=recent_invoices)


# ====== CUSTOMERS ======

@pos_bp.route('/customers')
@login_required
def customers():
    all_customers = Customer.query.filter_by(organization_id=g.current_org.id).order_by(Customer.last_name, Customer.first_name).all()
    form = CustomerForm()
    return render_template('pos/customers.html', customers=all_customers, form=form)


@pos_bp.route('/customers/add', methods=['POST'])
@login_required
def add_customer():
    form = CustomerForm()
    if form.validate_on_submit():
        customer = Customer(
            organization_id=g.current_org.id,
            first_name=(form.first_name.data or '').strip() or None,
            last_name=form.last_name.data.strip(),
            company=form.company.data,
            address=form.address.data,
            phone=form.phone.data,
            email=form.email.data,
            tax_exempt=form.tax_exempt.data,
            notes=form.notes.data,
        )
        db.session.add(customer)
        db.session.commit()
        flash(f"Customer '{customer.name}' added.", "success")
    else:
        flash("Please correct the errors and try again.", "danger")
    return redirect(url_for('pos.customers'))


@pos_bp.route('/customers/<int:customer_id>/edit', methods=['POST'])
@login_required
def edit_customer(customer_id):
    customer = Customer.query.filter_by(id=customer_id, organization_id=g.current_org.id).first_or_404()
    form = CustomerForm()
    if form.validate_on_submit():
        customer.first_name = (form.first_name.data or '').strip() or None
        customer.last_name = form.last_name.data.strip()
        customer.company = form.company.data
        customer.address = form.address.data
        customer.phone = form.phone.data
        customer.email = form.email.data
        customer.tax_exempt = form.tax_exempt.data
        customer.notes = form.notes.data
        db.session.commit()
        flash(f"Customer '{customer.name}' updated.", "success")
    else:
        flash("Please correct the errors and try again.", "danger")
    return redirect(url_for('pos.customers'))


@pos_bp.route('/customers/<int:customer_id>/delete', methods=['POST'])
@login_required
def delete_customer(customer_id):
    customer = Customer.query.filter_by(id=customer_id, organization_id=g.current_org.id).first_or_404()
    if customer.invoices:
        flash(f"Can't delete '{customer.name}' - they have invoices on file.", "danger")
        return redirect(url_for('pos.customers'))
    db.session.delete(customer)
    db.session.commit()
    flash("Customer removed.", "success")
    return redirect(url_for('pos.customers'))


def _get_org_tax_rate(org):
    return org.default_tax_rate


# ====== SERVICE INVOICE (from a ServiceTicket) ======

@pos_bp.route('/invoices/new/service/<int:ticket_id>', methods=['GET', 'POST'])
@login_required
def new_service_invoice(ticket_id):
    org = g.current_org
    ticket = ServiceTicket.query.filter_by(id=ticket_id, organization_id=org.id).first_or_404()

    uninvoiced_parts = [p for p in ticket.parts_used if not p.invoiced]
    uninvoiced_labor = [l for l in ticket.labor_entries if not l.invoiced]

    if not uninvoiced_parts and not uninvoiced_labor:
        flash("This ticket has no un-invoiced parts or labor.", "warning")
        return redirect(url_for('service_tickets.view', ticket_id=ticket.id))

    if request.method == 'POST':
        try:
            tax_rate = Decimal(request.form.get('tax_rate', '0') or '0')
        except InvalidOperation:
            tax_rate = Decimal('0')

        customer = ticket.customer
        unit = ticket.unit
        invoice = Invoice(
            organization_id=org.id,
            invoice_number=next_invoice_number(org.id),
            invoice_type='service',
            service_ticket_id=ticket.id,
            customer_id=customer.id if customer else None,
            bill_to_name=request.form.get('bill_to_name', '').strip() or (customer.name if customer else (unit.owner_name if unit else '')),
            bill_to_company=request.form.get('bill_to_company', '').strip() or (customer.company if customer else (unit.owner_company if unit else '')),
            bill_to_address=request.form.get('bill_to_address', '').strip() or (customer.address if customer else (unit.owner_address if unit else '')),
            bill_to_phone=request.form.get('bill_to_phone', '').strip() or (customer.phone if customer else (unit.owner_phone if unit else '')),
            bill_to_email=request.form.get('bill_to_email', '').strip() or (customer.email if customer else (unit.owner_email if unit else '')),
            status='unpaid',
            tax_rate=Decimal('0') if (customer and customer.tax_exempt) else tax_rate,
            created_by=current_user.id,
        )
        db.session.add(invoice)
        db.session.flush()

        for pu in uninvoiced_parts:
            db.session.add(InvoiceLineItem(
                invoice_id=invoice.id, line_type='part',
                description=f"{pu.quantity}x {pu.description_at_time_of_use or pu.part_number}",
                quantity=pu.quantity, unit_price=pu.cost_at_time_of_use,
                line_total=pu.quantity * pu.cost_at_time_of_use,
            ))
            pu.invoiced = True

        for le in uninvoiced_labor:
            db.session.add(InvoiceLineItem(
                invoice_id=invoice.id, line_type='labor',
                description=le.description or 'Labor',
                quantity=le.hours_spent, unit_price=le.rate_at_time_of_log,
                line_total=le.hours_spent * le.rate_at_time_of_log,
            ))
            le.invoiced = True

        db.session.flush()
        recalculate_invoice_totals(invoice)

        # Invoicing a service ticket means the job is done - close it.
        closed_note = ""
        if ticket.status != 'Closed':
            ticket.status = 'Closed'
            ticket.closed_date = datetime.utcnow()
            closed_note = f" Service Ticket #{ticket.id} marked Closed."

        db.session.commit()
        flash(f"Invoice #{invoice.invoice_number} created.{closed_note}", "success")
        return redirect(url_for('pos.view_invoice', invoice_id=invoice.id))

    default_tax_rate = _get_org_tax_rate(org)
    return render_template('pos/new_service_invoice.html', ticket=ticket, uninvoiced_parts=uninvoiced_parts,
                            uninvoiced_labor=uninvoiced_labor, default_tax_rate=default_tax_rate)


# ====== NEW SALE (mixed parts + whole goods on one ticket) ======

@pos_bp.route('/invoices/new', methods=['GET', 'POST'])
@login_required
def new_sale():
    org = g.current_org

    if request.method == 'POST':
        try:
            tax_rate = Decimal(request.form.get('tax_rate', '0') or '0')
        except InvalidOperation:
            tax_rate = Decimal('0')

        customer_id = request.form.get('customer_id', '').strip()
        customer = Customer.query.filter_by(id=int(customer_id), organization_id=org.id).first() if customer_id else None

        line_types = request.form.getlist('line_type[]')
        ref_ids = request.form.getlist('line_ref_id[]')
        descs = request.form.getlist('line_desc[]')
        qtys = request.form.getlist('line_qty[]')
        prices = request.form.getlist('line_price[]')
        forces = request.form.getlist('line_force[]')  # "1" = counter has it in hand

        line_data = []
        for i in range(len(qtys)):
            try:
                qty = Decimal(qtys[i] or '0')
                price = Decimal(prices[i] or '0')
            except InvalidOperation:
                continue
            if qty <= 0:
                continue
            line_type = line_types[i].strip() if i < len(line_types) else 'part'
            ref_id = ref_ids[i].strip() if i < len(ref_ids) else ''
            desc = descs[i].strip() if i < len(descs) else ''
            force = (forces[i].strip() in ('1', 'on', 'true', 'yes')) if i < len(forces) else False
            if not ref_id and not desc:
                continue
            line_data.append((line_type, ref_id, desc, qty, price, force))

        if not line_data:
            flash("Add at least one line item.", "danger")
            return redirect(url_for('pos.new_sale'))

        # A whole good can only appear once (each unit is a unique physical item)
        sold_units = []
        for line_type, ref_id, desc, qty, price, force in line_data:
            if line_type == 'whole_good' and ref_id:
                unit = Unit.query.filter_by(id=int(ref_id), organization_id=org.id).first()
                if not unit:
                    flash("One of the selected units was not found.", "danger")
                    return redirect(url_for('pos.new_sale'))
                if unit.status == 'Sold':
                    flash(f"{unit.manufacturer} {unit.model_number} is already marked Sold.", "danger")
                    return redirect(url_for('pos.new_sale'))
                sold_units.append(unit)

        invoice_type = 'whole_good' if any(lt == 'whole_good' for lt, *_ in line_data) else 'parts'
        if invoice_type == 'whole_good' and any(lt == 'part' for lt, *_ in line_data):
            invoice_type = 'mixed'

        invoice = Invoice(
            organization_id=org.id,
            invoice_number=next_invoice_number(org.id),
            invoice_type=invoice_type,
            customer_id=customer.id if customer else None,
            bill_to_name=request.form.get('bill_to_name', '').strip() or (customer.name if customer else ''),
            bill_to_company=request.form.get('bill_to_company', '').strip() or (customer.company if customer else ''),
            bill_to_address=request.form.get('bill_to_address', '').strip() or (customer.address if customer else ''),
            bill_to_phone=request.form.get('bill_to_phone', '').strip() or (customer.phone if customer else ''),
            bill_to_email=request.form.get('bill_to_email', '').strip() or (customer.email if customer else ''),
            status='unpaid',
            tax_rate=Decimal('0') if (customer and customer.tax_exempt) else tax_rate,
            created_by=current_user.id,
        )
        db.session.add(invoice)
        db.session.flush()

        special_orders, needs_vendor, forced_negative = [], [], []
        for line_type, ref_id, desc, qty, price, force in line_data:
            if line_type == 'whole_good':
                unit = next(u for u in sold_units if str(u.id) == ref_id)
                db.session.add(InvoiceLineItem(
                    invoice_id=invoice.id, line_type='whole_good',
                    description=desc or f"{unit.year or ''} {unit.manufacturer or ''} {unit.model_number or ''} (SN: {unit.serial_number or 'N/A'})".strip(),
                    quantity=1, unit_price=price, line_total=price,
                    unit_id=unit.id,
                ))
                unit.status = 'Sold'
                if customer:
                    unit.customer_id = customer.id
            else:
                part = PartInventory.query.filter_by(id=int(ref_id), organization_id=org.id).first() if ref_id else None
                li = InvoiceLineItem(
                    invoice_id=invoice.id, line_type='part',
                    description=desc or (part.description or part.part_number if part else 'Part'),
                    quantity=qty, unit_price=price, line_total=qty * price,
                    part_inventory_id=part.id if part else None,
                )
                db.session.add(li)
                if part:
                    db.session.flush()
                    po_line, vendor, short, _taken = apply_part_sale(
                        org.id, part, int(qty), force=force, invoice_id=invoice.id)
                    if po_line:
                        li.po_line_item_id = po_line.id
                        special_orders.append(f"{short}× {part.part_number} → {vendor.name} (PO #{po_line.purchase_order.po_number})")
                    elif force and (part.stock_on_hand or 0) < 0:
                        forced_negative.append(f"{part.part_number} ({part.stock_on_hand})")
                    elif short > 0:
                        needs_vendor.append(part.part_number)

        db.session.flush()
        recalculate_invoice_totals(invoice)
        db.session.commit()
        sold_note = " Unit(s) marked Sold." if sold_units else ""
        msg = f"Invoice #{invoice.invoice_number} created.{sold_note}"
        if special_orders:
            msg += " Special-ordered: " + "; ".join(special_orders) + "."
        flash(msg, "success")
        if needs_vendor:
            flash("No vendor is mapped for: " + ", ".join(sorted(set(needs_vendor)))
                  + ". These weren't ordered — map a vendor under Purchasing › Vendors, "
                  + "or tick 'have in hand' to sell without ordering.", "warning")
        if forced_negative:
            flash("Forced sale — stock is now negative for: " + ", ".join(forced_negative)
                  + ". Reconcile on the Negative Stock report.", "warning")
        return redirect(url_for('pos.view_invoice', invoice_id=invoice.id))

    # Parts are searched on demand via the part picker (inventory.search_parts) -
    # a dealer can have 100k+ of them, so they are never bulk-loaded into the page.
    units = Unit.query.filter_by(organization_id=org.id, status='Available').order_by(Unit.manufacturer).all()
    default_tax_rate = _get_org_tax_rate(org)
    return render_template('pos/new_sale.html', units=units, default_tax_rate=default_tax_rate)


# ====== INVOICE LIST / DETAIL / PAYMENT ======

@pos_bp.route('/invoices')
@login_required
def invoices():
    status_filter = request.args.get('status', '')
    query = Invoice.query.filter_by(organization_id=g.current_org.id)
    if status_filter:
        query = query.filter_by(status=status_filter)
    all_invoices = query.order_by(Invoice.created_at.desc()).all()
    return render_template('pos/invoices.html', invoices=all_invoices, status_filter=status_filter)


@pos_bp.route('/invoices/<int:invoice_id>')
@login_required
def view_invoice(invoice_id):
    invoice = Invoice.query.filter_by(id=invoice_id, organization_id=g.current_org.id).first_or_404()
    return render_template('pos/invoice_detail.html', invoice=invoice)


@pos_bp.route('/invoices/<int:invoice_id>/mark-paid', methods=['POST'])
@login_required
def mark_paid(invoice_id):
    invoice = Invoice.query.filter_by(id=invoice_id, organization_id=g.current_org.id).first_or_404()
    payment_method = request.form.get('payment_method', '').strip()
    payment_reference = request.form.get('payment_reference', '').strip()

    if not payment_method:
        flash("Select a payment method.", "danger")
        return redirect(url_for('pos.view_invoice', invoice_id=invoice.id))

    invoice.status = 'paid'
    invoice.payment_method = payment_method
    invoice.payment_reference = payment_reference or None
    invoice.paid_amount = invoice.total
    invoice.paid_at = datetime.utcnow()
    db.session.commit()
    flash(f"Invoice #{invoice.invoice_number} marked paid.", "success")
    return redirect(url_for('pos.view_invoice', invoice_id=invoice.id))


@pos_bp.route('/invoices/<int:invoice_id>/void', methods=['POST'])
@login_required
def void_invoice(invoice_id):
    invoice = Invoice.query.filter_by(id=invoice_id, organization_id=g.current_org.id).first_or_404()
    if invoice.status == 'void':
        flash("That invoice is already voided.", "info")
        return redirect(url_for('pos.view_invoice', invoice_id=invoice.id))
    if invoice.status == 'paid':
        flash("Paid invoices can't be voided. Refund it first.", "danger")
        return redirect(url_for('pos.view_invoice', invoice_id=invoice.id))

    notes = []
    if invoice.invoice_type == 'service':
        # Service invoices don't move stock themselves - the parts were pulled and
        # any special orders raised when they were added to the ticket. Voiding
        # just releases the ticket's parts/labor to be invoiced again.
        if invoice.service_ticket_id:
            n = 0
            for stp in ServiceTicketPart.query.filter_by(service_ticket_id=invoice.service_ticket_id, invoiced=True):
                stp.invoiced = False
                n += 1
            for stl in ServiceTicketLabor.query.filter_by(service_ticket_id=invoice.service_ticket_id, invoiced=True):
                stl.invoiced = False
                n += 1
            if n:
                notes.append(f"released {n} ticket line(s) to re-invoice")
    else:
        # Parts / whole-good / mixed sales: undo the inventory effects.
        for li in invoice.line_items:
            if li.line_type == 'whole_good' and li.unit_id:
                unit = db.session.get(Unit, li.unit_id)
                if unit and unit.status == 'Sold':
                    unit.status = 'Available'
                    unit.customer_id = None
                    notes.append(f"{unit.manufacturer or ''} {unit.model_number or ''}".strip() + " back to Available")
            elif li.line_type == 'part' and li.part_inventory_id:
                part = db.session.get(PartInventory, li.part_inventory_id)
                pol = li.po_line_item
                had_draft_po = bool(pol and pol.quantity_received == 0 and pol.purchase_order.status == 'draft')
                # Give back exactly what was pulled from stock; cancel an un-ordered special order.
                reverse_part_sale(part, li.quantity, pol)
                if had_draft_po:
                    notes.append(f"cancelled special order for {part.part_number if part else 'part'}")

    invoice.status = 'void'
    db.session.commit()
    detail = (" (" + "; ".join(notes) + ")") if notes else ""
    flash(f"Invoice #{invoice.invoice_number} voided.{detail}", "success")
    return redirect(url_for('pos.view_invoice', invoice_id=invoice.id))


@pos_bp.route('/invoices/<int:invoice_id>/email', methods=['POST'])
@login_required
def email_invoice(invoice_id):
    from app.core.email import send_invoice_email

    invoice = Invoice.query.filter_by(id=invoice_id, organization_id=g.current_org.id).first_or_404()
    recipient = request.form.get('recipient_email', '').strip() or invoice.bill_to_email

    if not recipient:
        flash("No email address on file for this invoice. Enter one to send.", "danger")
        return redirect(url_for('pos.view_invoice', invoice_id=invoice.id))

    if send_invoice_email(invoice, recipient, g.current_org):
        flash(f"Invoice #{invoice.invoice_number} emailed to {recipient}.", "success")
    else:
        flash(f"Could not send the email to {recipient}. Check the mail configuration and try again.", "danger")

    return redirect(url_for('pos.view_invoice', invoice_id=invoice.id))


# ====== CUSTOMER SEARCH / QUICK-ADD (AJAX, used by the shared customer picker) ======

@pos_bp.route('/customers/search')
@login_required
def search_customers():
    import re
    from sqlalchemy import func

    q = request.args.get('q', '').strip()
    if len(q) < 2:
        return {'results': []}

    org_id = g.current_org.id
    like = f'%{q}%'
    q_digits = re.sub(r'\D', '', q)

    filters = [Customer.name.ilike(like), Customer.company.ilike(like)]
    if q_digits:
        filters.append(func.regexp_replace(Customer.phone, '[^0-9]', '', 'g').ilike(f'%{q_digits}%'))

    results = Customer.query.filter_by(organization_id=org_id).filter(db.or_(*filters)).order_by(Customer.last_name, Customer.first_name).limit(20).all()
    return {'results': [
        {'id': c.id, 'name': c.name, 'first_name': c.first_name or '', 'last_name': c.last_name or '',
         'company': c.company or '', 'address': c.address or '',
         'phone': c.phone or '', 'email': c.email or '', 'tax_exempt': c.tax_exempt}
        for c in results
    ]}


@pos_bp.route('/customers/quick-add', methods=['POST'])
@login_required
def quick_add_customer():
    first_name = request.form.get('first_name', '').strip()
    last_name = request.form.get('last_name', '').strip()
    # Back-compat: accept a single "name" and split on the last space.
    if not last_name:
        legacy = request.form.get('name', '').strip()
        if legacy:
            parts = legacy.rsplit(' ', 1)
            if len(parts) == 2:
                first_name, last_name = parts[0], parts[1]
            else:
                last_name = legacy
    if not last_name:
        return {'error': 'Last name is required'}, 400

    customer = Customer(
        organization_id=g.current_org.id,
        first_name=first_name or None,
        last_name=last_name,
        company=request.form.get('company', '').strip() or None,
        phone=request.form.get('phone', '').strip() or None,
        email=request.form.get('email', '').strip() or None,
        address=request.form.get('address', '').strip() or None,
    )
    db.session.add(customer)
    db.session.commit()
    return {'id': customer.id, 'name': customer.name,
            'first_name': customer.first_name or '', 'last_name': customer.last_name or '',
            'company': customer.company or '',
            'address': customer.address or '', 'phone': customer.phone or '', 'email': customer.email or '',
            'tax_exempt': customer.tax_exempt}
