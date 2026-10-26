# -*- coding: utf-8 -*-
"""
OMNISTATE Core Coordinator
High-level transactional orchestrator for the begin -> step -> audit -> finish lifecycle.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from omnistate.config import OmniStateConfig
from omnistate.constants import (
    DEFAULT_CONFIG_FILE,
    DEFAULT_STATE_DIR,
    RiskTier,
    SessionStatus,
)
from omnistate.core.ledger import StateLedger
from omnistate.core.session import (
    OmniStateIntent,
    OmniStateSession,
    OmniStateStep,
    utc_now_iso,
)
from omnistate.gates import (
    AntiBloatCritic,
    AntiLazinessCritic,
    EvidenceGate,
    GateResult,
    ScopeGate,
    TestRunnerGate,
    compute_file_sha256,
    compute_files_fingerprint,
)


class OmniStateCoordinator:
    """Coordinates transaction lifecycle, safety gates, and state persistence."""

    def __init__(self, root_dir: Path, config: Optional[OmniStateConfig] = None):
        self.root_dir = root_dir.resolve()
        self.config = config or OmniStateConfig.load(self.root_dir)
        self.ledger = StateLedger(self.root_dir, self.config.state_dir)

    def init_repository(self, overwrite: bool = False) -> Dict[str, Any]:
        """Initializes the .omnistate governance directory in target repository."""
        self.ledger.ensure_directories()
        
        config_path = self.ledger.config_file
        if not config_path.is_file() or overwrite:
            default_config = self.config.to_dict()
            config_path.write_text(json.dumps(default_config, indent=2), encoding="utf-8")

        initial_state = self.ledger.load_state()
        self.ledger.save_state(initial_state)

        # Install pre-commit hook template
        hooks_dir = self.ledger.state_dir / "hooks"
        hooks_dir.mkdir(parents=True, exist_ok=True)
        pre_commit_hook = hooks_dir / "pre-commit"
        hook_script = (
            "#!/usr/bin/env sh\n"
            "# OMNISTATE Pre-commit Hook\n"
            "omnistate warden --check-staged\n"
        )
        pre_commit_hook.write_text(hook_script, encoding="utf-8")

        return {
            "status": "initialized",
            "state_dir": str(self.ledger.state_dir),
            "config_file": str(config_path),
            "current_revision": initial_state.get("current_revision", 0),
        }

    # Git Inspection Helpers
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

    def get_git_head_commit(self) -> Optional[str]:
        rc, out, _ = self._run_git(["rev-parse", "HEAD"])
        return out.strip() if rc == 0 and out.strip() else None

    def get_git_modified_files(self) -> List[str]:
        """Returns relative paths of all modified, added, or deleted files in git status."""
        rc, out, _ = self._run_git(["status", "--porcelain"])
        if rc != 0:
            return []
        files: List[str] = []
        for line in out.splitlines():
            line = line.strip()
            if not line:
                continue
            # Format: 'XY path' or 'R  orig -> new'
            parts = line.split(maxsplit=1)
            if len(parts) >= 2:
                path_part = parts[1]
                if " -> " in path_part:
                    path_part = path_part.split(" -> ")[1]
                clean_path = path_part.strip('"').strip("'").replace("\\", "/")
                # Ignore paths in state directory
                if not clean_path.startswith(f"{self.config.state_dir}/"):
                    files.append(clean_path)
        return sorted(set(files))

    def get_git_diff_text(self) -> str:
        rc, out, _ = self._run_git(["diff", "HEAD"])
        if rc == 0 and out:
            return out
        # Fallback to unstaged diff
        rc, out, _ = self._run_git(["diff"])
        return out if rc == 0 else ""

    # Transaction: Begin
    def begin(
        self,
        intent_summary: str,
        scope_paths: Optional[List[str]] = None,
        risk_tier: str = "standard",
        prompt: str = "",
        non_goals: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        force: bool = False,
    ) -> OmniStateSession:
        active_sess = self.ledger.load_session()
        if active_sess and active_sess.status == SessionStatus.IN_PROGRESS and not force:
            raise RuntimeError(
                f"Cannot begin transaction: Active session '{active_sess.session_id}' is already IN_PROGRESS. "
                "Use 'finish' or 'abort' first, or pass force=True."
            )

        scopes = scope_paths or ["*"]
        try:
            risk = RiskTier(risk_tier.lower())
        except ValueError:
            risk = RiskTier.STANDARD

        head_commit = self.get_git_head_commit()
        
        # Calculate baseline fingerprints for any existing files in scope
        baseline_files = self.get_git_modified_files()
        baseline_fp = compute_files_fingerprint(self.root_dir, baseline_files)

        intent = OmniStateIntent(
            summary=intent_summary,
            prompt=prompt,
            non_goals=non_goals or [],
        )

        session = OmniStateSession(
            status=SessionStatus.IN_PROGRESS,
            intent=intent,
            scope_paths=scopes,
            risk_tier=risk,
            baseline_commit=head_commit,
            baseline_fingerprints=baseline_fp,
            metadata=metadata or {},
        )
        session.add_step("Transaction Begun", f"Intent: {intent_summary}")
        self.ledger.save_session(session)
        return session

    # Transaction: Step
    def record_step(self, action: str, details: str = "") -> OmniStateStep:
        session = self.ledger.load_session()
        if not session or session.status not in (SessionStatus.IN_PROGRESS, SessionStatus.AUDITED):
            raise RuntimeError("No active in-progress transaction session found.")
        step = session.add_step(action, details)
        self.ledger.save_session(session)
        return step

    # Transaction: Audit
    def audit(
        self,
        files: Optional[List[str]] = None,
        run_tests: bool = True,
    ) -> Tuple[bool, List[GateResult]]:
        session = self.ledger.load_session()
        if not session or session.status != SessionStatus.IN_PROGRESS:
            raise RuntimeError("Cannot audit: Transaction must be in 'in_progress' status.")

        # Determine modified files
        modified_files = files or self.get_git_modified_files()
        diff_text = self.get_git_diff_text()

        # Build context for gates
        context: Dict[str, Any] = {
            "scope_paths": session.scope_paths,
            "modified_files": modified_files,
            "diff_text": diff_text,
            "state_dir_name": self.config.state_dir,
            "evidence_required": self.config.gates.evidence_required,
            "evidence_paths": session.evidence_paths,
            "test_command": self.config.gates.test_command if run_tests else None,
            "max_file_growth_ratio": self.config.gates.max_file_growth_ratio,
            "max_line_growth": self.config.gates.max_line_growth,
        }

        # Initialize gates
        gates = []
        if self.config.gates.scope_enforcement:
            gates.append(ScopeGate())
        if self.config.gates.anti_laziness:
            gates.append(AntiLazinessCritic())
        if self.config.gates.anti_bloat:
            gates.append(AntiBloatCritic())
        if self.config.gates.evidence_required or session.evidence_paths:
            gates.append(EvidenceGate())
        if run_tests and self.config.gates.test_command:
            gates.append(TestRunnerGate())

        all_passed = True
        gate_results: List[GateResult] = []

        for gate in gates:
            res = gate.evaluate(self.root_dir, context)
            gate_results.append(res)
            if not res.passed:
                all_passed = False

        session.audit_results = {
            "audited_at": utc_now_iso(),
            "all_passed": all_passed,
            "gates": [r.to_dict() for r in gate_results],
        }

        if all_passed:
            # Seal audit fingerprints for all modified files
            session.audit_fingerprints = compute_files_fingerprint(self.root_dir, modified_files)
            session.status = SessionStatus.AUDITED
            session.add_step("Audit Passed", f"Verified {len(modified_files)} files across {len(gates)} gates.")
        else:
            session.add_step("Audit Failed", f"{sum(len(r.errors) for r in gate_results)} errors encountered.")

        self.ledger.save_session(session)
        return all_passed, gate_results

    # Transaction: Finish
    def finish(
        self,
        evidence: Optional[List[str]] = None,
        note: str = "",
    ) -> OmniStateSession:
        session = self.ledger.load_session()
        if not session:
            raise RuntimeError("No active transaction found to finish.")
        if session.status != SessionStatus.AUDITED:
            raise RuntimeError(
                f"Cannot finish: Session status is '{session.status.value}'. Must pass 'audit' first."
            )

        if evidence:
            session.evidence_paths = sorted(set(session.evidence_paths + evidence))

        # 1. Anti-Tamper Check: Verify all audited files still match their SHA-256 signatures
        current_fp = compute_files_fingerprint(self.root_dir, session.audit_fingerprints.keys())
        tampered_files = []
        for path_key, expected_hash in session.audit_fingerprints.items():
            current_hash = current_fp.get(path_key, "MISSING")
            if current_hash != expected_hash:
                tampered_files.append({
                    "file": path_key,
                    "expected": expected_hash[:12],
                    "current": current_hash[:12],
                })

        if tampered_files:
            raise RuntimeError(
                f"Anti-Tamper Security Violation: Files were modified after audit! "
                f"Tampered files: {tampered_files}. Please run 'audit' again before finishing."
            )

        # 2. Generate Commit Clearance Token
        hasher = hashlib.sha256()
        hasher.update(session.session_id.encode("utf-8"))
        for k, v in sorted(session.audit_fingerprints.items()):
            hasher.update(f"{k}:{v}".encode("utf-8"))
        hasher.update(utc_now_iso().encode("utf-8"))
        clearance_token = f"OMNI_CLEAR_{hasher.hexdigest()[:24].upper()}"

        session.commit_clearance = clearance_token
        session.status = SessionStatus.COMPLETED
        session.add_step("Transaction Finished", f"Commit clearance issued: {clearance_token}. {note}".strip())

        # 3. Archive snapshot
        revision = self.ledger.archive_snapshot(session)
        session.metadata["archived_revision"] = revision
        self.ledger.save_session(session)

        return session

    # Transaction: Abort
    def abort(self, rollback: bool = False, note: str = "") -> OmniStateSession:
        session = self.ledger.load_session()
        if not session:
            raise RuntimeError("No active session to abort.")

        if rollback and session.scope_paths:
            # Optionally revert files in scope
            modified = self.get_git_modified_files()
            for f in modified:
                self._run_git(["checkout", "--", f])

        session.status = SessionStatus.ABORTED
        session.add_step("Transaction Aborted", note or "User/Agent triggered transaction abort.")
        self.ledger.save_session(session)
        return session

    # Transaction: Status
    def get_status(self) -> Dict[str, Any]:
        session = self.ledger.load_session()
        state = self.ledger.load_state()
        modified = self.get_git_modified_files()
        head = self.get_git_head_commit()

        return {
            "session": session.to_dict() if session else None,
            "is_active": session.status == SessionStatus.IN_PROGRESS if session else False,
            "has_clearance": bool(session and session.commit_clearance and session.status == SessionStatus.COMPLETED),
            "current_revision": state.get("current_revision", 0),
            "git_head": head,
            "git_modified_files": modified,
            "state_dir": str(self.ledger.state_dir),
        }
