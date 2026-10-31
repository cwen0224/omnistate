# -*- coding: utf-8 -*-
"""Unit tests for Postmortem Governance and AntiLaziness Markdown false-positive fix."""

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from omnistate.core.coordinator import OmniStateCoordinator
from omnistate.gates.anti_laziness import AntiLazinessCritic


class TestPostmortemGovernance(unittest.TestCase):
    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp())
        self.coord = OmniStateCoordinator(self.temp_dir)
        self.coord.init_repository()

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_record_postmortem_persists_in_session_and_snapshot(self):
        # 1. Begin transaction
        self.coord.begin(intent_summary="Test feature", scope_paths=["src/"], risk_tier="standard")

        # 2. Add file and step
        src_file = self.temp_dir / "src" / "feature.py"
        src_file.parent.mkdir(parents=True, exist_ok=True)
        src_file.write_text("x = 1\n", encoding="utf-8")

        # 3. Record postmortem
        flaws = [
            {"title": "Missing edge case", "description": "Need fuzzy Levenshtein match", "severity": "HIGH"}
        ]
        pm = self.coord.record_postmortem(
            summary="Thorough postmortem test",
            flaws=flaws,
            root_causes=["Assumption of clean text"],
            mitigations=["Add DP sliding window"],
            report_path="docs/POSTMORTEM.md"
        )
        self.assertEqual(pm["summary"], "Thorough postmortem test")
        self.assertEqual(len(pm["flaws"]), 1)

        # 4. Audit
        passed, _ = self.coord.audit(files=["src/feature.py"], run_tests=False)
        self.assertTrue(passed)

        # 5. Finish
        session = self.coord.finish(note="Finished test session")
        self.assertIn("postmortem", session.metadata)
        self.assertEqual(session.metadata["postmortem"]["summary"], "Thorough postmortem test")

        # 6. Verify snapshot archive
        rev = session.metadata.get("archived_revision")
        snapshot_file = self.temp_dir / ".omnistate" / "snapshots" / f"rev_{rev:04d}.json"
        self.assertTrue(snapshot_file.is_file())
        snapshot_data = json.loads(snapshot_file.read_text(encoding="utf-8"))
        self.assertIn("postmortem", snapshot_data.get("full_session", {}).get("metadata", {}))

    def test_anti_laziness_markdown_specification_exempted(self):
        critic = AntiLazinessCritic()
        c = chr(96)
        pattern1 = "// " + "..."
        pattern2 = "# " + "... existing code ..."

        # Markdown diff with backtick-wrapped ellipsis example
        md_diff = f"+++ b/docs/rules.md\n+- **STRICTLY FORBIDDEN**: Inserting ellipsis placeholders ({c}{pattern1}{c}, {c}{pattern2}{c}).\n"
        res = critic.evaluate(self.temp_dir, {"diff_text": md_diff, "modified_files": []})
        self.assertTrue(res.passed, f"Expected markdown spec example to pass, but got errors: {res.errors}")

        # Python file with actual ellipsis omission MUST fail
        py_diff = f"+++ b/src/bad.py\n+{pattern2}\n+def foo(): pass\n"
        res2 = critic.evaluate(self.temp_dir, {"diff_text": py_diff, "modified_files": []})
        self.assertFalse(res2.passed, "Expected python code ellipsis omission to fail.")


if __name__ == "__main__":
    unittest.main()
