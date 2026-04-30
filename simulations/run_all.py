from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent
EXPECTED_PATH = ROOT / "expected_simulations.yml"
RESULT_JSON = ROOT / "results" / "OC_CORE_1_3_3_SIMULATION_RESULTS_latest.json"
RESULT_MD = ROOT / "results" / "OC_CORE_1_3_3_SIMULATION_RESULTS_latest.md"
CONTRACT_SCHEMA_ID = "OC133_SIMULATION_CONTRACT_v12"
FORBIDDEN_CONTRACT_TOKEN_PARTS = (
    ("1", "3", "1"),
    ("release", "v11"),
    ("python_seeded", "release", "v11"),
    ("private", "v11"),
    ("private", "delta"),
    ("delta", "ledger"),
)


def load_expected() -> dict[str, Any]:
    return json.loads(EXPECTED_PATH.read_text(encoding="utf-8"))


def sha256_file(path: Path) -> str:
    data = path.read_bytes()
    if path.suffix.lower() in {".py", ".json", ".yml", ".yaml", ".md", ".txt"}:
        data = data.replace(b"\r\n", b"\n")
    return hashlib.sha256(data).hexdigest()


def validate_payload(payload: dict[str, Any], expected: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for key in ["simulation_id", "seed", "trace_points", "stability_score", "boundary_crossed"]:
        if key not in payload:
            errors.append(f"missing key {key}")
    if errors:
        return errors
    if payload["simulation_id"] != expected["simulation_id"]:
        errors.append(f"simulation_id mismatch: {payload['simulation_id']} != {expected['simulation_id']}")
    if payload["seed"] != expected["seed"]:
        errors.append(f"seed mismatch: {payload['seed']} != {expected['seed']}")
    exp = expected["expected"]
    if len(payload["trace_points"]) != exp["trace_points_length"]:
        errors.append(f"trace_points length mismatch: {len(payload['trace_points'])} != {exp['trace_points_length']}")
    if round(float(payload["stability_score"]), 6) != round(float(exp["stability_score"]), 6):
        errors.append(f"stability_score mismatch: {payload['stability_score']} != {exp['stability_score']}")
    if bool(payload["boundary_crossed"]) != bool(exp["boundary_crossed"]):
        errors.append(f"boundary_crossed mismatch: {payload['boundary_crossed']} != {exp['boundary_crossed']}")
    return errors


def validate_contract(contract: dict[str, Any], expected_row: dict[str, Any], expected_manifest: dict[str, Any], contract_text: str) -> list[str]:
    errors: list[str] = []
    if contract.get("schema_id") != CONTRACT_SCHEMA_ID:
        errors.append(f"contract schema_id mismatch: {contract.get('schema_id')} != {CONTRACT_SCHEMA_ID}")
    for key in ["release_id", "version", "simulation_id", "support_ceiling", "validation_claim_allowed"]:
        if key not in contract:
            errors.append(f"contract missing key {key}")
    if contract.get("release_id") != expected_manifest["release_id"]:
        errors.append(f"contract release_id mismatch: {contract.get('release_id')} != {expected_manifest['release_id']}")
    if contract.get("version") != expected_manifest["version"]:
        errors.append(f"contract version mismatch: {contract.get('version')} != {expected_manifest['version']}")
    if contract.get("simulation_id") != expected_row["simulation_id"]:
        errors.append(f"contract simulation_id mismatch: {contract.get('simulation_id')} != {expected_row['simulation_id']}")
    if contract.get("support_ceiling") != expected_manifest["support_ceiling"]:
        errors.append(
            f"contract support_ceiling mismatch: {contract.get('support_ceiling')} != {expected_manifest['support_ceiling']}"
        )
    if contract.get("validation_claim_allowed") is not expected_manifest["validation_claim_allowed"]:
        errors.append("contract validation_claim_allowed mismatch")
    if contract.get("empirical_support_allowed") is not False:
        errors.append("contract empirical_support_allowed must be false")
    if contract.get("prediction_support_allowed") is not False:
        errors.append("contract prediction_support_allowed must be false")
    if contract.get("source_binding") != "public oc_core_1_3_3 v12 no-send release surface":
        errors.append("contract source_binding must bind only to public oc_core_1_3_3 v12 no-send surface")
    if contract.get("paper_or_release_binding") != "OC Core 1.3.3 v12 no-send release package":
        errors.append("contract paper_or_release_binding must target OC Core 1.3.3 v12")
    lower_text = contract_text.lower()
    for parts in FORBIDDEN_CONTRACT_TOKEN_PARTS:
        token = ".".join(parts) if parts == ("1", "3", "1") else "_".join(parts)
        spaced = " ".join(parts)
        if token.lower() in lower_text or spaced.lower() in lower_text:
            errors.append(f"contract contains forbidden stale/private token class: {'/'.join(parts)}")
    return errors


def run() -> dict[str, Any]:
    expected = load_expected()
    timeout = int(expected["timeout_seconds"])
    rows = []
    failures = []
    actual_runners = {path.relative_to(ROOT).as_posix() for path in ROOT.glob("*/run_simulation.py")}
    expected_runners = {row["runner"] for row in expected["simulations"]}
    for missing in sorted(expected_runners - actual_runners):
        failures.append({"runner": missing, "errors": ["expected runner is absent"]})
    for extra in sorted(actual_runners - expected_runners):
        failures.append({"runner": extra, "errors": ["unexpected runner is present"]})
    for row in expected["simulations"]:
        runner = ROOT / row["runner"]
        payload: dict[str, Any] | None = None
        errors: list[str] = []
        if runner.exists():
            contract = runner.with_name("simulation_contract.json")
            if not contract.exists():
                errors.append("simulation_contract.json missing")
                contract_payload = {}
                contract_text = ""
            else:
                contract_text = contract.read_text(encoding="utf-8")
                try:
                    contract_payload = json.loads(contract_text)
                except json.JSONDecodeError as exc:
                    contract_payload = {}
                    errors.append(f"invalid contract json: {exc}")
                if contract_payload:
                    errors.extend(validate_contract(contract_payload, row, expected, contract_text))
            proc = subprocess.run([sys.executable, str(runner), "--seed", str(row["seed"])], cwd=REPO, capture_output=True, text=True, timeout=timeout)
            if proc.returncode != 0:
                errors.append(f"returncode {proc.returncode}")
            try:
                payload = json.loads(proc.stdout)
            except json.JSONDecodeError as exc:
                errors.append(f"invalid json: {exc}")
            if proc.stderr.strip():
                errors.append(f"stderr not empty: {proc.stderr.strip()}")
            if payload is not None:
                errors.extend(validate_payload(payload, row))
        else:
            errors.append("runner missing")
        result = {
            "runner": row["runner"],
            "expected_simulation_id": row["simulation_id"],
            "observed_simulation_id": payload.get("simulation_id") if payload else None,
            "returncode": 0 if not errors else 1,
            "errors": errors,
            "runner_sha256": sha256_file(runner) if runner.exists() else None,
            "contract_ref": runner.with_name("simulation_contract.json").relative_to(ROOT).as_posix() if runner.with_name("simulation_contract.json").exists() else None,
            "contract_sha256": sha256_file(runner.with_name("simulation_contract.json")) if runner.with_name("simulation_contract.json").exists() else None,
            "stdout_json": payload or {},
        }
        rows.append(result)
        if errors:
            failures.append({"runner": row["runner"], "errors": errors})
    report = {
        "release_id": expected["release_id"],
        "version": expected["version"],
        "runner": "simulations/run_all.py",
        "runner_claim": "current OC Core 1.3.3 simulation reproducibility entrypoint",
        "support_ceiling": expected["support_ceiling"],
        "validation_claim_allowed": expected["validation_claim_allowed"],
        "expected_manifest_sha256": sha256_file(EXPECTED_PATH),
        "contract_hash_bound_total": sum(1 for row in rows if row.get("contract_sha256")),
        "expected_total": expected["expected_total"],
        "simulation_total": len(rows),
        "failure_total": len(failures),
        "failures": failures,
        "results": rows,
    }
    return report


def write_report(report: dict[str, Any]) -> None:
    RESULT_JSON.parent.mkdir(parents=True, exist_ok=True)
    RESULT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    lines = [
        "# OC Core 1.3.3 Simulation Results",
        "",
        f"Support ceiling: `{report['support_ceiling']}`",
        f"Validation claim allowed: `{str(report['validation_claim_allowed']).lower()}`",
        f"Expected simulations: `{report['expected_total']}`",
        f"Observed simulations: `{report['simulation_total']}`",
        f"Failure total: `{report['failure_total']}`",
        "",
        "| Runner | Simulation ID | Result |",
        "| --- | --- | --- |",
    ]
    for row in report["results"]:
        state = "PASS" if not row["errors"] else "FAIL"
        lines.append(f"| `{row['runner']}` | `{row['observed_simulation_id']}` | `{state}` |")
    RESULT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write-report", action="store_true")
    args = parser.parse_args()
    report = run()
    if args.write_report:
        write_report(report)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 1 if report["failure_total"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
