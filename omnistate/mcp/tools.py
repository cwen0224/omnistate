# -*- coding: utf-8 -*-
"""
OMNISTATE MCP Tool Registry & Handlers
Exposes OMNISTATE governance tools to AI models via Model Context Protocol.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable, Dict, List, Tuple

from omnistate.core.coordinator import OmniStateCoordinator


class McpToolRegistry:
    def __init__(self, workspace_root: Path):
        self.workspace_root = workspace_root.resolve()
        self.coord = OmniStateCoordinator(self.workspace_root)

    def get_tool_definitions(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": "omnistate_init",
                "description": "Initialize OMNISTATE state governance and pre-commit guardrail in the current workspace.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "overwrite": {
                            "type": "boolean",
                            "description": "Whether to overwrite existing config if present.",
                            "default": False,
                        }
                    },
                },
            },
            {
                "name": "omnistate_begin",
                "description": "Begin a safe, transactional state change. Declares intent, scope boundaries, and risk tier.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "intent": {
                            "type": "string",
                            "description": "Clear, concise summary of what this code change will achieve.",
                        },
                        "scope": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of directories or files allowed to be modified (e.g. ['src/', 'tests/']).",
                            "default": ["*"],
                        },
                        "risk_tier": {
                            "type": "string",
                            "enum": ["low", "standard", "high"],
                            "description": "Risk tier of the task.",
                            "default": "standard",
                        },
                        "prompt": {
                            "type": "string",
                            "description": "Original raw user prompt.",
                            "default": "",
                        },
                        "non_goals": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Strict boundaries or things that must NOT be touched or altered.",
                            "default": [],
                        },
                    },
                    "required": ["intent"],
                },
            },
            {
                "name": "omnistate_step",
                "description": "Record an intermediate progress milestone or action within the active transaction.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "action": {
                            "type": "string",
                            "description": "Brief description of the action taken.",
                        },
                        "details": {
                            "type": "string",
                            "description": "Additional details or outcome notes.",
                            "default": "",
                        },
                    },
                    "required": ["action"],
                },
            },
            {
                "name": "omnistate_audit",
                "description": "Audit current modifications against scope boundaries, anti-laziness gates, and test suites.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "files": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Optional list of files to audit. If omitted, automatically checks git status.",
                        },
                        "run_tests": {
                            "type": "boolean",
                            "description": "Whether to run the configured test command.",
                            "default": True,
                        },
                    },
                },
            },
            {
                "name": "omnistate_finish",
                "description": "Finalize transaction, verify anti-tamper fingerprints, archive immutable snapshot, and issue commit clearance.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "evidence": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of evidence artifact file paths proving task completion.",
                            "default": [],
                        },
                        "note": {
                            "type": "string",
                            "description": "Completion note.",
                            "default": "",
                        },
                    },
                },
            },
            {
                "name": "omnistate_abort",
                "description": "Abort active transaction and optionally roll back uncommitted changes in scope.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "rollback": {
                            "type": "boolean",
                            "description": "Whether to revert uncommitted changes in scope via git.",
                            "default": False,
                        },
                        "note": {
                            "type": "string",
                            "description": "Reason for cancellation.",
                            "default": "",
                        },
                    },
                },
            },
            {
                "name": "omnistate_status",
                "description": "Get current OMNISTATE status, active transaction details, git head, and commit clearance state.",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                },
            },
            {
                "name": "omnistate_inspect_diff",
                "description": "Run anti-laziness and scope inspection on the working tree diff without altering state.",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                },
            },
            {
                "name": "omnistate_explain_rules",
                "description": "Explain the OMNISTATE transaction lifecycle rules and guardrails for AI coding assistants.",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                },
            },
        ]

    def call_tool(self, name: str, arguments: Dict[str, Any]) -> Tuple[bool, str]:
        try:
            if name == "omnistate_init":
                res = self.coord.init_repository(overwrite=arguments.get("overwrite", False))
                return True, json.dumps(res, indent=2)

            elif name == "omnistate_begin":
                session = self.coord.begin(
                    intent_summary=arguments["intent"],
                    scope_paths=arguments.get("scope", ["*"]),
                    risk_tier=arguments.get("risk_tier", "standard"),
                    prompt=arguments.get("prompt", ""),
                    non_goals=arguments.get("non_goals", []),
                )
                return True, f"Transaction '{session.session_id}' started in_progress.\nIntent: {session.intent.summary}\nScope: {session.scope_paths}"

            elif name == "omnistate_step":
                step = self.coord.record_step(
                    action=arguments["action"],
                    details=arguments.get("details", ""),
                )
                return True, f"Recorded step at {step.timestamp}: {step.action}"

            elif name == "omnistate_audit":
                passed, gate_results = self.coord.audit(
                    files=arguments.get("files"),
                    run_tests=arguments.get("run_tests", True),
                )
                out = {
                    "all_passed": passed,
                    "gates": [g.to_dict() for g in gate_results],
                }
                status_str = "PASSED" if passed else "FAILED"
                return passed, f"Audit {status_str}.\n{json.dumps(out, indent=2)}"

            elif name == "omnistate_finish":
                session = self.coord.finish(
                    evidence=arguments.get("evidence", []),
                    note=arguments.get("note", ""),
                )
                return True, (
                    f"Transaction '{session.session_id}' COMPLETED successfully!\n"
                    f"Commit Clearance: {session.commit_clearance}\n"
                    f"Archived Revision: #{session.metadata.get('archived_revision')}\n"
                    f"You may now proceed to commit changes via git."
                )

            elif name == "omnistate_abort":
                session = self.coord.abort(
                    rollback=arguments.get("rollback", False),
                    note=arguments.get("note", ""),
                )
                return True, f"Transaction '{session.session_id}' ABORTED."

            elif name == "omnistate_status":
                status = self.coord.get_status()
                return True, json.dumps(status, indent=2)

            elif name == "omnistate_inspect_diff":
                diff = self.coord.get_git_diff_text()
                mod_files = self.coord.get_git_modified_files()
                from omnistate.gates import AntiLazinessCritic
                critic = AntiLazinessCritic()
                res = critic.evaluate(self.workspace_root, {"diff_text": diff, "modified_files": mod_files})
                return True, json.dumps(res.to_dict(), indent=2)

            elif name == "omnistate_explain_rules":
                rules = (
                    "# OMNISTATE Protocol for AI Agents\n"
                    "1. Always call `omnistate_begin` with intent & scope before editing code.\n"
                    "2. Only modify files within declared scope.\n"
                    "3. Never insert lazy ellipsis comments (`// ...`, `# TODO: implement`).\n"
                    "4. Call `omnistate_audit` after changes to verify all gates.\n"
                    "5. Call `omnistate_finish` to seal the transaction and obtain commit clearance.\n"
                    "6. Git commits are blocked by Warden without a valid clearance token!"
                )
                return True, rules

            else:
                return False, f"Unknown tool: '{name}'"

        except Exception as e:
            return False, f"OMNISTATE Error: {str(e)}"
