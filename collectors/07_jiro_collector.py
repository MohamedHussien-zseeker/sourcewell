"""
Jiro Components Collector
Collects metadata from https://jiro.build/api/components
Source code requires purchase (Gumroad/Stripe)
"""

import json
import logging
import time
import requests
from datetime import datetime, timezone
from pathlib import Path
import os

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s',
    handlers=[logging.FileHandler('jiro_collector.log'), logging.StreamHandler()])
logger = logging.getLogger(__name__)

ROOT = Path(os.environ.get('SOURCEWELL_ROOT', str(Path(__file__).resolve().parent.parent / 'data')))
BASE_DIR = ROOT / 'jiro-components'


class JiroCollector:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': 'Mozilla/5.0'})
        self.results = []

    def collect_all(self):
        r = self.session.get('https://jiro.build/api/components', timeout=30)
        r.raise_for_status()
        data = r.json()

        if not data.get('success'):
            logger.error('API returned error')
            return

        components = data.get('components', [])
        categories = data.get('categories', [])
        category_groups = data.get('categoryGroups', [])

        logger.info(f'Total: {data.get("total")} components, {len(categories)} categories')

        # Classify and store
        by_group = {}
        for comp in components:
            group = comp.get('categoryGroup', 'other')
            if group not in by_group:
                by_group[group] = []
            by_group[group].append(comp)

        for group, items in by_group.items():
            logger.info(f'  {group}: {len(items)} items')

        self.results = components
        self.categories = categories
        self.category_groups = category_groups
        self.by_group = by_group

    def save(self):
        BASE_DIR.mkdir(parents=True, exist_ok=True)

        # Save by category group
        for group, items in self.by_group.items():
            group_dir = BASE_DIR / group
            group_dir.mkdir(exist_ok=True)

            index = []
            for comp in items:
                comp_dir = group_dir / comp['slug']
                comp_dir.mkdir(exist_ok=True)

                meta = {
                    'name': comp.get('name', ''),
                    'slug': comp.get('slug', ''),
                    'category': comp.get('category', ''),
                    'categoryLabel': comp.get('categoryLabel', ''),
                    'categoryGroup': comp.get('categoryGroup', ''),
                    'description': comp.get('description', ''),
                    'dependencies': comp.get('dependencies', []),
                    'isNew': comp.get('isNew', False),
                    'isPremium': comp.get('isPremium', False),
                    'thumbnail': comp.get('thumbnail', ''),
                    'videoPreview': comp.get('videoPreview'),
                    'source_url': f'https://jiro.build/components/{comp["slug"]}',
                    'collected_at': datetime.now(timezone.utc).isoformat(),
                }
                (comp_dir / 'metadata.json').write_text(json.dumps(meta, indent=2), encoding='utf-8')
                index.append(meta)

            (group_dir / 'index.json').write_text(json.dumps({
                'source': 'https://jiro.build',
                'group': group,
                'total': len(items),
                'items': index,
            }, indent=2), encoding='utf-8')

        # Root index
        premium_count = sum(1 for c in self.results if c.get('isPremium'))
        free_count = len(self.results) - premium_count

        (BASE_DIR / 'index.json').write_text(json.dumps({
            'source': 'https://jiro.build',
            'total': len(self.results),
            'premium': premium_count,
            'free': free_count,
            'categories': self.categories,
            'categoryGroups': self.category_groups,
            'byGroup': {k: len(v) for k, v in self.by_group.items()},
            'collected_at': datetime.now(timezone.utc).isoformat(),
            'note': 'Source code requires purchase. Metadata + descriptions collected.',
        }, indent=2), encoding='utf-8')

        # Manifest
        lines = [f'# Jiro Components ({len(self.results)} total, {free_count} free, {premium_count} premium)\n']
        lines.append(f'Source: https://jiro.build | Source code: paid\n\n')
        lines.append('| # | Name | Group | Category | Premium |\n')
        lines.append('|---|------|-------|----------|---------|\n')
        for i, c in enumerate(self.results[:50], 1):
            prem = 'Yes' if c.get('isPremium') else 'No'
            lines.append(f'| {i} | {c["name"][:40]} | {c.get("categoryGroup","")} | {c.get("categoryLabel","")} | {prem} |\n')
        if len(self.results) > 50:
            lines.append(f'| ... | {len(self.results) - 50} more | | | |\n')
        (BASE_DIR / 'MANIFEST.md').write_text(''.join(lines), encoding='utf-8')

        logger.info(f'Saved: {len(self.results)} components')


def main():
    collector = JiroCollector()
    collector.collect_all()
    collector.save()
    print(f'\nDone: {len(collector.results)} components')


if __name__ == '__main__':
    main()
