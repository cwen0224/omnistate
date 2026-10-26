# -*- coding: utf-8 -*-
"""
OMNISTATE State Ledger
Provides atomic file persistence, history revision tracking, and immutable snapshot archives.
"""

from __future__ import annotations

import json
import os
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional

from omnistate.constants import (
    DEFAULT_CONFIG_FILE,
    DEFAULT_SESSION_FILE,
    DEFAULT_SNAPSHOT_DIR,
    DEFAULT_STATE_DIR,
    DEFAULT_STATE_FILE,
)
from omnistate.core.session import OmniStateSession, utc_now_iso


class StateLedger:
    """Manages the .omnistate storage directory and immutable snapshots."""

    def __init__(self, root_dir: Path, state_dir_name: str = DEFAULT_STATE_DIR):
        self.root_dir = root_dir.resolve()
        self.state_dir = self.root_dir / state_dir_name
        self.snapshots_dir = self.state_dir / DEFAULT_SNAPSHOT_DIR
        self.session_file = self.state_dir / DEFAULT_SESSION_FILE
        self.state_file = self.state_dir / DEFAULT_STATE_FILE
        self.config_file = self.state_dir / DEFAULT_CONFIG_FILE

    def ensure_directories(self) -> None:
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.snapshots_dir.mkdir(parents=True, exist_ok=True)

    def is_initialized(self) -> bool:
        return self.state_dir.is_dir()

    def _atomic_write_json(self, target_path: Path, data: Any) -> None:
        self.ensure_directories()
        temp_path = target_path.with_suffix(f".tmp.{os.getpid()}")
        try:
            content = json.dumps(data, indent=2, ensure_ascii=False)
            temp_path.write_text(content, encoding="utf-8")
            temp_path.replace(target_path)
        except Exception:
            if temp_path.exists():
                temp_path.unlink()
            raise

    # Session CRUD
    def load_session(self) -> Optional[OmniStateSession]:
        if not self.session_file.is_file():
            return None
        try:
            data = json.loads(self.session_file.read_text(encoding="utf-8"))
            return OmniStateSession.from_dict(data)
        except Exception:
            return None

    def save_session(self, session: OmniStateSession) -> None:
        session.touch()
        self._atomic_write_json(self.session_file, session.to_dict())

    def clear_session(self) -> None:
        if self.session_file.is_file():
            self.session_file.unlink()

    # Global State Ledger CRUD
    def load_state(self) -> Dict[str, Any]:
        if not self.state_file.is_file():
            return {
                "project_root": str(self.root_dir),
                "current_revision": 0,
                "created_at": utc_now_iso(),
                "updated_at": utc_now_iso(),
                "history": [],
            }
        try:
            return json.loads(self.state_file.read_text(encoding="utf-8"))
        except Exception:
            return {
                "project_root": str(self.root_dir),
                "current_revision": 0,
                "created_at": utc_now_iso(),
                "updated_at": utc_now_iso(),
                "history": [],
            }

    def save_state(self, state: Dict[str, Any]) -> None:
        state["updated_at"] = utc_now_iso()
        self._atomic_write_json(self.state_file, state)

    # Immutable Snapshots
    def archive_snapshot(self, session: OmniStateSession) -> int:
        """Saves session state into an immutable rev_XXXX.json file and updates state ledger."""
        state = self.load_state()
        new_rev = int(state.get("current_revision", 0)) + 1
        snapshot_filename = f"rev_{new_rev:04d}.json"
        snapshot_path = self.snapshots_dir / snapshot_filename

        snapshot_payload = {
            "revision": new_rev,
            "session_id": session.session_id,
            "intent": session.intent.to_dict(),
            "scope_paths": session.scope_paths,
            "risk_tier": session.risk_tier.value,
            "commit_clearance": session.commit_clearance,
            "audit_fingerprints": session.audit_fingerprints,
            "steps_count": len(session.steps),
            "created_at": session.created_at,
            "archived_at": utc_now_iso(),
            "full_session": session.to_dict(),
        }

        self._atomic_write_json(snapshot_path, snapshot_payload)

        # Update state history summary
        state["current_revision"] = new_rev
        history = state.get("history", [])
        history.append({
            "revision": new_rev,
            "session_id": session.session_id,
            "intent": session.intent.summary,
            "scope": session.scope_paths,
            "snapshot_file": snapshot_filename,
            "timestamp": utc_now_iso(),
        })
        state["history"] = history
        self.save_state(state)

        return new_rev
