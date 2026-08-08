# TradingEngine Desktop Application

## Outcome

TradingEngine is distributed as a Windows desktop application. Opening the application starts its private Python service automatically, waits for it to become healthy, and then opens the Operator Console in a native Electron window. Closing the window also stops the private service.

Recommendation scans, paper-trading actions, dashboards, and backtests no longer require the user to start `operator_api.py`, Vite, PowerShell, or VS Code separately.

## Build

From the project root:

```powershell
powershell -ExecutionPolicy Bypass -File .\packaging\build_desktop.ps1
```

The first build installs the isolated Python and Node build dependencies. Later builds may use `-SkipDependencyInstall` when the lockfile and Python requirements have not changed.

The finished artifacts are written to:

```text
operator-console\release
```

The release directory contains:

- a Windows installer that creates desktop and Start Menu shortcuts;
- a portable executable that can be opened directly without installation;
- an unpacked build used for smoke testing.

## Runtime ownership

The Electron main process owns the entire desktop lifecycle:

1. It allocates an available loopback port.
2. It launches the packaged Python backend with no console window.
3. It waits for `/api/version` to respond.
4. It opens the native window only after the backend is ready.
5. It terminates the backend when TradingEngine closes.

The backend serves both the compiled React UI and `/api` routes from the same loopback origin. The service is bound only to `127.0.0.1` and is not exposed to the network.

## Existing local data

When the desktop executable is built and run from this repository, it automatically discovers the project root and reuses the existing local `.env`, Schwab token, configuration, recommendation history, and paper ledger.

For a standalone installation, writable runtime data is stored under the application's Windows user-data directory. Default non-secret configuration is copied there on first launch. Secrets are never embedded into the installer.

## Safety

Desktop packaging changes application startup and distribution only. It does not enable live broker orders. The existing research, read-only, and simulation-only safeguards remain in force.
