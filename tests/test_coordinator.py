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

    def test_planning_gate_requires_memo_checklist_and_subtask_completion(self):
        self.coord.begin(
            intent_summary="Planned feature",
            scope_paths=["app.py"],
            prompt="Implement a planned feature with verification.",
        )

        passed, results = self.coord.audit(files=[], run_tests=False)
        self.assertFalse(passed)
        self.assertFalse(next(r for r in results if r.gate_name == "PlanningGate").passed)

        self.coord.update_memo("Implement a planned feature with verification.", ["reference.png"])
        self.coord.add_checklist_item("CHECK-1", "Feature works", "Automated and visual evidence exists")
        self.coord.add_subtask("TASK-1", "Implement feature", "implementation")
        self.coord.add_subtask("TASK-2", "Verify feature", "visual_review", ["TASK-1"], "visual-supervisor")
        self.coord.link_checklist_subtask("CHECK-1", "TASK-1")
        self.coord.link_checklist_subtask("CHECK-1", "TASK-2", verification=True)
        self.coord.record_subtask_result("TASK-1", "PASS", ["test.txt"], "Implemented")
        self.coord.record_subtask_result("TASK-2", "PASS", ["screenshot.png"], "Verified")
        self.coord.set_checklist_status("CHECK-1", "PASS", ["test.txt", "screenshot.png"])
        self.coord.record_plan_review(
            "plan-reviewer", "APPROVED",
            findings=["Plan matches the requirement."],
            recommendations=["Keep visual evidence mandatory."],
            evidence=["reference.png"],
        )

        passed, results = self.coord.audit(files=[], run_tests=False)
        self.assertTrue(passed)
        self.assertTrue(next(r for r in results if r.gate_name == "PlanningGate").passed)

    def test_planning_gate_requires_independent_plan_review(self):
        self.coord.begin("Planned feature", ["app.py"], prompt="Implement a planned feature.")
        self.coord.update_memo("Implement a planned feature.")
        self.coord.add_checklist_item("CHECK-1", "Feature works", "Evidence exists")
        self.coord.add_subtask("TASK-1", "Implement feature", "implementation")
        self.coord.link_checklist_subtask("CHECK-1", "TASK-1")
        self.coord.record_subtask_result("TASK-1", "PASS", ["test.txt"], "Implemented")
        self.coord.set_checklist_status("CHECK-1", "PASS", ["test.txt"])

        passed, results = self.coord.audit(files=[], run_tests=False)

        self.assertFalse(passed)
        planning = next(r for r in results if r.gate_name == "PlanningGate")
        self.assertTrue(any("Independent plan review" in error for error in planning.errors))

        self.coord.record_plan_review(
            "plan-reviewer", "CHANGES_REQUIRED",
            findings=["The plan omits a visual check."],
            recommendations=["Add an independent screenshot review."],
        )
        passed, _ = self.coord.audit(files=[], run_tests=False)
        self.assertFalse(passed)

        self.coord.record_plan_review(
            "plan-reviewer", "RESOLVED",
            findings=["The visual check was added."],
            recommendations=["Keep the screenshot evidence."],
        )
        passed, results = self.coord.audit(files=[], run_tests=False)
        self.assertTrue(passed)
        self.assertEqual(next(r for r in results if r.gate_name == "PlanningGate").details["review_agent"], "plan-reviewer")

    def test_planning_gate_rejects_unresolved_dependency_and_conflict(self):
        self.coord.begin("Implement governed work", ["src/"], prompt="User requirement")
        self.coord.update_memo("User requirement")
        self.coord.add_checklist_item("CHECK-1", "Deliver work", "Independent verification")
        self.coord.add_subtask("TASK-1", "Implement", "implementation")
        self.coord.add_subtask("TASK-2", "Verify", "verification", depends_on=["TASK-1"])
        self.coord.link_checklist_subtask("CHECK-1", "TASK-1")
        self.coord.link_checklist_subtask("CHECK-1", "TASK-2", verification=True)
        self.coord.record_subtask_result("TASK-2", "PASS", ["verification.txt"], "Incorrectly early")
        self.coord.record_subtask_result("TASK-1", "CONFLICTED", ["conflict.txt"], "Agents disagree")
        self.coord.set_checklist_status("CHECK-1", "CONFLICTED", ["conflict.txt"])

        passed, results = self.coord.audit(run_tests=False)

        self.assertFalse(passed)
        planning = next(r for r in results if r.gate_name == "PlanningGate")
        self.assertFalse(planning.passed)
        self.assertTrue(any("not complete" in error for error in planning.errors))
        self.assertTrue(any("dependencies" in error for error in planning.errors))


if __name__ == "__main__":
    unittest.main()
