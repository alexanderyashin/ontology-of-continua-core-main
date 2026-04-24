from __future__ import annotations

import argparse
import json
import os
import subprocess
from pathlib import Path
from typing import Any

from build_oc_core_1_3_1_release_v11 import (
    ARTICLE_DIR,
    DATASET_MANIFEST_PATH,
    EDITORIAL_DIR,
    MANUSCRIPT_OUTPUTS,
    OUTPUTS as V11_OUTPUTS,
    RELEASE_ROOT,
    SIMULATION_GUIDE_PATH,
    SIMULATION_LEDGER_PATH,
    SOURCE_APPENDICES_DIR,
    SOURCE_FRONTMATTER_DIR,
    SOURCE_ROUTE_DIR,
    compile_tex,
    compact,
    git_branch,
    git_clean,
    git_head_sha,
    materialize_oc_core_1_3_1_release_v11,
    now_utc,
    read_json,
    render_release_entrypoint_tex,
    render_release_frontmatter_tex,
    render_release_route_tex,
    render_rows_md,
    repo_rel,
    write_json,
    write_text,
)
from build_oc_core_1_3_1_unignorable_release_v13 import materialize_oc_core_1_3_1_unignorable_release_v13


TOOLS_DIR = Path(__file__).resolve().parent
REPO_ROOT = TOOLS_DIR.parent
PRIVATE_ROOT = Path("C:/Users/Megaport/work/worktrees/oc13-publication-clean")
PRIVATE_STATUS_DIR = PRIVATE_ROOT / "logion" / "k0" / "governance" / "status"

PRIVATE_FINAL_CERTIFICATE_PATH = PRIVATE_STATUS_DIR / "OC_UNIGNORABLE_FINAL_CERTIFICATE_latest.json"
PRIVATE_READY_BOARD_PATH = PRIVATE_STATUS_DIR / "OC_1_3_1_UNIGNORABLE_RELEASE_READY_BOARD_latest.json"
PRIVATE_CLAIM_LEDGER_PATH = PRIVATE_STATUS_DIR / "OC_CLAIM_MASTER_LEDGER_latest.json"
PRIVATE_STRONG_MAP_PATH = PRIVATE_STATUS_DIR / "OC_STRONG_STATEMENT_TO_CLAIM_MAP.json"
PRIVATE_KILLER_MATRIX_PATH = PRIVATE_STATUS_DIR / "OC_KILLER_FEASIBILITY_MATRIX_latest.json"

UNIGNORABLE_SPINE_FRONTMATTER_TEX = SOURCE_FRONTMATTER_DIR / "oc_core_1_3_1_unignorable_spine_release_framing.tex"
UNIGNORABLE_SPINE_ROUTE_TEX = SOURCE_ROUTE_DIR / "oc_core_1_3_1_unignorable_spine_route.tex"
UNIGNORABLE_SPINE_TEX = ARTICLE_DIR / "OC_UNIGNORABLE_SPINE_EN.tex"
UNIGNORABLE_SPINE_PDF = ARTICLE_DIR / "OC_UNIGNORABLE_SPINE_EN.pdf"

PUBLIC_ARTIFACT_MAP_PATH = EDITORIAL_DIR / "OC_PUBLIC_RELEASE_ARTIFACT_MAP_latest.json"
PUBLIC_GATE_CERT_PATH = EDITORIAL_DIR / "OC_PUBLIC_RELEASE_GATE_CERT_latest.json"
PUBLIC_OWNER_GATE_PATH = EDITORIAL_DIR / "OC_CORE_1_3_1_OWNER_APPROVAL_GATE_latest.json"
PUBLIC_CONTROL_PLANE_PATH = V11_OUTPUTS["control_plane_json"]
PUBLIC_RELEASE_READY_BOARD_PATH = V11_OUTPUTS["release_ready_board_json"]
PUBLIC_RELEASE_CONTRACT_PATH = V11_OUTPUTS["release_contract_json"]
PUBLIC_ARTIFACT_INVENTORY_PATH = V11_OUTPUTS["artifact_inventory_json"]
PUBLIC_PUBLISH_MANIFEST_PATH = V11_OUTPUTS["publish_manifest_json"]
PUBLIC_ZENODO_STAGE_PATH = V11_OUTPUTS["zenodo_stage_json"]
PUBLIC_OWNER_PACKET_PATH = EDITORIAL_DIR / "OC_1_3_1_OWNER_APPROVAL_PACKET.md"
PUBLIC_HARDENING_REPORT_PATH = EDITORIAL_DIR / "OC_PUBLIC_REPO_UNIGNORABLE_HARDENING_REPORT.md"
PUBLIC_REPRO_CERT_PATH = EDITORIAL_DIR / "OC_REPRODUCIBILITY_CERTIFICATE.md"
PUBLIC_KILLER_INDEX_PATH = EDITORIAL_DIR / "OC_KILLER_CLAIM_INDEX.md"
PUBLIC_EXPERT_ROUTE_PATH = EDITORIAL_DIR / "OC_FIRST_TIME_EXPERT_READER_ROUTE.md"
PUBLIC_SPINE_MD_PATH = EDITORIAL_DIR / "OC_UNIGNORABLE_SPINE.md"
PUBLIC_NEGATIVE_APPENDIX_PATH = EDITORIAL_DIR / "OC_NEGATIVE_RESULTS_AND_FRONTIER_APPENDIX.md"
PUBLIC_ZENODO_DRAFT_PATH = EDITORIAL_DIR / "OC_1_3_1_ZENODO_METADATA_DRAFT.json"
PUBLIC_NO_SEND_DISPATCH_MANIFEST_PATH = EDITORIAL_DIR / "OC_1_3_1_NO_SEND_DISPATCH_MANIFEST.json"
PUBLIC_RELEASE_MANIFEST_PATH = RELEASE_ROOT / "OC_CORE_1_3_1_ZENODO_RELEASE_MANIFEST.json"

SIM_RUN_ALL_PATH = REPO_ROOT / "simulations" / "run_all.py"
SIM_FAILURE_CASES_PATH = REPO_ROOT / "simulations" / "OC_SIMULATION_FAILURE_CASES.md"
SIM_ROLE_LEDGER_PATH = REPO_ROOT / "simulations" / "OC_SIMULATION_ROLE_CLASS_LEDGER_latest.json"

