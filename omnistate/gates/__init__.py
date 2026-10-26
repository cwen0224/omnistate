# -*- coding: utf-8 -*-
"""
OMNISTATE Quality Gates Package
"""

from omnistate.gates.base import BaseGate, GateResult
from omnistate.gates.scope_gate import ScopeGate, is_path_in_scope
from omnistate.gates.anti_laziness import AntiLazinessCritic
from omnistate.gates.anti_bloat import AntiBloatCritic
from omnistate.gates.test_runner import TestRunnerGate
from omnistate.gates.evidence_gate import EvidenceGate
from omnistate.gates.fingerprint import compute_file_sha256, compute_files_fingerprint

__all__ = [
    "BaseGate",
    "GateResult",
    "ScopeGate",
    "is_path_in_scope",
    "AntiLazinessCritic",
    "AntiBloatCritic",
    "TestRunnerGate",
    "EvidenceGate",
    "compute_file_sha256",
    "compute_files_fingerprint",
]
