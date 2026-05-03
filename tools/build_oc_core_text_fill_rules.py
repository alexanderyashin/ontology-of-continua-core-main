from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from oc_core_release_assembly_lib import ASSEMBLY_ROOT, artifact_hash, stable_json, validation_result


RULES_DIR = ASSEMBLY_ROOT / "text_fill_rules"
RULES_STATUS = "OC_CORE_TEXT_FILL_RULES_READY"


STANDARD_SOURCES = [
    {
        "source_id": "nature_reporting_data_code_protocols",
        "title": "Nature Communications reporting standards and availability of data, materials, code and protocols",
        "url": "https://www.nature.com/ncomms/editorial-policies/reporting-standards",
        "criteria": ["replicability", "data availability", "code availability", "protocol availability", "transparent restrictions"],
    },
    {
        "source_id": "icmje_recommendations",
        "title": "ICMJE Recommendations",
        "url": "https://www.icmje.org/recommendations/",
        "criteria": ["authorship accountability", "manuscript responsibility", "conflicts", "AI-use boundary", "ethical reporting"],
    },
    {
        "source_id": "top_guidelines",
        "title": "Transparency and Openness Promotion Guidelines",
        "url": "https://incentivizingopen.org/projects2/transparency-and-openness-promotion-top-guidelines/",
        "criteria": ["data transparency", "analytic transparency", "materials transparency", "preregistration where applicable", "replication openness"],
    },
]


def rules_paths() -> dict[str, Path]:
    return {
        "rules_json": RULES_DIR / "OC_CORE_TEXT_FILL_RULES.json",
        "rules_md": RULES_DIR / "OC_CORE_TEXT_FILL_RULES.md",
        "audit_json": RULES_DIR / "OC_CORE_TEXT_FILL_RULES_AUDIT.json",
        "audit_md": RULES_DIR / "OC_CORE_TEXT_FILL_RULES_AUDIT.md",
    }


def build_rules_payload() -> dict[str, Any]:
    rule_groups = [
        {
            "group_id": "positive_node_requirements",
            "rules": [
                "Every generated section must declare audience, purpose, reader payoff, and relation to the surrounding argument.",
                "Every claim-bearing paragraph must bind to a claim boundary and at least one proof, evidence, source, example, or limitation route.",
                "Every artifact must expose source trace and verification rule before it can move to package assembly.",
            ],
        },
        {
            "group_id": "prohibited_generation_patterns",
            "rules": [
                "Do not transform raw ledgers into prose by dumping rows.",
                "Do not emit control-plane, approval-lock, or gate-jargon language into reader-facing artifacts.",
                "Do not emit stale version references, unsupported overclaims, broken links, bad encoding, duplicate boilerplate, or Markdown leakage.",
                "Do not emit a paragraph without reader payoff.",
            ],
        },
        {
            "group_id": "artifact_readiness_predicates",
            "rules": [
                "Title/frontmatter, audience contract, claim boundary, source trace, and artifact role must be present.",
                "A generated artifact must pass forbidden-term, stale-version, local-path, link, encoding, and repeated-boilerplate scans.",
                "A generated artifact must fail closed when required fill status remains not assessed for a promoted claim.",
            ],
        },
    ]
    payload: dict[str, Any] = {
        "schema_id": "OC_CORE_TEXT_FILL_RULES_v1",
        "artifact_kind": "OC_CORE_TEXT_FILL_RULES",
        "body_prose_included": False,
        "status": RULES_STATUS,
        "standard_sources": STANDARD_SOURCES,
        "rule_groups": rule_groups,
    }
    payload["artifact_hash"] = artifact_hash(payload)
    return payload


def validate_rules_payload(payload: dict[str, Any]) -> list[str]:
    failures = []
    if payload.get("status") != RULES_STATUS:
        failures.append("bad_status")
    if len(payload.get("standard_sources", [])) != len(STANDARD_SOURCES):
        failures.append("missing_standard_sources")
    needed = {"positive_node_requirements", "prohibited_generation_patterns", "artifact_readiness_predicates"}
    present = {group.get("group_id") for group in payload.get("rule_groups", [])}
    if not needed.issubset(present):
        failures.append("missing_rule_group")
    text = json.dumps(payload, ensure_ascii=False)
    for phrase in ["raw ledgers", "control-plane", "stale version", "unsupported overclaims", "bad encoding", "reader payoff"]:
        if phrase not in text:
            failures.append(f"missing_required_rule_phrase::{phrase}")
    if payload.get("artifact_hash") != artifact_hash(payload):
        failures.append("artifact_hash_mismatch")
    return failures


def build_audit_payload(rules: dict[str, Any]) -> dict[str, Any]:
    failures = validate_rules_payload(rules)
    payload: dict[str, Any] = {
        "schema_id": "OC_CORE_TEXT_FILL_RULES_AUDIT_v1",
        "artifact_kind": "OC_CORE_TEXT_FILL_RULES_AUDIT",
        "status": "PASS" if not failures else "FAIL",
        "failure_total": len(failures),
        "failures": failures,
        "rules_hash": rules["artifact_hash"],
        "standard_source_total": len(rules["standard_sources"]),
        "rule_group_total": len(rules["rule_groups"]),
    }
    payload["artifact_hash"] = artifact_hash(payload)
    return payload


def render_rules_md(payload: dict[str, Any]) -> str:
    lines = [
        "# OC Core Text Fill Rules",
        "",
        f"Status: `{payload['status']}`",
        f"Artifact hash: `{payload['artifact_hash']}`",
        "",
        "## Standard Sources",
        "",
    ]
    for source in payload["standard_sources"]:
        lines.append(f"- {source['title']}: {source['url']}")
    lines.extend(["", "## Rule Groups", ""])
    for group in payload["rule_groups"]:
        lines.append(f"### {group['group_id']}")
        for rule in group["rules"]:
            lines.append(f"- {rule}")
        lines.append("")
    return "\n".join(lines)


def render_audit_md(payload: dict[str, Any]) -> str:
    lines = [
        "# OC Core Text Fill Rules Audit",
        "",
        f"Status: `{payload['status']}`",
        f"Failures: `{payload['failure_total']}`",
        f"Rules hash: `{payload['rules_hash']}`",
        "",
    ]
    for failure in payload["failures"]:
        lines.append(f"- {failure}")
    return "\n".join(lines)


def expected_files() -> dict[Path, str]:
    rules = build_rules_payload()
    failures = validate_rules_payload(rules)
    if failures:
        raise RuntimeError(f"Text fill rules validation failed: {failures}")
    audit = build_audit_payload(rules)
    paths = rules_paths()
    return {
        paths["rules_json"]: stable_json(rules),
        paths["rules_md"]: render_rules_md(rules),
        paths["audit_json"]: stable_json(audit),
        paths["audit_md"]: render_audit_md(audit),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build generic OC Core text fill rules.")
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    if not args.write and not args.check:
        args.check = True
    result = validation_result(expected_files(), write=args.write)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["state"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
