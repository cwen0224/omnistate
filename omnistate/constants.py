# -*- coding: utf-8 -*-
"""
OMNISTATE Universal Constants & Status Enumerations
"""

from __future__ import annotations
from enum import Enum

VERSION = "1.0.0"
PROTOCOL_VERSION = "2024-11-05"

DEFAULT_STATE_DIR = ".omnistate"
DEFAULT_SESSION_FILE = "session.json"
DEFAULT_STATE_FILE = "state.json"
DEFAULT_CONFIG_FILE = "omnistate.json"
DEFAULT_SNAPSHOT_DIR = "snapshots"
DEFAULT_HOOKS_DIR = "hooks"


class SessionStatus(str, Enum):
    IDLE = "idle"
    IN_PROGRESS = "in_progress"
    AUDITED = "audited"
    COMPLETED = "completed"
    ABORTED = "aborted"


class RiskTier(str, Enum):
    LOW = "low"
    STANDARD = "standard"
    HIGH = "high"


# Standard Exit Codes
EXIT_SUCCESS = 0
EXIT_GATE_FAILURE = 1
EXIT_SESSION_ERROR = 2
EXIT_WARDEN_BLOCKED = 3
EXIT_CONFIGURATION_ERROR = 4
