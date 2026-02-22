from square.client import Client
import os
import uuid
import sys

class SquarePaymentService:
    def __init__(self):
        # Explicit print to stdout for debugging
        print("DEBUG: Initializing SquarePaymentService...", file=sys.stdout)
        
        self.access_token = os.environ.get('SQUARE_ACCESS_TOKEN')
        self.environment = os.environ.get('SQUARE_ENVIRONMENT', 'sandbox')
        
        print(f"DEBUG: Square Env: {self.environment}", file=sys.stdout)
        
        if not self.access_token:
            print("CRITICAL WARNING: SQUARE_ACCESS_TOKEN is missing in environment!", file=sys.stderr)
            
        try:
            self.client = Client(
                access_token=self.access_token,
                environment=self.environment
            )
            # self.client = None
            print("DEBUG: Square Client initialized successfully.", file=sys.stdout)
        except Exception as e:
            print(f"CRITICAL ERROR initializing Square Client: {e}", file=sys.stderr)
            raise e
        
    def create_customer(self, email, name):
        """Create a Customer in Square"""
        print(f"DEBUG: Creating customer {email}...", file=sys.stdout)
        try:
            body = {
                "given_name": name.split(" ")[0],
                "family_name": " ".join(name.split(" ")[1:]) if " " in name else "",
                "email_address": email,
                "reference_id": f"pes-{uuid.uuid4().hex[:8]}"
            }
            result = self.client.customers.create_customer(body)
            if result.is_success():
                return result.body['customer']['id']
            else:
                print(f"Square Create Customer Error: {result.errors}", file=sys.stderr)
                return None
        except Exception as e:
            print(f"Square Exception (create_customer): {e}", file=sys.stderr)
            return None

    def charge_card(self, source_id, amount_cents, customer_id, note="Charge"):
        """Process a payment"""
        print(f"DEBUG: Charging card for {amount_cents} cents...", file=sys.stdout)
        try:
            body = {
                "source_id": source_id,
                "idempotency_key": str(uuid.uuid4()),
                "amount_money": {
                    "amount": amount_cents,
                    "currency": "USD"
                },
                "customer_id": customer_id,
                "note": note
            }
            result = self.client.payments.create_payment(body)
            
            if result.is_success():
                return True, result.body['payment']['id']
            else:
                print(f"Square Charge Error: {result.errors}", file=sys.stderr)
                return False, result.errors[0]['detail'] if result.errors else "Unknown Error"
                
        except Exception as e:
            print(f"Square Exception (charge_card): {e}", file=sys.stderr)
            return False, str(e)

    def store_card(self, customer_id, card_nonce):
        """Store valid card on file (create card)"""
        try:
            body = {
                "idempotency_key": str(uuid.uuid4()),
                "source_id": card_nonce,
                "card": {
                    "customer_id": customer_id
                }
            }
            # Note: create_card might be under 'cards' API now
            result = self.client.cards.create_card(body)
            if result.is_success():
                return result.body['card']['id']
            else:
                print(f"Square Store Card Error: {result.errors}", file=sys.stderr)
                return None
        except Exception as e:
            print(f"Square Exception (store_card): {e}", file=sys.stderr)
            return None

    def create_subscription_plan(self, name, amount_cents):
        """Create a subscription plan (Catalog Object)"""
        # Simplified: Check if exists first? For now just return None to skip complexity
        # Real implementation needs Catalog API
        print("Skipping detailed Subscription Plan creation for MVP.", file=sys.stdout)
        return "plan_placeholder"

    def start_subscription(self, customer_id, card_id, plan_id):
        """Start a subscription"""
        # Simplified placeholder
        return "sub_placeholder"
