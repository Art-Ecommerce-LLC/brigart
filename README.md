# Welcome to BrigArt

The purpose of this project is to create a professional platform for the artist, Brig, to sell his prints.

## Current Features
- A singleton database connection to a databse that holds the images, titles, and prices of artwork.
- The ability to automatically update prices, titles, and images on an HTML template without always writing new HTML code based off the data in the database

## Features (Coming Soon)
- Automated product updates using the Stripe API that change the image and prices based on changes in the NocoDB database.
- Webhook to trigger the check to see if there are products that need updating when someone uses the API.

## Requirements
- Git
- Python virtual environment
- NocoDB Instance with PostgreSQL
- Python 3.9.13
- Stripe API

## .env file secrets

1. **Make sure the .env file is in the root directory. You need the secrets to be filled out. Find the necessary enviornment varibles in the src/artapi/config.py and src/artapi/noco_config.py**


## How to Set Up Local Environment

1. **Clone the repository:**

   ```bash
   git clone https://github.com/Art-Ecommerce-LLC/brigart.git
   ```

2. **Open terminal and navigate to the root directory of the repo**

   ```bash
   cd brigart
   ```

3. **Download a python virtual enviornment by running**

   ```bash
   python -m venv .venv
   ```

4. **(Mac OS/Linux) Activate the virtual enviornmnet with**
   ```bash
   source .venv/bin/activate
   ```
   **(Windows 11/10)**
   ```bash
   .venv/scripts/activate
   ```
5. **While in the root directory, make sure (.venv) pops up to the left, bottomost line of text in the terminal. Then run**

   ```bash
   pip install -r requirements.txt
   ```

6. **Now that dependencies are downloaded and you are in the root directory. Run**
   ```
   uvicorn src.app:app --reload
   ```



