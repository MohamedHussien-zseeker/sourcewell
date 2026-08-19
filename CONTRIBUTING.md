# Contributing to Sourcewell

Thanks for your interest in improving Sourcewell. This is a small, focused tool,
so contributions are welcome but keep them tight.

## Ground rules
1. **No secrets, ever.** Never commit API keys, session cookies, or tokens. All
   credentials stay in `.env` (gitignored) or environment variables. The repo
   must remain safe to make public.
2. **No collected data in the repo.** `./data/`, generated `data.js`, and
   `*.log` are gitignored on purpose. Don't force-add them.
3. **Respect licensing.** Don't add collectors for sources you aren't allowed
   to access, and don't bake in paywalled content.

## How to contribute
1. Fork and create a feature branch.
2. Keep collectors self-contained: one source per file, named `NN_name_collector.py`,
   reading any credentials from `os.environ`.
3. Run `python -m py_compile collectors/*.py build/*.py run_all.py` before pushing.
4. Update `README.md` / `AUTH_GUIDE.md` if you add a new credential or source.
5. Open a PR with a clear description of what changed and why.

## Adding a new collector
- Copy an existing `collectors/NN_*.py` as a template.
- Write output to `ROOT / '<source>'` where `ROOT` comes from `SOURCEWELL_ROOT`.
- Document the required env var in `.env.example` and `AUTH_GUIDE.md`.
- Keep the script runnable with `--limit` for safe testing where it fetches a lot.

## Code style
- Plain Python 3, stdlib + `requests` + `python-dotenv` + `playwright` only.
- No frameworks. Readability over cleverness.
