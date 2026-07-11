"""Standalone Cloud-Death Registry site -> site/registry/index.html
Self-contained single file (inline CSS, no JS deps) ready to upload to
registry.mordo.ai or any static host.
"""
import html
import os

import yaml

from common import config, db


def _sources_links(raw) -> str:
    if not raw:
        return ""
    urls = yaml.safe_load(raw) if isinstance(raw, str) else raw
    if not urls:
        return ""
    parts = [f'<a href="{html.escape(u)}" rel="nofollow">[{i+1}]</a>' for i, u in enumerate(urls)]
    return " ".join(parts)


def run() -> str:
    with db.connect() as conn:
        tombs = conn.execute(
            "SELECT * FROM tombstones ORDER BY death_date DESC"
        ).fetchall()
        devices = conn.execute(
            "SELECT * FROM registry_devices ORDER BY vendor, name"
        ).fetchall()

    tomb_cards = []
    for t in tombs:
        tomb_cards.append(f"""
<article class="tomb">
  <div class="tomb-head">
    <h3>{html.escape(t['product'])}</h3>
    <span class="died">&#10013; {html.escape(t['death_date'] or 'date unknown')}</span>
  </div>
  <p class="vendor">{html.escape(t['vendor'])}</p>
  <p><strong>What died:</strong> {html.escape(t['what_died'])}</p>
  <p><strong>Owners were left with:</strong> {html.escape(t['owners_left_with'] or '—')}</p>
  <p class="summary">{html.escape(t['summary'] or '')}</p>
  <p class="sources">Sources: {_sources_links(t['sources'])}</p>
</article>""")

    badge = {"full": "badge-full", "degraded": "badge-deg", "none": "badge-none"}
    dev_rows = []
    for d in devices:
        dev_rows.append(
            f"<tr><td>{html.escape(d['name'])}</td><td>{html.escape(d['vendor'] or '')}</td>"
            f"<td>{html.escape(d['protocol'] or '')}</td>"
            f"<td><span class='badge {badge.get(d['local_control'], '')}'>{html.escape(d['local_control'])}</span></td>"
            f"<td>{html.escape(d['degrades_how'] or d['local_api'] or '')}</td>"
            f"<td class='sources'>{_sources_links(d['sources'])}</td></tr>"
        )

    page = f"""<!doctype html>
<html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>The Cloud-Death Registry — which devices survive when the company loses interest</title>
<meta name="description" content="The permanent public record of smart devices bricked by cloud shutdowns, and a registry of which devices work without the cloud.">
<style>
:root {{ --bg:#0d1117; --panel:#161b22; --line:#30363d; --txt:#e6edf3; --dim:#8b949e;
         --accent:#e3b341; --full:#3fb950; --deg:#d29922; --none:#f85149; }}
* {{ box-sizing:border-box; }}
body {{ margin:0; background:var(--bg); color:var(--txt);
       font:16px/1.6 system-ui,-apple-system,Segoe UI,sans-serif; }}
.wrap {{ max-width:960px; margin:0 auto; padding:2rem 1.2rem 4rem; }}
header {{ text-align:center; padding:3rem 0 2rem; }}
header h1 {{ font-size:2.4rem; margin:0 0 .4rem; letter-spacing:.02em; }}
header h1 .skull {{ color:var(--accent); }}
header p.tag {{ color:var(--dim); font-size:1.1rem; max-width:640px; margin:0 auto; }}
h2 {{ margin:3rem 0 1rem; font-size:1.5rem; border-bottom:1px solid var(--line); padding-bottom:.5rem; }}
.tomb {{ background:var(--panel); border:1px solid var(--line); border-radius:8px;
         padding:1rem 1.2rem; margin:1rem 0; }}
.tomb-head {{ display:flex; justify-content:space-between; align-items:baseline; flex-wrap:wrap; }}
.tomb h3 {{ margin:0; font-size:1.15rem; }}
.died {{ color:var(--none); font-weight:600; white-space:nowrap; }}
.vendor {{ color:var(--dim); margin:.1rem 0 .6rem; }}
.summary {{ color:var(--dim); font-style:italic; }}
.sources, .sources a {{ color:var(--dim); font-size:.85rem; }}
.sources a {{ margin-right:.4rem; }}
table {{ border-collapse:collapse; width:100%; font-size:.95rem; }}
td,th {{ border:1px solid var(--line); padding:.5rem .7rem; text-align:left; }}
th {{ background:var(--panel); }}
.badge {{ padding:.1rem .55rem; border-radius:999px; font-size:.8rem; font-weight:700; }}
.badge-full {{ background:#12351c; color:var(--full); }}
.badge-deg  {{ background:#3a2d0c; color:var(--deg); }}
.badge-none {{ background:#4b1113; color:var(--none); }}
.cta {{ background:var(--panel); border:1px solid var(--line); border-radius:8px;
        padding:1.2rem; margin:2rem 0; text-align:center; }}
.cta a {{ color:var(--accent); font-weight:600; }}
footer {{ color:var(--dim); text-align:center; font-size:.85rem; margin-top:3rem; }}
a {{ color:var(--accent); }}
</style></head><body><div class="wrap">
<header>
  <h1><span class="skull">&#9760;</span> The Cloud-Death Registry</h1>
  <p class="tag">Will your device still work when the company loses interest?
  The permanent record of hardware killed by cloud shutdowns — and a registry of
  what actually works without one.</p>
</header>

<h2>The Tombstone Log <span style="color:var(--dim);font-size:1rem">({len(tomb_cards)} documented deaths)</span></h2>
{''.join(tomb_cards)}

<h2>The Device Registry <span style="color:var(--dim);font-size:1rem">(growing)</span></h2>
<p>Every device scored: <span class="badge badge-full">full</span> works entirely without cloud,
<span class="badge badge-deg">degraded</span> loses features,
<span class="badge badge-none">none</span> becomes a brick.</p>
<table>
<tr><th>Device</th><th>Vendor</th><th>Protocol</th><th>Local control</th><th>Details</th><th>Sources</th></tr>
{''.join(dev_rows)}
</table>

<div class="cta">
  Know a device we should score, or a death we haven't recorded?<br>
  <a href="https://github.com/tekzer0/instruments">Submit it via a pull request</a> — one small YAML file, reviewed in the open.
</div>

<footer>Data-driven, sources cited, updated automatically. No ads, no tracking.<br>
A public instrument. &#9760;</footer>
</div></body></html>"""

    out = config.path(os.path.join(config.get("SITE_DIR", "site"), "registry", "index.html"))
    with open(out, "w", encoding="utf-8") as f:
        f.write(page)
    return f"{len(tomb_cards)} tombstones, {len(dev_rows)} devices -> {out}"


if __name__ == "__main__":
    db.init()
    print(run())
