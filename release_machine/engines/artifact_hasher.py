from __future__ import annotations

from pathlib import Path

from release_machine.core import sha256_file


def hash_file(path: str) -> str:
    return sha256_file(Path(path))
