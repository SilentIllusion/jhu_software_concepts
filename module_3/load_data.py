import psycopg
import json

connection = psycopg.connect(
    dbname="grad_cafe",
    user="postgres",
    password="04021986")

with open("corrected_application_data_v2.json", "r", encoding="UTF-8") as f:
    rows = json.load(f)
data = []
for r in rows:
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

with connection.cursor() as cur:

    cur.executemany("""
                    INSERT INTO admission_results 
                    (program, comments, date_added, url, status, term, us_or_international, degree, gre, gre_v, gpa, gre_aw, llm_generated_program, llm_generated_university) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                    """, 
                    data
    )
connection.commit()
connection.close()