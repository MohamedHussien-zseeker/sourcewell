"""
Unlumen UI Collector
Collects all free components from https://ui.unlumen.com/
Pro components need Polar license key (set UNLUMEN_API_KEY env var)
"""

import json
import logging
import os
import time
import requests
from datetime import datetime, timezone
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s',
    handlers=[logging.FileHandler('unlumen_collector.log'), logging.StreamHandler()])
logger = logging.getLogger(__name__)

ROOT = Path(os.environ.get('SOURCEWELL_ROOT', str(Path(__file__).resolve().parent.parent / 'data')))
BASE_DIR = ROOT / 'unlumen-ui'
REGISTRY_URL = 'https://ui.unlumen.com/r/registry.json'


class UnlumenCollector:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0',
            'Accept': 'application/json',
        })
        self.api_key = os.environ.get('UNLUMEN_API_KEY', '')
        self.results = []
        self.errors = []

    def discover_all(self):
        r = self.session.get(REGISTRY_URL, timeout=15)
        r.raise_for_status()
        items = r.json().get('items', [])
        logger.info(f'Discovered {len(items)} items')
        return items

    def classify(self, item):
        name = item.get('name', '')
        item_type = item.get('type', '')
        if 'theme' in name.lower() or item_type == 'registry:theme':
            return 'themes'
        if item_type in ('registry:ui', 'registry:lib', 'registry:style'):
            return 'components'
        return 'components'

    def collect_item(self, name):
        headers = {'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json'}
        if self.api_key:
            headers['Authorization'] = f'Bearer {self.api_key}'

        r = self.session.get(f'https://ui.unlumen.com/r/{name}.json', headers=headers, timeout=15)
        if r.status_code == 401:
            self.errors.append({'name': name, 'error': '401 Pro (needs license)'})
            return None
        if r.status_code != 200:
            self.errors.append({'name': name, 'error': f'HTTP {r.status_code}'})
            return None

        data = r.json()
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
            'collected_at': datetime.now(timezone.utc).isoformat(),
        }

    def collect_all(self, limit=0):
        items = self.discover_all()
        ui_items = [i for i in items if i.get('type') in ('registry:ui', 'registry:lib', 'registry:style')]
        total = min(len(ui_items), limit) if limit else len(ui_items)
        logger.info(f'Collecting {total} components')

        for idx, item in enumerate(ui_items[:total], 1):
            name = item.get('name', 'unknown')
            category = self.classify(item)
            logger.info(f'[{idx}/{total}] {name}')

            result = self.collect_item(name)
            if result:
                result['category'] = category
                self.results.append(result)
            else:
                logger.warning(f'  Skipped: {self.errors[-1]["error"] if self.errors else "unknown"}')

            time.sleep(0.2)

    def save(self):
        cat_dir = BASE_DIR / 'components'
        cat_dir.mkdir(parents=True, exist_ok=True)

        index = []
        for comp in self.results:
            comp_dir = cat_dir / comp['name']
            comp_dir.mkdir(exist_ok=True)

            for filepath, content in comp['files'].items():
                flat = filepath.split('/')[-1]
                (comp_dir / flat).write_text(content, encoding='utf-8')

            meta = {k: v for k, v in comp.items() if k != 'files'}
            meta['file_count'] = len(comp['files'])
            (comp_dir / 'metadata.json').write_text(json.dumps(meta, indent=2), encoding='utf-8')
            index.append(meta)

        (BASE_DIR / 'index.json').write_text(json.dumps({
            'source': 'https://ui.unlumen.com',
            'total': len(self.results),
            'pro_blocked': len(self.errors),
            'collected_at': datetime.now(timezone.utc).isoformat(),
            'components': index,
            'errors': self.errors,
        }, indent=2), encoding='utf-8')

        lines = [f'# Unlumen UI Components ({len(self.results)} collected, {len(self.errors)} pro blocked)\n']
        lines.append(f'Source: https://ui.unlumen.com\n\n')
        lines.append('| # | Name | Files | Dependencies |\n')
        lines.append('|---|------|-------|--------------|\n')
        for i, m in enumerate(index, 1):
            deps = ', '.join(m.get('dependencies', [])[:3]) or '-'
            lines.append(f'| {i} | {m["name"]} | {m.get("file_count", 0)} | {deps} |\n')
        (BASE_DIR / 'MANIFEST.md').write_text(''.join(lines), encoding='utf-8')

        logger.info(f'Saved: {len(self.results)} components, {len(self.errors)} blocked')


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--limit', type=int, default=0)
    args = parser.parse_args()

    BASE_DIR.mkdir(parents=True, exist_ok=True)
    collector = UnlumenCollector()
    collector.collect_all(limit=args.limit)
    collector.save()
    print(f'\nDone: {len(collector.results)} components, {len(collector.errors)} pro blocked')


if __name__ == '__main__':
    main()
