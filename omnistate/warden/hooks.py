# -*- coding: utf-8 -*-
"""
OMNISTATE Git Hook Installer
Installs pre-commit warden hooks into target git repository.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path


def install_git_hooks(repo_dir: Path) -> bool:
    git_dir = repo_dir / ".git"
    if not git_dir.is_dir():
        return False

    hooks_dir = git_dir / "hooks"
    hooks_dir.mkdir(parents=True, exist_ok=True)

    pre_commit_path = hooks_dir / "pre-commit"

    # Cross-platform pre-commit hook script
    hook_content = (
        "#!/usr/bin/env sh\n"
        "# OMNISTATE Automated Pre-commit Guardrail Hook\n"
        "python -m omnistate.cli.main warden --check-staged\n"
        "EXIT_CODE=$?\n"
        "if [ $EXIT_CODE -ne 0 ]; then\n"
        "  exit $EXIT_CODE\n"
        "fi\n"
        "exit 0\n"
    )

    pre_commit_path.write_text(hook_content, encoding="utf-8")
    
    # Try to set executable permissions on POSIX systems
    try:
        current_mode = os.stat(pre_commit_path).st_mode
        os.chmod(pre_commit_path, current_mode | 0o111)
    except Exception:
        pass

    return True
