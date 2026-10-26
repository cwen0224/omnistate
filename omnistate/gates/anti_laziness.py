# -*- coding: utf-8 -*-
"""
OMNISTATE Anti-Laziness Critic Gate
Scans diffs and modified files for dangerous AI laziness placeholders and omissions.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List, Tuple

from omnistate.gates.base import BaseGate, GateResult

LAZINESS_PATTERNS: List[Tuple[str, str]] = [
    (r"(?i)//\s*\.\.\.\s*(existing|rest|code|unchanged|here)", "Ellipsis comment placeholder"),
    (r"(?i)#\s*\.\.\.\s*(existing|rest|code|unchanged|here)", "Python ellipsis comment placeholder"),
    (r"(?i)/\*\s*\.\.\.\s*\*/", "Block comment ellipsis"),
    (r"(?i)<!--\s*\.\.\.\s*-->", "HTML comment ellipsis"),
    (r"(?i)//\s*(rest of (the )?code|remaining (code|methods|classes|logic)|existing code)\s*(remains?|unchanged)?", "Unfinished rest-of-code note"),
    (r"(?i)#\s*(rest of (the )?code|remaining (code|methods|classes|logic)|existing code)\s*(remains?|unchanged)?", "Unfinished rest-of-code note"),
    (r"(?i)//\s*TODO:\s*(implement|fill in|add here|finish)", "Unimplemented placeholder TODO"),
    (r"(?i)#\s*TODO:\s*(implement|fill in|add here|finish)", "Unimplemented placeholder TODO"),
    (r"(?i)\bpass\s*#\s*TODO\b", "Python pass statement with TODO"),
    (r"(?i)\braise\s+NotImplementedError\b", "Unimplemented exception raised"),
]


class AntiLazinessCritic(BaseGate):
    """Detects lazy code omissions and placeholders left by generative LLMs."""

    @property
    def name(self) -> str:
        return "AntiLazinessCritic"

    def evaluate(self, root_dir: Path, context: Dict[str, Any]) -> GateResult:
        diff_text: str = context.get("diff_text", "")
        modified_files: List[str] = context.get("modified_files", [])

        errors: List[str] = []
        warnings: List[str] = []
        detections: List[Dict[str, Any]] = []

        # 1. Inspect diff text directly for newly added lines (+) with laziness patterns
        if diff_text:
            for line in diff_text.splitlines():
                if not line.startswith("+") or line.startswith("+++"):
                    continue
                line_content = line[1:].strip()
                for pattern, desc in LAZINESS_PATTERNS:
                    if re.search(pattern, line_content):
                        msg = f"Laziness pattern detected: '{desc}' in added line: `{line_content[:80]}`"
                        errors.append(msg)
                        detections.append({"pattern": desc, "line": line_content})
                        break

        # 2. Inspect physical files directly if diff was empty or for direct file inspection
        for rel_file in modified_files:
            file_path = (root_dir / rel_file).resolve()
            if not file_path.is_file():
                continue
            # Skip binary files or known large data files
            if file_path.suffix.lower() in [".png", ".jpg", ".jpeg", ".mp4", ".mov", ".mp3", ".wav", ".zip", ".bin"]:
                continue
            try:
                content = file_path.read_text(encoding="utf-8", errors="replace")
                for line_idx, line in enumerate(content.splitlines(), start=1):
                    for pattern, desc in LAZINESS_PATTERNS:
                        if re.search(pattern, line):
                            msg = f"[{rel_file}:{line_idx}] {desc}: `{line.strip()[:80]}`"
                            warnings.append(msg)
                            break
            except Exception:
                pass

        passed = len(errors) == 0
        return GateResult(
            gate_name=self.name,
            passed=passed,
            errors=errors,
            warnings=warnings,
            details={"detections": detections, "errors_count": len(errors), "warnings_count": len(warnings)},
        )
