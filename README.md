# Instagram Account Manager

> Privacy-first desktop tooling for importing, cleaning, tracking, and processing Instagram username lists locally.

![Python](https://img.shields.io/badge/Python-3.11%2B-blue)
![PySide6](https://img.shields.io/badge/UI-PySide6-green)
![Playwright](https://img.shields.io/badge/Browser-Playwright-orange)
![License](https://img.shields.io/badge/License-MIT-purple)

## ✨ Features

- 📥 TXT / CSV / JSON import
- 🧹 Username normalization and deduplication
- 🔎 Search and filtering
- 🗃️ Local SQLite persistence
- 📊 Status dashboard and progress tracking
- 🟢 Pending / Blocked / Skipped / Failed states
- 📤 CSV export
- 🌐 Optional Playwright browser integration
- 🔒 Local-first runtime data

## 🖥️ Screenshots

Store screenshots in `assets/` only after removing personal usernames and other private data.

Example:

```text
assets/dashboard.png
```

## 🏗️ Architecture

```text
TXT / CSV / JSON
       ↓
Importer
       ↓
Normalize + deduplicate
       ↓
SQLite
       ↓
PySide6 UI
       ↓
Browser integration
```

## 🚀 Setup

```bash
git clone https://github.com/YOUR_USERNAME/InstagramAccountManager.git
cd InstagramAccountManager
python -m pip install -r requirements.txt
python -m playwright install chromium
python app.py
```

## 📦 Supported formats

TXT:

```text
alice
@bob
charlie
```

CSV:

```csv
username
alice
bob
charlie
```

JSON:

The importer recursively handles nested JSON and common username/value fields used by exported data.

## 🔐 Privacy

The application is designed to keep runtime data local.

Never commit:

- personal follower lists
- `data/`
- `exports/`
- `chrome_profile/`
- databases
- cookies or browser storage
- passwords, tokens, or API keys
- screenshots containing private usernames

Before pushing:

```bash
git status
git diff --cached
```

## ⚠️ Third-party platform disclaimer

This is an independent project and is not affiliated with or endorsed by Instagram or Meta.

Users are responsible for complying with the terms, policies, and applicable laws governing third-party platforms.

## 🧪 Development

```bash
python -m compileall .
python -m pytest
```

## 🛣️ Roadmap

- [ ] Import preview
- [ ] Background worker for long browser tasks
- [ ] Pause / resume queue
- [ ] Retry queue
- [ ] Dark mode
- [ ] Windows executable release
- [ ] Broader automated test coverage
- [ ] More accessibility-first selectors

## 🤝 Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## 🛡️ Security

See [SECURITY.md](SECURITY.md).

## 📄 License

MIT License — see [LICENSE](LICENSE).
