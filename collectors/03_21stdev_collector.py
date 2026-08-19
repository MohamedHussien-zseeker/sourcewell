"""
21st.dev Collector v4 - MCP API based
Uses 21st.dev MCP API with API key to get full component source.
No browser needed. Works headlessly.

Usage:
  python 03_21stdev_collector.py                      # Collect all components
  python 03_21stdev_collector.py --limit 5            # Test with 5
  python 03_21stdev_collector.py --query "button"     # Search specific type
"""

import argparse
import json
import logging
import os
import time
import requests
from datetime import datetime, timezone
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s',
    handlers=[logging.FileHandler('21stdev_collector.log'), logging.StreamHandler()])
logger = logging.getLogger(__name__)

ROOT = Path(os.environ.get('SOURCEWELL_ROOT', str(Path(__file__).resolve().parent.parent / 'data')))
BASE_DIR = ROOT / '21st-dev'
API_KEY = os.environ.get('TWENTYFIRST_API_KEY', '')
MCP_URL = 'https://21st.dev/api/mcp'


class TwentyFirstCollector:
    def __init__(self):
        self.headers = {
            'x-api-key': API_KEY,
            'Content-Type': 'application/json',
        }
        self.results = []

    def mcp_call(self, method, params):
        r = requests.post(MCP_URL, headers=self.headers, timeout=30,
            json={'jsonrpc': '2.0', 'method': method, 'id': 1, 'params': params})
        r.raise_for_status()
        return r.json()

    def search(self, query='a', entity_type='component', limit=50, cursor=None):
        args = {'query': query, 'type': entity_type, 'limit': limit}
        if cursor:
            args['cursor'] = cursor
        resp = self.mcp_call('tools/call', {'name': 'search', 'arguments': args})
        data = resp.get('result', {}).get('structuredContent', {})
        return data.get('results', [])

    def get_usage(self):
        resp = self.mcp_call('tools/call', {'name': 'get_usage', 'arguments': {}})
        text = resp.get('result', {}).get('content', [{}])[0].get('text', '')
        return text

    def get_component(self, comp_id):
        resp = self.mcp_call('tools/call', {'name': 'get_component', 'arguments': {'id': comp_id}})
        text = resp.get('result', {}).get('content', [{}])[0].get('text', '')
        return text

    def get_theme(self, theme_id):
        resp = self.mcp_call('tools/call', {'name': 'get_theme', 'arguments': {'id': theme_id}})
        text = resp.get('result', {}).get('content', [{}])[0].get('text', '')
        return text

    def search_all_pages(self, queries, entity_type='component'):
        all_results = {}
        for query in queries:
            results = self.search(query=query, entity_type=entity_type, limit=50)
            for r in results:
                rid = r.get('id')
                if rid and rid not in all_results:
                    all_results[rid] = r
            time.sleep(0.3)
        return list(all_results.values())

    def collect(self, query='a', limit=0):
        # Check usage
        usage = self.get_usage()
        logger.info(f'Usage: {usage}')
        self.usage_text = usage

        # Parse remaining quota
        self.source_limit_reached = 'limit' in usage.lower() and 'resets' in usage.lower()

        # Broad search queries to cover all component types
        search_queries = [
            'button', 'card', 'hero', 'form', 'input', 'modal', 'dialog',
            'navbar', 'navigation', 'sidebar', 'menu', 'dropdown', 'tabs',
            'table', 'data', 'chart', 'graph', 'progress', 'loading', 'spinner',
            'animation', 'transition', 'effect', 'glow', 'shine', 'gradient',
            'background', 'particle', 'star', 'beam', 'light', 'shadow',
            'text', 'heading', 'typography', 'marquee', 'scroll', 'parallax',
            'image', 'gallery', 'carousel', 'slider', 'swiper', 'drag',
            'toggle', 'switch', 'checkbox', 'radio', 'select', 'dropdown',
            'tooltip', 'popover', 'toast', 'notification', 'alert', 'banner',
            'footer', 'header', 'layout', 'grid', 'flex', 'container',
            'pricing', 'testimonial', 'review', 'feedback', 'comment',
            'timeline', 'step', 'wizard', 'onboarding', 'accordion', 'collapse',
            'tree', 'folder', 'file', 'upload', 'dropzone', 'calendar', 'date',
            'avatar', 'badge', 'tag', 'chip', 'label', 'breadcrumb', 'pagination',
            'search', 'filter', 'sort', 'combo', 'command', 'kbd',
            'shimmer', 'skeleton', 'placeholder', 'blank', 'empty',
            'cursor', 'pointer', 'hover', 'interactive', 'click',
            'globe', 'map', '3d', 'webgl', 'canvas', 'shader',
            'chat', 'message', 'ai', 'assistant', 'bot', 'siri',
            'glass', 'blur', 'frosted', 'aurora', 'neon', 'cyber',
            'terminal', 'code', 'editor', 'syntax', 'highlight',
            'logo', 'icon', 'emoji', 'symbol',
            'compare', 'versus', 'vs', 'difference',
            'cta', 'action', 'subscribe', 'signup', 'login', 'auth',
            'team', 'member', 'profile', 'user', 'account',
            'feature', 'benefit', 'capability', 'highlight',
            'demo', 'example', 'showcase', 'sample',
        ]

        # Search components
        logger.info(f'Searching components with {len(search_queries)} queries...')
        components = self.search_all_pages(queries=search_queries, entity_type='component')
        logger.info(f'Found {len(components)} unique components')

        # Search themes
        theme_queries = ['dark', 'light', 'minimal', 'modern', 'color', 'gradient', 'neon', 'glass', 'nature', 'ocean', 'sunset', 'pastel', 'monochrome', 'vibrant', 'elegant']
        logger.info(f'Searching themes...')
        themes = self.search_all_pages(queries=theme_queries, entity_type='theme')
        logger.info(f'Found {len(themes)} themes')

        # Search templates
        template_queries = ['landing', 'dashboard', 'portfolio', 'blog', 'ecommerce', 'saas', 'startup', 'agency', 'resume', 'documentation']
        logger.info(f'Searching templates...')
        templates = self.search_all_pages(queries=template_queries, entity_type='template')
        logger.info(f'Found {len(templates)} templates')

        total = len(components) + len(themes) + len(templates)
        if limit:
            total = min(total, limit)
        logger.info(f'Total to collect: {total}')

        collected = {'components': [], 'themes': [], 'templates': []}
        count = 0

        # Collect components with full source
        for comp in components:
            if limit and count >= limit:
                break
            count += 1
            comp_id = comp.get('id')
            name = comp.get('name', 'unknown')
            author = comp.get('author', '')
            logger.info(f'[{count}/{total}] Component: {name} (id:{comp_id})')

            # Skip source fetch if limit already reached
            source = ''
            if not self.source_limit_reached:
                source = self.get_component(comp_id)
                time.sleep(0.5)
                if 'limit' in source.lower() and 'resets' in source.lower():
                    self.source_limit_reached = True
                    logger.warning('Source limit reached! Remaining components will only get metadata.')
            else:
                logger.info(f'  Skipping source (limit reached)')

            if source and 'limit' not in source.lower():
                # Parse source - extract component and demo code
                comp_code = ''
                demo_code = ''
                install_cmd = ''

                if '## Component' in source:
                    parts = source.split('## Component')
                    if len(parts) > 1:
                        comp_part = parts[1].split('## Demo')[0] if '## Demo' in parts[1] else parts[1]
                        # Extract code between ```tsx and ```
                        import re
                        code_match = re.search(r'```tsx?\n(.*?)```', comp_part, re.DOTALL)
                        if code_match:
                            comp_code = code_match.group(1).strip()

                if '## Demo' in source:
                    demo_part = source.split('## Demo')[1]
                    code_match = re.search(r'```tsx?\n(.*?)```', demo_part, re.DOTALL)
                    if code_match:
                        demo_code = code_match.group(1).strip()

                if 'install:' in source:
                    install_cmd = source.split('install:')[1].split('\n')[0].strip()

                collected['components'].append({
                    'id': comp_id, 'name': name, 'author': author,
                    'description': comp.get('description', ''),
                    'preview_url': comp.get('previewUrl', ''),
                    'source_url': comp.get('url', ''),
                    'install_command': install_cmd,
                    'component_source': comp_code,
                    'demo_code': demo_code,
                    'full_response': source,
                    'collected_at': datetime.now(timezone.utc).isoformat(),
                })

        # Collect themes
        for theme in themes:
            if limit and count >= limit:
                break
            count += 1
            theme_id = theme.get('id')
            name = theme.get('name', 'unknown')
            logger.info(f'[{count}/{total}] Theme: {name} (id:{theme_id})')

            css = self.get_theme(theme_id)
            time.sleep(0.5)

            collected['themes'].append({
                'id': theme_id, 'name': name,
                'author': theme.get('author', ''),
                'description': theme.get('description', ''),
                'css': css,
                'collected_at': datetime.now(timezone.utc).isoformat(),
            })

        # Collect templates
        for tmpl in templates:
            if limit and count >= limit:
                break
            count += 1
            collected['templates'].append({
                'id': tmpl.get('id'), 'name': tmpl.get('name', 'unknown'),
                'author': tmpl.get('author', ''),
                'description': tmpl.get('description', ''),
                'preview_url': tmpl.get('previewUrl', ''),
                'url': tmpl.get('url', ''),
                'collected_at': datetime.now(timezone.utc).isoformat(),
            })

        return collected

    def save(self, collected):
        for category, items in collected.items():
            cat_dir = BASE_DIR / category
            cat_dir.mkdir(parents=True, exist_ok=True)

            index = []
            for item in items:
                name_slug = item.get('name', 'unknown').lower().replace(' ', '-')
                author = item.get('author', 'unknown')
                item_dir = cat_dir / author / name_slug
                item_dir.mkdir(parents=True, exist_ok=True)

                # Save source files
                if item.get('component_source'):
                    (item_dir / f'{name_slug}.tsx').write_text(item['component_source'], encoding='utf-8')
                if item.get('demo_code'):
                    (item_dir / f'{name_slug}-demo.tsx').write_text(item['demo_code'], encoding='utf-8')
                if item.get('css'):
                    (item_dir / f'{name_slug}.css').write_text(item['css'], encoding='utf-8')

                # Save metadata
                meta = {k: v for k, v in item.items() if k not in ('component_source', 'demo_code', 'css', 'full_response')}
                (item_dir / 'metadata.json').write_text(json.dumps(meta, indent=2), encoding='utf-8')

                # Save full response
                if item.get('full_response'):
                    (item_dir / 'source.md').write_text(item['full_response'], encoding='utf-8')

                index.append(meta)

            (cat_dir / 'index.json').write_text(json.dumps({
                'source': 'https://21st.dev', 'category': category,
                'total': len(items), 'items': index,
                'collected_at': datetime.now(timezone.utc).isoformat(),
            }, indent=2), encoding='utf-8')

        # Root index
        (BASE_DIR / 'index.json').write_text(json.dumps({
            'source': 'https://21st.dev',
            'collected_at': datetime.now(timezone.utc).isoformat(),
            'summary': {k: len(v) for k, v in collected.items()},
        }, indent=2), encoding='utf-8')

        logger.info(f'Saved: {", ".join(f"{k}:{len(v)}" for k, v in collected.items())}')


def main():
    import sys
    if not API_KEY:
        print('ERROR: set TWENTYFIRST_API_KEY env var (no key baked in)'); sys.exit(1)
    parser = argparse.ArgumentParser()
    parser.add_argument('--limit', type=int, default=0, help='Max items to collect')
    parser.add_argument('--query', type=str, default='a', help='Search query')
    args = parser.parse_args()

    BASE_DIR.mkdir(parents=True, exist_ok=True)
    collector = TwentyFirstCollector()
    collected = collector.collect(query=args.query, limit=args.limit)
    collector.save(collected)
    print(f'\nDone: {", ".join(f"{k}:{len(v)}" for k, v in collected.items())}')


if __name__ == '__main__':
    main()
