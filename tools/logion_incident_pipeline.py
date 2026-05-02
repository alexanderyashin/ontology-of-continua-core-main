from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import time
from pathlib import Path
from typing import Any

from pypdf import PdfReader


ROOT = Path(__file__).resolve().parents[1]
INCIDENT_ID = "INC_OC133_PUBLIC_RELEASE_MONOGRAPH_SURROGATE_20260501"
INCIDENT_ROOT = ROOT / "operations" / "incidents" / INCIDENT_ID
RELEASE_ID = "oc_core_1_3_3"
VERSION = "1.3.3"
ESCALATION_MATRIX_REF = "operations/project_control/LOGION_ESCALATION_MATRIX.json"
INCIDENT_QUEUE_REF = "operations/project_control/LOGION_INCIDENT_QUEUE.json"
GITHUB_RELEASE_URL = "https://github.com/alexanderyashin/ontology-of-continua-core-main/releases/tag/v1.3.3"
FALLBACK_ZENODO_RECORD_URL = "https://zenodo.org/records/19957779"
FALLBACK_ZENODO_DOI = "10.5281/zenodo.19957779"


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def read_json(path: Path, default: Any | None = None) -> Any:
    if not path.exists():
        return {} if default is None else default
    return json.loads(read_text(path))


def write_text_if_changed(path: Path, text: str) -> bool:
    path.parent.mkdir(parents=True, exist_ok=True)
    normalized = text.rstrip() + "\n"
    if path.exists() and read_text(path) == normalized:
        return False
    path.write_text(normalized, encoding="utf-8", newline="\n")
    return True


def write_json_if_changed(path: Path, payload: Any) -> bool:
    return write_text_if_changed(path, json.dumps(payload, ensure_ascii=False, indent=2))


def sha256_file(path: Path) -> str | None:
    if not path.is_file():
        return None
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def pdf_stats(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"exists": False, "pages": 0, "text_chars": 0, "sha256": None, "size_bytes": 0}
    reader = PdfReader(str(path))
    text = "\n".join(page.extract_text() or "" for page in reader.pages)
    return {
        "exists": True,
        "pages": len(reader.pages),
        "text_chars": len(text),
        "sha256": sha256_file(path),
        "size_bytes": path.stat().st_size,
        "dedication_present": "Dedicated to my dear wife Maria" in text,
        "science_delta_present": all(anchor in text for anchor in ["T133-K0-RES", "Lean", "finite-model", "target-blind", "Cerberus"]),
        "stale_132_present": any(token in text for token in ["v1.3.2", "version 1.3.2", "oc_core_1_3_2"]),
    }


def run_command(args: list[str], *, timeout: int = 600) -> dict[str, Any]:
    started = time.time()
    completed = subprocess.run(
        args,
        cwd=ROOT,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        timeout=timeout,
    )
    return {
        "command": args,
        "returncode": completed.returncode,
        "ok": completed.returncode == 0,
        "elapsed_seconds": round(time.time() - started, 3),
        "stdout_tail": completed.stdout[-4000:],
        "stderr_tail": completed.stderr[-4000:],
    }


def public_release_approval_mode() -> bool:
    manifest = read_json(ROOT / "releases" / RELEASE_ID / "editorial" / "OC_CORE_1_3_3_PUBLISH_MANIFEST_DRAFT.json", {})
    return (
        manifest.get("owner_approved") is True
        and manifest.get("publish_allowed") is True
        and manifest.get("github_release_allowed") is True
        and manifest.get("zenodo_deposit_allowed") is True
        and manifest.get("journal_submissions_allowed") is False
        and manifest.get("software_heritage_deposit_allowed") is False
    )


