"""SQL queries and CLI output for Module 3 analytics."""

import psycopg

SQL_SELECT_EXISTING_URLS = "SELECT url FROM admission_results WHERE url IS NOT NULL"

SQL_LATEST_DATE_ADDED = """
SELECT date_added
FROM admission_results
WHERE date_added IS NOT NULL
ORDER BY date_added DESC
LIMIT 1
"""

SQL_INSERT_ADMISSION_RESULTS = """
INSERT INTO admission_results
(program, comments, date_added, url, status, term, us_or_international,
 gre, gre_v, gpa, gre_aw, degree, llm_generated_program, llm_generated_university)
VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
"""

SQL_INTL_PCT = """
SELECT ROUND(
    100.0 * SUM(CASE
        WHEN us_or_international NOT IN ('American', 'Other')
             AND us_or_international IS NOT NULL
        THEN 1 ELSE 0 END
    ) / NULLIF(COUNT(*), 0),
2)
FROM admission_results
"""

SQL_COUNT_FALL_2026 = """
SELECT COUNT(*)
FROM admission_results
WHERE term = 'Fall 2026'
"""

SQL_AVG_GPA = """
SELECT ROUND(AVG(gpa)::numeric, 2)
FROM admission_results
WHERE gpa IS NOT NULL
"""

SQL_AVG_GRE = """
SELECT ROUND(AVG(gre)::numeric, 2)
FROM admission_results
WHERE gre IS NOT NULL AND gre > 0
"""

SQL_AVG_GRE_V = """
SELECT ROUND(AVG(gre_v)::numeric, 2)
FROM admission_results
WHERE gre_v IS NOT NULL AND gre_v > 0
"""

SQL_AVG_GRE_AW = """
SELECT ROUND(AVG(gre_aw)::numeric, 2)
FROM admission_results
WHERE gre_aw IS NOT NULL AND gre_aw > 0
"""

SQL_AVG_GPA_AMERICAN_FALL_2026 = """
SELECT ROUND(AVG(gpa)::numeric, 2)
FROM admission_results
WHERE gpa IS NOT NULL
  AND us_or_international = 'American'
  AND term = 'Fall 2026'
"""

SQL_PCT_FALL_2026_ACCEPT = """
SELECT ROUND(
    100.0 * SUM(CASE
        WHEN status ILIKE 'Accepted%' THEN 1 ELSE 0 END
    ) / NULLIF(COUNT(*), 0),
2)
FROM admission_results
WHERE term = 'Fall 2026'
"""

SQL_AVG_GPA_FALL_2026_ACCEPT = """
SELECT ROUND(AVG(gpa)::numeric, 2)
FROM admission_results
WHERE gpa IS NOT NULL
  AND term = 'Fall 2026'
  AND status ILIKE '%Accepted%'
"""

SQL_JHU_MS_CS_COUNT = """
SELECT COUNT(*)
FROM admission_results
WHERE program ILIKE '%Computer Science%'
  AND (program ILIKE '%Johns Hopkins%' OR program ILIKE '%JHU%')
  AND degree ILIKE '%Master%'
"""

SQL_CS_PHD_2026_TOP_COUNT = """
SELECT COUNT(*)
FROM admission_results
WHERE term ILIKE '%2026%'
  AND status ILIKE 'Accepted%'
  AND degree ILIKE '%PhD%'
  AND program ILIKE '%Computer Science%'
  AND (
        program ILIKE '%Georgetown%'
     OR program ILIKE '%MIT%'
     OR program ILIKE '%Massachusetts Institute of Technology%'
     OR program ILIKE '%Stanford%'
     OR program ILIKE '%Carnegie Mellon%'
  )
"""

SQL_CS_PHD_2026_TOP_COUNT_LLM = """
SELECT COUNT(*)
FROM admission_results
WHERE term ILIKE '%2026%'
  AND status ILIKE 'Accepted%'
  AND degree ILIKE '%PhD%'
  AND llm_generated_program ILIKE '%Computer Science%'
  AND (
        llm_generated_university ILIKE '%Georgetown%'
     OR llm_generated_university ILIKE '%MIT%'
     OR llm_generated_university ILIKE '%Massachusetts Institute of Technology%'
     OR llm_generated_university ILIKE '%Stanford%'
     OR llm_generated_university ILIKE '%Carnegie Mellon%'
  )
"""

SQL_TOTAL_AI_COUNT = """
SELECT COUNT(*)
FROM admission_results
WHERE program ILIKE '%Artificial Intelligence%'
  AND status ILIKE '%Accepted%'
"""

SQL_AI_AVG_GPA = """
SELECT ROUND(AVG(gpa)::numeric, 2)
FROM admission_results
WHERE gpa IS NOT NULL
  AND program ILIKE '%Artificial Intelligence%'
  AND status ILIKE '%Accepted%'
"""

SQL_APPLICANT_COUNT = """
SELECT COUNT(*)
FROM admission_results
"""

SQL_INTL_COUNT = """
SELECT COUNT(*)
FROM admission_results
WHERE us_or_international NOT IN ('American', 'Other')
  AND us_or_international IS NOT NULL
"""

