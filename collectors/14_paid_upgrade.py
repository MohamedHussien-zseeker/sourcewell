"""
UNIFIED PAID UPGRADE SCRIPT
Run this after subscribing to any site to collect the full source code.

Usage:
  python 14_paid_upgrade.py --site acetonity    # Upgrade Aceternity (set ACETERNITY_AUTH_COOKIE)
  python 14_paid_upgrade.py --site magicui      # Upgrade Magic UI (set MAGICUI_AUTH_COOKIE)
  python 14_paid_upgrade.py --site 21stdev      # Upgrade 21st.dev (set TWENTYFIRST_API_KEY)
  python 14_paid_upgrade.py --site unlumen      # Upgrade Unlumen (set UNLUMEN_API_KEY)
  python 14_paid_upgrade.py --site beui         # Upgrade BeUI Pro (set BEUI_LICENSE_KEY)
  python 14_paid_upgrade.py --site jiro         # Upgrade Jiro (set JIRO_SESSION_COOKIE)
  python 14_paid_upgrade.py --site landingfolio # Upgrade Landingfolio (set LANDINGFOLIO_SESSION)
  python 14_paid_upgrade.py --site all          # Upgrade all (set all env vars)
"""

import argparse
import json
import logging
import os
import re
import time
import requests
from datetime import datetime, timezone
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s',
    handlers=[logging.FileHandler('paid_upgrade.log'), logging.StreamHandler()])
logger = logging.getLogger(__name__)

ROOT = Path(os.environ.get('SOURCEWELL_ROOT', str(Path(__file__).resolve().parent.parent / 'data')))
BASE = ROOT


def upgrade_aceternity():
    cookie = os.environ.get('ACETERNITY_AUTH_COOKIE', '')
    if not cookie:
        logger.error('Set ACETERNITY_AUTH_COOKIE env var')
        return 0
    headers = {'Cookie': cookie, 'User-Agent': 'Mozilla/5.0'}
    r = requests.get('https://ui.aceternity.com/registry.json', headers=headers, timeout=15)
    items = r.json().get('items', [])
    count = 0
    for item in items:
        name = item['name']
        resp = requests.get(f'https://ui.aceternity.com/registry/{name}.json', headers=headers, timeout=20)
        if resp.status_code == 200:
            data = resp.json()
            files = data.get('files', [])
            if files:
                comp_dir = BASE / 'ui.aceternity' / 'components' / name
                comp_dir.mkdir(parents=True, exist_ok=True)
                for f in files:
                    path, content = f.get('path', ''), f.get('content', '')
                    if path and content:
                        (comp_dir / path.split('/')[-1]).write_text(content, encoding='utf-8')
                        count += 1
        time.sleep(0.2)
    return count


def upgrade_magicui():
    cookie = os.environ.get('MAGICUI_AUTH_COOKIE', '')
    if not cookie:
        logger.error('Set MAGICUI_AUTH_COOKIE env var')
        return 0
    headers = {'Cookie': cookie, 'User-Agent': 'Mozilla/5.0'}
    r = requests.get('https://magicui.design/registry.json', headers=headers, timeout=15)
    items = r.json().get('items', [])
    count = 0
    for item in items:
        name = item['name']
        resp = requests.get(f'https://magicui.design/r/{name}.json', headers=headers, timeout=20)
        if resp.status_code == 200:
            data = resp.json()
            for f in data.get('files', []):
                path, content = f.get('path', ''), f.get('content', '')
                if path and content:
                    comp_dir = BASE / 'magic-ui' / 'components' / name
                    comp_dir.mkdir(parents=True, exist_ok=True)
                    (comp_dir / path.split('/')[-1]).write_text(content, encoding='utf-8')
                    count += 1
        time.sleep(0.2)
    return count


def upgrade_21stdev():
    api_key = os.environ.get('TWENTYFIRST_API_KEY', '')
    if not api_key:
        logger.error('Set TWENTYFIRST_API_KEY env var')
        return 0
    headers = {'x-api-key': api_key, 'Content-Type': 'application/json'}
    
    # Get component list via MCP search
    queries = ['button', 'card', 'hero', 'form', 'modal', 'navbar', 'sidebar', 'table',
               'animation', 'text', 'input', 'select', 'checkbox', 'toggle', 'tabs',
               'accordion', 'dialog', 'tooltip', 'dropdown', 'menu', 'breadcrumb',
               'pagination', 'avatar', 'badge', 'alert', 'toast', 'calendar', 'date',
               'upload', 'chart', 'progress', 'spinner', 'skeleton', 'marquee',
               'scroll', 'parallax', 'glow', 'shimmer', 'gradient', 'glass', 'neon',
               'globe', '3d', 'shader', 'chat', 'terminal', 'code', 'editor',
               'compare', 'pricing', 'testimonial', 'feature', 'cta', 'faq',
               'footer', 'header', 'layout', 'grid', 'container', 'timeline',
               'step', 'wizard', 'tree', 'file', 'search', 'filter', 'sort']
    
    all_ids = {}
    for q in queries:
        resp = requests.post('https://21st.dev/api/mcp', headers=headers, timeout=15,
            json={'jsonrpc': '2.0', 'method': 'tools/call', 'id': 1,
                  'params': {'name': 'search', 'arguments': {'query': q, 'type': 'component', 'limit': 50}}})
        if resp.status_code == 200:
            results = resp.json().get('result', {}).get('structuredContent', {}).get('results', [])
            for r in results:
                rid = r.get('id')
                if rid:
                    all_ids[rid] = r
        time.sleep(0.3)
    
    logger.info(f'Found {len(all_ids)} unique components')
    count = 0
    for comp_id, comp in list(all_ids.items()):
        resp = requests.post('https://21st.dev/api/mcp', headers=headers, timeout=15,
            json={'jsonrpc': '2.0', 'method': 'tools/call', 'id': 1,
                  'params': {'name': 'get_component', 'arguments': {'id': comp_id}}})
        if resp.status_code == 200:
            text = resp.json().get('result', {}).get('content', [{}])[0].get('text', '')
            if 'limit' not in text.lower() and '## Component' in text:
                author = comp.get('author', 'unknown')
                name = comp.get('name', str(comp_id)).lower().replace(' ', '-')
                comp_dir = BASE / '21st-dev' / 'components' / author / name
                comp_dir.mkdir(parents=True, exist_ok=True)
                (comp_dir / f'{name}.md').write_text(text, encoding='utf-8')
                # Parse component and demo code
                if '## Component' in text:
                    parts = text.split('## Component')
                    code_match = re.search(r'```tsx?\n(.*?)```', parts[1], re.DOTALL)
                    if code_match:
                        (comp_dir / f'{name}.tsx').write_text(code_match.group(1).strip(), encoding='utf-8')
                        count += 1
                if '## Demo' in text:
                    demo_match = re.search(r'```tsx?\n(.*?)```', text.split('## Demo')[1], re.DOTALL)
                    if demo_match:
                        (comp_dir / f'{name}-demo.tsx').write_text(demo_match.group(1).strip(), encoding='utf-8')
        time.sleep(0.5)
    return count


