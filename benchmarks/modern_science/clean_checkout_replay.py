from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any


GENERATED_ON = "2026-05-01"
SCHEMA_ID = "OC133_MODERN_SCIENCE_CLEAN_TEMP_TREE_REPLAY_v1"
REPLAY_ID = "OC133-MODERN-SCIENCE-CLEAN-TEMP-TREE-STRICT-PACK-REPLAY"

REGISTER_REL = "comparators/OC_1_3_3_MODERN_SCIENCE_SUPERIORITY_REGISTER.json"
LANES_REL = "benchmarks/modern_science/OC133_MODERN_SCIENCE_BENCHMARK_LANES.json"
REPORT_REL = "reports/OC_CORE_1_3_3_MODERN_SCIENCE_SUPERIORITY_REPORT.json"
HELPER_REL = "benchmarks/modern_science/clean_checkout_replay.py"
OUTPUT_REL = "reports/OC_CORE_1_3_3_MODERN_SCIENCE_CLEAN_REPLAY.json"
TEMP_MANIFEST_REL = "reports/OC_CORE_1_3_3_MODERN_SCIENCE_CLEAN_REPLAY_INPUT_MANIFEST.json"
TEMP_VERIFY_REL = "reports/OC_CORE_1_3_3_MODERN_SCIENCE_CLEAN_REPLAY_VERIFY.json"

MINIMUM_N = 20
CURRENT_PACK_REFS = {
    "biology": "validation/heldout/grand_science/biology/target_evidence/biology_target_evidence_candidate_pack.json",
    "chemistry": "validation/heldout/grand_science/chemistry/pubchem_hbond_donor/OC133_CHEMISTRY_PUBCHEM_HBOND_DONOR_CANDIDATE_PACK.json",
    "physics": "validation/heldout/grand_science/physics_chemistry/official_batch/physics_official_batch_candidate_evidence_pack.json",
    "systems": "validation/heldout/grand_science/systems/wdi_population_materiality/OC133_SYSTEMS_WDI_POPULATION_MATERIALITY_CANDIDATE_PACK.json",
}
BASE_INPUT_REFS = (HELPER_REL, REGISTER_REL, LANES_REL, REPORT_REL)
PUBLIC_ACTION_TRUE_KEYS = {
    "email_allowed",
    "journal_submissions_allowed",
    "public_action_allowed",
    "public_outbound_action_allowed",
    "public_release_action_allowed",
    "publish_allowed",
    "push_allowed",
    "registry_write_allowed",
}
PUBLIC_COMMAND_TOKENS = (
    "--execute-network",
    "git push",
    "zenodo",
    "doi",
    "journal",
    "email",
    "smtp",
    "twine upload",
)


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def canonical_json(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":"))


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def sha256_object(payload: Any) -> str:
    return sha256_bytes(canonical_json(payload).encode("utf-8"))


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8", newline="\n")


def as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    return value if isinstance(value, list) else [value]


def ordered_unique(values: list[Any]) -> list[Any]:
    seen: set[str] = set()
    out: list[Any] = []
    for value in values:
        key = canonical_json(value) if isinstance(value, (dict, list)) else str(value)
        if key in seen:
            continue
        seen.add(key)
        out.append(value)
    return out


