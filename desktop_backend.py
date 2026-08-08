from __future__ import annotations

import os

import uvicorn

from app.api.operator_console import app


def main() -> None:
    """Run the private API/UI server owned by the desktop application."""
    uvicorn.run(
        app,
        host=os.getenv("TRADINGENGINE_HOST", "127.0.0.1"),
        port=int(os.getenv("TRADINGENGINE_PORT", "8001")),
        reload=False,
        access_log=False,
        log_level=os.getenv("TRADINGENGINE_LOG_LEVEL", "warning"),
    )


if __name__ == "__main__":
    main()
