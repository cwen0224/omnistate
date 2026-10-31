"""python -m omnistate.governance.capability <begin|audit|caps|grant-extend|propose> — thin CLI for wiring."""
import argparse
import sys
from pathlib import Path

from .audit import format_report
from .lifecycle import CapabilityGovernance, render_capabilities


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="omni-governance")
    p.add_argument("--root", default=".")
    sub = p.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("begin"); b.add_argument("--mode", choices=["operate", "extend"])
    sub.add_parser("audit"); sub.add_parser("caps")
    g = sub.add_parser("grant-extend", help="HUMAN ONLY"); g.add_argument("--files", required=True); g.add_argument("--ttl", type=int, default=60)
    pr = sub.add_parser("propose"); pr.add_argument("--extends", required=True); pr.add_argument("--reason", required=True)
    a = p.parse_args(argv)
    gov = CapabilityGovernance(Path(a.root))
    if a.cmd == "begin":
        print(gov.on_begin(a.mode)); return 0
    if a.cmd == "caps":
        print(render_capabilities(gov.manifest)); return 0
    if a.cmd == "grant-extend":
        print(gov.grant_extend([f for f in a.files.split(",") if f], a.ttl)); return 0
    if a.cmd == "propose":
        print(gov.propose(a.extends, a.reason)); return 0
    v = gov.on_audit(); gov.on_finish(v); print(format_report(v))
    return 1 if any(x.severity == "block" for x in v) else 0


if __name__ == "__main__":
    sys.exit(main())
