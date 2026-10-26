# -*- coding: utf-8 -*-
"""
OMNISTATE Warden
Anti-Bypass, Anti-Tamper & Pre-Commit Guardrail.
Blocks unauthorized or un-audited git commits.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from omnistate.constants import (
    EXIT_GATE_FAILURE,
    EXIT_SUCCESS,
    EXIT_WARDEN_BLOCKED,
    SessionStatus,
)
from omnistate.core.coordinator import OmniStateCoordinator
from omnistate.gates import (
    AntiLazinessCritic,
    compute_file_sha256,
    is_path_in_scope,
)


class OmniStateWarden:
    """Enforces that git commits cannot bypass the OMNISTATE transaction lifecycle."""

    def __init__(self, root_dir: Path):
        self.root_dir = root_dir.resolve()
        self.coord = OmniStateCoordinator(self.root_dir)

    def _run_git(self, args: List[str]) -> Tuple[int, str, str]:
        try:
            res = subprocess.run(
                ["git"] + args,
                cwd=str(self.root_dir),
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            return res.returncode, res.stdout, res.stderr
        except Exception as e:
            return -1, "", str(e)

    def get_staged_files(self) -> List[str]:
        rc, out, _ = self._run_git(["diff", "--cached", "--name-only"])
        if rc != 0:
            return []
        files = []
        for line in out.splitlines():
            line = line.strip().replace("\\", "/")
            if line:
                files.append(line)
        return files

    def get_staged_diff(self) -> str:
        rc, out, _ = self._run_git(["diff", "--cached"])
        return out if rc == 0 else ""

    def check_staged(self) -> int:
        """
        Executed by .git/hooks/pre-commit.
        Returns 0 (allow commit) or non-zero (block commit).
        """
        staged_files = self.get_staged_files()
        if not staged_files:
            return EXIT_SUCCESS

        # If only governance state directory is staged, permit it
        state_dir_name = self.coord.config.state_dir
        non_state_files = [
            f for f in staged_files
            if not f.startswith(f"{state_dir_name}/") and f != state_dir_name
        ]
        if not non_state_files:
            return EXIT_SUCCESS

        session = self.coord.ledger.load_session()
        if not session:
            print("\n❌ [OMNISTATE WARDEN BLOCKED]")
            print("Commit blocked: No active OMNISTATE session found.")
            print("Please initialize a transaction using 'omnistate begin' before committing code.\n")
            return EXIT_WARDEN_BLOCKED

        # 1. Status Check
        if session.status != SessionStatus.COMPLETED:
            print("\n❌ [OMNISTATE WARDEN BLOCKED]")
            print(f"Commit blocked: Active transaction '{session.session_id}' status is '{session.status.value}'.")
            print("You must successfully run 'omnistate audit' and 'omnistate finish' first.\n")
            return EXIT_WARDEN_BLOCKED

        # 2. Clearance Token Check
        if not session.commit_clearance:
            print("\n❌ [OMNISTATE WARDEN BLOCKED]")
            print("Commit blocked: No commit clearance token present in session.\n")
            return EXIT_WARDEN_BLOCKED

        # 3. Scope Boundary Check
        scope_violations = []
        for f in non_state_files:
            if not is_path_in_scope(f, session.scope_paths, state_dir_name):
                scope_violations.append(f)

        if scope_violations:
            print("\n❌ [OMNISTATE WARDEN BLOCKED]")
            print(f"Commit blocked: Staged files violate declared scope {session.scope_paths}:")
            for sv in scope_violations:
                print(f"  • {sv}")
            print("\n")
            return EXIT_WARDEN_BLOCKED

        # 4. Fingerprint & Tamper Check
        tampered = []
        for f in non_state_files:
            expected = session.audit_fingerprints.get(f)
            current = compute_file_sha256(self.root_dir / f)
            if expected is None:
                tampered.append(f"{f} (staged without being audited)")
            elif expected != current:
                tampered.append(f"{f} (fingerprint mismatch: audited={expected[:10]}, staged={current[:10]})")

        if tampered:
            print("\n❌ [OMNISTATE WARDEN BLOCKED]")
            print("Commit blocked: Staged files were modified after audit or not audited:")
            for t in tampered:
                print(f"  • {t}")
            print("Please re-run 'omnistate audit' and 'omnistate finish'.\n")
            return EXIT_WARDEN_BLOCKED

        # 5. Anti-Laziness Staged Diff Check
        staged_diff = self.get_staged_diff()
        if staged_diff:
            critic = AntiLazinessCritic()
            res = critic.evaluate(self.root_dir, {"diff_text": staged_diff, "modified_files": non_state_files})
            if not res.passed:
                print("\n❌ [OMNISTATE WARDEN BLOCKED]")
                print("Commit blocked: Anti-laziness scan failed on staged changes:")
                for err in res.errors:
                    print(f"  • {err}")
                print("\n")
                return EXIT_GATE_FAILURE

        print(f"🛡️  [OMNISTATE WARDEN PASSED] Clearance Token verified: {session.commit_clearance}")
        return EXIT_SUCCESS
