from __future__ import annotations

import compileall
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class VerificationResult:
    compilation_ok: bool
    tests_ok: bool
    test_output: str

    @property
    def successful(self) -> bool:
        return self.compilation_ok and self.tests_ok


class DeploymentVerifier:
    """Run repeatable local pre-release verification checks."""

    def verify(self, project_root: str | Path = ".", *, run_tests: bool = True) -> VerificationResult:
        root = Path(project_root)
        compilation_ok = compileall.compile_dir(root / "app", quiet=1)
        if not run_tests:
            return VerificationResult(compilation_ok, True, "Tests skipped.")
        completed = subprocess.run(
            [sys.executable, "-m", "pytest", "-q"],
            cwd=root,
            capture_output=True,
            text=True,
            check=False,
        )
        output = (completed.stdout + completed.stderr).strip()
        return VerificationResult(compilation_ok, completed.returncode == 0, output)
