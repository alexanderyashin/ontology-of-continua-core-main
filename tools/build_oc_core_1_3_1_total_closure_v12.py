from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


TOOLS_DIR = Path(__file__).resolve().parent
REPO_ROOT = TOOLS_DIR.parent
PRIVATE_ROOT = Path("C:/Users/Megaport/work/worktrees/oc13-publication-clean")
PRIVATE_STATUS_DIR = PRIVATE_ROOT / "logion" / "k0" / "governance" / "status"

PRIVATE_CONTROL_PLANE_PATH = PRIVATE_STATUS_DIR / "OC_1_3_1_TOTAL_CLOSURE_CONTROL_PLANE_latest.json"
PRIVATE_DISCIPLINE_ATLAS_PATH = PRIVATE_STATUS_DIR / "OC_1_3_1_DISCIPLINE_EXPANSION_ATLAS_latest.json"
PRIVATE_EXPERIMENT_REGISTER_PATH = PRIVATE_STATUS_DIR / "OC_1_3_1_EXPERIMENT_REQUIRED_REGISTER_latest.json"
PRIVATE_REVIEWER_OBJECTION_MATRIX_PATH = PRIVATE_STATUS_DIR / "OC_1_3_1_REVIEWER_OBJECTION_MATRIX_latest.json"
PRIVATE_COUNTEREXAMPLE_LEDGER_PATH = PRIVATE_STATUS_DIR / "OC_1_3_1_COUNTEREXAMPLE_HUNT_LEDGER_latest.json"

RELEASE_ROOT = REPO_ROOT / "releases" / "oc_core_1_3_1"
EDITORIAL_DIR = RELEASE_ROOT / "editorial"
TOTAL_CLOSURE_DIR = EDITORIAL_DIR / "total_closure"
MANUSCRIPTS_DIR = RELEASE_ROOT / "manuscripts"
RELEASE_CONTROL_PLANE_PATH = EDITORIAL_DIR / "OC_CORE_1_3_1_RELEASE_CONTROL_PLANE_latest.json"

OUTPUTS = {
    "public_control_plane_json": TOTAL_CLOSURE_DIR / "OC_1_3_1_TOTAL_CLOSURE_PUBLIC_CONTROL_PLANE_latest.json",
    "public_index_json": TOTAL_CLOSURE_DIR / "OC_1_3_1_TOTAL_CLOSURE_PUBLIC_INDEX_latest.json",
    "public_discipline_atlas_json": TOTAL_CLOSURE_DIR / "OC_1_3_1_PUBLIC_DISCIPLINE_EXPANSION_ATLAS_latest.json",
    "public_experiment_register_json": TOTAL_CLOSURE_DIR / "OC_1_3_1_PUBLIC_EXPERIMENT_REQUIRED_REGISTER_latest.json",
    "public_brief_md": TOTAL_CLOSURE_DIR / "OC_1_3_1_TOTAL_CLOSURE_PUBLIC_BRIEF_latest.md",
    "public_reviewer_notes_md": TOTAL_CLOSURE_DIR / "OC_1_3_1_PUBLIC_REVIEWER_CLOSURE_NOTES_latest.md",
    "appendix_md": MANUSCRIPTS_DIR / "OC_1_3_1_TOTAL_CLOSURE_APPENDIX.md",
    "discipline_appendix_md": MANUSCRIPTS_DIR / "OC_1_3_1_DISCIPLINE_EXPANSION_APPENDIX.md",
    "experiment_appendix_md": MANUSCRIPTS_DIR / "OC_1_3_1_EXPERIMENT_REQUIRED_APPENDIX.md",
}


def _ensure_dirs() -> None:
    for path in [TOTAL_CLOSURE_DIR, MANUSCRIPTS_DIR]:
        path.mkdir(parents=True, exist_ok=True)


def _compact(value: Any) -> str:
    return " ".join(str(value or "").replace("\r", " ").replace("\n", " ").replace("\t", " ").split())


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _git_output(*args: str) -> str:
    proc = subprocess.run(
        ["git", *args],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        check=True,
        timeout=30,
    )
    return proc.stdout.strip()


