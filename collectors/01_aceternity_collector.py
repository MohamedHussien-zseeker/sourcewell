"""
Aceternity UI Collector v2
Collects Components, Templates, and Themes from https://ui.aceternity.com
Premium-ready: set AUTH_COOKIE env var for paid content
"""

import json
import logging
import os
import time
import requests
from datetime import datetime, timezone
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s',
    handlers=[logging.FileHandler('aceternity_collector.log'), logging.StreamHandler()])
logger = logging.getLogger(__name__)

ROOT = Path(os.environ.get('SOURCEWELL_ROOT', str(Path(__file__).resolve().parent.parent / 'data')))
BASE_DIR = ROOT / 'ui.aceternity'
REGISTRY_URL = 'https://ui.aceternity.com/registry'


class AceternityCollector:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Referer': 'https://ui.aceternity.com/',
        })
        self.session.headers.pop('Accept-Encoding', None)

        # Premium support: set AUTH_COOKIE env var with your session cookie
        auth_cookie = os.environ.get('ACETERNITY_AUTH_COOKIE', '')
        if auth_cookie:
            self.session.headers['Cookie'] = auth_cookie
            logger.info('Premium mode: using auth cookie')

        self.results = {'components': [], 'templates': [], 'themes': []}
        self.errors = []

    def discover_all(self) -> list:
        resp = self.session.get('https://ui.aceternity.com/registry.json', timeout=15)
        resp.raise_for_status()
        return resp.json().get('items', [])

    def classify(self, item: dict) -> str:
        name = item.get('name', '')
        item_type = item.get('type', '')
        # Templates usually have demo/example suffixes or are in template categories
        if 'template' in name.lower() or 'demo' in name.lower() or item_type == 'registry:template':
            return 'templates'
        # Themes are style presets
        if 'theme' in name.lower() or item_type == 'registry:theme':
            return 'themes'
        return 'components'

    def collect_item(self, name: str) -> dict | None:
        try:
            resp = self.session.get(f'{REGISTRY_URL}/{name}.json', timeout=20)
            if resp.status_code == 401:
                logger.warning(f'[PREMIUM] {name} - needs auth')
                self.errors.append({'name': name, 'error': '401 Premium', 'needs_auth': True})
                return None
            if resp.status_code != 200:
                logger.warning(f'[{resp.status_code}] {name}')
                self.errors.append({'name': name, 'error': f'HTTP {resp.status_code}'})
                return None

            data = resp.json()
            source_files = {}
            for f in data.get('files', []):
                path = f.get('path', '')
                content = f.get('content', '')
                if path and content:
                    source_files[path] = content

            return {
                'name': data.get('name', name),
                'type': data.get('type', 'unknown'),
                'dependencies': data.get('dependencies', []),
                'files': source_files,
                'registry_url': f'{REGISTRY_URL}/{name}.json',
                'collected_at': datetime.now(timezone.utc).isoformat(),
            }
        except Exception as e:
            logger.error(f'Error {name}: {e}')
            self.errors.append({'name': name, 'error': str(e)})
            return None

    def collect_all(self):
        items = self.discover_all()
        total = len(items)
        logger.info(f'Discovered {total} items')

        for idx, item in enumerate(items, 1):
            name = item['name']
            category = self.classify(item)
            logger.info(f'[{idx}/{total}] {name} ({category})')

            result = self.collect_item(name)
            if result:
                result['category'] = category
                self.results[category].append(result)

            if idx % 25 == 0:
                logger.info(f'Progress: C={len(self.results["components"])} T={len(self.results["templates"])} Th={len(self.results["themes"])}')

    def save(self):
        for category, items in self.results.items():
            cat_dir = BASE_DIR / category
            cat_dir.mkdir(parents=True, exist_ok=True)

            index = []
            for comp in items:
                comp_dir = cat_dir / comp['name']
                comp_dir.mkdir(exist_ok=True)
                for filepath, content in comp['files'].items():
                    (comp_dir / filepath.split('/')[-1]).write_text(content, encoding='utf-8')
                meta = {k: v for k, v in comp.items() if k != 'files'}
                (comp_dir / 'metadata.json').write_text(json.dumps(meta, indent=2), encoding='utf-8')
                index.append(meta)

            (cat_dir / 'index.json').write_text(json.dumps({
                'source': 'https://ui.aceternity.com',
                'category': category,
                'total': len(items),
                'collected_at': datetime.now(timezone.utc).isoformat(),
                'items': index,
            }, indent=2), encoding='utf-8')

        # Root index
        (BASE_DIR / 'index.json').write_text(json.dumps({
            'source': 'https://ui.aceternity.com',
            'collected_at': datetime.now(timezone.utc).isoformat(),
            'summary': {k: len(v) for k, v in self.results.items()},
            'errors': len(self.errors),
            'premium_needed': [e['name'] for e in self.errors if e.get('needs_auth')],
        }, indent=2), encoding='utf-8')

        logger.info(f'Saved: {", ".join(f"{k}:{len(v)}" for k, v in self.results.items())}')


def main():
    collector = AceternityCollector()
    collector.collect_all()
    collector.save()
    print(f'\nDone: {", ".join(f"{k}:{len(v)}" for k, v in collector.results.items())}')
    if collector.errors:
        premium = [e for e in collector.errors if e.get('needs_auth')]
        print(f'Premium needed: {len(premium)} (set ACETERNITY_AUTH_COOKIE env var)')


if __name__ == '__main__':
    main()
