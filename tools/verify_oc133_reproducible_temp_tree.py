from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
RELEASE_ID = "oc_core_1_3_3"
VERSION = "1.3.3"

COMPARE_REFS = [
    "formal/lean/LEAN_BUILD_CERTIFICATE_1_3_3.json",
    "proofs/finite_model_checks/OC133_FINITE_MODEL_INPUTS.json",
    "proofs/FINITE_MODEL_CHECKS_1_3_3.json",
    "validation/numeric_replay_qa/OC133_NUMERIC_REPLAY_QA_TABLE.json",
    "validation/numeric_predictions/OC133_NUMERIC_REPLAY_LOG.json",
    "reports/OC_CORE_1_3_3_DOMAIN_VALIDATION_REPORT.json",
    "reports/OC_CORE_1_3_3_DOMAIN_VALIDATION_REPORT.md",
    "manifest.json",
    "checksums.txt",
    "ro-crate-metadata.jsonld",
    "CITATION.cff",
    ".codemeta.json",
    "releases/oc_core_1_3_3/editorial/metadata_drafts/zenodo.no_send.draft.json",
    "simulations/results/OC_CORE_1_3_3_SIMULATION_RESULTS_latest.json",
    "reports/OC_CORE_1_3_3_ADVERSARIAL_SIMULATION_REPORT.json",
    "review/OC_1_3_3_TOTAL_ATTACK_MATRIX.json",
    "reviews/OC_CORE_1_3_3_REVIEWER_RESPONSE_MATRIX.json",
    "releases/oc_core_1_3_3/editorial/OC_CORE_1_3_3_ARTIFACT_INVENTORY.json",
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

COMMAND_OUTPUT_TAIL_LIMIT = 1200
SYNC_REASON_COMMAND_FAILURE = "sync_regenerated_artifacts_refused_due_command_failure"
SYNC_REASON_REQUESTED = "sync_regenerated_artifacts_executed_after_successful_commands"
SYNC_REASON_FLAG_NOT_SET = "sync_regenerated_artifacts_not_requested"

PORTABLE_COMMANDS = [
    ["python", "tools/materialize_oc_core_1_3_3_v12_closure.py"],
    ["python", "proofs/finite_model_checks/run_finite_model_checks.py"],
    ["python", "validation/run_all.py", "--qa-only"],
    ["python", "simulations/run_all.py", "--write-report"],
    ["python", "simulations/adversarial/run_all.py"],
    ["python", "-m", "release_machine", "package", "--release", "oc_core_1_3_3", "--channel", "all", "--no-publish"],
]


def tail_text(value: str | None, max_chars: int = COMMAND_OUTPUT_TAIL_LIMIT) -> str:
    if not value:
        return ""
    if len(value) <= max_chars:
        return value
    return value[-max_chars:]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def stable_ref_sha256(path: Path) -> str:
    data = path.read_bytes()
    if path.suffix.lower() in {".py", ".lean", ".yml", ".yaml", ".json", ".md", ".tex", ".txt", ".cff", ".jsonld"}:
        data = data.replace(b"\r\n", b"\n")
    return hashlib.sha256(data).hexdigest()


def sha256_json(payload: Any) -> str:
    return hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()


def zip_member_manifest(path: Path) -> dict[str, Any]:
    rows = []
    with zipfile.ZipFile(path) as zf:
        for info in sorted(zf.infolist(), key=lambda item: item.filename):
            if info.is_dir():
                continue
            rows.append(
                {
                    "filename": info.filename,
                    "file_size": info.file_size,
                    "compress_size": info.compress_size,
                    "crc": info.CRC,
                    "sha256": hashlib.sha256(zf.read(info.filename)).hexdigest(),
                }
            )
    return {
        "member_total": len(rows),
        "member_manifest_sha256": sha256_json(rows),
    }


def parse_checksum_lines(path: Path) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8", errors="ignore").splitlines(), start=1):
        stripped = line.strip()
        if not stripped:
            continue
        parts = stripped.split(maxsplit=1)
        if len(parts) != 2:
            rows.append({"line_no": str(line_no), "sha256": "", "path": "", "parse_error": "CHECKSUM_LINE_PARSE_FAILED"})
            continue
        rows.append({"line_no": str(line_no), "sha256": parts[0], "path": parts[1].strip()})
    return rows


def internal_checksum_failures(repo: Path) -> tuple[list[dict[str, Any]], set[str]]:
    """Validate hashes declared inside regenerated manifests/checksum files."""
    failures: list[dict[str, Any]] = []
    manifest_nonrecursive_exceptions: set[str] = set()

    def check_file_ref(source_ref: str, ref: str, expected_sha: str | None, expected_size: int | None = None) -> None:
        if not ref:
            failures.append({"source_ref": source_ref, "path": ref, "reason": "EMPTY_REF"})
            return
        path = repo / ref
        if not path.is_file():
            failures.append({"source_ref": source_ref, "path": ref, "reason": "MISSING_REFERENCED_FILE"})
            return
        actual_sha = sha256_file(path)
        if expected_sha and actual_sha != expected_sha:
            failures.append({"source_ref": source_ref, "path": ref, "reason": "SHA256_MISMATCH", "expected": expected_sha, "actual": actual_sha})
        if expected_size is not None and path.stat().st_size != int(expected_size):
            failures.append({"source_ref": source_ref, "path": ref, "reason": "SIZE_MISMATCH", "expected": expected_size, "actual": path.stat().st_size})

    manifest_path = repo / "manifest.json"
    if manifest_path.is_file():
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except Exception as exc:
            failures.append({"source_ref": "manifest.json", "reason": "JSON_PARSE_FAILED", "error": str(exc)})
        else:
            manifest_nonrecursive_exceptions = {
                str(row.get("path", ""))
                for row in manifest.get("nonrecursive_manifest_exceptions", [])
                if isinstance(row, dict) and row.get("path")
            }
            for row in manifest.get("files", []):
                if isinstance(row, dict):
                    check_file_ref("manifest.json", str(row.get("path", "")), row.get("sha256"), row.get("size_bytes"))

    checksums_path = repo / "checksums.txt"
    if checksums_path.is_file():
        for row in parse_checksum_lines(checksums_path):
            if row.get("parse_error"):
                failures.append({"source_ref": "checksums.txt", **row})
            else:
                check_file_ref("checksums.txt", row["path"], row["sha256"])

    inventory_path = repo / "releases" / RELEASE_ID / "editorial" / "OC_CORE_1_3_3_ARTIFACT_INVENTORY.json"
    if inventory_path.is_file():
        try:
            inventory = json.loads(inventory_path.read_text(encoding="utf-8"))
        except Exception as exc:
            failures.append({"source_ref": inventory_path.relative_to(repo).as_posix(), "reason": "JSON_PARSE_FAILED", "error": str(exc)})
        else:
            for row in inventory.get("rows", []):
                if isinstance(row, dict):
                    check_file_ref(inventory_path.relative_to(repo).as_posix(), str(row.get("path", "")), row.get("sha256"), row.get("size_bytes"))

    sha_path = repo / "releases" / RELEASE_ID / "editorial" / "OC_CORE_1_3_3_SHA256SUMS"
    if sha_path.is_file():
        sha_ref = sha_path.relative_to(repo).as_posix()
        for row in parse_checksum_lines(sha_path):
            if row.get("parse_error"):
                failures.append({"source_ref": sha_ref, **row})
            else:
                check_file_ref(sha_ref, row["path"], row["sha256"])

    zip_integrity_path = repo / "releases" / RELEASE_ID / "editorial" / "OC_CORE_1_3_3_ZIP_INTEGRITY_latest.json"
    if zip_integrity_path.is_file():
        try:
            zip_integrity = json.loads(zip_integrity_path.read_text(encoding="utf-8"))
        except Exception as exc:
            failures.append({"source_ref": zip_integrity_path.relative_to(repo).as_posix(), "reason": "JSON_PARSE_FAILED", "error": str(exc)})
        else:
            check_file_ref(
                zip_integrity_path.relative_to(repo).as_posix(),
                str(zip_integrity.get("package", "")),
                zip_integrity.get("package_sha256"),
                zip_integrity.get("package_size_bytes"),
            )
            package_ref = str(zip_integrity.get("package", ""))
            package_path = repo / package_ref
            if package_path.is_file() and zip_integrity.get("package_member_total") is not None:
                actual_member_total = zip_member_manifest(package_path).get("member_total")
                if actual_member_total != int(zip_integrity.get("package_member_total")):
                    failures.append({
                        "source_ref": zip_integrity_path.relative_to(repo).as_posix(),
                        "path": package_ref,
                        "reason": "ZIP_MEMBER_TOTAL_MISMATCH",
                        "expected": zip_integrity.get("package_member_total"),
                        "actual": actual_member_total,
                    })
    return failures, manifest_nonrecursive_exceptions


def summarize_internal_checksum_failures(
    failures: list[dict[str, Any]],
    declared_manifest_exceptions: set[str],
) -> dict[str, Any]:
    reason_counts: dict[str, int] = {}
    path_sources: dict[str, set[str]] = {}
    parse_error_total = 0
    for failure in failures:
        reason = str(failure.get("reason", "UNKNOWN"))
        reason_counts[reason] = reason_counts.get(reason, 0) + 1
        if reason == "CHECKSUM_LINE_PARSE_FAILED":
            parse_error_total += 1
        path = str(failure.get("path", ""))
        if not path:
            continue
        path_sources.setdefault(path, set()).add(str(failure.get("source_ref", "")))

    cycle_candidates: list[dict[str, Any]] = []
    for path, sources in sorted(path_sources.items()):
        source_list = sorted(source for source in sources if source)
        if len(source_list) < 2:
            continue
        if "manifest.json" in source_list or "checksums.txt" in source_list:
            cycle_candidates.append(
                {
                    "path": path,
                    "source_refs": source_list,
                    "manifest_declares_nonrecursive_exception": path in declared_manifest_exceptions,
                    "likely_cross_file_cycle": set(source_list).issuperset({"manifest.json", "checksums.txt"}),
                }
            )

    return {
        "total": len(failures),
        "parse_error_total": parse_error_total,
        "reason_totals": dict(sorted(reason_counts.items())),
        "control_file_cycle_candidates": cycle_candidates,
    }


def recompute_manifest_stable_payload_hash(manifest: dict[str, Any] | None) -> str | None:
    if not isinstance(manifest, dict):
        return None
    stable = {
        key: value
        for key, value in manifest.items()
        if key not in {"schema_id", "stable_payload_sha256", "previous_manifest_self_check", "verdict"}
    }
    return sha256_json(stable)


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


def run_command(
    repo: Path,
    command: list[str],
    portable_command: list[str],
    capture_success_output: bool,
) -> dict[str, Any]:
    completed = subprocess.run(
        command,
        cwd=repo,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        timeout=1200,
    )
    row = {
        "command": " ".join(portable_command),
        "executed_with_current_python": True,
        "returncode": completed.returncode,
    }
    if capture_success_output or completed.returncode != 0:
        row["stdout_tail"] = tail_text(completed.stdout, COMMAND_OUTPUT_TAIL_LIMIT)
        row["stderr_tail"] = tail_text(completed.stderr, COMMAND_OUTPUT_TAIL_LIMIT)
    return row


def compare_ref_row(
    ref: str,
    baseline_exists: bool,
    baseline_sha: str | None,
    regenerated_exists: bool,
    regenerated_sha: str | None,
    baseline_zip_manifest: dict[str, Any] | None = None,
    regenerated_zip_manifest: dict[str, Any] | None = None,
) -> dict[str, Any]:
    mismatch_reasons: list[str] = []
    if not baseline_exists:
        mismatch_reasons.append("MISSING_BASELINE_REF")
    if not regenerated_exists:
        mismatch_reasons.append("MISSING_REGENERATED_FILE")
    elif baseline_sha is None:
        mismatch_reasons.append("BASELINE_HASH_UNKNOWN")
    elif regenerated_sha is None:
        mismatch_reasons.append("REGENERATED_HASH_UNKNOWN")
    elif baseline_sha != regenerated_sha:
        mismatch_reasons.append("SHA256_MISMATCH")

    row = {
        "ref": ref,
        "committed_clean_checkout_baseline_exists": baseline_exists,
        "regenerated_exists": regenerated_exists,
        "committed_clean_checkout_baseline_sha256": baseline_sha,
        "regenerated_sha256": regenerated_sha,
        "mismatch_reasons": mismatch_reasons,
    }
    matches = not mismatch_reasons
    if ref.endswith(".zip"):
        row.update(
            {
                "zip_member_manifest_compared": True,
                "committed_clean_checkout_baseline_zip_member_manifest": baseline_zip_manifest,
                "regenerated_zip_member_manifest": regenerated_zip_manifest,
            }
        )
        manifest_match = baseline_zip_manifest == regenerated_zip_manifest
        if not manifest_match:
            mismatch_reasons.append("ZIP_MEMBER_MANIFEST_MISMATCH")
            matches = False
        row["zip_member_manifest_matches"] = manifest_match
    row["matches"] = matches
    return row


def sync_plan(sync_requested: bool, bad_commands: list[dict[str, Any]]) -> tuple[bool, str]:
    if not sync_requested:
        return False, SYNC_REASON_FLAG_NOT_SET
    if bad_commands:
        return False, SYNC_REASON_COMMAND_FAILURE
    return True, SYNC_REASON_REQUESTED


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify OC Core 1.3.3 post-generation reproducibility from immutable HEAD.")
    parser.add_argument(
        "--allow-dirty-worktree",
        action="store_true",
        help="Development-only mode: records dirty state but still runs. Release verdict remains FAIL when tracked dirty state exists.",
    )
    parser.add_argument(
        "--sync-regenerated-artifacts",
        action="store_true",
        help=(
            "Copy regenerated compared artifacts from the detached clean worktree back to the main tree only after "
            "all commands finish with returncode 0."
        ),
    )
    parser.add_argument(
        "--include-command-output",
        action="store_true",
        help=(
            "Keep stdout/stderr tails for successful commands in the manifest payload. "
            "Without this flag, only command failures keep tails."
        ),
    )
    args = parser.parse_args()
    state = git_state()
    source_manifest = head_source_manifest()
    previous_manifest_path = ROOT / "reports" / "OC_CORE_1_3_3_POST_GENERATION_REPRODUCIBILITY_MANIFEST.json"
    previous_manifest = json.loads(previous_manifest_path.read_text(encoding="utf-8")) if previous_manifest_path.exists() else None
    copied_source_refs: list[str] = []
    temp_git_index: dict[str, Any] = {
        "temp_git_index_initialized": False,
        "temp_git_checkout_mode": "NOT_STARTED",
    }
    preexisting_targets: list[str] = []
    command_rows: list[dict[str, Any]] = []
    rows: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []
    bad_commands: list[dict[str, Any]] = []
    synced_refs: list[str] = []
    non_compare_mutations: list[dict[str, Any]] = []
    internal_hash_failures: list[dict[str, Any]] = []
    internal_checksum_exceptioned_paths: set[str] = set()
    sync_executed = False
    sync_reason = SYNC_REASON_FLAG_NOT_SET
    if not state["strict_head_replay_clean"] and not args.allow_dirty_worktree:
        payload = {
            "schema_id": "OC133_POST_GENERATION_REPRODUCIBILITY_MANIFEST_v12",
            "release_id": RELEASE_ID,
            "version": VERSION,
            "verification_mode": "IMMUTABLE_HEAD_REPLAY_REFUSED_DIRTY_TRACKED_STATE",
            "source_tree_policy": "Verifier uses a detached clean git worktree at HEAD and refuses tracked worktree/staged/missing drift in strict release mode.",
            "git_state": state,
            "head_source_manifest_sha256": sha256_json(source_manifest),
            "command_total": 0,
            "command_failure_total": 1,
            "compared_artifact_total": len(COMPARE_REFS),
            "mismatch_total": len(COMPARE_REFS),
            "mismatches": [{"ref": ref, "reason": "STRICT_HEAD_REPLAY_REFUSED_DIRTY_TRACKED_STATE"} for ref in COMPARE_REFS],
            "non_compare_ref_mutation_total": 0,
            "non_compare_ref_mutations": [],
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
            preexisting_target_sha256: dict[str, str] = {}
            preexisting_zip_manifests: dict[str, dict[str, Any]] = {}
            pre_run_non_compare_hashes: dict[str, str] = {
                ref: stable_ref_sha256(temp_root / ref)
                for ref in copied_source_refs
                if ref not in set(COMPARE_REFS) and (temp_root / ref).is_file()
            }
            for ref in COMPARE_REFS:
                target = temp_root / ref
                if target.exists():
                    preexisting_targets.append(ref)
                    if target.is_file():
                        preexisting_target_sha256[ref] = sha256_file(target)
                        if ref.endswith(".zip"):
                            preexisting_zip_manifests[ref] = zip_member_manifest(target)
                    target.unlink()
            command_rows = [
                run_command(
                    temp_root,
                    command,
                    portable,
                    capture_success_output=args.include_command_output,
                )
                for command, portable in zip(COMMANDS, PORTABLE_COMMANDS)
            ]
            rows = []
            failures = []
            for ref in COMPARE_REFS:
                regenerated = temp_root / ref
                baseline_exists = ref in preexisting_target_sha256
                regenerated_exists = regenerated.exists()
                baseline_sha = preexisting_target_sha256.get(ref)
                regenerated_sha = sha256_file(regenerated) if regenerated_exists and regenerated.is_file() else None
                baseline_zip_manifest: dict[str, Any] | None = None
                regenerated_zip_manifest: dict[str, Any] | None = None
                if ref.endswith(".zip"):
                    baseline_zip_manifest = preexisting_zip_manifests.get(ref)
                    regenerated_zip_manifest = (
                        zip_member_manifest(regenerated)
                        if regenerated_exists and regenerated.exists()
                        else None
                    )
                row = compare_ref_row(
                    ref=ref,
                    baseline_exists=baseline_exists,
                    baseline_sha=baseline_sha,
                    regenerated_exists=regenerated_exists,
                    regenerated_sha=regenerated_sha,
                    baseline_zip_manifest=baseline_zip_manifest,
                    regenerated_zip_manifest=regenerated_zip_manifest,
                )
                rows.append(row)
                if not row["matches"]:
                    failures.append(row)
            bad_commands = [row for row in command_rows if row["returncode"] != 0]
            internal_hash_failures, internal_checksum_exceptioned_paths = internal_checksum_failures(temp_root)
            internal_checksum_summary = summarize_internal_checksum_failures(
                internal_hash_failures,
                internal_checksum_exceptioned_paths,
            )
            non_compare_mutations = []
            for ref, before_sha in sorted(pre_run_non_compare_hashes.items()):
                path = temp_root / ref
                if not path.exists() or not path.is_file():
                    non_compare_mutations.append(
                        {
                            "ref": ref,
                            "before_sha256": before_sha,
                            "after_sha256": None,
                            "mutation": "DELETED_OR_NON_FILE",
                        }
                    )
                    continue
                after_sha = stable_ref_sha256(path)
                if after_sha != before_sha:
                    non_compare_mutations.append(
                        {
                            "ref": ref,
                            "before_sha256": before_sha,
                            "after_sha256": after_sha,
                            "mutation": "NON_COMPARE_REF_CHANGED_BY_REPRODUCIBILITY_COMMANDS",
                        }
                    )
            sync_executed, sync_reason = sync_plan(bad_commands=bad_commands, sync_requested=args.sync_regenerated_artifacts)
            if sync_executed:
                for row in failures:
                    ref = row["ref"]
                    regenerated = temp_root / ref
                    if regenerated.exists() and regenerated.is_file():
                        target = ROOT / ref
                        target.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(regenerated, target)
                        synced_refs.append(ref)
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
        "source_only_package_generation_claimed": False,
        "package_reproducibility_scope": "BYTE_REPRODUCIBILITY_OF_COMMITTED_PACKAGE_INPUT_SET_PLUS_REGENERATED_COMPARE_REFS",
        "package_member_regeneration_policy": "The verifier deletes and regenerates COMPARE_REFS, then compares package bytes and zip-member hashes. It does not claim every package member was regenerated from primitive sources unless that member is listed in COMPARE_REFS or a future generated-output inventory.",
        "cross_environment_byte_identity_claimed": False,
        "packaging_stack_policy": "Byte identity is a same-stack local release check unless a future container/provisioning digest is supplied; canonical artifacts must not promote cross-Python/zlib byte identity.",
        "git_state": state,
        "head_source_manifest_sha256": sha256_json(source_manifest),
        "head_source_ref_total": len(source_manifest),
        "copied_source_ref_total": len(copied_source_refs),
        "temp_git_index": temp_git_index,
        "source_only_target_policy": "All COMPARE_REFS are deleted from the tracked-source temp tree before producers run. Package byte identity is claimed for the committed package input set plus regenerated COMPARE_REFS, not for full source-only regeneration of every package member.",
        "non_compare_ref_mutation_policy": "All tracked refs outside COMPARE_REFS are snapshotted before producers and must remain stable by normalized text hash or byte hash. Source-generator mutations outside the compared artifact set fail this verifier.",
        "comparison_baseline_policy": "Byte comparison is against the preexisting committed files in the same detached clean worktree before deletion, not against ambient current worktree bytes.",
        "preexisting_compared_target_total": len(preexisting_targets),
        "preexisting_compared_targets_deleted_before_generation": preexisting_targets,
        "host_local_path_policy": "Canonical command records use portable argv forms; interpreter path is intentionally not serialized.",
        "command_total": len(command_rows),
        "command_failure_total": len(bad_commands),
        "commands": command_rows,
        "command_output_capture_policy": {
            "capture_success_output": args.include_command_output,
            "stdout_stderr_tail_limit": COMMAND_OUTPUT_TAIL_LIMIT,
        },
        "sync_regenerated_artifacts_requested": args.sync_regenerated_artifacts,
        "sync_regenerated_artifacts_executed": sync_executed,
        "sync_regenerated_artifacts_execution_reason": sync_reason,
        "synced_regenerated_artifact_total": len(synced_refs),
        "synced_regenerated_artifacts": synced_refs,
        "compared_artifact_total": len(rows),
        "mismatch_total": len(failures),
        "mismatches": failures,
        "non_compare_ref_mutation_total": len(non_compare_mutations),
        "non_compare_ref_mutations": non_compare_mutations[:200],
        "internal_checksum_failure_total": len(internal_hash_failures),
        "internal_checksum_failures": internal_hash_failures[:200],
        "internal_checksum_failure_summary": internal_checksum_summary,
        "internal_checksum_control_file_cycle_candidate_total": len(internal_checksum_summary["control_file_cycle_candidates"]),
        "internal_checksum_control_file_cycle_candidates": internal_checksum_summary["control_file_cycle_candidates"][:200],
        "rows": rows,
        "no_send": True,
    }
    stable_payload_sha256 = sha256_json(stable_payload)
    previous_stable_sha = previous_manifest.get("stable_payload_sha256") if isinstance(previous_manifest, dict) else None
    previous_recomputed_stable_sha = recompute_manifest_stable_payload_hash(previous_manifest)
    previous_declared_hash_valid = (
        previous_recomputed_stable_sha == previous_stable_sha
        if previous_stable_sha and previous_recomputed_stable_sha
        else None
    )
    previous_self_check = {
        "previous_manifest_existed": isinstance(previous_manifest, dict),
        "previous_manifest_stable_payload_sha256": previous_stable_sha,
        "previous_manifest_recomputed_stable_payload_sha256": previous_recomputed_stable_sha,
        "previous_manifest_declared_hash_valid": previous_declared_hash_valid,
        "current_stable_payload_sha256": stable_payload_sha256,
        "previous_manifest_matches_current_stable_payload": (previous_recomputed_stable_sha == stable_payload_sha256) if previous_recomputed_stable_sha else None,
        "self_check_policy": "The outer manifest is non-cyclic: stable_payload_sha256 excludes this self-check wrapper. Before overwriting, the verifier recomputes the previous stable payload hash from previous manifest fields, rejects edited payloads whose declared hash no longer matches, and then compares the recomputed previous hash to the current stable payload.",
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
            and not non_compare_mutations
            and not internal_hash_failures
            and (
                previous_manifest is None
                or (
                    previous_declared_hash_valid is True
                    and previous_recomputed_stable_sha == stable_payload_sha256
                )
            )
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
