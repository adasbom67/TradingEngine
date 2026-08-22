# TradingEngine Architecture

The canonical architecture is maintained in [docs/SYSTEM_OVERVIEW.md](docs/SYSTEM_OVERVIEW.md), especially:

- **Runtime architecture** for the Electron, React, FastAPI, domain, storage, and Schwab boundaries;
- **Major code areas** for module ownership;
- **Primary workflows** for recommendations, paper trading, and Critical Events;
- **API surface** and **Local state and configuration** for runtime integration details;
- **Safety invariants** for the system trust boundary.

This file remains as a stable entry point for existing links. Architecture changes should be made in the system overview rather than duplicated here.
