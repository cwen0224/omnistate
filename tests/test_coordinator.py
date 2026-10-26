# -*- coding: utf-8 -*-
"""
Tests for OmniStateCoordinator Lifecycle & Anti-Tamper Security
"""

import tempfile
import unittest
from pathlib import Path

from omnistate.constants import SessionStatus
from omnistate.core.coordinator import OmniStateCoordinator


class TestCoordinatorLifecycle(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.root_dir = Path(self.tmp_dir.name)
        self.coord = OmniStateCoordinator(self.root_dir)
        self.coord.init_repository()

    def tearDown(self):
        self.tmp_dir.cleanup()

    def test_full_transaction_flow(self):
        # 1. Create a dummy file
        src_file = self.root_dir / "app.py"
        src_file.write_text("print('hello')\n", encoding="utf-8")

        # 2. Begin
        session = self.coord.begin(
            intent_summary="Add multiply function",
            scope_paths=["app.py"],
        )
        self.assertEqual(session.status, SessionStatus.IN_PROGRESS)

        # 3. Record step
        self.coord.record_step("Modifying app.py", "Added multiply function")

        # 4. Modify file cleanly
        src_file.write_text("print('hello')\ndef multiply(a, b): return a * b\n", encoding="utf-8")

        # 5. Audit
        passed, gate_results = self.coord.audit(files=["app.py"], run_tests=False)
        self.assertTrue(passed)
        audited_session = self.coord.ledger.load_session()
        self.assertEqual(audited_session.status, SessionStatus.AUDITED)
        self.assertIn("app.py", audited_session.audit_fingerprints)

        # 6. Finish
        finished = self.coord.finish()
        self.assertEqual(finished.status, SessionStatus.COMPLETED)
        self.assertIsNotNone(finished.commit_clearance)
        self.assertTrue(finished.commit_clearance.startswith("OMNI_CLEAR_"))

    def test_anti_tamper_fails_when_modified_after_audit(self):
        src_file = self.root_dir / "app.py"
        src_file.write_text("v1", encoding="utf-8")

        self.coord.begin(intent_summary="Tamper test", scope_paths=["app.py"])
        passed, _ = self.coord.audit(files=["app.py"], run_tests=False)
        self.assertTrue(passed)

        # Sneaky sneak modification after audit:
        src_file.write_text("v2_tampered", encoding="utf-8")

        # Finish should detect fingerprint mismatch and BLOCK
        with self.assertRaises(RuntimeError) as ctx:
            self.coord.finish()
        self.assertIn("Anti-Tamper Security Violation", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
