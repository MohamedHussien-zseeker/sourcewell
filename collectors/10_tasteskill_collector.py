"""
TasteSkill Collector
Collects all design skills/prompts from https://github.com/Leonxlnx/taste-skill
Source: GitHub repo (67k+ stars)
"""

import json
import logging
import time
import requests
from datetime import datetime, timezone
from pathlib import Path
import os

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s',
    handlers=[logging.FileHandler('tasteskill_collector.log'), logging.StreamHandler()])
logger = logging.getLogger(__name__)

ROOT = Path(os.environ.get('SOURCEWELL_ROOT', str(Path(__file__).resolve().parent.parent / 'data')))
BASE_DIR = ROOT / 'taste-skill'
GITHUB_RAW = 'https://raw.githubusercontent.com/Leonxlnx/taste-skill/main'
REPO_API = 'https://api.github.com/repos/Leonxlnx/taste-skill'

SKILLS = [
    'taste-skill', 'taste-skill-v1', 'gpt-tasteskill', 'brutalist-skill',
    'minimalist-skill', 'soft-skill', 'stitch-skill', 'output-skill',
    'redesign-skill', 'brandkit', 'image-to-code-skill',
    'imagegen-frontend-web', 'imagegen-frontend-mobile',
]


class TasteSkillCollector:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': 'Mozilla/5.0'})
        self.results = []

    def collect_all(self):
        # Fetch main skill
        logger.info('Fetching main taste-skill...')
        r = self.session.get(f'{GITHUB_RAW}/skills/taste-skill/SKILL.md', timeout=20)
        if r.status_code == 200:
            self.results.append({
                'name': 'taste-skill',
                'description': 'Anti-slop frontend skill for landing pages, portfolios, and redesigns',
                'content': r.text,
                'size': len(r.text),
                'is_default': True,
            })

        # Fetch all other skills
        for skill in SKILLS:
            if skill == 'taste-skill':
                continue
            logger.info(f'Fetching {skill}...')
            r = self.session.get(f'{GITHUB_RAW}/skills/{skill}/SKILL.md', timeout=20)
            if r.status_code == 200:
                # Extract description from frontmatter
                desc = ''
                if 'description:' in r.text:
                    for line in r.text.split('\n'):
                        if line.startswith('description:'):
                            desc = line.split('description:', 1)[1].strip()
                            break

                self.results.append({
                    'name': skill,
                    'description': desc,
                    'content': r.text,
                    'size': len(r.text),
                    'is_default': False,
                })
            time.sleep(0.3)

        # Fetch llms.txt
        logger.info('Fetching llms.txt...')
        r = self.session.get(f'{GITHUB_RAW}/skills/llms.txt', timeout=15)
        if r.status_code == 200:
            (BASE_DIR / 'llms.txt').write_text(r.text, encoding='utf-8')

        logger.info(f'Total: {len(self.results)} skills')

    def save(self):
        BASE_DIR.mkdir(parents=True, exist_ok=True)
        skills_dir = BASE_DIR / 'skills'
        skills_dir.mkdir(exist_ok=True)

        index = []
        for skill in self.results:
            # Save as .md file
            (skills_dir / f'{skill["name"]}.md').write_text(skill['content'], encoding='utf-8')

            # Save metadata
            meta = {k: v for k, v in skill.items() if k != 'content'}
            (skills_dir / f'{skill["name"]}.json').write_text(json.dumps(meta, indent=2), encoding='utf-8')
            index.append(meta)

        # Root files
        (BASE_DIR / 'index.json').write_text(json.dumps({
            'source': 'https://github.com/Leonxlnx/taste-skill',
            'website': 'https://www.tasteskill.dev',
            'stars': 67581,
            'total': len(self.results),
            'exported_at': datetime.now(timezone.utc).isoformat(),
            'skills': index,
        }, indent=2), encoding='utf-8')

        lines = [f'# TasteSkill Design Skills ({len(self.results)} collected)\n']
        lines.append(f'Source: https://github.com/Leonxlnx/taste-skill (67k+ stars)\n\n')
        lines.append('| # | Skill | Size | Description |\n')
        lines.append('|---|-------|------|-------------|\n')
        for i, m in enumerate(index, 1):
            desc = (m.get('description', '') or '')[:60]
            lines.append(f'| {i} | {m["name"]} | {m["size"]}b | {desc} |\n')
        (BASE_DIR / 'MANIFEST.md').write_text(''.join(lines), encoding='utf-8')

        logger.info(f'Saved: {len(self.results)} skills')


def main():
    BASE_DIR.mkdir(parents=True, exist_ok=True)
    collector = TasteSkillCollector()
    collector.collect_all()
    collector.save()
    print(f'\nDone: {len(collector.results)} skills collected')


if __name__ == '__main__':
    main()
