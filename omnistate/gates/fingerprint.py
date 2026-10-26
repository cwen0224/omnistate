# -*- coding: utf-8 -*-
"""
OMNISTATE Cryptographic Fingerprint Utilities
Generates deterministic SHA-256 signatures for files and trees.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Dict, Iterable, List, Optional


def compute_file_sha256(path: Path) -> str:
    """Calculates SHA-256 for a given file. Returns 'DELETED' if missing."""
    if not path.is_file():
        return "DELETED"
    hasher = hashlib.sha256()
    with path.open("rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def compute_files_fingerprint(root_dir: Path, rel_paths: Iterable[str]) -> Dict[str, str]:
    """Generates a sorted dictionary of relative_path -> sha256."""
    fingerprint: Dict[str, str] = {}
    for raw_rel in sorted(set(rel_paths)):
        clean_rel = raw_rel.replace("\\", "/").strip()
        while clean_rel.startswith("./"):
            clean_rel = clean_rel[2:]
        if not clean_rel:
            continue
        full_path = (root_dir / clean_rel).resolve()
        try:
            norm_rel = full_path.relative_to(root_dir.resolve()).as_posix()
        except ValueError:
            norm_rel = clean_rel
        fingerprint[norm_rel] = compute_file_sha256(full_path)
    return fingerprint
