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
        WHEN status ILIKE %s THEN 1 ELSE 0 END
    ) / NULLIF(COUNT(*), 0),
2)
FROM admission_results
WHERE term = %s
"""

SQL_AVG_GPA_FALL_2026_ACCEPT = """
SELECT ROUND(AVG(gpa)::numeric, 2)
FROM admission_results
WHERE gpa IS NOT NULL
  AND term = %s
  AND status ILIKE %s
"""

SQL_JHU_MS_CS_COUNT = """
SELECT COUNT(*)
FROM admission_results
WHERE program ILIKE %s
  AND (program ILIKE %s OR program ILIKE %s)
  AND degree ILIKE %s
"""

SQL_CS_PHD_2026_TOP_COUNT = """
SELECT COUNT(*)
FROM admission_results
WHERE term ILIKE %s
  AND status ILIKE %s
  AND degree ILIKE %s
  AND program ILIKE %s
  AND (
        program ILIKE %s
     OR program ILIKE %s
     OR program ILIKE %s
     OR program ILIKE %s
     OR program ILIKE %s
  )
"""

SQL_CS_PHD_2026_TOP_COUNT_LLM = """
SELECT COUNT(*)
FROM admission_results
WHERE term ILIKE %s
  AND status ILIKE %s
  AND degree ILIKE %s
  AND llm_generated_program ILIKE %s
  AND (
        llm_generated_university ILIKE %s
     OR llm_generated_university ILIKE %s
     OR llm_generated_university ILIKE %s
     OR llm_generated_university ILIKE %s
     OR llm_generated_university ILIKE %s
  )
"""

SQL_TOTAL_AI_COUNT = """
SELECT COUNT(*)
FROM admission_results
WHERE program ILIKE %s
  AND status ILIKE %s
"""

SQL_AI_AVG_GPA = """
SELECT ROUND(AVG(gpa)::numeric, 2)
FROM admission_results
WHERE gpa IS NOT NULL
  AND program ILIKE %s
  AND status ILIKE %s
"""
