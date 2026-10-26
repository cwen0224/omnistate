# -*- coding: utf-8 -*-
"""
OMNISTATE Scope Enclosure Gate
Ensures that modified files strictly stay within declared boundary scopes.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Set

from omnistate.gates.base import BaseGate, GateResult


def is_path_in_scope(rel_path: str, scope_paths: List[str], state_dir_name: str = ".omnistate") -> bool:
    norm_rel = rel_path.replace("\\", "/").strip()
    while norm_rel.startswith("./"):
        norm_rel = norm_rel[2:]
    
    clean_state_dir = state_dir_name.replace("\\", "/").strip()
    while clean_state_dir.startswith("./"):
        clean_state_dir = clean_state_dir[2:]
    
    # State governance directory itself is always permitted
    if norm_rel.startswith(f"{clean_state_dir}/") or norm_rel == clean_state_dir:
        return True
        
    if not scope_paths or "*" in scope_paths:
        return True

    for sp in scope_paths:
        norm_sp = sp.replace("\\", "/").strip("`").strip()
        while norm_sp.startswith("./"):
            norm_sp = norm_sp[2:]
        if norm_sp.endswith("/"):
            if norm_rel.startswith(norm_sp) or norm_rel == norm_sp.rstrip("/"):
                return True
        else:
            if norm_rel == norm_sp or norm_rel.startswith(norm_sp + "/"):
                return True
    return False


class ScopeGate(BaseGate):
    """Enforces that AI modifications do not escape declared scope boundaries."""

    @property
    def name(self) -> str:
        return "ScopeEnclosureGate"

    def evaluate(self, root_dir: Path, context: Dict[str, Any]) -> GateResult:
        scope_paths = context.get("scope_paths", [])
        modified_files = context.get("modified_files", [])
        state_dir_name = context.get("state_dir_name", ".omnistate")

        violations: List[str] = []
        for file_path in modified_files:
            if not is_path_in_scope(file_path, scope_paths, state_dir_name):
                violations.append(file_path)

        if violations:
            return GateResult(
                gate_name=self.name,
                passed=False,
                errors=[
                    f"Files modified outside declared scope {scope_paths}: {violations}"
                ],
                details={"violations": violations, "scope_paths": scope_paths},
            )

        return GateResult(
            gate_name=self.name,
            passed=True,
            details={"checked_files_count": len(modified_files), "scope_paths": scope_paths},
        )
