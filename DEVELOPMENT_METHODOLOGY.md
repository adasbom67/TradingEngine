# Development Methodology

## Guiding principles

1. Research before automation.
2. Paper trading before live trading.
3. No feature is complete until it passes the full local test suite.
4. Results verified on the user's Windows environment are the release authority.
5. Trading logic and operational infrastructure remain modular.
6. Configuration replaces hard-coded operational values where practical.
7. Safety, observability, and auditability precede live capital deployment.

## Branch model

- `main`: stable, tagged, releasable code.
- `develop`: active integration branch.
- Optional feature branches: isolated high-risk or large changes.

## Development cycle

1. Confirm the active milestone in `PROJECT_STATUS.md`.
2. Implement one coherent increment on `develop`.
3. Add or update automated tests.
4. Run the complete suite locally.
5. Validate representative CLI workflows.
6. Update the system overview and applicable focused supplements.
7. Commit and push `develop`.
8. Merge into `main` only after local verification.
9. Tag the release from `main`.

## Definition of done

A milestone is complete only when:

- implementation is present;
- automated tests pass locally;
- expected CLI behavior is verified;
- secrets and generated runtime data are excluded from Git;
- documentation reflects the new state;
- known limitations are stated explicitly.

## Future-session restart procedure

At the beginning of every future session:

1. Read `docs/SYSTEM_OVERVIEW.md`.
2. Read `PROJECT_STATUS.md`.
3. Read the active section of `ROADMAP.md`.
4. Review the latest entry in `CHANGELOG.md`.
5. Confirm the current Git branch and test count.
6. Continue from the current working milestone.

## Operational-readiness increment checklist

Every operational-readiness increment must include:

1. Failure-mode analysis.
2. Bounded recovery behavior.
3. Automated tests for both success and failure paths.
4. Operator-facing diagnostics.
5. Release notes and continuity-document updates.
6. Local verification on Windows before promotion from `develop`.
