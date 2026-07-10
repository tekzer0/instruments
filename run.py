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
