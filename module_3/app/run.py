import threading
import time

import psycopg
from flask import Flask, redirect, render_template, request, url_for

from query_data import (
    SQL_AI_AVG_GPA,
    SQL_AVG_GPA,
    SQL_AVG_GPA_AMERICAN_FALL_2026,
    SQL_AVG_GPA_FALL_2026_ACCEPT,
    SQL_AVG_GRE,
    SQL_AVG_GRE_AW,
    SQL_AVG_GRE_V,
    SQL_COUNT_FALL_2026,
    SQL_CS_PHD_2026_TOP_COUNT,
    SQL_CS_PHD_2026_TOP_COUNT_LLM,
    SQL_INSERT_ADMISSION_RESULTS,
    SQL_INTL_PCT,
    SQL_JHU_MS_CS_COUNT,
    SQL_LATEST_DATE_ADDED,
    SQL_PCT_FALL_2026_ACCEPT,
    SQL_SELECT_EXISTING_URLS,
    SQL_TOTAL_AI_COUNT,
)
from scripts.clean import clean_data
from scripts.scrape import scrape_new_data

app = Flask(__name__)

def get_db_connection():

    connection = psycopg.connect(
        dbname="grad_cafe",
        user="postgres",
        password="04021986"
    )
    return connection

def query_scalar(cur, sql, params=None):
    cur.execute(sql, params or ())
    row = cur.fetchone()
    if row is None:
        return None
    return row[0]


scrape_state = {"running": False, "message": None, "last_run": None}
scrape_lock = threading.Lock()


def _get_existing_urls(conn):
    with conn.cursor() as cur:
        cur.execute(SQL_SELECT_EXISTING_URLS)
        rows = cur.fetchall()
    urls = set()
    for row in rows:
        if row and row[0]:
            urls.add(row[0])
    return urls


def _get_latest_date_added(conn):
    with conn.cursor() as cur:
        cur.execute(SQL_LATEST_DATE_ADDED)
        row = cur.fetchone()
    return row[0] if row else None


def _insert_entries(conn, entries):
    if not entries:
        return 0

    data = []
    for r in entries:
        data.append(
            (
                r.get("program"),
                r.get("comments"),
                r.get("date_added"),
                r.get("url"),
                r.get("applicant_status"),
                r.get("semester_year"),
                r.get("international_american"),
                r.get("gre_score") if r.get("gre_score") is not None else 0.0,
                r.get("gre_v_score") if r.get("gre_v_score") is not None else 0.0,
                r.get("gpa"),
                r.get("gre_aw") if r.get("gre_aw") is not None else 0.0,
                r.get("degree_type"),
                None,
                None,
            )
        )

    with conn.cursor() as cur:
        cur.executemany(
            SQL_INSERT_ADMISSION_RESULTS,
            data,
        )
    conn.commit()
    return len(data)


def _run_scrape_job():
    with scrape_lock:
        if scrape_state["running"]:
            return
        scrape_state["running"] = True
        scrape_state["message"] = "Pull Data is running. This may take several minutes."

    started = time.time()
    inserted = 0
    try:
        conn = get_db_connection()
        existing_urls = _get_existing_urls(conn)
        latest_date = _get_latest_date_added(conn)
        new_entries = scrape_new_data(existing_urls, latest_date=latest_date)
        cleaned_entries = clean_data(new_entries)
        inserted = _insert_entries(conn, cleaned_entries)
        conn.close()

        elapsed = int(time.time() - started)
        scrape_state["message"] = f"Pull Data completed. Added {inserted} new rows in {elapsed}s."
        scrape_state["last_run"] = time.strftime("%Y-%m-%d %H:%M:%S")
    except Exception as exc:
        scrape_state["message"] = f"Pull Data failed: {exc}"
    finally:
        with scrape_lock:
            scrape_state["running"] = False

