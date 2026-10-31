"""Glue between Omnistate's begin/step/audit/finish and the governance primitives."""
from __future__ import annotations

import json
import time
from pathlib import Path

from . import audit as A


def _read(p: Path, default=None):
    try:
        return json.loads(p.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError):
        return default


def _write(p: Path, data) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def load_manifest(path: Path) -> dict:
    if path.suffix in (".yaml", ".yml"):
        import yaml  # optional dependency; JSON manifests need nothing
        return yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return _read(path, {})


def render_capabilities(manifest: dict) -> str:
    lines = ["[CAPABILITIES — use these; do not write replacement scripts]"]
    for c in manifest.get("capabilities", []):
        prod = ", ".join(c.get("produces", []))
        lines.append(f"- {c['id']}: {c['invoke']}" + (f"   → {prod}" if prod else ""))
    return "\n".join(lines)


class CapabilityGovernance:
    """Implements the GovernanceHook shape: on_begin / on_audit / on_finish."""

    def __init__(self, root: str | Path):
        self.root = Path(root).resolve()
        self.cfg = _read(self.root / ".omnistaterc.json", {})
        self.manifest = load_manifest(self.root / self.cfg.get("capability_manifest", "capabilities.manifest.json"))
        self.state = self.root / ".omni" / "state"

    # --- human-only: the guard hook refuses to let the agent run this ---
    def grant_extend(self, files: list[str], ttl_minutes: int = 60) -> Path:
        t = {"files": files, "granted_at": time.time(), "expires_at": time.time() + ttl_minutes * 60}
        _write(self.state / "extend_ticket.json", t)
        return self.state / "extend_ticket.json"

    def on_begin(self, mode: str | None = None) -> str:
        mode = mode or self.cfg.get("modes", {}).get("default", "operate")
        if mode == "extend" and not A.ticket_valid(self.root):
            raise PermissionError("extend mode requires a human-issued ticket: run `grant-extend` in your own terminal")
        _write(self.state / "session.json", {"mode": mode, "started_at": time.time()})
        _write(self.state / "baseline.json", A.take_baseline(self.root, self.cfg))
        frame = (f"[MODE: {mode}] You are OPERATING the project's tools, not scripting around them. "
                 + ("No new code files; no direct remotion/chrome/ffmpeg; no python -c / node -e."
                    if mode == "operate" else "Only files covered by the human extend ticket may be created."))
        return f"{frame}\n{render_capabilities(self.manifest)}"

    def on_audit(self) -> list[A.Violation]:
        base = _read(self.state / "baseline.json")
        if base is None:
            raise RuntimeError("no baseline: `begin` was not run")
        return A.audit(self.root, self.cfg, base, self.manifest)

    def on_finish(self, violations: list[A.Violation]) -> Path:
        out = self.root / ".omni" / "reports" / "last_audit.json"
        _write(out, {"at": time.time(), "violations": [v.__dict__ for v in violations]})
        return out

    def propose(self, extends: str, reason: str) -> Path:
        p = self.root / ".omni" / "proposals" / f"{int(time.time())}_{extends.replace('.', '_')}.json"
        _write(p, {"extends": extends, "reason": reason, "status": "pending_human_review"})
        return p
