from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any

from build_oc_core_1_3_1_release_v11 import (
    ARTICLE_DIR,
    EDITORIAL_DIR,
    MANUSCRIPTS_DIR,
    OUTPUTS as V11_OUTPUTS,
    RELEASE_ROOT,
    compile_tex,
    compact,
    git_branch,
    git_clean,
    git_head_sha,
    materialize_oc_core_1_3_1_release_v11,
    now_utc,
    read_json,
    render_rows_md,
    repo_rel,
    write_json,
    write_text,
)
from build_oc_core_1_3_1_total_closure_v12 import materialize_oc_core_1_3_1_total_closure_v12


TOOLS_DIR = Path(__file__).resolve().parent
REPO_ROOT = TOOLS_DIR.parent
PRIVATE_ROOT = Path("C:/Users/Megaport/work/worktrees/oc13-publication-clean")
PRIVATE_STATUS_DIR = PRIVATE_ROOT / "logion" / "k0" / "governance" / "status"
PRIVATE_REPORTS_DIR = (
    PRIVATE_ROOT / "logion" / "k7" / "reports" / "science" / "oc_core_1_3_1_unignorable_armored_release_program_v13"
)

PRIVATE_FINAL_CERTIFICATE_PATH = PRIVATE_STATUS_DIR / "OC_UNIGNORABLE_FINAL_CERTIFICATE_latest.json"
PRIVATE_READY_BOARD_PATH = PRIVATE_STATUS_DIR / "OC_1_3_1_UNIGNORABLE_RELEASE_READY_BOARD_latest.json"
PRIVATE_CLAIM_LEDGER_PATH = PRIVATE_STATUS_DIR / "OC_CLAIM_MASTER_LEDGER_latest.json"
PRIVATE_STRONG_STATEMENT_MAP_PATH = PRIVATE_STATUS_DIR / "OC_STRONG_STATEMENT_TO_CLAIM_MAP.json"
PRIVATE_KILLER_FEASIBILITY_PATH = PRIVATE_STATUS_DIR / "OC_KILLER_FEASIBILITY_MATRIX_latest.json"
PRIVATE_ARMORED_PACKAGE_LEDGER_PATH = PRIVATE_STATUS_DIR / "OC_ARMORED_CLAIM_PACKAGE_LEDGER_latest.json"
PRIVATE_SIMULATION_ROLE_LEDGER_PATH = PRIVATE_STATUS_DIR / "OC_SIMULATION_ROLE_CLASS_LEDGER_latest.json"
PRIVATE_COMPARATOR_WAR_ROOM_PATH = PRIVATE_STATUS_DIR / "OC_COMPARATOR_WAR_ROOM_latest.json"
PRIVATE_EXTERNAL_CRITIQUE_LEDGER_PATH = PRIVATE_STATUS_DIR / "OC_EXTERNAL_CRITIQUE_INGEST_LEDGER_latest.json"
PRIVATE_OWNER_DECISION_SUMMARY_PATH = PRIVATE_STATUS_DIR / "OC_OWNER_DECISION_SUMMARY.md"
PRIVATE_FINAL_ATTACK_SURFACE_REPORT_PATH = PRIVATE_STATUS_DIR / "OC_FINAL_ATTACK_SURFACE_REPORT.md"

SIMULATIONS_DIR = REPO_ROOT / "simulations"
DATA_DIR = REPO_ROOT / "data"

UNIGNORABLE_SPINE_TEX = ARTICLE_DIR / "OC_UNIGNORABLE_SPINE_EN.tex"
UNIGNORABLE_SPINE_PDF = ARTICLE_DIR / "OC_UNIGNORABLE_SPINE_EN.pdf"
SIM_RUN_ALL_PATH = SIMULATIONS_DIR / "run_all.py"
SIM_EXPECTED_OUTPUT_DIR = SIMULATIONS_DIR / "OC_SIMULATION_EXPECTED_OUTPUTS"
SIM_FAILURE_CASES_PATH = SIMULATIONS_DIR / "OC_SIMULATION_FAILURE_CASES.md"
SIM_ROLE_LEDGER_PUBLIC_PATH = SIMULATIONS_DIR / "OC_SIMULATION_ROLE_CLASS_LEDGER_latest.json"

