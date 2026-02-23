"""Load corrected application data into the ``admission_results`` table."""

from __future__ import annotations

import json
from typing import Iterable, Sequence

from psycopg import sql

from query_data import get_db_connection

SQL_INSERT_ADMISSION_RESULTS = sql.SQL("""
INSERT INTO admission_results
(program, comments, date_added, url, status, term, us_or_international,
 degree, gre, gre_v, gpa, gre_aw, llm_generated_program, llm_generated_university)
VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
""")


def _get_connection():  # pragma: no cover
    """Create a psycopg connection from environment variables."""
    return get_db_connection()


def _to_rows(records: Iterable[dict]) -> list[Sequence]:
    """Convert dict records into tuples matching the admission_results schema."""
    data = []
    for r in records:
        row = (
            r["program"],
            r["comments"],
            r["date_added"],
            r["url"],
            r["applicant_status"],
            r["semester_year"],
            r["international_american"],
            r["degree_type"],
            r["gre_score"],
            r["gre_v_score"],
            r["gpa"],
            r["gre_aw"],
            r["llm-generated-program"],
            r["llm-generated-university"],
        )
        data.append(row)
    return data


def load_corrected_data(filepath: str = "corrected_application_data_v2.json", conn=None) -> int:
    """
    Load the corrected Grad Cafe data JSON file into the database.

    Args:
        filepath: Path to the corrected JSON file.
        conn: Optional existing psycopg connection; when omitted a new one is created.

    Returns:
        Number of rows inserted.
    """
    close_conn = False
    if conn is None:
        conn = _get_connection()
        close_conn = True

    with open(filepath, "r", encoding="UTF-8") as f:
        records = json.load(f)

    data = _to_rows(records)

    with conn.cursor() as cur:
        cur.executemany(SQL_INSERT_ADMISSION_RESULTS, data)

    conn.commit()
    if close_conn:
        conn.close()

    return len(data)


if __name__ == "__main__":  # pragma: no cover
    inserted = load_corrected_data()
    print(f"Inserted {inserted} rows from corrected_application_data_v2.json")
