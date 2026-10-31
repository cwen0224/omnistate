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
                "name": "omnistate_memo",
                "description": "Record the complete original requirement and references for the active transaction.",
                "inputSchema": {"type": "object", "properties": {"prompt": {"type": "string"}, "references": {"type": "array", "items": {"type": "string"}}}, "required": ["prompt"]},
            },
            {
                "name": "omnistate_plan_review",
                "description": "Record an independent subagent review of the completed plan; unresolved findings block audit.",
                "inputSchema": {"type": "object", "properties": {"agent_id": {"type": "string"}, "status": {"type": "string", "enum": ["APPROVED", "CHANGES_REQUIRED", "RESOLVED", "CONFLICTED"]}, "findings": {"type": "array", "items": {"type": "string"}}, "recommendations": {"type": "array", "items": {"type": "string"}}, "evidence": {"type": "array", "items": {"type": "string"}}}, "required": ["agent_id", "status"]},
            },
            {
                "name": "omnistate_checklist",
                "description": "Add, link, or update a requirement checklist item.",
                "inputSchema": {"type": "object", "properties": {"action": {"type": "string", "enum": ["add", "link", "status"]}, "check_id": {"type": "string"}, "title": {"type": "string"}, "acceptance": {"type": "string"}, "subtask_id": {"type": "string"}, "verification": {"type": "boolean"}, "status": {"type": "string"}, "evidence": {"type": "array", "items": {"type": "string"}}}, "required": ["action", "check_id"]},
            },
            {
                "name": "omnistate_subtask",
                "description": "Create, assign, or record the result of a dependency-aware subtask.",
                "inputSchema": {"type": "object", "properties": {"action": {"type": "string", "enum": ["add", "assign", "result"]}, "subtask_id": {"type": "string"}, "title": {"type": "string"}, "task_type": {"type": "string"}, "depends_on": {"type": "array", "items": {"type": "string"}}, "owner": {"type": "string"}, "agent_id": {"type": "string"}, "role": {"type": "string"}, "status": {"type": "string"}, "result": {"type": "string"}, "evidence": {"type": "array", "items": {"type": "string"}}}, "required": ["action", "subtask_id"]},
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
                "name": "omnistate_postmortem",
                "description": "Record deep postmortem reflection, flaws, and root causes before or during task completion.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "summary": {
                            "type": "string",
                            "description": "Executive summary of what went wrong, bottlenecks, or key lessons learned.",
                        },
                        "flaws": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "title": {"type": "string"},
                                    "description": {"type": "string"},
                                    "severity": {"type": "string", "enum": ["LOW", "MEDIUM", "HIGH", "CRITICAL"]}
                                },
                                "required": ["title"]
                            },
                            "description": "List of specific flaws, bottlenecks, or brittle points identified.",
                            "default": [],
                        },
                        "root_causes": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Root causes underlying the identified flaws.",
                            "default": [],
                        },
                        "mitigations": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Mitigations or future action items to resolve flaws.",
                            "default": [],
                        },
                        "report_path": {
                            "type": "string",
                            "description": "Optional path to full markdown postmortem document.",
                        }
                    },
                    "required": ["summary"]
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

            elif name == "omnistate_memo":
                memo = self.coord.update_memo(arguments["prompt"], arguments.get("references", []))
                return True, json.dumps(memo, indent=2)

            elif name == "omnistate_plan_review":
                review = self.coord.record_plan_review(
                    arguments["agent_id"],
                    arguments["status"],
                    arguments.get("findings", []),
                    arguments.get("recommendations", []),
                    arguments.get("evidence", []),
                )
                return True, json.dumps(review, indent=2)

            elif name == "omnistate_checklist":
                action = arguments["action"]
                if action == "add":
                    result = self.coord.add_checklist_item(arguments["check_id"], arguments.get("title", ""), arguments.get("acceptance", ""))
                elif action == "link":
                    result = self.coord.link_checklist_subtask(arguments["check_id"], arguments["subtask_id"], arguments.get("verification", False))
                else:
                    result = self.coord.set_checklist_status(arguments["check_id"], arguments.get("status", "TODO"), arguments.get("evidence", []))
                return True, json.dumps(result, indent=2)

            elif name == "omnistate_subtask":
                action = arguments["action"]
                if action == "add":
                    result = self.coord.add_subtask(arguments["subtask_id"], arguments.get("title", ""), arguments.get("task_type", "implementation"), arguments.get("depends_on", []), arguments.get("owner", "primary"))
                elif action == "assign":
                    result = self.coord.assign_subtask(arguments["subtask_id"], arguments["agent_id"], arguments.get("role", "worker"))
                else:
                    result = self.coord.record_subtask_result(arguments["subtask_id"], arguments.get("status", "PASS"), arguments.get("evidence", []), arguments.get("result", ""))
                return True, json.dumps(result, indent=2)

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

            elif name == "omnistate_postmortem":
                pm = self.coord.record_postmortem(
                    summary=arguments.get("summary", ""),
                    flaws=arguments.get("flaws", []),
                    root_causes=arguments.get("root_causes", []),
                    mitigations=arguments.get("mitigations", []),
                    report_path=arguments.get("report_path"),
                )
                msg = "Postmortem recorded successfully:\n" + json.dumps(pm, ensure_ascii=False, indent=2)
                return True, msg

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
                    "5. For prompted work, record `omnistate_memo`, create checklist items, and link dependency-aware subtasks before implementation.\n"
                    "6. After the plan is complete, activate an independent subagent through `omnistate_plan_review`; record mismatches, omissions, and better alternatives.\n"
                    "7. Resolve review findings and record APPROVED or RESOLVED; unresolved review findings block audit.\n"
                    "8. Assign independent verification subtasks and record their evidence; FAIL or CONFLICTED blocks completion.\n"
                    "9. Call `omnistate_finish` to seal the transaction and obtain commit clearance.\n"
                    "10. Git commits are blocked by Warden without a valid clearance token!"
                )
                return True, rules

            else:
                return False, f"Unknown tool: '{name}'"

        except Exception as e:
            return False, f"OMNISTATE Error: {str(e)}"