def rel(root: Path, path: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def collect_source_capsule_refs(register: dict[str, Any]) -> list[str]:
    refs: list[str] = []
    for row in register.get("domain_evidence_matrix", []):
        source_block = row.get("incumbent_modern_science_source", {}) if isinstance(row, dict) else {}
        for source in source_block.get("source_refs", []):
            if isinstance(source, dict) and source.get("local_source_capsule_ref"):
                refs.append(str(source["local_source_capsule_ref"]))
    for row in register.get("rows", []):
        for source in row.get("source_refs", []) if isinstance(row, dict) else []:
            if isinstance(source, dict) and source.get("local_source_capsule_ref"):
                refs.append(str(source["local_source_capsule_ref"]))
    return [str(item) for item in ordered_unique(refs)]


def selected_input_refs(root: Path) -> list[str]:
    register = read_json(root / REGISTER_REL)
    return [
        *BASE_INPUT_REFS,
        *CURRENT_PACK_REFS.values(),
        *collect_source_capsule_refs(register),
    ]


def copy_input_tree(source_root: Path, temp_root: Path, refs: list[str]) -> dict[str, str]:
    hashes: dict[str, str] = {}
    for ref in refs:
        source = (source_root / ref).resolve()
        source.relative_to(source_root.resolve())
        if not source.is_file():
            raise FileNotFoundError(ref)
        target = temp_root / ref
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        hashes[ref] = sha256_file(target)
    return hashes


def tree_refs(root: Path) -> list[str]:
    refs: list[str] = []
    for path in root.rglob("*"):
        if path.is_file():
            refs.append(rel(root, path))
    return sorted(refs)


def command_is_public_action(command: list[str]) -> bool:
    text = " ".join(command).lower()
    return any(token in text for token in PUBLIC_COMMAND_TOKENS)


def pack_source_refs(pack: dict[str, Any]) -> list[str]:
    refs: list[str] = []
    source_separation = pack.get("source_separation", {})
    for key in ("training_sources", "target_sources"):
        refs.extend(str(item) for item in as_list(source_separation.get(key)) if item)
    if source_separation.get("attestation_ref"):
        refs.append(str(source_separation["attestation_ref"]))
    for source_hash in as_list(pack.get("source_hashes")):
        if isinstance(source_hash, dict) and source_hash.get("source_ref"):
            refs.append(str(source_hash["source_ref"]))
    return [str(item) for item in ordered_unique(refs)]


def pack_source_hash_refs(pack: dict[str, Any]) -> list[dict[str, Any]]:
    refs: list[dict[str, Any]] = []
    for source_hash in as_list(pack.get("source_hashes")):
        if isinstance(source_hash, dict):
            refs.append(dict(source_hash))
    for digest in as_list(pack.get("source_separation", {}).get("source_hashes")):
        refs.append({"source_ref": "source_separation.source_hashes", "sha256": digest})
    return refs


def negative_controls_rejected(pack: dict[str, Any]) -> bool:
    controls = as_list(pack.get("negative_controls"))
    return bool(controls) and all(isinstance(control, dict) and control.get("rejected") is True for control in controls)


def strict_pack_predicates(domain: str, pack: dict[str, Any], pack_hash: str, expected_hash: str) -> dict[str, bool]:
    residuals = pack.get("residuals", {})
    comparator = pack.get("comparator_baseline", {})
    source_separation = pack.get("source_separation", {})
    try:
        model_residual = float(residuals.get("model"))
        comparator_residual = float(residuals.get("comparator"))
        margin = float(residuals.get("superiority_margin"))
    except (TypeError, ValueError):
        model_residual = comparator_residual = margin = 0.0
    return {
        "selected_pack_hash_matches_register": bool(expected_hash) and pack_hash == expected_hash,
        "schema_is_strict_grand_empirical": pack.get("schema_id") == "OC133_GRAND_EMPIRICAL_EVIDENCE_v1",
        "domain_matches_pack": pack.get("domain") == domain,
        "minimum_n_met": int(pack.get("n", 0) or 0) >= MINIMUM_N,
        "source_separation_mode_allowed": source_separation.get("mode") in {"prospective", "target_blind"},
        "pre_target_lock_present": source_separation.get("pre_target_lock") is True,
        "target_hidden_until_scoring": source_separation.get("target_hidden_until_scoring") is True,
        "training_and_target_source_refs_present": bool(pack_source_refs(pack)),
        "comparator_baseline_declared": bool(comparator.get("name") and comparator.get("prediction_rule")),
        "comparator_baseline_pre_registered": comparator.get("pre_registered") is True,
        "uncertainty_declared": bool(pack.get("uncertainty", {}).get("metric")) and pack.get("uncertainty", {}).get("interval") is not None,
        "residuals_show_model_beats_declared_comparator": comparator_residual > model_residual and margin > 0.0,
        "negative_controls_rejected": negative_controls_rejected(pack),
        "falsifier_declared": bool(pack.get("falsifiers")),
        "strict_pack_support_allowed": pack.get("grand_toe_support_allowed") is True,
    }


def public_action_true_paths(value: Any, path: str = "$") -> list[str]:
    failures: list[str] = []
    if isinstance(value, dict):
        for key, item in value.items():
            next_path = f"{path}.{key}"
            if key in PUBLIC_ACTION_TRUE_KEYS and item is True:
                failures.append(next_path)
            failures.extend(public_action_true_paths(item, next_path))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            failures.extend(public_action_true_paths(item, f"{path}[{index}]"))
    return failures


def verify_temp_tree(root: Path, manifest_rel: str) -> dict[str, Any]:
    manifest = read_json(root / manifest_rel)
    allowed_refs = set(str(ref) for ref in manifest.get("allowed_input_refs", []))
    allowed_generated = set(str(ref) for ref in manifest.get("allowed_generated_refs", []))
    observed_refs = set(tree_refs(root))
    unexpected_refs = sorted(observed_refs - allowed_refs - allowed_generated)

    input_hash_failures: list[str] = []
    for ref, expected_hash in sorted(manifest.get("input_sha256", {}).items()):
        path = root / ref
        if not path.is_file():
            input_hash_failures.append(f"MISSING_INPUT::{ref}")
            continue
        actual_hash = sha256_file(path)
        if actual_hash != expected_hash:
            input_hash_failures.append(f"INPUT_HASH_MISMATCH::{ref}")

    register = read_json(root / REGISTER_REL)
    declared_refs = register.get("current_evidence_pack_refs", {})
    declared_hashes = register.get("current_evidence_pack_sha256", {})
    pack_results: dict[str, Any] = {}
    failures: list[str] = []
    selected_hashes: dict[str, str] = {}
    selected_source_refs: dict[str, list[str]] = {}
    selected_source_hash_refs: dict[str, list[dict[str, Any]]] = {}
    public_lock_failures: list[str] = []

    for domain, ref in CURRENT_PACK_REFS.items():
        if declared_refs.get(domain) != ref:
            failures.append(f"REGISTER_PACK_REF_MISMATCH::{domain}")
        path = root / ref
        if not path.is_file():
            failures.append(f"MISSING_SELECTED_PACK::{domain}::{ref}")
            continue
        pack = read_json(path)
        pack_hash = sha256_file(path)
        selected_hashes[domain] = pack_hash
        selected_source_refs[domain] = pack_source_refs(pack)
        selected_source_hash_refs[domain] = pack_source_hash_refs(pack)
        predicates = strict_pack_predicates(domain, pack, pack_hash, str(declared_hashes.get(domain) or ""))
        predicate_failures = [key for key, passed in predicates.items() if passed is not True]
        if predicate_failures:
            failures.append(f"STRICT_PACK_REPLAY_FAILURE::{domain}::{','.join(predicate_failures)}")
        lock_failures = [f"{ref}{item}" for item in public_action_true_paths(pack)]
        public_lock_failures.extend(lock_failures)
        pack_results[domain] = {
            "pack_ref": ref,
            "pack_sha256": pack_hash,
            "evidence_pack_id": pack.get("evidence_pack_id"),
            "source_ref_total": len(selected_source_refs[domain]),
            "source_hash_ref_total": len(selected_source_hash_refs[domain]),
            "predicates": predicates,
            "predicate_failures": predicate_failures,
        }

    for ref in (REGISTER_REL, LANES_REL, REPORT_REL):
        public_lock_failures.extend(f"{ref}{item}" for item in public_action_true_paths(read_json(root / ref)))

    failures.extend(input_hash_failures)
    failures.extend(f"UNEXPECTED_TEMP_TREE_REF::{ref}" for ref in unexpected_refs)
    failures.extend(f"PUBLIC_ACTION_TRUE::{item}" for item in public_lock_failures)
    failures = [str(item) for item in ordered_unique(failures)]

    passed = not failures
    return {
        "schema_id": SCHEMA_ID,
        "replay_id": REPLAY_ID,
        "generated_on": GENERATED_ON,
        "replay_kind": "deterministic_clean_temp_tree_current_strict_evidence_pack_replay",
        "replay_scope": "current strict evidence packs bound by the modern-science comparator register",
        "satisfies_register_predicate": passed,
        "bounded": False,
        "clean_temp_tree": {
            "isolated_copy": True,
            "deterministic_allowlist_copy": True,
            "dirty_untracked_leak_detected": bool(unexpected_refs),
            "allowed_input_ref_total": len(allowed_refs),
            "unexpected_ref_total": len(unexpected_refs),
            "unexpected_refs": unexpected_refs,
        },
        "register_binding": {
            "register_ref": REGISTER_REL,
            "benchmark_lanes_ref": LANES_REL,
            "superiority_report_ref": REPORT_REL,
            "declared_current_evidence_pack_refs": declared_refs,
            "declared_current_evidence_pack_sha256": declared_hashes,
            "selected_evidence_pack_refs": CURRENT_PACK_REFS,
            "selected_evidence_pack_sha256": selected_hashes,
            "selected_source_ref_total": sum(len(refs) for refs in selected_source_refs.values()),
            "selected_source_hash_ref_total": sum(len(refs) for refs in selected_source_hash_refs.values()),
        },
        "no_send_locks": {
            "no_send": True,
            "network_allowed": False,
            "public_release_action_allowed": False,
            "publish_allowed": False,
            "push_allowed": False,
            "registry_write_allowed": False,
            "journal_submissions_allowed": False,
            "email_allowed": False,
            "public_action_true_path_total": len(public_lock_failures),
            "public_action_true_paths": public_lock_failures,
        },
        "pack_replay_results": pack_results,
        "failures": failures,
    }


def verifier_command_template() -> list[str]:
    return [
        "python",
        HELPER_REL,
        "--verify-temp",
        "--root",
        "<temp_tree>",
        "--manifest",
        TEMP_MANIFEST_REL,
        "--output",
        TEMP_VERIFY_REL,
    ]


def run_clean_replay(root: Path) -> dict[str, Any]:
    refs = selected_input_refs(root)
    with tempfile.TemporaryDirectory(prefix="oc133_modern_science_clean_replay_") as temp_name:
        temp_root = Path(temp_name).resolve()
        input_hashes = copy_input_tree(root, temp_root, refs)
        manifest = {
            "schema_id": "OC133_MODERN_SCIENCE_CLEAN_REPLAY_INPUT_MANIFEST_v1",
            "generated_on": GENERATED_ON,
            "allowed_input_refs": refs,
            "allowed_generated_refs": [TEMP_MANIFEST_REL, TEMP_VERIFY_REL],
            "input_sha256": input_hashes,
        }
        write_json(temp_root / TEMP_MANIFEST_REL, manifest)
        actual_command = [
            sys.executable,
            str(temp_root / HELPER_REL),
            "--verify-temp",
            "--root",
            str(temp_root),
            "--manifest",
            TEMP_MANIFEST_REL,
            "--output",
            TEMP_VERIFY_REL,
        ]
        command_template = verifier_command_template()
        public_command = command_is_public_action(command_template)
        if public_command:
            verify_payload = {
                "schema_id": SCHEMA_ID,
                "replay_id": REPLAY_ID,
                "generated_on": GENERATED_ON,
                "satisfies_register_predicate": False,
                "failures": ["PUBLIC_OUTBOUND_RELEASE_COMMAND_BLOCKED"],
            }
            completed = subprocess.CompletedProcess(actual_command, 126, "", "blocked public outbound command")
        else:
            completed = subprocess.run(
                actual_command,
                cwd=temp_root,
                text=True,
                capture_output=True,
                timeout=30,
                check=False,
            )
            verify_path = temp_root / TEMP_VERIFY_REL
            verify_payload = read_json(verify_path) if verify_path.is_file() else {
                "schema_id": SCHEMA_ID,
                "replay_id": REPLAY_ID,
                "generated_on": GENERATED_ON,
                "satisfies_register_predicate": False,
                "failures": ["VERIFY_OUTPUT_MISSING"],
            }

        stdout_bytes = completed.stdout.encode("utf-8")
        stderr_bytes = completed.stderr.encode("utf-8")
        verify_output_hash = sha256_file(temp_root / TEMP_VERIFY_REL) if (temp_root / TEMP_VERIFY_REL).is_file() else ""
        command_result = {
            "command": " ".join(command_template),
            "command_sha256": sha256_object(command_template),
            "allowed_by_replay_command_allowlist": public_command is False,
            "public_outbound_release_action": public_command,
            "timeout_seconds": 30,
            "exit_code": completed.returncode,
            "stdout_sha256": sha256_bytes(stdout_bytes),
            "stderr_sha256": sha256_bytes(stderr_bytes),
            "output_ref": TEMP_VERIFY_REL,
            "output_sha256": verify_output_hash,
        }

    failures = list(verify_payload.get("failures", []))
    if completed.returncode != 0:
        failures.append(f"COMMAND_EXIT_NONZERO::{completed.returncode}")
    if public_command:
        failures.append("PUBLIC_OUTBOUND_RELEASE_COMMAND_BLOCKED")
    failures = [str(item) for item in ordered_unique(failures)]

    final_payload = dict(verify_payload)
    final_payload["satisfies_register_predicate"] = not failures and verify_payload.get("satisfies_register_predicate") is True
    final_payload["command_allowlist"] = [" ".join(verifier_command_template())]
    final_payload["command_results"] = [command_result]
    final_payload["failures"] = failures
    final_payload["report_hash_policy"] = "sha256 over deterministic JSON with sorted keys for register binding"
    final_payload["report_sha256"] = sha256_object({key: value for key, value in final_payload.items() if key != "report_sha256"})
    return final_payload


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Replay modern-science strict packs from a deterministic clean temp tree.")
    parser.add_argument("--root", default=str(repo_root()))
    parser.add_argument("--write", action="store_true", help=f"write {OUTPUT_REL}")
    parser.add_argument("--verify-temp", action="store_true", help="isolated verifier mode for the isolated temp tree")
    parser.add_argument("--manifest", default=TEMP_MANIFEST_REL)
    parser.add_argument("--output", default=OUTPUT_REL)
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    if args.verify_temp:
        payload = verify_temp_tree(root, args.manifest)
        write_json(root / args.output, payload)
        print(json.dumps({"status": "ok" if payload["satisfies_register_predicate"] else "failed", "output_ref": args.output}, sort_keys=True))
        return 0 if payload["satisfies_register_predicate"] else 1

    payload = run_clean_replay(root)
    if args.write:
        write_json(root / args.output, payload)
    print(json.dumps({"status": "ok" if payload["satisfies_register_predicate"] else "failed", "output_ref": args.output, "sha256": sha256_object(payload)}, sort_keys=True))
    return 0 if payload["satisfies_register_predicate"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
