"""Static site generation — proof-of-life version.

Renders site_data/rankings.json + registry tables into site/index.html.
Deliberately ugly and framework-free: the real design pass is a later session.
If rankings.json is missing/stale, the previous site output is left untouched
(last-good-data rule).
"""
import html
import json
import os

from common import config, db


def _fmt(v, suffix=""):
    return f"{v}{suffix}" if v is not None else "—"


def run() -> str:
    src = os.path.join(config.root_dir(), "site_data", "rankings.json")
    if not os.path.exists(src):
        raise RuntimeError("no rankings.json yet — run `python run.py join` first")
    with open(src, encoding="utf-8") as f:
        data = json.load(f)

    rows = []
    for c in data["cards"]:
        p78 = c["perf"].get("7-8B", {})
        rows.append(
            "<tr>"
            f"<td>{html.escape(c['name'])}</td>"
            f"<td>{_fmt(c['median_price_usd'], ' $')}<small> ({c['price_window']}, n={c['n_price_obs']})</small></td>"
            f"<td>{_fmt(c['vram_gb'])}</td>"
            f"<td>{_fmt(p78.get('tok_s'))}</td>"
            f"<td><b>{_fmt(p78.get('toks_per_100usd'))}</b></td>"
            f"<td>{_fmt(p78.get('w_per_toks'))}</td>"
            f"<td>{_fmt(c['vram_gb_per_100usd'])}</td>"
            "</tr>"
        )

    with db.connect() as conn:
        tombs = conn.execute(
            "SELECT product, vendor, death_date, what_died, owners_left_with "
            "FROM tombstones ORDER BY death_date DESC"
        ).fetchall()
    tomb_rows = [
        "<tr>"
        f"<td>{html.escape(t['product'])}</td><td>{html.escape(t['vendor'])}</td>"
        f"<td>{html.escape(t['death_date'] or '?')}</td>"
        f"<td>{html.escape(t['what_died'])}</td>"
        f"<td>{html.escape(t['owners_left_with'] or '')}</td>"
        "</tr>"
        for t in tombs
    ]

    page = f"""<!doctype html><html><head><meta charset=\"utf-8\">
<title>The Instruments — proof of life</title>
<style>body{{font-family:system-ui;margin:2rem;max-width:1100px}}
table{{border-collapse:collapse;width:100%;margin:1rem 0 2rem}}
td,th{{border:1px solid #ccc;padding:.4rem .6rem;text-align:left}}
th{{background:#f4f4f4}} small{{color:#777}}</style></head><body>
<h1>Local-AI Cost Observatory <small>(generated {data['generated_at']} UTC)</small></h1>
<p>Ranked by <b>tokens/sec per $100</b> (7–8B class, best community tg result, median sold price).</p>
<table><tr><th>Card</th><th>Median sold price</th><th>VRAM GB</th>
<th>tg tok/s (7-8B)</th><th>tok/s per $100</th><th>W per tok/s</th><th>VRAM GB per $100</th></tr>
{''.join(rows)}</table>
<h1>Cloud-Death Registry — Tombstone Log</h1>
<table><tr><th>Product</th><th>Vendor</th><th>Died</th><th>What died</th><th>Owners left with</th></tr>
{''.join(tomb_rows)}</table>
<p><small>Proof-of-life build. Data accumulates in instruments.db.</small></p>
</body></html>"""

    out = config.path(os.path.join(config.get("SITE_DIR", "site"), "index.html"))
    with open(out, "w", encoding="utf-8") as f:
        f.write(page)
    return f"{len(rows)} cards, {len(tomb_rows)} tombstones -> {out}"
