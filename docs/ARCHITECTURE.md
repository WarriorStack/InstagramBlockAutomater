# Architecture

## Components

- `app.py`: PySide6 UI and dashboard.
- `importer.py`: TXT/CSV/JSON normalization and extraction.
- `database.py`: SQLite persistence.
- `instagram.py`: isolated browser integration layer.

## Principles

- Local-first storage
- No credentials in source
- Separation of concerns
- Observable state transitions
- Recoverable failures
- Testable components

As the project grows, consider moving toward:

```text
src/
  ui/
  services/
  storage/
  browser/
tests/
docs/
.github/
```