SQL_US_COUNT = """
SELECT COUNT(*)
FROM admission_results
WHERE us_or_international = 'American'
"""

SQL_OTHER_COUNT = """
SELECT COUNT(*)
FROM admission_results
WHERE us_or_international = 'Other'
"""

SQL_ACCEPTANCE_COUNT = """
SELECT COUNT(*)
FROM admission_results
WHERE status ILIKE 'Accepted%'
"""

SQL_ACCEPTANCE_PCT = """
SELECT ROUND(
    100.0 * SUM(CASE
        WHEN status ILIKE 'Accepted%' THEN 1 ELSE 0 END
    ) / NULLIF(COUNT(*), 0),
2)
FROM admission_results
"""

SQL_AVG_GPA_ACCEPTANCE = """
SELECT ROUND(AVG(gpa)::numeric, 2)
FROM admission_results
WHERE gpa IS NOT NULL
  AND status ILIKE 'Accepted%'
"""


def get_db_connection():
    """Create a new database connection."""
    connection = psycopg.connect(
        dbname="grad_cafe",
        user="postgres",
        password="04021986",
    )
    return connection


def query_scalar(cur, sql, params=None):
    """Run a query that returns a single scalar value."""
    if params is None:
        cur.execute(sql)
    else:
        cur.execute(sql, params)
    row = cur.fetchone()
    if row is None:
        return None
    return row[0]


if __name__ == "__main__":  # pragma: no cover
    conn = get_db_connection()
    cur = conn.cursor()

    count_fall_2026 = query_scalar(cur, SQL_COUNT_FALL_2026)
    intl_pct = query_scalar(cur, SQL_INTL_PCT)
    avg_gpa = query_scalar(cur, SQL_AVG_GPA)
    avg_gre = query_scalar(cur, SQL_AVG_GRE)
    avg_gre_v = query_scalar(cur, SQL_AVG_GRE_V)
    avg_gre_aw = query_scalar(cur, SQL_AVG_GRE_AW)

    avg_gpa_american_fall_2026 = query_scalar(
        cur,
        SQL_AVG_GPA_AMERICAN_FALL_2026,
    )

    pct_fall_2026_accept = query_scalar(
        cur,
        SQL_PCT_FALL_2026_ACCEPT,
    )

    avg_gpa_fall_2026_accept = query_scalar(cur, SQL_AVG_GPA_FALL_2026_ACCEPT)

    jhu_ms_cs_count = query_scalar(cur, SQL_JHU_MS_CS_COUNT)

    cs_phd_2026_top_count = query_scalar(cur, SQL_CS_PHD_2026_TOP_COUNT)

    cs_phd_2026_top_count_llm = query_scalar(cur, SQL_CS_PHD_2026_TOP_COUNT_LLM)

    total_ai_count = query_scalar(cur, SQL_TOTAL_AI_COUNT)

    ai_avg_gpa = query_scalar(cur, SQL_AI_AVG_GPA)

    cur.close()
    conn.close()

    counts_change = cs_phd_2026_top_count != cs_phd_2026_top_count_llm
    change_explanation = (
        f"Yes. Downloaded fields count = {cs_phd_2026_top_count}, "
        f"LLM fields count = {cs_phd_2026_top_count_llm}."
        if counts_change
        else (
            f"No. Both methods return {cs_phd_2026_top_count}."
            if cs_phd_2026_top_count is not None
            else "No. Both methods returned no result."
        )
    )

    print(
        "How many entries do you have in your database who have applied for Fall 2026? "
        f"{count_fall_2026}"
    )
    print(
        "What percentage of entries are from international students "
        "(not American or Other) (to two decimal places)? "
        f"{intl_pct}"
    )
    print(
        "What is the average GPA, GRE, GRE V, GRE AW of applicants who provide "
        "these metrics? "
        f"GPA {avg_gpa}, GRE {avg_gre}, GRE V {avg_gre_v}, GRE AW {avg_gre_aw}"
    )
    print(
        "What is their average GPA of American students in Fall 2026? "
        f"{avg_gpa_american_fall_2026}"
    )
    print(
        "What percent of entries for Fall 2026 are Acceptances? "
        f"{pct_fall_2026_accept}"
    )
    print(
        "What is the average GPA of applicants who applied for Fall 2026 "
        "who were accepted? "
        f"{avg_gpa_fall_2026_accept}"
    )
    print(
        "How many entries are from applicants who applied to JHU for a "
        "masters degrees in Computer Science? "
        f"{jhu_ms_cs_count}"
    )
    print(
        "How many entries from 2026 are acceptances from applicants who applied "
        "to Georgetown University, MIT, Stanford University, or Carnegie Mellon "
        "University for a PhD in Computer Science? "
        f"{cs_phd_2026_top_count}"
    )
    print(
        "Do the numbers for question 8 change if you use LLM Generated Fields "
        "(rather than your downloaded fields)? "
        f"{'Yes' if counts_change else 'No'}"
    )
    print(change_explanation)
    print(
        "How many entries are from applicants that applied to Artificial Intelligence "
        f"programs? {total_ai_count}"
    )
    print(
        "What is the average GPA of applicants that were accepted to a Artificial "
        f"Intelligence programs? {ai_avg_gpa}"
    )