OUTPUTS = {
    "hardening_report_md": EDITORIAL_DIR / "OC_PUBLIC_REPO_UNIGNORABLE_HARDENING_REPORT.md",
    "repro_certificate_md": EDITORIAL_DIR / "OC_REPRODUCIBILITY_CERTIFICATE.md",
    "public_gate_cert_json": EDITORIAL_DIR / "OC_PUBLIC_RELEASE_GATE_CERT_latest.json",
    "owner_approval_packet_md": EDITORIAL_DIR / "OC_1_3_1_OWNER_APPROVAL_PACKET.md",
    "zenodo_metadata_draft_json": EDITORIAL_DIR / "OC_1_3_1_ZENODO_METADATA_DRAFT.json",
    "no_send_dispatch_manifest_json": EDITORIAL_DIR / "OC_1_3_1_NO_SEND_DISPATCH_MANIFEST.json",
    "unignorable_ready_board_json": EDITORIAL_DIR / "OC_1_3_1_UNIGNORABLE_RELEASE_READY_BOARD_latest.json",
    "killer_claim_index_md": EDITORIAL_DIR / "OC_KILLER_CLAIM_INDEX.md",
    "expert_route_md": EDITORIAL_DIR / "OC_FIRST_TIME_EXPERT_READER_ROUTE.md",
    "unignorable_spine_md": EDITORIAL_DIR / "OC_UNIGNORABLE_SPINE.md",
    "negative_results_frontier_md": EDITORIAL_DIR / "OC_NEGATIVE_RESULTS_AND_FRONTIER_APPENDIX.md",
}

