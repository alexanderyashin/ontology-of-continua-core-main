from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
RESULT_DIR = ROOT / "reviews" / "oc133_llm_cerberus" / "results"
PROMPT_DIR = ROOT / "reviews" / "oc133_llm_cerberus" / "prompts_v12"
LAST_DIR = ROOT / "reviews" / "oc133_llm_cerberus" / "raw_v12"
CONTEXT_DIR = ROOT / "reviews" / "oc133_llm_cerberus" / "context_v12"

ROLES = [
    "formal_mathematician",
    "dynamical_systems_reviewer",
    "category_type_theory_reviewer",
    "empirical_statistician",
    "prior_art_historian",
    "hostile_journal_reviewer",
    "not_novel_attacker",
    "phenomenon_x_attacker",
    "clarity_didactic_reviewer",
    "reproducibility_auditor",
    "theorem_theater_auditor",
    "empirical_theater_auditor",
    "claim_boundary_auditor",
    "public_surface_auditor",
]

CONTEXT_REFS = [
    "claims/CLAIM_LEDGER_1_3_3.json",
    "proofs/THEOREM_INVENTORY_1_3_3.json",
    "proofs/PROOF_LEDGER_1_3_3.md",
    "proofs/FINITE_MODEL_CHECKS_1_3_3.json",
    "proofs/finite_model_checks/OC133_FINITE_MODEL_INPUTS.json",
    "proofs/finite_model_checks/run_finite_model_checks.py",
    "formal/lean/OC133V12.lean",
    "validation/numeric_replay_qa/OC133_NUMERIC_REPLAY_QA_TABLE.json",
    "comparators/OC_1_3_3_NOVELTY_AND_PRIORITY_REGISTER.json",
    "docs/OC_1_3_3_PHENOMENON_COVERAGE_MATRIX.json",
    "review/OC_1_3_3_TOTAL_ATTACK_MATRIX.json",
    "releases/oc_core_1_3_3/editorial/OC_CORE_1_3_3_PUBLISH_MANIFEST_DRAFT.json",
    "manifest.json",
    "checksums.txt",
    "ro-crate-metadata.jsonld",
]

