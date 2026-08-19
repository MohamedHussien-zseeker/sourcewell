#!/usr/bin/env python3
"""Sourcewell catalog builder v2 — scan REAL source files in work-Helium.

Output:
  data.js            -> window.__HELIUM__ (embedded: curated Aura subset + all code items)
  aura_full.json     -> all 21k Aura metadata (localhost-only, disk-load source)
  catalog_meta.json  -> stats for build report
Drops all metadata-only collections (no source file on disk).
"""
import os, json, re

ROOT = os.environ.get('SOURCEWELL_DATA', str(Path(__file__).resolve().parent.parent / 'data'))
OUT  = os.environ.get('SOURCEWELL_BUILD', str(Path(__file__).resolve().parent / 'gallery'))
AURA_EMBED_N = 150          # curated Aura templates embedded (with truncated code) for public link
CODE_CAP     = 12000        # max chars of code embedded per item (full kept on localhost)
HTML_EMBED_CAP = 9000       # Aura HTML embedded truncated for public link

# Collections we KEEP (have real source on disk). Everything else is dropped.
KEEP = {
    'aura':          ('aura',        'template', 'Aura'),
    'magic-ui':      ('magic-ui/components',      'component', 'Magic UI'),
    'origin-ui':     ('origin-ui/components',     'component', 'Origin UI'),
    'ui.aceternity': ('ui.aceternity/components', 'component', 'Aceternity'),
    'unlumen-ui':    ('unlumen-ui/components',    'component', 'Unlumen'),
    '21st-dev':      ('21st-dev/components',      'component', '21st.dev'),
    'hermes-engine': ('hermes-engine',           'component', 'Hermes Engine'),
    'new-test':      ('new-test',                'template',  'New Test'),
    'taste-skill':   ('taste-skill/skills',       'skill',     'Taste Skill'),
    'ui-skills':     ('ui-skills',               'skill',     'UI Skills'),
    'scripts':       ('scripts',                 'script',    'Scripts'),
}

items = []
aura_all = []   # full metadata for localhost

def read_file(p, limit=None):
    try:
        with open(p, encoding='utf-8', errors='replace') as f:
            return f.read() if limit is None else f.read(limit)
    except Exception:
        return ''

# ---------------- AURA ----------------
a = json.load(open(f'{ROOT}/aura/index.json', encoding='utf-8'))
aura_items = []
for t in a['templates']:
    sl = t.get('slug')
    if not sl: continue
    hp = f'{ROOT}/aura/templates/{sl}.html'
    if not os.path.exists(hp): continue
    rec = {
        'id': f'aura/{sl}', 'col': 'aura', 'title': t.get('title') or sl,
        'author': t.get('username') or 'aura', 'img': t.get('image_url') or '',
        'pro': bool(t.get('premium')), 'views': int(t.get('views') or 0),
        'remixes': int(t.get('forks') or 0), 'cat': t.get('category') or 'Template',
        'tags': t.get('tags') or [], 'desc': t.get('description') or '',
        'path': f'aura/templates/{sl}.html', 'lang': 'html', 'code': '',
    }
    aura_items.append(rec)
    aura_all.append(rec)   # localhost full set (no code yet)

# curated: top N by views, embed truncated code
curated = sorted(aura_items, key=lambda r: -r['views'])[:AURA_EMBED_N]
for r in curated:
    hp = f'{ROOT}/{r["path"]}'
    r['code'] = read_file(hp, HTML_EMBED_CAP)
items.extend(curated)

# ---------------- COMPONENT LIBS (tsx/ts/jsx) ----------------
def walk_tsx(colkey, folder):
    out = []
    base = f'{ROOT}/{folder}'
    if not os.path.isdir(base): return out
    for dp, _, fs in os.walk(base):
        for fn in fs:
            low = fn.lower()
            if low.endswith(('.tsx', '.ts', '.jsx')):
                fp = os.path.join(dp, fn)
                rel = os.path.relpath(fp, ROOT).replace('\\', '/')
                stem = os.path.splitext(fn)[0]
                lang = 'tsx' if low.endswith('.tsx') else ('ts' if low.endswith('.ts') else 'jsx')
                code = read_file(fp, CODE_CAP)
                out.append({
                    'id': rel, 'col': colkey, 'title': stem,
                    'author': colkey, 'img': '',
                    'pro': False, 'views': 0, 'remixes': 0, 'cat': 'Component',
                    'tags': [], 'desc': '', 'path': rel, 'lang': lang, 'code': code,
                })
    return out

for key, (folder, kind, label) in KEEP.items():
    if kind != 'component': continue
    items.extend(walk_tsx(key, folder))

