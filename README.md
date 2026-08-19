# Sourcewell

A **design-source collector + offline gallery builder**. You run the collectors
against the design libraries you're licensed to use; they download the real
source files into `./data/`, then the builder turns that into a single-file
searchable gallery you run locally. No cloud, no bundled third-party content, no
accounts baked in.

> **Public repo, zero personal data.** This repository contains only scripts and
> documentation — no API keys, no scraped data, no personal paths. Every
> credential the tools need is read from environment variables / a local `.env`.

## What's in here
- `collectors/` — 13 Python collectors for: Aura, Magic UI, Origin UI,
  Aceternity, Unlumen, 21st.dev, TasteSkill, UI Skills, Jiro, Landingfolio,
  BeUI Pro, and a multi-site metadata scraper.
- `build/build_catalog.py` — scans `./data/` → emits `build/gallery/data.js`
- `build/gallery/index.html` — offline viewer (loads `data.js`)
- `run_all.py` — optional orchestrator that runs every collector in sequence
- `AUTH_GUIDE.md` — **how to sign in / get keys for each source**

**No scraped data is committed to this repo.** You collect your own.

## Quick start
```bash
pip install -r requirements.txt
cp .env.example .env          # add the keys for the sources you want
python run_all.py             # or run collectors/XX_*.py individually
python build/build_catalog.py
python -m http.server 8000
# open http://localhost:8000/build/gallery/index.html
```

## Configuration (all via env / `.env`)
| Variable | Used by | Purpose |
|---|---|---|
| `SOURCEWELL_ROOT` | all collectors | where collected data is written (default `./data`) |
| `SOURCEWELL_DATA` | builder | where the builder reads (default `./data`) |
| `SOURCEWELL_BUILD` | builder | where `data.js` is written (default `./build/gallery`) |
| `AURA_SUPABASE_URL` / `AURA_SUPABASE_ANON_KEY` | Aura | Aura's public API (anon key optional, see AUTH_GUIDE) |
| `TWENTYFIRST_API_KEY` | 21st.dev | 21st.dev API key (free tier available) |
| `ACETERNITY_AUTH_COOKIE` | Aceternity | *optional*, unlocks premium |
| `MAGICUI_AUTH_COOKIE` | Magic UI | *optional*, unlocks premium |
| `UNLUMEN_API_KEY` | Unlumen | *optional*, unlocks Pro |
| `BEUI_LICENSE_KEY` | BeUI Pro | *optional*, unlocks source |
| `JIRO_SESSION_COOKIE` | Jiro | *optional*, unlocks source |
| `LANDINGFOLIO_SESSION` | Landingfolio | *optional*, unlocks source |

See **`AUTH_GUIDE.md`** for step-by-step instructions on obtaining each one.

## How authentication works (the independent design)
- **Open / free sources** (Origin UI, Magic UI free, Aceternity free, Unlumen
  free, TasteSkill, UI Skills) need **no login** — just run the collector.
- **Sites with a free account** (21st.dev, Aura) need a key you generate in your
  own account. You paste it into `.env`; the script never logs in for you, never
  stores it permanently, never shares it.
- **Paid-only sources** (Jiro, Landingfolio, BeUI Pro) collect metadata without
  a license, and *only* pull source code if you supply your own purchased
  license/session. Without it, those collectors safely skip the paywalled part.
- **Nothing is hard-coded.** The only baked-in values are public API base URLs
  (e.g. `magicui.design`) and Aura's public Supabase project URL, which you can
  override with `AURA_SUPABASE_URL`.

## Legal / licensing
Collected material belongs to its owners and may be **copyrighted or behind
paid licenses**. See `NOTICE`. Collect only what you are licensed to use, and do
not redistribute downloaded material. The open-source libraries carry their own
upstream licenses — keep their notices.

This repo is provided as-is, no warranty.
