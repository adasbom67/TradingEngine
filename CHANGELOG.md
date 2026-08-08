# Changelog

## [0.9.3] — 2026-08-08

### Added
- Electron desktop workstation
- Windows installer and portable executable builds
- Packaged Python/FastAPI backend
- Automatic private-backend startup, health waiting, and shutdown
- Single-window workflow for recommendations, backtesting, dashboards, and paper trading
- Same-origin production UI/API hosting and Vite development proxy
- Reproducible desktop build script and packaging documentation

### Validation
- 191 Python tests passing
- Vite production build passing
- Packaged API and UI return HTTP 200 from the private loopback service
- Constrained live SPY scan completed with one symbol succeeded, zero failed, and three candidates
- Desktop shutdown confirmed to terminate the owned backend process

### Safety
- Backend binds only to a dynamically allocated `127.0.0.1` port
- Electron renderer has Node integration disabled, context isolation enabled, and sandboxing enabled
- Schwab secrets and OAuth tokens are not embedded in desktop artifacts
- Live broker-order submission remains disabled

## [0.9.0] — 2026-08-04

### Added
- React Operator Console
- Command Center Intelligence
- Backtesting workspace
- Recommendation workspace
- Optional recommendation constraints
- Trading profiles
- Recommendation history
- Quote audit
- Recommendation diagnostics
- Recommendation pipeline validation
- FastAPI operator-console endpoints
- Expanded automated test coverage

### Validation
- 185 Python tests passing
- Vite production build passing

### Safety
- Research Mode
- Read-only execution
- Paper and live order submission disabled