def publication_context() -> dict[str, str]:
    editorial = ROOT / "releases" / RELEASE_ID / "editorial"
    draft = read_json(editorial / f"ZENODO_REPLACEMENT_DRAFT_{VERSION}_latest.json", {})
    presentation = read_json(editorial / f"PUBLIC_RELEASE_PRESENTATION_{VERSION}_latest.json", {})
    approval = read_json(editorial / f"OWNER_RELEASE_APPROVAL_v{VERSION}.json", {})
    draft_record = str(draft.get("draft_record_id") or draft.get("draft_id") or "").strip()
    draft_doi = str(draft.get("reserved_doi") or "").strip()
    record_url = (
        f"https://zenodo.org/records/{draft_record}"
        if draft_record
        else str(presentation.get("zenodo_record_url") or approval.get("zenodo_record_url") or FALLBACK_ZENODO_RECORD_URL)
    )
    doi = draft_doi or str(presentation.get("zenodo_doi") or approval.get("zenodo_doi") or FALLBACK_ZENODO_DOI)
    return {"zenodo_record_url": record_url, "zenodo_doi": doi, "github_release_url": GITHUB_RELEASE_URL}


def owner_release_authorization_granted() -> bool:
    grant = read_json(ROOT / "releases" / RELEASE_ID / "editorial" / "OWNER_APPROVAL_GRANTED_1.3.3.json", {})
    approval = grant.get("approval", {}) if isinstance(grant, dict) else {}
    return (
        approval.get("owner_approved") is True
        and approval.get("publish_allowed") is True
        and approval.get("github_release_allowed") is True
        and approval.get("zenodo_deposit_allowed") is True
        and approval.get("journal_submissions_allowed") is False
        and approval.get("software_heritage_deposit_allowed") is False
    )


