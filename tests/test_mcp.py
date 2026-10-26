# -*- coding: utf-8 -*-
"""
Tests for Model Context Protocol (MCP) Server & Tool Registry
"""

import json
import tempfile
import unittest
from pathlib import Path

from omnistate.mcp.protocol import McpServer
from omnistate.mcp.tools import McpToolRegistry


class TestMcpServer(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.workspace_root = Path(self.tmp_dir.name)
        self.registry = McpToolRegistry(self.workspace_root)
        self.server = McpServer(self.workspace_root)

    def tearDown(self):
        self.tmp_dir.cleanup()

    def test_tool_definitions(self):
        tools = self.registry.get_tool_definitions()
        tool_names = [t["name"] for t in tools]
        self.assertIn("omnistate_begin", tool_names)
        self.assertIn("omnistate_audit", tool_names)
        self.assertIn("omnistate_finish", tool_names)
        self.assertIn("omnistate_status", tool_names)
        self.assertIn("omnistate_explain_rules", tool_names)

    def test_mcp_tool_execution(self):
        # 1. Init
        ok, res = self.registry.call_tool("omnistate_init", {})
        self.assertTrue(ok)

        # 2. Begin
        ok, res = self.registry.call_tool("omnistate_begin", {
            "intent": "Implement user auth",
            "scope": ["src/"],
        })
        self.assertTrue(ok)
        self.assertIn("Transaction", res)

        # 3. Step
        ok, res = self.registry.call_tool("omnistate_step", {
            "action": "Created auth schema",
        })
        self.assertTrue(ok)

        # 4. Status
        ok, res = self.registry.call_tool("omnistate_status", {})
        self.assertTrue(ok)
        status_data = json.loads(res)
        self.assertTrue(status_data["is_active"])

        # 5. Explain Rules
        ok, res = self.registry.call_tool("omnistate_explain_rules", {})
        self.assertTrue(ok)
        self.assertIn("OMNISTATE Protocol for AI Agents", res)


if __name__ == "__main__":
    unittest.main()
