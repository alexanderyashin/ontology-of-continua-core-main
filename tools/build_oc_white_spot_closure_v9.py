from __future__ import annotations

import argparse
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


TOOLS_DIR = Path(__file__).resolve().parent
REPO_ROOT = TOOLS_DIR.parent
LOGION_ROOT = Path("C:/Users/Megaport/work/worktrees/oc13-publication-clean")
PRIVATE_STATUS_DIR = LOGION_ROOT / "logion" / "k0" / "governance" / "status"

PUBLIC_EDITORIAL_DIR = REPO_ROOT / "releases" / "oc_core_1_3" / "editorial" / "research_gaps_closure"
PUBLIC_REDLINE_DIR = (
    REPO_ROOT / "releases" / "oc_core_1_3" / "manuscripts" / "redline" / "oc_1_3_1_white_spot_closure"
)
PUBLIC_HOSTILE_REVIEW_DIR = (
    REPO_ROOT / "releases" / "oc_core_1_3" / "editorial" / "dossier_packages" / "hostile_review" / "public_repo"
)

PRIVATE_CONTROL_PLANE_PATH = PRIVATE_STATUS_DIR / "OC_FULL_WHITE_SPOT_CLOSURE_CONTROL_PLANE_latest.json"
PRIVATE_REGISTER_PATH = PRIVATE_STATUS_DIR / "WHITE_SPOT_REGISTER_latest.json"
PRIVATE_REVIEW_PATH = PRIVATE_STATUS_DIR / "HOSTILE_REVIEW_RESPONSE_MATRIX_latest.json"
PRIVATE_REDLINE_INDEX_PATH = PRIVATE_STATUS_DIR / "OC_1_3_1_WHITE_SPOT_CLOSURE_REDLINE_INDEX_latest.json"

OUTPUTS = {
    "summary_md": PUBLIC_EDITORIAL_DIR / "OC_1_3_1_WHITE_SPOT_CLOSURE_PUBLIC_SUMMARY_latest.md",
    "register_json": PUBLIC_EDITORIAL_DIR / "OC_1_3_1_WHITE_SPOT_REGISTER_PUBLIC_latest.json",
    "review_md": PUBLIC_EDITORIAL_DIR / "OC_1_3_1_HOSTILE_REVIEW_RESPONSE_PUBLIC_latest.md",
    "index_json": PUBLIC_EDITORIAL_DIR / "OC_1_3_1_RESEARCH_GAPS_CLOSURE_INDEX_latest.json",
    "claim_boundary_md": PUBLIC_EDITORIAL_DIR / "OC_1_3_1_PUBLIC_CLAIM_BOUNDARY_NOTE_latest.md",
    "review_packet_md": PUBLIC_HOSTILE_REVIEW_DIR / "oc_1_3_1_white_spot_closure_review_packet_latest.md",
    "manifest_json": PUBLIC_HOSTILE_REVIEW_DIR / "manifest.json",
    "redlines_md": PUBLIC_REDLINE_DIR / "OC_1_3_1_WHITE_SPOT_CLOSURE_REDLINES_latest.md",
}


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def git(args: list[str], cwd: Path) -> str:
    proc = subprocess.run(args, cwd=cwd, capture_output=True, text=True, check=True)
    return proc.stdout.strip()


def git_head_sha() -> str:
    return git(["git", "rev-parse", "HEAD"], REPO_ROOT)


def git_branch() -> str:
    return git(["git", "rev-parse", "--abbrev-ref", "HEAD"], REPO_ROOT)


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not text.endswith("\n"):
        text += "\n"
    path.write_text(text, encoding="utf-8")


def compact(value: Any) -> str:
    return " ".join(str(value or "").replace("\r", " ").replace("\n", " ").replace("\t", " ").split())


