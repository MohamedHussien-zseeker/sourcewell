"""
Aura Prompt Templates Exporter
Exports all templates from https://www.aura.build/ Supabase API
Full HTML source code included in each template.
"""

import json
import logging
import time
import requests
from datetime import datetime, timezone
from pathlib import Path
import os

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s',
    handlers=[logging.FileHandler('aura_exporter.log'), logging.StreamHandler()])
logger = logging.getLogger(__name__)

ROOT = Path(os.environ.get('SOURCEWELL_ROOT', str(Path(__file__).resolve().parent.parent / 'data')))
BASE_DIR = ROOT / 'aura'
# Aura's Supabase project URL. This is the public anon endpoint for aura.build.
# Override with AURA_SUPABASE_URL if Aura changes it / you point at a fork.
API_URL = os.environ.get('AURA_SUPABASE_URL', 'https://hoirqrkdgbmvpwutwuwj.supabase.co')
ANON_KEY = os.environ.get('AURA_SUPABASE_ANON_KEY', '')


class AuraExporter:
    def __init__(self):
        self.headers = {'apikey': ANON_KEY, 'Authorization': f'Bearer {ANON_KEY}'}
        self.templates = []

    def fetch_all(self, limit=0):
        offset = 0
        batch = 100

        while True:
            params = {'select': '*', 'limit': batch, 'offset': offset, 'order': 'id.desc'}
            r = requests.get(f'{API_URL}/rest/v1/shared_code', headers=self.headers,
                params=params, timeout=30)
            if r.status_code != 200:
                logger.error(f'Error: {r.status_code} {r.text[:200]}')
                break

            items = r.json()
            if not items:
                break

            self.templates.extend(items)
            logger.info(f'Fetched {len(self.templates)} templates...')

            offset += batch
            if limit and len(self.templates) >= limit:
                self.templates = self.templates[:limit]
                break
            if len(items) < batch:
                break
            time.sleep(0.5)

        logger.info(f'Total: {len(self.templates)} templates')

    def save(self):
        BASE_DIR.mkdir(parents=True, exist_ok=True)
        templates_dir = BASE_DIR / 'templates'
        templates_dir.mkdir(exist_ok=True)

        index = []
        for t in self.templates:
            tid = t.get('id', 'unknown')
            slug = t.get('slug', str(tid))
            code = t.get('code', '')

            # Save HTML source
            if code:
                (templates_dir / f'{slug}.html').write_text(code, encoding='utf-8')

            # Save metadata
            meta = {k: v for k, v in t.items() if k != 'code'}
            meta['code_length'] = len(code)
            (templates_dir / f'{slug}.json').write_text(json.dumps(meta, indent=2), encoding='utf-8')
            index.append(meta)

        # Root files
        (BASE_DIR / 'index.json').write_text(json.dumps({
            'source': 'https://www.aura.build',
            'total': len(self.templates),
            'exported_at': datetime.now(timezone.utc).isoformat(),
            'templates': index,
        }, indent=2), encoding='utf-8')

        lines = [f'# Aura Templates ({len(self.templates)} exported)\n']
        lines.append(f'Source: https://www.aura.build | API: Supabase\n\n')
        lines.append('| # | Title | Slug | Code Size |\n')
        lines.append('|---|-------|------|-----------|\n')
        for i, m in enumerate(index[:50], 1):
            title = (m.get('title', '') or '')[:40]
            lines.append(f'| {i} | {title} | {m.get("slug", "")} | {m.get("code_length", 0)}b |\n')
        (BASE_DIR / 'MANIFEST.md').write_text(''.join(lines), encoding='utf-8')

        logger.info(f'Exported: {len(self.templates)} templates')


def main():
    import sys
    if not ANON_KEY:
        print('ERROR: set AURA_SUPABASE_ANON_KEY env var (no key baked in)'); sys.exit(1)
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--limit', type=int, default=0)
    args = parser.parse_args()

    BASE_DIR.mkdir(parents=True, exist_ok=True)
    exporter = AuraExporter()
    exporter.fetch_all(limit=args.limit)
    exporter.save()
    print(f'\nDone: {len(exporter.templates)} templates exported')


if __name__ == '__main__':
    main()
