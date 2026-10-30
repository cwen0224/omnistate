# -*- coding: utf-8 -*-
"""Deterministic planning completeness gate."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

from omnistate.gates.base import BaseGate, GateResult


class PlanningGate(BaseGate):
    """Blocks planned transactions with missing memo, checklist, or task evidence."""

    @property
    def name(self) -> str:
        return "PlanningGate"

    def evaluate(self, root_dir: Path, context: Dict[str, Any]) -> GateResult:
        planning = context.get("planning", {})
        if not planning.get("required", False):
            return GateResult(self.name, True, details={"required": False})

        errors: List[str] = []
        memo = planning.get("memo", {})
        checklist = planning.get("checklist", [])
        subtasks = planning.get("subtasks", [])
        if not memo.get("original_prompt"):
            errors.append("Requirement memo must preserve the original prompt.")
        if not checklist:
            errors.append("At least one checklist item is required before audit.")
        unfinished = [
            item.get("check_id", "unknown")
            for item in checklist
            if item.get("status") not in {"PASS", "DEFERRED"}
        ]
        if unfinished:
            errors.append(f"Checklist items are not complete: {unfinished}")
        missing_subtasks = [
            item.get("check_id", "unknown")
            for item in checklist
            if not item.get("implementation_subtasks") and not item.get("verification_subtasks")
        ]
        if missing_subtasks:
            errors.append(f"Checklist items lack linked subtasks: {missing_subtasks}")
        invalid_subtasks = [
            task.get("subtask_id", "unknown")
            for task in subtasks
            if task.get("status") not in {"PASS", "CANCELLED"}
        ]
        if invalid_subtasks:
            errors.append(f"Subtasks are not complete: {invalid_subtasks}")
        known_ids = {task.get("subtask_id") for task in subtasks}
        for task in subtasks:
            task_id = task.get("subtask_id", "unknown")
            dependencies = task.get("depends_on", [])
            missing = [dependency for dependency in dependencies if dependency not in known_ids]
            if missing:
                errors.append(f"Subtask '{task_id}' has unknown dependencies: {missing}")
            unfinished_dependencies = [
                dependency
                for dependency in dependencies
                if next((candidate for candidate in subtasks if candidate.get("subtask_id") == dependency), {}).get("status") != "PASS"
            ]
            if task.get("status") == "PASS" and unfinished_dependencies:
                errors.append(f"Subtask '{task_id}' passed before dependencies: {unfinished_dependencies}")
        return GateResult(
            self.name,
            not errors,
            errors=errors,
            details={"required": True, "checklist_count": len(checklist), "subtask_count": len(subtasks)},
        )
