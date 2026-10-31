# -*- coding: utf-8 -*-
"""
OMNISTATE: Universal State Governance, Transaction Guardrails & Anti-Bypass Framework
Adaptable to any AI MCP (Model Context Protocol) or CLI project.
"""

from omnistate.constants import (
    RiskTier,
    SessionStatus,
    VERSION,
)
from omnistate.config import OmniStateConfig
from omnistate.core.coordinator import OmniStateCoordinator
from omnistate.core.ledger import StateLedger
from omnistate.core.session import (
    OmniStateIntent,
    OmniStateSession,
    OmniStateStep,
)
from omnistate.gates import (
    AntiBloatCritic,
    AntiLazinessCritic,
    EvidenceGate,
    GateResult,
    ScopeGate,
    PlanningGate,
    TestRunnerGate,
    compute_file_sha256,
    compute_files_fingerprint,
    is_path_in_scope,
)
from omnistate.warden import OmniStateWarden, install_git_hooks

__version__ = VERSION

__all__ = [
    "VERSION",
    "SessionStatus",
    "RiskTier",
    "OmniStateConfig",
    "OmniStateCoordinator",
    "StateLedger",
    "OmniStateSession",
    "OmniStateStep",
    "OmniStateIntent",
    "GateResult",
    "ScopeGate",
    "PlanningGate",
    "AntiLazinessCritic",
    "AntiBloatCritic",
    "TestRunnerGate",
    "EvidenceGate",
    "OmniStateWarden",
    "install_git_hooks",
    "compute_file_sha256",
    "compute_files_fingerprint",
    "is_path_in_scope",
]
