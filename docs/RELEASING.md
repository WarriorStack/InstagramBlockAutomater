# Release Checklist

- [ ] Run `python -m compileall .`
- [ ] Run `python -m pytest`
- [ ] Review `git status`
- [ ] Review staged diff
- [ ] Confirm no personal data is present
- [ ] Confirm `chrome_profile/` is ignored
- [ ] Confirm databases/exports are ignored
- [ ] Update README/release notes
- [ ] Tag using semantic versioning, e.g. `v0.1.0`
- [ ] Publish GitHub Release notes
