# -*- coding: utf-8 -*-
"""
Tests for OmniState CLI
"""

import tempfile
import unittest
from pathlib import Path

from omnistate.cli.main import main
from omnistate.constants import EXIT_SUCCESS


class TestCli(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.root_dir = Path(self.tmp_dir.name)

    def tearDown(self):
        self.tmp_dir.cleanup()

    def test_cli_lifecycle(self):
        root_arg = f"--root={self.root_dir}"

        # 1. init
        rc = main(["init", root_arg])
        self.assertEqual(rc, EXIT_SUCCESS)
        self.assertTrue((self.root_dir / ".omnistate").is_dir())

        # 2. begin
        rc = main(["begin", "--intent=Test CLI feature", "--scope=src/", root_arg])
        self.assertEqual(rc, EXIT_SUCCESS)

        # 3. step
        rc = main(["step", "--action=Added feature file", root_arg])
        self.assertEqual(rc, EXIT_SUCCESS)

        # 4. status
        rc = main(["status", root_arg])
        self.assertEqual(rc, EXIT_SUCCESS)

        # 5. abort
        rc = main(["abort", root_arg])
        self.assertEqual(rc, EXIT_SUCCESS)


if __name__ == "__main__":
    unittest.main()
