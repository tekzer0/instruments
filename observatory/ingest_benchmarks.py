"""llama-bench ingestion.

Drop raw llama-bench output (.txt/.md) into data/inbox_benchmarks/ — pasted from
your own runs, GitHub discussions, or r/LocalLLaMA posts. First line may name the
GPU explicitly:  `# gpu: rtx 3090`  (otherwise we try to match a card alias
anywhere in the file, e.g. from the device line llama-bench prints).

Parses the standard llama-bench markdown table:
| model            | size     | params | backend | ngl | test  | t/s          |
| llama 8B Q4_K_M  | 4.58 GiB | 8.03 B | CUDA    | 99  | tg128 | 55.21 ± 0.32 |

Implausible numbers get flagged (kept, excluded from rankings) — never publish
silently wrong.
"""
import glob
import os
import re

from common import config, db
from observatory import cardmap

INBOX = config.path("data/inbox_benchmarks/.keep") and os.path.join(
    config.root_dir(), "data", "inbox_benchmarks"
)
ROW = re.compile(r"^\s*\|(.+)\|\s*$")
TOKS = re.compile(r"([\d.]+)\s*(?:±|\+/-)?\s*[\d.]*\s*$")

# sanity ceilings by size class, single-node consumer hardware, tg (tokens/sec)
PLAUSIBLE_TG_MAX = {"7-8B": 300.0, "13-14B": 160.0, "30-34B": 80.0, "70B+": 40.0, "other": 400.0}


def size_class(model_label: str, params_field: str = "") -> str:
    text = f"{model_label} {params_field}".lower()
    m = re.search(r"(\d+(?:\.\d+)?)\s*b\b", text)
    if not m:
        return "other"
    p = float(m.group(1))
    if p <= 9:
        return "7-8B"
    if p <= 16:
        return "13-14B"
    if p <= 40:
        return "30-34B"
    return "70B+"


def parse_file(text: str) -> tuple[str | None, list[dict]]:
    """Returns (card_key or None, rows). Header/separator rows are skipped."""
    card_key = None
    m = re.search(r"^#\s*gpu:\s*(.+)$", text, re.MULTILINE | re.IGNORECASE)
    if m:
        card_key = cardmap.match(m.group(1))
    if not card_key:
        card_key = cardmap.match(text)

    rows = []
    for line in text.splitlines():
        mrow = ROW.match(line)
        if not mrow:
            continue
        cells = [c.strip() for c in mrow.group(1).split("|")]
        if len(cells) < 7 or set(cells[0]) <= {"-", ":", " "} or cells[0].lower() == "model":
            continue
        model, size, params, backend, _ngl, test, toks = (
            cells[0], cells[1], cells[2], cells[3], cells[4], cells[5], cells[6],
        )
        mt = TOKS.search(toks)
        if not mt:
            continue
        tok_s = float(mt.group(1))
        sc = size_class(model, params)
        flagged = 1 if (test.startswith("tg") and tok_s > PLAUSIBLE_TG_MAX[sc]) else 0
        rows.append(
            {"model_label": f"{model} ({size})", "size_class": sc, "test": test,
             "tok_s": tok_s, "backend": backend, "flagged": flagged}
        )
    return card_key, rows


def run() -> str:
    ids = cardmap.sync_catalog()
    files = sorted(glob.glob(os.path.join(INBOX, "*.txt")) + glob.glob(os.path.join(INBOX, "*.md")))
    done_dir = os.path.join(INBOX, "ingested")
    os.makedirs(done_dir, exist_ok=True)
    inserted = flagged = unmatched = 0

    for path in files:
        with open(path, encoding="utf-8", errors="replace") as f:
            text = f.read()
        card_key, rows = parse_file(text)
        if not card_key or not rows:
            unmatched += 1
            print(f"[bench] could not use {os.path.basename(path)} "
                  f"(card={card_key}, rows={len(rows)}) — leaving in inbox")
            continue
        with db.connect() as conn:
            for r in rows:
                conn.execute(
                    "INSERT INTO bench_obs "
                    "(card_id, model_label, size_class, test, tok_s, backend, source, flagged) "
                    "VALUES (?,?,?,?,?,?,?,?)",
                    (ids[card_key], r["model_label"], r["size_class"], r["test"],
                     r["tok_s"], r["backend"], os.path.basename(path), r["flagged"]),
                )
                inserted += 1
                flagged += r["flagged"]
        os.replace(path, os.path.join(done_dir, os.path.basename(path)))
    return f"inserted={inserted} flagged={flagged} unmatched_files={unmatched}"
