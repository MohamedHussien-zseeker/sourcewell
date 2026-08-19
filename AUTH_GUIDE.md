# Sourcewell — Authentication & Key Guide

Every collector reads its credentials from environment variables (or a local
`.env` file). **None are stored in the repo, and none are required to run the
open/free collectors.** Below is exactly what each source needs and how to get it.

---

## A. No login required (just run it)

These work out of the box with no credentials:

| Source | Collector | Notes |
|---|---|---|
| Origin UI | `04_originui_collector.py` | Pulls from public GitHub `cosscom/coss` |
| TasteSkill | `10_tasteskill_collector.py` | Public GitHub `Leonxlnx/taste-skill` |
| UI Skills | `11_uiskills_collector.py` | Public GitHub `ibelick/ui-skills` + others |
| Magic UI (free) | `02_magicui_collector.py` | Free components; no key needed |
| Aceternity (free) | `01_aceternity_collector.py` | Free components; no key needed |
| Unlumen (free) | `05_unlumen_collector.py` | Free components; no key needed |
| Landingfolio | `13_landingfolio_collector.py` | Metadata only, no login |
| Jiro | `07_jiro_collector.py` | Metadata only, no login |
| BeUI Pro | `06_beui_collector.py` | Metadata only, no login |
| Multi-site | `15_multisite_collector.py` | Public metadata; needs `playwright install chromium` |

---

## B. Needs a free account key

### 21st.dev — `TWENTYFIRST_API_KEY`
1. Sign up at **21st.dev** (free tier exists).
2. Go to **Settings → API Keys** and create a key.
3. Add to `.env`: `TWENTYFIRST_API_KEY=your_key_here`
4. Run: `python collectors/03_21stdev_collector.py`

### Aura — `AURA_SUPABASE_ANON_KEY` (optional)
Aura's templates are served from a public Supabase endpoint. The anon key is
embedded in the site's network requests, so it is **not a secret** — but to keep
the repo clean we don't ship it. To collect Aura:
1. Open **aura.build** in a browser, press **F12 → Network**.
2. Reload, find any request to `*.supabase.co`, copy the `apikey` header value.
3. Add to `.env`: `AURA_SUPABASE_ANON_KEY=that_value`
   (optional) `AURA_SUPABASE_URL=https://hoirqrkdgbmvpwutwuwj.supabase.co`
4. Run: `python collectors/08_aura_exporter.py --limit 50` (test first)

---

## C. Optional — unlocks *paid* source (only if you bought it)

Set these **only** if you own a valid license. Without them, the collector
gracefully collects free/metadata only.

| Source | Variable | How to get it |
|---|---|---|
| Aceternity premium | `ACETERNITY_AUTH_COOKIE` | Log into ui.aceternity.com, copy the `cookie` header from a Network request |
| Magic UI premium | `MAGICUI_AUTH_COOKIE` | Same, from magicui.design |
| Unlumen Pro | `UNLUMEN_API_KEY` | From your Unlumen Polar account |
| BeUI Pro source | `BEUI_LICENSE_KEY` | From your BeUI Polar purchase |
| Jiro source | `JIRO_SESSION_COOKIE` | Log into jiro.build, copy session cookie |
| Landingfolio source | `LANDINGFOLIO_SESSION` | Log into landingfolio.com, copy session cookie |

> **Cookie safety:** a session cookie is like a password. Paste it only into your
> local `.env` (which is gitignored), never into the repo or anywhere shared.

---

## D. Running everything
```bash
# fill .env with whichever keys above you have
cp .env.example .env
python run_all.py          # runs all collectors; skips any whose key is missing
python build/build_catalog.py
```
Collected files land in `./data/<source>/`. The builder reads them and produces
`build/gallery/data.js` for the viewer.
