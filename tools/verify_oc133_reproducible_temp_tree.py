from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
RELEASE_ID = "oc_core_1_3_3"
VERSION = "1.3.3"

COMPARE_REFS = [
    "formal/lean/LEAN_BUILD_CERTIFICATE_1_3_3.json",
    "proofs/FINITE_MODEL_CHECKS_1_3_3.json",
    "validation/numeric_replay_qa/OC133_NUMERIC_REPLAY_QA_TABLE.json",
    "validation/numeric_predictions/OC133_NUMERIC_REPLAY_LOG.json",
    "reports/OC_CORE_1_3_3_DOMAIN_VALIDATION_REPORT.json",
    "reports/OC_CORE_1_3_3_DOMAIN_VALIDATION_REPORT.md",
    "simulations/results/OC_CORE_1_3_3_SIMULATION_RESULTS_latest.json",
    "reports/OC_CORE_1_3_3_ADVERSARIAL_SIMULATION_REPORT.json",
    "releases/oc_core_1_3_3/editorial/OC_CORE_1_3_3_SHA256SUMS",
    "releases/oc_core_1_3_3/editorial/OC_CORE_1_3_3_ZIP_INTEGRITY_latest.json",
    "releases/oc_core_1_3_3/artifacts/oc_core_1_3_3_no_send_release.zip",
]

COMMANDS = [
    [sys.executable, "tools/materialize_oc_core_1_3_3_v12_closure.py"],
    [sys.executable, "proofs/finite_model_checks/run_finite_model_checks.py"],
    [sys.executable, "validation/run_all.py", "--qa-only"],
    [sys.executable, "simulations/run_all.py", "--write-report"],
    [sys.executable, "simulations/adversarial/run_all.py"],
    [sys.executable, "-m", "release_machine", "package", "--release", "oc_core_1_3_3", "--channel", "all", "--no-publish"],
]

PORTABLE_COMMANDS = [
    ["python", "tools/materialize_oc_core_1_3_3_v12_closure.py"],
    ["python", "proofs/finite_model_checks/run_finite_model_checks.py"],
    ["python", "validation/run_all.py", "--qa-only"],
    ["python", "simulations/run_all.py", "--write-report"],
    ["python", "simulations/adversarial/run_all.py"],
    ["python", "-m", "release_machine", "package", "--release", "oc_core_1_3_3", "--channel", "all", "--no-publish"],
]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_json(payload: Any) -> str:
    return hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()


def git_run(args: list[str], *, timeout: int = 60, check: bool = True) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        timeout=timeout,
    )
    if check and completed.returncode != 0:
        raise RuntimeError(completed.stderr[-1000:])
    return completed


def git_state() -> dict[str, Any]:
    head = git_run(["rev-parse", "HEAD"]).stdout.strip()
    tree = git_run(["rev-parse", "HEAD^{tree}"]).stdout.strip()
    tracked_dirty = git_run(["diff", "--name-only"], check=False).stdout.splitlines()
    staged_dirty = git_run(["diff", "--cached", "--name-only"], check=False).stdout.splitlines()
    missing_tracked = git_run(["ls-files", "--deleted"], check=False).stdout.splitlines()
    untracked = git_run(["ls-files", "--others", "--exclude-standard"], check=False).stdout.splitlines()
    return {
        "head_commit": head,
        "head_tree": tree,
        "tracked_worktree_dirty_total": len([row for row in tracked_dirty if row.strip()]),
        "staged_dirty_total": len([row for row in staged_dirty if row.strip()]),
        "missing_tracked_total": len([row for row in missing_tracked if row.strip()]),
        "untracked_ignored_for_head_replay_total": len([row for row in untracked if row.strip()]),
        "tracked_worktree_dirty_refs": [row.strip().replace("\\", "/") for row in tracked_dirty if row.strip()][:200],
        "staged_dirty_refs": [row.strip().replace("\\", "/") for row in staged_dirty if row.strip()][:200],
        "missing_tracked_refs": [row.strip().replace("\\", "/") for row in missing_tracked if row.strip()][:200],
        "strict_head_replay_clean": not tracked_dirty and not staged_dirty and not missing_tracked,
    }


def head_tracked_source_refs() -> list[str]:
    completed = git_run(["ls-tree", "-r", "--name-only", "HEAD"], timeout=120)
    return [line.strip() for line in completed.stdout.splitlines() if line.strip()]


def head_source_manifest() -> list[dict[str, str]]:
    completed = git_run(["ls-tree", "-r", "--full-tree", "HEAD"], timeout=120)
    rows = []
    for line in completed.stdout.splitlines():
        meta, ref = line.split("\t", 1)
        mode, kind, object_id = meta.split()
        rows.append({"ref": ref.replace("\\", "/"), "mode": mode, "kind": kind, "git_object_id": object_id})
    return rows


