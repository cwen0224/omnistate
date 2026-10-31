# -*- coding: utf-8 -*-
"""
OMNISTATE Universal Command Line Interface (CLI)
Provides human developers and autonomous AI terminal sessions with full control
over the state governance lifecycle.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import List, Optional

from omnistate.constants import (
    EXIT_CONFIGURATION_ERROR,
    EXIT_GATE_FAILURE,
    EXIT_SESSION_ERROR,
    EXIT_SUCCESS,
    EXIT_WARDEN_BLOCKED,
    VERSION,
    SessionStatus,
)
from omnistate.core.coordinator import OmniStateCoordinator
from omnistate.gates import AntiLazinessCritic
from omnistate.warden import OmniStateWarden, install_git_hooks


def format_status_dashboard(coord: OmniStateCoordinator) -> str:
    status_data = coord.get_status()
    session = status_data.get("session")
    is_active = status_data.get("is_active", False)
    has_clearance = status_data.get("has_clearance", False)
    rev = status_data.get("current_revision", 0)
    git_head = status_data.get("git_head") or "N/A"
    mod_files = status_data.get("git_modified_files", [])

    lines = [
        "==================================================================",
        f"  🌐 OMNISTATE STATE GOVERNANCE DASHBOARD (v{VERSION})",
        "==================================================================",
        f"  Project Root     : {coord.root_dir}",
        f"  State Directory  : {status_data['state_dir']}",
        f"  Current Revision : #{rev:04d}",
        f"  Git HEAD Commit  : {git_head[:10] if git_head != 'N/A' else git_head}",
        "------------------------------------------------------------------",
    ]

    if not session or session["status"] == SessionStatus.IDLE.value:
        lines.append("  Transaction State: [ IDLE ] (No active transaction)")
        lines.append("  Run 'omnistate begin --intent \"...\"' to start a new task.")
    else:
        st_val = session["status"].upper()
        icon = "🟢" if st_val == "COMPLETED" else ("🟡" if st_val in ("IN_PROGRESS", "AUDITED") else "🔴")
        lines.append(f"  Transaction ID   : {session['session_id']}")
        lines.append(f"  Transaction State: {icon} [ {st_val} ]")
        lines.append(f"  Intent Summary   : {session['intent'].get('summary', 'N/A')}")
        lines.append(f"  Scope Boundary   : {session.get('scope_paths', ['*'])}")
        lines.append(f"  Risk Tier        : {session.get('risk_tier', 'standard').upper()}")
        lines.append(f"  Steps Recorded   : {len(session.get('steps', []))}")

        if session.get("commit_clearance"):
            lines.append(f"  Commit Clearance : 🛡️  {session['commit_clearance']}")
        elif st_val == "AUDITED":
            lines.append("  Audit Status     : ✅ PASSED (Ready for 'omnistate finish')")
        elif st_val == "IN_PROGRESS":
            lines.append("  Audit Status     : ⏳ PENDING (Run 'omnistate audit' when edits complete)")

    lines.append("------------------------------------------------------------------")
    lines.append(f"  Working Tree Mod : {len(mod_files)} files modified")
    for mf in mod_files[:8]:
        lines.append(f"    • {mf}")
    if len(mod_files) > 8:
        lines.append(f"    ... and {len(mod_files) - 8} more")
    lines.append("==================================================================")
    return "\n".join(lines)


def main(argv: Optional[List[str]] = None) -> int:
    if sys.stdout.encoding != "utf-8" and hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if sys.stderr.encoding != "utf-8" and hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

    root_parent = argparse.ArgumentParser(add_help=False)
    root_parent.add_argument("--root", default=".", help="Target workspace root directory (default: current directory)")

    parser = argparse.ArgumentParser(
        prog="omnistate",
        parents=[root_parent],
        description=f"OMNISTATE Universal State Governance & Guardrails CLI (v{VERSION})",
    )
    parser.add_argument("-v", "--version", action="version", version=f"omnistate {VERSION}")

    subparsers = parser.add_subparsers(dest="command")

    # 1. init
    p_init = subparsers.add_parser("init", parents=[root_parent], help="Initialize .omnistate in workspace and install pre-commit hook")
    p_init.add_argument("--overwrite", action="store_true", help="Overwrite existing configuration")

    # 2. begin
    p_begin = subparsers.add_parser("begin", parents=[root_parent], help="Begin a safe transactional state modification")
    p_begin.add_argument("--intent", required=True, help="Clear intent summary of the modification")
    p_begin.add_argument("--scope", default="*", help="Comma-separated scope directories or files (e.g. 'src/,tests/')")
    p_begin.add_argument("--risk", default="standard", choices=["low", "standard", "high"], help="Risk tier")
    p_begin.add_argument("--prompt", default="", help="Original raw user prompt")
    p_begin.add_argument("--non-goals", default="", help="Comma-separated non-goals/boundaries")
    p_begin.add_argument("--force", action="store_true", help="Force begin even if another session is active")

    # 3. step
    p_step = subparsers.add_parser("step", parents=[root_parent], help="Record an incremental milestone step in active transaction")
    p_step.add_argument("--action", required=True, help="Action taken")
    p_step.add_argument("--details", default="", help="Additional details or output")

    p_memo = subparsers.add_parser("memo", parents=[root_parent], help="Create or update the active requirement memo")
    p_memo.add_argument("--prompt", required=True, help="Original user requirement")
    p_memo.add_argument("--references", default="", help="Comma-separated references")

    p_review = subparsers.add_parser("plan-review", parents=[root_parent], help="Record independent subagent review of the completed plan")
    p_review.add_argument("--agent-id", required=True, help="Independent reviewing subagent identifier")
    p_review.add_argument("--status", required=True, choices=["APPROVED", "CHANGES_REQUIRED", "RESOLVED", "CONFLICTED"])
    p_review.add_argument("--findings", default="", help="Semicolon-separated findings")
    p_review.add_argument("--recommendations", default="", help="Semicolon-separated recommendations")
    p_review.add_argument("--evidence", default="", help="Comma-separated evidence paths")

    p_check = subparsers.add_parser("checklist", parents=[root_parent], help="Manage requirement checklist")
    p_check.add_argument("action", choices=["add", "link", "status"])
    p_check.add_argument("--id", required=True, help="Checklist id")
    p_check.add_argument("--title", default="")
    p_check.add_argument("--acceptance", default="")
    p_check.add_argument("--subtask", default="")
    p_check.add_argument("--verification", action="store_true")
    p_check.add_argument("--value", default="TODO", help="Checklist status")
    p_check.add_argument("--evidence", default="")

    p_subtask = subparsers.add_parser("subtask", parents=[root_parent], help="Create, assign, or complete a subtask")
    p_subtask.add_argument("action", choices=["add", "assign", "result"])
    p_subtask.add_argument("--id", required=True, help="Subtask id")
    p_subtask.add_argument("--title", default="")
    p_subtask.add_argument("--type", default="implementation")
    p_subtask.add_argument("--depends-on", default="")
    p_subtask.add_argument("--owner", default="primary")
    p_subtask.add_argument("--agent-id", default="")
    p_subtask.add_argument("--role", default="worker")
    p_subtask.add_argument("--value", default="PASS")
    p_subtask.add_argument("--result", default="")
    p_subtask.add_argument("--evidence", default="")

    # postmortem
    p_postmortem = subparsers.add_parser("postmortem", parents=[root_parent], help="Record postmortem reflection, flaws, and root-cause analysis")
    p_postmortem.add_argument("--summary", required=True, help="Executive summary of the postmortem review")
    p_postmortem.add_argument("--flaw", action="append", default=[], help="Flaw item in format 'title:description:severity' (e.g. 'Fuzzy Match:Lacking phonetic fallback:HIGH')")
    p_postmortem.add_argument("--cause", action="append", default=[], help="Root cause description (can be specified multiple times)")
    p_postmortem.add_argument("--mitigation", action="append", default=[], help="Future mitigation or action item (can be specified multiple times)")
    p_postmortem.add_argument("--report", default="", help="Path to markdown postmortem report file (e.g. 18_Note/xxx.md)")

    # 4. audit
    p_audit = subparsers.add_parser("audit", parents=[root_parent], help="Audit modifications against scope, anti-laziness, and test gates")
    p_audit.add_argument("--files", default=None, help="Comma-separated file list (default: checks git status)")
    p_audit.add_argument("--no-tests", action="store_true", help="Skip running configured test suite")

    # 5. finish
    p_finish = subparsers.add_parser("finish", parents=[root_parent], help="Verify fingerprints, archive snapshot, and issue commit clearance")
    p_finish.add_argument("--evidence", default="", help="Comma-separated paths to verification evidence files")
    p_finish.add_argument("--note", default="", help="Completion summary note")

    # 6. abort
    p_abort = subparsers.add_parser("abort", parents=[root_parent], help="Abort active transaction")
    p_abort.add_argument("--rollback", action="store_true", help="Revert uncommitted modifications in scope via git")
    p_abort.add_argument("--note", default="", help="Reason for aborting")

    # 7. status
    p_status = subparsers.add_parser("status", parents=[root_parent], help="Show transaction and governance status")
    p_status.add_argument("--json", action="store_true", help="Output status as structured JSON")

    # 8. diff
    p_diff = subparsers.add_parser("diff", parents=[root_parent], help="Inspect git diff for anti-laziness and placeholder comments")

    # 9. warden
    p_warden = subparsers.add_parser("warden", parents=[root_parent], help="Pre-commit and anti-tamper security enforcement")
    p_warden.add_argument("--check-staged", action="store_true", help="Verify staged git files before commit")
    p_warden.add_argument("--install-hooks", action="store_true", help="Install pre-commit hook into .git/hooks")

    # 10. mcp
    p_mcp = subparsers.add_parser("mcp", parents=[root_parent], help="Start OMNISTATE Model Context Protocol stdio server")

    args = parser.parse_args(argv)
    if not args.command:
        parser.print_help()
        return EXIT_SUCCESS

    root_dir = Path(args.root).resolve()
    coord = OmniStateCoordinator(root_dir)

    try:
        # Command: init
        if args.command == "init":
            res = coord.init_repository(overwrite=args.overwrite)
            hooks_installed = install_git_hooks(root_dir)
            print(f"✅ Initialized OMNISTATE in {res['state_dir']}")
            print(f"📄 Config written to: {res['config_file']}")
            if hooks_installed:
                print("🛡️  Git pre-commit warden hook installed successfully!")
            return EXIT_SUCCESS

        # Command: begin
        elif args.command == "begin":
            raw_scopes = [s.strip() for s in args.scope.split(",") if s.strip()]
            raw_non_goals = [ng.strip() for ng in args.non_goals.split(",") if ng.strip()]
            session = coord.begin(
                intent_summary=args.intent,
                scope_paths=raw_scopes or ["*"],
                risk_tier=args.risk,
                prompt=args.prompt,
                non_goals=raw_non_goals,
                force=args.force,
            )
            print(f"🟢 [OMNISTATE] Transaction begun: {session.session_id}")
            print(f"🎯 Intent : {session.intent.summary}")
            print(f"📦 Scopes : {session.scope_paths}")
            print(f"⚡ Risk   : {session.risk_tier.value.upper()}")
            return EXIT_SUCCESS

        # Command: step
        elif args.command == "step":
            step = coord.record_step(action=args.action, details=args.details)
            print(f"📝 Step recorded [{step.timestamp}]: {step.action}")
            return EXIT_SUCCESS

        elif args.command == "memo":
            memo = coord.update_memo(args.prompt, [x.strip() for x in args.references.split(",") if x.strip()])
            print(json.dumps(memo, ensure_ascii=False, indent=2))
            return EXIT_SUCCESS

        elif args.command == "plan-review":
            result = coord.record_plan_review(
                args.agent_id,
                args.status,
                [x.strip() for x in args.findings.split(";") if x.strip()],
                [x.strip() for x in args.recommendations.split(";") if x.strip()],
                [x.strip() for x in args.evidence.split(",") if x.strip()],
            )
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return EXIT_SUCCESS

        elif args.command == "checklist":
            if args.action == "add":
                result = coord.add_checklist_item(args.id, args.title, args.acceptance)
            elif args.action == "link":
                result = coord.link_checklist_subtask(args.id, args.subtask, args.verification)
            else:
                result = coord.set_checklist_status(args.id, args.value, [x.strip() for x in args.evidence.split(",") if x.strip()])
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return EXIT_SUCCESS

        elif args.command == "subtask":
            if args.action == "add":
                result = coord.add_subtask(args.id, args.title, args.type, [x.strip() for x in args.depends_on.split(",") if x.strip()], args.owner)
            elif args.action == "assign":
                result = coord.assign_subtask(args.id, args.agent_id, args.role)
            else:
                result = coord.record_subtask_result(args.id, args.value, [x.strip() for x in args.evidence.split(",") if x.strip()], args.result)
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return EXIT_SUCCESS

        # Command: postmortem
        elif args.command == "postmortem":
            flaw_items = []
            for item in args.flaw:
                parts = [p.strip() for p in item.split(":", 2)]
                if len(parts) == 3:
                    flaw_items.append({"title": parts[0], "description": parts[1], "severity": parts[2]})
                elif len(parts) == 2:
                    flaw_items.append({"title": parts[0], "description": parts[1], "severity": "MEDIUM"})
                else:
                    flaw_items.append({"title": parts[0], "description": "", "severity": "LOW"})

            result = coord.record_postmortem(
                summary=args.summary,
                flaws=flaw_items,
                root_causes=args.cause,
                mitigations=args.mitigation,
                report_path=args.report or None,
            )
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return EXIT_SUCCESS

        # Command: audit
        elif args.command == "audit":
            file_list = [f.strip() for f in args.files.split(",") if f.strip()] if args.files else None
            passed, gate_results = coord.audit(files=file_list, run_tests=not args.no_tests)
            print("\n================ OMNISTATE AUDIT RESULTS ================")
            for gr in gate_results:
                icon = "✅ PASS" if gr.passed else "❌ FAIL"
                print(f"  {icon} | {gr.gate_name}")
                for err in gr.errors:
                    print(f"         🚨 Error: {err}")
                for warn in gr.warnings:
                    print(f"         ⚠️  Warn : {warn}")
            print("=========================================================")
            if passed:
                print("🎉 All quality gates PASSED! Ready to execute 'omnistate finish'.\n")
                return EXIT_SUCCESS
            else:
                print("⛔ Audit FAILED. Please resolve errors before finishing.\n")
                return EXIT_GATE_FAILURE

        # Command: finish
        elif args.command == "finish":
            ev_list = [e.strip() for e in args.evidence.split(",") if e.strip()] if args.evidence else []
            session = coord.finish(evidence=ev_list, note=args.note)
            print(f"\n🎉 [OMNISTATE] Transaction COMPLETED: {session.session_id}")
            print(f"🛡️  Commit Clearance Token: {session.commit_clearance}")
            print(f"📦 Archived Revision     : #{session.metadata.get('archived_revision')}")
            print("🚀 You are now cleared to commit your changes with git!\n")
            return EXIT_SUCCESS

        # Command: abort
        elif args.command == "abort":
            session = coord.abort(rollback=args.rollback, note=args.note)
            print(f"🛑 [OMNISTATE] Transaction ABORTED: {session.session_id}")
            if args.rollback:
                print("🔄 Changes in scope rolled back.")
            return EXIT_SUCCESS

        # Command: status
        elif args.command == "status":
            if args.json:
                print(json.dumps(coord.get_status(), indent=2, ensure_ascii=False))
            else:
                print(format_status_dashboard(coord))
            return EXIT_SUCCESS

        # Command: diff
        elif args.command == "diff":
            diff_text = coord.get_git_diff_text()
            mod_files = coord.get_git_modified_files()
            critic = AntiLazinessCritic()
            res = critic.evaluate(root_dir, {"diff_text": diff_text, "modified_files": mod_files})
            print(f"🔍 Working tree diff inspection: {'PASSED' if res.passed else 'FAILED'}")
            for err in res.errors:
                print(f"  🚨 {err}")
            for warn in res.warnings:
                print(f"  ⚠️  {warn}")
            return EXIT_SUCCESS if res.passed else EXIT_GATE_FAILURE

        # Command: warden
        elif args.command == "warden":
            warden = OmniStateWarden(root_dir)
            if args.install_hooks:
                ok = install_git_hooks(root_dir)
                if ok:
                    print("🛡️  Git pre-commit warden hook installed successfully!")
                    return EXIT_SUCCESS
                else:
                    print("❌ Failed to install hooks: No .git directory found.")
                    return EXIT_CONFIGURATION_ERROR
            elif args.check_staged:
                return warden.check_staged()
            else:
                p_warden.print_help()
                return EXIT_SUCCESS

        # Command: mcp
        elif args.command == "mcp":
            from omnistate.mcp.protocol import McpServer
            server = McpServer(root_dir)
            server.run_stdio()
            return EXIT_SUCCESS

    except Exception as e:
        print(f"\n❌ [OMNISTATE ERROR]: {e}\n", file=sys.stderr)
        return EXIT_SESSION_ERROR

    return EXIT_SUCCESS


if __name__ == "__main__":
    sys.exit(main())
