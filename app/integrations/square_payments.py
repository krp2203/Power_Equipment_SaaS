import os
import sys
import uuid
import hmac
import hashlib
import base64

from square import Square
from square.client import SquareEnvironment
from square.core.api_error import ApiError

BASE_PLAN_NAME = "Base Plan"


class SquarePaymentService:
    def __init__(self):
        self.access_token = os.environ.get('SQUARE_ACCESS_TOKEN')
        self.location_id = os.environ.get('SQUARE_LOCATION_ID')
        env_name = os.environ.get('SQUARE_ENVIRONMENT', 'sandbox')
        environment = SquareEnvironment.PRODUCTION if env_name == 'production' else SquareEnvironment.SANDBOX

        if not self.access_token:
            print("CRITICAL WARNING: SQUARE_ACCESS_TOKEN is missing in environment!", file=sys.stderr)

        self.client = Square(token=self.access_token, environment=environment)

    def create_customer(self, email, name):
        """Create a Customer in Square. Returns customer_id or None."""
        try:
            given_name = name.split(" ")[0]
            family_name = " ".join(name.split(" ")[1:]) if " " in name else ""
            response = self.client.customers.create(
                given_name=given_name,
                family_name=family_name,
                email_address=email,
                reference_id=f"pes-{uuid.uuid4().hex[:8]}"
            )
            return response.customer.id
        except ApiError as e:
            print(f"Square Create Customer Error: {e.body}", file=sys.stderr)
            return None

    def charge_card(self, source_id, amount_cents, customer_id, note="Charge"):
        """Process a one-time payment. Returns (success, payment_id_or_error_message)."""
        try:
            response = self.client.payments.create(
                source_id=source_id,
                idempotency_key=str(uuid.uuid4()),
                amount_money={"amount": amount_cents, "currency": "USD"},
                customer_id=customer_id,
                note=note
            )
            return True, response.payment.id
        except ApiError as e:
            print(f"Square Charge Error: {e.body}", file=sys.stderr)
            detail = e.body.get('errors', [{}])[0].get('detail', 'Unknown Error') if isinstance(e.body, dict) else str(e.body)
            return False, detail

    def store_card(self, customer_id, card_nonce):
        """Store a card on file for a customer. Returns card_id or None."""
        try:
            response = self.client.cards.create(
                idempotency_key=str(uuid.uuid4()),
                source_id=card_nonce,
                card={"customer_id": customer_id}
            )
            return response.card.id
        except ApiError as e:
            print(f"Square Store Card Error: {e.body}", file=sys.stderr)
            return None

    def ensure_base_plan_variation(self):
        """
        Idempotently find-or-create the single 'Base Plan' Catalog subscription
        plan + monthly variation, shared by every dealer. Per-dealer pricing is
        handled separately via price_override_money on each subscription, not
        by creating a new Catalog plan per price tier.

        Returns the plan_variation_id, or None on failure.
        """
        try:
            existing = self.client.catalog.search(
                object_types=["SUBSCRIPTION_PLAN"],
                include_related_objects=True
            )
            for obj in (existing.objects or []):
                plan_data = getattr(obj, 'subscription_plan_data', None)
                if plan_data and plan_data.name == BASE_PLAN_NAME:
                    variations = plan_data.subscription_plan_variations or []
                    if variations:
                        return variations[0].id
        except ApiError as e:
            print(f"Square Catalog Search Error: {e.body}", file=sys.stderr)

        # Not found — create it. Default recurring price is a placeholder;
        # every real subscription overrides it via price_override_money.
        try:
            variation_id = f"#base-plan-variation-{uuid.uuid4().hex[:8]}"
            response = self.client.catalog.object.upsert(
                idempotency_key=str(uuid.uuid4()),
                object={
                    "type": "SUBSCRIPTION_PLAN",
                    "id": f"#base-plan-{uuid.uuid4().hex[:8]}",
                    "subscription_plan_data": {
                        "name": BASE_PLAN_NAME,
                        "subscription_plan_variations": [
                            {
                                "type": "SUBSCRIPTION_PLAN_VARIATION",
                                "id": variation_id,
                                "subscription_plan_variation_data": {
                                    "name": f"{BASE_PLAN_NAME} - Monthly",
                                    "phases": [
                                        {
                                            "cadence": "MONTHLY",
                                            "pricing": {
                                                "type": "STATIC",
                                                "price_money": {"amount": 4900, "currency": "USD"}
                                            }
                                        }
                                    ]
                                }
                            }
                        ]
                    }
                }
            )
            created_variation = response.catalog_object.subscription_plan_data.subscription_plan_variations[0]
            return created_variation.id
        except ApiError as e:
            print(f"Square Catalog Create Error: {e.body}", file=sys.stderr)
            return None

    def start_subscription(self, customer_id, card_id, plan_variation_id, price_cents):
        """Create a real recurring subscription with a per-dealer price override. Returns subscription_id or None."""
        try:
            response = self.client.subscriptions.create(
                idempotency_key=str(uuid.uuid4()),
                location_id=self.location_id,
                customer_id=customer_id,
                card_id=card_id,
                plan_variation_id=plan_variation_id,
                price_override_money={"amount": price_cents, "currency": "USD"}
            )
            return response.subscription.id
        except ApiError as e:
            print(f"Square Start Subscription Error: {e.body}", file=sys.stderr)
            return None

    def update_subscription_price(self, subscription_id, new_price_cents):
        """Change the price of an existing live subscription. Returns True/False."""
        try:
            self.client.subscriptions.update(
                subscription_id,
                subscription={"price_override_money": {"amount": new_price_cents, "currency": "USD"}}
            )
            return True
        except ApiError as e:
            print(f"Square Update Subscription Price Error: {e.body}", file=sys.stderr)
            return False


def verify_webhook_signature(request_body, square_signature_header, notification_url):
    """
    Verify a Square webhook's HMAC-SHA256 signature per Square's documented
    algorithm: base64(HMAC-SHA256(signature_key, notification_url + body)).
    """
    signature_key = os.environ.get('SQUARE_WEBHOOK_SIGNATURE_KEY')
    if not signature_key or not square_signature_header:
        return False

    hmac_obj = hmac.new(
        signature_key.encode('utf-8'),
        (notification_url + request_body.decode('utf-8')).encode('utf-8'),
        hashlib.sha256
    )
    expected_signature = base64.b64encode(hmac_obj.digest()).decode('utf-8')
    return hmac.compare_digest(expected_signature, square_signature_header)
