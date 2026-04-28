from __future__ import annotations

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
    "formal/lean/OC133V12.lean",
    "validation/numeric_predictions/OC133_NUMERIC_PREDICTION_TABLE.json",
    "comparators/OC_1_3_3_NOVELTY_AND_PRIORITY_REGISTER.json",
    "docs/OC_1_3_3_PHENOMENON_COVERAGE_MATRIX.json",
    "review/OC_1_3_3_TOTAL_ATTACK_MATRIX.json",
    "releases/oc_core_1_3_3/editorial/OC_CORE_1_3_3_PUBLISH_MANIFEST_DRAFT.json",
]


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
    return f"""You are the OC Core 1.3.3 v12 adversarial reviewer role `{role}`.

Work read-only. Inspect only these release-critical artifacts unless a directly referenced file is needed:
{refs}

Attack the release hard. Focus on unsupported critical/high claims, theorem theater, empirical theater,
prior-art relabeling, phenomenon coverage gaps, no-send violations, and absolute TOE overclaims.

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


def main() -> int:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    PROMPT_DIR.mkdir(parents=True, exist_ok=True)
    LAST_DIR.mkdir(parents=True, exist_ok=True)
    result_refs = []
    parse_failures = []
    critical_total = 0
    high_total = 0
    for role in ROLES:
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
        completed = subprocess.run(cmd, input=prompt, cwd=ROOT, text=True, capture_output=True, timeout=420)
        result_path = RESULT_DIR / f"{role}.json"
        result_refs.append(result_path.resolve().relative_to(ROOT.resolve()).as_posix())
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
            parse_failures.append(role)
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
                parse_failures.append(role)
        critical_total += int(payload.get("critical_open_total", 0))
        high_total += int(payload.get("high_open_total", 0))
        result_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    summary = {
        "schema_id": "OC133_LLM_CERBERUS_SUMMARY_v12",
        "release_id": "oc_core_1_3_3",
        "version": "1.3.3",
        "roles": ROLES,
        "role_total": len(ROLES),
        "execution_status": "EXECUTED_WITH_FINDINGS_CLOSED" if critical_total == 0 and high_total == 0 and not parse_failures else "EXECUTED_WITH_OPEN_FINDINGS",
        "critical_open_total": critical_total,
        "high_open_total": high_total,
        "parse_failure_total": len(parse_failures),
        "parse_failures": parse_failures,
        "pending_role_total": 0,
        "pending_roles": [],
        "result_refs": result_refs,
    }
    (ROOT / "reviews" / "oc133_llm_cerberus" / "OC133_LLM_CERBERUS_SUMMARY.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if summary["execution_status"] == "EXECUTED_WITH_FINDINGS_CLOSED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
