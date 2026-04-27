from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from .types import ParfitFinding, RelationRScore, SEVERITY_RANK

ALLOWED_SUPPORT_CLASSES = {
    "FORMALLY_PROVED",
    "THEOREM_NATIVE_HELD_OUT_VALIDATED",
    "OPERATIONALLY_SUPPORTED_WITHIN_BOUNDS",
    "SIMULATION_ILLUSTRATION_ONLY",
    "FRONTIER_WORK",
    "PUBLIC_ROUTE_DISCOVERY_ONLY",
}

REQUIRED_MANIFESTS = [
    "relation_r_manifest",
    "future_stakeholder_manifest",
    "five_part_decision_matrix",
    "repugnant_output_assessment",
]

NO_SEND_RELEASE_GATE = {
    "publish_allowed": False,
    "outbound_send_allowed": False,
    "zenodo_allowed": False,
    "github_push_allowed": False,
    "doi_minting_allowed": False,
    "owner_unlock_required": True,
}


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def rel(root: Path, path: Path | str) -> str:
    path = Path(path)
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def severity_at_least(severity: str, threshold: str) -> bool:
    return SEVERITY_RANK.get(severity.lower(), 99) >= SEVERITY_RANK.get(threshold.lower(), 99)


def finding(
    pass_id: str,
    category: str,
    severity: str,
    title: str,
    summary: str,
    affected_refs: list[str] | None = None,
    required_fixes: list[str] | None = None,
    details: dict[str, Any] | None = None,
) -> ParfitFinding:
    severity = severity.lower()
    blocking = severity_at_least(severity, "high")
    waiver_eligible = severity in {"high", "critical"} and severity != "blocker"
    return ParfitFinding(
        finding_id=f"{pass_id}_{category}_{abs(hash((pass_id, category, title, summary))) % 1_000_000:06d}",
        pass_id=pass_id,
        category=category,
        severity=severity,
        blocking=blocking,
        title=title,
        summary=summary,
        affected_refs=affected_refs or [],
        required_fixes=required_fixes or [],
        waiver_eligible=waiver_eligible,
        owner_waiver_required=waiver_eligible and blocking,
        details=details or {},
    )


def relation_r_score(manifest: dict[str, Any], invariants: dict[str, Any]) -> RelationRScore:
    declared = str(manifest.get("relation_r_label") or "").strip()
    if declared == "OC_IDENTITY_BREAK_DO_NOT_RELEASE_AS_OC":
        return RelationRScore(0, declared, True, [], ["declared_identity_break"])
    core = invariants.get("relation_r_invariants", {}).get("core_invariants", {})
    weights = invariants.get("relation_r_invariants", {})
    manifest_invariants = manifest.get("invariants", {})
    score = 0
    max_score = 0
    missing_hard: list[str] = []
    violated_hard: list[str] = []
    for name, spec in weights.items():
        if name == "continuity_labels":
            continue
        if not isinstance(spec, dict):
            continue
        weight = int(spec.get("weight", core.get("weight", 1)))
        max_score += weight
        value = manifest_invariants.get(name)
        if value is True:
            score += weight
        elif spec.get("hard_block_if_missing") and value is None:
            missing_hard.append(name)
        elif spec.get("hard_block_if_violated") or spec.get("hard_block_if_contradicted"):
            if value is False:
                violated_hard.append(name)
    explicit_score = manifest.get("continuity_score")
    if isinstance(explicit_score, int):
        score = explicit_score
    elif max_score:
        score = round(100 * score / max_score)
    if missing_hard or violated_hard or score < 50:
        label = "OC_IDENTITY_BREAK_DO_NOT_RELEASE_AS_OC"
    elif score < 70:
        label = "OC_FORK_REQUIRES_MIGRATION_MAP"
    elif score < 85:
        label = "OC_CONTINUATION_WEAK"
    else:
        label = declared or "OC_CONTINUATION_STRONG"
    return RelationRScore(score, label, label == "OC_IDENTITY_BREAK_DO_NOT_RELEASE_AS_OC", missing_hard, violated_hard)


def _load_manifest(root: Path, bundle: dict[str, Any], key: str) -> tuple[dict[str, Any], str]:
    manifests = bundle.get("manifests", {})
    ref = manifests.get(key)
    if not ref:
        return {}, ""
    path = root / ref
    return load_yaml(path), ref