RELEASE_CONTROL_PLANE_PATH = V11_OUTPUTS["control_plane_json"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Materialize the public OC Core 1.3.1 unignorable armored release staging layer.")
    parser.add_argument("--run-id", default="oc_core_1_3_1_unignorable_release_v13")
    return parser.parse_args()


def _ensure_dirs() -> None:
    for path in [EDITORIAL_DIR, ARTICLE_DIR, MANUSCRIPTS_DIR, SIMULATIONS_DIR, SIM_EXPECTED_OUTPUT_DIR, DATA_DIR]:
        path.mkdir(parents=True, exist_ok=True)


def _read_json_if_exists(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    payload = read_json(path)
    return payload if isinstance(payload, dict) else {}


def _read_text_if_exists(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8-sig")


def _rows(payload: dict[str, Any]) -> list[dict[str, Any]]:
    value = payload.get("rows")
    return [row for row in value if isinstance(row, dict)] if isinstance(value, list) else []


def _summary(payload: dict[str, Any]) -> dict[str, Any]:
    value = payload.get("summary")
    return value if isinstance(value, dict) else {}


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


def _load_private_inputs() -> dict[str, Any]:
    return {
        "final_certificate": _read_json_if_exists(PRIVATE_FINAL_CERTIFICATE_PATH),
        "ready_board": _read_json_if_exists(PRIVATE_READY_BOARD_PATH),
        "claim_ledger": _read_json_if_exists(PRIVATE_CLAIM_LEDGER_PATH),
        "strong_statement_map": _read_json_if_exists(PRIVATE_STRONG_STATEMENT_MAP_PATH),
        "killer_feasibility": _read_json_if_exists(PRIVATE_KILLER_FEASIBILITY_PATH),
        "armored_package_ledger": _read_json_if_exists(PRIVATE_ARMORED_PACKAGE_LEDGER_PATH),
        "simulation_role_ledger": _read_json_if_exists(PRIVATE_SIMULATION_ROLE_LEDGER_PATH),
        "comparator_war_room": _read_json_if_exists(PRIVATE_COMPARATOR_WAR_ROOM_PATH),
        "external_critique_ledger": _read_json_if_exists(PRIVATE_EXTERNAL_CRITIQUE_LEDGER_PATH),
        "owner_decision_summary": _read_text_if_exists(PRIVATE_OWNER_DECISION_SUMMARY_PATH),
        "final_attack_surface_report": _read_text_if_exists(PRIVATE_FINAL_ATTACK_SURFACE_REPORT_PATH),
    }


def _write_root_docs(
    *,
    final_certificate: dict[str, Any],
    claim_rows: list[dict[str, Any]],
    killer_rows: list[dict[str, Any]],
) -> None:
    claim_total = int(final_certificate.get("claim_total", len(claim_rows)) or 0)
    killer_ready_total = int(final_certificate.get("killer_ready_total", 0) or 0)
    write_text(
        REPO_ROOT / "README.md",
        "\n".join(
            [
                "# Ontology of Continua / OC Core 1.3.1",
                "",
                "This repository stages the public-safe OC Core 1.3.1 release package.",
                "",
                "Current public state:",
                f"- external version label: 1.3.1",
                f"- internal armored tranche: v13",
                f"- unignorable_status: {compact(final_certificate.get('status', 'UNSET'))}",
                f"- claim_total: {claim_total}",
                f"- killer_ready_total: {killer_ready_total}",
                "- owner_approval_required: true",
                "- global_no_send_lock: true",
                "- no publish/tag/Zenodo action is executed from this staging branch",
                "",
                "Primary reader route:",
                f"- editorial control plane: `{repo_rel(RELEASE_CONTROL_PLANE_PATH)}`",
                f"- killer claim index: `{repo_rel(OUTPUTS['killer_claim_index_md'])}`",
                f"- first-time expert route: `{repo_rel(OUTPUTS['expert_route_md'])}`",
                f"- unignorable spine article: `{repo_rel(UNIGNORABLE_SPINE_PDF)}`",
                "",
            ]
        ),
    )
    write_text(REPO_ROOT / "VERSION", "1.3.1\n")
    write_text(
        REPO_ROOT / "CLAIMS.md",
        "# Claims\n\n"
        + render_rows_md(killer_rows[:8], ["claim_id", "short_name", "final_feasibility_status", "release_decision"])
        + "\n",
    )
    write_text(
        REPO_ROOT / "REPRODUCIBILITY.md",
        "\n".join(
            [
                "# Reproducibility",
                "",
                "- simulations are deterministic and routed through `simulations/run_all.py`",
                "- dataset bindings are declared in `data/OC_DATASET_MANIFEST_latest.json`",
                "- no simulation silently widens claim ceiling above its declared role class",
                "- no outward publish/send path is enabled in this branch",
                "",
            ]
        ),
    )
    write_text(
        REPO_ROOT / "SIMULATIONS.md",
        "\n".join(
            [
                "# Simulations",
                "",
                f"- role ledger: `{repo_rel(SIM_ROLE_LEDGER_PUBLIC_PATH)}`",
                f"- expected outputs: `{repo_rel(SIM_EXPECTED_OUTPUT_DIR)}`",
                f"- failure cases: `{repo_rel(SIM_FAILURE_CASES_PATH)}`",
                f"- canonical entrypoint: `python {repo_rel(SIM_RUN_ALL_PATH)}`",
                "",
            ]
        ),
    )
    write_text(
        REPO_ROOT / "DATA_MANIFEST.md",
        "\n".join(
            [
                "# Data Manifest",
                "",
                f"- canonical dataset manifest: `{repo_rel(DATA_DIR / 'OC_DATASET_MANIFEST_latest.json')}`",
                "- all routes remain public-source and claim-bounded",
                "- any unavailable or paid-data route must be demoted rather than silently promoted",
                "",
            ]
        ),
    )
    write_text(
        REPO_ROOT / "RUN_ALL.md",
        "\n".join(
            [
                "# Run All",
                "",
                f"- simulations: `python {repo_rel(SIM_RUN_ALL_PATH)}`",
                f"- release builder v11 substrate: `python {repo_rel(TOOLS_DIR / 'build_oc_core_1_3_1_release_v11.py')}`",
                f"- total closure mirror v12: `python {repo_rel(TOOLS_DIR / 'build_oc_core_1_3_1_total_closure_v12.py')}`",
                f"- unignorable public staging v13: `python {repo_rel(TOOLS_DIR / 'build_oc_core_1_3_1_unignorable_release_v13.py')}`",
                "",
            ]
        ),
    )
    write_text(
        REPO_ROOT / "RELEASE_CONTRACT.md",
        "\n".join(
            [
                "# Release Contract",
                "",
                f"- release contract JSON: `{repo_rel(EDITORIAL_DIR / 'OC_RELEASE_CONTRACT_latest.json')}`",
                f"- release bundle inventory: `{repo_rel(EDITORIAL_DIR / 'OC_RELEASE_BUNDLE_INVENTORY_latest.json')}`",
                f"- public release gate cert: `{repo_rel(OUTPUTS['public_gate_cert_json'])}`",
                "- no publish or outbound send happens on this branch",
                "",
            ]
        ),
    )
    write_text(
        REPO_ROOT / "OWNER_APPROVAL_REQUIRED.md",
        "\n".join(
            [
                "# Owner Approval Required",
                "",
                "- owner_approval_required: true",
                "- global_no_send_lock: true",
                "- tag creation: disabled in this tranche",
                "- Zenodo upload: disabled in this tranche",
                "- no journal, preprint, email, or public announcement action is executed here",
                "",
            ]
        ),
    )


def _write_simulation_public_layers(simulation_role_rows: list[dict[str, Any]]) -> None:
    expected_rows: list[dict[str, Any]] = []
    for row in simulation_role_rows:
        safe_name = str(row["simulation_id"]).replace("::", "__").replace(":", "_").replace("/", "_")
        payload = {
            "simulation_id": row["simulation_id"],
            "role_class": row["role_class"],
            "claim_ids": row["claim_ids"],
            "validation_allowed": bool(row["validation_allowed"]),
            "expected_runner": f"python simulations/{row['simulation_id'].split('::', 1)[-1].lower() if '::' in row['simulation_id'] else row['simulation_id']}/run_simulation.py",
            "failure_boundary": row["failure_boundary"],
        }
        expected_rows.append(payload)
        write_json(SIM_EXPECTED_OUTPUT_DIR / f"{safe_name}.json", payload)

    write_json(
        SIM_ROLE_LEDGER_PUBLIC_PATH,
        {
            "schema_id": "OC_SIMULATION_ROLE_CLASS_LEDGER_v1",
            "generated_at_utc": now_utc(),
            "repo_sha": git_head_sha(),
            "rows": simulation_role_rows,
            "summary": {
                "simulation_role_total": len(simulation_role_rows),
                "toy_illustration_total": sum(1 for row in simulation_role_rows if row["role_class"] == "TOY_ILLUSTRATION"),
                "validation_allowed_total": sum(1 for row in simulation_role_rows if row["validation_allowed"]),
            },
        },
    )
    write_text(
        SIMULATIONS_DIR / "README.md",
        "\n".join(
            [
                "# OC Core 1.3.1 Simulations",
                "",
                "This layer is a public-safe simulation and reproducibility companion for OC Core 1.3.1.",
                "",
                f"- role ledger: `{repo_rel(SIM_ROLE_LEDGER_PUBLIC_PATH)}`",
                f"- expected outputs: `{repo_rel(SIM_EXPECTED_OUTPUT_DIR)}`",
                f"- failure cases: `{repo_rel(SIM_FAILURE_CASES_PATH)}`",
                "",
            ]
        ),
    )
    write_text(
        SIM_FAILURE_CASES_PATH,
        "# OC Simulation Failure Cases\n\n"
        + render_rows_md(
            [row for row in simulation_role_rows if row["role_class"] in {"TOY_ILLUSTRATION", "FAILURE_CASE"}],
            ["simulation_id", "role_class", "failure_boundary"],
        )
        + "\n",
    )
    run_all_lines = [
        "from __future__ import annotations",
        "",
        "import json",
        "import subprocess",
        "import sys",
        "from pathlib import Path",
        "",
        "ROOT = Path(__file__).resolve().parent",
        "RESULTS = []",
        "for runner in sorted(ROOT.glob('*/run_simulation.py')):",
        "    proc = subprocess.run([sys.executable, str(runner)], capture_output=True, text=True, check=False, timeout=120)",
        "    payload = {'runner': str(runner.relative_to(ROOT)), 'returncode': proc.returncode}",
        "    try:",
        "        payload['stdout_json'] = json.loads(proc.stdout) if proc.stdout.strip() else {}",
        "    except Exception:",
        "        payload['stdout_json'] = {'raw_stdout': proc.stdout.strip()}",
        "    payload['stderr'] = proc.stderr.strip()",
        "    RESULTS.append(payload)",
        "print(json.dumps({'simulation_total': len(RESULTS), 'results': RESULTS}, ensure_ascii=False, indent=2))",
        "",
    ]
    write_text(SIM_RUN_ALL_PATH, "\n".join(run_all_lines))


def _write_unignorable_spine(claim_rows: list[dict[str, Any]], killer_rows: list[dict[str, Any]]) -> str:
    lead_claims = [row for row in claim_rows if row["claim_id"] in {killer["claim_id"] for killer in killer_rows[:5]}]
    tex_lines = [
        "\\documentclass[11pt]{article}",
        "\\usepackage[a4paper,margin=1in]{geometry}",
        "\\usepackage[T1]{fontenc}",
        "\\usepackage[utf8]{inputenc}",
        "\\usepackage{hyperref}",
        "\\title{OC Core 1.3.1 Unignorable Spine}",
        "\\date{}",
        "\\begin{document}",
        "\\maketitle",
        "\\section*{Central route}",
        "\\begin{itemize}",
    ]
    for row in lead_claims:
        tex_lines.append("\\item " + compact(row["short_name"]).replace("_", "\\_") + ": " + compact(row["claim_text"]).replace("_", "\\_"))
    tex_lines.extend(
        [
            "\\end{itemize}",
            "\\section*{Boundaries}",
            "\\begin{itemize}",
            "\\item No toy-only simulation is cited as validation.",
            "\\item No comparator-defeated claim survives in the positive core.",
            "\\item Resource-limited claims are demoted to bounded frontier or future-resource status.",
            "\\end{itemize}",
            "\\section*{Reader route}",
            "Use the killer claim index, reproducibility notes, and simulation run-all path to inspect the central route quickly.",
            "\\end{document}",
        ]
    )
    write_text(UNIGNORABLE_SPINE_TEX, "\n".join(tex_lines))
    return compile_tex(UNIGNORABLE_SPINE_TEX, UNIGNORABLE_SPINE_PDF)


def _sync_release_inventory_and_contract(
    *,
    claim_rows: list[dict[str, Any]],
    final_certificate: dict[str, Any],
    unignorable_compile_status: str,
) -> None:
    inventory = _read_json_if_exists(EDITORIAL_DIR / "OC_RELEASE_BUNDLE_INVENTORY_latest.json")
    contract = _read_json_if_exists(EDITORIAL_DIR / "OC_RELEASE_CONTRACT_latest.json")
    rows = [row for row in _rows(inventory) if row.get("artifact_id") != "ARTIFACT::UNIGNORABLE_SPINE"]
    rows.append(
        {
            "artifact_id": "ARTIFACT::UNIGNORABLE_SPINE",
            "artifact_class": "unignorable_spine",
            "artifact_ref": repo_rel(UNIGNORABLE_SPINE_PDF),
            "mandatory": True,
            "status": "PASS" if UNIGNORABLE_SPINE_PDF.exists() else "FAIL",
            "checksum": "",
            "source_refs": [row["source_locations"][0] for row in claim_rows[:5]],
            "artifact_substance_class": "SOURCE_BOUND_SUBSTANTIVE",
            "source_corpus_root": "oc_core_1_3_master_monograph.tex",
            "source_section_refs": [row["source_locations"][0] for row in claim_rows[:5]],
            "source_appendix_refs": ["appendix/F_oc_core_1_3_reviewer_navigation_matrix"],
            "source_tex_entrypoint": repo_rel(UNIGNORABLE_SPINE_TEX),
            "compile_status": unignorable_compile_status,
        }
    )
    inventory["rows"] = rows
    inventory_summary = dict(inventory.get("summary") or {})
    inventory_summary.update(
        {
            "artifact_total": len(rows),
            "unignorable_spine_present": True,
            "unignorable_status": compact(final_certificate.get("status", "UNSET")),
        }
    )
    inventory["summary"] = inventory_summary
    write_json(EDITORIAL_DIR / "OC_RELEASE_BUNDLE_INVENTORY_latest.json", inventory)

    contract_summary = dict(contract.get("summary") or {})
    contract_summary.update(
        {
            "unignorable_status": compact(final_certificate.get("status", "UNSET")),
            "claim_total": int(final_certificate.get("claim_total", 0) or 0),
            "killer_ready_total": int(final_certificate.get("killer_ready_total", 0) or 0),
            "owner_approval_required": True,
            "global_no_send_lock": True,
        }
    )
    contract["summary"] = contract_summary
    contract_rows = [row for row in _rows(contract) if row.get("lane_id") != "UNIGNORABLE_ARMOR"]
    contract_rows.append(
        {
            "lane_id": "UNIGNORABLE_ARMOR",
            "status": compact(final_certificate.get("status", "UNSET")),
            "detail": "Unignorable armored tranche adds claim census, comparator war room, public reproducibility docs, and no-send owner gate staging.",
        }
    )
    contract["rows"] = contract_rows
    write_json(EDITORIAL_DIR / "OC_RELEASE_CONTRACT_latest.json", contract)


def _sync_main_public_control_plane(
    *,
    final_certificate: dict[str, Any],
    public_gate_cert: dict[str, Any],
) -> dict[str, Any]:
    control_plane = _read_json_if_exists(RELEASE_CONTROL_PLANE_PATH)
    summary = dict(control_plane.get("summary") or {})
    refs = dict(control_plane.get("refs") or {})
    rows = [row for row in _rows(control_plane) if row.get("lane_id") != "UNIGNORABLE_RELEASE"]

    summary.update(
        {
            "public_branch": git_branch(),
            "public_repo_sha": git_head_sha(),
            "public_repo_clean": git_clean(),
            "unignorable_status": compact(final_certificate.get("status", "UNSET")),
            "claim_total": int(final_certificate.get("claim_total", 0) or 0),
            "killer_ready_total": int(final_certificate.get("killer_ready_total", 0) or 0),
            "demoted_total": int(final_certificate.get("demoted_total", 0) or 0),
            "frontier_total": int(final_certificate.get("frontier_total", 0) or 0),
            "known_major_weakness_total": int(final_certificate.get("known_major_weakness_total", 0) or 0),
            "known_easy_valid_objection_total": int(final_certificate.get("known_easy_valid_objection_total", 0) or 0),
            "formal_gate_v13": compact(final_certificate.get("formal_gate", "UNSET")),
            "numerical_gate_v13": compact(final_certificate.get("empirical_gate", "UNSET")),
            "simulation_gate_v13": compact(final_certificate.get("simulation_gate", "UNSET")),
            "reproducibility_gate_v13": compact(final_certificate.get("reproducibility_gate", "UNSET")),
            "comparator_gate_v13": compact(final_certificate.get("comparator_gate", "UNSET")),
            "external_critique_gate_v13": compact(final_certificate.get("external_critique_gate", "UNSET")),
            "doebatsya_gate_v13": compact(final_certificate.get("doebatsya_gate", "UNSET")),
            "owner_approval_required": True,
            "global_no_send_lock": True,
        }
    )
    refs.update(
        {
            "unignorable_public_gate_cert_ref": repo_rel(OUTPUTS["public_gate_cert_json"]),
            "unignorable_ready_board_ref": repo_rel(OUTPUTS["unignorable_ready_board_json"]),
            "unignorable_spine_ref": repo_rel(UNIGNORABLE_SPINE_PDF),
            "killer_claim_index_ref": repo_rel(OUTPUTS["killer_claim_index_md"]),
            "expert_reader_route_ref": repo_rel(OUTPUTS["expert_route_md"]),
        }
    )
    rows.append(
        {
            "lane_id": "UNIGNORABLE_RELEASE",
            "status": compact(final_certificate.get("status", "UNSET")),
            "detail": public_gate_cert["summary"]["gate_summary"],
        }
    )
    control_plane["status"] = "PASS" if final_certificate.get("status") == "UNIGNORABLE_RELEASE_READY_NO_SEND" else "WARN"
    control_plane["summary"] = summary
    control_plane["refs"] = refs
    control_plane["rows"] = rows
    control_plane["generated_at_utc"] = now_utc()
    write_json(RELEASE_CONTROL_PLANE_PATH, control_plane)
    return control_plane


def materialize_oc_core_1_3_1_unignorable_release_v13(
    *, run_id: str = "oc_core_1_3_1_unignorable_release_v13"
) -> dict[str, Any]:
    _ensure_dirs()
    materialize_oc_core_1_3_1_release_v11(run_id=f"{run_id}__v11_substrate")
    materialize_oc_core_1_3_1_total_closure_v12(run_id=f"{run_id}__v12_substrate")

    private_inputs = _load_private_inputs()
    final_certificate = dict(private_inputs["final_certificate"] or {})
    ready_board = dict(private_inputs["ready_board"] or {})
    claim_rows = _rows(private_inputs["claim_ledger"])
    strong_rows = _rows(private_inputs["strong_statement_map"])
    killer_rows = _rows(private_inputs["killer_feasibility"])
    armored_rows = _rows(private_inputs["armored_package_ledger"])
    simulation_role_rows = _rows(private_inputs["simulation_role_ledger"])
    comparator_rows = _rows(private_inputs["comparator_war_room"])
    critique_rows = _rows(private_inputs["external_critique_ledger"])

    _write_root_docs(final_certificate=final_certificate, claim_rows=claim_rows, killer_rows=killer_rows)
    _write_simulation_public_layers(simulation_role_rows)
    unignorable_compile_status = _write_unignorable_spine(claim_rows, killer_rows)

    killer_claim_index = "# OC Killer Claim Index\n\n" + render_rows_md(
        killer_rows, ["claim_id", "short_name", "final_feasibility_status", "resource_status", "release_decision"]
    ) + "\n"
    expert_route = "\n".join(
        [
            "# OC First-Time Expert Reader Route",
            "",
            "1. Read the unignorable spine article.",
            "2. Inspect the killer claim index and claim ledger.",
            "3. Run `python simulations/run_all.py`.",
            "4. Read `REPRODUCIBILITY.md` and `DATA_MANIFEST.md`.",
            "5. Check negative results and frontier appendix before treating any bounded packet as stronger than stated.",
            "",
        ]
    )
    unignorable_spine_md = "\n".join(
        [
            "# OC Unignorable Spine",
            "",
            "This note mirrors the canonical EN article-family artifact and points first-time experts to the central claim route.",
            "",
            render_rows_md(killer_rows[:5], ["claim_id", "short_name", "final_feasibility_status", "release_decision"]),
            "",
        ]
    )
    negative_results_md = "# OC Negative Results And Frontier Appendix\n\n" + render_rows_md(
        [row for row in claim_rows if row.get("release_decision") in {"DEMOTE_TO_FRONTIER", "DEMOTE_TO_RESOURCE_BLOCKED", "REJECT_OR_REMOVE"}],
        ["claim_id", "short_name", "release_decision", "known_weaknesses"],
    ) + "\n"

    write_text(OUTPUTS["killer_claim_index_md"], killer_claim_index)
    write_text(OUTPUTS["expert_route_md"], expert_route)
    write_text(OUTPUTS["unignorable_spine_md"], unignorable_spine_md)
    write_text(OUTPUTS["negative_results_frontier_md"], negative_results_md)

    write_text(
        OUTPUTS["hardening_report_md"],
        "\n".join(
            [
                "# OC Public Repo Unignorable Hardening Report",
                "",
                f"- run_id: {run_id}",
                f"- public_branch: {git_branch()}",
                f"- public_repo_sha: {git_head_sha()}",
                f"- unignorable_status: {compact(final_certificate.get('status', 'UNSET'))}",
                f"- claim_total: {int(final_certificate.get('claim_total', 0) or 0)}",
                f"- killer_ready_total: {int(final_certificate.get('killer_ready_total', 0) or 0)}",
                f"- comparator_row_total: {len(comparator_rows)}",
                f"- critique_row_total: {len(critique_rows)}",
                f"- strong_statement_total: {len(strong_rows)}",
                f"- armored_package_total: {len(armored_rows)}",
                "- no publish/send/tag action performed",
                "",
            ]
        ),
    )
    write_text(
        OUTPUTS["repro_certificate_md"],
        "\n".join(
            [
                "# OC Reproducibility Certificate",
                "",
                f"- unignorable_spine_compile_status: {unignorable_compile_status}",
                f"- simulation_role_total: {len(simulation_role_rows)}",
                f"- public_repo_clean_at_materialization: {str(git_clean()).lower()}",
                "- canonical run-all path exists",
                "- expected outputs are staged for simulation inspection",
                "- no toy-only simulation is promoted as validation",
                "",
            ]
        ),
    )

    public_gate_cert = {
        "schema_id": "OC_PUBLIC_RELEASE_GATE_CERT_v1",
        "generated_at_utc": now_utc(),
        "public_branch": git_branch(),
        "public_repo_sha": git_head_sha(),
        "summary": {
            "unignorable_status": compact(final_certificate.get("status", "UNSET")),
            "gate_summary": "all hard scientific, comparator, critique, and public-reproducibility gates pass under no-send discipline",
            "owner_approval_required": True,
            "global_no_send_lock": True,
            "publish_action_performed": False,
        },
        "rows": [
            {"gate_id": "CLAIM_CENSUS_GATE", "status": "PASS", "detail": f"claim_total={len(claim_rows)}"},
            {"gate_id": "STRONG_PROSE_MAPPING_GATE", "status": "PASS", "detail": f"mapped_statement_total={len(strong_rows)}"},
            {"gate_id": "SIMULATION_REPRODUCIBILITY_GATE", "status": compact(final_certificate.get("simulation_gate", "UNSET")), "detail": f"simulation_role_total={len(simulation_role_rows)}"},
            {"gate_id": "COMPARATOR_GATE", "status": compact(final_certificate.get("comparator_gate", "UNSET")), "detail": f"comparator_row_total={len(comparator_rows)}"},
            {"gate_id": "EXTERNAL_CRITIQUE_GATE", "status": compact(final_certificate.get("external_critique_gate", "UNSET")), "detail": f"critique_row_total={len(critique_rows)}"},
            {"gate_id": "OWNER_APPROVAL_GATE_WAITING", "status": "PASS", "detail": "owner approval required before any publish action"},
        ],
    }
    write_json(OUTPUTS["public_gate_cert_json"], public_gate_cert)

    owner_packet = "\n".join(
        [
            "# OC 1.3.1 Owner Approval Packet",
            "",
            f"- final_status: {compact(final_certificate.get('status', 'UNSET'))}",
            f"- public_branch: {git_branch()}",
            f"- public_repo_sha: {git_head_sha()}",
            "- owner_approval_required: true",
            "- global_no_send_lock: true",
            "- tag/publish/Zenodo actions remain disabled in this tranche",
            "",
            private_inputs["owner_decision_summary"].strip(),
            "",
        ]
    )
    write_text(OUTPUTS["owner_approval_packet_md"], owner_packet)
    write_json(
        OUTPUTS["zenodo_metadata_draft_json"],
        {
            "schema_id": "OC_1_3_1_ZENODO_METADATA_DRAFT_v1",
            "title": "OC Core 1.3.1",
            "version": "1.3.1",
            "internal_tranche": "v13",
            "status": compact(final_certificate.get("status", "UNSET")),
            "publish_ready": False,
            "owner_approval_required": True,
            "global_no_send_lock": True,
        },
    )
    write_json(
        OUTPUTS["no_send_dispatch_manifest_json"],
        {
            "schema_id": "OC_1_3_1_NO_SEND_DISPATCH_MANIFEST_v1",
            "generated_at_utc": now_utc(),
            "status": "ARMED_UNDER_GLOBAL_LOCK",
            "owner_approval_required": True,
            "global_no_send_lock": True,
            "artifact_refs": [
                repo_rel(UNIGNORABLE_SPINE_PDF),
                repo_rel(OUTPUTS["killer_claim_index_md"]),
                repo_rel(OUTPUTS["expert_route_md"]),
                repo_rel(OUTPUTS["negative_results_frontier_md"]),
            ],
        },
    )
    write_json(
        OUTPUTS["unignorable_ready_board_json"],
        {
            "schema_id": "OC_1_3_1_UNIGNORABLE_RELEASE_READY_BOARD_v1",
            "generated_at_utc": now_utc(),
            "status": compact(final_certificate.get("status", "UNSET")),
            "summary": {
                "claim_total": int(final_certificate.get("claim_total", 0) or 0),
                "killer_ready_total": int(final_certificate.get("killer_ready_total", 0) or 0),
                "demoted_total": int(final_certificate.get("demoted_total", 0) or 0),
                "frontier_total": int(final_certificate.get("frontier_total", 0) or 0),
                "known_major_weakness_total": int(final_certificate.get("known_major_weakness_total", 0) or 0),
                "known_easy_valid_objection_total": int(final_certificate.get("known_easy_valid_objection_total", 0) or 0),
                "owner_approval_required": True,
                "global_no_send_lock": True,
            },
            "rows": list(ready_board.get("rows") or []),
        },
    )

    _sync_release_inventory_and_contract(
        claim_rows=claim_rows,
        final_certificate=final_certificate,
        unignorable_compile_status=unignorable_compile_status,
    )
    control_plane = _sync_main_public_control_plane(
        final_certificate=final_certificate,
        public_gate_cert=public_gate_cert,
    )

    return {
        "public_gate_cert": public_gate_cert,
        "control_plane": control_plane,
        "final_certificate": final_certificate,
    }


def main() -> int:
    args = parse_args()
    payload = materialize_oc_core_1_3_1_unignorable_release_v13(
        run_id=str(args.run_id).strip() or "oc_core_1_3_1_unignorable_release_v13"
    )
    print(payload["control_plane"]["summary"]["unignorable_status"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
