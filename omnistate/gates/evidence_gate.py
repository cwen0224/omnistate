# -*- coding: utf-8 -*-
"""
OMNISTATE Evidence Verification Gate
Validates that required physical verification proof files exist and are non-empty.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

from omnistate.gates.base import BaseGate, GateResult


class EvidenceGate(BaseGate):
    """Verifies that empirical evidence artifacts exist, are non-empty, and valid."""

    @property
    def name(self) -> str:
        return "EvidenceVerificationGate"

    def evaluate(self, root_dir: Path, context: Dict[str, Any]) -> GateResult:
        evidence_required: bool = context.get("evidence_required", False)
        evidence_paths: List[str] = context.get("evidence_paths", [])

        if not evidence_required and not evidence_paths:
            return GateResult(
                gate_name=self.name,
                passed=True,
                details={"status": "not_required"},
            )

        if evidence_required and not evidence_paths:
            return GateResult(
                gate_name=self.name,
                passed=False,
                errors=["Evidence is strictly required by policy, but no evidence paths were provided."],
            )

        missing_or_empty: List[str] = []
        verified: List[str] = []

        for p_str in evidence_paths:
            p = (root_dir / p_str).resolve()
            if not p.exists():
                missing_or_empty.append(f"{p_str} (does not exist)")
            elif p.is_file() and p.stat().st_size == 0:
                missing_or_empty.append(f"{p_str} (empty file)")
            else:
                verified.append(p_str)

        if missing_or_empty:
            return GateResult(
                gate_name=self.name,
                passed=False,
                errors=[f"Invalid evidence files: {missing_or_empty}"],
                details={"missing_or_empty": missing_or_empty, "verified": verified},
            )

        return GateResult(
            gate_name=self.name,
            passed=True,
            details={"verified_count": len(verified), "verified": verified},
        )
