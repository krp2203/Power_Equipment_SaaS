"""
Shared numbering and totals logic for Invoices and Purchase Orders, used by
all three POS invoice flows (parts sale, whole-good sale, service invoice)
and by the purchasing module.
"""
from decimal import Decimal
from sqlalchemy import func


def next_invoice_number(org_id):
    from app.core.models import Invoice
    current_max = Invoice.query.filter_by(organization_id=org_id).with_entities(
        func.max(Invoice.invoice_number)
    ).scalar()
    return (current_max or 0) + 1


def next_po_number(org_id):
    from app.core.models import PurchaseOrder
    current_max = PurchaseOrder.query.filter_by(organization_id=org_id).with_entities(
        func.max(PurchaseOrder.po_number)
    ).scalar()
    return (current_max or 0) + 1


def recalculate_invoice_totals(invoice):
    """Recomputes subtotal/tax_amount/total from the invoice's current line items. Does not commit."""
    subtotal = sum((li.line_total for li in invoice.line_items), Decimal('0'))
    tax_rate = invoice.tax_rate or Decimal('0')
    tax_amount = (subtotal * tax_rate / Decimal('100')).quantize(Decimal('0.01'))

    invoice.subtotal = subtotal
    invoice.tax_amount = tax_amount
    invoice.total = subtotal + tax_amount
