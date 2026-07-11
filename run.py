#!/usr/bin/env python3
"""Single entrypoint for all jobs. Usage: python run.py <job>

Jobs:
  initdb    create/upgrade the database
  prices    ingest sold prices (SoldComps)
  bench     ingest llama-bench files from data/inbox_benchmarks/
  join      compute price+perf rankings
  publish   regenerate static site from rankings
  news      run tombstone news watcher
  validate  validate registry device YAML files
  digest    send weekly status digest
  queue     list pending tombstone candidates
  dismiss N mark candidate N as dismissed (not a real cloud death)
  confirm N mark candidate N as confirmed (then add it to tombstones.yaml)
  all       prices + bench + join + publish + news
"""
import sys

from common import db
from common.health import tracked


def main() -> int:
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
        print(__doc__)
        return 1
    job = sys.argv[1]
    db.init()

    if job == "initdb":
        print("db ready:", db.DB_PATH)
        return 0
    if job == "prices":
        from observatory.ingest_prices import run
        return tracked("prices", run)
    if job == "bench":
        from observatory.ingest_benchmarks import run
        return tracked("bench", run)
    if job == "join":
        from observatory.join import run
        return tracked("join", run)
    if job == "publish":
        from observatory.publish import run
        return tracked("publish", run)
    if job == "news":
        from registry.watch_news import run
        return tracked("news", run)
    if job == "validate":
        from registry.validate import run
        return tracked("validate", run)
    if job == "digest":
        from digest.weekly_digest import run
        return tracked("digest", run)
    if job == "queue":
        with db.connect() as conn:
            rows = conn.execute(
                "SELECT id, payload, created_at FROM events_queue WHERE status='pending' ORDER BY id"
            ).fetchall()
        if not rows:
            print("queue empty — nothing pending")
        for r in rows:
            print(f"[{r['id']}] {r['created_at']}\n    {r['payload'].splitlines()[0]}")
        return 0
    if job in ("dismiss", "confirm"):
        if len(sys.argv) < 3:
            print(f"usage: python run.py {job} <id>")
            return 1
        status = "dismissed" if job == "dismiss" else "confirmed"
        with db.connect() as conn:
            cur = conn.execute(
                "UPDATE events_queue SET status=? WHERE id=? AND status='pending'",
                (status, sys.argv[2]),
            )
        if cur.rowcount:
            print(f"candidate {sys.argv[2]} -> {status}")
            if status == "confirmed":
                print("now add the entry to registry/tombstones.yaml (with sources) and run validate")
        else:
            print(f"no pending candidate with id {sys.argv[2]}")
        return 0
    if job == "all":
        rc = 0
        for j in ("prices", "bench", "join", "publish", "news"):
            sys.argv[1] = j
            rc |= main()
        return rc
    print("unknown job:", job)
    print(__doc__)
    return 1


if __name__ == "__main__":
    sys.exit(main())
