---
name: sourcewell
description: "Use when you need to collect real source code/components/templates from design libraries (Aura, Magic UI, Origin UI, Aceternity, Unlumen, 21st.dev, TasteSkill, UI Skills, Jiro, Landingfolio, BeUI Pro) into one local offline-searchable gallery. Covers cloning the repo, configuring per-source credentials, running collectors, and building the viewer."
version: 1.0.0
author: beblawy
license: MIT (with NOTICE redistribution restrictions on collected third-party material)
tags: [design, scraping, gallery, components, templates, collectors, web]
category: web
metadata:
  hermes:
    tags: [web, design, scraping, gallery]
---

# sourcewell

A design-source collector + offline gallery builder. You point the collectors at
the component/template libraries you're licensed to use; they download real
source into `./data/`, then the builder turns that into a single-file searchable
gallery you run locally. No cloud, no bundled third-party content, no accounts
baked in.

The full project lives at **https://github.com/MohamedHussien-zseeker/sourcewell**
(public). This skill is also vendored inside that repo as `SKILL.md` so a user
who clones it gets the instructions too.

## When to use
- User wants to gather real component/template source from multiple design
  libraries into one searchable index.
- User has (or can get) API keys / session cookies for the sources they're
  licensed to access.
- User wants an **offline** gallery (no SaaS, no uploads).

## When NOT to use
- Collecting only one library → just run that library's single collector script.
- User is not licensed to access a paid source → do not collect its paywalled
  content. Metadata-only collectors (Jiro, Landingfolio, BeUI) are fine without
  a license; source code requires the user's own purchased key.

## Setup (must run before collecting)
1. Clone / download the repo.
2. `pip install -r requirements.txt`
3. For the multi-site scraper only: `playwright install chromium`
4. `cp .env.example .env` and fill in **only** the keys the user is licensed for.

## Credentials model (independence)
- **No login required** for: Origin UI, TasteSkill, UI Skills, Magic UI (free),
  Aceternity (free), Unlumen (free), Landingfolio (metadata), Jiro (metadata),
  BeUI Pro (metadata), multi-site (metadata).
- **Free account key** for: 21st.dev (`TWENTYFIRST_API_KEY`), Aura
  (`AURA_SUPABASE_ANON_KEY`, optional — see AUTH_GUIDE.md for how to grab the
  public anon key from the browser Network tab).
- **Optional paid unlock** (only if user bought it): `ACETERNITY_AUTH_COOKIE`,
  `MAGICUI_AUTH_COOKIE`, `UNLUMEN_API_KEY`, `BEUI_LICENSE_KEY`,
  `JIRO_SESSION_COOKIE`, `LANDINGFOLIO_SESSION`.
- All values come from env / `.env`. **Nothing is hardcoded.** The only baked-in
  values are public API base URLs (e.g. `magicui.design`) and Aura's public
  Supabase project URL, which you can override with `AURA_SUPABASE_URL`.

Full per-source step-by-step: read **`AUTH_GUIDE.md`** in the repo.

## Collect (run in repo root)
```bash
# one source
python collectors/02_magicui_collector.py
python collectors/08_aura_exporter.py --limit 50   # test Aura first

# everything you're licensed for (skips collectors whose key is missing)
python run_all.py
```
Collected files land in `./data/<source>/`.

## Build & view
```bash
python build/build_catalog.py
python -m http.server 8000
# open http://localhost:8000/build/gallery/index.html
```

## Env overrides
| Variable | Default | Purpose |
|---|---|---|
| `SOURCEWELL_ROOT` | `./data` | where collectors write |
| `SOURCEWELL_DATA` | `./data` | where builder reads |
| `SOURCEWELL_BUILD` | `./build/gallery` | where `data.js` is written |

## Pitfalls
- Running a collector without its required key: 21st.dev and Aura **exit with an
  error** (by design — no silent empty runs). All others silently skip the
  paywalled part.
- `.env` and `./data/` are gitignored — never commit them.
- Aura's full HTML set is large (21k+ files). Use `--limit` to test first.
- Collected material is copyrighted / licensed. Do not redistribute it. See
  `NOTICE`.

## Verification
After a collect+build, sanity-check before telling the user it works:
```bash
python -c "import json; d=json.load(open('build/gallery/data.js'.replace('data.js','data.js')))" 2>/dev/null \
  && echo "data.js OK" || echo "data.js MISSING — run build/build_catalog.py"
ls data/ | head   # should list the sources you collected
```
