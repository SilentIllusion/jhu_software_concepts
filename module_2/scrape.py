"""
Grad Cafe Web Scraper - Module 2 Assignment
Scrapes applicant admission data from The Grad Cafe survey pages.
Uses urllib3 for URL management and BeautifulSoup for HTML parsing.
"""

import json
import re
from urllib3 import PoolManager
from urllib3.util.retry import Retry
from bs4 import BeautifulSoup
from clean import clean_data, save_data



# Base URL for Grad Cafe survey
BASE_URL = "https://www.thegradcafe.com"
SURVEY_URL = f"{BASE_URL}/survey/"


def _build_request_headers():
    """Build headers for HTTP requests to mimic a browser."""
    return {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
    }


def _extract_gre_from_text(text):
    """
    Extract GRE scores from comment/notes text using regex.
    Looks for patterns like: GRE 170, GRE V 163, GRE AW 4.0
    Returns (gre_total, gre_v, gre_aw) as strings or None.
    """
    if not text:
        return None, None, None
    gre_total = None
    gre_v = None
    gre_aw = None
    # GRE total: "GRE 170" or "GRE: 170"
    gre_match = re.search(r"GRE\s*:?\s*(\d{2,3})\b", text, re.IGNORECASE)
    if gre_match:
        gre_total = gre_match.group(1)
    # GRE V: "GRE V 163" or "GRE Verbal 163" or "V 163"
    gre_v_match = re.search(r"GRE\s*V(?:erbal)?\s*:?\s*(\d{2,3})\b", text, re.IGNORECASE)
    if gre_v_match:
        gre_v = gre_v_match.group(1)
    # GRE AW: "GRE AW 4.0" or "AW 4.0" or "Analytical Writing 4.0"
    gre_aw_match = re.search(r"(?:GRE\s*)?AW\s*:?\s*(\d\.?\d*)\b", text, re.IGNORECASE)
    if gre_aw_match:
        gre_aw = gre_aw_match.group(1)
    return gre_total, gre_v, gre_aw


def _extract_gpa_from_text(text):
    """Extract GPA from text like 'GPA 3.69' or 'GPA: 3.7'."""
    if not text:
        return None
    gpa_match = re.search(r"GPA\s*:?\s*(\d\.?\d*)", text, re.IGNORECASE)
    return gpa_match.group(1) if gpa_match else None


def _parse_decision_date(decision_text):
    """
    Parse decision text to extract status and date.
    E.g. 'Accepted on 29 Jan' -> ('Accepted', '29 Jan')
    'Rejected on 7 Jun' -> ('Rejected', '7 Jun')
    """
    if not decision_text:
        return None, None
    text = decision_text.strip()
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
    date_match = re.search(r"on\s+(\d{1,2}\s+\w+)", text, re.IGNORECASE)
    date_str = date_match.group(1) if date_match else None
    return status, date_str


def _parse_semester(text):
    """Extract semester/year like 'Fall 2026' or 'Spring 2025'."""
    if not text:
        return None
    match = re.search(r"(Fall|Spring)\s+(\d{4})", text, re.IGNORECASE)
    if match:
        return f"{match.group(1)} {match.group(2)}"
    return None


def _parse_student_type(text):
    """Extract International, American, or Other from badge text."""
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


def _parse_degree(text):
    """Extract degree type: PhD, Masters, MBA, etc."""
    if not text:
        return None
    degree_types = ["PhD", "Masters", "MBA", "MFA", "JD", "EdD", "PsyD", "Other"]
    text_clean = text.strip()
    for d in degree_types:
        if d.lower() in text_clean.lower():
            return d
    return None


