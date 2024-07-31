from src.artapi.config import STRIPE_SECRET_KEY
from src.artapi.logger import logger
import stripe
import tempfile
import requests
import os
from typing import List

class StripeAPI:
    def __init__(self):
        stripe.api_key = STRIPE_SECRET_KEY

    def update_price(self, price_id: str, new_price: int) -> None:
        try:
            stripe.Price.modify(price_id, unit_amount=new_price)
            logger.info(f"Updated price ID {price_id} to new price {new_price}")
        except Exception as e:
            logger.error(f"Error updating price ID {price_id}: {e}")
            raise

    def create_price(self, product_id: str, new_price: int) -> stripe.Price:
        try:
            price = stripe.Price.create(
                product=product_id,
                unit_amount=int(new_price) * 100,
                currency='usd'
            )
            logger.info(f"Created new price {new_price} for product ID {product_id}")
            return price
        except Exception as e:
            logger.error(f"Error creating new price for product ID {product_id}: {e}")
            raise

    def archive_price(self, price_id: str) -> None:
        try:
            stripe.Price.modify(price_id, active=False)
            logger.info(f"Archived price ID {price_id}")
        except Exception as e:
            logger.error(f"Error archiving price ID {price_id}: {e}")
            raise

    def unarchive_price(self, price_id: str) -> None:
        try:
            stripe.Price.modify(price_id, active=True)
            logger.info(f"Unarchived price ID {price_id}")
        except Exception as e:
            logger.error(f"Error unarchiving price ID {price_id}: {e}")
            raise

    def archive_product(self, product_id: str) -> None:
        try:
            stripe.Product.modify(product_id, active=False)
            logger.info(f"Archived product ID {product_id}")
        except Exception as e:
            logger.error(f"Error archiving product ID {product_id}: {e}")
            raise

    def unarchive_product(self, product_id: str) -> None:
        try:
            stripe.Product.modify(product_id, active=True)
            logger.info(f"Unarchived product ID {product_id}")
        except Exception as e:
            logger.error(f"Error unarchiving product ID {product_id}: {e}")
            raise

    def list_products(self) -> stripe.Product:
        return stripe.Product.list()

    def retrieve_product(self, product_id: str):
        return stripe.Product.retrieve(product_id)

    def retrieve_price(self, price_id: str):
        return stripe.Price.retrieve(price_id)

    def create_file(self, image_url: str) -> stripe.File:
        try:
            # Download the image from the URL
            response = requests.get(image_url)
            response.raise_for_status()

            # Create a temporary file
            with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                temp_file.write(response.content)
                temp_file_path = temp_file.name

            # Open the temporary file and upload it to Stripe
            with open(temp_file_path, "rb") as fp:
                file = stripe.File.create(purpose='product_image', file=fp)

            logger.info(f"Uploaded file from {temp_file_path}")

            # Clean up the temporary file
            os.remove(temp_file_path)

            return file
        except Exception as e:
            logger.error(f"Error uploading file from {image_url}: {e}")
            raise

    def create_file_link(self, file_id: str) -> stripe.FileLink:
        try:
            file_link = stripe.FileLink.create(file=file_id)
            logger.info(f"Created file link for file ID {file_id}")
            return file_link
        except Exception as e:
            logger.error(f"Error creating file link for file ID {file_id}: {e}")
            raise

    def upload_image_to_stripe(self, file_url : str) -> stripe.FileLink:
        try:
            file = self.create_file(file_url)
            file_link = self.create_file_link(file.id)
            logger.info(f"Uploaded image to Stripe: File ID {file.id}, File Link {file_link.url}")
            return file_link
        except Exception as e:
            logger.error(f"Error uploading image to Stripe from {file_url}: {e}")
            raise

    # Working on updating functions
    # def update_product(self, product_id: str, price: int, image_url: str) -> None:
    #     try:
    #         self.update_product_image(product_id, image_url)
    #         self.update_product_price(product_id, price)
    #     except Exception as e:
    #         logger.error(f"Error updating product ID {product_id}: {e}")
    #         raise

    def update_product_image(self, product_id: str, image_url: str) -> None:
        try:
            existing_images = self.retrieve_product(product_id).images
            if existing_images != [image_url]:
                stripe.Product.modify(product_id, images=[image_url])
                logger.info(f"Updated image for product ID {product_id}")
        except Exception as e:
            logger.error(f"Error updating image for product ID {product_id}: {e}")
            raise

    def create_product(self, title: str, price: int, file_link: str) -> stripe.Product:
        try:
            new_product = stripe.Product.create(
                name=title,
                tax_code="txcd_99999999",
                default_price_data={
                    'currency': 'usd',
                    'unit_amount': int(price) * 100,
                    'tax_behavior': 'exclusive'
                },
                images=[file_link],
                shippable=True,
            )
            logger.info(f"Created new product {title}, product ID {new_product.id}")
            return new_product
        except Exception as e:
            logger.error(f"Error creating product {title}: {e}")
            raise

    def sync_products(self, img_quant_list : list, path_list : list) -> list:
        try:
            # Search the active product list for to see if the product already exists
            active_products = stripe.Product.list(active=True, limit=100).data
            active_product_titles = [product.name for product in active_products]
            active_product_ids = [product.id for product in active_products]
            line_items = []
            for each_product in img_quant_list:
                title = each_product['title']
                if title in active_product_titles:
                    # If True, then check that the price is correct on the product
                    product_index = active_product_titles.index(title)
                    product_id = active_product_ids[product_index]
                    if self.price_match(product_id, each_product['price']):
                        # The price matches and the product exists,
                        # Return the default price of the object and move on
                        # return self.retrieve_product(product_id).default_price
                        line_items.append({
                            "price":self.retrieve_product(product_id).default_price,
                            "quantity":each_product['quantity']}
                            )
                    else:
                        # The price does not match the default price, check if there is a price that matches

                        default_price = self.check_price_existence(product_id, each_product['price'], each_product['quantity'])

                        # return default_price
                        line_items.append({
                            "price":default_price,
                            "quantity":each_product['quantity']}
                            )
                else:
                    # If False, then create a new product, with the price, and the title,
                    # Get the image url by indexing the cached artwork object for the path
                    title = each_product['title']
                    price = each_product['price']
                    quantity = each_product['quantity']
                    image_url = path_list[img_quant_list.index(each_product)]

                    # Create file link and upload image to stripe
                    file_link = self.upload_image_to_stripe(image_url)
                    price_amount = (int(price) // int(quantity))
                    new_product = self.create_product(title, price_amount, file_link.url)

                    # return new_product.default_price
                    line_items.append({
                        "price":new_product.default_price,
                        "quantity":each_product['quantity']}
                        )
                    
            return line_items
                
        except Exception as e:
            logger.error(f"Error syncing products: {e}")
            raise
    
    def retrieve_price(self, price_id: str) -> stripe.Price:
        return stripe.Price.retrieve(price_id)

    def price_match(self, product_id: str, price: int) -> bool:
        product = self.retrieve_product(product_id)
        default_price = product.default_price
        unit_amount = self.retrieve_price(default_price).unit_amount
        # Retrive unity amount from stripe product price
        if unit_amount != price:
            return False
        return True
    
    def check_price_existence(self, product_id: str, price: int, quantity: int) -> stripe.Price:
        # Check if the price exists, lists all prices for product id
        active_price_list = stripe.Price.list(product=product_id, limit=100).data
        inactive_price_list = stripe.Price.list(product=product_id,limit= 100, active=False).data# Check both active and inactive prices
        price_list = active_price_list + inactive_price_list
        price_list = [price.unit_amount for price in price_list]
        unit_price_amount = (int(price) // int(quantity)) * 100
        if unit_price_amount not in price_list:
            price_amount = (int(price) // int(quantity))
            new_price = self.create_price(product_id, price_amount)
            # Make the new price the default price
            updated_product = stripe.Product.modify(product_id, default_price=new_price.id)
            return updated_product.default_price
        else:
            # Grab the price id from the price list of the product
            price_id = stripe.Price.list(product=product_id, limit=100).data[price_list.index(unit_price_amount)].id
            updated_product = stripe.Product.modify(product_id, default_price=price_id)
            return updated_product.default_price

def get_stripe_api():
    return StripeAPI()