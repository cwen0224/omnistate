# -*- coding: utf-8 -*-
"""
Tests for Quality Gates
"""

import tempfile
import unittest
from pathlib import Path

from omnistate.gates import (
    AntiLazinessCritic,
    EvidenceGate,
    ScopeGate,
    compute_file_sha256,
    compute_files_fingerprint,
    is_path_in_scope,
)


class TestQualityGates(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.root_dir = Path(self.tmp_dir.name)

    def tearDown(self):
        self.tmp_dir.cleanup()

    def test_scope_enclosure(self):
        gate = ScopeGate()
        context = {
            "scope_paths": ["src/", "tests/"],
            "modified_files": ["src/app.py", "tests/test_app.py", ".omnistate/session.json"],
        }
        res = gate.evaluate(self.root_dir, context)
        self.assertTrue(res.passed)

        # Violation
        context_violating = {
            "scope_paths": ["src/"],
            "modified_files": ["src/app.py", "docs/index.md"],
        }
        res_viol = gate.evaluate(self.root_dir, context_violating)
        self.assertFalse(res_viol.passed)
        self.assertTrue(any("docs/index.md" in e for e in res_viol.errors))

    def test_anti_laziness_critic(self):
        critic = AntiLazinessCritic()
        
        # Clean diff
        clean_diff = "--- a/src/app.py\n+++ b/src/app.py\n@@ -1 +1,2 @@\n+def add(a, b):\n+    return a + b\n"
        res_clean = critic.evaluate(self.root_dir, {"diff_text": clean_diff, "modified_files": []})
        self.assertTrue(res_clean.passed)

        # Lazy diff with placeholder
        lazy_diff = "--- a/src/app.py\n+++ b/src/app.py\n@@ -1 +1,2 @@\n+// ... rest of code unchanged\n+def add(a, b): pass\n"
        res_lazy = critic.evaluate(self.root_dir, {"diff_text": lazy_diff, "modified_files": []})
        self.assertFalse(res_lazy.passed)
        self.assertTrue(len(res_lazy.errors) > 0)

    def test_evidence_gate(self):
        gate = EvidenceGate()
        
        # Valid non-empty file
        proof_file = self.root_dir / "proof.txt"
        proof_file.write_text("Verification passed with 100% tests.", encoding="utf-8")
        
        res = gate.evaluate(self.root_dir, {
            "evidence_required": True,
            "evidence_paths": ["proof.txt"],
        })
        self.assertTrue(res.passed)

        # Empty file fails
        empty_proof = self.root_dir / "empty.txt"
        empty_proof.write_text("", encoding="utf-8")
        res_empty = gate.evaluate(self.root_dir, {
            "evidence_required": True,
            "evidence_paths": ["empty.txt"],
        })
        self.assertFalse(res_empty.passed)


if __name__ == "__main__":
    unittest.main()
