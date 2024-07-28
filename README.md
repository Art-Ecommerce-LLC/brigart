# Welcome to BrigArt

The purpose of this project is to create a professional platform for the artist, Brig, to sell his prints.

## Features (Coming Soon)
- Automated product updates using the Stripe API that change the image and prices based on changes in the NocoDB database.
- Webhook to trigger the check to see if there are products that need updating when someone uses the API.

## Requirements
- Git
- Python virtual environment
- NocoDB Instance with PostgreSQL
- Python 3.9.13

## How to Set Up Local Environment

1. **Clone the repository:**

   ```bash
   git clone https://github.com/Art-Ecommerce-LLC/brigart.git
   ```

2. **Open terminal and navigate to the main directory of the repo**

3. **Download a python virtual enviornment by running**

   ```bash
   python -m venv .venv**
   ```

4. **(Mac OS) Activate the virtual enviornmnet with source**
   ```bash
   .venv/bin/activate
   ```
   **(Windows 11/10)**
   ```bash
   .venv/scripts/activate.bat 
   ```
5. **While in the main directory, make sure (.venv) pops up to the left, bottomost line of text in the terminal. Then run**

  ```bash
   pip install -r requirements.txt
  ```

6. **Now that dependencies are download and you are in the main directory. Run**
   ```
    uvicorn src.app:app --reload
   ```



