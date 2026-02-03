# Module 2: Grad Cafe Web Scraper

Graduate school applicant admission data scraper for [The Grad Cafe](https://www.thegradcafe.com/survey/). Gathers program, university, decision status, GRE/GPA metrics, and comments from publicly submitted survey entries.

## Requirements

- Python 3.10+
- urllib3
- beautifulsoup4

## Setup

```bash
pip install -r requirements.txt
```

## Usage

### 1. Scrape Data

```bash
python scrape.py
```

Scrapes at least 30,000 applicant entries from Grad Cafe survey pages and saves to `applicant_data.json`. Uses urllib3 for HTTP requests and BeautifulSoup for HTML parsing.

### 2. Clean Data

```bash
python clean.py
```

Loads `applicant_data.json`, removes remnant HTML, normalizes values, and saves cleaned data. Unavailable fields are set to `None`.

### 3. LLM Standardization (Program/University Names)

Download the provided `llm_hosting` zip and add it as a subfolder:

```
module_2/
  llm_hosting/    # from assignment zip
  scrape.py
  clean.py
  ...
```

Then:

```bash
cd llm_hosting
pip install -r requirements.txt
python app.py --file "../applicant_data.json" > ../applicant_data_cleaned.json
```

This adds `llm-generated-program` and `llm-generated-university` columns for consistent analysis.

## Data Fields

| Field | Description |
|-------|-------------|
| program | Program and university combined (e.g., "Computer Science, MIT") |
| comments | Applicant notes (if available) |
| date_added | Date added to Grad Cafe |
| url | Link to applicant entry |
| applicant_status | Accepted, Rejected, Interview, Wait listed |
| acceptance_date | Date if accepted |
| rejection_date | Date if rejected |
| semester_year | Start term (e.g., Fall 2026) |
| international_american | International, American, or Other |
| gre_score | GRE total (if available) |
| gre_v_score | GRE Verbal (if available) |
| degree_type | PhD, Masters, MBA, etc. |
| gpa | GPA (if available) |
| gre_aw | GRE Analytical Writing (if available) |

## robots.txt Compliance

Scraping complies with [The Grad Cafe robots.txt](https://www.thegradcafe.com/robots.txt):

- `User-agent: *` with `Allow: /` permits general crawling
- `Content-Signal: search=yes` allows content collection for search
- No disallow rules for the `/survey/` or `/result/` paths used by this scraper

## Project Structure

```
module_2/
  scrape.py           # Scraping logic (urllib3, BeautifulSoup)
  clean.py            # Data cleaning
  applicant_data.json # Output (30,000+ entries)
  llm_extended_application_data.json
  application_data.json.jsonl
  requirements.txt
  README.md
  screenshot.jpg      # robots.txt verification
  llm_hosting/        # LLM standardizer (from assignment zip)
```

## Repository

Part of `jhu_software_concepts` in folder `module_2`.
