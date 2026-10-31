# -*- coding: utf-8 -*-
"""
OMNISTATE Anti-Laziness Critic Gate
Scans diffs and modified files for dangerous AI laziness placeholders and omissions.
Enhanced with Markdown specification block & backtick span exemptions.
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

DOC_EXTENSIONS = {".md", ".markdown", ".rst", ".txt", ".adoc"}


def is_markdown_specification_example(line: str) -> bool:
    """
    Check if a line in documentation is demonstrating forbidden examples rather than omitting code.
    E.g.: '- **STRICTLY FORBIDDEN**: Inserting ellipsis placeholders (`// ...`, `# ...`)'
    """
    # If the line contains backticks wrapping the placeholder pattern, or discusses 'prohibit' / 'forbidden'
    if ("`" in line or "``" in line) and any(kw in line.lower() for kw in ["forbidden", "prohibit", "disallow", "ban", "never", "placeholder", "example", "warn", "嚴禁", "禁止"]):
        return True
    return False


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

        # Track active file context during unified diff parsing
        current_file: Optional[str] = None

        # 1. Inspect diff text directly for newly added lines (+) with laziness patterns
        if diff_text:
            for raw_line in diff_text.splitlines():
                if raw_line.startswith("+++ b/"):
                    current_file = raw_line[6:].strip()
                    continue
                if not raw_line.startswith("+") or raw_line.startswith("+++"):
                    continue

                line_content = raw_line[1:].strip()
                is_doc_file = bool(current_file and Path(current_file).suffix.lower() in DOC_EXTENSIONS)

                for pattern, desc in LAZINESS_PATTERNS:
                    if re.search(pattern, line_content):
                        # If this is a markdown/doc file and the line is just describing forbidden examples
                        if is_doc_file and is_markdown_specification_example(line_content):
                            # Exempt specification examples, record as info/warning if needed
                            warnings.append(f"Exempted doc specification example in {current_file}: `{line_content[:80]}`")
                            break

                        msg = f"Laziness pattern detected: '{desc}' in added line: `{line_content[:80]}`"
                        errors.append(msg)
                        detections.append({"pattern": desc, "line": line_content, "file": current_file})
                        break

        # 2. Inspect physical files directly if diff was empty or for direct file inspection
        for rel_file in modified_files:
            file_path = (root_dir / rel_file).resolve()
            if not file_path.is_file():
                continue
            # Skip binary files or known large data files
            if file_path.suffix.lower() in [".png", ".jpg", ".jpeg", ".mp4", ".mov", ".mp3", ".wav", ".zip", ".bin"]:
                continue

            is_doc = file_path.suffix.lower() in DOC_EXTENSIONS

            try:
                content = file_path.read_text(encoding="utf-8", errors="replace")
                for line_idx, line in enumerate(content.splitlines(), start=1):
                    line_str = line.strip()
                    for pattern, desc in LAZINESS_PATTERNS:
                        if re.search(pattern, line):
                            if is_doc and is_markdown_specification_example(line_str):
                                continue
                            msg = f"[{rel_file}:{line_idx}] {desc}: `{line_str[:80]}`"
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
