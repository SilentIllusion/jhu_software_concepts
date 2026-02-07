"""
Grad Cafe Data Cleaning - Module 2 Assignment
Cleans scraped applicant data: removes HTML, normalizes values, structures output.
LLM-based program/university standardization is done via llm_hosting (run separately).
"""

import json
import re

from bs4 import BeautifulSoup


# Canonical keys expected for each applicant entry in the cleaned output.
# Any missing/unavailable value should be normalized to None (unless serialized later).
EXPECTED_KEYS = [
    "program",
    "comments",
    "date_added",
    "url",
    "applicant_status",
    "acceptance_date",
    "rejection_date",
    "semester_year",
    "international_american",
    "gre_score",
    "gre_v_score",
    "degree_type",
    "gpa",
    "gre_aw",
]


def _strip_html(text):
    """
    Remove remnant HTML tags from text.

    Uses BeautifulSoup only when the input appears to contain tags.
    Returns:
        - cleaned string when a non-empty string is produced
        - None when input is None, non-string, or empty after stripping
    """
    if text is None:
        return None
    if not isinstance(text, str):
        return None

    text = text.strip()
    if not text:
        return None

    # Only parse with BeautifulSoup if the string likely contains HTML.
    if "<" in text and ">" in text:
        soup = BeautifulSoup(text, "html.parser")
        text = soup.get_text(separator=" ", strip=True)

    text = text.strip()
    return text if text else None


def _normalize_value(val):
    """
    Normalize an individual value into a consistent Python type.

    Rules:
        - None stays None
        - "null"/"none"/"" (case-insensitive) -> None
        - int/float preserved as-is
        - strings have HTML removed and are trimmed; empty -> None
        - everything else -> None (unsupported types)
    """
    if val is None:
        return None

    if isinstance(val, str) and val.strip().lower() in ("null", "none", ""):
        return None

    if isinstance(val, (int, float)):
        return val

    if isinstance(val, str):
        cleaned = _strip_html(val)
        return cleaned if cleaned else None

    return None


def _clean_single_entry(entry):
    """
    Clean a single applicant entry:
        - normalizes all expected keys
        - optionally backfills 'program' using legacy fields (program_name/university)
        - preserves additional, non-canonical fields when they look like real data

    Notes:
        - This function avoids "cleaning logic" that changes meaning; it focuses on
          normalization, HTML stripping, and shaping data into a consistent schema.
    """
    record = entry or {}

    # Backward compatibility: some scraped payloads may have program_name/university
    # instead of a single 'program' field. If 'program' is missing, build it.
    if not record.get("program") and (record.get("program_name") or record.get("university")):
        program_name = (record.get("program_name") or "").strip()
        university = (record.get("university") or "").strip()

        if program_name and university:
            record = {**record, "program": f"{program_name}, {university}"}
        elif program_name:
            record = {**record, "program": program_name}
        elif university:
            record = {**record, "program": university}

    # Normalize all expected fields into the cleaned schema.
    cleaned = {}
    for key in EXPECTED_KEYS:
        cleaned[key] = _normalize_value(record.get(key))

    # Preserve unexpected keys (lightly), but exclude known legacy/LLM fields.
    # This allows you to keep extra scraped columns without breaking your schema.
    skip_keys = (
        "program_name",
        "university",
        "llm-generated-program",
        "llm-generated-university",
    )

    for key, val in record.items():
        if key in EXPECTED_KEYS or key in skip_keys:
            continue

        # Skip fields that look like internal metadata (None/empty).
        if val in (None, ""):
            continue

        # Only preserve values that are JSON-serializable primitives and normalize them.
        if isinstance(val, (str, int, float)):
            cleaned[key] = _normalize_value(val)

    return cleaned


def _remove_messy_content(text):
    """
    Remove unexpected/messy information from a text field.

    Examples:
        - control characters
        - excessive whitespace

    Returns:
        - cleaned string, or None if the result is empty/invalid
    """
    if not isinstance(text, str) or not text:
        return None

    # Remove control characters (ASCII control ranges).
    text = re.sub(r"[\x00-\x1f\x7f-\x9f]", "", text)

    # Collapse repeated whitespace to a single space.
    text = re.sub(r"\s+", " ", text).strip()

    return text if text else None


def clean_data(entries):
    """
    Convert raw scraped data into a structured, cleaned format.

    Cleaning performed:
        - HTML stripping for all string fields (via _normalize_value)
        - unavailable values normalized to None
        - additional cleanup for specific text fields (program/comments)

    Args:
        entries: list of dicts (raw scraped entries)

    Returns:
        list of cleaned dicts with consistent keys and normalized values
    """
    cleaned_list = []

    for entry in entries:
        # Skip non-dict rows to avoid runtime errors and keep output consistent.
        if not isinstance(entry, dict):
            continue

        cleaned = _clean_single_entry(entry)

        # Apply post-normalization cleanup to selected text fields only.
        for key in ("program", "comments"):
            if cleaned.get(key):
                cleaned[key] = _remove_messy_content(cleaned[key]) or None

        cleaned_list.append(cleaned)

    return cleaned_list


def _replace_none_with_string(obj):
    """
    Recursively replace Python None with the string "none" for JSON output.

    This is a serialization choice (not a data-cleaning rule). It preserves the
    idea of "missing" while avoiding JSON null if required by your assignment.
    """
    if obj is None:
        return "none"

    if isinstance(obj, dict):
        return {key: _replace_none_with_string(value) for key, value in obj.items()}

    if isinstance(obj, list):
        return [_replace_none_with_string(item) for item in obj]

    return obj


def save_data(entries, filepath="applicant_data.json"):
    """
    Save cleaned data to a JSON file.

    Notes:
        - None values are serialized as the string "none" (via _replace_none_with_string).
        - ensure_ascii=False preserves non-ASCII characters.
    """
    with open(filepath, "w", encoding="utf-8") as file_handle:
        json.dump(
            _replace_none_with_string(entries),
            file_handle,
            indent=2,
            ensure_ascii=False,
        )

    print(f"Saved {len(entries)} entries to {filepath}")


def load_data(filepath="applicant_data.json"):
    """
    Load data from a JSON file.

    Returns:
        Parsed JSON object (usually a list of dict entries).
    """
    with open(filepath, "r", encoding="utf-8") as file_handle:
        return json.load(file_handle)


if __name__ == "__main__":
    # Simple CLI execution:
    # 1) Load previously saved scraped data
    # 2) Clean/normalize it
    # 3) Save the cleaned output back to disk
    raw_entries = load_data("applicant_data.json")
    cleaned_entries = clean_data(raw_entries)
    save_data(cleaned_entries, "applicant_data.json")
    print(f"Cleaned {len(cleaned_entries)} entries")