ROLE_CONTEXT_REFS = {
    "formal_mathematician": [
        "proofs/THEOREM_INVENTORY_1_3_3.json",
        "proofs/PROOF_LEDGER_1_3_3.md",
        "proofs/FINITE_MODEL_CHECKS_1_3_3.json",
        "formal/lean/OC133V12.lean",
        "formal/lean/LEAN_BUILD_CERTIFICATE_1_3_3.json",
        "claims/CLAIM_LEDGER_1_3_3.json",
    ],
    "dynamical_systems_reviewer": [
        "formal/lean/OC133V12.lean",
        "content/OC_1_3_3_OPERATOR_SEMANTICS.tex",
        "proofs/FINITE_MODEL_CHECKS_1_3_3.json",
        "proofs/finite_model_checks/run_finite_model_checks.py",
        "docs/OC_1_3_3_PHENOMENON_COVERAGE_MATRIX.json",
        "claims/CLAIM_LEDGER_1_3_3.json",
    ],
    "category_type_theory_reviewer": [
        "formal/lean/OC133V12.lean",
        "proofs/FINITE_MODEL_CHECKS_1_3_3.json",
        "proofs/finite_model_checks/run_finite_model_checks.py",
        "claims/CLAIM_LEDGER_1_3_3.json",
        "proofs/THEOREM_INVENTORY_1_3_3.json",
    ],
    "empirical_statistician": [
        "validation/numeric_replay_qa/OC133_NUMERIC_REPLAY_QA_TABLE.json",
        "validation/numeric_predictions/OC133_NUMERIC_REPLAY_LOG.json",
        "reports/OC_CORE_1_3_3_DOMAIN_VALIDATION_REPORT.json",
        "validation/run_all.py",
        "claims/CLAIM_LEDGER_1_3_3.json",
    ],
    "prior_art_historian": [
        "comparators/OC_1_3_3_NOVELTY_AND_PRIORITY_REGISTER.json",
        "comparators/source_snapshots",
        "claims/CLAIM_LEDGER_1_3_3.json",
    ],
    "hostile_journal_reviewer": [
        "claims/CLAIM_LEDGER_1_3_3.json",
        "proofs/THEOREM_INVENTORY_1_3_3.json",
        "validation/numeric_replay_qa/OC133_NUMERIC_REPLAY_QA_TABLE.json",
        "comparators/OC_1_3_3_NOVELTY_AND_PRIORITY_REGISTER.json",
        "docs/OC_1_3_3_PHENOMENON_COVERAGE_MATRIX.json",
        "review/OC_1_3_3_TOTAL_ATTACK_MATRIX.json",
    ],
    "not_novel_attacker": [
        "comparators/OC_1_3_3_NOVELTY_AND_PRIORITY_REGISTER.json",
        "claims/CLAIM_LEDGER_1_3_3.json",
        "docs/OC_1_3_3_HOSTILE_READER_GUIDE.md",
    ],
    "phenomenon_x_attacker": [
        "docs/OC_1_3_3_PHENOMENON_COVERAGE_MATRIX.json",
        "proofs/FINITE_MODEL_CHECKS_1_3_3.json",
        "claims/CLAIM_LEDGER_1_3_3.json",
    ],
    "clarity_didactic_reviewer": [
        "docs/OC_1_3_3_HOSTILE_READER_GUIDE.md",
        "docs/OC_1_3_3_PHENOMENON_COVERAGE_MATRIX.json",
        "proofs/THEOREM_INVENTORY_1_3_3.json",
        "proofs/FINITE_MODEL_CHECKS_1_3_3.json",
        "claims/CLAIM_LEDGER_1_3_3.json",
    ],
    "reproducibility_auditor": [
        "lakefile.lean",
        "lean-toolchain",
        "formal/lean/LEAN_BUILD_CERTIFICATE_1_3_3.json",
        "reports/OC_CORE_1_3_3_POST_GENERATION_REPRODUCIBILITY_MANIFEST.json",
        "tools/verify_oc133_reproducible_temp_tree.py",
        "proofs/finite_model_checks/run_finite_model_checks.py",
        "validation/run_all.py",
        "simulations/run_all.py",
        "simulations/adversarial/run_all.py",
    ],
    "theorem_theater_auditor": [
        "formal/lean/OC133V12.lean",
        "proofs/THEOREM_INVENTORY_1_3_3.json",
        "proofs/PROOF_LEDGER_1_3_3.md",
        "proofs/FINITE_MODEL_CHECKS_1_3_3.json",
        "claims/CLAIM_LEDGER_1_3_3.json",
    ],
    "empirical_theater_auditor": [
        "validation/numeric_replay_qa/OC133_NUMERIC_REPLAY_QA_TABLE.json",
        "validation/numeric_predictions/OC133_NUMERIC_REPLAY_LOG.json",
        "reports/OC_CORE_1_3_3_DOMAIN_VALIDATION_REPORT.json",
        "docs/OC_1_3_3_PHENOMENON_COVERAGE_MATRIX.json",
    ],
    "claim_boundary_auditor": [
        "claims/CLAIM_LEDGER_1_3_3.json",
        "review/OC_1_3_3_TOTAL_ATTACK_MATRIX.json",
        "docs/OC_1_3_3_HOSTILE_READER_GUIDE.md",
        "validation/numeric_replay_qa/OC133_NUMERIC_REPLAY_QA_TABLE.json",
    ],
    "public_surface_auditor": [
        ".zenodo.json",
        "CITATION.cff",
        ".codemeta.json",
        "manifest.json",
        "checksums.txt",
        "ro-crate-metadata.jsonld",
        "releases/oc_core_1_3_3/editorial/metadata_drafts/zenodo.no_send.draft.json",
        "releases/oc_core_1_3_3/editorial/OC_CORE_1_3_3_PUBLISH_MANIFEST_DRAFT.json",
        "releases/oc_core_1_3_3/editorial/OWNER_RELEASE_APPROVAL_v1.3.3.json",
        "proofs/FINITE_MODEL_CHECKS_1_3_3.json",
        "docs/OC_1_3_3_PHENOMENON_COVERAGE_MATRIX.json",
    ],
}

