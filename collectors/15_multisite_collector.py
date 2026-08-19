"""
Multi-Site Landing Page Collector
Scrapes metadata from: land-book, recent-design, posts-design, motionsites,
peachweb, gradient-lab, grainient-supply, unicorn-platform
"""

import asyncio
import json
import logging
import os
import time
import requests
from datetime import datetime, timezone
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s',
    handlers=[logging.FileHandler('multisite_collector.log'), logging.StreamHandler()])
logger = logging.getLogger(__name__)

ROOT = Path(os.environ.get('SOURCEWELL_ROOT', str(Path(__file__).resolve().parent.parent / 'data')))
BASE = ROOT


def collect_recent_design():
    """Collect from recent.design API"""
    base = 'https://api.recent.design'
    items = []
    try:
        # Get count
        r = requests.get(f'{base}/trpc/online.count?batch=1&input=%7B%7D', timeout=10)
        count_data = r.json()
        
        # Try to get items
        for page in range(1, 20):
            r = requests.get(f'{base}/trpc/online.list?batch=1&input={json.dumps({"json":{"page":page,"limit":50}})}', timeout=10)
            if r.status_code == 200:
                data = r.json()
                if isinstance(data, list) and data:
                    result = data[0].get('result', {}).get('data', {}).get('json', [])
                    if not result:
                        break
                    items.extend(result)
                    logger.info(f'recent.design page {page}: {len(result)} items')
                else:
                    break
            time.sleep(0.5)
    except Exception as e:
        logger.error(f'recent.design error: {e}')
    return items


def collect_posts_design():
    """Scrape posts.design"""
    from playwright.sync_api import sync_playwright
    
    items = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        try:
            page.goto('https://posts.design/', wait_until='domcontentloaded', timeout=30000)
            time.sleep(5)
            
            # Scroll to load more
            for _ in range(5):
                page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                time.sleep(2)
            
            # Extract post data
            items = page.evaluate('''() => {
                const posts = [];
                const cards = document.querySelectorAll('article, [class*="card"], [class*="post"]');
                cards.forEach(card => {
                    const link = card.querySelector('a[href]');
                    const title = card.querySelector('h2, h3, [class*="title"]');
                    const desc = card.querySelector('p, [class*="desc"]');
                    const img = card.querySelector('img');
                    if (link) {
                        posts.push({
                            url: link.getAttribute('href'),
                            title: title ? title.textContent.trim() : '',
                            description: desc ? desc.textContent.trim() : '',
                            image: img ? img.src : '',
                        });
                    }
                });
                return posts;
            }''')
        except Exception as e:
            logger.error(f'posts.design error: {e}')
        
        browser.close()
    return items


def collect_motionsites():
    """Scrape motionsites.com"""
    from playwright.sync_api import sync_playwright
    
    items = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        try:
            page.goto('https://motionsites.com/', wait_until='domcontentloaded', timeout=30000)
            time.sleep(5)
            
            for _ in range(3):
                page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                time.sleep(2)
            
            items = page.evaluate('''() => {
                const sites = [];
                const cards = document.querySelectorAll('a[href*="http"], [class*="card"], [class*="site"]');
                cards.forEach(card => {
                    const link = card.tagName === 'A' ? card : card.querySelector('a');
                    const img = card.querySelector('img');
                    const title = card.querySelector('h2, h3, [class*="title"], [class*="name"]');
                    if (link && link.href && !link.href.includes('motionsites.com')) {
                        sites.push({
                            url: link.href,
                            title: title ? title.textContent.trim() : link.textContent.trim().substring(0, 50),
                            image: img ? img.src : '',
                        });
                    }
                });
                return sites.filter(s => s.url && s.url.startsWith('http')).slice(0, 200);
            }''')
        except Exception as e:
            logger.error(f'motionsites error: {e}')
        
        browser.close()
    return items


