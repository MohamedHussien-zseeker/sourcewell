"""
Origin UI (coss.com/ui) Collector
Collects all components from https://originui.com/
Source: GitHub repo cosscom/coss (568 components)
"""

import json
import logging
import os
import re
import time
import requests
from datetime import datetime, timezone
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s',
    handlers=[logging.FileHandler('originui_collector.log'), logging.StreamHandler()])
logger = logging.getLogger(__name__)

ROOT = Path(os.environ.get('SOURCEWELL_ROOT', str(Path(__file__).resolve().parent.parent / 'data')))
BASE_DIR = ROOT / 'origin-ui'
GITHUB_RAW = 'https://raw.githubusercontent.com/cosscom/coss/main/apps/ui'
REGISTRY_URL = f'{GITHUB_RAW}/registry.json'


class OriginUICollector:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': 'Mozilla/5.0'})
        self.results = []

    def discover_all(self):
        r = self.session.get(REGISTRY_URL, timeout=15)
        r.raise_for_status()
        items = r.json().get('items', [])
        logger.info(f'Discovered {len(items)} items')
        return items

    def fetch_source(self, path):
        url = f'{GITHUB_RAW}/{path}'
        r = self.session.get(url, timeout=15)
        if r.status_code == 200:
            return r.text
        return ''

    def collect_item(self, item):
        name = item.get('name', '')
        item_type = item.get('type', 'unknown')
        deps = item.get('dependencies', [])
        reg_deps = item.get('registryDependencies', [])
        files_list = item.get('files', [])

        source_files = {}
        for f in files_list:
            path = f.get('path', '')
            if path:
                content = self.fetch_source(path)
                if content:
                    source_files[path] = content
                time.sleep(0.1)

        # If no files listed, try the default path
        if not source_files and name != 'ui':
            default_path = f'registry/default/ui/{name}.tsx'
            content = self.fetch_source(default_path)
            if content:
                source_files[default_path] = content
            else:
                default_path = f'registry/default/ui/{name}.jsx'
                content = self.fetch_source(default_path)
                if content:
                    source_files[default_path] = content

        return {
            'name': name,
            'type': item_type,
            'dependencies': deps,
            'registryDependencies': reg_deps,
            'files': source_files,
            'collected_at': datetime.now(timezone.utc).isoformat(),
        }

    def classify(self, item):
        name = item.get('name', '')
        item_type = item.get('type', '')
        if 'example' in name.lower() or item_type == 'registry:example':
            return 'examples'
        if 'theme' in name.lower() or item_type == 'registry:theme':
            return 'themes'
        if item_type in ('registry:ui', 'registry:lib', 'registry:style'):
            return 'components'
        return 'components'

    def collect_all(self, limit=0):
        items = self.discover_all()
        total = min(len(items), limit) if limit else len(items)

        for idx, item in enumerate(items[:total], 1):
            name = item.get('name', 'unknown')
            category = self.classify(item)
            logger.info(f'[{idx}/{total}] {name} ({category})')

            result = self.collect_item(item)
            result['category'] = category
            self.results.append(result)

            if idx % 50 == 0:
                logger.info(f'Progress: {len(self.results)}/{idx}')

    def save(self):
        for category in ['components', 'examples', 'themes']:
            cat_items = [r for r in self.results if r.get('category') == category]
            if not cat_items:
                continue

            cat_dir = BASE_DIR / category
            cat_dir.mkdir(parents=True, exist_ok=True)

            index = []
            for comp in cat_items:
                comp_dir = cat_dir / comp['name']
                comp_dir.mkdir(exist_ok=True)

                for filepath, content in comp['files'].items():
                    flat = filepath.split('/')[-1]
                    (comp_dir / flat).write_text(content, encoding='utf-8')

                meta = {k: v for k, v in comp.items() if k != 'files'}
                meta['file_count'] = len(comp['files'])
                (comp_dir / 'metadata.json').write_text(json.dumps(meta, indent=2), encoding='utf-8')
                index.append(meta)

            (cat_dir / 'index.json').write_text(json.dumps({
                'source': 'https://originui.com', 'category': category,
                'total': len(cat_items), 'items': index,
                'collected_at': datetime.now(timezone.utc).isoformat(),
            }, indent=2), encoding='utf-8')

        # Root index
        (BASE_DIR / 'index.json').write_text(json.dumps({
            'source': 'https://originui.com',
            'github': 'https://github.com/cosscom/coss',
            'collected_at': datetime.now(timezone.utc).isoformat(),
            'summary': {},
        }, indent=2), encoding='utf-8')

        # Update root summary
        summary = {}
        for r in self.results:
            cat = r.get('category', 'unknown')
            summary[cat] = summary.get(cat, 0) + 1
        with open(BASE_DIR / 'index.json', 'r+') as f:
            data = json.load(f)
            data['summary'] = summary
            f.seek(0)
            json.dump(data, f, indent=2)
            f.truncate()

        # Manifest
        lines = [f'# Origin UI Components ({len(self.results)} collected)\n']
        lines.append(f'Source: https://originui.com | GitHub: cosscom/coss\n\n')
        lines.append('| # | Name | Type | Files | Dependencies |\n')
        lines.append('|---|------|------|-------|--------------|\n')
        for i, r in enumerate(self.results, 1):
            deps = ', '.join(r.get('dependencies', [])[:3]) or '-'
            lines.append(f'| {i} | {r["name"]} | {r["category"]} | {r.get("file_count", 0)} | {deps} |\n')
        (BASE_DIR / 'MANIFEST.md').write_text(''.join(lines), encoding='utf-8')

        logger.info(f'Saved: {", ".join(f"{k}:{v}" for k, v in summary.items())}')


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--limit', type=int, default=0)
    args = parser.parse_args()

    BASE_DIR.mkdir(parents=True, exist_ok=True)
    collector = OriginUICollector()
    collector.collect_all(limit=args.limit)
    collector.save()
    print(f'\nDone: {len(collector.results)} items')


if __name__ == '__main__':
    main()