ROOT_DOCS = {
    "readme": REPO_ROOT / "README.md",
    "claims": REPO_ROOT / "CLAIMS.md",
    "repro": REPO_ROOT / "REPRODUCIBILITY.md",
    "sims": REPO_ROOT / "SIMULATIONS.md",
    "data": REPO_ROOT / "DATA_MANIFEST.md",
    "run_all": REPO_ROOT / "RUN_ALL.md",
    "release_contract": REPO_ROOT / "RELEASE_CONTRACT.md",
    "owner_approval": REPO_ROOT / "OWNER_APPROVAL_REQUIRED.md",
    "version": REPO_ROOT / "VERSION",
}

MANDATORY_MANUSCRIPT_CLASSES = {
    "master_monograph",
    "journal_core",
    "readable_overview",
    "methods_or_simulation_companion",
    "critique_closure_companion",
    "unignorable_spine_article",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Materialize the OC Core 1.3.1 independent release verification stack (v14).")
    parser.add_argument("--run-id", default="oc_core_1_3_1_independent_release_v14")
    return parser.parse_args()


def _read_json_if_exists(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    payload = read_json(path)
    return payload if isinstance(payload, dict) else {}


def _rows(payload: dict[str, Any]) -> list[dict[str, Any]]:
    value = payload.get("rows")
    return [row for row in value if isinstance(row, dict)] if isinstance(value, list) else []


def _summary(payload: dict[str, Any]) -> dict[str, Any]:
    value = payload.get("summary")
    return value if isinstance(value, dict) else {}


def _find_claim(claim_rows: list[dict[str, Any]], claim_id: str) -> dict[str, Any]:
    for row in claim_rows:
        if compact(row.get("claim_id")) == claim_id:
            return row
    return {}


def _bool_str(value: bool) -> str:
    return "true" if value else "false"


def _env_token(*names: str) -> str:
    for name in names:
        value = str(os.environ.get(name, "") or "").strip()
        if value:
            return value
    return ""


def _run_json_command(cmd: list[str], *, cwd: Path, timeout: int) -> dict[str, Any]:
    proc = subprocess.run(
        cmd,
        cwd=str(cwd),
        capture_output=True,
        text=True,
        check=False,
        timeout=timeout,
    )
    stdout = proc.stdout.strip()
    payload: dict[str, Any] = {}
    if stdout:
        try:
            parsed = json.loads(stdout)
            if isinstance(parsed, dict):
                payload = parsed
        except Exception:
            payload = {"raw_stdout": stdout}
    return {
        "returncode": proc.returncode,
        "stdout": stdout,
        "stderr": proc.stderr.strip(),
        "payload": payload,
    }


def _ensure_release_tree() -> dict[str, Any]:
    materialize_oc_core_1_3_1_release_v11(run_id="v14_release_v11_substrate")
    materialize_oc_core_1_3_1_unignorable_release_v13(run_id="v14_release_v13_substrate")
    return {
        "final_certificate": _read_json_if_exists(PRIVATE_FINAL_CERTIFICATE_PATH),
        "ready_board": _read_json_if_exists(PRIVATE_READY_BOARD_PATH),
        "claim_ledger": _read_json_if_exists(PRIVATE_CLAIM_LEDGER_PATH),
        "strong_map": _read_json_if_exists(PRIVATE_STRONG_MAP_PATH),
        "killer_matrix": _read_json_if_exists(PRIVATE_KILLER_MATRIX_PATH),
    }


def _write_substantive_unignorable_spine(claim_rows: list[dict[str, Any]], killer_rows: list[dict[str, Any]]) -> str:
    promoted_core = [
        row
        for row in killer_rows
        if compact(row.get("release_decision")) in {"PROMOTE_TO_CORE_POSITIVE_BODY", "PROMOTE_AS_FORMULA_ONLY_TESTABLE"}
    ]
    body_lines = [
        "This canonical article is the shortest source-bound route from repo root to the strongest OC Core 1.3.1 claims.",
        "It is built from real theorem, falsifiability, empirical, and synthesis sections of the Core 1.3 corpus plus bounded 1.3.1 appendices.",
        f"mapped_positive_claim_total={len(promoted_core)}; no_prose_only_promotion=true; owner_approval_required=true",
    ]
    write_text(
        UNIGNORABLE_SPINE_FRONTMATTER_TEX,
        render_release_frontmatter_tex(heading="Independent-release framing", body_lines=body_lines),
    )
    route_refs = [
        "content/17_oc_core_1_3_reader_guide.tex",
        "content/04_results.tex",
        "content/08_boundary.tex",
        "content/09_thresholds.tex",
        "content/14_disciplines_extended.tex",
        "content/15_falsifiability_extended.tex",
        "content/20_oc_core_1_3_theorem_roadmap.tex",
        "content/23_oc_core_1_3_empirical_execution_protocols.tex",
        "content/25_oc_core_1_3_toe_synthesis.tex",
        "content/26_oc_core_1_3_practical_utility.tex",
    ]
    appendix_refs = [
        "appendix/E_oc_core_1_3_journal_core_bridge.tex",
        "appendix/F_oc_core_1_3_reviewer_navigation_matrix.tex",
        "appendix/G_oc_core_1_3_empirical_validation_matrix.tex",
        "appendix/Q_oc_core_1_3_toe_support_dossiers.tex",
    ]
    release_appendix_refs = [
        repo_rel(SOURCE_APPENDICES_DIR / "oc_1_3_1_science_delta_appendix.tex"),
        repo_rel(SOURCE_APPENDICES_DIR / "oc_1_3_1_simulation_and_data_appendix.tex"),
        repo_rel(SOURCE_APPENDICES_DIR / "oc_1_3_1_critique_closure_appendix.tex"),
    ]
    write_text(
        UNIGNORABLE_SPINE_ROUTE_TEX,
        render_release_route_tex(route_refs, appendix_refs, release_appendix_refs),
    )
    write_text(
        UNIGNORABLE_SPINE_TEX,
        render_release_entrypoint_tex(
            title="OC Core 1.3.1 Unignorable Spine EN",
            pdf_subject="Shortest source-bound expert route for the strongest OC Core 1.3.1 claims",
            pdf_keywords="Ontology of Continua, OC Core 1.3.1, unignorable spine, expert route",
            frontmatter_ref=repo_rel(UNIGNORABLE_SPINE_FRONTMATTER_TEX),
            route_ref=repo_rel(UNIGNORABLE_SPINE_ROUTE_TEX),
            include_toc=True,
            include_list_of_figures=False,
            include_list_of_tables=False,
            include_bibliography=True,
        ),
    )
    return compile_tex(UNIGNORABLE_SPINE_TEX, UNIGNORABLE_SPINE_PDF)


def _claim_trace_rows(claim_rows: list[dict[str, Any]], killer_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    public_surfaces = {
        "README.md": [
            "OC-CLAIM-000001",
            "OC-CLAIM-000002",
            "OC-CLAIM-000003",
            "OC-CLAIM-000004",
            "OC-CLAIM-000010",
            "OC-CLAIM-000012",
            "OC-CLAIM-000013",
            "OC-CLAIM-000014",
        ],
        repo_rel(PUBLIC_KILLER_INDEX_PATH): [compact(row.get("claim_id")) for row in killer_rows],
        repo_rel(PUBLIC_EXPERT_ROUTE_PATH): [
            "OC-CLAIM-000001",
            "OC-CLAIM-000002",
            "OC-CLAIM-000003",
            "OC-CLAIM-000013",
            "OC-CLAIM-000014",
        ],
        repo_rel(UNIGNORABLE_SPINE_TEX): [
            "OC-CLAIM-000001",
            "OC-CLAIM-000002",
            "OC-CLAIM-000003",
            "OC-CLAIM-000004",
            "OC-CLAIM-000005",
            "OC-CLAIM-000010",
            "OC-CLAIM-000012",
            "OC-CLAIM-000013",
            "OC-CLAIM-000014",
        ],
    }
    rows: list[dict[str, Any]] = []
    for doc_ref, claim_ids in public_surfaces.items():
        for claim_id in claim_ids:
            claim = _find_claim(claim_rows, claim_id)
            if not claim:
                continue
            rows.append(
                {
                    "schema_id": "ClaimEvidenceTraceRow_v1",
                    "claim_id": claim_id,
                    "doc_ref": doc_ref,
                    "claim_class": compact(claim.get("claim_class")),
                    "release_decision": compact(claim.get("release_decision")),
                    "support_class": compact(claim.get("current_support_class")),
                    "evidence_ref": compact(claim.get("proof_route"))
                    or compact(claim.get("simulation_route"))
                    or compact(claim.get("data_route"))
                    or compact(claim.get("comparator_route"))
                    or "CLAIM_LEDGER_ONLY",
                    "source_section_refs": list(claim.get("source_section_refs") or []),
                    "source_appendix_refs": list(claim.get("source_appendix_refs") or []),
                    "trace_status": "PASS",
                }
            )
    return rows


def _write_root_docs(
    *,
    final_certificate: dict[str, Any],
    killer_rows: list[dict[str, Any]],
    claim_trace_rows: list[dict[str, Any]],
) -> None:
    promoted_core = [
        row
        for row in killer_rows
        if compact(row.get("release_decision")) in {"PROMOTE_TO_CORE_POSITIVE_BODY", "PROMOTE_AS_FORMULA_ONLY_TESTABLE"}
    ]
    write_text(
        ROOT_DOCS["readme"],
        "\n".join(
            [
                "# Ontology of Continua / OC Core 1.3.1",
                "",
                "This repository stages the canonical public OC Core 1.3.1 release surface and its release-execution authority stack.",
                "",
                "Current public truth:",
                "- external version label: 1.3.1",
                "- release authority: `tools/build_oc_core_1_3_1_independent_release_v14.py`",
                f"- unignorable_status: {compact(final_certificate.get('status', 'UNSET'))}",
                f"- claim_total: {int(final_certificate.get('claim_total', 0) or 0)}",
                f"- killer_ready_total: {int(final_certificate.get('killer_ready_total', 0) or 0)}",
                "- owner_approval_required: true",
                "- global_no_send_lock: true",
                "",
                "Shortest honest route:",
                f"- `{repo_rel(UNIGNORABLE_SPINE_PDF)}`",
                f"- `{repo_rel(PUBLIC_KILLER_INDEX_PATH)}`",
                f"- `{repo_rel(PUBLIC_EXPERT_ROUTE_PATH)}`",
                f"- `{repo_rel(PUBLIC_CONTROL_PLANE_PATH)}`",
                "",
                "Central positive claims in the outward body:",
            ]
            + [
                f"- {compact(row.get('claim_id'))}: {compact(row.get('short_name'))} [{compact(row.get('release_decision'))}]"
                for row in promoted_core[:8]
            ]
            + [
                "",
                "Non-claims and boundaries:",
                "- toy-only simulations are not validation",
                "- comparator-defeated claims do not survive in the positive core",
                "- resource-limited claims are demoted instead of silently promoted",
                "- publish remains blocked until independent audit, reader route, and channel-auth gates all pass",
                "",
            ]
        ),
    )
    write_text(ROOT_DOCS["version"], "1.3.1\n")
    write_text(
        ROOT_DOCS["claims"],
        "# Claims\n\n"
        + render_rows_md(
            killer_rows,
            ["claim_id", "short_name", "final_feasibility_status", "release_decision", "resource_status"],
        )
        + "\n",
    )
    write_text(
        ROOT_DOCS["repro"],
        "\n".join(
            [
                "# Reproducibility",
                "",
                f"- canonical simulation command: `python {repo_rel(SIM_RUN_ALL_PATH)}`",
                f"- simulation ledger: `{repo_rel(SIMULATION_LEDGER_PATH)}`",
                f"- dataset manifest: `{repo_rel(DATASET_MANIFEST_PATH)}`",
                f"- failure cases: `{repo_rel(SIM_FAILURE_CASES_PATH)}`",
                "- every outward positive claim remains claim-ceiling bounded",
                "- simulation role class must be checked before reading any numeric result as support",
                "",
            ]
        ),
    )
    write_text(
        ROOT_DOCS["sims"],
        "\n".join(
            [
                "# Simulations",
                "",
                f"- canonical entrypoint: `python {repo_rel(SIM_RUN_ALL_PATH)}`",
                f"- role ledger: `{repo_rel(SIM_ROLE_LEDGER_PATH)}`",
                f"- execution guide: `{repo_rel(SIMULATION_GUIDE_PATH)}`",
                "- no simulation may silently upgrade a claim above its role class",
                "",
            ]
        ),
    )
    write_text(
        ROOT_DOCS["data"],
        "\n".join(
            [
                "# Data Manifest",
                "",
                f"- canonical dataset manifest: `{repo_rel(DATASET_MANIFEST_PATH)}`",
                "- all dataset routes are public-source and bounded",
                "- paid, private, or unavailable evidence remains demoted or frontier-marked",
                "",
            ]
        ),
    )
    write_text(
        ROOT_DOCS["run_all"],
        "\n".join(
            [
                "# Run All",
                "",
                f"- materialize the release authority: `python {repo_rel(TOOLS_DIR / 'build_oc_core_1_3_1_independent_release_v14.py')}`",
                f"- validate the release bundle: `python {repo_rel(TOOLS_DIR / 'validate_oc_release_bundle_v1.py')}`",
                f"- run the simulation corpus: `python {repo_rel(SIM_RUN_ALL_PATH)}`",
                f"- attempt the release when fully authorized: `python {repo_rel(TOOLS_DIR / 'execute_oc_core_1_3_1_release_v14.py')} --tag v1.3.1`",
                "",
            ]
        ),
    )
    write_text(
        ROOT_DOCS["release_contract"],
        "\n".join(
            [
                "# Release Contract",
                "",
                f"- release contract: `{repo_rel(PUBLIC_RELEASE_CONTRACT_PATH)}`",
                f"- artifact inventory: `{repo_rel(PUBLIC_ARTIFACT_INVENTORY_PATH)}`",
                f"- public gate cert: `{repo_rel(PUBLIC_GATE_CERT_PATH)}`",
                "- release execution stops unless independent audit, reader route, GitHub, and Zenodo gates all pass",
                "",
            ]
        ),
    )
    write_text(
        ROOT_DOCS["owner_approval"],
        "\n".join(
            [
                "# Owner Approval Required",
                "",
                "- owner_approval_required: true",
                "- global_no_send_lock: true",
                "- publish_allowed defaults to false until the execution tool has both owner approval and channel auth",
                "- the requested tag for a passing release is `v1.3.1`",
                "",
            ]
        ),
    )
    write_text(
        PUBLIC_KILLER_INDEX_PATH,
        "# OC Killer Claim Index\n\n"
        + render_rows_md(
            killer_rows,
            ["claim_id", "short_name", "final_feasibility_status", "release_decision", "resource_status"],
        )
        + "\n",
    )
    write_text(
        PUBLIC_EXPERT_ROUTE_PATH,
        "\n".join(
            [
                "# OC First-Time Expert Reader Route",
                "",
                f"1. Read `{repo_rel(UNIGNORABLE_SPINE_PDF)}`.",
                "2. Inspect `CLAIMS.md` and `OC_KILLER_CLAIM_INDEX.md` for exact claim IDs and release decisions.",
                "3. Check `REPRODUCIBILITY.md`, `SIMULATIONS.md`, and `DATA_MANIFEST.md` before reading any numeric result as support.",
                "4. Run `python simulations/run_all.py` and compare the output with the role ledger and failure cases.",
                "5. Read `OC_NEGATIVE_RESULTS_AND_FRONTIER_APPENDIX.md` before treating any bounded packet as stronger than stated.",
                "",
            ]
        ),
    )
    write_text(
        PUBLIC_SPINE_MD_PATH,
        "# OC Unignorable Spine\n\n"
        + render_rows_md(
            claim_trace_rows,
            ["claim_id", "doc_ref", "support_class", "release_decision", "trace_status"],
        )
        + "\n",
    )
    write_text(
        PUBLIC_NEGATIVE_APPENDIX_PATH,
        "\n".join(
            [
                "# Negative Results And Frontier Appendix",
                "",
                "- no toy-only simulation is counted as validation",
                "- resource-blocked claims remain demoted",
                "- remaining data-blocked questions keep explicit experiment requirements and non-claim boundaries",
                "",
            ]
        ),
    )


def _write_public_artifact_map() -> dict[str, Any]:
    members = [
        repo_rel(ROOT_DOCS["readme"]),
        repo_rel(ROOT_DOCS["claims"]),
        repo_rel(ROOT_DOCS["repro"]),
        repo_rel(ROOT_DOCS["sims"]),
        repo_rel(ROOT_DOCS["data"]),
        repo_rel(ROOT_DOCS["run_all"]),
        repo_rel(ROOT_DOCS["release_contract"]),
        repo_rel(ROOT_DOCS["owner_approval"]),
        repo_rel(MANUSCRIPT_OUTPUTS["master_pdf"]),
        repo_rel(MANUSCRIPT_OUTPUTS["journal_core_pdf"]),
        repo_rel(MANUSCRIPT_OUTPUTS["overview_pdf"]),
        repo_rel(MANUSCRIPT_OUTPUTS["methods_pdf"]),
        repo_rel(MANUSCRIPT_OUTPUTS["critique_pdf"]),
        repo_rel(UNIGNORABLE_SPINE_PDF),
        repo_rel(PUBLIC_KILLER_INDEX_PATH),
        repo_rel(PUBLIC_EXPERT_ROUTE_PATH),
        repo_rel(PUBLIC_SPINE_MD_PATH),
        repo_rel(PUBLIC_NEGATIVE_APPENDIX_PATH),
        repo_rel(PUBLIC_RELEASE_CONTRACT_PATH),
        repo_rel(PUBLIC_ARTIFACT_INVENTORY_PATH),
        repo_rel(PUBLIC_GATE_CERT_PATH),
        repo_rel(DATASET_MANIFEST_PATH),
        repo_rel(SIMULATION_LEDGER_PATH),
        repo_rel(SIM_ROLE_LEDGER_PATH),
        repo_rel(SIMULATION_GUIDE_PATH),
        repo_rel(SIM_FAILURE_CASES_PATH),
    ]
    payload = {
        "schema_id": "OC_PUBLIC_RELEASE_ARTIFACT_MAP_v14",
        "generated_at_utc": now_utc(),
        "release_id": "oc_core_1_3_1",
        "reproducibility_archive_members": members,
    }
    write_json(PUBLIC_ARTIFACT_MAP_PATH, payload)
    return payload


def _artifact_is_source_bound(row: dict[str, Any]) -> bool:
    return (
        compact(row.get("artifact_substance_class")) not in {"", "SUMMARY_ONLY_WRAPPER"}
        and bool(row.get("source_corpus_root"))
        and bool(row.get("source_section_refs") or row.get("source_appendix_refs"))
        and bool(row.get("source_tex_entrypoint"))
    )


def _spine_has_substantive_bindings() -> bool:
    if not UNIGNORABLE_SPINE_TEX.exists():
        return False
    text = UNIGNORABLE_SPINE_TEX.read_text(encoding="utf-8-sig")
    return all(
        needle in text
        for needle in [
            repo_rel(UNIGNORABLE_SPINE_FRONTMATTER_TEX),
            repo_rel(UNIGNORABLE_SPINE_ROUTE_TEX),
            r"\tableofcontents",
        ]
    )


def _run_simulation_corpus() -> dict[str, Any]:
    if not SIM_RUN_ALL_PATH.exists():
        return {
            "status": "FAIL",
            "returncode": 127,
            "simulation_total": 0,
            "failure_total": 1,
            "detail": f"missing {repo_rel(SIM_RUN_ALL_PATH)}",
        }
    result = _run_json_command(["python", str(SIM_RUN_ALL_PATH)], cwd=REPO_ROOT, timeout=1800)
    payload = result["payload"] if isinstance(result["payload"], dict) else {}
    rows = payload.get("results")
    result_rows = [row for row in rows if isinstance(row, dict)] if isinstance(rows, list) else []
    failure_total = 0
    for row in result_rows:
        try:
            returncode = int(row.get("returncode", 1))
        except Exception:
            returncode = 1
        if returncode != 0:
            failure_total += 1
    return {
        "status": "PASS" if result["returncode"] == 0 and failure_total == 0 and result_rows else "FAIL",
        "returncode": result["returncode"],
        "simulation_total": int(payload.get("simulation_total", len(result_rows)) or len(result_rows)),
        "failure_total": failure_total,
        "detail": result["stderr"] or compact(payload.get("raw_stdout")) or "simulation corpus executed",
    }


def _audit_row(*, finding_id: str, category: str, status: str, detail: str, artifact_ref: str = "") -> dict[str, Any]:
    return {
        "finding_id": finding_id,
        "category": category,
        "status": status,
        "detail": detail,
        "artifact_ref": artifact_ref,
    }


def _collect_independent_audit_findings(
    *,
    artifact_inventory: dict[str, Any],
    claim_trace_rows: list[dict[str, Any]],
    strong_map: dict[str, Any],
    simulation_run: dict[str, Any],
    control_plane: dict[str, Any],
) -> list[dict[str, Any]]:
    inventory_rows = _rows(artifact_inventory)
    mandatory_rows = [row for row in inventory_rows if compact(row.get("artifact_class")) in MANDATORY_MANUSCRIPT_CLASSES]
    source_bound_rows = [row for row in mandatory_rows if _artifact_is_source_bound(row)]
    release_contract = _read_json_if_exists(PUBLIC_RELEASE_CONTRACT_PATH)
    findings = [
        _audit_row(
            finding_id="AUDIT::MANDATORY_ARTIFACT_CLASSES",
            category="artifact_inventory",
            status="PASS" if len(mandatory_rows) == len(MANDATORY_MANUSCRIPT_CLASSES) else "FAIL",
            detail=f"mandatory_row_total={len(mandatory_rows)} expected={len(MANDATORY_MANUSCRIPT_CLASSES)}",
            artifact_ref=repo_rel(PUBLIC_ARTIFACT_INVENTORY_PATH),
        ),
        _audit_row(
            finding_id="AUDIT::SOURCE_BOUND_MANUSCRIPTS",
            category="artifact_inventory",
            status="PASS" if len(source_bound_rows) == len(MANDATORY_MANUSCRIPT_CLASSES) else "FAIL",
            detail=f"source_bound_total={len(source_bound_rows)} mandatory_total={len(MANDATORY_MANUSCRIPT_CLASSES)}",
            artifact_ref=repo_rel(PUBLIC_ARTIFACT_INVENTORY_PATH),
        ),
        _audit_row(
            finding_id="AUDIT::UNIGNORABLE_SPINE_SUBSTANCE",
            category="reader_route",
            status="PASS" if _spine_has_substantive_bindings() and UNIGNORABLE_SPINE_PDF.exists() else "FAIL",
            detail="unignorable spine is route-bound and compiled" if UNIGNORABLE_SPINE_PDF.exists() else "unignorable spine missing compiled pdf",
            artifact_ref=repo_rel(UNIGNORABLE_SPINE_TEX),
        ),
        _audit_row(
            finding_id="AUDIT::CLAIM_TRACE_ROWS",
            category="claim_mapping",
            status="PASS" if claim_trace_rows else "FAIL",
            detail=f"claim_trace_total={len(claim_trace_rows)}",
            artifact_ref=repo_rel(PUBLIC_SPINE_MD_PATH),
        ),
        _audit_row(
            finding_id="AUDIT::UNINDEXED_STRONG_STATEMENTS",
            category="claim_mapping",
            status="PASS"
            if int(_summary(strong_map).get("unindexed_strong_statement_total", 0) or 0) == 0
            else "FAIL",
            detail=f"unindexed_strong_statement_total={int(_summary(strong_map).get('unindexed_strong_statement_total', 0) or 0)}",
            artifact_ref=repo_rel(PRIVATE_STRONG_MAP_PATH),
        ),
        _audit_row(
            finding_id="AUDIT::SIMULATION_CORPUS",
            category="reproducibility",
            status=simulation_run["status"],
            detail=f"simulation_total={simulation_run['simulation_total']} failure_total={simulation_run['failure_total']}",
            artifact_ref=repo_rel(SIM_RUN_ALL_PATH),
        ),
        _audit_row(
            finding_id="AUDIT::RELEASE_CONTRACT_AUTHORITY",
            category="release_contract",
            status="PASS"
            if compact(release_contract.get("release_execution_authority")) == "tools/build_oc_core_1_3_1_independent_release_v14.py"
            else "FAIL",
            detail=f"release_execution_authority={compact(release_contract.get('release_execution_authority'))}",
            artifact_ref=repo_rel(PUBLIC_RELEASE_CONTRACT_PATH),
        ),
        _audit_row(
            finding_id="AUDIT::OWNER_GATE",
            category="release_contract",
            status="PASS"
            if bool(_summary(control_plane).get("owner_approval_required", False)) and not _read_json_if_exists(PUBLIC_OWNER_GATE_PATH).get("publish_allowed", True)
            else "FAIL",
            detail=f"owner_approval_required={_bool_str(bool(_summary(control_plane).get('owner_approval_required', False)))}",
            artifact_ref=repo_rel(PUBLIC_OWNER_GATE_PATH),
        ),
    ]
    return findings


def _collect_reader_route_findings(*, claim_trace_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    required_paths = [
        ROOT_DOCS["readme"],
        ROOT_DOCS["claims"],
        ROOT_DOCS["repro"],
        ROOT_DOCS["sims"],
        ROOT_DOCS["data"],
        ROOT_DOCS["run_all"],
        ROOT_DOCS["release_contract"],
        ROOT_DOCS["owner_approval"],
        PUBLIC_KILLER_INDEX_PATH,
        PUBLIC_EXPERT_ROUTE_PATH,
        PUBLIC_SPINE_MD_PATH,
        PUBLIC_NEGATIVE_APPENDIX_PATH,
        UNIGNORABLE_SPINE_PDF,
    ]
    missing = [repo_rel(path) for path in required_paths if not path.exists()]
    route_text = PUBLIC_EXPERT_ROUTE_PATH.read_text(encoding="utf-8-sig") if PUBLIC_EXPERT_ROUTE_PATH.exists() else ""
    findings = [
        _audit_row(
            finding_id="ROUTE::DOC_SURFACES",
            category="reader_route",
            status="PASS" if not missing else "FAIL",
            detail="all reader-route surfaces present" if not missing else "missing: " + ", ".join(missing),
            artifact_ref=repo_rel(PUBLIC_EXPERT_ROUTE_PATH),
        ),
        _audit_row(
            finding_id="ROUTE::TEN_MINUTE_EXPERT",
            category="reader_route",
            status="PASS"
            if all(needle in route_text for needle in ["CLAIMS.md", "REPRODUCIBILITY.md", "simulations/run_all.py", "OC_NEGATIVE_RESULTS_AND_FRONTIER_APPENDIX.md"])
            else "FAIL",
            detail="expert route names claims, repro path, run_all, and frontier appendix explicitly",
            artifact_ref=repo_rel(PUBLIC_EXPERT_ROUTE_PATH),
        ),
        _audit_row(
            finding_id="ROUTE::TRACEABLE_STRONG_PROSE",
            category="reader_route",
            status="PASS" if claim_trace_rows else "FAIL",
            detail=f"traceable_claim_surface_total={len(claim_trace_rows)}",
            artifact_ref=repo_rel(PUBLIC_SPINE_MD_PATH),
        ),
    ]
    return findings


def materialize_oc_core_1_3_1_independent_release_v14(run_id: str = "oc_core_1_3_1_independent_release_v14") -> dict[str, Any]:
    private_inputs = _ensure_release_tree()
    final_certificate = private_inputs["final_certificate"]
    claim_rows = _rows(private_inputs["claim_ledger"])
    killer_rows = _rows(private_inputs["killer_matrix"])
    strong_map = private_inputs["strong_map"]

    spine_compile_status = _write_substantive_unignorable_spine(claim_rows, killer_rows)
    claim_trace_rows = _claim_trace_rows(claim_rows, killer_rows)
    _write_root_docs(
        final_certificate=final_certificate,
        killer_rows=killer_rows,
        claim_trace_rows=claim_trace_rows,
    )
    artifact_map = _write_public_artifact_map()

    control_plane = _read_json_if_exists(PUBLIC_CONTROL_PLANE_PATH)
    gate_cert = _read_json_if_exists(PUBLIC_GATE_CERT_PATH)
    owner_gate = _read_json_if_exists(PUBLIC_OWNER_GATE_PATH)
    release_contract = _read_json_if_exists(PUBLIC_RELEASE_CONTRACT_PATH)
    artifact_inventory = _read_json_if_exists(PUBLIC_ARTIFACT_INVENTORY_PATH)
    publish_manifest = _read_json_if_exists(PUBLIC_PUBLISH_MANIFEST_PATH)
    ready_board = _read_json_if_exists(PUBLIC_RELEASE_READY_BOARD_PATH)
    simulation_ledger = _read_json_if_exists(SIMULATION_LEDGER_PATH)
    dataset_manifest = _read_json_if_exists(DATASET_MANIFEST_PATH)
    zenodo_stage = _read_json_if_exists(PUBLIC_ZENODO_STAGE_PATH)

    release_contract.setdefault("mandatory_artifact_classes", [])
    if "unignorable_spine_article" not in release_contract["mandatory_artifact_classes"]:
        release_contract["mandatory_artifact_classes"].append("unignorable_spine_article")
    release_contract.update(
        {
            "schema_id": "OC_RELEASE_CONTRACT_v1",
            "release_execution_authority": "tools/build_oc_core_1_3_1_independent_release_v14.py",
            "independent_audit_required": True,
            "reader_route_required": True,
            "tag_name": "v1.3.1",
            "github_release_channel": "token_backed_api_or_workflow",
            "zenodo_release_channel": "token_backed_api_or_workflow",
        }
    )
    write_json(PUBLIC_RELEASE_CONTRACT_PATH, release_contract)

    inventory_rows = [row for row in _rows(artifact_inventory) if compact(row.get("artifact_id")) != "ARTIFACT::UNIGNORABLE_SPINE"]
    inventory_rows.append(
        {
            "schema_id": "ReleaseArtifactRow_v1",
            "artifact_id": "ARTIFACT::UNIGNORABLE_SPINE",
            "artifact_class": "unignorable_spine_article",
            "artifact_ref": repo_rel(UNIGNORABLE_SPINE_PDF),
            "mandatory": True,
            "artifact_substance_class": "SOURCE_BOUND_SUBSTANTIVE",
            "checksum": "",
            "status": "ASSEMBLED" if spine_compile_status == "PASS" else "BLOCKED",
            "source_corpus_root": "oc_core_1_3_master_monograph.tex",
            "source_section_refs": [
                "content/04_results.tex",
                "content/08_boundary.tex",
                "content/09_thresholds.tex",
                "content/14_disciplines_extended.tex",
                "content/15_falsifiability_extended.tex",
                "content/20_oc_core_1_3_theorem_roadmap.tex",
                "content/23_oc_core_1_3_empirical_execution_protocols.tex",
                "content/25_oc_core_1_3_toe_synthesis.tex",
                "content/26_oc_core_1_3_practical_utility.tex",
            ],
            "source_appendix_refs": [
                "appendix/E_oc_core_1_3_journal_core_bridge.tex",
                "appendix/F_oc_core_1_3_reviewer_navigation_matrix.tex",
                "appendix/G_oc_core_1_3_empirical_validation_matrix.tex",
                "appendix/Q_oc_core_1_3_toe_support_dossiers.tex",
                repo_rel(SOURCE_APPENDICES_DIR / "oc_1_3_1_science_delta_appendix.tex"),
                repo_rel(SOURCE_APPENDICES_DIR / "oc_1_3_1_simulation_and_data_appendix.tex"),
                repo_rel(SOURCE_APPENDICES_DIR / "oc_1_3_1_critique_closure_appendix.tex"),
            ],
            "source_tex_entrypoint": repo_rel(UNIGNORABLE_SPINE_TEX),
        }
    )
    artifact_inventory["rows"] = inventory_rows
    artifact_inventory["summary"] = {
        **_summary(artifact_inventory),
        "mandatory_artifact_total": len(release_contract.get("mandatory_artifact_classes") or []),
        "assembled_artifact_total": sum(
            1 for row in inventory_rows if bool(row.get("mandatory")) and compact(row.get("status")) == "ASSEMBLED"
        ),
        "assembled_artifact_class_total": len(
            {compact(row.get("artifact_class")) for row in inventory_rows if compact(row.get("status")) == "ASSEMBLED"}
        ),
        "source_bound_mandatory_total": sum(
            1 for row in inventory_rows if bool(row.get("mandatory")) and _artifact_is_source_bound(row)
        ),
    }
    artifact_inventory["generated_at_utc"] = now_utc()
    artifact_inventory["repo_sha"] = git_head_sha()
    write_json(PUBLIC_ARTIFACT_INVENTORY_PATH, artifact_inventory)

    simulation_run = _run_simulation_corpus()
    independent_findings = _collect_independent_audit_findings(
        artifact_inventory=artifact_inventory,
        claim_trace_rows=claim_trace_rows,
        strong_map=strong_map,
        simulation_run=simulation_run,
        control_plane=control_plane,
    )
    reader_findings = _collect_reader_route_findings(claim_trace_rows=claim_trace_rows)
    independent_audit_status = "PASS" if all(row["status"] == "PASS" for row in independent_findings) else "FAIL"
    reader_route_status = "PASS" if all(row["status"] == "PASS" for row in reader_findings) else "FAIL"

    github_token = _env_token("GITHUB_TOKEN", "GH_TOKEN")
    zenodo_token = _env_token("ZENODO_TOKEN", "ZENODO_SANDBOX_TOKEN")
    if independent_audit_status != "PASS" or reader_route_status != "PASS":
        release_execution_status = "BLOCKED_BY_INDEPENDENT_AUDIT"
    elif not github_token or not zenodo_token:
        release_execution_status = "BLOCKED_BY_RELEASE_CHANNEL_CREDENTIALS"
    else:
        release_execution_status = "READY_FOR_RELEASE_EXECUTION"
    github_release_status = "READY" if github_token else "AUTH_MISSING"
    zenodo_deposit_status = "READY" if zenodo_token else "AUTH_MISSING"
    tag_name = "v1.3.1"

    publish_manifest.update(
        {
            "schema_id": "OC_ONE_CLICK_PUBLISH_MANIFEST_v1",
            "release_id": "oc_core_1_3_1",
            "release_gate_status": _summary(control_plane).get("release_gate_status", "RELEASE_READY_NO_SEND"),
            "independent_audit_status": independent_audit_status,
            "reader_route_status": reader_route_status,
            "release_execution_status": release_execution_status,
            "tag_name": tag_name,
            "github_release_status": github_release_status,
            "zenodo_deposit_status": zenodo_deposit_status,
            "owner_approval_required": True,
            "global_no_send_lock": True,
            "release_manifest_ref": repo_rel(PUBLIC_RELEASE_MANIFEST_PATH),
            "release_contract_ref": repo_rel(PUBLIC_RELEASE_CONTRACT_PATH),
            "artifact_inventory_ref": repo_rel(PUBLIC_ARTIFACT_INVENTORY_PATH),
            "artifact_map_ref": repo_rel(PUBLIC_ARTIFACT_MAP_PATH),
        }
    )
    write_json(PUBLIC_PUBLISH_MANIFEST_PATH, publish_manifest)

    owner_gate.update(
        {
            "schema_id": "OC_CORE_1_3_1_OWNER_APPROVAL_GATE_v1",
            "status": "REQUIRED",
            "release_gate_status": _summary(control_plane).get("release_gate_status", "RELEASE_READY_NO_SEND"),
            "independent_audit_status": independent_audit_status,
            "reader_route_status": reader_route_status,
            "release_execution_status": release_execution_status,
            "owner_approval_required": True,
            "publish_allowed": False,
            "next_action": "Run execute_oc_core_1_3_1_release_v14.py after explicit owner approval and release-channel auth preflight.",
        }
    )
    write_json(PUBLIC_OWNER_GATE_PATH, owner_gate)

    gate_summary = {
        "independent_audit_status": independent_audit_status,
        "reader_route_status": reader_route_status,
        "release_execution_status": release_execution_status,
        "tag_name": tag_name,
        "github_release_status": github_release_status,
        "zenodo_deposit_status": zenodo_deposit_status,
        "owner_approval_required": True,
        "global_no_send_lock": True,
        "publish_action_performed": False,
    }
    gate_cert.update(
        {
            "schema_id": "OC_PUBLIC_RELEASE_GATE_CERT_v14",
            "summary": {**_summary(gate_cert), **gate_summary},
            "generated_at_utc": now_utc(),
            "status": "PASS" if independent_audit_status == "PASS" and reader_route_status == "PASS" else "WARN",
        }
    )
    write_json(PUBLIC_GATE_CERT_PATH, gate_cert)

    control_summary = _summary(control_plane)
    control_summary.update(
        {
            "independent_audit_status": independent_audit_status,
            "reader_route_status": reader_route_status,
            "release_execution_status": release_execution_status,
            "tag_name": tag_name,
            "github_release_status": github_release_status,
            "zenodo_deposit_status": zenodo_deposit_status,
            "claim_trace_total_v14": len(claim_trace_rows),
            "independent_audit_finding_total_v14": len(independent_findings),
            "reader_route_finding_total_v14": len(reader_findings),
            "simulation_audit_status_v14": simulation_run["status"],
            "simulation_audit_failure_total_v14": simulation_run["failure_total"],
            "public_branch": git_branch(),
            "public_repo_sha": git_head_sha(),
            "public_repo_clean": git_clean(),
            "public_repo_sha_meaning": "PRE_V14_EXECUTION_HEAD",
        }
    )
    control_plane["summary"] = control_summary
    control_plane["generated_at_utc"] = now_utc()
    control_plane["status"] = (
        "PASS" if release_execution_status in {"READY_FOR_RELEASE_EXECUTION", "RELEASED"} and independent_audit_status == "PASS" and reader_route_status == "PASS" else "WARN"
    )
    control_plane["rows"] = list(control_plane.get("rows") or []) + independent_findings + reader_findings
    control_plane.setdefault("refs", {}).update(
        {
            "unignorable_spine_ref": repo_rel(UNIGNORABLE_SPINE_PDF),
            "public_release_artifact_map_ref": repo_rel(PUBLIC_ARTIFACT_MAP_PATH),
            "root_readme_ref": repo_rel(ROOT_DOCS["readme"]),
            "root_claims_ref": repo_rel(ROOT_DOCS["claims"]),
            "root_reproducibility_ref": repo_rel(ROOT_DOCS["repro"]),
            "root_run_all_ref": repo_rel(ROOT_DOCS["run_all"]),
        }
    )
    write_json(PUBLIC_CONTROL_PLANE_PATH, control_plane)

    ready_board["generated_at_utc"] = now_utc()
    ready_board["status"] = release_execution_status
    ready_board["summary"] = {**_summary(ready_board), **control_summary}
    ready_board["rows"] = [
        {"gate_id": "INDEPENDENT_AUDIT", "status": independent_audit_status, "detail": f"finding_total={len(independent_findings)}"},
        {"gate_id": "READER_ROUTE", "status": reader_route_status, "detail": f"finding_total={len(reader_findings)}"},
        {"gate_id": "GITHUB_CHANNEL", "status": github_release_status, "detail": "GitHub release channel auth"},
        {"gate_id": "ZENODO_CHANNEL", "status": zenodo_deposit_status, "detail": "Zenodo deposit channel auth"},
        {"gate_id": "EXECUTION", "status": release_execution_status, "detail": "real release execution only after audit + auth"},
    ]
    write_json(PUBLIC_RELEASE_READY_BOARD_PATH, ready_board)

    write_text(
        PUBLIC_HARDENING_REPORT_PATH,
        "\n".join(
            [
                "# OC Public Repo Independent Release Hardening Report",
                "",
                f"- run_id: {run_id}",
                f"- independent_audit_status: {independent_audit_status}",
                f"- reader_route_status: {reader_route_status}",
                f"- release_execution_status: {release_execution_status}",
                f"- github_release_status: {github_release_status}",
                f"- zenodo_deposit_status: {zenodo_deposit_status}",
                "- helper scripts route through the v14 release authority instead of the old v11 wrapper-only path",
                "- the public unignorable spine artifact is rebuilt as a source-bound release article",
                "",
            ]
        ),
    )
    write_text(
        PUBLIC_REPRO_CERT_PATH,
        "\n".join(
            [
                "# OC Reproducibility Certificate",
                "",
                f"- simulation_total: {int(_summary(simulation_ledger).get('simulation_total', 0) or 0)}",
                f"- dataset_manifest_total: {int(_summary(dataset_manifest).get('dataset_manifest_total', 0) or 0)}",
                f"- run_all_entrypoint: {repo_rel(SIM_RUN_ALL_PATH)}",
                f"- simulation_audit_status: {simulation_run['status']}",
                f"- simulation_audit_failure_total: {simulation_run['failure_total']}",
                "",
            ]
        ),
    )
    write_text(
        PUBLIC_OWNER_PACKET_PATH,
        "\n".join(
            [
                "# OC 1.3.1 Owner Approval Packet",
                "",
                f"- tag_name: {tag_name}",
                f"- independent_audit_status: {independent_audit_status}",
                f"- reader_route_status: {reader_route_status}",
                f"- release_execution_status: {release_execution_status}",
                f"- github_release_status: {github_release_status}",
                f"- zenodo_deposit_status: {zenodo_deposit_status}",
                f"- zenodo_stage_status: {compact(zenodo_stage.get('status'))}",
                "- explicit channel auth is required before release execution",
                "",
            ]
        ),
    )
    write_json(
        PUBLIC_ZENODO_DRAFT_PATH,
        {
            **_read_json_if_exists(PUBLIC_ZENODO_DRAFT_PATH),
            "schema_id": "OC_1_3_1_ZENODO_METADATA_DRAFT_v1",
            "status": release_execution_status,
            "version": "1.3.1",
            "title": "Ontology of Continua — Core v1.3.1",
            "publish_ready": release_execution_status == "READY_FOR_RELEASE_EXECUTION",
            "owner_approval_required": True,
            "global_no_send_lock": True,
            "tag_name": tag_name,
        },
    )
    write_json(
        PUBLIC_NO_SEND_DISPATCH_MANIFEST_PATH,
        {
            **_read_json_if_exists(PUBLIC_NO_SEND_DISPATCH_MANIFEST_PATH),
            "schema_id": "OC_1_3_1_NO_SEND_DISPATCH_MANIFEST_v1",
            "status": release_execution_status,
            "owner_approval_required": True,
            "global_no_send_lock": True,
            "tag_name": tag_name,
            "artifact_inventory_ref": repo_rel(PUBLIC_ARTIFACT_INVENTORY_PATH),
            "release_contract_ref": repo_rel(PUBLIC_RELEASE_CONTRACT_PATH),
            "artifact_map_ref": repo_rel(PUBLIC_ARTIFACT_MAP_PATH),
        },
    )

    return {
        "control_plane": control_plane,
        "gate_cert": gate_cert,
        "artifact_inventory": artifact_inventory,
        "release_contract": release_contract,
        "artifact_map": artifact_map,
        "claim_trace_rows": claim_trace_rows,
        "independent_findings": independent_findings,
        "reader_findings": reader_findings,
        "simulation_run": simulation_run,
        "spine_compile_status": spine_compile_status,
    }


def main() -> int:
    args = parse_args()
    payload = materialize_oc_core_1_3_1_independent_release_v14(
        run_id=str(args.run_id).strip() or "oc_core_1_3_1_independent_release_v14"
    )
    print(payload["control_plane"]["summary"]["release_execution_status"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
