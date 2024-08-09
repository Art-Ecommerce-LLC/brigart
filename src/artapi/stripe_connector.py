from src.artapi.config import STRIPE_SECRET_KEY
from src.artapi.logger import logger
import stripe
import tempfile
import requests
import os
from typing import List
from PIL import Image
from io import BytesIO

class StripeAPI:
    def __init__(self):
        stripe.api_key = STRIPE_SECRET_KEY
        self.resolution_factor = 0.8

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

    def create_file(self, image_url: str) -> stripe.File:
        try:
            # Download the image from the URL
            response = requests.get(image_url)
            response.raise_for_status()

            # Convert image bytes to processed image bytes
            image_data = self.process_image(response.content)

            # Create a temporary file
            with tempfile.NamedTemporaryFile(delete=False, mode='wb') as temp_file:
                temp_file.write(image_data)
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

    def process_image(self, image_data: bytes) -> bytes:
        """
        Process image data and return the processed image bytes
        
        Arguments:
            image_data (bytes): The image data to process
        
        Returns:
            bytes: The processed image data
        
        Raises:
            Exception: If there is an error processing the image data
        """
        try:
            with Image.open(BytesIO(image_data)) as img:
                if img.mode == 'RGBA':
                    img = img.convert('RGB')
                width, height = img.size
                new_size = (int(width * self.resolution_factor), int(height * self.resolution_factor))
                resized_img = img.resize(new_size, Image.ANTIALIAS)
                buffer = BytesIO()
                resized_img.save(buffer, format="JPEG")
                processed_img_data = buffer.getvalue()
            logger.info("Processed image data")
            return processed_img_data
        except Exception as e:
            logger.error(f"Error processing image data: {e}")
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
        """
            Syncs the products in the stripe account with the products in the database

            Arguments:
                img_quant_list (list): A list of dictionaries containing the product title, price and quantity
                path_list (list): A list of image paths

            Returns:
                list: A list of dictionaries containing the product price and quantity
        """
        try:
            active_products = stripe.Product.list(active=True, limit=100).data
            active_product_titles = [product.name for product in active_products]
            active_product_ids = [product.id for product in active_products]
            line_items = []
            for each_product in img_quant_list:
                title = each_product['title']
                if title in active_product_titles:
                    product_index = active_product_titles.index(title)
                    product_id = active_product_ids[product_index]
                    if self.price_match(product_id, each_product['price']):
                        line_items.append({
                            "price":self.retrieve_product(product_id).default_price,
                            "quantity":each_product['quantity']}
                            )
                    else:
                        default_price = self.check_price_existence(product_id, each_product['price'], each_product['quantity'])
                        line_items.append({
                            "price":default_price,
                            "quantity":each_product['quantity']}
                            )
                else:
                    title = each_product['title']
                    price = each_product['price']
                    quantity = each_product['quantity']
                    image_url = path_list[img_quant_list.index(each_product)]
                    file_link = self.upload_image_to_stripe(image_url)
                    price_amount = (int(price) // int(quantity))
                    new_product = self.create_product(title, price_amount, file_link.url)
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
        try:
            product = self.retrieve_product(product_id)
            default_price = product.default_price
            unit_amount = self.retrieve_price(default_price).unit_amount
            # Retrive unity amount from stripe product price
            if unit_amount != price:
                return False
            return True
        except Exception as e:
            logger.error(f"Error matching price for product ID {product_id}: {e}")
            raise
    
    def check_price_existence(self, product_id: str, price: int, quantity: int) -> stripe.Price:
        try:
            active_price_list = stripe.Price.list(product=product_id, limit=100).data
            inactive_price_list = stripe.Price.list(product=product_id,limit= 100, active=False).data
            price_list = active_price_list + inactive_price_list
            price_list = [price.unit_amount for price in price_list]
            unit_price_amount = (int(price) // int(quantity)) * 100
            if unit_price_amount not in price_list:
                price_amount = (int(price) // int(quantity))
                new_price = self.create_price(product_id, price_amount)
                updated_product = stripe.Product.modify(product_id, default_price=new_price.id)
                return updated_product.default_price
            else:
                price_id = stripe.Price.list(product=product_id, limit=100).data[price_list.index(unit_price_amount)].id
                updated_product = stripe.Product.modify(product_id, default_price=price_id)
                return updated_product.default_price
        except Exception as e:
            logger.error(f"Error checking price existence: {e}")
            raise

def get_stripe_api():
    return StripeAPI()