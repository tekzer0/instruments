#!/bin/bash
# Auto-deploy fresh site builds to Hostinger via FTP after nightly publish.
# Self-updates code from GitHub first. Also publishes the static JSON API:
#   observatory.mordo.ai/data.json  (rankings dataset)
#   registry.mordo.ai/data.json     (tombstones + devices dataset)
#
# .env needs: FTP_HOST, FTP_USER, FTP_PASS (quote specials), FTP_OBS_PATH, FTP_REG_PATH
# optional: KOFI_URL (enables support links)
# Cron: 55 5 * * * cd /opt/instruments && bash deploy/deploy.sh >> data/cron.log 2>&1

set -e
cd "$(dirname "$0")/.."

git pull -q || echo "git pull failed, deploying with current code"

set -a; source .env; set +a
: "${FTP_HOST:?FTP_HOST not set in .env}"
: "${FTP_USER:?FTP_USER not set in .env}"
: "${FTP_PASS:?FTP_PASS not set in .env}"

# regenerate both sites + JSON API files from current DB
python3 - <<'PY'
import json, sys, yaml
sys.path.insert(0, '.')
from common import db; db.init()
from observatory.publish_observatory import run as obs
from registry.publish_registry import run as reg
print(obs()); print(reg())

# --- static JSON API ---
META = {
    "license": "CC BY 4.0 - cite the source site",
    "project": "https://github.com/tekzer0/instruments",
}

# observatory: rankings dataset
rankings = json.load(open("site_data/rankings.json", encoding="utf-8"))
rankings["meta"] = dict(META, source="https://observatory.mordo.ai",
    description="Used-GPU median sold prices joined with llama.cpp tg128 benchmarks")
json.dump(rankings, open("site/observatory/data.json", "w", encoding="utf-8"), indent=1)

# registry: tombstones + devices dataset
with db.connect() as c:
    tombs = [dict(r) for r in c.execute("SELECT slug,product,vendor,death_date,what_died,owners_left_with,summary,sources FROM tombstones ORDER BY death_date DESC")]
    devs = [dict(r) for r in c.execute("SELECT slug,name,vendor,category,protocol,local_control,degrades_how,local_api,notes,sources FROM registry_devices ORDER BY vendor,name")]
for row in tombs + devs:
    if row.get("sources"):
        try: row["sources"] = yaml.safe_load(row["sources"])
        except Exception: pass
out = {"meta": dict(META, source="https://registry.mordo.ai",
    description="Cloud-death tombstone log and device cloud-dependency registry"),
    "tombstones": tombs, "devices": devs}
json.dump(out, open("site/registry/data.json", "w", encoding="utf-8"), indent=1)
print(f"data.json: {len(tombs)} tombstones, {len(devs)} devices, {len(rankings.get('cards', []))} cards")
PY

for f in index.html data.json; do
  curl -sS -T "site/observatory/$f" "${FTP_HOST}${FTP_OBS_PATH}/$f" --user "${FTP_USER}:${FTP_PASS}" --ftp-create-dirs
  curl -sS -T "site/registry/$f"    "${FTP_HOST}${FTP_REG_PATH}/$f" --user "${FTP_USER}:${FTP_PASS}" --ftp-create-dirs
done
echo "deployed $(date -Is)"
