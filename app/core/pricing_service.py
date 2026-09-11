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
