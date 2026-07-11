# The Instruments

Two autonomous data instruments + shared plumbing.
Full business plan: see `PLAN.md`.

- **Observatory** — Local-AI hardware cost index: joins used-GPU sold prices with
  community inference benchmarks → tokens/sec-per-dollar rankings. 
- **Registry** — Cloud-Death Registry: which smart devices work without the cloud,
  plus the Tombstone Log of cloud shutdowns that bricked hardware (12 events pre-seeded).

  Live at:
  Cloud-Death Registry - https://registry.mordo.ai
  Local-AI Hardware Cost Index - https://observatory.mordo.ai

## Quickstart

1. `cp .env.example .env` and fill in:
   - `TELEGRAM_BOT_TOKEN` / `TELEGRAM_CHAT_ID` — alerts + digest (leave blank → prints to stdout)
   - `SOLDCOMPS_API_KEY` — free key from https://sold-comps.com (no card needed)
2. `pip install -r requirements.txt` (just requests + pyyaml)
3. `python run.py initdb` — creates `data/instruments.db`
4. `python run.py bench` — parses llama-bench files from `data/inbox_benchmarks/`
5. `python run.py prices` — pulls sold prices (needs the SoldComps key)
6. `python run.py join && python run.py publish` — builds `site/index.html`. Open it.
7. `python run.py digest` — sends/prints the status digest
8. When happy, install the crontab: `cron/crontab.example`

## Feeding benchmarks

Run llama-bench on any machine (llama.cpp release builds include it):

    llama-bench -m model-q4_k_m.gguf -ngl 99 > bench-output.txt

Add `# gpu: <card name>` as the first line, drop the file in `data/inbox_benchmarks/`.
Community-posted llama-bench tables (r/LocalLLaMA, llama.cpp discussions) work the
same way — paste table into a .txt with the header line. Implausible numbers are
auto-flagged and excluded from rankings.

## Design rules baked in

- **Nothing publishes silently wrong**: every job records to `scraper_runs`; 3 consecutive
  failures of any job → one Telegram alert (not spam). Site always serves last-good data.
- **Nothing needs remembering**: cron runs jobs; the Monday digest tells you if anything
  needs you. Silence = healthy.
- **The dataset is the asset**: everything accumulates in SQLite on your hardware.
  Marketplaces and sites are replaceable mouths, not the organism.

## Layout

    common/        config, sqlite, telegram, health tracking
    observatory/   cards.yaml (card catalog), price + benchmark ingest, join, publish
    registry/      device schema + validator, tombstones.yaml seed, news watcher
    digest/        weekly digest
    cron/          crontab.example
    data/          db, inboxes (runtime, gitignored)
    site/          generated static output (gitignored)

## Not here yet (next sessions)

- Real site design (publish.py output is a functional ugly table — proof of life)
- r/hardwareswap + backup eBay scraper
- Registry GitHub PR flow + CI validator action
- API metering layer (Foundry phase)
