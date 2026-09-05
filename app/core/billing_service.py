"""
Shared billing logic used by both the super-admin "Start Plan" action and
the dealer's own "Start My Plan" action. Trial orgs carry no card on file;
converting to paid always collects a fresh card at the moment of activation.
"""

SETUP_FEE_CENTS = 19900   # $199.00 one-time
DEFAULT_MONTHLY_CENTS = 4900  # $49.00/mo, unless the org has a custom monthly_price


class ActivationError(Exception):
    """Raised when starting a paid plan fails; message is safe to flash to the user."""
    pass


def activate_subscription(org, card_nonce, contact_email, contact_name):
    """
    Converts a trial Organization to an active paid subscription:
    creates the Square customer, charges the setup fee + first month,
    stores the card, ensures the shared Catalog plan exists, and starts a
    real recurring subscription priced at the org's monthly_price.

    Raises ActivationError with a user-safe message on any failure.
    Returns nothing; mutates and commits `org` on success.
    """
    from app.core.extensions import db
    from app.integrations.square_payments import SquarePaymentService

    if org.subscription_status == 'active':
        raise ActivationError("This site's plan is already active.")

    monthly_price_cents = org.monthly_price or DEFAULT_MONTHLY_CENTS
    initial_charge_cents = SETUP_FEE_CENTS + monthly_price_cents

    square = SquarePaymentService()

    customer_id = org.customer_id or square.create_customer(contact_email, contact_name)
    if not customer_id:
        raise ActivationError("Could not create payment customer. Please try again.")

    # The card nonce from the Web Payments SDK is single-use — consume it once
    # here to get a durable card_id, then use that card_id for both the
    # initial charge and the recurring subscription. Charging with the raw
    # nonce and separately trying to store the same (already-spent) nonce
    # produces a card reference Square can't actually bill recurringly.
    card_id = square.store_card(customer_id, card_nonce)
    if not card_id:
        raise ActivationError("Could not save the card on file. Please try again.")

    success, result = square.charge_card(
        source_id=card_id,
        amount_cents=initial_charge_cents,
        customer_id=customer_id,
        note=f"Setup Fee & First Month for {org.name}"
    )
    if not success:
        raise ActivationError(f"Payment failed: {result}")
    payment_id = result

    plan_variation_id = square.ensure_base_plan_variation()
    if not plan_variation_id:
        raise ActivationError(
            f"Card was charged (payment {payment_id}) but the recurring subscription could not be created. "
            "Contact support before retrying to avoid a duplicate charge."
        )

    subscription_id = square.start_subscription(customer_id, card_id, plan_variation_id, monthly_price_cents)
    if not subscription_id:
        raise ActivationError(
            f"Card was charged (payment {payment_id}) but the recurring subscription could not be created. "
            "Contact support before retrying to avoid a duplicate charge."
        )

    org.customer_id = customer_id
    org.subscription_id = subscription_id
    org.subscription_status = 'active'
    org.monthly_price = monthly_price_cents
    db.session.commit()
