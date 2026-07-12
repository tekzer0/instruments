#!/bin/bash
# Auto-deploy fresh site builds to Hostinger via FTP after nightly publish.
# Also self-updates the code from GitHub first, so pushed improvements arrive
# automatically — no manual git pull needed on the LXC.
#
# One-time setup:
#   1. Hostinger hPanel -> Files -> FTP Accounts -> create an account.
#   2. Add to /opt/instruments/.env (gitignored, never committed):
#        FTP_HOST=ftp://ftp.mordo.ai
#        FTP_USER=youruser
#        FTP_PASS='yourpass'                # single-quote if it has special chars
#        FTP_OBS_PATH=/observatory          # relative to the FTP account root
#        FTP_REG_PATH=/registry
#        KOFI_URL=                          # optional: enables support links when set
#   3. Test:  bash deploy/deploy.sh
#   4. Cron (after the nightly publish):
#      55 5 * * * cd /opt/instruments && bash deploy/deploy.sh >> data/cron.log 2>&1

set -e
cd "$(dirname "$0")/.."

# self-update code (never fatal — a GitHub hiccup shouldn't stop a deploy)
git pull -q || echo "git pull failed, deploying with current code"

# pull FTP creds from .env
set -a; source .env; set +a
: "${FTP_HOST:?FTP_HOST not set in .env}"
: "${FTP_USER:?FTP_USER not set in .env}"
: "${FTP_PASS:?FTP_PASS not set in .env}"

# regenerate both standalone sites from current DB
python3 - <<'PY'
import sys; sys.path.insert(0, '.')
from common import db; db.init()
from observatory.publish_observatory import run as obs
from registry.publish_registry import run as reg
print(obs()); print(reg())
PY

curl -sS -T site/observatory/index.html "${FTP_HOST}${FTP_OBS_PATH}/index.html" --user "${FTP_USER}:${FTP_PASS}" --ftp-create-dirs
curl -sS -T site/registry/index.html    "${FTP_HOST}${FTP_REG_PATH}/index.html" --user "${FTP_USER}:${FTP_PASS}" --ftp-create-dirs
echo "deployed $(date -Is)"