ROLE_FOCUS = {
    "formal_mathematician": "Check whether each Lean theorem proves the proposition the public ledger claims, especially minimality, K-level irreducibility, k=0, boundary, and hybrid semantics.",
    "dynamical_systems_reviewer": "Attack universal-dynamics overreach, smoothness assumptions, hybrid guard/reset semantics, and any hidden ODE claim.",
    "category_type_theory_reviewer": "Attack typed-carrier/morphism claims, identity/residue/rebirth separation, and any categorical wording not supported by the Lean subset.",
    "empirical_statistician": "Attack numeric replay language, heldout/baseline-control/residual claims, and any empirical PASS based only on official snapshots.",
    "prior_art_historian": "Attack novelty and priority using the comparator rows as bibliographic positioning only. Do not treat single-source non-observation as absence evidence unless the current row promotes it.",
    "hostile_journal_reviewer": "Attack whether a skeptical journal could reject the package for theorem theater, empirical theater, novelty inflation, or didactic opacity.",
    "not_novel_attacker": "Try to reduce OC to GST, autopoiesis, dynamical systems, category/topos formalisms, RAF, complexity measures, identity theory, systems engineering, hybrid systems, or formal methods.",
    "phenomenon_x_attacker": "Attack the phenomenon coverage model cards: each broad phenomenon must have a specific model, observable, negative control, and falsifier.",
    "clarity_didactic_reviewer": "Attack whether a hostile reader can follow tuple -> theorem -> semantic finite case -> falsifier without author help.",
    "reproducibility_auditor": "Attack whether a clean checkout can regenerate current artifacts without hidden local state or cached .lake files.",
    "theorem_theater_auditor": "Attack any theorem whose Lean/formal/finite evidence is only definitional, circular, or weaker than the promoted claim.",
    "empirical_theater_auditor": "Attack any numeric/validation row that is snapshot replay while being used as empirical prediction support.",
    "claim_boundary_auditor": "Attack absolute TOE/truth/irrefutability/public-promotion overclaims and any claim boundary that relies on wording instead of evidence.",
    "public_surface_auditor": "Attack no-send, owner approval, DOI/public action, stale release metadata, local paths, and public-surface parity.",
}

G58_INPUT_REFS = sorted(
    {
        "tools/run_oc133_v12_cerberus.py",
        *CONTEXT_REFS,
        *[ref for refs in ROLE_CONTEXT_REFS.values() for ref in refs],
    }
)
G58_FRONTIER_REFS = sorted({*G58_INPUT_REFS, "reviews/oc133_llm_cerberus/results"})


def extract_json(text: str) -> dict[str, Any]:
    stripped = text.strip()
    if stripped.startswith("{"):
        return json.loads(stripped)
    match = re.search(r"\{.*\}", stripped, re.S)
    if not match:
        raise ValueError("No JSON object found")
    return json.loads(match.group(0))


def canonical_sha256(payload: Any) -> str:
    digest = hashlib.sha256()
    digest.update(
        json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    )
    return digest.hexdigest()


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def ref_path(ref: str) -> Path:
    return ROOT / ref


def directory_sha256(path: Path) -> tuple[str, int]:
    child_hashes = []
    for child in sorted(path.rglob("*")):
        if child.is_file() and ".git" not in child.parts:
            child_hashes.append(f"{rel(child)}:{file_sha256(child)}")
    return hashlib.sha256("\n".join(child_hashes).encode("utf-8")).hexdigest(), len(child_hashes)


def artifact_hash_row(ref: str) -> dict[str, Any]:
    path = ref_path(ref)
    row: dict[str, Any] = {"ref": ref}
    if path.is_file():
        row.update({"kind": "file", "sha256": file_sha256(path)})
    elif path.is_dir():
        digest, child_total = directory_sha256(path)
        row.update({"kind": "directory", "sha256": digest, "child_file_total": child_total})
    else:
        row.update({"kind": "missing", "sha256": None})
    return row


