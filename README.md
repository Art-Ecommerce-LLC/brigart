# Welcome to BrigArt
The purpose of this project is to create a professional platform for the artist, Brig, to sell his prints.

## User Stories 
- A user wants to buy art from the artist's website and have it shipped to their home
- A user wants to browse the collection of art from an artist
- A user wants to check out the artist's social media (Coming soon!)
- A user wants to checkout the parent company's social media (Coming soon!)

## Current Features
- The ability to automatically update prices, titles, and images on an HTML template without always writing new HTML code based off the data in the database
- Selected images have their resolution reduced. Then they are turned into Data URI's which are sent to the HTML through the template context. They are recieved on the frontend in a background-image: url(...) to prevent users or browsers from easily downloading them.
- Caching to optimize the retreival of large payloads that are pulled from a database
- Automated product updates using the Stripe API that change the product data such as images, prices, and titles based off the database records
- Error system that automatically pings the developer on telegram and over email the error code while also storing a ticket in the database
- No need for api get operations with NocoDB, since it is pulling from PostreSQL
- Database filter searching

## Features in the works
- Backend migration from Render -> AWS with CI/CD
- Database migration from Railway -> AWS
- Store backend and database containers on Kubernetes Pod
- Migration of Pillow dependency to something more secure for artist portal creation
- Create portal where artist can set up there own website instances with ease, connect there accounts with Stripe Connect
- Add feature to portal that allows artists to easily change art, prices and titles on there instance
- Implement cookie payload caching similar to artwork caching to optimize speed
- Make the only API Connection to Noco the the creation and upload of images, everything else make PostgreSQL create, read, update, and delete, 
- Sync img table to a datauri table to save money and load time, use SQL relationships

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

   **Mac OS/Linux**
   ```bash
   python3 -m venv .venv
   ```

   **Windows 11**
   ```bash
   python -m venv .venv
   ```

4. **Activate the virtual enviornmnet with**

   **Mac OS/Linux**
   ```bash
   source .venv/bin/activate
   ```

   **Windows 11**
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



