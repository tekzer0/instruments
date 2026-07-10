"""Job wrapper: records every run; alerts once after 3 consecutive failures.

Philosophy: the system nags the operator, the operator never has to remember.
One alert per failure streak (at exactly 3), not one per failure — no spam.
"""
import traceback

from common import db, notify

FAILURE_ALERT_THRESHOLD = 3


def _record(job: str, status: str, message: str = "") -> None:
    with db.connect() as conn:
        conn.execute(
            "INSERT INTO scraper_runs (job, status, message) VALUES (?,?,?)",
            (job, status, message[:2000]),
        )


def _consecutive_failures(job: str) -> int:
    with db.connect() as conn:
        rows = conn.execute(
            "SELECT status FROM scraper_runs WHERE job=? ORDER BY id DESC LIMIT ?",
            (job, FAILURE_ALERT_THRESHOLD),
        ).fetchall()
    n = 0
    for r in rows:
        if r["status"] == "fail":
            n += 1
        else:
            break
    return n


def tracked(job: str, fn) -> int:
    """Run fn(); record outcome; alert on failure streak. Returns shell rc."""
    try:
        msg = fn() or ""
        _record(job, "ok", str(msg))
        print(f"[{job}] ok {msg}")
        return 0
    except Exception:  # noqa: BLE001 - cron jobs must record, not die silently
        err = traceback.format_exc()
        _record(job, "fail", err)
        print(f"[{job}] FAIL\n{err}")
        if _consecutive_failures(job) == FAILURE_ALERT_THRESHOLD:
            notify.send(
                f"⚠ instrument job '{job}' has failed {FAILURE_ALERT_THRESHOLD}x in a row. "
                f"Site keeps serving last-good data. Last error:\n{err.splitlines()[-1]}"
            )
        return 1