def build_self_repair_contract() -> dict[str, Any]:
    ctx = publication_context()
    return {
        "schema_id": "LOGION_ARCHITECTURE_SELF_REPAIR_CONTRACT_v1",
        "incident_id": INCIDENT_ID,
        "authority_chain": [
            "Safety Directive",
            "LOGI",
            "K6 Strategy HQ",
            "Service Router",
            "Owning Service Director",
            "Service Executor",
        ],
        "operating_policy": {
            "codex_role": "external_controller_auditor_only",
            "manual_science_patch_allowed": False,
            "manual_release_patch_allowed": False,
            "safe_executor_required": True,
            "write_scope": "repository-local tracked architecture, generation, audit, and release artifacts only",
            "service_architecture_rule": (
                "Incident management coordinates containment/RCA only. Research, editorial, verification, "
                "release engineering, publication records, and governance remain independent services connected by router contracts."
            ),
            "space_separation_rule": (
                "Development, verification, and release spaces are separate logical spaces. "
                "Source rebinding happens in verification space; owner-approved publication controls are then "
                "re-applied as an explicit release-space migration, never by editing product artifacts directly."
            ),
        },
        "repair_classes": [
            {
                "repair_class_id": "SERVICE_ARCHITECTURE_ROUTER",
                "detects": [
                    "incident pipeline absorbs editorial/research/release responsibilities",
                    "case-specific repair path masquerades as a permanent Logion service",
                    "signal has no independent service owner and downstream contracts",
                ],
                "owner_capability": "ServiceArchitecture/Router",
                "executor": "tools/logion_service_architecture.py",
                "safe_commands": [
                    "python -m release_machine services --write --check"
                ],
                "closure_evidence": [
                    "LOGION_SERVICE_REGISTRY.json contains independent services",
                    "LOGION_SERVICE_ROUTER.json routes bad_public_release_record to incident_management and downstream services",
                    "incident_management and editorial_manuscript are distinct service ids",
                ],
            },
            {
                "repair_class_id": "SOURCE_CERTIFICATE_REBIND",
                "detects": [
                    "release-critical automation source changed after Lean/finite certificate was generated",
                    "finite runner source manifest mismatch",
                    "template/materializer changed and generated runner must be rebound",
                ],
                "owner_capability": "IT/ReleaseAutomation",
                "executor": "tools/materialize_oc_core_1_3_3_v12_closure.py",
                "safe_commands": [
                    "python tools/materialize_oc_core_1_3_3_v12_closure.py"
                ],
                "closure_evidence": [
                    "LEAN_BUILD_CERTIFICATE_1_3_3.json::clean_source_manifest_sha256=current",
                    "FINITE_MODEL_CHECKS_1_3_3.json::certificate_binding_failure_total=0",
                ],
            },
            {
                "repair_class_id": "SCIENCE_TO_MANUSCRIPT_PROJECTION",
                "detects": [
                    "master monograph too small",
                    "master monograph generated from route/control Markdown",
                    "promoted 1.3.3 science absent from corpus ledger",
                ],
                "owner_capability": "Research/ManuscriptIntegration",
                "executor": "release_machine.science_monolith",
                "safe_commands": [
                    "python -m release_machine science-monolith --release-id oc_core_1_3_3 --check"
                ],
                "closure_evidence": [
                    "SCIENCE_MONOLITH_AUDIT_1_3_3_latest.json::state=PASS",
                    "SCIENCE_MONOLITH_CORPUS_LEDGER_1_3_3_latest.json::missing_total=0",
                ],
            },
            {
                "repair_class_id": "PUBLIC_PAYLOAD_ROLE_SEMANTICS",
                "detects": [
                    "control sheet occupies primary scientific role",
                    "metadata/checksum wall is first public experience",
                    "public package contains no-send contradiction",
                ],
                "owner_capability": "IT/ReleaseAutomation",
                "executor": "tools/oc133_public_release_payload.py",
                "safe_commands": [
                    f"python -m release_machine public-payload --release-id oc_core_1_3_3 --doi {ctx['zenodo_doi']} --zenodo-record-url {ctx['zenodo_record_url']} --github-release-url {ctx['github_release_url']}",
                    "python -m release_machine public-payload --release-id oc_core_1_3_3 --check"
                ],
                "closure_evidence": [
                    "PUBLIC_PAYLOAD_SUITABILITY_1.3.3_latest.json::state=PASS",
                    "PUBLIC_PAYLOAD_SUITABILITY_1.3.3_latest.json::science_monolith_audit.state=PASS",
                ],
            },
            {
                "repair_class_id": "RELEASE_SPACE_SEPARATION",
                "detects": [
                    "verification control language leaks into public release artifacts",
                    "root public metadata is used as a verification/no-outbound control surface",
                    "development, verification, and release outputs are regenerated by the same write step",
                ],
                "owner_capability": "IT/ReleaseAutomation",
                "executor": "tools/logion_release_spaces.py",
                "safe_commands": [
                    "python -m release_machine release-spaces --release-id oc_core_1_3_3 --repair --write --check"
                ],
                "closure_evidence": [
                    "LOGION_RELEASE_SPACE_AUDIT.json::state=PASS",
                    "LOGION_RELEASE_SPACE_AUDIT.json::control_language_hit_total=0",
                    "root manifest is PUBLIC_GITHUB_ZENODO_RELEASE",
                ],
            },
            {
                "repair_class_id": "FUNCTION_PRODUCT_SEPARATION",
                "detects": [
                    "stable Logion function definition contains product-specific outcome details",
                    "production line is confused with one concrete release",
                    "repair line absorbs normal editorial or research production work",
                ],
                "owner_capability": "ServiceArchitecture/Router",
                "executor": "tools/logion_function_product_separation.py",
                "safe_commands": [
                    "python -m release_machine function-product --write --check"
                ],
                "closure_evidence": [
                    "LOGION_FUNCTION_PRODUCT_SEPARATION_AUDIT.json::state=PASS",
                    "function_registry_product_token_hit_total=0",
                    "production_line_product_token_hit_total=0",
                    "product outcome ledger contains OC Core 1.3.3 as product_layer",
                ],
            },
            {
                "repair_class_id": "APPROVAL_MODE_CONTRACT",
                "detects": [
                    "no-send semantic gate blocks owner-approved GitHub/Zenodo replacement",
                    "owner audit requires public scope before owner approval",
                    "publication path mutates scientific baseline unexpectedly",
                ],
                "owner_capability": "IT/ReleaseAutomation",
                "executor": "finite-runner approval-mode policy plus personal release audit scope policy",
                "safe_commands": [
                    "python tools/materialize_oc_core_1_3_3_v12_closure.py",
                    "python -m release_machine owner-approve --release-id oc_core_1_3_3 --owner-identity Alexander Yashin",
                    "python proofs/finite_model_checks/run_finite_model_checks.py",
                    "python tools/oc133_personal_release_audit.py",
                ],
                "closure_evidence": [
                    "ARCHITECTURE_SELF_REPAIR_EXECUTION.json::mode_transition_policy=APPROVED_PUBLIC_RELEASE_REBIND_AND_REAPPLY_APPROVAL",
                    "FINITE_MODEL_CHECKS_1_3_3.json::failure_total=0",
                    "OC_CORE_1_3_3_PERSONAL_RELEASE_AUDIT_latest.json::blocker_total=0",
                ],
            },
            {
                "repair_class_id": "PUBLIC_RECORD_REPLACEMENT",
                "detects": [
                    "GitHub/Zenodo public record has wrong files",
                    "Zenodo description leaks raw Markdown",
                    "published record uses old DOI or inherited draft files",
                ],
                "owner_capability": "Publication/PublicRecords",
                "executor": "release_machine.publish-replace",
                "safe_commands": [
                    "python -m release_machine publication-replacement-draft --release-id oc_core_1_3_3",
                    "python -m release_machine publish-replace --release-id oc_core_1_3_3",
                    "python -m release_machine postflight --release oc_core_1_3_3",
                ],
                "closure_evidence": [
                    "PUBLIC_RELEASE_EXECUTION_REPORT_v1.3.3.json::state=PASS",
                    "GitHub v1.3.3 asset set equals expected set",
                    "Zenodo newest record asset set equals expected set",
                ],
            },
        ],
        "auto_escalation_rule": (
            "If any repair class has no deterministic safe executor, Strategy HQ must create an IT work order "
            "before Codex or any external controller edits scientific/release artifacts directly."
        ),
    }


