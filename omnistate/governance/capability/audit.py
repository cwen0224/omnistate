"""Omnistate v1.3.0 — Project Capability & Anti-Adhoc Governance: deterministic audit gate.

Domain-neutral: every project-specific fact comes from .omnistaterc.json / the manifest.
Two independent checks, both git/filesystem-based (no LLM, no intent guessing):

  1. UNDECLARED_CODE_FILE — code files that appeared since `begin` (tracked-added, untracked,
     AND git-ignored), unless a valid human extend ticket covers them.
  2. UNSIGNED_ARTIFACT   — files under an artifact contract glob that are new/changed since
     `begin` and are not backed by a provenance record (path + sha256).
"""
from __future__ import annotations

import fnmatch
import hashlib
import json
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path

DEFAULT_EXCLUDES = ["**/node_modules/**", "**/.git/**", "**/.venv/**", "**/__pycache__/**"]


@dataclass(frozen=True)
class Violation:
    code: str
    subject: str
    remediation: str          # mandatory: a block without an alternative is harassment
    severity: str = "block"


# ---------- git helpers ----------
def _git(root: Path, *args: str, check: bool = True) -> str:
    r = subprocess.run(["git", *args], cwd=root, capture_output=True)
    if check and r.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {r.stderr.decode('utf-8', 'replace')}")
    return r.stdout.decode("utf-8", "replace")


def _split(z: str) -> set[str]:
    return {p for p in z.split("\0") if p}


def _excludes(cfg: dict) -> list[str]:
    pats = cfg.get("scan_excludes", DEFAULT_EXCLUDES)
    return [f":(exclude,glob){p}" for p in pats]


def _others(root: Path, cfg: dict) -> set[str]:
    ex = _excludes(cfg)
    out = _split(_git(root, "ls-files", "-z", "--others", "--exclude-standard", "--", ".", *ex))
    if cfg.get("new_code_files", {}).get("include_ignored", True):
        out |= _split(_git(root, "ls-files", "-z", "--others", "--ignored", "--exclude-standard",
                           "--", ".", *ex))
    return out


def _head(root: Path) -> str | None:
    r = _git(root, "rev-parse", "--verify", "-q", "HEAD", check=False).strip()
    return r or None


def _norm(p: str) -> str:
    return p.replace("\\", "/")


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while b := f.read(1 << 20):
            h.update(b)
    return h.hexdigest()


def _artifact_files(root: Path, cfg: dict) -> dict[str, Path]:
    found: dict[str, Path] = {}
    for c in cfg.get("artifact_contracts", []):
        for f in root.glob(c["glob"]):
            if f.is_file():
                found[_norm(f.relative_to(root).as_posix())] = f
    return found


# ---------- lifecycle entry points ----------
def take_baseline(root: Path, cfg: dict) -> dict:
    """Called by `begin`. Snapshot what already exists so audit only judges the delta."""
    return {
        "head": _head(root),
        "others": sorted(_others(root, cfg)),
        "artifacts": {p: sha256_of(f) for p, f in _artifact_files(root, cfg).items()},
        "taken_at": time.time(),
    }


def added_since(root: Path, cfg: dict, base: dict) -> set[str]:
    added: set[str] = set()
    if base.get("head"):
        added |= _split(_git(root, "diff", "-z", "--name-only", "--no-renames",
                             "--diff-filter=A", base["head"], "--", ".", *_excludes(cfg)))
    added |= _others(root, cfg) - set(base.get("others", []))
    return {p for p in map(_norm, added) if (root / p).is_file()}


def load_ledger(root: Path) -> dict[str, set[str]]:
    ledger: dict[str, set[str]] = {}
    d = root / ".omni" / "provenance"
    for f in sorted(d.glob("*.json")) if d.is_dir() else []:
        try:
            for a in json.loads(f.read_text(encoding="utf-8")).get("artifacts", []):
                ledger.setdefault(_norm(a["path"]), set()).add(a["sha256"])
        except (OSError, ValueError, KeyError):
            continue
    return ledger


def extend_allowance(root: Path, now: float | None = None) -> tuple[str, list[str]]:
    """('extend', globs) only if session.mode == extend AND a valid, unexpired human ticket exists."""
    now = now or time.time()
    try:
        sess = json.loads((root / ".omni/state/session.json").read_text(encoding="utf-8"))
        ticket = json.loads((root / ".omni/state/extend_ticket.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return "operate", []
    if sess.get("mode") == "extend" and ticket.get("expires_at", 0) > now:
        return "extend", [_norm(f).lower() for f in ticket.get("files", [])]
    return "operate", []


def ticket_valid(root: Path, now: float | None = None) -> bool:
    try:
        t = json.loads((Path(root) / ".omni/state/extend_ticket.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return False
    return t.get("expires_at", 0) > (now or time.time())


def audit(root: Path, cfg: dict, base: dict, manifest: dict) -> list[Violation]:
    root = Path(root)
    out: list[Violation] = []
    mode, allowed = extend_allowance(root)
    rule = cfg.get("new_code_files", {})
    exts = tuple(e.lower() for e in rule.get("extensions", [".py", ".ts", ".tsx", ".js", ".ps1", ".sh"]))
    sev = rule.get("severity", "block")
    hints = "\n".join(f"    {c['invoke']}" for c in manifest.get("capabilities", []) if c.get("invoke"))
    propose = cfg.get("commands", {}).get("propose", "omni propose-capability")

    for p in sorted(added_since(root, cfg, base)):
        if not p.lower().endswith(exts):
            continue
        if any(fnmatch.fnmatch(p.lower(), g.lower()) for g in rule.get("allow_globs", [])):
            continue
        if mode == "extend" and any(fnmatch.fnmatch(p.lower(), g) for g in allowed):
            continue
        out.append(Violation(
            "UNDECLARED_CODE_FILE", p,
            f"{mode} 模式不得新增程式碼檔。請改用既有能力:\n{hints}\n"
            f"能力不足: {propose} --extends <id> --reason \"...\"；"
            f"或請人類簽發 extend 票據。若為誤判，刪除該檔後重跑 audit。", sev))

    ledger = load_ledger(root)
    base_art = base.get("artifacts", {})
    for p, f in sorted(_artifact_files(root, cfg).items()):
        sha = sha256_of(f)
        if base_art.get(p) == sha:
            continue                                  # unchanged since begin
        if sha not in ledger.get(p, set()):
            out.append(Violation(
                "UNSIGNED_ARTIFACT", p,
                "此產出物在本次工作期間新增/被改動，但沒有 hpvs 簽發的來源紀錄（可能由臨時腳本產生，"
                "或在產生後被手動改過）。請用 hpvs 重新產生，不要手動複製或修改。"))
    return out


def format_report(violations: list[Violation]) -> str:
    if not violations:
        return "AUDIT PASS: no governance violations."
    lines = [f"AUDIT FAIL: {sum(v.severity == 'block' for v in violations)} blocking violation(s)"]
    for v in violations:
        lines += [f"✗ [{v.severity}] {v.code}  {v.subject}", *(f"    {l}" for l in v.remediation.splitlines())]
    return "\n".join(lines)
