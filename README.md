# Welcome to BrigArt

The purpose of this project is to create a professional platform for the artist, Brig, to sell his prints.

## Features (Coming Soon)
- Automated product updates using the Stripe API that change the image and prices based off of changes in the NocoDB database.
- Webhook to trigger the check to see if there are products that need updating when someone uses the API.

## Requirements
- Git
- Python virtual environment
- NocoDB Instance with PostgreSQL

## How to Set Up Local Environment

1. **Clone the repository:**

   ```bash
   git clone https://github.com/Art-Ecommerce-LLC/brigart.git


* Open terminal and navigate to the main directory of the repo
* Download a python virtual enviornment by running python -m venv .venv
* Activate the virtual enviornmnet with source .venv/bin/activate for Mac OS/Linux and .
* .venv/scripts/activate.bat for Windows
* While in the main directory, make sure (.venv) pops up to the left, bottomost line of text in the terminal
* Run pip install -r requirements.txt
* Now that dependencies are download and you are in the main directory. Run uvicorn src.app:app --reload to run your instance