def extract_head_sources(temp_root: Path) -> list[str]:
    refs = head_tracked_source_refs()
    checkout = git_run(["worktree", "add", "--detach", "--quiet", str(temp_root), "HEAD"], timeout=180)
    if checkout.returncode != 0:
        raise RuntimeError(checkout.stderr[-1000:])
    return refs


def initialize_temp_git_index(temp_root: Path, refs: list[str]) -> dict[str, Any]:
    """Recreate the tracked-source index expected by release package filters."""
    if (temp_root / ".git").exists():
        indexed = subprocess.run(
            ["git", "ls-files", "--cached"],
            cwd=temp_root,
            text=True,
            encoding="utf-8",
            errors="replace",
            capture_output=True,
            timeout=60,
        )
        if indexed.returncode != 0:
            raise RuntimeError(indexed.stderr[-1000:])
        indexed_refs = [line.strip() for line in indexed.stdout.splitlines() if line.strip()]
        return {
            "temp_git_index_initialized": True,
            "temp_git_checkout_mode": "DETACHED_CLEAN_GIT_WORKTREE_FROM_HEAD",
            "temp_git_add_batch_total": 0,
            "temp_git_index_ref_total": len(indexed_refs),
            "temp_git_index_matches_copied_refs": set(indexed_refs) == set(refs),
        }
    init = subprocess.run(
        ["git", "init", "-q"],
        cwd=temp_root,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        timeout=60,
    )
    if init.returncode != 0:
        raise RuntimeError(init.stderr[-1000:])

    copied_refs = [ref.replace("\\", "/") for ref in refs if (temp_root / ref).is_file()]
    batch_total = 0
    for idx in range(0, len(copied_refs), 200):
        batch = copied_refs[idx : idx + 200]
        completed = subprocess.run(
            ["git", "add", "--", *batch],
            cwd=temp_root,
            text=True,
            encoding="utf-8",
            errors="replace",
            capture_output=True,
            timeout=120,
        )
        if completed.returncode != 0:
            raise RuntimeError(completed.stderr[-1000:])
        batch_total += 1

    indexed = subprocess.run(
        ["git", "ls-files", "--cached"],
        cwd=temp_root,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        timeout=60,
    )
    if indexed.returncode != 0:
        raise RuntimeError(indexed.stderr[-1000:])
    indexed_refs = [line.strip() for line in indexed.stdout.splitlines() if line.strip()]
    return {
        "temp_git_index_initialized": True,
        "temp_git_add_batch_total": batch_total,
        "temp_git_index_ref_total": len(indexed_refs),
        "temp_git_index_matches_copied_refs": set(indexed_refs) == set(copied_refs),
    }


