# -*- coding: utf-8 -*-
"""
OMNISTATE Session State Model
Tracks the active lifecycle of a transactional AI modification.
"""

from __future__ import annotations

import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from omnistate.constants import RiskTier, SessionStatus


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class OmniStateStep:
    action: str
    details: str = ""
    timestamp: str = field(default_factory=utc_now_iso)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> OmniStateStep:
        return cls(
            action=data.get("action", ""),
            details=data.get("details", ""),
            timestamp=data.get("timestamp", utc_now_iso()),
        )


@dataclass
class OmniStateIntent:
    summary: str = ""
    prompt: str = ""
    non_goals: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> OmniStateIntent:
        return cls(
            summary=data.get("summary", ""),
            prompt=data.get("prompt", ""),
            non_goals=data.get("non_goals", []),
        )


@dataclass
class OmniStateSession:
    session_id: str = field(default_factory=lambda: f"sess_{uuid.uuid4().hex[:12]}")
    status: SessionStatus = SessionStatus.IDLE
    intent: OmniStateIntent = field(default_factory=OmniStateIntent)
    scope_paths: List[str] = field(default_factory=list)
    risk_tier: RiskTier = RiskTier.STANDARD
    created_at: str = field(default_factory=utc_now_iso)
    updated_at: str = field(default_factory=utc_now_iso)
    baseline_commit: Optional[str] = None
    baseline_fingerprints: Dict[str, str] = field(default_factory=dict)
    audit_fingerprints: Dict[str, str] = field(default_factory=dict)
    audit_results: Dict[str, Any] = field(default_factory=dict)
    commit_clearance: Optional[str] = None
    evidence_paths: List[str] = field(default_factory=list)
    steps: List[OmniStateStep] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "status": self.status.value,
            "intent": self.intent.to_dict(),
            "scope_paths": self.scope_paths,
            "risk_tier": self.risk_tier.value,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "baseline_commit": self.baseline_commit,
            "baseline_fingerprints": self.baseline_fingerprints,
            "audit_fingerprints": self.audit_fingerprints,
            "audit_results": self.audit_results,
            "commit_clearance": self.commit_clearance,
            "evidence_paths": self.evidence_paths,
            "steps": [s.to_dict() for s in self.steps],
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> OmniStateSession:
        intent_data = data.get("intent", {})
        intent = OmniStateIntent.from_dict(intent_data) if isinstance(intent_data, dict) else OmniStateIntent()
        raw_steps = data.get("steps", [])
        steps = [OmniStateStep.from_dict(s) for s in raw_steps if isinstance(s, dict)]
        
        status_val = data.get("status", SessionStatus.IDLE.value)
        try:
            status = SessionStatus(status_val)
        except ValueError:
            status = SessionStatus.IDLE

        risk_val = data.get("risk_tier", RiskTier.STANDARD.value)
        try:
            risk = RiskTier(risk_val)
        except ValueError:
            risk = RiskTier.STANDARD

        return cls(
            session_id=data.get("session_id", f"sess_{uuid.uuid4().hex[:12]}"),
            status=status,
            intent=intent,
            scope_paths=data.get("scope_paths", []),
            risk_tier=risk,
            created_at=data.get("created_at", utc_now_iso()),
            updated_at=data.get("updated_at", utc_now_iso()),
            baseline_commit=data.get("baseline_commit"),
            baseline_fingerprints=data.get("baseline_fingerprints", {}),
            audit_fingerprints=data.get("audit_fingerprints", {}),
            audit_results=data.get("audit_results", {}),
            commit_clearance=data.get("commit_clearance"),
            evidence_paths=data.get("evidence_paths", []),
            steps=steps,
            metadata=data.get("metadata", {}),
        )

    def touch(self) -> None:
        self.updated_at = utc_now_iso()

    def add_step(self, action: str, details: str = "") -> OmniStateStep:
        step = OmniStateStep(action=action, details=details)
        self.steps.append(step)
        self.touch()
        return step
