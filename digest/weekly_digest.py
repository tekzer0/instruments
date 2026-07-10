"""Monday digest: the ONE thing that keeps you informed with zero remembering.
Silence in your inbox never happens — a healthy week still sends a short 'all green'.
"""
from common import db, notify


def _one(conn, sql, *args):
    return conn.execute(sql, args).fetchone()[0]


def run() -> str:
    with db.connect() as conn:
        prices_wk = _one(conn, "SELECT COUNT(*) FROM price_obs WHERE ingested_at >= datetime('now','-7 days')")
        prices_all = _one(conn, "SELECT COUNT(*) FROM price_obs")
        bench_wk = _one(conn, "SELECT COUNT(*) FROM bench_obs WHERE ingested_at >= datetime('now','-7 days')")
        bench_all = _one(conn, "SELECT COUNT(*) FROM bench_obs")
        flagged = _one(conn, "SELECT COUNT(*) FROM bench_obs WHERE flagged=1")
        devices = _one(conn, "SELECT COUNT(*) FROM registry_devices")
        tombs = _one(conn, "SELECT COUNT(*) FROM tombstones")
        pending = _one(conn, "SELECT COUNT(*) FROM events_queue WHERE status='pending'")
        fails = conn.execute(
            "SELECT job, COUNT(*) n FROM scraper_runs "
            "WHERE status='fail' AND ran_at >= datetime('now','-7 days') GROUP BY job"
        ).fetchall()

    fail_txt = ("\n".join(f"  ⚠ {r['job']}: {r['n']} failures" for r in fails)) or "  ✓ all jobs green"
    msg = (
        "📊 Instruments — weekly digest\n"
        f"Observatory: +{prices_wk} prices (total {prices_all}), "
        f"+{bench_wk} bench rows (total {bench_all}, {flagged} flagged)\n"
        f"Registry: {devices} devices, {tombs} tombstones, {pending} candidates awaiting your confirm\n"
        f"Job health (7d):\n{fail_txt}"
    )
    notify.send(msg)
    return f"sent (pending_candidates={pending}, failing_jobs={len(fails)})"
