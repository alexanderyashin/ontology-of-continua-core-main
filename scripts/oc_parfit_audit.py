from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from release_machine.parfit import (  # noqa: E402
    audit_benchmark_corpus,
    audit_candidate_bundle,
    benchmark_markdown,
    markdown_report,
    severity_at_least,
)


def _load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def _write(path: Path | None, text: str) -> None:
    if path is None:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def _exit_code(report: dict, fail_on: str, advisory: bool) -> int:
    if advisory:
        return 0
    findings = report.get("findings", [])
    if any(row.get("category") == "missing_required_manifest" for row in findings):
        return 3
    if any(row.get("severity") == "blocker" for row in findings):
        return 4
    if any(severity_at_least(str(row.get("severity")), fail_on) for row in findings):
        return 1
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the OC Parfitian Cerberus audit.")
    parser.add_argument("--candidate", type=Path, help="ReleaseCandidateBundle YAML file.")
    parser.add_argument("--benchmark", type=Path, help="Parfitian benchmark corpus YAML file.")
    parser.add_argument("--config", type=Path, default=ROOT / "configs/parfit/parfit_audit_config.yaml")
    parser.add_argument("--format", choices=["json", "md"], default="json")
    parser.add_argument("--out-json", type=Path)
    parser.add_argument("--out-md", type=Path)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--advisory", action="store_true")
    parser.add_argument("--fail-on", default="high", choices=["low", "medium", "high", "critical", "blocker"])
    args = parser.parse_args(argv)

    try:
        if args.benchmark:
            report = audit_benchmark_corpus(_load_yaml(args.benchmark))
            md = benchmark_markdown(report)
            exit_code = 0 if report.get("status") == "PASS" else 1
        elif args.candidate:
            report = audit_candidate_bundle(ROOT, _load_yaml(args.candidate), _load_yaml(args.config))
            md = markdown_report(report)
            exit_code = _exit_code(report, args.fail_on, args.advisory)
        else:
            parser.error("Provide --candidate or --benchmark.")
    except (FileNotFoundError, yaml.YAMLError, json.JSONDecodeError, ValueError) as exc:
        sys.stderr.write(f"Parfit audit configuration/schema error: {exc}\n")
        return 2

    if not args.dry_run:
        _write(args.out_json, json.dumps(report, indent=2, sort_keys=True))
        _write(args.out_md, md)
    if args.format == "md":
        sys.stdout.write(md + "\n")
    else:
        sys.stdout.write(json.dumps(report, indent=2, sort_keys=True) + "\n")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