def artifact_hashes(refs: list[str]) -> list[dict[str, Any]]:
    return [artifact_hash_row(ref) for ref in sorted(dict.fromkeys(refs))]


def artifact_hash_map(refs: list[str]) -> dict[str, str | None]:
    return {row["ref"]: row["sha256"] for row in artifact_hashes(refs)}


def artifacts_manifest_hash(refs: list[str]) -> str:
    return canonical_sha256(artifact_hashes(refs))


def g58_frontier_hash() -> str:
    return artifacts_manifest_hash(G58_FRONTIER_REFS)


def existing_role_context_refs(role: str) -> list[str]:
    refs = []
    for source_ref in ROLE_CONTEXT_REFS.get(role, CONTEXT_REFS):
        if source_ref == "review/OC_1_3_3_TOTAL_ATTACK_MATRIX.json":
            context_ref = (CONTEXT_DIR / role / source_ref).resolve().relative_to(ROOT.resolve()).as_posix()
            refs.append(context_ref if (ROOT / context_ref).exists() else source_ref)
        else:
            refs.append(source_ref)
    return refs


def is_cerberus_row(row: dict[str, Any]) -> bool:
    source = str(row.get("source", "")).strip().lower()
    if source == "llm_cerberus" or source == "llm_cerberus_sourced":
        return True
    source_ref = str(row.get("source_result_ref", "")).strip()
    return source_ref.startswith("reviews/oc133_llm_cerberus/results/")


def row_is_closed(row: dict[str, Any]) -> bool:
    status = str(row.get("status", "OPEN")).upper()
    return status in {"CLOSED", "RESOLVED", "CLOSED_BY_V12_EVIDENCE", "CLOSED_BY_SPECIFIC_V12_EVIDENCE"}


def compact_attack_row(row: dict[str, Any]) -> dict[str, Any]:
    keep = {
        "objection_id",
        "source",
        "source_result_ref",
        "source_finding_hash",
        "theme",
        "severity",
        "attacked_claim",
        "artifact_location",
        "objection",
        "failure_mode",
        "required_repair",
        "closure_verification_query",
        "status",
        "no_send",
    }
    compact = {key: row[key] for key in keep if key in row}
    compact["row_context_hash"] = canonical_sha256(compact)
    return compact


def normalize(role: str, payload: dict[str, Any], output_path: Path) -> dict[str, Any]:
    findings = payload.get("findings", [])
    if not isinstance(findings, list):
        findings = []
    critical = [
        row for row in findings
        if str(row.get("severity", "")).upper() == "CRITICAL"
        and str(row.get("status", "OPEN")).upper() not in {"CLOSED", "RESOLVED", "CLOSED_BY_V12_EVIDENCE"}
    ]
    high = [
        row for row in findings
        if str(row.get("severity", "")).upper() == "HIGH"
        and str(row.get("status", "OPEN")).upper() not in {"CLOSED", "RESOLVED", "CLOSED_BY_V12_EVIDENCE"}
    ]
    return {
        "schema_id": "OC133_LLM_CERBERUS_RESULT_v12",
        "role": payload.get("role", role),
        "execution_status": "EXECUTED",
        "critical_open_total": len(critical),
        "high_open_total": len(high),
        "finding_total": len(findings),
        "findings": findings,
        "raw_output_ref": output_path.resolve().relative_to(ROOT.resolve()).as_posix(),
    }


def prompt_for(role: str, context_refs: list[str] | None = None) -> str:
    refs = "\n".join(f"- `{path}`" for path in (context_refs or role_context_refs(role)))
    focus = ROLE_FOCUS.get(role, "Attack unsupported critical/high release claims.")
    return f"""You are the OC Core 1.3.3 v12 adversarial reviewer role `{role}`.

Work read-only. Inspect only these release-critical artifacts unless a directly referenced file is needed:
{refs}

Role focus: {focus}

Attack the release hard. Focus on unsupported critical/high claims, theorem theater, empirical theater,
prior-art relabeling, phenomenon coverage gaps, no-send violations, and absolute TOE overclaims.
Use the current artifacts exactly. Context references include role-scoped attack-matrix hashes and
fresh totals; do not re-report findings from stale LLM rows.

Return exactly one JSON object with this shape:
{{
  "role": "{role}",
  "findings": [
    {{
      "severity": "CRITICAL|HIGH|MEDIUM|LOW",
      "artifact_ref": "path",
      "claim": "attacked claim",
      "failure_mode": "why it fails",
      "required_repair": "specific repair",
      "status": "OPEN"
    }}
  ]
}}

If no critical/high issues remain, return an empty findings array or only lower-severity findings.
Do not include markdown outside the JSON object.
"""


