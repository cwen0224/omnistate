# -*- coding: utf-8 -*-
"""
Tests for OmniStateSession and StateLedger
"""

import json
import tempfile
import unittest
from pathlib import Path

from omnistate.constants import RiskTier, SessionStatus
from omnistate.core.ledger import StateLedger
from omnistate.core.session import OmniStateIntent, OmniStateSession, OmniStateStep


class TestSessionAndLedger(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.root_dir = Path(self.tmp_dir.name)
        self.ledger = StateLedger(self.root_dir)

    def tearDown(self):
        self.tmp_dir.cleanup()

    def test_session_lifecycle(self):
        intent = OmniStateIntent(summary="Fix authentication bug", prompt="Fix login", non_goals=["Refactor DB"])
        session = OmniStateSession(
            intent=intent,
            scope_paths=["auth/", "tests/"],
            risk_tier=RiskTier.STANDARD,
        )
        self.assertEqual(session.status, SessionStatus.IDLE)
        step = session.add_step("Added unit test", "test_auth.py")
        self.assertEqual(len(session.steps), 1)
        self.assertEqual(step.action, "Added unit test")

        d = session.to_dict()
        restored = OmniStateSession.from_dict(d)
        self.assertEqual(restored.session_id, session.session_id)
        self.assertEqual(restored.intent.summary, "Fix authentication bug")
        self.assertEqual(len(restored.steps), 1)

    def test_ledger_persistence(self):
        session = OmniStateSession(
            status=SessionStatus.IN_PROGRESS,
            intent=OmniStateIntent(summary="Test task"),
            scope_paths=["*"],
        )
        self.ledger.save_session(session)
        loaded = self.ledger.load_session()
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded.session_id, session.session_id)
        self.assertEqual(loaded.status, SessionStatus.IN_PROGRESS)

        # Snapshot archive
        session.status = SessionStatus.COMPLETED
        session.commit_clearance = "OMNI_CLEAR_TEST123"
        rev = self.ledger.archive_snapshot(session)
        self.assertEqual(rev, 1)

        state = self.ledger.load_state()
        self.assertEqual(state["current_revision"], 1)
        self.assertEqual(len(state["history"]), 1)


if __name__ == "__main__":
    unittest.main()
