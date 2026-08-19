"""
Magic UI Collector v2
Collects Components, Examples, and Themes from https://magicui.design
Premium-ready: set AUTH_COOKIE env var for paid content
"""

import json
import logging
import os
import requests
from datetime import datetime, timezone
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s',
    handlers=[logging.FileHandler('magicui_collector.log'), logging.StreamHandler()])
logger = logging.getLogger(__name__)

ROOT = Path(os.environ.get('SOURCEWELL_ROOT', str(Path(__file__).resolve().parent.parent / 'data')))
BASE_DIR = ROOT / 'magic-ui'
REGISTRY_BASE = 'https://magicui.design/r'


class MagicUICollector:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Referer': 'https://magicui.design/',
            'Origin': 'https://magicui.design',
        })
        self.session.headers.pop('Accept-Encoding', None)

        auth_cookie = os.environ.get('MAGICUI_AUTH_COOKIE', '')
        if auth_cookie:
            self.session.headers['Cookie'] = auth_cookie
            logger.info('Premium mode: using auth cookie')

        self.results = {'components': [], 'examples': [], 'themes': []}
        self.errors = []

    def discover_all(self) -> list:
        resp = self.session.get('https://magicui.design/registry.json', timeout=15)
        resp.raise_for_status()
        return resp.json().get('items', [])

    def classify(self, item: dict) -> str:
        item_type = item.get('type', '')
        name = item.get('name', '')
        if item_type == 'registry:example':
            return 'examples'
        if item_type == 'registry:theme' or 'theme' in name.lower():
            return 'themes'
        if item_type in ('registry:ui', 'registry:lib', 'registry:style'):
            return 'components'
        return 'components'

    def collect_item(self, name: str) -> dict | None:
        try:
            resp = self.session.get(f'{REGISTRY_BASE}/{name}.json', timeout=20)
            if resp.status_code == 401:
                logger.warning(f'[PREMIUM] {name}')
                self.errors.append({'name': name, 'error': '401 Premium', 'needs_auth': True})
                return None
            if resp.status_code != 200:
                self.errors.append({'name': name, 'error': f'HTTP {resp.status_code}'})
                return None

            data = resp.json()
            source_files = {}
            for f in data.get('files', []):
                path, content = f.get('path', ''), f.get('content', '')
                if path and content:
                    source_files[path] = content

            return {
                'name': data.get('name', name),
                'type': data.get('type', 'unknown'),
                'dependencies': data.get('dependencies', []),
                'files': source_files,
                'registry_url': f'{REGISTRY_BASE}/{name}.json',
                'collected_at': datetime.now(timezone.utc).isoformat(),
            }
        except Exception as e:
            self.errors.append({'name': name, 'error': str(e)})
            return None

    def collect_all(self):
        items = self.discover_all()
        total = len(items)
        for idx, item in enumerate(items, 1):
            name = item['name']
            category = self.classify(item)
            logger.info(f'[{idx}/{total}] {name} ({category})')
            result = self.collect_item(name)
            if result:
                result['category'] = category
                self.results[category].append(result)

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
                'source': 'https://magicui.design', 'category': category,
                'total': len(items), 'items': index,
                'collected_at': datetime.now(timezone.utc).isoformat(),
            }, indent=2), encoding='utf-8')

        (BASE_DIR / 'index.json').write_text(json.dumps({
            'source': 'https://magicui.design',
            'collected_at': datetime.now(timezone.utc).isoformat(),
            'summary': {k: len(v) for k, v in self.results.items()},
            'errors': len(self.errors),
            'premium_needed': [e['name'] for e in self.errors if e.get('needs_auth')],
        }, indent=2), encoding='utf-8')


def main():
    collector = MagicUICollector()
    collector.collect_all()
    collector.save()
    print(f'Done: {", ".join(f"{k}:{len(v)}" for k, v in collector.results.items())}')
    if collector.errors:
        premium = [e for e in collector.errors if e.get('needs_auth')]
        print(f'Premium needed: {len(premium)} (set MAGICUI_AUTH_COOKIE env var)')


if __name__ == '__main__':
    main()