def run_role(role: str, timeout_seconds: int = 420) -> dict[str, Any]:
    context_refs = role_context_refs(role)
    prompt = prompt_for(role, context_refs)
    prompt_path = PROMPT_DIR / f"{role}.txt"
    output_path = LAST_DIR / f"{role}.txt"
    prompt_path.write_text(prompt, encoding="utf-8")
    cmd = [
        "codex",
        "exec",
        "-s",
        "read-only",
        "-c",
        "approval_policy='never'",
        "-C",
        str(ROOT),
        "-o",
        str(output_path),
        "-",
    ]
    result_path = RESULT_DIR / f"{role}.json"
    try:
        completed = subprocess.run(
            cmd,
            input=prompt,
            cwd=ROOT,
            text=True,
            encoding="utf-8",
            errors="replace",
            capture_output=True,
            timeout=timeout_seconds,
        )
    except subprocess.TimeoutExpired as exc:
        payload = {
            "schema_id": "OC133_LLM_CERBERUS_RESULT_v12",
            "role": role,
            "execution_status": "EXECUTION_TIMEOUT",
            "critical_open_total": 1,
            "high_open_total": 0,
            "finding_total": 1,
            "findings": [
                {
                    "severity": "CRITICAL",
                    "artifact_ref": "tools/run_oc133_v12_cerberus.py",
                    "claim": "LLM adversarial review must execute.",
                    "failure_mode": f"Role `{role}` exceeded timeout_seconds={timeout_seconds}: {exc}",
                    "required_repair": "Rerun role with smaller context or repair Codex CLI latency; stale prior JSON must not be reused.",
                    "status": "OPEN",
                }
            ],
        }
    else:
        if completed.returncode != 0:
            payload = {
                "schema_id": "OC133_LLM_CERBERUS_RESULT_v12",
                "role": role,
                "execution_status": "EXECUTION_FAILED",
                "critical_open_total": 1,
                "high_open_total": 0,
                "finding_total": 1,
                "findings": [
                    {
                        "severity": "CRITICAL",
                        "artifact_ref": "tools/run_oc133_v12_cerberus.py",
                        "claim": "LLM adversarial review must execute.",
                        "failure_mode": completed.stderr[-2000:],
                        "required_repair": "Restore Codex CLI execution and rerun.",
                        "status": "OPEN",
                    }
                ],
            }
        else:
            try:
                raw = output_path.read_text(encoding="utf-8")
                payload = normalize(role, extract_json(raw), output_path)
            except Exception as exc:
                payload = {
                    "schema_id": "OC133_LLM_CERBERUS_RESULT_v12",
                    "role": role,
                    "execution_status": "PARSE_FAILED",
                    "critical_open_total": 1,
                    "high_open_total": 0,
                    "finding_total": 1,
                    "findings": [
                        {
                            "severity": "CRITICAL",
                            "artifact_ref": output_path.resolve().relative_to(ROOT.resolve()).as_posix(),
                            "claim": "LLM adversarial review output must be structured JSON.",
                            "failure_mode": str(exc),
                            "required_repair": "Rerun role or repair schema compliance.",
                            "status": "OPEN",
                        }
                    ],
                }
    result_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {
        "role": role,
        "payload": payload,
        "result_ref": result_path.resolve().relative_to(ROOT.resolve()).as_posix(),
        "role_context_refs": context_refs,
        "role_context_sha256": artifacts_manifest_hash(context_refs),
        "prompt_ref": prompt_path.resolve().relative_to(ROOT.resolve()).as_posix(),
        "prompt_sha256": file_sha256(prompt_path),
        "raw_output_ref": output_path.resolve().relative_to(ROOT.resolve()).as_posix(),
        "raw_output_sha256": file_sha256(output_path) if output_path.exists() else None,
        "result_sha256": file_sha256(result_path),
        "parse_failed": payload.get("execution_status") == "PARSE_FAILED",
        "execution_failed": payload.get("execution_status") in {"EXECUTION_FAILED", "EXECUTION_TIMEOUT"},
    }


