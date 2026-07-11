#!/bin/bash
# Auto-deploy fresh site builds to the mordo.ai web container.
# One-time setup on the instruments LXC (.108):
#   1. ssh-keygen -t ed25519 -N "" -f ~/.ssh/id_ed25519     (if no key yet)
#   2. ssh-copy-id root@WEB_HOST                            (or the right user)
#   3. Fill in the two variables below.
#   4. Test:  bash deploy/deploy.sh
#   5. Cron (add after the nightly publish line, e.g. 55 5 * * *):
#      55 5 * * * cd /opt/instruments && bash deploy/deploy.sh >> data/cron.log 2>&1

WEB_HOST="CHANGE_ME"                  # IP or hostname of the container serving mordo.ai
WEB_USER="root"
OBS_PATH="CHANGE_ME"                  # web root for observatory.mordo.ai
REG_PATH="CHANGE_ME"                  # web root for registry.mordo.ai

set -e
cd "$(dirname "$0")/.."

# regenerate both standalone sites from current DB
python3 - <<'PY'
import sys; sys.path.insert(0, '.')
from common import db; db.init()
from observatory.publish_observatory import run as obs
from registry.publish_registry import run as reg
print(obs()); print(reg())
PY

scp -q site/observatory/index.html "${WEB_USER}@${WEB_HOST}:${OBS_PATH}/index.html"
scp -q site/registry/index.html    "${WEB_USER}@${WEB_HOST}:${REG_PATH}/index.html"
echo "deployed $(date -Is)"
