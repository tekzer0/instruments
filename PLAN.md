# The Instruments — Build Plan
*Two autonomous instruments + the API Foundry wrapped around them. Target $2,500/mo. No YouTube, no Amazon, no customers. Date: 2026-07-10.*

## The idea in one paragraph

You build two scientific instruments that watch things nobody watches, publish themselves, and become the reference source for their subject. The free sites earn citations, sponsors, affiliate, and donations. The underlying data feeds become paid APIs on marketplaces that handle every buyer, key, and invoice — machines selling machine labor. Everything runs unattended on your Proxmox; your role after build is reading a Monday digest and occasionally answering a Telegram ping. This is a venture bet, not a grind: months of $0, then compounding authority. You'd be proud of it on day one, before it earns a cent — that's the point, and it's also the honest hedge.

---

## Instrument 1 — The Local-AI Cost Observatory

**The question it answers forever:** "What should I buy to run AI at home, and what does it actually cost per token?"

**Prior art (honest):** used-GPU *price* trackers exist (Second Hand Silicon, PCPrice.watch, ResalePrices). None pair price with inference performance. The moat is the joined metric nobody computes:

- **tokens/sec per dollar** (by model size and quant — 7B/13B/70B)
- **VRAM per dollar**, **watts per token**, whole-rig cost curves (multi-GPU, Macs, mini-PCs — not just cards)
- price trend + "buy now or wait" momentum per card

**Data pipeline (all cron):**
1. **Sold prices:** SoldComps API (free tier), r/hardwareswap parsing later, backup scraper later.
2. **Performance:** community llama.cpp/vLLM benchmark results, normalized, flagged-for-review when implausible. Your own rig contributes reference benchmarks — the calibration standard.
3. **Join + publish:** static site regenerates nightly. If a scraper dies, the site serves last-good data and Telegram pings — nothing wrong ever publishes silently.

## Instrument 2 — The Cloud-Death Registry

**The question it answers forever:** "Will this device still work when the company loses interest?"

**Prior art (honest):** blog listicles and scattered forum wisdom. No maintained structured registry exists anywhere.

**Two halves:**
1. **The Registry:** every smart-home/IoT device, scored: works fully local / degrades / bricks without cloud; protocol; local API; firmware lockdown history. Public submissions **via GitHub PRs only** (self-moderating — no inbox).
2. **The Tombstone Log:** the permanent record of every cloud shutdown that bricked hardware, with dates, what died, and what owners were left holding. Watchers monitor news feeds; candidate events queue for one-tap confirm. Every future IoT obituary in the press cites you.

## The Foundry — how the money side works

**Layer 1 — the reference sites (months 1+):** passive sponsor slots, affiliate links on Observatory listings, Ko-fi. No ad network initially; credibility first.

**Layer 2 — paid APIs (months 3+):** Observatory feed (price/perf history) and Registry feed (device local-capability lookup) on API marketplaces — APILayer (85% revenue share), Zyla API Hub, paid Apify actors. Marketplaces own the customer entirely.

**Layer 3 — dataset licensing (months 6+):** historical datasets on Datarade/AWS Data Exchange. Slow, occasional, larger checks.

**Foundry expansion:** any weekend, a new standalone API joins the portfolio. Each is a small bet; the infrastructure is already built after the first two.

## Maintenance design (the "I'll forget" problem, solved structurally)

- Nothing requires remembering. The system holds all state and initiates all contact.
- Monday digest: traffic, revenue, scraper health, pending confirmations. Silence from you = everything keeps running.
- Telegram pings only for: anomaly, tombstone confirm, scraper fix. Ignorable for weeks — sites serve last-good data, queues wait.
- Real floor: **~1–2 hrs/week average**, lumpy.

## Build schedule (~10 weeks)

- **Wk 1–2:** shared plumbing — scraper framework, DB, site generator, Telegram bot, digest, health checks. ✓ DONE 2026-07-10
- **Wk 3–5:** Observatory — price ingestion ✓, benchmark harvester ✓, join ✓, real site design, more sources.
- **Wk 6–7:** Registry — schema ✓, tombstone backfill ✓ (needs source verification), GitHub submission flow + CI.
- **Wk 8:** launch posts: r/LocalLLaMA, r/homeassistant, r/selfhosted, Show HN. The one marketing act.
- **Wk 9–10:** APIs metered, documented, listed. Sponsor page up.

**Costs:** two domains (~$20/yr), Cloudflare free tier, SoldComps free tier. Everything else runs on owned hardware.

## Revenue honesty

| Phase | Realistic |
|---|---|
| Months 0–3 | $0. Authority-building. |
| Months 4–8 | $50–400/mo — Ko-fi, first affiliate, first sponsor, first API trickle. |
| Months 9–15 | $300–1,200/mo if either instrument becomes the default citation in its niche. |
| Months 15–24 | $1,000–3,000/mo — sponsors scale with authority, API/data sales compound. |

Wide variance: could stall at $200/mo, could blow past $2,500 if one instrument becomes infrastructure. The pride floor, unlike the money floor, is guaranteed.

**Kill criteria:** Observatory <5k visits/mo at month 9 → coasts, stop investing. Registry never killed — costs nothing, value cumulative. Foundry APIs individually retired if $0 for 6 months.

## Why this survives platforms

No YouTube rules, no Amazon fees, no algorithm. The instruments live on owned hardware behind Cloudflare; marketplaces are interchangeable sales counters, not landlords. The dataset itself — years of joined price/perf history, the complete tombstone record — is the asset, and it appreciates with time regardless of what any platform does.
