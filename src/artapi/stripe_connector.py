from src.artapi.config import STRIPE_SECRET_KEY
import stripe

class StripeAPI:
    def __init__(self):
        stripe.api_key = STRIPE_SECRET_KEY

    def update_price(self, price_id: str, new_price: int):
        stripe.Price.modify(
            price_id,
            unit_amount=new_price,
        )
    
    def create_price(self, product_id: str, new_price: int):
        stripe.Price.create(
            product=product_id,
            unit_amount=new_price,
            currency='usd',
        )
    
    def archive_price(self, price_id: str):
        stripe.Price.modify(
            price_id,
            active=False,
        )
    
    def unarchive_price(self, price_id: str):
        stripe.Price.modify(
            price_id,
            active=True,
        )

    def list_prices(self):
        return stripe.Price.list()
    
    def list_products(self):
        return stripe.Product.list()
