"""
UI Skills Collector
Collects all design skills from https://www.ui-skills.com/
Source: GitHub repo ibelick/ui-skills (6.3k stars) + website
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
    handlers=[logging.FileHandler('uiskills_collector.log'), logging.StreamHandler()])
logger = logging.getLogger(__name__)

ROOT = Path(os.environ.get('SOURCEWELL_ROOT', str(Path(__file__).resolve().parent.parent / 'data')))
BASE_DIR = ROOT / 'ui-skills'
GITHUB_RAW = 'https://raw.githubusercontent.com/ibelick/ui-skills/main'

# All skills from website
SKILLS = [
    'ibelick/ui-skills-root', 'ibelick/improve-ui', 'anthropics/frontend-design',
    'mengto/design-taste-frontend', 'emilkowalski/improve-animations',
    'millionco/improve-react', 'shadcn/improve', 'shadcn-ui/shadcn',
    'jakubkrehel/better-ui', '0xdesign/design-lab', 'nextlevelbuilder/ui-ux-pro-max',
    'dammyjay93/interface-design', 'raphaelsalaja/12-principles-of-animation',
    'pbakaus/impeccable', 'bencium/bencium-innovative-ux-designer',
    'leonxlnx/gpt-tasteskill', 'antfu/web-design-guidelines', 'rams/rams',
    'wshobson/interaction-design', 'addyosmani/frontend-ui-engineering',
    'ibelick/create-design-md', 'jakubkrehel/make-interfaces-feel-better'
]


class UISkillsCollector:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': 'Mozilla/5.0'})
        self.results = []

    def fetch_github_skill(self, author, name):
        """Try to fetch skill from GitHub repo"""
        # Try multiple paths
        paths = [
            f'skills/{name}/SKILL.md',
            f'skills/{name}/skill.md',
            f'skills/{name}/prompt.md',
        ]
        for path in paths:
            r = self.session.get(f'{GITHUB_RAW}/{path}', timeout=15)
            if r.status_code == 200:
                return r.text
        return None

    def collect_all(self):
        for idx, skill_path in enumerate(SKILLS, 1):
            author, name = skill_path.split('/')
            logger.info(f'[{idx}/{len(SKILLS)}] {skill_path}')

            content = self.fetch_github_skill(author, name)

            if not content:
                # Try alternate name patterns
                alt_names = [name.replace('-', '_'), name.replace('_', '-')]
                for alt in alt_names:
                    content = self.fetch_github_skill(author, alt)
                    if content:
                        break

            if content:
                # Extract description from frontmatter
                desc = ''
                if 'description:' in content[:500]:
                    match = re.search(r'description:\s*(.+)', content[:500])
                    if match:
                        desc = match.group(1).strip().strip('"').strip("'")

                self.results.append({
                    'name': name,
                    'author': author,
                    'description': desc,
                    'content': content,
                    'size': len(content),
                    'source_url': f'https://www.ui-skills.com/skills/{skill_path}',
                    'github_url': f'https://github.com/ibelick/ui-skills/tree/main/skills/{name}',
                    'collected_at': datetime.now(timezone.utc).isoformat(),
                })
                logger.info(f'  Got {len(content)} bytes')
            else:
                logger.warning(f'  Not found on GitHub')

            time.sleep(0.3)

    def save(self):
        BASE_DIR.mkdir(parents=True, exist_ok=True)
        skills_dir = BASE_DIR / 'skills'
        skills_dir.mkdir(exist_ok=True)

        index = []
        for skill in self.results:
            # Save as .md
            (skills_dir / f'{skill["name"]}.md').write_text(skill['content'], encoding='utf-8')
            # Save metadata
            meta = {k: v for k, v in skill.items() if k != 'content'}
            (skills_dir / f'{skill["name"]}.json').write_text(json.dumps(meta, indent=2), encoding='utf-8')
            index.append(meta)

        (BASE_DIR / 'index.json').write_text(json.dumps({
            'source': 'https://www.ui-skills.com',
            'github': 'https://github.com/ibelick/ui-skills',
            'total': len(self.results),
            'exported_at': datetime.now(timezone.utc).isoformat(),
            'skills': index,
        }, indent=2), encoding='utf-8')

        lines = [f'# UI Skills ({len(self.results)} collected)\n']
        lines.append(f'Source: https://www.ui-skills.com | GitHub: ibelick/ui-skills (6.3k stars)\n\n')
        lines.append('| # | Skill | Author | Size |\n')
        lines.append('|---|-------|--------|------|\n')
        for i, m in enumerate(index, 1):
            lines.append(f'| {i} | {m["name"]} | {m["author"]} | {m["size"]}b |\n')
        (BASE_DIR / 'MANIFEST.md').write_text(''.join(lines), encoding='utf-8')
        logger.info(f'Saved: {len(self.results)} skills')


def main():
    BASE_DIR.mkdir(parents=True, exist_ok=True)
    collector = UISkillsCollector()
    collector.collect_all()
    collector.save()
    print(f'\nDone: {len(collector.results)} skills')


if __name__ == '__main__':
    main()
