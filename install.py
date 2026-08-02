from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Install TradingEngine dependencies and verify the deployment")
    parser.add_argument("--skip-install", action="store_true")
    parser.add_argument("--skip-tests", action="store_true")
    args = parser.parse_args()
    root = Path(__file__).resolve().parent
    if not args.skip_install:
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", str(root / "requirements.txt")], check=True)
    result = subprocess.run([sys.executable, str(root / "verify.py"), *( ["--skip-tests"] if args.skip_tests else [] )])
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
