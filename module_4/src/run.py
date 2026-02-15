"""Flask app for Grad Cafe analytics and data refresh."""

import os
import threading
import time

import psycopg
from flask import Blueprint, Flask, current_app, jsonify, redirect, render_template, url_for

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

pages = Blueprint("pages", __name__)

scrape_state = {"running": False, "message": None, "last_run": None}
scrape_lock = threading.Lock()


def create_app(test_config=None):
    """Create and configure the Flask app."""
    app = Flask(__name__)
    app.config.update({"TESTING": False, "SYNC_PULL_DATA": False})
    if test_config:
        app.config.update(test_config)
    app.register_blueprint(pages)
    return app


def get_db_connection():
    """Create a new database connection.

    Prefers DATABASE_URL if set; otherwise falls back to local defaults.
    """
    url = os.environ.get("DATABASE_URL")
    if url:
        return psycopg.connect(url)
    return psycopg.connect(dbname="grad_cafe", user="postgres")


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


def _format_two_decimals(value):
    """Format percentage-like values with two decimals."""
    if value is None:
        return None
    return f"{float(value):.2f}"


def _get_existing_urls(conn):
    """Return a set of URLs already present in the database."""
    with conn.cursor() as cur:
        cur.execute(SQL_SELECT_EXISTING_URLS)
        rows = cur.fetchall()
    urls = set()
    for row in rows:
        if row and row[0]:
            urls.add(row[0])
    return urls


def _get_latest_date_added(conn):
    """Return the most recent date_added value, if present."""
    with conn.cursor() as cur:
        cur.execute(SQL_LATEST_DATE_ADDED)
        row = cur.fetchone()
    return row[0] if row else None


def _insert_entries(conn, entries):
    """Insert scraped entries and return the number inserted."""
    if not entries:
        return 0

    data = []
    seen_urls = set()
    for r in entries:
        row_url = r.get("url")
        if row_url and row_url in seen_urls:
            continue
        if row_url:
            seen_urls.add(row_url)

        data.append(
            (
                r.get("program"),
                r.get("comments"),
                r.get("date_added"),
                row_url,
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
        cur.executemany(SQL_INSERT_ADMISSION_RESULTS, data)
    conn.commit()
    return len(data)


def _run_scrape_job():
    """Background job to scrape new data and update the database."""
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


def get_analysis_data():
    """Return all dashboard answers as a dict."""
    conn = get_db_connection()
    cur = conn.cursor()

    intl_pct = query_scalar(cur, SQL_INTL_PCT)
    count_fall_2026 = query_scalar(cur, SQL_COUNT_FALL_2026)
    avg_gpa = query_scalar(cur, SQL_AVG_GPA)
    avg_gre = query_scalar(cur, SQL_AVG_GRE)
    avg_gre_v = query_scalar(cur, SQL_AVG_GRE_V)
    avg_gre_aw = query_scalar(cur, SQL_AVG_GRE_AW)
    avg_gpa_american_fall_2026 = query_scalar(cur, SQL_AVG_GPA_AMERICAN_FALL_2026)
    pct_fall_2026_accept = query_scalar(cur, SQL_PCT_FALL_2026_ACCEPT)
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

    return {
        "intl_pct": _format_two_decimals(intl_pct),
        "count_fall_2026": count_fall_2026,
        "avg_gpa": avg_gpa,
        "avg_gre": avg_gre,
        "avg_gre_v": avg_gre_v,
        "avg_gre_aw": avg_gre_aw,
        "avg_gpa_american_fall_2026": avg_gpa_american_fall_2026,
        "pct_fall_2026_accept": _format_two_decimals(pct_fall_2026_accept),
        "avg_gpa_fall_2026_accept": avg_gpa_fall_2026_accept,
        "jhu_ms_cs_count": jhu_ms_cs_count,
        "cs_phd_2026_top_count": cs_phd_2026_top_count,
        "cs_phd_2026_top_count_llm": cs_phd_2026_top_count_llm,
        "counts_change": counts_change,
        "change_explanation": change_explanation,
        "total_ai_count": total_ai_count,
        "ai_avg_gpa": ai_avg_gpa,
        "scrape_running": scrape_state["running"],
        "scrape_message": scrape_state["message"],
        "scrape_last_run": scrape_state["last_run"],
    }


@pages.route("/")
def index():
    """Redirect root to analysis page."""
    return redirect(url_for("pages.analysis"))


@pages.route("/analysis")
def analysis():
    """Render the analytics dashboard."""
    return render_template("index.html", **get_analysis_data())


@pages.route("/pull-data", methods=["POST"])
def pull_data():
    """Start a scrape job if one is not already running."""
    with scrape_lock:
        if scrape_state["running"]:
            scrape_state["message"] = "Pull Data is already running. Please wait until it finishes."
            return jsonify({"busy": True, "message": scrape_state["message"]}), 409

    if current_app.config.get("SYNC_PULL_DATA"):
        _run_scrape_job()
    else:
        thread = threading.Thread(target=_run_scrape_job, daemon=True)
        thread.start()

    return jsonify({"ok": True, "message": "Pull started"}), 200


@pages.route("/update-analysis", methods=["POST"])
def update_analysis():
    """Refresh analysis when no scrape job is running."""
    with scrape_lock:
        if scrape_state["running"]:
            scrape_state["message"] = "Update Analysis is disabled while Pull Data is running."
            return jsonify({"busy": True, "message": scrape_state["message"]}), 409

    return jsonify({"ok": True, "message": "Analysis refreshed"}), 200


app = create_app()

if __name__ == "__main__":  # pragma: no cover
    app.run(host="0.0.0.0", port=8080)

