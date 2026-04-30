"""Logion Release Machine for external release quality control."""

from __future__ import annotations

try:
    from .versioning import current_release

    __version__ = current_release().version
except Exception:  # pragma: no cover - import-time fallback for broken worktrees
    __version__ = "0+unknown"
