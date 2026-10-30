# -*- coding: utf-8 -*-
"""
Tests for OmniStateWarden Anti-Bypass Guardrail
"""

import subprocess
import tempfile
import unittest
from pathlib import Path

from omnistate.constants import EXIT_SUCCESS, EXIT_WARDEN_BLOCKED, SessionStatus
from omnistate.core.coordinator import OmniStateCoordinator
from omnistate.warden.warden import OmniStateWarden
from omnistate.warden.hooks import install_git_hooks


class TestWarden(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.root_dir = Path(self.tmp_dir.name)

        # Initialize git repo in temp dir
        subprocess.run(["git", "init"], cwd=str(self.root_dir), capture_output=True, check=True)
        subprocess.run(["git", "config", "user.name", "TestUser"], cwd=str(self.root_dir), capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=str(self.root_dir), capture_output=True)

        self.coord = OmniStateCoordinator(self.root_dir)
        self.coord.init_repository()
        install_git_hooks(self.root_dir)
        self.warden = OmniStateWarden(self.root_dir)

    def tearDown(self):
        self.tmp_dir.cleanup()

    def test_warden_blocks_unauthorized_staged_commit(self):
        # Create a file and stage it without an active session
        test_file = self.root_dir / "index.js"
        test_file.write_text("console.log('hello');", encoding="utf-8")
        subprocess.run(["git", "add", "index.js"], cwd=str(self.root_dir), capture_output=True)

        # Warden must BLOCK with non-zero exit code
        rc = self.warden.check_staged()
        self.assertEqual(rc, EXIT_WARDEN_BLOCKED)

    def test_warden_passes_when_session_completed_with_clearance(self):
        test_file = self.root_dir / "index.js"
        test_file.write_text("console.log('hello');\n", encoding="utf-8")

        # 1. Begin
        self.coord.begin(intent_summary="Add index script", scope_paths=["index.js"])

        # 2. Audit
        passed, _ = self.coord.audit(files=["index.js"], run_tests=False)
        self.assertTrue(passed)

        # 3. Finish -> Generates clearance token
        finished = self.coord.finish()
        self.assertEqual(finished.status, SessionStatus.COMPLETED)

        # 4. Stage audited file
        subprocess.run(["git", "add", "index.js"], cwd=str(self.root_dir), capture_output=True)

        # 5. Warden must PASS
        rc = self.warden.check_staged()
        self.assertEqual(rc, EXIT_SUCCESS)

    def test_installed_hook_uses_real_cli_module(self):
        hook = (self.root_dir / ".git" / "hooks" / "pre-commit").read_text(encoding="utf-8")
        self.assertIn("python -m omnistate.cli.main warden --check-staged", hook)


if __name__ == "__main__":
    unittest.main()