def selected_roles(raw_roles: str) -> list[str]:
    if not raw_roles:
        return list(ROLES)
    requested = [role.strip() for role in raw_roles.split(",") if role.strip()]
    unknown = sorted(set(requested) - set(ROLES))
    if unknown:
        raise SystemExit(f"Unknown Cerberus roles: {', '.join(unknown)}")
    return requested


def fresh_context_ref(role: str, ref: str) -> str:
    if ref != "review/OC_1_3_3_TOTAL_ATTACK_MATRIX.json":
        return ref
    source_path = ROOT / ref
    if not source_path.exists():
        return ref
    payload = json.loads(source_path.read_text(encoding="utf-8"))
    rows = payload.get("rows", [])
    if not isinstance(rows, list):
        rows = []
    source_attack_matrix_rows = [row for row in rows if isinstance(row, dict)]
    deterministic_rows = [row for row in source_attack_matrix_rows if not is_cerberus_row(row)]
    excluded_rows = [row for row in source_attack_matrix_rows if is_cerberus_row(row)]
    deterministic_open_rows = [row for row in deterministic_rows if not row_is_closed(row)]
    compacted_rows = [compact_attack_row(row) for row in deterministic_rows]

    view = dict(payload)
    view["fresh_cerberus_context_view"] = True
    view["release_closure_matrix_kind"] = "ROLE_CONTEXT_VIEW_NOT_RELEASE_MATRIX"
    view["source_attack_matrix_ref"] = ref
    view["source_attack_matrix_sha256"] = file_sha256(source_path)
    view["excluded_prior_llm_cerberus_row_total"] = len(excluded_rows)
    view["fresh_context_policy"] = (
        "Prior LLM-derived rows are excluded from this reviewer context so a fresh role rerun "
        "does not self-repeat stale open findings. The reviewer must inspect underlying current "
        "artifacts and report only defects still present now."
    )
    view["rows"] = compacted_rows
    deterministic_critical = sum(
        1 for row in deterministic_rows
        if str(row.get("severity", "")).upper() == "CRITICAL" and not row_is_closed(row)
    )
    deterministic_high = sum(
        1 for row in deterministic_rows
        if str(row.get("severity", "")).upper() == "HIGH" and not row_is_closed(row)
    )
    view["critical_context_row_total"] = len(deterministic_rows)
    view["high_context_row_total"] = sum(
        1 for row in deterministic_rows
        if str(row.get("severity", "")).upper() == "HIGH"
    )
    view["critical_context_open_row_total"] = sum(
        1 for row in deterministic_open_rows if str(row.get("severity", "")).upper() == "CRITICAL"
    )
    view["high_context_open_row_total"] = sum(
        1 for row in deterministic_open_rows if str(row.get("severity", "")).upper() == "HIGH"
    )
    view["deterministic_context_critical_unresolved_total"] = deterministic_critical
    view["deterministic_context_high_unresolved_total"] = deterministic_high
    summary_path = ROOT / "reviews" / "oc133_llm_cerberus" / "OC133_LLM_CERBERUS_SUMMARY.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8")) if summary_path.exists() else {}
    fresh_critical = int(summary.get("critical_open_total", 0) or 0)
    fresh_high = int(summary.get("high_open_total", 0) or 0)
    view["fresh_context_critical_open_total"] = fresh_critical
    view["fresh_context_high_open_total"] = fresh_high
    view["critical_unresolved_total"] = deterministic_critical + fresh_critical
    view["high_unresolved_total"] = deterministic_high + fresh_high
    view["release_closure_claim_asserted"] = False
    view["fresh_context_counter_policy"] = (
        "This role-specific context is intentionally not a release-closure matrix. "
        "deterministic_context_* counters describe the filtered deterministic view; "
        "critical_unresolved_total/high_unresolved_total include the latest fresh Cerberus open findings so the context view never displays release-like zero blockers while G58/G70 remain open; "
        "fresh_cerberus_* fields copy the latest integrated summary and the release matrix must be regenerated after this role result."
    )
    view["objection_total"] = len(deterministic_rows)
    view["open_objection_total"] = len(deterministic_open_rows)
    view["cerberus_sourced_objection_total"] = 0
    view["fresh_cerberus_review_satisfied"] = False
    view["fresh_cerberus_review_gate_status"] = "CONTEXT_VIEW_NOT_RELEASE_GATE"
    view["fresh_context_not_release_evidence"] = True
    view["fresh_context_pass_fields_suppressed"] = True
    view["fresh_cerberus_execution_status"] = summary.get("execution_status", "NO_PRIOR_SUMMARY")
    view["fresh_cerberus_critical_open_total"] = fresh_critical
    view["fresh_cerberus_high_open_total"] = fresh_high
    view["post_role_integration_required"] = True
    view["release_pass_badge_allowed"] = False
    view["context_row_hashes"] = [
        {
            "objection_id": row.get("objection_id", f"row-{index}"),
            "source": row.get("source"),
            "row_hash": canonical_sha256(row),
        }
        for index, row in enumerate(compacted_rows)
    ]
    view["context_view_sha256"] = canonical_sha256({k: v for k, v in view.items() if k != "context_view_sha256"})
    view_path = CONTEXT_DIR / role / ref
    view_path.parent.mkdir(parents=True, exist_ok=True)
    view_path.write_text(json.dumps(view, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return view_path.resolve().relative_to(ROOT.resolve()).as_posix()


def role_context_refs(role: str) -> list[str]:
    return [fresh_context_ref(role, ref) for ref in ROLE_CONTEXT_REFS.get(role, CONTEXT_REFS)]


def main() -> int:
    parser = argparse.ArgumentParser(description="Run OC Core 1.3.3 v12 Cerberus review roles.")
    parser.add_argument("--roles", default="", help="Comma-separated role names. Empty means all roles.")
    parser.add_argument("--max-workers", type=int, default=1, help="Parallel role workers.")
    parser.add_argument("--role-timeout", type=int, default=420, help="Per-role Codex CLI timeout seconds.")
    args = parser.parse_args()
    roles = selected_roles(args.roles)
    max_workers = max(1, min(int(args.max_workers), len(roles) or 1))
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    PROMPT_DIR.mkdir(parents=True, exist_ok=True)
    LAST_DIR.mkdir(parents=True, exist_ok=True)
    result_refs = []
    parse_failures = []
    execution_bad = []
    critical_total = 0
    high_total = 0

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = {pool.submit(run_role, role, int(args.role_timeout)): role for role in roles}
        for future in concurrent.futures.as_completed(futures):
            role_for_future = futures[future]
            try:
                result = future.result()
            except Exception as exc:
                result_path = RESULT_DIR / f"{role_for_future}.json"
                payload = {
                    "schema_id": "OC133_LLM_CERBERUS_RESULT_v12",
                    "role": role_for_future,
                    "execution_status": "RUNNER_EXCEPTION",
                    "critical_open_total": 1,
                    "high_open_total": 0,
                    "finding_total": 1,
                    "findings": [
                        {
                            "severity": "CRITICAL",
                            "artifact_ref": "tools/run_oc133_v12_cerberus.py",
                            "claim": "LLM adversarial review runner must not leave stale role results.",
                            "failure_mode": repr(exc),
                            "required_repair": "Fix runner exception handling and rerun the role.",
                            "status": "OPEN",
                        }
                    ],
                }
                result_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
                result = {
                    "role": role_for_future,
                    "payload": payload,
                    "result_ref": result_path.resolve().relative_to(ROOT.resolve()).as_posix(),
                    "parse_failed": False,
                    "execution_failed": True,
                }
            role = result["role"]
            payload = result["payload"]
            result_refs.append(result["result_ref"])
            if result["parse_failed"] or result["execution_failed"]:
                parse_failures.append(role)
            if payload.get("execution_status") != "EXECUTED":
                execution_bad.append(role)
            critical_total += int(payload.get("critical_open_total", 0))
            high_total += int(payload.get("high_open_total", 0))
    aggregate_refs = []
    pending_roles = []
    critical_total = 0
    high_total = 0
    parse_failures = []
    execution_bad = []
    for role in ROLES:
        result_path = RESULT_DIR / f"{role}.json"
        if not result_path.exists():
            pending_roles.append(role)
            continue
        aggregate_refs.append(result_path.resolve().relative_to(ROOT.resolve()).as_posix())
        payload = json.loads(result_path.read_text(encoding="utf-8"))
        critical_total += int(payload.get("critical_open_total", 0))
        high_total += int(payload.get("high_open_total", 0))
        if payload.get("execution_status") in {"PARSE_FAILED", "EXECUTION_FAILED", "EXECUTION_TIMEOUT", "RUNNER_EXCEPTION"}:
            parse_failures.append(role)
        if payload.get("execution_status") != "EXECUTED":
            execution_bad.append(role)

    role_context_refs_by_role = {role: existing_role_context_refs(role) for role in ROLES}
    prompt_hashes = artifact_hash_map(
        [
            (PROMPT_DIR / f"{role}.txt").resolve().relative_to(ROOT.resolve()).as_posix()
            for role in ROLES
        ]
    )
    raw_output_hashes = artifact_hash_map(
        [
            (LAST_DIR / f"{role}.txt").resolve().relative_to(ROOT.resolve()).as_posix()
            for role in ROLES
        ]
    )
    result_hashes = artifact_hash_map(aggregate_refs)
    summary = {
        "schema_id": "OC133_LLM_CERBERUS_SUMMARY_v12",
        "release_id": "oc_core_1_3_3",
        "version": "1.3.3",
        "roles": ROLES,
        "executed_roles_this_run": roles,
        "role_total": len(ROLES),
        "configured_role_total": len(ROLES),
        "max_workers": max_workers,
        "execution_status": "EXECUTED_WITH_FINDINGS_CLOSED" if critical_total == 0 and high_total == 0 and not parse_failures and not pending_roles and not execution_bad else "EXECUTED_WITH_OPEN_FINDINGS",
        "critical_open_total": critical_total,
        "high_open_total": high_total,
        "parse_failure_total": len(parse_failures),
        "parse_failures": parse_failures,
        "execution_bad_total": len(execution_bad),
        "execution_bad_roles": execution_bad,
        "pending_role_total": len(pending_roles),
        "pending_roles": pending_roles,
        "result_refs": aggregate_refs,
        "result_refs_this_run": result_refs,
        "freshness_hash_binding_policy": (
            "G58 summary is bound to current role context files, current release-critical input artifacts, "
            "generated prompts, raw role outputs, and normalized result JSON files. These hashes are audit "
            "bindings only; critical/high open-finding counters remain authoritative for pass/block semantics."
        ),
        "role_context_refs": role_context_refs_by_role,
        "role_context_hashes": {
            role: artifacts_manifest_hash(refs)
            for role, refs in role_context_refs_by_role.items()
        },
        "role_context_artifact_hashes": {
            role: artifact_hash_map(refs)
            for role, refs in role_context_refs_by_role.items()
        },
        "input_artifact_hashes": artifact_hash_map(G58_INPUT_REFS),
        "prompt_hashes": prompt_hashes,
        "raw_output_hashes": raw_output_hashes,
        "result_hashes": result_hashes,
        "g58_frontier_refs": G58_FRONTIER_REFS,
        "g58_frontier_hash": g58_frontier_hash(),
    }
    (ROOT / "reviews" / "oc133_llm_cerberus" / "OC133_LLM_CERBERUS_SUMMARY.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if summary["execution_status"] == "EXECUTED_WITH_FINDINGS_CLOSED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
