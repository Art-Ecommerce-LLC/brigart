from src.artapi.config import STRIPE_SECRET_KEY
from src.artapi.logger import logger
import stripe

class StripeAPI:
    def __init__(self):
        stripe.api_key = STRIPE_SECRET_KEY

    def update_price(self, price_id: str, new_price: int):
        try:
            stripe.Price.modify(price_id, unit_amount=new_price)
            logger.info(f"Updated price ID {price_id} to new price {new_price}")
        except Exception as e:
            logger.error(f"Error updating price ID {price_id}: {e}")
            raise

    def create_price(self, product_id: str, new_price: int):
        try:
            price = stripe.Price.create(
                product=product_id,
                unit_amount=new_price,
                currency='usd'
            )
            logger.info(f"Created new price {new_price} for product ID {product_id}")
            return price
        except Exception as e:
            logger.error(f"Error creating new price for product ID {product_id}: {e}")
            raise

    def archive_price(self, price_id: str):
        try:
            stripe.Price.modify(price_id, active=False)
            logger.info(f"Archived price ID {price_id}")
        except Exception as e:
            logger.error(f"Error archiving price ID {price_id}: {e}")
            raise

    def unarchive_price(self, price_id: str):
        try:
            stripe.Price.modify(price_id, active=True)
            logger.info(f"Unarchived price ID {price_id}")
        except Exception as e:
            logger.error(f"Error unarchiving price ID {price_id}: {e}")
            raise

    def list_prices(self):
        return stripe.Price.list()

    def list_products(self):
        return stripe.Product.list()

    def retrieve_product(self, product_id: str):
        return stripe.Product.retrieve(product_id)

    def retrieve_price(self, price_id: str):
        return stripe.Price.retrieve(price_id)

    def create_file(self, file_path: str):
        try:
            with open(file_path, "rb") as fp:
                file = stripe.File.create(purpose='product_image', file=fp)
            logger.info(f"Uploaded file from {file_path}")
            return file
        except Exception as e:
            logger.error(f"Error uploading file from {file_path}: {e}")
            raise

    def create_file_link(self, file_id: str):
        try:
            file_link = stripe.FileLink.create(file=file_id)
            logger.info(f"Created file link for file ID {file_id}")
            return file_link
        except Exception as e:
            logger.error(f"Error creating file link for file ID {file_id}: {e}")
            raise

    def upload_image_to_stripe(self, file_path: str) -> str:
        try:
            stripe_file = self.create_file(file_path)
            file_link = self.create_file_link(stripe_file.id)
            logger.info(f"Uploaded image to Stripe: File ID {stripe_file.id}, File Link {file_link.url}")
            return file_link.url
        except Exception as e:
            logger.error(f"Error uploading image to Stripe from {file_path}: {e}")
            raise

    def create_or_update_product(self, title: str, price: int, image_url: str) -> None:
        try:
            products = self.list_products()
            product = next((p for p in products.data if p.name == title), None)

            if product:
                self.update_product(product.id, price, image_url)
            else:
                self.create_product(title, price, image_url)
        except Exception as e:
            logger.error(f"Error creating or updating product {title}: {e}")
            raise

    def update_product(self, product_id: str, price: int, image_url: str) -> None:
        try:
            self.update_product_image(product_id, image_url)
            self.update_product_price(product_id, price)
        except Exception as e:
            logger.error(f"Error updating product ID {product_id}: {e}")
            raise

    def update_product_image(self, product_id: str, image_url: str) -> None:
        try:
            existing_images = self.retrieve_product(product_id).images
            if existing_images != [image_url]:
                stripe.Product.modify(product_id, images=[image_url])
                logger.info(f"Updated image for product ID {product_id}")
        except Exception as e:
            logger.error(f"Error updating image for product ID {product_id}: {e}")
            raise

    def update_product_price(self, product_id: str, price: int) -> None:
        try:
            product = self.retrieve_product(product_id)
            existing_price_id = product.default_price
            existing_price = self.retrieve_price(existing_price_id)
            existing_price_amount = existing_price.unit_amount // 100

            if existing_price_amount != price:
                prices = self.list_prices()
                matching_inactive_price = next((p for p in prices.data if p.unit_amount == price * 100 and not p.active), None)

                if matching_inactive_price:
                    self.unarchive_price(matching_inactive_price.id)
                    new_price_id = matching_inactive_price.id
                    logger.info(f"Reactivated existing price for product ID {product_id}")
                else:
                    new_price = self.create_price(product_id, price)
                    new_price_id = new_price.id
                    logger.info(f"Created new price for product ID {product_id}")

                stripe.Product.modify(product_id, default_price=new_price_id)
                self.archive_price(existing_price_id)
                logger.info(f"Updated price for product ID {product_id} and archived old price")
        except Exception as e:
            logger.error(f"Error updating price for product ID {product_id}: {e}")
            raise

    def create_product(self, title: str, price: int, image_url: str) -> None:
        try:
            new_product = stripe.Product.create(
                name=title,
                tax_code="txcd_99999999",
                default_price_data={
                    'currency': 'usd',
                    'unit_amount': price * 100,
                    'tax_behavior': 'exclusive'
                },
                images=[image_url],
                shippable=True,
            )
            logger.info(f"Created new product {title}, product ID {new_product.id}")
        except Exception as e:
            logger.error(f"Error creating product {title}: {e}")
            raise
