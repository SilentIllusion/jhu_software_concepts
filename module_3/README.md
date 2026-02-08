# Module 3

This module contains a Flask app and supporting scripts to scrape, clean, load, and analyze Grad Cafe admission results stored in a PostgreSQL database.

## Project Layout
- `app/run.py`: Flask application entry point.
- `app/query_data.py`: Centralized SQL queries used by the app.
- `app/scripts/`: Scrape and cleaning utilities.
- `requirements.txt`: Python dependencies for this module.
- `load_data.py`: One-time load script to load the initial data from a JSON file.

## Setup
1. Create and activate a virtual environment. (optional)
2. Install dependencies:

```bash
pip install -r module_3/requirements.txt
```

## Database
The app expects a PostgreSQL database named `grad_cafe` with an `admission_results` table matching the columns used in `app/query_data.py`.

Connection settings are currently in `app/run.py`:
- `dbname`: `grad_cafe`
- `user`: `postgres`
- `password`: set in code

## Run the App
From the repo root:

```bash
python module_3/app/run.py
```

Then visit `http://localhost:8080`.

## Notes
- All SQL queries are centralized in `app/query_data.py`.
- Scraping is triggered from the UI via the "Pull Data" action.
