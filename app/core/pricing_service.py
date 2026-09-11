"""
Extended price calculation: applies an organization's configured MarkupTier
cost-range rules to a part's dealer_cost to produce its extended_price
(the dealer's actual selling price, which may differ from the vendor's
suggested retail_price).
"""
from decimal import Decimal


def compute_extended_price(dealer_cost, tiers):
    """
    dealer_cost: Decimal/float/None
    tiers: iterable of MarkupTier belonging to one organization
    Returns a Decimal extended_price, or None if no cost or no matching tier.
    """
    if dealer_cost is None:
        return None
    cost = Decimal(str(dealer_cost))

    for tier in tiers:
        if tier.applies_to(cost):
            markup = Decimal(str(tier.markup_percent))
            return (cost * (Decimal('1') + markup / Decimal('100'))).quantize(Decimal('0.01'))

    return None


def effective_unit_price(part):
    """
    The single price to charge for one unit of `part` right now, used
    everywhere a part's sell price is read (part search, POS, service
    tickets): the computed extended_price (dealer_cost + markup tier) if
    it's been set, else the vendor's suggested retail_price, else the raw
    dealer_cost, else 0. Every caller must use this so the price shown when
    searching for a part always matches the price charged when it's added.
    """
    if part.extended_price is not None:
        return part.extended_price
    if part.retail_price is not None:
        return part.retail_price
    return part.dealer_cost or Decimal('0')


def recalculate_extended_prices(org_id):
    """
    Recomputes PartInventory.extended_price for every priced part in the
    org from its current dealer_cost and the org's current MarkupTiers.
    Call this after adding/editing/removing a markup tier, or as a manual
    "fix stale prices" action - extended_price is otherwise only computed
    once, at import or manual entry time, and does not update itself when
    tiers change later. Returns the number of parts whose price changed.
    """
    from app.core.extensions import db
    from app.core.models import PartInventory, MarkupTier

    tiers = MarkupTier.query.filter_by(organization_id=org_id).order_by(MarkupTier.min_cost).all()
    changed = 0
    parts = PartInventory.query.filter_by(organization_id=org_id).filter(PartInventory.dealer_cost.isnot(None))
    for part in parts.yield_per(500):
        new_price = compute_extended_price(part.dealer_cost, tiers)
        if new_price != part.extended_price:
            part.extended_price = new_price
            changed += 1
    db.session.commit()
    return changed