def run_self_repair_contract() -> dict[str, Any]:
    contract = build_self_repair_contract()
    active_approved_mode = public_release_approval_mode()
    durable_release_authorization = owner_release_authorization_granted()
    approved_mode = active_approved_mode or durable_release_authorization
    ctx = publication_context()
    commands: list[tuple[str, list[str], int]] = []
    mode_transition_policy = (
        "APPROVED_PUBLIC_RELEASE_REBIND_AND_REAPPLY_APPROVAL"
        if approved_mode
        else "VERIFICATION_SPACE_REBIND_BEFORE_OWNER_APPROVAL"
    )
    commands.append(
        (
            "SERVICE_ARCHITECTURE_ROUTER",
            ["python", "-m", "release_machine", "services", "--write", "--check"],
            300,
        )
    )
    commands.append(
        (
            "SOURCE_CERTIFICATE_REBIND",
            ["python", "tools/materialize_oc_core_1_3_3_v12_closure.py"],
            1200,
        )
    )
    commands.append(
        (
            "VERIFICATION_SPACE_FINITE_SEMANTICS",
            ["python", "proofs/finite_model_checks/run_finite_model_checks.py"],
            600,
        )
    )
    if not approved_mode:
        commands.append(
            (
                "REVIEW_SCORECARD_PRE_APPROVAL",
                ["python", "-m", "release_machine", "evaluate", "--release", RELEASE_ID, "--channel", "all", "--mode", "dry-run"],
                900,
            )
        )
    commands.extend([
        (
            "SCIENCE_TO_MANUSCRIPT_PROJECTION",
            ["python", "-m", "release_machine", "science-monolith", "--release-id", RELEASE_ID, "--check"],
            900,
        ),
        (
            "PUBLIC_PAYLOAD_MATERIALIZE",
            [
                "python",
                "-m",
                "release_machine",
                "public-payload",
                "--release-id",
                RELEASE_ID,
                "--doi",
                ctx["zenodo_doi"],
                "--zenodo-record-url",
                ctx["zenodo_record_url"],
                "--github-release-url",
                ctx["github_release_url"],
            ],
            1200,
        ),
        (
            "PUBLIC_PAYLOAD_ROLE_SEMANTICS",
            ["python", "-m", "release_machine", "public-payload", "--release-id", RELEASE_ID, "--check"],
            600,
        ),
        (
            "RELEASE_SPACE_SEPARATION",
            ["python", "-m", "release_machine", "release-spaces", "--release-id", RELEASE_ID, "--repair", "--write", "--check"],
            900,
        ),
        (
            "FUNCTION_PRODUCT_SEPARATION",
            ["python", "-m", "release_machine", "function-product", "--write", "--check"],
            300,
        ),
    ])
    if approved_mode:
        commands.append(
            (
                "RELEASE_SPACE_OWNER_APPROVAL_REAPPLY",
                [
                    "python",
                    "-m",
                    "release_machine",
                    "owner-approve",
                    "--release-id",
                    RELEASE_ID,
                    "--owner-identity",
                    "Alexander Yashin",
                ],
                900,
            )
        )
    commands.extend([
        (
            "APPROVAL_MODE_CONTRACT_FINITE",
            ["python", "proofs/finite_model_checks/run_finite_model_checks.py"],
            600,
        ),
        (
            "REVIEW_SCORECARD_POST_REPAIR",
            ["python", "-m", "release_machine", "evaluate", "--release", RELEASE_ID, "--channel", "all", "--mode", "dry-run"],
            900,
        ),
        (
            "APPROVAL_MODE_CONTRACT_OWNER_AUDIT",
            ["python", "tools/oc133_personal_release_audit.py"],
            600,
        ),
    ])
    if not approved_mode:
        commands = [
            row for row in commands
            if row[0] != "APPROVAL_MODE_CONTRACT_FINITE"
        ]
    rows = []
    for repair_class_id, args, timeout in commands:
        result = run_command(args, timeout=timeout)
        result["repair_class_id"] = repair_class_id
        rows.append(result)
        if not result["ok"]:
            break
    return {
        "schema_id": "LOGION_ARCHITECTURE_SELF_REPAIR_EXECUTION_v1",
        "incident_id": INCIDENT_ID,
        "release_id": RELEASE_ID,
        "version": VERSION,
        "public_release_approval_mode": approved_mode,
        "active_public_release_approval_mode": active_approved_mode,
        "durable_owner_release_authorization": durable_release_authorization,
        "mode_transition_policy": mode_transition_policy,
        "contract": contract,
        "rows": rows,
        "failure_total": sum(1 for row in rows if not row["ok"]),
        "state": "PASS" if rows and all(row["ok"] for row in rows) else "REPAIR_FAILED",
    }


