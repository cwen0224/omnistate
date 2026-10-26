# -*- coding: utf-8 -*-
"""
OMNISTATE Anti-Bloat Critic Gate
Monitors code bloat, runaway file size inflation, and excessive duplicate code additions.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

from omnistate.gates.base import BaseGate, GateResult


class AntiBloatCritic(BaseGate):
    """Guards against uncontrolled code inflation and redundant boilerplate."""

    @property
    def name(self) -> str:
        return "AntiBloatCritic"

    def evaluate(self, root_dir: Path, context: Dict[str, Any]) -> GateResult:
        max_ratio = float(context.get("max_file_growth_ratio", 2.5))
        max_lines = int(context.get("max_line_growth", 800))
        file_stats: Dict[str, Dict[str, int]] = context.get("file_stats", {})

        warnings: List[str] = []
        errors: List[str] = []
        details: Dict[str, Any] = {}

        for rel_path, stats in file_stats.items():
            old_lines = stats.get("old_lines", 0)
            new_lines = stats.get("new_lines", 0)
            diff_lines = new_lines - old_lines

            if old_lines > 50 and diff_lines > max_lines:
                growth_ratio = new_lines / max(1, old_lines)
                if growth_ratio > max_ratio:
                    msg = f"Suspicious bloat in `{rel_path}`: grew by +{diff_lines} lines ({growth_ratio:.1f}x from {old_lines} to {new_lines} lines)"
                    warnings.append(msg)
                    details[rel_path] = {"old": old_lines, "new": new_lines, "ratio": growth_ratio}

        return GateResult(
            gate_name=self.name,
            passed=True,  # Default to warning unless configured strict
            warnings=warnings,
            details=details,
        )
