#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
Init placeholder content for CrossK module files.

- Defines a set of standard cross-K chapter files up to MAX_K.
- Creates them under content/crossk/ if missing.
- Skips crossk_master.tex and the auto-include file.
- If a file is empty or comment-only, writes a structured placeholder.
"""

from pathlib import Path
import re

CROSSK_DIR = Path("content/crossk")

# ------------------------------------------------------------
# Configuration: up to which K-level do we want CrossK stubs?
# This gives neighbour bridges: K0–K1, K1–K2, ..., K11–K12.
# Change this ONE number if you ever extend/shrink the ladder.
# ------------------------------------------------------------
MAX_K = 12

# Build the default list of neighbour cross-K files
CROSSK_FILES = [
    f"crossk_k{i}_k{i+1}.tex"
    for i in range(MAX_K)
]

# Plus one global file
CROSSK_FILES.append("crossk_global_landscape.tex")

HEADER_TEMPLATE = r"""% ======================================================================
% Ontology of Continua — Core 1.1
% Cross-K module: {fname}
% This file is currently a structural placeholder.
% Replace this stub with real content when ready.
% ======================================================================

\subsection{{{title}}}
\label{{sec:crossk-{label}}}

% TODO: Describe the cross-level structure, thresholds, and operators
%       relevant to this K-level combination.
%
% Suggested outline:
%   1. Levels involved and their roles
%   2. Shared / inherited axes and thresholds
%   3. Cross-level flows (J), cycles (C), and tensions (T)
%   4. Birth / death conditions across the levels
%   5. Empirical or conceptual examples

"""

def is_empty_or_comment_only(text: str) -> bool:
    """Return True if file has no non-comment, non-whitespace content."""
    stripped = text.strip()
    if not stripped:
        return True
    # Remove LaTeX comments line by line
    lines = [re.sub(r"%.*", "", line).strip() for line in text.splitlines()]
    joined = "".join(lines).strip()
    return not joined


def make_title_from_filename(fname: str) -> str:
    """
    'crossk_k3_k4.tex' -> 'K3–K4 cross-level structure'
    'crossk_global_landscape.tex' -> 'Global cross-K landscape'
    """
    base = fname.replace(".tex", "")
    base = re.sub(r"^crossk_?", "", base)
    if base == "global_landscape":
        return "Global cross-K landscape"
    parts = re.split(r"[_\-]+", base)
    parts = [p for p in parts if p]
    if not parts:
        return "Cross-level structure"
    title = " ".join(
        p.upper() if p.lower().startswith("k") and p[1:].isdigit()
        else p.capitalize()
        for p in parts
    )
    return f"{title} cross-level structure"


def make_label_from_filename(fname: str) -> str:
    """
    'crossk_k3_k4.tex' -> 'k3-k4'
    """
    base = fname.replace(".tex", "")
    base = re.sub(r"^crossk_?", "", base)
    base = re.sub(r"[^a-zA-Z0-9]+", "-", base)
    base = base.strip("-").lower()
    return base or "generic"


def main():
    if not CROSSK_DIR.exists():
        raise SystemExit(f"{CROSSK_DIR} does not exist")

    # Ensure all desired files at least exist
    for fname in CROSSK_FILES:
        path = CROSSK_DIR / fname
        if not path.exists():
            path.write_text("% auto-created CrossK stub\n", encoding="utf-8")
            print(f"Created empty stub: {fname}")

    # Now walk through all .tex in content/crossk
    tex_files = sorted(CROSSK_DIR.glob("*.tex"))
    if not tex_files:
        print("No .tex files found in content/crossk/")
        return

    for path in tex_files:
        fname = path.name
        if fname in ("crossk_master.tex", "_auto_crossk_inputs.tex"):
            print(f"Skip meta file: {fname}")
            continue

        text = path.read_text(encoding="utf-8")
        if not is_empty_or_comment_only(text):
            print(f"Keep as-is (non-empty): {fname}")
            continue

        title = make_title_from_filename(fname)
        label = make_label_from_filename(fname)

        placeholder = HEADER_TEMPLATE.format(
            fname=fname,
            title=title,
            label=label,
        )
        path.write_text(placeholder, encoding="utf-8")
        print(f"Initialized placeholder in: {fname}")


if __name__ == "__main__":
    main()