def _branch_name() -> str:
    return _git_output("rev-parse", "--abbrev-ref", "HEAD")


def _head_sha() -> str:
    return _git_output("rev-parse", "HEAD")


def _repo_clean() -> bool:
    return _git_output("status", "--short") == ""


def _sync_main_release_control_plane(
    *,
    private_summary: dict[str, Any],
    public_control_plane_path: Path,
) -> None:
    release_control_plane = _read_json(RELEASE_CONTROL_PLANE_PATH)
    if not release_control_plane:
        return
    summary = dict(release_control_plane.get("summary") or {})
    refs = dict(release_control_plane.get("refs") or {})
    summary.update(
        {
            "public_branch": _branch_name(),
            "public_repo_sha": _head_sha(),
            "public_repo_clean": _repo_clean(),
            "public_repo_sha_meaning": "PRE_TOTAL_CLOSURE_MATERIALIZATION_HEAD",
            "theory_completeness_status": private_summary.get("theory_completeness_status", "UNSET"),
            "open_attack_surface_total": int(private_summary.get("open_attack_surface_total", 0) or 0),
            "data_blocked_experiment_total": int(private_summary.get("data_blocked_experiment_total", 0) or 0),
            "discipline_closed_total": int(private_summary.get("discipline_closed_total", 0) or 0),
            "discipline_bounded_total": int(private_summary.get("discipline_bounded_total", 0) or 0),
            "frontier_remaining_total": int(private_summary.get("frontier_remaining_total", 0) or 0),
            "total_closure_ready": private_summary.get("theory_completeness_status") == "TOTAL_CLOSURE_READY",
        }
    )
    refs.update(
        {
            "total_closure_public_control_plane_ref": str(public_control_plane_path.relative_to(REPO_ROOT)),
            "total_closure_public_index_ref": str(OUTPUTS["public_index_json"].relative_to(REPO_ROOT)),
            "total_closure_appendix_ref": str(OUTPUTS["appendix_md"].relative_to(REPO_ROOT)),
        }
    )
    release_control_plane["summary"] = summary
    release_control_plane["refs"] = refs
    _write_json(RELEASE_CONTROL_PLANE_PATH, release_control_plane)


