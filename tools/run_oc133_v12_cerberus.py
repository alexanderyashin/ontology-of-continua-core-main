from __future__ import annotations

import argparse
import concurrent.futures
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
    "validation/numeric_predictions/OC133_NUMERIC_PREDICTION_TABLE.json",
    "comparators/OC_1_3_3_NOVELTY_AND_PRIORITY_REGISTER.json",
    "docs/OC_1_3_3_PHENOMENON_COVERAGE_MATRIX.json",
    "review/OC_1_3_3_TOTAL_ATTACK_MATRIX.json",
    "releases/oc_core_1_3_3/editorial/OC_CORE_1_3_3_PUBLISH_MANIFEST_DRAFT.json",
]

ROLE_FOCUS = {
    "formal_mathematician": "Check whether each Lean theorem proves the proposition the public ledger claims, especially minimality, K-level irreducibility, k=0, boundary, and hybrid semantics.",
    "dynamical_systems_reviewer": "Attack universal-dynamics overreach, smoothness assumptions, hybrid guard/reset semantics, and any hidden ODE claim.",
    "category_type_theory_reviewer": "Attack typed-carrier/morphism claims, identity/residue/rebirth separation, and any categorical wording not supported by the Lean subset.",
    "empirical_statistician": "Attack numeric prediction language, heldout/comparator/residual claims, and any empirical PASS based only on official snapshots.",
    "prior_art_historian": "Attack novelty and priority using the exact source-backed comparator rows and their absence tests.",
    "hostile_journal_reviewer": "Attack whether a skeptical journal could reject the package for theorem theater, empirical theater, novelty inflation, or didactic opacity.",
    "not_novel_attacker": "Try to reduce OC to GST, autopoiesis, dynamical systems, category/topos formalisms, RAF, complexity measures, identity theory, systems engineering, hybrid systems, or formal methods.",
    "phenomenon_x_attacker": "Attack the phenomenon coverage model cards: each broad phenomenon must have a specific model, observable, negative control, and falsifier.",
    "clarity_didactic_reviewer": "Attack whether a hostile reader can follow tuple -> theorem -> semantic finite case -> falsifier without author help.",
    "reproducibility_auditor": "Attack whether a clean checkout can regenerate current artifacts without hidden local state or cached .lake files.",
    "theorem_theater_auditor": "Attack any theorem whose Lean/formal/finite evidence is only definitional, circular, or weaker than the promoted claim.",
    "empirical_theater_auditor": "Attack any numeric/validation row that is snapshot replay while being used as empirical prediction support.",
    "claim_boundary_auditor": "Attack absolute TOE/truth/irrefutability/public-promotion overclaims and any claim boundary that relies on wording instead of evidence.",
    "public_surface_auditor": "Attack no-send, owner approval, DOI/public action, local paths, and public-surface parity.",
}


def extract_json(text: str) -> dict[str, Any]:
    stripped = text.strip()
    if stripped.startswith("{"):
        return json.loads(stripped)
    match = re.search(r"\{.*\}", stripped, re.S)
    if not match:
        raise ValueError("No JSON object found")
    return json.loads(match.group(0))


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


def prompt_for(role: str) -> str:
    refs = "\n".join(f"- `{path}`" for path in CONTEXT_REFS)
    focus = ROLE_FOCUS.get(role, "Attack unsupported critical/high release claims.")
    return f"""You are the OC Core 1.3.3 v12 adversarial reviewer role `{role}`.

Work read-only. Inspect only these release-critical artifacts unless a directly referenced file is needed:
{refs}

Role focus: {focus}

Attack the release hard. Focus on unsupported critical/high claims, theorem theater, empirical theater,
prior-art relabeling, phenomenon coverage gaps, no-send violations, and absolute TOE overclaims.
Use the current artifacts exactly. Do not repeat a stale finding unless the current file still contains
the defect after inspection. A valid critical/high finding must cite a current path, attacked claim,
specific failure mode, and specific repair.

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
    prompt = prompt_for(role)
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
        completed = subprocess.run(cmd, input=prompt, cwd=ROOT, text=True, capture_output=True, timeout=timeout_seconds)
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
            critical_total += int(payload.get("critical_open_total", 0))
            high_total += int(payload.get("high_open_total", 0))
    aggregate_refs = []
    pending_roles = []
    critical_total = 0
    high_total = 0
    parse_failures = []
    for role in ROLES:
        result_path = RESULT_DIR / f"{role}.json"
        if not result_path.exists():
            pending_roles.append(role)
            continue
        aggregate_refs.append(result_path.resolve().relative_to(ROOT.resolve()).as_posix())
        payload = json.loads(result_path.read_text(encoding="utf-8"))
        critical_total += int(payload.get("critical_open_total", 0))
        high_total += int(payload.get("high_open_total", 0))
        if payload.get("execution_status") in {"PARSE_FAILED", "EXECUTION_FAILED"}:
            parse_failures.append(role)

    summary = {
        "schema_id": "OC133_LLM_CERBERUS_SUMMARY_v12",
        "release_id": "oc_core_1_3_3",
        "version": "1.3.3",
        "roles": ROLES,
        "executed_roles_this_run": roles,
        "role_total": len(ROLES),
        "configured_role_total": len(ROLES),
        "max_workers": max_workers,
        "execution_status": "EXECUTED_WITH_FINDINGS_CLOSED" if critical_total == 0 and high_total == 0 and not parse_failures and not pending_roles else "EXECUTED_WITH_OPEN_FINDINGS",
        "critical_open_total": critical_total,
        "high_open_total": high_total,
        "parse_failure_total": len(parse_failures),
        "parse_failures": parse_failures,
        "pending_role_total": len(pending_roles),
        "pending_roles": pending_roles,
        "result_refs": aggregate_refs,
        "result_refs_this_run": result_refs,
    }
    (ROOT / "reviews" / "oc133_llm_cerberus" / "OC133_LLM_CERBERUS_SUMMARY.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if summary["execution_status"] == "EXECUTED_WITH_FINDINGS_CLOSED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