def upgrade_unlumen():
    api_key = os.environ.get('UNLUMEN_API_KEY', '')
    if not api_key:
        logger.error('Set UNLUMEN_API_KEY env var')
        return 0
    headers = {'Authorization': f'Bearer {api_key}', 'User-Agent': 'Mozilla/5.0'}
    r = requests.get('https://ui.unlumen.com/r/registry.json', timeout=15)
    items = r.json().get('items', [])
    count = 0
    for item in items:
        if item.get('type') not in ('registry:ui', 'registry:lib'):
            continue
        name = item['name']
        resp = requests.get(f'https://ui.unlumen.com/r/{name}.json', headers=headers, timeout=20)
        if resp.status_code == 200:
            data = resp.json()
            for f in data.get('files', []):
                path, content = f.get('path', ''), f.get('content', '')
                if path and content:
                    comp_dir = BASE / 'unlumen-ui' / 'components' / name
                    comp_dir.mkdir(parents=True, exist_ok=True)
                    (comp_dir / path.split('/')[-1]).write_text(content, encoding='utf-8')
                    count += 1
        time.sleep(0.2)
    return count


def upgrade_beui():
    license_key = os.environ.get('BEUI_LICENSE_KEY', '')
    if not license_key:
        logger.error('Set BEUI_LICENSE_KEY env var')
        return 0
    # BeUI uses Polar license - check their docs for API endpoint
    logger.info('BeUI Pro uses Polar license. Check https://pro.beui.dev for API docs.')
    return 0


def upgrade_jiro():
    cookie = os.environ.get('JIRO_SESSION_COOKIE', '')
    if not cookie:
        logger.error('Set JIRO_SESSION_COOKIE env var')
        return 0
    headers = {'Cookie': cookie, 'User-Agent': 'Mozilla/5.0'}
    # Jiro doesn't have a public API - need to scrape pages
    logger.info('Jiro requires browser-based collection. Use Playwright with session cookie.')
    return 0


def upgrade_landingfolio():
    session = os.environ.get('LANDINGFOLIO_SESSION', '')
    if not session:
        logger.error('Set LANDINGFOLIO_SESSION env var')
        return 0
    headers = {'Cookie': session, 'User-Agent': 'Mozilla/5.0'}
    # Check if there's a pro templates API
    r = requests.get('https://s3.landingfolio.com/inspiration?category=landing-page&page=1', headers=headers, timeout=15)
    if r.status_code == 200:
        data = r.json()
        count = 0
        for item in data:
            item_id = item.get('_id', '')
            title = item.get('title', '').lower().replace(' ', '-')
            comp_dir = BASE / 'landingfolio' / 'templates' / title[:50]
            comp_dir.mkdir(parents=True, exist_ok=True)
            # Check for source code field
            source = item.get('source', item.get('code', ''))
            if source:
                (comp_dir / f'{title}.html').write_text(source, encoding='utf-8')
                count += 1
        return count
    return 0


UPGRADERS = {
    'acetonity': upgrade_aceternity,
    'magicui': upgrade_magicui,
    '21stdev': upgrade_21stdev,
    'unlumen': upgrade_unlumen,
    'beui': upgrade_beui,
    'jiro': upgrade_jiro,
    'landingfolio': upgrade_landingfolio,
}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--site', required=True, choices=list(UPGRADERS.keys()) + ['all'])
    args = parser.parse_args()

    if args.site == 'all':
        total = 0
        for name, fn in UPGRADERS.items():
            logger.info(f'Upgrading {name}...')
            count = fn()
            logger.info(f'  {name}: {count} files upgraded')
            total += count
        logger.info(f'Total: {total} files upgraded')
    else:
        count = UPGRADERS[args.site]()
        logger.info(f'{args.site}: {count} files upgraded')


if __name__ == '__main__':
    main()
