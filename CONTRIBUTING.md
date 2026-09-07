# Contributing

Thanks for contributing.

## Development

```bash
python -m pip install -r requirements.txt
python -m playwright install chromium
```

## Before submitting a PR

- Keep changes focused.
- Do not commit credentials, browser profiles, databases, or personal data.
- Run `python -m compileall .`.
- Run `python -m pytest`.
- Update docs for behavior changes.

## Commit style

Use clear messages:

```text
feat: add JSON import preview
fix: handle malformed JSON
docs: improve setup instructions
test: add importer coverage
refactor: separate browser lifecycle
```