# ---------------- SKILLS (md) ----------------
def walk_md(folder, colkey, label):
    out = []
    base = f'{ROOT}/{folder}'
    if not os.path.isdir(base): return out
    for dp, _, fs in os.walk(base):
        for fn in fs:
            if fn.lower().endswith('.md') and fn.lower() != 'manifest.md':
                fp = os.path.join(dp, fn)
                rel = os.path.relpath(fp, ROOT).replace('\\', '/')
                stem = os.path.splitext(fn)[0]
                code = read_file(fp, CODE_CAP)
                out.append({
                    'id': rel, 'col': colkey, 'title': stem,
                    'author': label, 'img': '', 'pro': False, 'views': 0, 'remixes': 0,
                    'cat': 'Skill', 'tags': [], 'desc': '', 'path': rel, 'lang': 'md', 'code': code,
                })
    return out

items.extend(walk_md('taste-skill/skills', 'taste-skill', 'Taste Skill'))
items.extend(walk_md('ui-skills', 'ui-skills', 'UI Skills'))

# ---------------- SCRIPTS (py) ----------------
base = f'{ROOT}/scripts'
if os.path.isdir(base):
    for fn in sorted(os.listdir(base)):
        if fn.endswith('.py'):
            fp = os.path.join(base, fn)
            rel = f'scripts/{fn}'
            items.append({
                'id': rel, 'col': 'scripts', 'title': fn, 'author': 'Scripts',
                'img': '', 'pro': False, 'views': 0, 'remixes': 0, 'cat': 'Script',
                'tags': ['python'], 'desc': '', 'path': rel, 'lang': 'python',
                'code': read_file(fp, CODE_CAP),
            })

# ---------------- NEW-TEST (html templates, no image) ----------------
base = f'{ROOT}/new-test'
if os.path.isdir(base):
    for fn in sorted(os.listdir(base)):
        if fn.lower().endswith('.html'):
            fp = os.path.join(base, fn)
            rel = f'new-test/{fn}'
            items.append({
                'id': rel, 'col': 'new-test', 'title': os.path.splitext(fn)[0],
                'author': 'New Test', 'img': '', 'pro': False, 'views': 0, 'remixes': 0,
                'cat': 'Template', 'tags': [], 'desc': '', 'path': rel, 'lang': 'html',
                'code': read_file(fp, HTML_EMBED_CAP),
            })

# ---------------- INDEXES (author / category) over embedded items ----------------
author_idx, cat_idx = {}, {}
for it in items:
    author_idx.setdefault(it['author'], []).append(it['id'])
    cat_idx.setdefault(it['cat'], []).append(it['id'])

# ---------------- COLLECTIONS META ----------------
from collections import Counter, defaultdict
from pathlib import Path
col_counter = Counter(it['col'] for it in items)
lang_counter = Counter(it['lang'] for it in items)
col_labels = {v[1]: v[2] for v in KEEP.values()}
collections = []
for key in KEEP:
    ck = key.replace('/', '.')
    n = col_counter.get(ck, 0)
    if n == 0: continue
    collections.append({'key': ck, 'label': col_labels.get(ck, ck), 'kind': KEEP[key][1],
                        'count': n, 'hasImage': ck == 'aura'})

meta = {'total': len(items), 'collections': collections,
        'langs': dict(lang_counter), 'auraFull': len(aura_all)}

# ---------------- WRITE data.js ----------------
data = {'meta': meta, 'items': items, 'authorIdx': author_idx, 'catIdx': cat_idx}
with open(f'{OUT}/data.js', 'w', encoding='utf-8') as f:
    f.write('window.__HELIUM__=')
    json.dump(data, f, separators=(',', ':'), ensure_ascii=False)
    f.write(';')

# ---------------- WRITE aura_full.json (localhost) ----------------
with open(f'{OUT}/aura_full.json', 'w', encoding='utf-8') as f:
    json.dump({'meta': {'total': len(aura_all)}, 'items': aura_all}, f,
              separators=(',', ':'), ensure_ascii=False)

# ---------------- REPORT ----------------
report = {
    'embedded_items': len(items),
    'aura_embedded': len(curated),
    'aura_full': len(aura_all),
    'component_items': sum(1 for i in items if i['lang'] in ('tsx', 'ts', 'jsx')),
    'code_items': sum(1 for i in items if i['code']),
    'collections': [(c['label'], c['count']) for c in collections],
    'langs': dict(lang_counter),
    'data_js_mb': round(os.path.getsize(f'{OUT}/data.js')/1048576, 2),
}
with open(f'{OUT}/catalog_meta.json', 'w', encoding='utf-8') as f:
    json.dump(report, f, indent=2)

print('=== BUILD REPORT ===')
print(json.dumps(report, indent=2))