@app.route('/')
def index():
    conn = get_db_connection()
    cur = conn.cursor()

    intl_pct = query_scalar(cur, SQL_INTL_PCT)

    count_fall_2026 = query_scalar(cur, SQL_COUNT_FALL_2026)

    avg_gpa = query_scalar(cur, SQL_AVG_GPA)

    avg_gre = query_scalar(cur, SQL_AVG_GRE)

    avg_gre_v = query_scalar(cur, SQL_AVG_GRE_V)

    avg_gre_aw = query_scalar(cur, SQL_AVG_GRE_AW)

    avg_gpa_american_fall_2026 = query_scalar(cur, SQL_AVG_GPA_AMERICAN_FALL_2026)

    pct_fall_2026_accept = query_scalar(
        cur,
        SQL_PCT_FALL_2026_ACCEPT,
        ("Accepted%", "Fall 2026"),
    )

    avg_gpa_fall_2026_accept = query_scalar(
        cur,
        SQL_AVG_GPA_FALL_2026_ACCEPT,
        ("Fall 2026", "Accepted%"),
    )

    jhu_ms_cs_count = query_scalar(
        cur,
        SQL_JHU_MS_CS_COUNT,
        ("%Computer Science%", "%Johns Hopkins%", "%JHU%", "%Master%"),
    )

    cs_phd_2026_top_count = query_scalar(
        cur,
        SQL_CS_PHD_2026_TOP_COUNT,
        (
            "%2026%",
            "Accepted%",
            "%PhD%",
            "%Computer Science%",
            "%Georgetown%",
            "%MIT%",
            "%Massachusetts Institute of Technology%",
            "%Stanford%",
            "%Carnegie Mellon%",
        ),
    )

    cs_phd_2026_top_count_llm = query_scalar(
        cur,
        SQL_CS_PHD_2026_TOP_COUNT_LLM,
        (
            "%2026%",
            "Accepted%",
            "%PhD%",
            "%Computer Science%",
            "%Georgetown%",
            "%MIT%",
            "%Massachusetts Institute of Technology%",
            "%Stanford%",
            "%Carnegie Mellon%",
        ),
    )

    total_ai_count = query_scalar(
        cur,
        SQL_TOTAL_AI_COUNT,
        (
            "%Artificial Intelligence%",
            "%Accepted%",
        ),
    )

    ai_avg_gpa = query_scalar(
            cur,
        SQL_AI_AVG_GPA,
        ("%Artificial Intelligence%", "%Accepted%"),
        )

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

    return render_template(
        'index.html',
        intl_pct=intl_pct,
        count_fall_2026=count_fall_2026,
        avg_gpa=avg_gpa,
        avg_gre=avg_gre,
        avg_gre_v=avg_gre_v,
        avg_gre_aw=avg_gre_aw,
        avg_gpa_american_fall_2026=avg_gpa_american_fall_2026,
        pct_fall_2026_accept=pct_fall_2026_accept,
        avg_gpa_fall_2026_accept=avg_gpa_fall_2026_accept,
        jhu_ms_cs_count=jhu_ms_cs_count,
        cs_phd_2026_top_count=cs_phd_2026_top_count,
        cs_phd_2026_top_count_llm=cs_phd_2026_top_count_llm,
        counts_change=counts_change,
        change_explanation=change_explanation,
        total_ai_count=total_ai_count,
        ai_avg_gpa=ai_avg_gpa,
        scrape_running=scrape_state["running"],
        scrape_message=scrape_state["message"],
        scrape_last_run=scrape_state["last_run"],
    )


@app.route("/pull-data", methods=["POST"])
def pull_data():
    with scrape_lock:
        if scrape_state["running"]:
            scrape_state["message"] = (
                "Pull Data is already running. Please wait until it finishes."
            )
            return redirect(url_for("index"))

        thread = threading.Thread(target=_run_scrape_job, daemon=True)
        thread.start()

    return redirect(url_for("index"))


@app.route("/update-analysis", methods=["POST"])
def update_analysis():
    with scrape_lock:
        if scrape_state["running"]:
            scrape_state["message"] = (
                "Update Analysis is disabled while Pull Data is running."
            )
            return redirect(url_for("index"))

    return redirect(url_for("index"))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