def run_command(repo: Path, command: list[str], portable_command: list[str]) -> dict[str, Any]:
    completed = subprocess.run(
        command,
        cwd=repo,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        timeout=1200,
    )
    return {
        "command": " ".join(portable_command),
        "executed_with_current_python": True,
        "returncode": completed.returncode,
        "stdout_tail": completed.stdout[-1200:],
        "stderr_tail": completed.stderr[-1200:],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify OC Core 1.3.3 post-generation reproducibility from immutable HEAD.")
    parser.add_argument(
        "--allow-dirty-worktree",
        action="store_true",
        help="Development-only mode: records dirty state but still runs. Release verdict remains FAIL when tracked dirty state exists.",
    )
    args = parser.parse_args()
    state = git_state()
    source_manifest = head_source_manifest()
    previous_manifest_path = ROOT / "reports" / "OC_CORE_1_3_3_POST_GENERATION_REPRODUCIBILITY_MANIFEST.json"
    previous_manifest = json.loads(previous_manifest_path.read_text(encoding="utf-8")) if previous_manifest_path.exists() else None
    if not state["strict_head_replay_clean"] and not args.allow_dirty_worktree:
        payload = {
            "schema_id": "OC133_POST_GENERATION_REPRODUCIBILITY_MANIFEST_v12",
            "release_id": RELEASE_ID,
            "version": VERSION,
            "verification_mode": "IMMUTABLE_HEAD_REPLAY_REFUSED_DIRTY_TRACKED_STATE",
            "source_tree_policy": "Verifier uses git archive HEAD and refuses tracked worktree/staged/missing drift in strict release mode.",
            "git_state": state,
            "head_source_manifest_sha256": sha256_json(source_manifest),
            "command_total": 0,
            "command_failure_total": 1,
            "compared_artifact_total": len(COMPARE_REFS),
            "mismatch_total": len(COMPARE_REFS),
            "mismatches": [{"ref": ref, "reason": "STRICT_HEAD_REPLAY_REFUSED_DIRTY_TRACKED_STATE"} for ref in COMPARE_REFS],
            "no_send": True,
            "verdict": "FAIL",
        }
        previous_manifest_path.parent.mkdir(parents=True, exist_ok=True)
        previous_manifest_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 1
    with tempfile.TemporaryDirectory(prefix="oc133_repro_verify_") as tmp:
        temp_root = Path(tmp) / "repo"
        try:
            copied_source_refs = extract_head_sources(temp_root)
            temp_git_index = initialize_temp_git_index(temp_root, copied_source_refs)
            preexisting_targets = []
            for ref in COMPARE_REFS:
                target = temp_root / ref
                if target.exists():
                    preexisting_targets.append(ref)
                    target.unlink()
            command_rows = [
                run_command(temp_root, command, portable)
                for command, portable in zip(COMMANDS, PORTABLE_COMMANDS)
            ]
            rows = []
            failures = []
            for ref in COMPARE_REFS:
                current = ROOT / ref
                regenerated = temp_root / ref
                current_exists = current.exists()
                regenerated_exists = regenerated.exists()
                current_sha = sha256_file(current) if current_exists and current.is_file() else None
                regenerated_sha = sha256_file(regenerated) if regenerated_exists and regenerated.is_file() else None
                matches = current_sha == regenerated_sha and current_exists and regenerated_exists
                row = {
                    "ref": ref,
                    "current_exists": current_exists,
                    "regenerated_exists": regenerated_exists,
                    "current_sha256": current_sha,
                    "regenerated_sha256": regenerated_sha,
                    "matches": matches,
                }
                rows.append(row)
                if not matches:
                    failures.append(row)
            bad_commands = [row for row in command_rows if row["returncode"] != 0]
        finally:
            subprocess.run(
                ["git", "worktree", "remove", "--force", str(temp_root)],
                cwd=ROOT,
                text=True,
                encoding="utf-8",
                errors="replace",
                capture_output=True,
                timeout=120,
            )
    stable_payload = {
        "release_id": RELEASE_ID,
        "version": VERSION,
        "verification_mode": "IMMUTABLE_HEAD_TEMP_TREE_VERIFY_ONLY_NO_CURRENT_ARTIFACT_OVERWRITE_BEFORE_COMPARISON",
        "source_tree_policy": "Temp tree is built from a detached clean git worktree at HEAD, preserving checkout filters while refusing tracked worktree/staged drift in strict mode.",
        "git_state": state,
        "head_source_manifest_sha256": sha256_json(source_manifest),
        "head_source_ref_total": len(source_manifest),
        "copied_source_ref_total": len(copied_source_refs),
        "temp_git_index": temp_git_index,
        "source_only_target_policy": "All compared generated targets are deleted from the tracked-source temp tree before producers run; any regenerated target must be newly produced by the command sequence.",
        "preexisting_compared_target_total": len(preexisting_targets),
        "preexisting_compared_targets_deleted_before_generation": preexisting_targets,
        "host_local_path_policy": "Canonical command records use portable argv forms; interpreter path is intentionally not serialized.",
        "command_total": len(command_rows),
        "command_failure_total": len(bad_commands),
        "commands": command_rows,
        "compared_artifact_total": len(rows),
        "mismatch_total": len(failures),
        "mismatches": failures,
        "rows": rows,
        "no_send": True,
    }
    stable_payload_sha256 = sha256_json(stable_payload)
    previous_stable_sha = previous_manifest.get("stable_payload_sha256") if isinstance(previous_manifest, dict) else None
    previous_self_check = {
        "previous_manifest_existed": isinstance(previous_manifest, dict),
        "previous_manifest_stable_payload_sha256": previous_stable_sha,
        "current_stable_payload_sha256": stable_payload_sha256,
        "previous_manifest_matches_current_stable_payload": (previous_stable_sha == stable_payload_sha256) if previous_stable_sha else None,
        "self_check_policy": "The outer manifest is non-cyclic: stable_payload_sha256 excludes this self-check wrapper. A rerun detects stale or locally edited manifest payloads before overwriting.",
    }
    payload = {
        "schema_id": "OC133_POST_GENERATION_REPRODUCIBILITY_MANIFEST_v12",
        "stable_payload_sha256": stable_payload_sha256,
        "previous_manifest_self_check": previous_self_check,
        **stable_payload,
        "verdict": "PASS"
        if (
            state["strict_head_replay_clean"]
            and preexisting_targets
            and not bad_commands
            and not failures
            and (previous_stable_sha in {None, stable_payload_sha256})
        )
        else "FAIL",
    }
    out = previous_manifest_path
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload["verdict"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