def _parse_listing_row(main_row, detail_row, comment_row):
    """
    Parse a single applicant entry from listing page table rows.
    main_row: tr with school, program, date, decision
    detail_row: tr with badges (semester, international/american, GPA)
    comment_row: tr with comment/notes text
    """
    entry = {
        "program_name": None,
        "university": None,
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

    # Parse main row - 4 td cells: School, Program, Added On, Decision, Actions
    tds = main_row.find_all("td")
    if len(tds) < 4:
        return None

    # School (university)
    school_div = tds[0].find("div", class_=re.compile(r"tw-font-medium"))
    if school_div:
        entry["university"] = school_div.get_text(strip=True)

    # Program and degree
    program_div = tds[1].find("div", class_=re.compile(r"tw-text-gray-900"))
    if program_div:
        spans = program_div.find_all("span")
        if spans:
            entry["program_name"] = spans[0].get_text(strip=True)
            if len(spans) >= 2:
                entry["degree_type"] = _parse_degree(spans[1].get_text())

    # Added On date
    if len(tds) >= 3:
        added_text = tds[2].get_text(strip=True)
        if added_text and "comments" not in added_text.lower():
            entry["date_added"] = added_text

    # Decision
    decision_div = tds[3].find("div", class_=re.compile(r"tw-inline-flex"))
    if decision_div:
        decision_text = decision_div.get_text(strip=True)
        status, date_str = _parse_decision_date(decision_text)
        entry["applicant_status"] = status
        if status == "Accepted":
            entry["acceptance_date"] = date_str
        elif status == "Rejected":
            entry["rejection_date"] = date_str

    # Result URL - from link in last column
    link = main_row.find("a", href=re.compile(r"/result/\d+"))
    if link and link.get("href"):
        href = link["href"]
        if href.startswith("/"):
            entry["url"] = BASE_URL + href
        else:
            entry["url"] = href

    # Parse detail row - badges for semester, international/american, GPA
    if detail_row:
        badges = detail_row.find_all("div", class_=re.compile(r"tw-inline-flex"))
        for badge in badges:
            text = badge.get_text(strip=True)
            if not text:
                continue
            if _parse_semester(text):
                entry["semester_year"] = _parse_semester(text)
            elif _parse_student_type(text):
                entry["international_american"] = _parse_student_type(text)
            elif _extract_gpa_from_text(text):
                entry["gpa"] = _extract_gpa_from_text(text)

    # Parse comment row - may contain GRE info, notes
    if comment_row:
        p_tag = comment_row.find("p")
        if p_tag:
            comment_text = p_tag.get_text(strip=True)
            entry["comments"] = comment_text if comment_text else None
            # Extract GRE from comments if not already found
            gre_total, gre_v, gre_aw = _extract_gre_from_text(comment_text)
            if gre_total and not entry["gre_score"]:
                entry["gre_score"] = gre_total
            if gre_v and not entry["gre_v_score"]:
                entry["gre_v_score"] = gre_v
            if gre_aw and not entry["gre_aw"]:
                entry["gre_aw"] = gre_aw
            # GPA might be in comments too
            if not entry["gpa"] and _extract_gpa_from_text(comment_text):
                entry["gpa"] = _extract_gpa_from_text(comment_text)

    return entry


def scrape_data(max_entries=50000):
    """
    Pull data from Grad Cafe survey pages.
    Paginates through results until max_entries is reached.
    Returns list of applicant entry dictionaries.
    """
    http = PoolManager(
        retries=Retry(connect=3, read=2, backoff_factor=1),
        headers=_build_request_headers(),
    )
    all_entries = []
    page = 1
    per_page = 100

    while len(all_entries) < max_entries:
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
        except Exception as e:
            print(f"Error fetching page {page}: {e}")
            break

        soup = BeautifulSoup(html, "html.parser")
        tbody = soup.find("tbody", class_=re.compile(r"tw-divide-y"))
        if not tbody:
            print(f"Page {page}: No tbody found")
            break

        rows = tbody.find_all("tr")
        page_entries = 0
        i = 0
        while i < len(rows):
            row = rows[i]
            # Skip non-data rows (e.g. border-none detail/comment rows when we process them)
            if "tw-border-none" in row.get("class", []):
                i += 1
                continue

            main_row = row
            detail_row = None
            comment_row = None
            if i + 1 < len(rows) and "tw-border-none" in rows[i + 1].get("class", []):
                detail_row = rows[i + 1]
                i += 1
            if i + 1 < len(rows) and "tw-border-none" in rows[i + 1].get("class", []):
                comment_row = rows[i + 1]
                i += 1

            entry = _parse_listing_row(main_row, detail_row, comment_row)
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

    save_data(all_entries)
    return all_entries


def save_data(entries, filepath="applicant_data.json"):
    """Save scraped data to JSON file."""
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(entries, f, indent=2, ensure_ascii=False)
    print(f"Saved {len(entries)} entries to {filepath}")


if __name__ == "__main__":
    scrape_data(max_entries=50000)