def build_incident_payload() -> dict[str, Any]:
    master = ROOT / "releases" / RELEASE_ID / "artifacts" / "OC_CORE_1_3_3_MASTER_MONOGRAPH_EN.pdf"
    monolith_audit = read_json(ROOT / "releases" / RELEASE_ID / "editorial" / "SCIENCE_MONOLITH_AUDIT_1_3_3_latest.json", {})
    public_payload = read_json(ROOT / "releases" / RELEASE_ID / "editorial" / "PUBLIC_PAYLOAD_SUITABILITY_1.3.3_latest.json", {})
    scorecard = read_json(ROOT / "releases" / RELEASE_ID / "editorial" / "OC_CORE_1_3_3_RELEASE_SCORECARD_latest.json", {})
    summary = scorecard.get("summary", scorecard)
    current_master = pdf_stats(master)
    bad_release_records = ["19956748", "19956854", "19957779", "19964204"]
    root_causes = [
        {
            "root_cause_id": "RC-001",
            "owner_capability": "Publication/ReleaseEngineering",
            "cause": "The public payload builder allowed the MASTER_MONOGRAPH role to be generated from compact Markdown.",
            "class_fix": "FULL_MONOGRAPH_GATE and PUBLIC_PAYLOAD_ROLE_GATE require a full TeX monolith plus 1.3.3 science delta coverage.",
        },
        {
            "root_cause_id": "RC-002",
            "owner_capability": "Research/ManuscriptIntegration",
            "cause": "There was no explicit science-to-manuscript corpus ledger proving all promoted 1.3.3 science surfaces entered the manuscript.",
            "class_fix": "SCIENCE_MONOLITH_CORPUS_LEDGER records baseline corpus, 1.3.3 science deltas, proof sheets, and exclusion policy.",
        },
        {
            "root_cause_id": "RC-003",
            "owner_capability": "IT/ReleaseAutomation",
            "cause": "Presentation gates checked metadata formatting but not role semantics, source provenance, or primary-PDF substance.",
            "class_fix": "SOURCE_TO_PDF_TRACE_GATE and PUBLIC_FILE_SET_GATE bind role, page/text thresholds, source hashes, and PDF anchors.",
        },
        {
            "root_cause_id": "RC-004",
            "owner_capability": "StrategyHQ/IncidentManagement",
            "cause": "The failed publication path did not auto-open an incident, assign capability work orders, and block replacement until RCA closure.",
            "class_fix": "This incident pipeline emits RCA, work orders, cockpit state, and closure predicates for the release replacement.",
        },
        {
            "root_cause_id": "RC-005",
            "owner_capability": "IT/ReleaseAutomation",
            "cause": "The same root metadata files were used as verification/no-outbound controls and as public release artifacts.",
            "class_fix": "LOGION_RELEASE_SPACE_MODEL separates development, verification, and release spaces; migration gates carry approval predicates between spaces.",
        },
        {
            "root_cause_id": "RC-006",
            "owner_capability": "ServiceArchitecture/Router",
            "cause": "The first repair design treated incident, editorial, research, verification, release, and publication as one case pipeline instead of independent Logion services.",
            "class_fix": "LOGION_SERVICE_REGISTRY and LOGION_SERVICE_ROUTER define independent service lines and route the 1.3.3 incident as one signal across them.",
        },
    ]
    work_orders = [
        {
            "work_order_id": "OC133-INC-WO-001",
            "owner_capability": "ServiceArchitecture/Router",
            "title": "Define independent Logion services and route the 1.3.3 publication incident through service contracts",
            "artifacts": [
                "operations/logion_services/LOGION_SERVICE_REGISTRY.json",
                "operations/logion_services/LOGION_SERVICE_ROUTER.json",
                "operations/logion_services/LOGION_SERVICE_CONTRACTS.json",
            ],
            "closure_predicate": "service registry PASS, incident_management/editorial/research/release/publication are separate services",
            "verification_command": "python -m release_machine services --check",
            "status": "CLOSED"
            if read_json(ROOT / "operations" / "logion_services" / "LOGION_SERVICE_REGISTRY.json", {}).get("service_total", 0) >= 8
            else "OPEN",
        },
        {
            "work_order_id": "OC133-INC-WO-002",
            "owner_capability": "Research/ManuscriptIntegration",
            "title": "Build OC Core 1.3.3 science monolith from full corpus plus 1.3.3 delta",
            "artifacts": [
                "releases/oc_core_1_3_3/artifacts/OC_CORE_1_3_3_MASTER_MONOGRAPH_EN.pdf",
                "releases/oc_core_1_3_3/editorial/SCIENCE_MONOLITH_CORPUS_LEDGER_1_3_3_latest.json",
            ],
            "closure_predicate": "master pages >= 690, dedication present, all 1.3.3 science anchors present, stale 1.3.2 identity absent",
            "verification_command": "python -m release_machine science-monolith --release-id oc_core_1_3_3 --check",
            "status": "CLOSED" if monolith_audit.get("state") == "PASS" else "OPEN",
        },
        {
            "work_order_id": "OC133-INC-WO-003",
            "owner_capability": "IT/ReleaseAutomation",
            "title": "Prevent surrogate PDFs and control packets from occupying public scientific roles",
            "artifacts": ["release_machine/science_monolith.py", "tools/oc133_public_release_payload.py", "release_machine/public_release.py"],
            "closure_predicate": "public payload suitability requires science_monolith_audit PASS and rejects tiny primary PDFs",
            "verification_command": "python -m release_machine public-payload --release-id oc_core_1_3_3 --check",
            "status": "CLOSED" if public_payload.get("state") == "PASS" and monolith_audit.get("state") == "PASS" else "OPEN",
        },
        {
            "work_order_id": "OC133-INC-WO-004",
            "owner_capability": "Review/Cerberus",
            "title": "Re-run release gates after monolith integration and reopen any scientific or public-surface blockers",
            "artifacts": ["releases/oc_core_1_3_3/editorial/OC_CORE_1_3_3_RELEASE_SCORECARD_latest.json"],
            "closure_predicate": "release scorecard PASS, Cerberus critical/high/parse = 0/0/0, public replacement preflight PASS",
            "verification_command": "python -m release_machine evaluate --release oc_core_1_3_3 --channel all --mode dry-run",
            "status": "CLOSED" if summary.get("master_verdict") == "PASS" else "OPEN",
        },
        {
            "work_order_id": "OC133-INC-WO-005",
            "owner_capability": "IT/ReleaseAutomation",
            "title": "Separate development, verification, and release spaces so public artifacts contain no verification-control vocabulary",
            "artifacts": [
                "operations/project_control/LOGION_RELEASE_SPACE_MODEL.json",
                "operations/project_control/LOGION_RELEASE_SPACE_AUDIT.json",
                "tools/logion_release_spaces.py",
            ],
            "closure_predicate": "release space audit PASS, control_language_hit_total=0, root manifest is PUBLIC_GITHUB_ZENODO_RELEASE",
            "verification_command": "python -m release_machine release-spaces --release-id oc_core_1_3_3 --check",
            "status": "CLOSED"
            if read_json(ROOT / "operations" / "project_control" / "LOGION_RELEASE_SPACE_AUDIT.json", {}).get("state") == "PASS"
            else "OPEN",
        },
        {
            "work_order_id": "OC133-INC-WO-006",
            "owner_capability": "Publication/PublicRecords",
            "title": "Replace bad GitHub and Zenodo public records only after local incident closure",
            "artifacts": ["releases/oc_core_1_3_3/editorial/PUBLIC_RELEASE_EXECUTION_REPORT_v1.3.3.json"],
            "closure_predicate": "GitHub v1.3.3 and newest Zenodo version contain exact corrected file set and checksums",
            "verification_command": "python -m release_machine postflight --release oc_core_1_3_3",
            "status": "PENDING_LOCAL_GATES",
        },
    ]
    open_total = sum(1 for row in work_orders if row["status"] not in {"CLOSED"})
    self_repair_contract = build_self_repair_contract()
    return {
        "schema_id": "LOGION_INCIDENT_MANAGEMENT_CASE_v1",
        "incident_id": INCIDENT_ID,
        "release_id": RELEASE_ID,
        "version": VERSION,
        "authority_chain": [
            "Safety Directive",
            "LOGI",
            "K6 Strategy HQ",
            "Institute Director",
            "Capability Directors",
            "Release Executors",
        ],
        "state": "CLOSED_READY_FOR_PUBLIC_REPLACEMENT" if open_total == 1 and work_orders[-1]["status"] == "PENDING_LOCAL_GATES" else "ACTIVE_REPAIR",
        "severity": "P0",
        "signal_class": "bad_public_release_record",
        "strategy_hq_signal": "IMMEDIATE",
        "incident_commander": "K6 Strategy HQ",
        "escalation_matrix_ref": ESCALATION_MATRIX_REF,
        "incident_queue_ref": INCIDENT_QUEUE_REF,
        "freeze_policy": "freeze further public actions except controlled GitHub/Zenodo replacement through release_machine.publish-replace",
        "manual_repair_allowed": False,
        "bad_public_records": bad_release_records,
        "current_master_pdf": current_master,
        "monolith_audit": {
            "state": monolith_audit.get("state"),
            "pages": monolith_audit.get("pages"),
            "text_chars": monolith_audit.get("text_chars"),
            "sha256": monolith_audit.get("sha256"),
            "failures": monolith_audit.get("failures"),
        },
        "public_payload_state": public_payload.get("state"),
        "release_scorecard": {
            "master_verdict": summary.get("master_verdict"),
            "release_state": summary.get("release_state"),
            "gate_counts": summary.get("gate_counts"),
        },
        "root_causes": root_causes,
        "self_repair_contract": self_repair_contract,
        "work_orders": work_orders,
        "open_work_order_total": open_total,
        "replacement_block_rule": "No GitHub/Zenodo replacement until all non-publication work orders are CLOSED and publication work order is the only remaining pending action.",
    }


