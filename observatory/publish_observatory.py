"""Standalone Local-AI Cost Observatory site -> site/observatory/index.html
Self-contained single file (inline CSS + tiny vanilla-JS sort), ready to upload
to observatory.mordo.ai. Sister design to the Cloud-Death Registry.
"""
import html
import json
import os

from common import config, db


def _fmt(v, dash="—"):
    return dash if v is None else v


def run() -> str:
    src = os.path.join(config.root_dir(), "site_data", "rankings.json")
    with open(src, encoding="utf-8") as f:
        data = json.load(f)

    rows = []
    best_value = None
    for c in data["cards"]:
        p = c["perf"].get("7-8B", {})
        val = p.get("toks_per_100usd")
        if val and (best_value is None or val > best_value):
            best_value = val
    for c in data["cards"]:
        p = c["perf"].get("7-8B", {})
        val = p.get("toks_per_100usd")
        crown = " \U0001f3c6" if val and val == best_value else ""
        price = c["median_price_usd"]
        rows.append(
            f"<tr>"
            f"<td data-v=\"{html.escape(c['name'])}\">{html.escape(c['name'])}{crown}</td>"
            f"<td data-v=\"{price or 10**9}\">{'$'+format(price, ',.0f') if price else '—'}"
            f"<small> n={c['n_price_obs']}, {c['price_window']}</small></td>"
            f"<td data-v=\"{c['vram_gb'] or 0}\">{_fmt(c['vram_gb'])}</td>"
            f"<td data-v=\"{p.get('tok_s') or 0}\">{_fmt(p.get('tok_s'))}</td>"
            f"<td data-v=\"{val or 0}\" class=\"hl\">{_fmt(val)}</td>"
            f"<td data-v=\"{p.get('w_per_toks') or 10**9}\">{_fmt(p.get('w_per_toks'))}</td>"
            f"<td data-v=\"{c['vram_gb_per_100usd'] or 0}\">{_fmt(c['vram_gb_per_100usd'])}</td>"
            f"</tr>"
        )

    with db.connect() as conn:
        n_prices = conn.execute("SELECT COUNT(*) c FROM price_obs").fetchone()["c"]
        n_bench = conn.execute("SELECT COUNT(*) c FROM bench_obs WHERE flagged=0").fetchone()["c"]

    kofi = config.get("KOFI_URL")
    support_html = (
        f'<div class="cta">If this instrument saved you money or research time, '
        f'<a href="{kofi}">you can fuel it here</a> — it runs on one tiny container and stubbornness.</div>'
        if kofi else ""
    )

    page = f"""<!doctype html>
<html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>The Local-AI Cost Observatory — tokens per second per dollar, from real sold prices</title>
<meta name="description" content="What does it actually cost to run AI at home? Live used-GPU market prices joined with community inference benchmarks: tokens/sec per $100, watts per token, VRAM per dollar.">
<style>
:root {{ --bg:#0d1117; --panel:#161b22; --line:#30363d; --txt:#e6edf3; --dim:#8b949e;
         --accent:#58a6ff; --gold:#e3b341; --green:#3fb950; }}
* {{ box-sizing:border-box; }}
body {{ margin:0; background:var(--bg); color:var(--txt);
       font:16px/1.6 system-ui,-apple-system,Segoe UI,sans-serif; }}
.wrap {{ max-width:1080px; margin:0 auto; padding:2rem 1.2rem 4rem; }}
header {{ text-align:center; padding:3rem 0 1.5rem; }}
header h1 {{ font-size:2.3rem; margin:0 0 .4rem; }}
header h1 .tele {{ color:var(--accent); }}
header p.tag {{ color:var(--dim); font-size:1.1rem; max-width:680px; margin:0 auto; }}
.stats {{ display:flex; gap:1rem; justify-content:center; flex-wrap:wrap; margin:1.5rem 0; }}
.stat {{ background:var(--panel); border:1px solid var(--line); border-radius:8px;
         padding:.6rem 1.2rem; text-align:center; }}
.stat b {{ display:block; font-size:1.4rem; color:var(--accent); }}
.stat span {{ color:var(--dim); font-size:.85rem; }}
h2 {{ margin:2.5rem 0 1rem; font-size:1.4rem; border-bottom:1px solid var(--line); padding-bottom:.5rem; }}
table {{ border-collapse:collapse; width:100%; font-size:.95rem; }}
td,th {{ border:1px solid var(--line); padding:.5rem .7rem; text-align:left; white-space:nowrap; }}
th {{ background:var(--panel); cursor:pointer; user-select:none; }}
th:hover {{ color:var(--accent); }}
th .arrow {{ color:var(--accent); font-size:.8rem; }}
td.hl {{ color:var(--gold); font-weight:700; }}
td small {{ color:var(--dim); display:block; font-size:.75rem; }}
tr:hover td {{ background:#161b22; }}
.method {{ background:var(--panel); border:1px solid var(--line); border-radius:8px; padding:1rem 1.4rem; }}
.method p {{ margin:.5rem 0; }}
.cta {{ background:var(--panel); border:1px solid var(--line); border-radius:8px;
        padding:1.2rem; margin:2rem 0; text-align:center; }}
a {{ color:var(--accent); }}
footer {{ color:var(--dim); text-align:center; font-size:.85rem; margin-top:3rem; }}
.scroll {{ overflow-x:auto; }}
</style></head><body><div class="wrap">
<header>
  <h1><span class="tele">&#128301;</span> The Local-AI Cost Observatory</h1>
  <p class="tag">What does it actually cost to run AI at home? Real sold prices from the
  used market, joined with community inference benchmarks. The metric that matters:
  <b>tokens per second, per $100 spent.</b></p>
</header>

<div class="stats">
  <div class="stat"><b>{n_prices:,}</b><span>sold-price observations</span></div>
  <div class="stat"><b>{len(rows)}</b><span>cards tracked</span></div>
  <div class="stat"><b>{n_bench}</b><span>benchmark results</span></div>
  <div class="stat"><b>{data['generated_at'][:10]}</b><span>last updated (UTC)</span></div>
</div>

<h2>Value Rankings — 7–8B class models <span style="color:var(--dim);font-size:.9rem">(click headers to sort)</span></h2>
<div class="scroll">
<table id="rank">
<thead><tr>
  <th>Card</th><th>Median sold price</th><th>VRAM GB</th>
  <th>Gen speed (tok/s)</th><th>tok/s per $100 ▾</th><th>W per tok/s</th><th>VRAM GB per $100</th>
</tr></thead>
<tbody>
{''.join(rows)}
</tbody></table>
</div>

<h2>Methodology <span style="color:var(--dim);font-size:.9rem">(the honest part)</span></h2>
<div class="method">
<p><b>Prices</b> are medians of real completed/sold used-market listings (currently eBay
sold data), sanity-filtered, deduplicated by listing ID. <i>n</i> is the sample size;
the window shows whether the median is from the last 30 days or all recorded history.</p>
<p><b>Performance</b> is the best community <code>llama-bench</code> text-generation result
(<code>tg128</code>) per card from the official llama.cpp
<a href="https://github.com/ggml-org/llama.cpp/discussions/15013">CUDA</a> and
<a href="https://github.com/ggml-org/llama.cpp/discussions/15021">ROCm</a> scoreboards —
all measured on the <b>same model</b> (Llama 2 7B Q4_0), so cards are directly comparable.
Implausible submissions are auto-flagged and excluded.</p>
<p><b>Value</b> = tok/s ÷ median price × 100. <b>Efficiency</b> = card TDP ÷ tok/s
(lower is better; power cost matters if it runs all day).</p>
<p><b>Caveats we won't hide:</b> VRAM ceilings matter more than speed if you want larger
models — a fast 10GB card can't run what a slow 24GB card can. Datacenter cards
(P100, P40, MI50, V100) need cooling and mounting work. Prices move; we re-harvest twice monthly.</p>
</div>

<div class="cta">
  Have a card we're missing, or a llama-bench run to contribute?<br>
  <a href="https://github.com/tekzer0/instruments">Send it via the GitHub repo</a> — raw
  llama-bench output is all we need.
</div>

<div class="cta" style="border-color:#3a2d0c">
  &#9760; Sister instrument: <a href="https://registry.mordo.ai">The Cloud-Death Registry</a> —
  which smart devices survive when the company loses interest.
</div>

{support_html}
<footer>Data-driven, sources cited, updated automatically. No ads, no tracking.<br>
A public instrument. &#128301;</footer>
</div>
<script>
document.querySelectorAll('#rank th').forEach((th, i) => {{
  let dir = -1;
  th.addEventListener('click', () => {{
    const tb = document.querySelector('#rank tbody');
    const rows = [...tb.querySelectorAll('tr')];
    rows.sort((a, b) => {{
      const av = a.cells[i].dataset.v, bv = b.cells[i].dataset.v;
      const an = parseFloat(av), bn = parseFloat(bv);
      const cmp = (!isNaN(an) && !isNaN(bn)) ? an - bn : av.localeCompare(bv);
      return cmp * dir;
    }});
    dir *= -1;
    document.querySelectorAll('#rank th .arrow').forEach(s => s.remove());
    const s = document.createElement('span');
    s.className = 'arrow'; s.textContent = dir === 1 ? ' ▴' : ' ▾';
    th.appendChild(s);
    rows.forEach(r => tb.appendChild(r));
  }});
}});
</script>
</body></html>"""

    out = config.path(os.path.join(config.get("SITE_DIR", "site"), "observatory", "index.html"))
    with open(out, "w", encoding="utf-8") as f:
        f.write(page)
    return f"{len(rows)} cards -> {out}"
