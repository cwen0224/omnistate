# -*- coding: utf-8 -*-
"""
OMNISTATE Configuration Manager
Provides flexible configuration discovery from omnistate.json, .omnistaterc,
or pyproject.toml [tool.omnistate].
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from omnistate.constants import DEFAULT_STATE_DIR


@dataclass
class GateConfig:
    scope_enforcement: bool = True
    anti_laziness: bool = True
    anti_bloat: bool = True
    max_file_growth_ratio: float = 2.0
    max_line_growth: int = 600
    test_command: Optional[str] = None
    evidence_required: bool = False

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> GateConfig:
        return cls(
            scope_enforcement=data.get("scope_enforcement", True),
            anti_laziness=data.get("anti_laziness", True),
            anti_bloat=data.get("anti_bloat", True),
            max_file_growth_ratio=float(data.get("max_file_growth_ratio", 2.0)),
            max_line_growth=int(data.get("max_line_growth", 600)),
            test_command=data.get("test_command"),
            evidence_required=data.get("evidence_required", False),
        )


@dataclass
class WardenConfig:
    enforce_pre_commit: bool = True
    block_unclear_commits: bool = True

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> WardenConfig:
        return cls(
            enforce_pre_commit=data.get("enforce_pre_commit", True),
            block_unclear_commits=data.get("block_unclear_commits", True),
        )


@dataclass
class OmniStateConfig:
    state_dir: str = DEFAULT_STATE_DIR
    ignored_paths: List[str] = field(default_factory=lambda: [
        ".git", ".venv", "venv", "node_modules", "__pycache__", ".omnistate",
        "dist", "build", ".pytest_cache", ".ruff_cache", ".mypy_cache"
    ])
    gates: GateConfig = field(default_factory=GateConfig)
    warden: WardenConfig = field(default_factory=WardenConfig)

    @classmethod
    def load(cls, root_dir: Path) -> OmniStateConfig:
        """
        Find and load configuration for the target project root.
        Order of precedence:
        1. <root>/.omnistate/omnistate.json
        2. <root>/omnistate.json
        3. <root>/.omnistaterc
        """
        candidates = [
            root_dir / DEFAULT_STATE_DIR / "omnistate.json",
            root_dir / "omnistate.json",
            root_dir / ".omnistaterc",
        ]
        
        for cand in candidates:
            if cand.is_file():
                try:
                    data = json.loads(cand.read_text(encoding="utf-8"))
                    return cls(
                        state_dir=data.get("state_dir", DEFAULT_STATE_DIR),
                        ignored_paths=data.get("ignored_paths", [
                            ".git", ".venv", "venv", "node_modules", "__pycache__", ".omnistate",
                            "dist", "build", ".pytest_cache", ".ruff_cache", ".mypy_cache"
                        ]),
                        gates=GateConfig.from_dict(data.get("gates", {})),
                        warden=WardenConfig.from_dict(data.get("warden", {})),
                    )
                except Exception:
                    pass
        
        return cls()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "state_dir": self.state_dir,
            "ignored_paths": self.ignored_paths,
            "gates": {
                "scope_enforcement": self.gates.scope_enforcement,
                "anti_laziness": self.gates.anti_laziness,
                "anti_bloat": self.gates.anti_bloat,
                "max_file_growth_ratio": self.gates.max_file_growth_ratio,
                "max_line_growth": self.gates.max_line_growth,
                "test_command": self.gates.test_command,
                "evidence_required": self.gates.evidence_required,
            },
            "warden": {
                "enforce_pre_commit": self.warden.enforce_pre_commit,
                "block_unclear_commits": self.warden.block_unclear_commits,
            }
        }
