"""
Landingfolio Collector
Collects landing page inspiration from https://www.landingfolio.com/
API: s3.landingfolio.com/inspiration
"""

import json
import logging
import time
import requests
from datetime import datetime, timezone
from pathlib import Path
import os

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s',
    handlers=[logging.FileHandler('landingfolio_collector.log'), logging.StreamHandler()])
logger = logging.getLogger(__name__)

ROOT = Path(os.environ.get('SOURCEWELL_ROOT', str(Path(__file__).resolve().parent.parent / 'data')))
BASE_DIR = ROOT / 'landingfolio'
API_BASE = 'https://s3.landingfolio.com'


class LandingfolioCollector:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': 'Mozilla/5.0'})
        self.results = []

    def collect_all(self, limit=0):
        page = 1
        seen_ids = set()

        while True:
            logger.info(f'Fetching page {page}...')
            r = self.session.get(f'{API_BASE}/inspiration', params={
                'category': 'landing-page', 'page': page
            }, timeout=15)

            if r.status_code != 200:
                logger.error(f'Error: {r.status_code}')
                break

            items = r.json()
            if not items:
                break

            new_items = 0
            for item in items:
                item_id = item.get('_id', '')
                if item_id in seen_ids:
                    continue
                seen_ids.add(item_id)
                self.results.append(item)
                new_items += 1

            logger.info(f'  Got {new_items} new items (total: {len(self.results)})')

            if new_items == 0:
                break
            if limit and len(self.results) >= limit:
                self.results = self.results[:limit]
                break

            page += 1
            time.sleep(0.5)

    def save(self):
        BASE_DIR.mkdir(parents=True, exist_ok=True)
        templates_dir = BASE_DIR / 'templates'
        templates_dir.mkdir(exist_ok=True)

        index = []
        for item in self.results:
            item_id = item.get('_id', 'unknown')
            title = item.get('title', 'unknown').lower().replace(' ', '-').replace('/', '-')
            slug = item.get('slug', title)[:50]

            # Save metadata
            meta = {
                'id': item_id,
                'title': item.get('title', ''),
                'slug': slug,
                'url': item.get('url', ''),
                'postDate': item.get('postDate', ''),
                'categories': item.get('categories', []),
                'analytics': item.get('analytics', {}),
                'colors': item.get('colors', {}).get('hex', []),
                'screenshots': item.get('screenshots', []),
            }

            # Save screenshot URLs
            screenshots = item.get('screenshots', [])
            if screenshots:
                meta['screenshot_urls'] = [s.get('url', '') for s in screenshots if isinstance(s, dict)]

            comp_dir = templates_dir / slug
            comp_dir.mkdir(exist_ok=True)
            (comp_dir / 'metadata.json').write_text(json.dumps(meta, indent=2), encoding='utf-8')
            index.append(meta)

        # Root index
        (BASE_DIR / 'index.json').write_text(json.dumps({
            'source': 'https://www.landingfolio.com',
            'total': len(self.results),
            'exported_at': datetime.now(timezone.utc).isoformat(),
            'templates': index,
        }, indent=2), encoding='utf-8')

        # Manifest
        lines = [f'# Landingfolio Templates ({len(self.results)} collected)\n']
        lines.append(f'Source: https://www.landingfolio.com\n\n')
        lines.append('| # | Title | Categories | Views | Favorites |\n')
        lines.append('|---|-------|------------|-------|-----------|\n')
        for i, m in enumerate(index[:50], 1):
            cats = ', '.join(m.get('categories', [])[:3])
            analytics = m.get('analytics', {})
            views = analytics.get('views', 0)
            favs = analytics.get('favorites', 0)
            lines.append(f'| {i} | {m["title"][:35]} | {cats} | {views} | {favs} |\n')
        (BASE_DIR / 'MANIFEST.md').write_text(''.join(lines), encoding='utf-8')

        logger.info(f'Saved: {len(self.results)} templates')


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--limit', type=int, default=0)
    args = parser.parse_args()

    BASE_DIR.mkdir(parents=True, exist_ok=True)
    collector = LandingfolioCollector()
    collector.collect_all(limit=args.limit)
    collector.save()
    print(f'\nDone: {len(collector.results)} templates')


if __name__ == '__main__':
    main()