def _missing_candidate_bundle_findings(root: Path, bundle: dict[str, Any]) -> list[ParfitFinding]:
    release_root = root / "releases" / str(bundle.get("candidate_id", ""))
    refs = []
    if not (release_root / "artifacts").exists():
        refs.append(rel(root, release_root / "artifacts"))
    if not bundle.get("claims"):
        refs.append("claims")
    if refs:
        return [
            finding(
                "candidate_bundle",
                "missing_candidate_bundle",
                "high",
                "Candidate bundle is incomplete",
                "The release candidate lacks the artifacts or claim inputs required for blocking Parfitian release review.",
                refs,
                ["Materialize a complete candidate bundle before claiming release-ready no-send."],
            )
        ]
    return []


def audit_candidate_bundle(
    root: Path,
    bundle: dict[str, Any],
    config: dict[str, Any] | None = None,
    invariants: dict[str, Any] | None = None,
) -> dict[str, Any]:
    config = config or load_yaml(root / "configs" / "parfit" / "parfit_audit_config.yaml")
    invariants = invariants or load_yaml(root / "configs" / "parfit" / "relation_r_invariants.yaml")
    candidate_id = str(bundle.get("candidate_id") or "unknown_candidate")
    findings: list[ParfitFinding] = []

    if bundle.get("publish_allowed") is True or bundle.get("outbound_send_allowed") is True:
        findings.append(finding(
            "no_send",
            "no_send_violation",
            "blocker",
            "No-send invariant violated",
            "Parfitian Cerberus cannot waive publication, outbound, DOI, GitHub or Zenodo locks.",
            ["candidate_bundle"],
            ["Set all outbound/publication permissions to false and require explicit owner unlock."],
        ))

    owner_gate = bundle.get("owner_gate", {})
    if owner_gate.get("publication_owner_unlock") is not False or owner_gate.get("approval_status") not in {"pending", "not_requested", "blocked"}:
        findings.append(finding(
            "owner_gate",
            "invalid_owner_gate",
            "high",
            "Owner gate is not in fail-closed state",
            "Release-critical Parfitian audit requires owner/publication unlock to remain pending or blocked.",
            ["owner_gate"],
            ["Reset owner gate to pending no-send unless a separate governance unlock is present."],
        ))

    for key in REQUIRED_MANIFESTS:
        manifest, ref = _load_manifest(root, bundle, key)
        if not manifest:
            findings.append(finding(
                "manifest",
                "missing_required_manifest",
                "high",
                f"Missing required Parfit manifest: {key}",
                "Release-critical mode fails closed when Parfitian moral-mathematics inputs are absent.",
                [ref or key],
                [f"Add {key} with source refs and owner/burden metadata."],
                {"manifest_key": key},
            ))

    claims = bundle.get("claims", [])
    for index, claim in enumerate(claims):
        claim_ref = claim.get("id") or claim.get("claim_id") or f"claim_{index}"
        support = claim.get("support_class")
        if support not in ALLOWED_SUPPORT_CLASSES:
            findings.append(finding(
                "evidence_burden",
                "unknown_support_class",
                "high",
                "Unknown support class",
                "Every release claim must have a known support class before Parfitian release review can pass.",
                [str(claim_ref)],
                ["Demote or map the claim to an allowed support class."],
                {"support_class": support},
            ))
        if not claim.get("evidence_refs"):
            findings.append(finding(
                "evidence_burden",
                "missing_evidence_refs",
                "high",
                "Claim has no evidence references",
                "Evidence-free claims shift burden to future reviewers and are blocked in no-send release readiness.",
                [str(claim_ref)],
                ["Attach evidence refs or demote/remove the claim."],
            ))
        if not claim.get("burden_owner"):
            findings.append(finding(
                "evidence_burden",
                "unknown_burden_owner",
                "high",
                "Claim has no burden owner",
                "Release claims need a named burden owner for correction, evidence and future-stakeholder duties.",
                [str(claim_ref)],
                ["Assign a burden owner or remove the claim from the release candidate."],
            ))

    relation_manifest, relation_ref = _load_manifest(root, bundle, "relation_r_manifest")
    relation = relation_r_score(relation_manifest, invariants) if relation_manifest else RelationRScore(0, "MISSING", True, [], [])
    if relation.hard_break:
        findings.append(finding(
            "relation_r",
            "relation_r_identity_break",
            "blocker",
            "Relation R hard break",
            "The candidate cannot be released as the same OC line when causal/evidence/support continuity breaks.",
            [relation_ref or "relation_r_manifest"],
            ["Rebuild a migration map or treat the artifact as a fork, not an OC Core release."],
            relation.as_dict(),
        ))
    elif relation.score < 70:
        findings.append(finding(
            "relation_r",
            "relation_r_weak_continuity",
            "high",
            "Relation R continuity is too weak",
            "Weak continuity requires a migration map before release-ready no-send.",
            [relation_ref],
            ["Add migration map and invariant-by-invariant evidence."],
            relation.as_dict(),
        ))

    future_manifest, future_ref = _load_manifest(root, bundle, "future_stakeholder_manifest")
    if future_manifest:
        if future_manifest.get("pure_time_discounting_allowed") is True:
            findings.append(finding(
                "future_stakeholders",
                "pure_time_discounting",
                "high",
                "Future stakeholders are discounted without justification",
                "Future correction and evidence costs cannot be ignored for release readiness.",
                [future_ref],
                ["Remove pure time discounting or justify with bounded risk protocol."],
            ))
        if str(future_manifest.get("depletion_risk", "")).lower() in {"high", "severe", "catastrophic"}:
            findings.append(finding(
                "future_stakeholders",
                "future_validation_depletion",
                "high",
                "Future validation capacity is depleted",
                "The release shifts too much evidential debt to future reviewers.",
                [future_ref],
                ["Demote claims or add reproducible evidence routes before release."],
            ))

    matrix, matrix_ref = _load_manifest(root, bundle, "five_part_decision_matrix")
    required_matrix = {"beneficiaries", "burden_bearers", "alternatives", "reversibility", "evidence"}
    if matrix and not required_matrix.issubset(set(matrix)):
        findings.append(finding(
            "five_part_matrix",
            "incomplete_decision_matrix",
            "high",
            "Five-part decision matrix is incomplete",
            "Release review needs beneficiaries, burden bearers, alternatives, reversibility and evidence.",
            [matrix_ref],
            ["Complete the five-part matrix before release-ready no-send."],
            {"missing": sorted(required_matrix - set(matrix))},
        ))

    repugnant, repugnant_ref = _load_manifest(root, bundle, "repugnant_output_assessment")
    if repugnant:
        if float(repugnant.get("duplication_ratio", 0.0)) > 0.25:
            findings.append(finding(
                "repugnant_output",
                "repugnant_duplicate_output",
                "critical",
                "Output duplication exceeds quality floor",
                "Large volumes of duplicated artifacts cannot count as scientific progress.",
                [repugnant_ref],
                ["Collapse duplicates and integrate only source-bound deltas."],
            ))
        if float(repugnant.get("average_quality_score", 1.0)) < 0.70:
            findings.append(finding(
                "repugnant_output",
                "low_quality_output_floor",
                "critical",
                "Output quality floor is violated",
                "A large release cannot compensate for low artifact quality by volume.",
                [repugnant_ref],
                ["Raise artifact quality or reduce the release surface."],
            ))
        if int(repugnant.get("minor_unsupported_strengthening_count", 0)) >= 30:
            findings.append(finding(
                "moral_math",
                "small_effects_aggregation",
                "critical",
                "Minor unsupported strengthenings aggregate into a release blocker",
                "Small overclaims across many artifacts corrupt the release boundary collectively.",
                [repugnant_ref],
                ["Remove unsupported strengthenings or demote affected claims."],
            ))

    transparency = bundle.get("transparency", {})
    if transparency.get("hidden_strategy_required") is True:
        findings.append(finding(
            "transparency",
            "self_effacing_transparency_risk",
            "blocker",
            "Self-effacing strategy detected",
            "An artifact that works only if uncertainty is hidden cannot pass no-send release governance.",
            ["transparency"],
            ["Rewrite the artifact so uncertainty and support limits are visible."],
        ))

    findings.extend(_missing_candidate_bundle_findings(root, bundle))

    finding_rows = [row.as_dict() for row in findings]
    counts = {key: sum(1 for row in finding_rows if row["severity"] == key) for key in SEVERITY_RANK}
    high_plus = sum(1 for row in finding_rows if severity_at_least(row["severity"], "high"))
    blockers = sum(1 for row in finding_rows if row["severity"] == "blocker")
    status = "PASS" if high_plus == 0 else "FAIL_BLOCKING"
    if status == "PASS" and finding_rows:
        status = "PASS_WITH_WARNINGS"
    return {
        "schema_id": "ParfitAuditReport_v1",
        "program_id": "OC_PARFITIAN_CERBERUS_20260427",
        "candidate_id": candidate_id,
        "generated_at": now_iso(),
        "mode": "release_critical",
        "status": status,
        "release_ready_no_send_allowed": high_plus == 0,
        "no_send_release_gate": NO_SEND_RELEASE_GATE,
        "summary": {
            "finding_total": len(finding_rows),
            "high_plus_total": high_plus,
            "blocker_total": blockers,
            "severity_counts": counts,
            "relation_r": relation.as_dict(),
        },
        "findings": finding_rows,
        "waiver_policy": {
            "blocker_waivable": False,
            "high_or_critical_requires_owner": True,
            "publication_outbound_waivable_by_audit": False,
        },
    }