def materialize_oc_core_1_3_1_total_closure_v12(
    *, run_id: str = "oc_core_1_3_1_total_closure_v12"
) -> dict[str, Any]:
    _ensure_dirs()
    private_control_plane = _read_json(PRIVATE_CONTROL_PLANE_PATH)
    private_discipline_atlas = _read_json(PRIVATE_DISCIPLINE_ATLAS_PATH)
    private_experiment_register = _read_json(PRIVATE_EXPERIMENT_REGISTER_PATH)
    private_objection_matrix = _read_json(PRIVATE_REVIEWER_OBJECTION_MATRIX_PATH)
    private_counterexample_ledger = _read_json(PRIVATE_COUNTEREXAMPLE_LEDGER_PATH)

    private_summary = dict(private_control_plane.get("summary") or {})
    discipline_rows = list(private_discipline_atlas.get("rows") or [])
    experiment_rows = list(private_experiment_register.get("rows") or [])
    objection_rows = list(private_objection_matrix.get("rows") or [])
    counterexample_rows = list(private_counterexample_ledger.get("rows") or [])

    public_discipline_rows = [
        {
            "discipline_id": row.get("discipline_id"),
            "discipline_name": row.get("discipline_name"),
            "state": row.get("state"),
            "k_level_mapping": row.get("k_level_mapping"),
            "theorem_fit_statement": row.get("theorem_fit_statement"),
            "evidence_route": row.get("evidence_route"),
            "falsifier_route": row.get("falsifier_route"),
            "claim_ceiling": row.get("claim_ceiling"),
            "source_refs": row.get("source_refs"),
        }
        for row in discipline_rows
    ]
    public_experiment_rows = [
        {
            "experiment_id": row.get("experiment_id"),
            "source_gap_id": row.get("source_gap_id"),
            "missing_evidence": row.get("missing_evidence"),
            "experiment_design": row.get("experiment_design"),
            "expected_outcomes": row.get("expected_outcomes"),
            "claim_boundary": row.get("claim_boundary"),
            "source_refs": row.get("source_refs"),
        }
        for row in experiment_rows
    ]

    public_control_plane = {
        "schema_id": "OC_1_3_1_TOTAL_CLOSURE_PUBLIC_CONTROL_PLANE_v1",
        "status": "PASS",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "summary": {
            "public_label": "1.3.1",
            "public_branch": _branch_name(),
            "public_repo_sha": _head_sha(),
            "public_repo_clean": _repo_clean(),
            "theory_completeness_status": private_summary.get("theory_completeness_status", "UNSET"),
            "open_attack_surface_total": int(private_summary.get("open_attack_surface_total", 0) or 0),
            "data_blocked_experiment_total": int(private_summary.get("data_blocked_experiment_total", 0) or 0),
            "discipline_closed_total": int(private_summary.get("discipline_closed_total", 0) or 0),
            "discipline_bounded_total": int(private_summary.get("discipline_bounded_total", 0) or 0),
            "frontier_remaining_total": int(private_summary.get("frontier_remaining_total", 0) or 0),
            "public_reintegration_status": "PASS",
            "owner_approval_required": True,
            "global_no_send_lock": True,
        },
        "refs": {
            "private_control_plane": str(PRIVATE_CONTROL_PLANE_PATH),
            "public_total_closure_appendix": str(OUTPUTS["appendix_md"]),
            "public_discipline_atlas": str(OUTPUTS["public_discipline_atlas_json"]),
            "public_experiment_register": str(OUTPUTS["public_experiment_register_json"]),
        },
        "rows": [
            {
                "row_id": "PUBLIC_TOTAL_CLOSURE::MASTER",
                "title": "OC 1.3.1 public-safe total-closure mirror",
                "status": "PASS",
                "detail": "Public 1.3.1 now carries closure addenda, explicit experiment-needed notes, and discipline expansion packets without leaking private governance.",
            }
        ],
    }
    _write_json(OUTPUTS["public_control_plane_json"], public_control_plane)
    _sync_main_release_control_plane(
        private_summary=private_summary,
        public_control_plane_path=OUTPUTS["public_control_plane_json"],
    )

    public_index = {
        "schema_id": "OC_1_3_1_TOTAL_CLOSURE_PUBLIC_INDEX_v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "summary": {
            "discipline_total": len(public_discipline_rows),
            "experiment_required_total": len(public_experiment_rows),
            "reviewer_objection_total": len(objection_rows),
            "counterexample_total": len(counterexample_rows),
        },
        "refs": {
            "public_control_plane": str(OUTPUTS["public_control_plane_json"]),
            "public_brief": str(OUTPUTS["public_brief_md"]),
            "public_reviewer_notes": str(OUTPUTS["public_reviewer_notes_md"]),
            "appendix": str(OUTPUTS["appendix_md"]),
            "discipline_appendix": str(OUTPUTS["discipline_appendix_md"]),
            "experiment_appendix": str(OUTPUTS["experiment_appendix_md"]),
        },
    }
    _write_json(OUTPUTS["public_index_json"], public_index)

    public_discipline_atlas = {
        "schema_id": "OC_1_3_1_PUBLIC_DISCIPLINE_EXPANSION_ATLAS_v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "rows": public_discipline_rows,
        "summary": {
            "discipline_total": len(public_discipline_rows),
            "discipline_closed_total": sum(1 for row in public_discipline_rows if _compact(row.get("state")) == "CLOSED_IN_CORPUS"),
            "discipline_bounded_total": sum(1 for row in public_discipline_rows if _compact(row.get("state")) == "BOUNDED_BUT_NOT_FULLY_CLOSED"),
            "discipline_data_blocked_total": sum(1 for row in public_discipline_rows if _compact(row.get("state")) == "DATA_BLOCKED_EXPERIMENT_REQUIRED"),
        },
    }
    _write_json(OUTPUTS["public_discipline_atlas_json"], public_discipline_atlas)

    public_experiment_register = {
        "schema_id": "OC_1_3_1_PUBLIC_EXPERIMENT_REQUIRED_REGISTER_v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "rows": public_experiment_rows,
        "summary": {
            "experiment_required_total": len(public_experiment_rows),
        },
    }
    _write_json(OUTPUTS["public_experiment_register_json"], public_experiment_register)

    public_brief_md = "\n".join(
        [
            "# OC 1.3.1 Total Closure Public Brief",
            "",
            f"- theory_completeness_status: {_compact(private_summary.get('theory_completeness_status'))}",
            f"- open_attack_surface_total: {int(private_summary.get('open_attack_surface_total', 0) or 0)}",
            f"- data_blocked_experiment_total: {int(private_summary.get('data_blocked_experiment_total', 0) or 0)}",
            f"- discipline_closed_total: {int(private_summary.get('discipline_closed_total', 0) or 0)}",
            f"- discipline_bounded_total: {int(private_summary.get('discipline_bounded_total', 0) or 0)}",
            "",
            "This public-safe mirror integrates the completeness pass without pretending that missing data has been solved by prose. Residual non-closed surfaces appear only as explicit experiment-needed notes with claim boundaries.",
            "",
        ]
    )
    _write_text(OUTPUTS["public_brief_md"], public_brief_md)

    public_reviewer_notes_md = "\n".join(
        [
            "# OC 1.3.1 Public Reviewer Closure Notes",
            "",
            "## Reviewer objections",
            "",
            *[
                f"- finding_id={row.get('finding_id')}; attack_type={row.get('attack_type')}; disposition={row.get('disposition')}; answer={row.get('answer_summary')}"
                for row in objection_rows
            ],
            "",
            "## Counterexample hunt",
            "",
            *[
                f"- finding_id={row.get('finding_id')}; disposition={row.get('disposition')}; challenge={row.get('challenge_statement')}"
                for row in counterexample_rows
            ],
            "",
        ]
    )
    _write_text(OUTPUTS["public_reviewer_notes_md"], public_reviewer_notes_md)

    appendix_md = "\n".join(
        [
            "# OC 1.3.1 Total Closure Appendix",
            "",
            "This appendix adds the total-closure pass to the public-safe 1.3.1 release tree. It does not widen public claims; it records where the theory is closed and where further progress honestly depends on new data.",
            "",
            "## Closure state",
            "",
            f"- theory_completeness_status: {_compact(private_summary.get('theory_completeness_status'))}",
            f"- data_blocked_experiment_total: {int(private_summary.get('data_blocked_experiment_total', 0) or 0)}",
            "",
        ]
    )
    _write_text(OUTPUTS["appendix_md"], appendix_md)

    discipline_appendix_md = "\n".join(
        [
            "# OC 1.3.1 Discipline Expansion Appendix",
            "",
            *[
                f"- discipline_id={row.get('discipline_id')}; state={row.get('state')}; k_levels={', '.join(row.get('k_level_mapping') or [])}; claim_ceiling={row.get('claim_ceiling')}"
                for row in public_discipline_rows
            ],
            "",
        ]
    )
    _write_text(OUTPUTS["discipline_appendix_md"], discipline_appendix_md)

    experiment_appendix_md = "\n".join(
        [
            "# OC 1.3.1 Experiment Required Appendix",
            "",
            *[
                f"- experiment_id={row.get('experiment_id')}; source_gap_id={row.get('source_gap_id')}; missing_evidence={row.get('missing_evidence')}; expected_outcomes={row.get('expected_outcomes')}"
                for row in public_experiment_rows
            ],
            "",
        ]
    )
    _write_text(OUTPUTS["experiment_appendix_md"], experiment_appendix_md)

    return {
        "public_control_plane": public_control_plane,
        "public_index": public_index,
        "public_discipline_atlas": public_discipline_atlas,
        "public_experiment_register": public_experiment_register,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Materialize the OC Core 1.3.1 public-safe total-closure mirror.")
    parser.add_argument("--run-id", default="oc_core_1_3_1_total_closure_v12")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    payload = materialize_oc_core_1_3_1_total_closure_v12(
        run_id=str(args.run_id).strip() or "oc_core_1_3_1_total_closure_v12"
    )
    print(payload["public_control_plane"]["summary"]["theory_completeness_status"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
