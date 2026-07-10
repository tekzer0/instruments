"""Registry data validation + DB sync.

- Loads tombstones.yaml into the tombstones table (upsert by slug).
- Validates and loads device YAML files from registry/devices/*.yaml
  (this is the future GitHub-PR submission format — CI will run this same
  validator on every PR, so contributors get robot feedback, not your time).
"""
import glob
import os

import yaml

from common import db

DEVICE_REQUIRED = {"slug", "name", "vendor", "protocol", "local_control"}
LOCAL_CONTROL_VALUES = {"full", "degraded", "none"}
TOMB_REQUIRED = {"slug", "product", "vendor", "what_died"}


def _load_yaml(path: str):
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def validate_device(d: dict, origin: str) -> list[str]:
    errs = []
    missing = DEVICE_REQUIRED - set(d or {})
    if missing:
        errs.append(f"{origin}: missing {sorted(missing)}")
        return errs
    if d["local_control"] not in LOCAL_CONTROL_VALUES:
        errs.append(f"{origin}: local_control must be one of {sorted(LOCAL_CONTROL_VALUES)}")
    if d["local_control"] == "degraded" and not d.get("degrades_how"):
        errs.append(f"{origin}: 'degraded' requires degrades_how")
    if not d.get("sources"):
        errs.append(f"{origin}: at least one source URL required")
    return errs


def run() -> str:
    here = os.path.dirname(__file__)
    errors: list[str] = []

    # tombstones
    tombs = _load_yaml(os.path.join(here, "tombstones.yaml")) or []
    for t in tombs:
        missing = TOMB_REQUIRED - set(t)
        if missing:
            errors.append(f"tombstones:{t.get('slug', '?')}: missing {sorted(missing)}")
    if not errors:
        with db.connect() as conn:
            for t in tombs:
                conn.execute(
                    "INSERT INTO tombstones (slug, product, vendor, death_date, what_died, "
                    "owners_left_with, summary, sources) VALUES (?,?,?,?,?,?,?,?) "
                    "ON CONFLICT(slug) DO UPDATE SET product=excluded.product, "
                    "vendor=excluded.vendor, death_date=excluded.death_date, "
                    "what_died=excluded.what_died, owners_left_with=excluded.owners_left_with, "
                    "summary=excluded.summary, sources=excluded.sources",
                    (t["slug"], t["product"], t["vendor"], t.get("death_date"),
                     t["what_died"], t.get("owners_left_with"), t.get("summary"),
                     yaml.safe_dump(t.get("sources")) if t.get("sources") else None),
                )

    # devices
    n_dev = 0
    for path in sorted(glob.glob(os.path.join(here, "devices", "*.yaml"))):
        d = _load_yaml(path)
        errs = validate_device(d, os.path.basename(path))
        if errs:
            errors.extend(errs)
            continue
        with db.connect() as conn:
            conn.execute(
                "INSERT INTO registry_devices (slug, name, vendor, category, protocol, "
                "local_control, degrades_how, local_api, notes, sources, updated_at) "
                "VALUES (?,?,?,?,?,?,?,?,?,?,datetime('now')) "
                "ON CONFLICT(slug) DO UPDATE SET name=excluded.name, vendor=excluded.vendor, "
                "category=excluded.category, protocol=excluded.protocol, "
                "local_control=excluded.local_control, degrades_how=excluded.degrades_how, "
                "local_api=excluded.local_api, notes=excluded.notes, sources=excluded.sources, "
                "updated_at=datetime('now')",
                (d["slug"], d["name"], d["vendor"], d.get("category"), d["protocol"],
                 d["local_control"], d.get("degrades_how"), d.get("local_api"),
                 d.get("notes"), yaml.safe_dump(d.get("sources"))),
            )
        n_dev += 1

    if errors:
        raise RuntimeError("validation failed:\n" + "\n".join(errors))
    return f"tombstones={len(tombs)} devices={n_dev}"