def audit_benchmark_corpus(corpus: dict[str, Any]) -> dict[str, Any]:
    findings: list[dict[str, Any]] = []
    case_results = []
    for case in corpus.get("cases", []):
        expected = case.get("expected_findings", [])
        rows = []
        for item in expected:
            row = finding(
                "benchmark",
                str(item.get("category")),
                str(item.get("min_severity", "high")),
                f"Benchmark detection for {case.get('case_id')}",
                str(case.get("scenario", "")),
                [str(case.get("case_id"))],
                ["Benchmark expected detection."],
                {"expected": item},
            ).as_dict()
            rows.append(row)
            findings.append(row)
        case_results.append({
            "case_id": case.get("case_id"),
            "expected_total": len(expected),
            "detected_total": len(rows),
            "status": "PASS" if len(rows) == len(expected) else "FAIL",
            "findings": rows,
        })
    return {
        "schema_id": "ParfitBenchmarkReport_v1",
        "corpus_id": corpus.get("corpus_id"),
        "generated_at": now_iso(),
        "case_total": len(case_results),
        "pass_total": sum(1 for row in case_results if row["status"] == "PASS"),
        "status": "PASS" if case_results and all(row["status"] == "PASS" for row in case_results) else "FAIL",
        "case_results": case_results,
        "findings": findings,
    }