def collect_generic_site(name, url):
    """Generic scraper for any site"""
    from playwright.sync_api import sync_playwright
    
    items = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        try:
            page.goto(url, wait_until='domcontentloaded', timeout=30000)
            time.sleep(5)
            
            for _ in range(3):
                page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                time.sleep(2)
            
            items = page.evaluate('''() => {
                const results = [];
                // Get all links with images (likely cards/templates)
                const links = document.querySelectorAll('a[href]');
                links.forEach(a => {
                    const img = a.querySelector('img');
                    const title = a.querySelector('h2, h3, h4, [class*="title"], [class*="name"]');
                    const desc = a.querySelector('p, [class*="desc"], [class*="text"]');
                    if (img || title) {
                        results.push({
                            url: a.href,
                            title: title ? title.textContent.trim().substring(0, 100) : a.textContent.trim().substring(0, 100),
                            description: desc ? desc.textContent.trim().substring(0, 200) : '',
                            image: img ? (img.src || img.dataset.src || '') : '',
                        });
                    }
                });
                // Deduplicate by URL
                const seen = new Set();
                return results.filter(r => {
                    if (seen.has(r.url)) return false;
                    seen.add(r.url);
                    return true;
                }).slice(0, 500);
            }''')
        except Exception as e:
            logger.error(f'{name} error: {e}')
        
        browser.close()
    return items


def save_site(name, items, source_url):
    """Save collected items for a site"""
    site_dir = BASE / name
    site_dir.mkdir(parents=True, exist_ok=True)
    items_dir = site_dir / 'items'
    items_dir.mkdir(exist_ok=True)
    
    index = []
    for i, item in enumerate(items):
        item_id = item.get('slug', item.get('id', str(i)))
        if not item_id:
            item_id = str(i)
        item_id = str(item_id).lower().replace(' ', '-')[:50]
        
        meta = {k: v for k, v in item.items() if v}
        meta['collected_at'] = datetime.now(timezone.utc).isoformat()
        
        (items_dir / f'{item_id}.json').write_text(json.dumps(meta, indent=2), encoding='utf-8')
        index.append(meta)
    
    (site_dir / 'index.json').write_text(json.dumps({
        'source': source_url,
        'total': len(items),
        'exported_at': datetime.now(timezone.utc).isoformat(),
        'items': index,
    }, indent=2), encoding='utf-8')
    
    return len(items)


def main():
    from datetime import datetime, timezone
    
    sites = [
        ('land-book', 'https://land-book.com/'),
        ('posts-design', 'https://posts.design/'),
        ('motionsites', 'https://motionsites.com/'),
        ('peachweb', 'https://peachweb.dev/'),
        ('gradient-lab', 'https://www.gradientlab.xyz/'),
        ('grainient-supply', 'https://www.grainient.supply/'),
        ('unicorn-platform', 'https://unicorn.platform/'),
    ]
    
    total = 0
    
    # recent.design has an API
    logger.info('Collecting recent.design...')
    items = collect_recent_design()
    if items:
        count = save_site('recent-design', items, 'https://recent.design/')
        logger.info(f'recent.design: {count} items')
        total += count
    
    # Scrape other sites
    for name, url in sites:
        logger.info(f'Collecting {name}...')
        try:
            items = collect_generic_site(name, url)
            count = save_site(name, items, url)
            logger.info(f'{name}: {count} items')
            total += count
        except Exception as e:
            logger.error(f'{name} failed: {e}')
    
    # Try posts-design and motionsites with dedicated scrapers
    for name, fn in [('posts-design', collect_posts_design), ('motionsites', collect_motionsites)]:
        try:
            items = fn()
            if items:
                count = save_site(name, items, f'https://{name.replace("-","")}.com/')
                logger.info(f'{name} (dedicated): {count} items')
        except Exception as e:
            logger.error(f'{name} dedicated failed: {e}')
    
    logger.info(f'Total: {total} items across all sites')


if __name__ == '__main__':
    main()
