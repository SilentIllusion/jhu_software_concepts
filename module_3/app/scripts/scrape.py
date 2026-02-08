"""
Grad Cafe Web Scraper - Module 2 Assignment

Scrapes applicant admission data from The Grad Cafe survey pages.
Uses urllib3 for HTTP requests and BeautifulSoup for HTML parsing.

Notes:
- This module focuses on scraping and basic parsing.
- Data cleaning and persistence should live in clean.py (imported below).
"""

import json
import re
from datetime import date, datetime
from typing import Any, Dict, List, Optional, Tuple

from bs4 import BeautifulSoup
from urllib3 import PoolManager
from urllib3.util.retry import Retry

try:
    from .clean import clean_data, save_data
except ImportError:
    from clean import clean_data, save_data


# Base URL for Grad Cafe survey
BASE_URL = "https://www.thegradcafe.com"
SURVEY_URL = f"{BASE_URL}/survey/"


def _build_request_headers() -> Dict[str, str]:
    """
    Build headers for HTTP requests to mimic a normal browser.

    Returns:
        Dict[str, str]: A headers dictionary suitable for urllib3 requests.
    """
    return {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept": (
            "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
        ),
        "Accept-Language": "en-US,en;q=0.5",
    }


def _extract_gre_from_text(text: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """
    Extract GRE scores from comment/notes text using regex.

    Looks for patterns like:
      - GRE 170
      - GRE: 170
      - GRE V 163
      - GRE Verbal 163
      - GRE AW 4.0
      - AW 4.0
      - Analytical Writing 4.0 (partial support via AW pattern)

    Args:
        text (str): Input text from comments/notes.

    Returns:
        Tuple[Optional[str], Optional[str], Optional[str]]:
            (gre_total, gre_verbal, gre_aw) as strings, or None if not found.
    """
    if not text:
        return None, None, None

    gre_total: Optional[str] = None
    gre_verbal: Optional[str] = None
    gre_aw: Optional[str] = None

    # GRE total: "GRE 170" or "GRE: 170"
    gre_match = re.search(
        r"\bGRE\b\s*:?\s*(\d{2,3})\b",
        text,
        re.IGNORECASE,
    )
    if gre_match:
        gre_total = gre_match.group(1)

    # GRE verbal: "GRE V 163" or "GRE Verbal 163"
    gre_v_match = re.search(
        r"\bGRE\b\s*V(?:erbal)?\s*:?\s*(\d{2,3})\b",
        text,
        re.IGNORECASE,
    )
    if gre_v_match:
        gre_verbal = gre_v_match.group(1)

    # GRE analytical writing: "GRE AW 4.0" or "AW 4.0"
    gre_aw_match = re.search(
        r"\b(?:GRE\s*)?AW\b\s*:?\s*(\d\.?\d*)\b",
        text,
        re.IGNORECASE,
    )
    if gre_aw_match:
        gre_aw = gre_aw_match.group(1)

    return gre_total, gre_verbal, gre_aw


def _extract_gre_from_badge_text(
    text: str,
) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """
    Extract GRE fields from a badge/label text on the listing page.

    Badge examples (site-specific, best effort):
      - "GRE 320"
      - "GRE V 163"
      - "GRE AW 4.0"
      - "Verbal 163" (fallback)
      - "AW 4.0"
    """
    if not text:
        return None, None, None

    gre_total = None
    gre_verbal = None
    gre_aw = None

    # Normalize whitespace for easier matching.
    text = re.sub(r"\s+", " ", text).strip()

    # GRE total: "GRE 320" or "GRE: 320"
    total_match = re.search(r"\bGRE\b\s*:?\s*(\d{2,3})\b", text, re.IGNORECASE)
    if total_match:
        gre_total = total_match.group(1)

    # GRE verbal: "GRE V 163" / "GRE Verbal 163" / "Verbal 163"
    verbal_match = re.search(
        r"\b(?:GRE\s*)?V(?:erbal)?\b\s*:?\s*(\d{2,3})\b",
        text,
        re.IGNORECASE,
    )
    if verbal_match:
        gre_verbal = verbal_match.group(1)

    # GRE analytical writing: "GRE AW 4.0" / "AW 4.0"
    aw_match = re.search(
        r"\b(?:GRE\s*)?AW\b\s*:?\s*(\d\.?\d*)\b",
        text,
        re.IGNORECASE,
    )
    if aw_match:
        gre_aw = aw_match.group(1)

    return gre_total, gre_verbal, gre_aw


def _extract_gpa_from_text(text: str) -> Optional[float]:
    """
    Extract GPA from text like 'GPA 3.69' or 'GPA: 3.7'.

    Args:
        text (str): Input text that may contain a GPA.

    Returns:
        Optional[str]: The GPA string if found, otherwise None.
    """
    if not text:
        return None

    gpa_match = re.search(r"GPA\s*:?\s*(\d\.?\d*)", text, re.IGNORECASE)
    if not gpa_match:
        return None

    try:
        return float(gpa_match.group(1))
    except ValueError:
        return None


def _parse_decision_date(decision_text: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Parse decision text to extract status and date.

    Examples:
      - 'Accepted on 29 Jan' -> ('Accepted', '29 Jan')
      - 'Rejected on 7 Jun'  -> ('Rejected', '7 Jun')

    Args:
        decision_text (str): Decision text extracted from the row.

    Returns:
        Tuple[Optional[str], Optional[str]]:
            (status, date_str) where date_str is typically 'DD Mon'.
    """
    if not decision_text:
        return None, None

    text = decision_text.strip()

    # Determine status (best-effort, based on substring matching).
    if "Accepted" in text:
        status = "Accepted"
    elif "Rejected" in text:
        status = "Rejected"
    elif "Interview" in text:
        status = "Interview"
    elif "Wait listed" in text or "Waitlisted" in text:
        status = "Wait listed"
    else:
        status = None

    # Extract a decision date if present (e.g., "on 29 Jan").
    date_match = re.search(r"on\s+(\d{1,2}\s+\w+)", text, re.IGNORECASE)
    date_str = date_match.group(1) if date_match else None

    return status, date_str


def _parse_semester(text: str) -> Optional[str]:
    """
    Extract semester/year like 'Fall 2026' or 'Spring 2025'.

    Args:
        text (str): Badge text.

    Returns:
        Optional[str]: Normalized semester/year string, or None if not found.
    """
    if not text:
        return None

    match = re.search(r"(Fall|Spring)\s+(\d{4})", text, re.IGNORECASE)
    if match:
        return f"{match.group(1)} {match.group(2)}"

    return None


def _parse_student_type(text: str) -> Optional[str]:
    """
    Extract student type from badge text.

    Args:
        text (str): Badge text.

    Returns:
        Optional[str]: "International", "American", "Other", or None.
    """
    if not text:
        return None

    text_lower = text.strip().lower()
    if "international" in text_lower:
        return "International"
    if "american" in text_lower:
        return "American"
    if "other" in text_lower:
        return "Other"

    return None


def _parse_degree(text: str) -> Optional[str]:
    """
    Extract degree type: PhD, Masters, MBA, etc.

    Args:
        text (str): Program badge/subtitle text.

    Returns:
        Optional[str]: Degree type if detected, otherwise None.
    """
    if not text:
        return None

    degree_types = ["PhD", "Masters", "MBA", "MFA", "JD", "EdD", "PsyD", "Other"]
    text_clean = text.strip()

    for degree in degree_types:
        if degree.lower() in text_clean.lower():
            return degree

    return None


def _parse_listing_row(
    main_row: Any,
    detail_row: Optional[Any],
    comment_row: Optional[Any],
) -> Optional[Dict[str, Any]]:
    """
    Parse a single applicant entry from listing page table rows.

    The GradCafe listing layout commonly uses:
      - main_row: contains school, program, added date, decision, and a result link
      - detail_row: optional row (border-none) containing badges (semester, intl/us, gpa)
      - comment_row: optional row (border-none) containing comments/notes

    Args:
        main_row (Any): The primary <tr> row.
        detail_row (Optional[Any]): The detail/badge <tr> row (may be None).
        comment_row (Optional[Any]): The comments <tr> row (may be None).

    Returns:
        Optional[Dict[str, Any]]: Parsed entry dict, or None if row is not parseable.
    """
    entry: Dict[str, Any] = {
        "program": None,
        "comments": None,
        "date_added": None,
        "url": None,
        "applicant_status": None,
        "acceptance_date": None,
        "rejection_date": None,
        "semester_year": None,
        "international_american": None,
        "gre_score": None,
        "gre_v_score": None,
        "degree_type": None,
        "gpa": None,
        "gre_aw": None,
    }

    # Main row should contain multiple <td> cells. If fewer than expected, skip.
    tds = main_row.find_all("td")
    if len(tds) < 4:
        return None

    # University/school (typically in first column)
    school_div = tds[0].find("div", class_=re.compile(r"tw-font-medium"))
    university = school_div.get_text(strip=True) if school_div else ""

    # Program name and optional degree info (typically in second column)
    program_div = tds[1].find("div", class_=re.compile(r"tw-text-gray-900"))
    program_name = ""

    if program_div:
        spans = program_div.find_all("span")
        if spans:
            program_name = spans[0].get_text(strip=True)

            # Some rows include degree type in the second span.
            if len(spans) >= 2:
                entry["degree_type"] = _parse_degree(spans[1].get_text())

    # Combine program + university for downstream standardization compatibility.
    if program_name and university:
        entry["program"] = f"{program_name}, {university}"
    elif program_name:
        entry["program"] = program_name
    elif university:
        entry["program"] = university

    # Added-on date (often in third column)
    if len(tds) >= 3:
        added_text = tds[2].get_text(strip=True)
        if added_text and "comments" not in added_text.lower():
            entry["date_added"] = added_text

    # Decision/status (often in fourth column)
    decision_div = tds[3].find("div", class_=re.compile(r"tw-inline-flex"))
    if decision_div:
        decision_text = decision_div.get_text(strip=True)
        status, date_str = _parse_decision_date(decision_text)

        entry["applicant_status"] = status

        # Store date under the appropriate key when possible.
        if status == "Accepted":
            entry["acceptance_date"] = date_str
        elif status == "Rejected":
            entry["rejection_date"] = date_str

    # Result URL (look for link like /result/935454)
    link = main_row.find("a", href=re.compile(r"/result/\d+"))
    if link and link.get("href"):
        href = link["href"]
        entry["url"] = BASE_URL + href if href.startswith("/") else href

    # Detail row: badges (semester, international/american, GPA)
    if detail_row:
        badges = detail_row.find_all("div", class_=re.compile(r"tw-inline-flex"))
        for badge in badges:
            badge_text = badge.get_text(strip=True)
            if not badge_text:
                continue

            semester = _parse_semester(badge_text)
            if semester:
                entry["semester_year"] = semester
                continue

            student_type = _parse_student_type(badge_text)
            if student_type:
                entry["international_american"] = student_type
                continue

            gpa = _extract_gpa_from_text(badge_text)
            if gpa is not None:
                entry["gpa"] = gpa

            gre_total, gre_verbal, gre_aw = _extract_gre_from_badge_text(badge_text)
            if gre_total and not entry["gre_score"]:
                entry["gre_score"] = gre_total
            if gre_verbal and not entry["gre_v_score"]:
                entry["gre_v_score"] = gre_verbal
            if gre_aw and not entry["gre_aw"]:
                entry["gre_aw"] = gre_aw

    # Comment row: notes/comments; does not populate GRE anymore.
    if comment_row:
        p_tag = comment_row.find("p")
        if p_tag:
            comment_text = p_tag.get_text(strip=True)
            entry["comments"] = comment_text if comment_text else None

            # GPA may also appear in comments.
            if not entry["gpa"]:
                gpa_from_comment = _extract_gpa_from_text(comment_text)
                if gpa_from_comment is not None:
                    entry["gpa"] = gpa_from_comment

    # If GRE badges were not found, set default to 0.0 (as requested).
    if not entry["gre_score"]:
        entry["gre_score"] = 0.0
    if not entry["gre_v_score"]:
        entry["gre_v_score"] = 0.0
    if not entry["gre_aw"]:
        entry["gre_aw"] = 0.0

    return entry


def scrape_data(max_entries: int = 50000) -> List[Dict[str, Any]]:
    """
    Pull data from Grad Cafe survey pages.

    Paginates through results until max_entries is reached or no more rows exist.

    Args:
        max_entries (int): Maximum number of entries to scrape.

    Returns:
        List[Dict[str, Any]]: List of scraped applicant entry dictionaries.
    """
    http = PoolManager(
        retries=Retry(connect=3, read=2, backoff_factor=1),
        headers=_build_request_headers(),
    )

    all_entries: List[Dict[str, Any]] = []
    page = 1
    per_page = 100

    while len(all_entries) < max_entries:
        # Build paginated URL (page parameter omitted for page 1).
        if page == 1:
            url = f"{SURVEY_URL}?per_page={per_page}"
        else:
            url = f"{SURVEY_URL}?per_page={per_page}&page={page}"

        # Fetch page HTML.
        try:
            response = http.request("GET", url)
            if response.status != 200:
                print(f"Page {page}: HTTP {response.status}")
                break

            html = response.data.decode("utf-8", errors="replace")

        except Exception as exc:
            print(f"Error fetching page {page}: {exc}")
            break

        # Parse HTML for the results table body.
        soup = BeautifulSoup(html, "html.parser")
        tbody = soup.find("tbody", class_=re.compile(r"tw-divide-y"))
        if not tbody:
            print(f"Page {page}: No tbody found")
            break

        rows = tbody.find_all("tr")
        page_entries = 0

        # GradCafe uses a pattern of:
        #   main <tr> followed by 0-2 "tw-border-none" <tr> rows.
        i = 0
        while i < len(rows):
            row = rows[i]

            # Skip detail/comment rows until we hit a main row.
            if "tw-border-none" in (row.get("class") or []):
                i += 1
                continue

            main_row = row
            detail_row = None
            comment_row = None

            # Next row may be detail row
            if i + 1 < len(rows) and "tw-border-none" in (rows[i + 1].get("class") or []):
                detail_row = rows[i + 1]
                i += 1

            # Next row may be comment row
            if i + 1 < len(rows) and "tw-border-none" in (rows[i + 1].get("class") or []):
                comment_row = rows[i + 1]
                i += 1

            entry = _parse_listing_row(main_row, detail_row, comment_row)

            # Only keep entries that include a result URL.
            if entry and entry.get("url"):
                all_entries.append(entry)
                page_entries += 1

                if len(all_entries) >= max_entries:
                    break

            i += 1

        if page_entries == 0:
            print(f"Page {page}: No new entries")
            break

        print(f"Page {page}: {page_entries} entries (total: {len(all_entries)})")

        if len(all_entries) >= max_entries:
            break

        page += 1

    # Persist scraped output using clean.py helper (preferred).
    save_data(all_entries)

    return all_entries


def scrape_new_data(
    existing_urls,
    max_entries: int = 5000,
    max_pages: int = 50,
    latest_date: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Scrape only new entries (by URL) and stop when a page yields no new results.

    Args:
        existing_urls: set of URLs already in the database
        max_entries: cap on new entries to return
        max_pages: cap on pages to scan

    Returns:
        List of new entry dicts
    """
    http = PoolManager(
        retries=Retry(connect=3, read=2, backoff_factor=1),
        headers=_build_request_headers(),
    )

    latest_dt = None
    if latest_date:
        latest_dt = _parse_added_date(latest_date)

    all_entries: List[Dict[str, Any]] = []
    page = 1
    per_page = 100

    while len(all_entries) < max_entries and page <= max_pages:
        if page == 1:
            url = f"{SURVEY_URL}?per_page={per_page}"
        else:
            url = f"{SURVEY_URL}?per_page={per_page}&page={page}"

        try:
            response = http.request("GET", url)
            if response.status != 200:
                print(f"Page {page}: HTTP {response.status}")
                break

            html = response.data.decode("utf-8", errors="replace")

        except Exception as exc:
            print(f"Error fetching page {page}: {exc}")
            break

        soup = BeautifulSoup(html, "html.parser")
        tbody = soup.find("tbody", class_=re.compile(r"tw-divide-y"))
        if not tbody:
            print(f"Page {page}: No tbody found")
            break

        rows = tbody.find_all("tr")
        page_entries = 0
        page_new = 0

        i = 0
        while i < len(rows):
            row = rows[i]

            if "tw-border-none" in (row.get("class") or []):
                i += 1
                continue

            main_row = row
            detail_row = None
            comment_row = None

            if i + 1 < len(rows) and "tw-border-none" in (rows[i + 1].get("class") or []):
                detail_row = rows[i + 1]
                i += 1

            if i + 1 < len(rows) and "tw-border-none" in (rows[i + 1].get("class") or []):
                comment_row = rows[i + 1]
                i += 1

            entry = _parse_listing_row(main_row, detail_row, comment_row)

            if entry and entry.get("url"):
                page_entries += 1
                if entry["url"] not in existing_urls:
                    if latest_dt:
                        entry_dt = _parse_added_date(entry.get("date_added"))
                        if entry_dt and entry_dt <= latest_dt:
                            i += 1
                            continue
                    all_entries.append(entry)
                    page_new += 1

                    if len(all_entries) >= max_entries:
                        break

            i += 1

        if page_entries == 0:
            print(f"Page {page}: No entries")
            break

        print(f"Page {page}: {page_new} new entries (total: {len(all_entries)})")

        if page_new == 0:
            break

        page += 1

    return all_entries


def _parse_added_date(text: Optional[str]) -> Optional[datetime]:
    if not text:
        return None

    if isinstance(text, datetime):
        return text
    if isinstance(text, date):
        return datetime(text.year, text.month, text.day)
    if not isinstance(text, str):
        return None

    text = text.strip()
    formats = [
        "%B %d, %Y",
        "%b %d, %Y",
        "%B %d %Y",
        "%b %d %Y",
    ]
    for fmt in formats:
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue
    return None


def save_scraped_data(entries: List[Dict[str, Any]], filepath: str = "applicant_data.json") -> None:
    """
    Save scraped data to a JSON file.

    Args:
        entries (List[Dict[str, Any]]): Scraped entries.
        filepath (str): Output file path.
    """
    with open(filepath, "w", encoding="utf-8") as file_handle:
        json.dump(entries, file_handle, indent=2, ensure_ascii=False)

    print(f"Saved {len(entries)} entries to {filepath}")


if __name__ == "__main__":
    # Run a scrape directly from the CLI for quick testing.
    scrape_data(max_entries=50000)
