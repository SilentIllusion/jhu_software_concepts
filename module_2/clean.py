from bs4 import BeautifulSoup
import re

def clean_data(records):
    if not records:
        return []
    
    expected_keys = [
        "Program Name",
            "University",
            "Comments",
            "Date of Information Added to Grad Café",
            "URL link to applicant entry",
            "Applicant Status",
            "Accepted: Acceptance Date",
            "Rejected: Rejection Date",
            "Semester and Year of Program Start",
            "International / American Student",
            "GRE Score",
            "GRE V Score",
            "Masters or PhD",
            "GPA",
            "GRE AW",
    ]

    missing_values = {
        "n/a",
        "na",
        "none",
        "null",
        "unknown",
        "not available",
        "not applicable",
        "-",
        "—",
        "--",
        "tbd",
    }

    cleaned_records = []

    for record in records:
        if not isinstance(record, dict):
            continue

        cleaned = {}

        for key in expected_keys:
            value = record.get(key)

            # Normalize missing keys/None
            if value is None:
                cleaned[key] = None
                continue

            # Convert non-strings to string
            if not isinstance(value, str):
                value = str(value)

            # Strip HTML tags if any exist
            value = BeautifulSoup(value, "html.parser").get_text(" ", strip=True)

            # Normalize whitespace
            value = re.sub(r"\s+", " ", value).strip()

            # Normalize empty string
            if value == "":
                cleaned[key] = None
                continue

            # Normalize placeholder values
            if value.lower() in missing_values:
                cleaned[key] = None
                continue

            # If it's only punctuation/noise, treat as missing
            if re.fullmatch(r"[\W_]+", value):
                cleaned[key] = None
                continue

            cleaned[key] = value

        # Light cleanup that doesn't "invent" data:
        # Validate URL shape
        url_value = cleaned.get("URL link to applicant entry")
        if url_value is not None:
            url_value = re.sub(r"\s+", "", url_value)
            if re.match(r"^https?://", url_value):
                cleaned["URL link to applicant entry"] = url_value
            else:
                cleaned["URL link to applicant entry"] = None

        cleaned_records.append(cleaned)

    return cleaned_records

def save_data():
    return

def load():
    return