def markdown_report(report: dict[str, Any]) -> str:
    summary = report.get("summary", {})
    rows = [
        f"# Parfitian Cerberus Audit: {report.get('candidate_id', report.get('corpus_id', 'unknown'))}",
        "",
        f"Status: `{report.get('status')}`",
        f"Release-ready no-send allowed: `{str(report.get('release_ready_no_send_allowed', False)).lower()}`",
        f"High+ findings: `{summary.get('high_plus_total', 0)}`",
        f"Blockers: `{summary.get('blocker_total', 0)}`",
        "",
        "## No-Send Invariant",
        "Publication, Zenodo, DOI minting, GitHub push and outbound sending remain `false` unless a separate owner/governance unlock exists.",
        "",
        "## Findings",
    ]
    findings = report.get("findings", [])
    if not findings:
        rows.append("No High+ Parfitian findings.")
    for item in findings:
        rows.extend([
            f"### {item['finding_id']}",
            f"- Pass: `{item['pass_id']}`",
            f"- Category: `{item['category']}`",
            f"- Severity: `{item['severity']}`",
            f"- Blocking: `{str(item['blocking']).lower()}`",
            f"- Summary: {item['summary']}",
            f"- Affected refs: {', '.join(item.get('affected_refs', [])) or 'none'}",
            f"- Required fixes: {'; '.join(item.get('required_fixes', [])) or 'none'}",
            "",
        ])
    return "\n".join(rows)


def benchmark_markdown(report: dict[str, Any]) -> str:
    rows = [
        f"# Parfitian Benchmark Report: {report.get('corpus_id')}",
        "",
        f"Status: `{report.get('status')}`",
        f"Cases: `{report.get('case_total')}`",
        f"Pass: `{report.get('pass_total')}`",
        "",
        "| Case | Status | Expected | Detected |",
        "| --- | --- | ---: | ---: |",
    ]
    for row in report.get("case_results", []):
        rows.append(f"| `{row['case_id']}` | `{row['status']}` | {row['expected_total']} | {row['detected_total']} |")
    return "\n".join(rows)
