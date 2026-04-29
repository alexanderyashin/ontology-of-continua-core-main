from __future__ import annotations

import json
import re
import runpy
import contextlib
import io
from pathlib import Path
from typing import Any, Callable


RELEASE_ID = "oc_core_1_3_3"
VERSION = "1.3.3"

REQUIRED_LLM_ROLES = {
    "formal_mathematician",
    "dynamical_systems_reviewer",
    "category_type_theory_reviewer",
    "empirical_statistician",
    "prior_art_historian",
    "hostile_journal_reviewer",
    "not_novel_attacker",
    "phenomenon_x_attacker",
    "clarity_didactic_reviewer",
}

PROOF_HEADINGS = [
    "## Assumptions",
    "## Definitions",
    "## Lemma 1",
    "## Lemma 2",
    "## Theorem",
    "## Proof",
    "## Counterexample Boundary",
    "## Machine-Checkable Finite Example",
    "## Dependency Refs",
    "## Reviewer Attack Answered",
]

PUBLIC_SCAN_GLOBS = [
    "claims/*1_3_3*",
    "reports/OC_CORE_1_3_3_CLAIM_PROMOTION_REPORT.md",
    "reports/OC_CORE_1_3_3_SCIENTIFIC_CLOSURE_REPORT.md",
    "reports/OC_CORE_1_3_3_THEOREM_CLOSURE_REPORT.md",
    "releases/oc_core_1_3_3/README.md",
    "releases/oc_core_1_3_3/editorial/OC_CORE_1_3_3_PUBLISH_MANIFEST_DRAFT.json",
    "appendix/OC_1_3_3_*.tex",
    "content/OC_1_3_3_*.tex",
    "proofs/THEOREM_REGISTRY_1_3_3.*",
]

FORBIDDEN_OVERCLAIM_PATTERNS = [
    ("absolute_100_percent", re.compile(r"\b100\s*%\b|\b100 percent\b", re.IGNORECASE)),
    ("irrefutable", re.compile(r"\birrefutable\b|\bunrefutable\b|\bнеопроверж", re.IGNORECASE)),
    ("unfalsifiable", re.compile(r"\bunfalsifiable\b", re.IGNORECASE)),
    ("final_theory", re.compile(r"\bfinal theory\b|\bокончательн[а-я]*\s+теори", re.IGNORECASE)),
    ("toe_complete", re.compile(r"\bTOE[-\s]?complete\b|\btheory of everything\b", re.IGNORECASE)),
    ("all_domain_numeric_prediction", re.compile(r"\ball[-\s]?domain numerical prediction\b|\ball domains?[^.\n]{0,80}\bnumerical prediction", re.IGNORECASE)),
    ("proves_everything", re.compile(r"\bproves?\s+(?:all|everything|every phenomenon)\b", re.IGNORECASE)),
    ("complete_truth", re.compile(r"\bcomplete truth\b|\bfinal truth\b|\bоднозначно\s+правдив", re.IGNORECASE)),
]

NEGATION_CUES = (
    "not ",
    "no ",
    "does not ",
    "do not ",
    "must not ",
    "forbidden",
    "blocked",
    "reject",
    "unsupported",
    "не ",
    "нельзя",
    "запрещ",
)


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not text.endswith("\n"):
        text += "\n"
    path.write_text(text, encoding="utf-8")


