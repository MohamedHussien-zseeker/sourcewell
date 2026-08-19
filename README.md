# Sourcewell

A private, self-hosted **design-source collector + searchable gallery**.

You point the collectors at the component/template libraries you're licensed to
use, they download the real source files into `./data/`, then the builder turns
that into a single-file searchable gallery you run locally. No accounts, no
cloud, no bundled third-party content.

## What's in here
- `collectors/` — 13 Python scripts that pull real source from design libraries
  (Aura, Magic UI, Origin UI, Aceternity, Unlumen, 21st.dev, TasteSkill, UI
  Skills, Jiro, Landingfolio, BeUI, Framer, etc.)
- `build/build_catalog.py` — scans `./data/` and emits `build/gallery/data.js`
- `build/gallery/index.html` — the offline viewer (loads `data.js`)
- `run_all.py` — optional orchestrator that runs every collector in sequence

**No scraped data is committed to this repo.** You collect your own.

## Setup
```bash
pip install -r requirements.txt
cp .env.example .env   # fill in the keys for the sources you want
# optional: playwright for the multisite collector
playwright install chromium
```

## Collect
```bash
# one source
python collectors/02_magicui_collector.py
python collectors/08_aura_exporter.py --limit 50   # test first

# everything (respects .env keys)
python run_all.py
```
Collected files land in `./data/<source>/`.

## Build & view
```bash
python build/build_catalog.py
# from repo root:
python -m http.server 8000
# open http://localhost:8000/build/gallery/index.html
```

## Configuration
- `SOURCEWELL_ROOT` — where collectors write (default `./data`)
- `SOURCEWELL_DATA` — where the builder reads (default `./data`)
- `SOURCEWELL_BUILD` — where `data.js` is written (default `./build/gallery`)
- Keys are read from environment / `.env` — **none are baked into the code.**

## Legal / licensing
This tool collects content that may be **copyrighted or behind paid licenses**
(Aura, Jiro, Landingfolio, BeUI, Framer, premium tiers of the OSS libs, etc.).
See `NOTICE`. Collect only what you are licensed to use, and do not redistribute
downloaded material. The open-source component libraries (Magic UI, Origin UI,
Aceternity free tier, Unlumen, 21st.dev free tier, TasteSkill, UI Skills) carry
their own upstream licenses — keep their notices.

This repository is **PRIVATE**. Do not make it public or share the collected
material.