def render_rows(rows: list[dict[str, Any]], fields: list[str]) -> str:
    if not rows:
        return "- none"
    return "\n".join(
        "- " + "; ".join(f"{field}={compact(row.get(field, ''))}" for field in fields) for row in rows
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Materialize the public-safe OC v9 white-spot closure companion.")
    parser.add_argument("--run-id", default="oc_white_spot_closure_v9_public")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    control_plane = load_json(PRIVATE_CONTROL_PLANE_PATH)
    register = load_json(PRIVATE_REGISTER_PATH)
    review_matrix = load_json(PRIVATE_REVIEW_PATH)
    redline_index = load_json(PRIVATE_REDLINE_INDEX_PATH)

    control_summary = dict(control_plane.get("summary") or {})
    if control_summary.get("private_closure_gate_status") != "PASS":
        raise SystemExit("Private v9 closure gate is not PASS.")

    public_rows = [
        {
            "gap_id": row["gap_id"],
            "name": row["name"],
            "public_status": row["current_repo_status"],
            "theorem_fate_class": row["theorem_fate_class"],
            "claim_boundary_class": row["claim_boundary_class"],
            "public_note": row["reviewer_note"],
        }
        for row in register.get("rows") or []
        if isinstance(row, dict)
    ]
    public_review_rows = [
        {
            "objection_id": row["objection_id"],
            "claim_text": row["claim_text"],
            "response_mode": row["response_mode"],
            "remaining_frontier": row["remaining_frontier"],
        }
        for row in review_matrix.get("rows") or []
        if isinstance(row, dict)
    ]
    public_redline_rows = [
        {
            "redline_id": row["redline_id"],
            "target_zone": row["target_zone"],
            "change_type": row["change_type"],
            "reason": row["reason"],
        }
        for row in redline_index.get("rows") or []
        if isinstance(row, dict)
    ]

    generated_at = now_utc()
    repo_sha = git_head_sha()
    branch = git_branch()

    summary_md = "\n".join(
        [
            "# OC 1.3.1 White-Spot Closure Public Summary",
            "",
            f"- run_id: {args.run_id}",
            f"- public_branch: {branch}",
            f"- public_repo_sha: {repo_sha}",
            f"- white_spot_total: {control_summary.get('white_spot_total', 0)}",
            f"- already_closed_total: {control_summary.get('already_closed_total', 0)}",
            f"- partially_closed_total: {control_summary.get('partially_closed_total', 0)}",
            f"- unresolved_blocker_total: {control_summary.get('unresolved_blocker_total', 0)}",
            f"- k0_classification: {control_summary.get('k0_classification', 'UNSET')}",
            f"- feedback_topology_classification: {control_summary.get('feedback_topology_classification', 'UNSET')}",
            "",
            "## Public-safe white-spot rows",
            "",
            render_rows(public_rows[:12], ["gap_id", "public_status", "theorem_fate_class", "claim_boundary_class"]),
            "",
        ]
    )
    review_md = "\n".join(
        [
            "# OC 1.3.1 Hostile Review Response Public",
            "",
            render_rows(public_review_rows, ["objection_id", "claim_text", "response_mode", "remaining_frontier"]),
            "",
        ]
    )
    claim_boundary_md = "\n".join(
        [
            "# OC 1.3.1 Public Claim Boundary Note",
            "",
            "- This public companion does not widen theorem-core or public claim boundaries.",
            "- K0 remains strictly classified as a non-dynamical substrate in the public-safe summary.",
            "- Any stronger extension-language remains explicitly non-theorem-bearing unless separately promoted.",
            "",
        ]
    )
    review_packet_md = "\n".join(
        [
            "# OC 1.3.1 White-Spot Closure Review Packet",
            "",
            "- package_class: public_repo / hostile_review / white_spot_closure",
            f"- white_spot_total: {control_summary.get('white_spot_total', 0)}",
            f"- unresolved_blocker_total: {control_summary.get('unresolved_blocker_total', 0)}",
            "",
            "## Included surfaces",
            "",
            f"- {OUTPUTS['summary_md'].resolve().relative_to(REPO_ROOT.resolve()).as_posix()}",
            f"- {OUTPUTS['review_md'].resolve().relative_to(REPO_ROOT.resolve()).as_posix()}",
            f"- {OUTPUTS['redlines_md'].resolve().relative_to(REPO_ROOT.resolve()).as_posix()}",
            "",
        ]
    )
    redlines_md = "\n".join(
        [
            "# OC 1.3.1 White-Spot Closure Redlines",
            "",
            render_rows(public_redline_rows, ["redline_id", "target_zone", "change_type", "reason"]),
            "",
        ]
    )

    index_json = {
        "schema_id": "OC_1_3_1_RESEARCH_GAPS_CLOSURE_INDEX_v1",
        "generated_at_utc": generated_at,
        "repo_sha": repo_sha,
        "branch": branch,
        "status": "INSTITUTE_GRADE_PUBLIC_SURFACE",
        "summary": {
            "white_spot_total": int(control_summary.get("white_spot_total", 0) or 0),
            "already_closed_total": int(control_summary.get("already_closed_total", 0) or 0),
            "partially_closed_total": int(control_summary.get("partially_closed_total", 0) or 0),
            "unresolved_blocker_total": int(control_summary.get("unresolved_blocker_total", 0) or 0),
            "k0_classification": str(control_summary.get("k0_classification", "") or ""),
            "feedback_topology_classification": str(control_summary.get("feedback_topology_classification", "") or ""),
            "public_safe_row_total": len(public_rows),
        },
        "refs": {
            "summary_ref": OUTPUTS["summary_md"].resolve().relative_to(REPO_ROOT.resolve()).as_posix(),
            "register_ref": OUTPUTS["register_json"].resolve().relative_to(REPO_ROOT.resolve()).as_posix(),
            "review_ref": OUTPUTS["review_md"].resolve().relative_to(REPO_ROOT.resolve()).as_posix(),
            "claim_boundary_ref": OUTPUTS["claim_boundary_md"].resolve().relative_to(REPO_ROOT.resolve()).as_posix(),
            "review_packet_ref": OUTPUTS["review_packet_md"].resolve().relative_to(REPO_ROOT.resolve()).as_posix(),
            "redlines_ref": OUTPUTS["redlines_md"].resolve().relative_to(REPO_ROOT.resolve()).as_posix(),
        },
    }
    register_json = {
        "schema_id": "OC_1_3_1_WHITE_SPOT_REGISTER_PUBLIC_v1",
        "generated_at_utc": generated_at,
        "repo_sha": repo_sha,
        "rows": public_rows,
        "summary": {
            "row_total": len(public_rows),
            "already_closed_total": sum(1 for row in public_rows if row["public_status"] == "ALREADY_CLOSED"),
            "partially_closed_total": sum(1 for row in public_rows if row["public_status"] == "PARTIALLY_CLOSED"),
        },
    }
    manifest_json = {
        "package_id": "hostile_review/public_repo",
        "generated_at_utc": generated_at,
        "repo_sha": repo_sha,
        "status": "CRITIQUE_READY",
        "files": [
            OUTPUTS["summary_md"].resolve().relative_to(REPO_ROOT.resolve()).as_posix(),
            OUTPUTS["register_json"].resolve().relative_to(REPO_ROOT.resolve()).as_posix(),
            OUTPUTS["review_md"].resolve().relative_to(REPO_ROOT.resolve()).as_posix(),
            OUTPUTS["claim_boundary_md"].resolve().relative_to(REPO_ROOT.resolve()).as_posix(),
            OUTPUTS["review_packet_md"].resolve().relative_to(REPO_ROOT.resolve()).as_posix(),
            OUTPUTS["redlines_md"].resolve().relative_to(REPO_ROOT.resolve()).as_posix(),
        ],
    }

    write_text(OUTPUTS["summary_md"], summary_md)
    write_json(OUTPUTS["register_json"], register_json)
    write_text(OUTPUTS["review_md"], review_md)
    write_json(OUTPUTS["index_json"], index_json)
    write_text(OUTPUTS["claim_boundary_md"], claim_boundary_md)
    write_text(OUTPUTS["review_packet_md"], review_packet_md)
    write_text(OUTPUTS["redlines_md"], redlines_md)
    write_json(OUTPUTS["manifest_json"], manifest_json)

    print(index_json["status"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