def write_incident(payload: dict[str, Any]) -> dict[str, Any]:
    changed = []
    if write_json_if_changed(INCIDENT_ROOT / "INCIDENT_CASE.json", payload):
        changed.append("INCIDENT_CASE.json")
    if write_json_if_changed(INCIDENT_ROOT / "WORK_ORDERS.json", payload["work_orders"]):
        changed.append("WORK_ORDERS.json")
    if write_json_if_changed(INCIDENT_ROOT / "ARCHITECTURE_SELF_REPAIR_CONTRACT.json", payload["self_repair_contract"]):
        changed.append("ARCHITECTURE_SELF_REPAIR_CONTRACT.json")
    lines = [
        f"# {payload['incident_id']}",
        "",
        f"- state: `{payload['state']}`",
        f"- release: `{payload['release_id']}` v`{payload['version']}`",
        f"- master pages: `{payload['current_master_pdf'].get('pages')}`",
        f"- monolith audit: `{payload['monolith_audit'].get('state')}`",
        f"- release scorecard: `{payload['release_scorecard'].get('master_verdict')}`",
        f"- open work orders: `{payload['open_work_order_total']}`",
        "",
        "## Root Causes",
    ]
    for row in payload["root_causes"]:
        lines.append(f"- `{row['root_cause_id']}` `{row['owner_capability']}`: {row['cause']}")
    lines.extend(["", "## Work Orders"])
    for row in payload["work_orders"]:
        lines.append(f"- `{row['work_order_id']}` `{row['owner_capability']}` `{row['status']}`: {row['title']}")
    lines.extend(["", "## Self-Repair Classes"])
    for row in payload["self_repair_contract"]["repair_classes"]:
        lines.append(f"- `{row['repair_class_id']}` `{row['owner_capability']}` -> `{row['executor']}`")
    if write_text_if_changed(INCIDENT_ROOT / "RCA_AND_COCKPIT.md", "\n".join(lines)):
        changed.append("RCA_AND_COCKPIT.md")
    return {"state": payload["state"], "changed": changed, "changed_total": len(changed)}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Logion incident pipeline for release/publication failures.")
    parser.add_argument("--release-id", default=RELEASE_ID)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--run-self-repair", action="store_true")
    args = parser.parse_args(argv)
    if args.release_id != RELEASE_ID:
        raise SystemExit(f"unsupported release id: {args.release_id}")
    payload = build_incident_payload()
    if args.run_self_repair:
        execution = run_self_repair_contract()
        payload["self_repair_execution"] = execution
        if args.write:
            write_json_if_changed(INCIDENT_ROOT / "ARCHITECTURE_SELF_REPAIR_EXECUTION.json", execution)
    if args.write:
        payload["write_result"] = write_incident(payload)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload["state"] in {"ACTIVE_REPAIR", "CLOSED_READY_FOR_PUBLIC_REPLACEMENT"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
