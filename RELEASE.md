# Release Packaging

## Build release package

Run from repository root:

```bash
bash scripts/package_release.sh
```

Outputs in `dist/`:

- `entitlement-schema-v<version>.tar.gz`
- `entitlement-schema-v<version>.tar.gz.sha256`
- `entitlement-schema-v<version>.manifest.txt`

## Versioning

- Update `VERSION` before packaging.
- Keep release notes in commit message or tag annotation.

## Configuration handling

- Do not ship `system_config.ini` with machine-local credentials.
- Use `system_config.example.ini` in release artifacts.
