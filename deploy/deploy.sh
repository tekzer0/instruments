#!/bin/bash
# Auto-deploy fresh site builds to Hostinger via FTP after nightly publish.
#
# One-time setup:
#   1. Hostinger hPanel -> Files -> FTP Accounts -> create an account
#      (scope it to the mordo.ai subdomain web roots if possible).
#   2. Add to /opt/instruments/.env (gitignored, never committed):
#        FTP_HOST=ftp://ftp.yourhostingerhost.com
#        FTP_USER=youruser
#        FTP_PASS=yourpass
#        FTP_OBS_PATH=/public_html/observatory   # web root for observatory.mordo.ai
#        FTP_REG_PATH=/public_html/registry      # web root for registry.mordo.ai
#      (check the real paths in hPanel's file manager — subdomain roots vary)
#   3. Test:  bash deploy/deploy.sh
#   4. Cron (after the nightly publish):
#      55 5 * * * cd /opt/instruments && bash deploy/deploy.sh >> data/cron.log 2>&1

set -e
cd "$(dirname "$0")/.."

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
