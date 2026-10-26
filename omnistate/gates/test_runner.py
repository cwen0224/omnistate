# -*- coding: utf-8 -*-
"""
OMNISTATE Test Suite Runner Gate
Executes project test suites (pytest, npm test, cargo test, etc.) and enforces passing status.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from omnistate.gates.base import BaseGate, GateResult


class TestRunnerGate(BaseGate):
    """Executes automated tests to verify regression-free changes."""

    @property
    def name(self) -> str:
        return "TestRunnerGate"

    def evaluate(self, root_dir: Path, context: Dict[str, Any]) -> GateResult:
        cmd_str: Optional[str] = context.get("test_command")
        if not cmd_str or not cmd_str.strip():
            return GateResult(
                gate_name=self.name,
                passed=True,
                details={"status": "skipped", "reason": "No test command configured."},
            )

        try:
            res = subprocess.run(
                cmd_str,
                shell=True,
                cwd=str(root_dir),
                capture_output=True,
                text=True,
                timeout=300,
            )
            passed = (res.returncode == 0)
            output_snippet = (res.stdout + "\n" + res.stderr)[-1000:].strip()
            
            if not passed:
                return GateResult(
                    gate_name=self.name,
                    passed=False,
                    errors=[f"Test suite failed with exit code {res.returncode}: {cmd_str}"],
                    details={"returncode": res.returncode, "output": output_snippet},
                )

            return GateResult(
                gate_name=self.name,
                passed=True,
                details={"returncode": 0, "output": output_snippet},
            )
        except subprocess.TimeoutExpired:
            return GateResult(
                gate_name=self.name,
                passed=False,
                errors=[f"Test command timed out after 300s: {cmd_str}"],
            )
        except Exception as e:
            return GateResult(
                gate_name=self.name,
                passed=False,
                errors=[f"Failed to execute test command '{cmd_str}': {e}"],
            )
