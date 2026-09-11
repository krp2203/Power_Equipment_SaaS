"""Special-order helpers: pick the vendor for a part, keep one rolling draft
PO per vendor, and append shortfall lines to it when stock runs short."""
from app.core.extensions import db
from app.core.invoicing_service import next_po_number


def vendor_for_part(org_id, part):
    """Which vendor to special-order `part` from:
      1. the part's own vendor_id override, if set;
      2. else the primary VendorManufacturer for the part's manufacturer;
      3. else the sole VendorManufacturer for that manufacturer;
      4. else None (ambiguous / unmapped - staff must assign).
    """
    from app.core.models import Vendor, VendorManufacturer

    if part.vendor_id:
        return db.session.get(Vendor, part.vendor_id)
    if not part.manufacturer:
        return None

    vms = VendorManufacturer.query.filter_by(
        organization_id=org_id, manufacturer=part.manufacturer
    ).all()
    if not vms:
        return None
    primary = next((vm for vm in vms if vm.is_primary), None)
    chosen = primary or (vms[0] if len(vms) == 1 else None)
    return db.session.get(Vendor, chosen.vendor_id) if chosen else None


def rolling_draft_po(org_id, vendor_id):
    """Find (or create) the open auto-draft PO for a vendor - special orders
    pile onto it until someone reviews it and marks it ordered."""
    from app.core.models import PurchaseOrder

    po = (PurchaseOrder.query
          .filter_by(organization_id=org_id, vendor_id=vendor_id,
                     status='draft', is_auto_draft=True)
          .order_by(PurchaseOrder.id.desc())
          .first())
    if po is None:
        po = PurchaseOrder(organization_id=org_id, vendor_id=vendor_id,
                           po_number=next_po_number(org_id),
                           status='draft', is_auto_draft=True)
        db.session.add(po)
        db.session.flush()
    return po


def special_order_shortfall(org_id, part, qty_needed, *, service_ticket_id=None, invoice_id=None):
    """If on-hand stock is short of qty_needed, append the shortfall to the
    vendor's rolling draft PO.

    Call this BEFORE decrementing stock for the pull. Only positive on-hand
    counts toward covering the line - anything already negative is short stock
    that a prior pull's special order is already covering.

    Returns (po_line_item | None, vendor | None, shortfall_qty).
      - (line, vendor, n)  -> ordered n from vendor
      - (None, None, n)    -> short by n but no vendor could be resolved
      - (None, None, 0)    -> enough stock, nothing to do
    """
    from app.core.models import PurchaseOrderLineItem

    on_hand = max(0, part.stock_on_hand or 0)
    shortfall = qty_needed - on_hand
    if shortfall <= 0:
        return None, None, 0

    vendor = vendor_for_part(org_id, part)
    if vendor is None:
        return None, None, shortfall

    po = rolling_draft_po(org_id, vendor.id)
    line = PurchaseOrderLineItem(
        purchase_order_id=po.id,
        line_type='part',
        part_inventory_id=part.id,
        part_number=part.part_number,
        manufacturer=part.manufacturer,
        description=part.description,
        quantity_ordered=shortfall,
        unit_cost=part.dealer_cost,
        service_ticket_id=service_ticket_id,
        invoice_id=invoice_id,
    )
    db.session.add(line)
    db.session.flush()
    return line, vendor, shortfall


def apply_part_sale(org_id, part, qty, *, force=False, service_ticket_id=None, invoice_id=None):
    """Record selling `qty` of `part` on a sale or service ticket.

    Normal: take only what's physically on the shelf (stock never goes below 0)
    and special-order the shortfall onto the vendor's draft PO.

    force=True: the counter has the item in hand even though the count says it's
    short - take the full quantity (stock may go negative, shows on the Negative
    Stock report) and raise NO special order.

    Returns (po_line_item | None, vendor | None, shortfall, taken_from_stock).
    """
    on_hand = part.stock_on_hand or 0
    if force:
        part.stock_on_hand = on_hand - qty
        return None, None, 0, qty

    take = max(0, min(qty, on_hand))
    po_line, vendor, shortfall = special_order_shortfall(
        org_id, part, qty, service_ticket_id=service_ticket_id, invoice_id=invoice_id)
    part.stock_on_hand = on_hand - take
    return po_line, vendor, shortfall, take


def reverse_part_sale(part, quantity, po_line_item):
    """Undo apply_part_sale for a voided invoice or a removed ticket part:
    give back exactly what was taken from stock, and cancel the special order
    if it is still an un-ordered draft line."""
    ordered = po_line_item.quantity_ordered if po_line_item else 0
    taken = int(quantity or 0) - ordered
    if taken > 0 and part is not None:
        part.stock_on_hand = (part.stock_on_hand or 0) + taken
    if (po_line_item is not None
            and po_line_item.quantity_received == 0
            and po_line_item.purchase_order.status == 'draft'):
        db.session.delete(po_line_item)
