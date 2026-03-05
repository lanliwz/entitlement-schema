# Changelog

## v1.1.0 - 2026-03-05

- Standardized ontology naming/storage conventions and RDF-first workflow documentation.
- Added global release packaging flow:
  - `VERSION`
  - `RELEASE.md`
  - `scripts/package_release.sh`
  - `system_config.example.ini`
- Added setuptools packaging via `setup.py`.
- Updated demo speech assets:
  - renamed demo readme to `demo/README4DEMO.md`
  - added review narration script `demo/speech_script/review_script_v1.txt`
- Improved runtime compatibility:
  - LangChain 1.2 style message invocation updates
  - environment variable expansion in config loader
  - tracer-safe entitlement state keys
