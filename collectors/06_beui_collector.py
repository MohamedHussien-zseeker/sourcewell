"""
BeUI Pro Collector
Collects metadata from https://pro.beui.dev/
Source code requires paid license (Polar)
"""

import json
import logging
import re
import time
import requests
from datetime import datetime, timezone
from pathlib import Path
import os

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s',
    handlers=[logging.FileHandler('beui_collector.log'), logging.StreamHandler()])
logger = logging.getLogger(__name__)

ROOT = Path(os.environ.get('SOURCEWELL_ROOT', str(Path(__file__).resolve().parent.parent / 'data')))
BASE_DIR = ROOT / 'beui-pro'
CATALOG_JS = 'https://pro.beui.dev/_next/static/chunks/2z4rsh99qeem4.js?dpl=dpl_EEs84j8pwRUbL4qtnzHw4vQ1g86D'


class BeUIProCollector:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': 'Mozilla/5.0'})
        self.results = []

    def discover(self):
        r = self.session.get(CATALOG_JS, timeout=15)
        matches = re.findall(r'slug:"([^"]+)",name:"([^"]+)",category:"([^"]+)"', r.text)
        logger.info(f'Discovered {len(matches)} components')
        return [{'slug': m[0], 'name': m[1], 'category': m[2]} for m in matches]

    def collect_all(self):
        items = self.discover()
        for idx, item in enumerate(items, 1):
            slug = item['slug']
            url = f'https://pro.beui.dev/components/{slug}'
            logger.info(f'[{idx}/{len(items)}] {slug}')

            try:
                r = self.session.get(url, timeout=15)
                text = r.text

                # Extract description from meta
                desc_match = re.search(r'<meta name="description" content="([^"]*)"', text)
                description = desc_match.group(1) if desc_match else ''

                # Extract install command
                install_match = re.search(r'(bunx|npx|pnpm|yarn)[^"]*shadcn add @beui-pro/[^\s<"]*', text)
                install_cmd = install_match.group(0) if install_match else f'bunx shadcn add @beui-pro/{slug}'

                self.results.append({
                    'slug': slug,
                    'name': item['name'],
                    'category': item['category'],
                    'description': description,
                    'install_command': install_cmd,
                    'source_url': url,
                    'source_locked': True,
                    'collected_at': datetime.now(timezone.utc).isoformat(),
                })

            except Exception as e:
                logger.error(f'Error {slug}: {e}')

            time.sleep(0.3)

    def save(self):
        BASE_DIR.mkdir(parents=True, exist_ok=True)
        comp_dir = BASE_DIR / 'components'
        comp_dir.mkdir(exist_ok=True)

        index = []
        for comp in self.results:
            d = comp_dir / comp['slug']
            d.mkdir(exist_ok=True)
            (d / 'metadata.json').write_text(json.dumps(comp, indent=2), encoding='utf-8')
            index.append(comp)

        (BASE_DIR / 'index.json').write_text(json.dumps({
            'source': 'https://pro.beui.dev',
            'total': len(self.results),
            'source_locked': True,
            'license': 'Polar (paid)',
            'collected_at': datetime.now(timezone.utc).isoformat(),
            'components': index,
        }, indent=2), encoding='utf-8')

        lines = [f'# BeUI Pro Components ({len(self.results)} - metadata only, source paywalled)\n']
        lines.append(f'Source: https://pro.beui.dev | License: Polar (paid)\n\n')
        lines.append('| # | Name | Category | Install Command |\n')
        lines.append('|---|------|----------|----------------|\n')
        for i, m in enumerate(index, 1):
            lines.append(f'| {i} | {m["name"]} | {m["category"]} | `{m["install_command"]}` |\n')
        (BASE_DIR / 'MANIFEST.md').write_text(''.join(lines), encoding='utf-8')
        logger.info(f'Saved: {len(self.results)} components')


def main():
    collector = BeUIProCollector()
    collector.collect_all()
    collector.save()
    print(f'\nDone: {len(collector.results)} components (metadata only, source paywalled)')


if __name__ == '__main__':
    main()
