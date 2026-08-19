"""Run every collector in sequence.

Respects SOURCEWELL_ROOT / .env keys. Skips collectors whose required key is
missing (logs a warning). Safe to re-run.
"""
import os, sys, subprocess, importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parent
COLLECTORS = sorted((ROOT / 'collectors').glob('*.py'))

# which env var each collector needs (best-effort map; empty = none required)
REQUIRED_KEY = {
    '03_21stdev_collector.py': 'TWENTYFIRST_API_KEY',
    '08_aura_exporter.py': 'AURA_SUPABASE_ANON_KEY',
}

def main():
    # load .env if present
    try:
        from dotenv import load_dotenv
        load_dotenv(ROOT / '.env')
    except Exception:
        pass
    for c in COLLECTORS:
        need = REQUIRED_KEY.get(c.name)
        if need and not os.environ.get(need):
            print(f'[skip] {c.name} — missing {need}')
            continue
        print(f'[run ] {c.name}')
        try:
            subprocess.run([sys.executable, str(c)], cwd=str(ROOT), check=False)
        except KeyboardInterrupt:
            raise
        except Exception as e:
            print(f'  error: {e}')
    print('\nDone. Collected data is in ./data/ — run build/build_catalog.py next.')

if __name__ == '__main__':
    main()
