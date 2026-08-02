# Release Process

## Release candidate

1. Work on `develop`.
2. Update `VERSION` and `config/runtime.json`.
3. Run `pytest -q`.
4. Run representative commands, including `python main.py config validate` and `python main.py health`.
5. Update release notes and changelog.
6. Commit and push `develop`.

## Stable release

1. Merge verified `develop` into `main`.
2. Run the full test suite again on `main`.
3. Tag the release using semantic versioning.
4. Push `main` and the tag.
5. Create GitHub release notes from `docs/releases/`.

## Versioning policy

- Patch (`0.9.1`): production hardening, fixes, documentation, compatible improvements.
- Minor (`0.10.0`): substantial new pre-live capability.
- Major (`1.0.0`): controlled live trading approved for operational use.

## Rollback

Stable tags are immutable recovery points. If a release candidate fails verification, return to the last stable tag and correct the issue on `develop`; never rewrite a published stable tag.