def rel(root: Path, path: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore") if path.exists() else ""


def ensure_hardened(root: Path) -> None:
    required = [
        root / "docs" / "OC_1_3_3_HOSTILE_READER_GUIDE.md",
        root / "docs" / "OC_1_3_3_PRIOR_ART_COMPARATOR_MATRIX.json",
        root / "docs" / "OC_1_3_3_PHENOMENON_COVERAGE_MATRIX.json",
        root / "validation" / "numeric_predictions" / "OC133_NUMERIC_PREDICTION_TABLE.json",
        root / "reviews" / "oc133_llm_cerberus" / "OC133_LLM_CERBERUS_SUMMARY.json",
        root / "reports" / "OC_CORE_1_3_3_HOSTILE_HARDENING_REPORT.json",
    ]
    proof_dir = root / "proofs" / "proof_sheets"
    proof_ready = proof_dir.exists() and all(path.stat().st_size > 1200 for path in proof_dir.glob("T133-*.md"))
    if all(path.exists() for path in required) and proof_ready:
        return
    script = root / "tools" / "harden_oc_core_1_3_3_release.py"
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            runpy.run_path(str(script), run_name="__main__")
    except SystemExit as exc:
        if int(exc.code or 0) != 0:
            raise


def _required_field_total(rows: list[dict[str, Any]], fields: set[str]) -> int:
    return sum(1 for row in rows if all(row.get(field) not in (None, "", []) for field in fields))


def red_team_concreteness_audit(root: Path) -> dict[str, Any]:
    path = root / "reviews" / "OC_CORE_1_3_3_REVIEWER_RESPONSE_MATRIX.json"
    if not path.exists():
        return {"state": "FAIL", "missing": True, "generic_row_total": 999, "complete_row_total": 0}
    payload = read_json(path)
    rows = payload.get("rows", [])
    required = {"attacked_claim", "artifact_location", "failure_mode", "required_repair", "closure_evidence"}
    generic_rows = [
        row.get("objection_id")
        for row in rows
        if "Hostile reviewer attack" in str(row.get("objection", ""))
        or str(row.get("source_location", "")).strip() == "OC Core 1.3.3 scientific closure package"
    ]
    critical_open = [row for row in rows if row.get("severity") == "CRITICAL" and not str(row.get("status", "")).startswith("CLOSED")]
    high_open = [row for row in rows if row.get("severity") == "HIGH" and not str(row.get("status", "")).startswith("CLOSED")]
    complete_row_total = _required_field_total(rows, required)
    ok = (
        len(rows) >= 100
        and not generic_rows
        and not critical_open
        and not high_open
        and complete_row_total == len(rows)
        and payload.get("critical_unresolved_total") == 0
        and payload.get("high_unresolved_total") == 0
    )
    return {
        "state": "PASS" if ok else "FAIL",
        "objection_total": len(rows),
        "complete_row_total": complete_row_total,
        "generic_row_total": len(generic_rows),
        "generic_rows": generic_rows[:20],
        "critical_open_total": len(critical_open),
        "high_open_total": len(high_open),
    }


def llm_adversarial_audit(root: Path) -> dict[str, Any]:
    summary_path = root / "reviews" / "oc133_llm_cerberus" / "OC133_LLM_CERBERUS_SUMMARY.json"
    if not summary_path.exists():
        return {
            "state": "BLOCKED",
            "execution_status": "MISSING_SUMMARY",
            "role_total": 0,
            "missing_roles": sorted(REQUIRED_LLM_ROLES),
            "critical_open_total": 0,
            "high_open_total": 0,
        }
    payload = read_json(summary_path)
    roles = set(payload.get("roles", []))
    missing_roles = sorted(REQUIRED_LLM_ROLES - roles)
    execution_ok = payload.get("execution_status") in {"EXECUTED", "EXECUTED_WITH_FINDINGS_CLOSED"}
    open_critical = int(payload.get("critical_open_total", 0))
    open_high = int(payload.get("high_open_total", 0))
    parse_failures = int(payload.get("parse_failure_total", 0))
    ok = execution_ok and not missing_roles and open_critical == 0 and open_high == 0 and parse_failures == 0
    return {
        "state": "PASS" if ok else "BLOCKED",
        "execution_status": payload.get("execution_status"),
        "role_total": len(roles),
        "missing_roles": missing_roles,
        "critical_open_total": open_critical,
        "high_open_total": open_high,
        "parse_failure_total": parse_failures,
        "result_refs": payload.get("result_refs", []),
    }


def proof_depth_audit(root: Path) -> dict[str, Any]:
    registry_path = root / "proofs" / "THEOREM_REGISTRY_1_3_3.json"
    if not registry_path.exists():
        return {"state": "FAIL", "missing_registry": True}
    registry = read_json(registry_path)
    failures: list[dict[str, Any]] = []
    sheets_seen = 0
    for row in registry.get("rows", []):
        theorem_id = row.get("theorem_id")
        sheet = root / "proofs" / "proof_sheets" / f"{theorem_id}.md"
        text = _text(sheet)
        missing = [heading for heading in PROOF_HEADINGS if heading not in text]
        sketch_terms = []
        for term in ["TODO", "placeholder", "proof sketch", "route only"]:
            if term.lower() in text.lower():
                sketch_terms.append(term)
        lemma_chain_ok = "## Lemma 1" in text and "## Lemma 2" in text and "## Proof" in text
        by_definition_only = "by definition" in text.lower() and not lemma_chain_ok
        if sheet.exists():
            sheets_seen += 1
        if missing or sketch_terms or by_definition_only or len(text) < 1400:
            failures.append({
                "theorem_id": theorem_id,
                "path": rel(root, sheet),
                "missing_headings": missing,
                "sketch_terms": sketch_terms,
                "by_definition_only": by_definition_only,
                "char_count": len(text),
            })
    finite = root / "proofs" / "FINITE_MODEL_CHECKS_1_3_3.json"
    finite_payload = read_json(finite) if finite.exists() else {}
    finite_ok = finite_payload.get("failure_total") == 0 and finite_payload.get("case_total", 0) >= len(registry.get("rows", []))
    ok = not failures and finite_ok and sheets_seen == registry.get("theorem_total")
    return {
        "state": "PASS" if ok else "FAIL",
        "theorem_total": registry.get("theorem_total"),
        "proof_sheet_total": sheets_seen,
        "failure_total": len(failures),
        "failures": failures,
        "finite_model_case_total": finite_payload.get("case_total", 0),
        "finite_model_failure_total": finite_payload.get("failure_total", 999),
    }


def empirical_numeric_audit(root: Path) -> dict[str, Any]:
    path = root / "validation" / "numeric_predictions" / "OC133_NUMERIC_PREDICTION_TABLE.json"
    if not path.exists():
        return {"state": "FAIL", "missing": True}
    payload = read_json(path)
    rows = payload.get("rows", [])
    required = {
        "lane",
        "claim_id",
        "replay_rule",
        "dataset_snapshot_ref",
        "split_policy",
        "replay_value",
        "observed_value",
        "uncertainty",
        "baseline_control_value",
        "residual",
        "negative_control",
        "falsifier",
        "promotion_status",
    }
    incomplete = [row.get("claim_id") for row in rows if not all(key in row for key in required)]
    promoted_without_numeric = [
        row.get("claim_id")
        for row in rows
        if str(row.get("promotion_status", "")).startswith("PROMOTED")
        and (row.get("replay_value") is None or row.get("observed_value") is None)
    ]
    fake_pass = [
        row.get("claim_id")
        for row in rows
        if row.get("promotion_status") == "PASS"
        and row.get("numeric_replay") is not True
    ]
    lane_total = len({row.get("lane") for row in rows})
    ok = (
        lane_total >= 5
        and len(rows) >= 5
        and not incomplete
        and not promoted_without_numeric
        and not fake_pass
        and payload.get("unsupported_promoted_total") == 0
    )
    return {
        "state": "PASS" if ok else "FAIL",
        "lane_total": lane_total,
        "row_total": len(rows),
        "incomplete_total": len(incomplete),
        "incomplete_claims": incomplete,
        "promoted_without_numeric_total": len(promoted_without_numeric),
        "promoted_without_numeric_claims": promoted_without_numeric,
        "fake_pass_total": len(fake_pass),
        "unsupported_promoted_total": payload.get("unsupported_promoted_total"),
        "blocked_for_promotion_total": payload.get("blocked_for_promotion_total", 0),
    }


def novelty_competitor_audit(root: Path) -> dict[str, Any]:
    path = root / "docs" / "OC_1_3_3_PRIOR_ART_COMPARATOR_MATRIX.json"
    if not path.exists():
        return {"state": "FAIL", "missing": True}
    payload = read_json(path)
    rows = payload.get("rows", [])
    required = {"tradition", "source_refs", "prior_art_has", "bounded_positioning_note", "what_oc_must_not_claim", "uniqueness_claim_status"}
    complete = _required_field_total(rows, required)
    unsupported = [
        row.get("tradition")
        for row in rows
        if row.get("uniqueness_claim_status") in {"UNSUPPORTED", "PROMOTED_AS_ABSOLUTE"}
    ]
    ok = len(rows) >= 8 and complete == len(rows) and not unsupported and payload.get("unsupported_uniqueness_total") == 0
    return {
        "state": "PASS" if ok else "FAIL",
        "row_total": len(rows),
        "complete_row_total": complete,
        "unsupported_uniqueness_total": len(unsupported),
        "unsupported_uniqueness_rows": unsupported,
    }


def phenomenon_coverage_audit(root: Path) -> dict[str, Any]:
    path = root / "docs" / "OC_1_3_3_PHENOMENON_COVERAGE_MATRIX.json"
    if not path.exists():
        return {"state": "FAIL", "missing": True}
    payload = read_json(path)
    rows = payload.get("rows", [])
    required = {"phenomenon_id", "hostile_question", "claim_boundary", "oc_explanation_route", "evidence_refs", "prediction_status", "falsifier", "limitation"}
    complete = _required_field_total(rows, required)
    unsupported_closed = [
        row.get("phenomenon_id")
        for row in rows
        if row.get("explanation_status") == "CLOSED"
        and not row.get("evidence_refs")
    ]
    ok = len(rows) >= 12 and complete == len(rows) and not unsupported_closed and payload.get("unsupported_closed_total") == 0
    return {
        "state": "PASS" if ok else "FAIL",
        "row_total": len(rows),
        "complete_row_total": complete,
        "unsupported_closed_total": len(unsupported_closed),
        "unsupported_closed_rows": unsupported_closed,
    }


def didactic_hostile_reader_audit(root: Path) -> dict[str, Any]:
    path = root / "docs" / "OC_1_3_3_HOSTILE_READER_GUIDE.md"
    text = _text(path)
    required_phrases = [
        "Tuple",
        "Theorem path",
        "Example path",
        "Falsifier path",
        "What OC does not yet explain",
        "minimal prerequisites",
        "liveness",
        "death",
        "residue",
        "K0 resolution",
        "boundaries",
        "operators",
        "prediction limits",
    ]
    missing = [phrase for phrase in required_phrases if phrase.lower() not in text.lower()]
    ok = path.exists() and not missing and len(text) >= 5000
    return {
        "state": "PASS" if ok else "FAIL",
        "path": rel(root, path),
        "char_count": len(text),
        "missing_phrases": missing,
    }


def _context_window(text: str, start: int, end: int, radius: int = 90) -> str:
    return text[max(0, start - radius): min(len(text), end + radius)].replace("\n", " ")


def _is_negated_context(context: str) -> bool:
    lowered = context.lower()
    return any(cue in lowered for cue in NEGATION_CUES)


def absolute_overclaim_audit(root: Path) -> dict[str, Any]:
    hits: list[dict[str, Any]] = []
    seen_paths: set[Path] = set()
    for pattern in PUBLIC_SCAN_GLOBS:
        for path in root.glob(pattern):
            if not path.is_file() or path in seen_paths:
                continue
            seen_paths.add(path)
            text = _text(path)
            for tag, regex in FORBIDDEN_OVERCLAIM_PATTERNS:
                for match in regex.finditer(text):
                    context = _context_window(text, match.start(), match.end())
                    if _is_negated_context(context):
                        continue
                    hits.append({
                        "path": rel(root, path),
                        "pattern": tag,
                        "match": match.group(0),
                        "context": context[:220],
                    })
    return {
        "state": "PASS" if not hits else "FAIL",
        "hit_total": len(hits),
        "hits": hits[:50],
        "scanned_file_total": len(seen_paths),
    }


def run_hardening_audits(root: Path) -> dict[str, Any]:
    return {
        "schema_id": "OC133_HOSTILE_HARDENING_AUDIT_v1",
        "release_id": RELEASE_ID,
        "version": VERSION,
        "red_team_concreteness": red_team_concreteness_audit(root),
        "llm_adversarial_review": llm_adversarial_audit(root),
        "proof_depth": proof_depth_audit(root),
        "empirical_numeric_prediction": empirical_numeric_audit(root),
        "novelty_competitor": novelty_competitor_audit(root),
        "phenomenon_coverage": phenomenon_coverage_audit(root),
        "hostile_reader_didactics": didactic_hostile_reader_audit(root),
        "absolute_toe_overclaim": absolute_overclaim_audit(root),
    }


def write_hardening_report(root: Path, audits: dict[str, Any]) -> None:
    gates = [
        audits["llm_adversarial_review"],
        audits["proof_depth"],
        audits["empirical_numeric_prediction"],
        audits["novelty_competitor"],
        audits["phenomenon_coverage"],
        audits["hostile_reader_didactics"],
        audits["absolute_toe_overclaim"],
    ]
    summary = {
        "schema_id": "OC133_HOSTILE_HARDENING_REPORT_v1",
        "release_id": RELEASE_ID,
        "version": VERSION,
        "gate_total": len(gates),
        "pass_total": sum(1 for row in gates if row.get("state") == "PASS"),
        "fail_total": sum(1 for row in gates if row.get("state") == "FAIL"),
        "blocked_total": sum(1 for row in gates if row.get("state") == "BLOCKED"),
        "red_team_concreteness_state": audits["red_team_concreteness"]["state"],
        "no_send": True,
        "publish_allowed": False,
        "journal_submissions_allowed": False,
        "audits": audits,
    }
    write_json(root / "reports" / "OC_CORE_1_3_3_HOSTILE_HARDENING_REPORT.json", summary)
    lines = [
        "# OC Core 1.3.3 Hostile Hardening Report",
        "",
        f"Pass: `{summary['pass_total']}`",
        f"Fail: `{summary['fail_total']}`",
        f"Blocked: `{summary['blocked_total']}`",
        f"Red-team concreteness: `{summary['red_team_concreteness_state']}`",
        "",
        "| Audit | State | Key evidence |",
        "| --- | --- | --- |",
    ]
    for key in [
        "llm_adversarial_review",
        "proof_depth",
        "empirical_numeric_prediction",
        "novelty_competitor",
        "phenomenon_coverage",
        "hostile_reader_didactics",
        "absolute_toe_overclaim",
    ]:
        audit = audits[key]
        evidence = ", ".join(f"{k}={v}" for k, v in audit.items() if k.endswith("_total") or k in {"role_total", "row_total", "hit_total"})
        lines.append(f"| `{key}` | `{audit['state']}` | {evidence} |")
    write_text(root / "reports" / "OC_CORE_1_3_3_HOSTILE_HARDENING_REPORT.md", "\n".join(lines))


def hardening_gate_results(root: Path, gate_fn: Callable[[str, str, str, str, str, dict[str, Any] | None], dict[str, Any]]) -> list[dict[str, Any]]:
    audits = run_hardening_audits(root)
    write_hardening_report(root, audits)
    specs = [
        ("G46", "llm_adversarial_review", "CRITICAL", audits["llm_adversarial_review"], "CLI Cerberus review must execute for all adversarial roles and leave zero open critical/high findings."),
        ("G47", "proof_depth", "CRITICAL", audits["proof_depth"], "Promoted theorems require full proof sheets with assumptions, definitions, lemmas, proof, boundaries, dependencies, and finite examples."),
        ("G48", "empirical_numeric_prediction", "CRITICAL", audits["empirical_numeric_prediction"], "Empirical promotion requires numeric replay rows; official snapshots alone cannot pass as prediction closure."),
        ("G49", "novelty_competitor", "HIGH", audits["novelty_competitor"], "Novelty claims must be bounded against prior art and must reject absolute uniqueness language."),
        ("G50", "phenomenon_coverage", "HIGH", audits["phenomenon_coverage"], "Coverage claims must name the phenomenon, route, evidence, falsifier, and limitation."),
        ("G51", "hostile_reader_didactics", "HIGH", audits["hostile_reader_didactics"], "A hostile reader must be able to follow tuple to theorem to example to falsifier without hidden prerequisites."),
        ("G52", "absolute_toe_overclaim", "CRITICAL", audits["absolute_toe_overclaim"], "Public 1.3.3 claims must not contain unsupported final-truth, irrefutability, or all-domain numeric prediction language."),
    ]
    rows = []
    for gate_id, name, severity, audit, summary in specs:
        state = audit["state"]
        rows.append(gate_fn(gate_id, name, state, severity, summary, audit))
    return rows
