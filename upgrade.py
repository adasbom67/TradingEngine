from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

PROTECTED = ("data", "logs", "reports", ".env", "token.json")


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a local runtime backup and verify an upgraded TradingEngine tree")
    parser.add_argument("--backup-directory", default="backups")
    parser.add_argument("--skip-tests", action="store_true")
    args = parser.parse_args()
    root = Path(__file__).resolve().parent
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    destination = root / args.backup_directory / stamp
    destination.mkdir(parents=True, exist_ok=True)
    for name in PROTECTED:
        source = root / name
        if source.is_dir():
            shutil.copytree(source, destination / name, dirs_exist_ok=True)
        elif source.is_file():
            shutil.copy2(source, destination / name)
    result = subprocess.run([sys.executable, str(root / "verify.py"), *( ["--skip-tests"] if args.skip_tests else [] )])
    print(f"Runtime backup: {destination}")
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
