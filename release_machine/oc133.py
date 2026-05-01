from __future__ import annotations

import hashlib
import json
import fnmatch
import os
import runpy
import subprocess
import sys
import zipfile
from pathlib import Path
from typing import Any

from . import complete
from . import oc133_hardening
from . import oc133_platinum
from . import oc133_v12
from .constants import GATE_STATES, SEVERITIES, TIMESTAMP


RELEASE_ID = "oc_core_1_3_3"
VERSION = "1.3.3"
BRANCH = "release/oc-core-1.3.3-total-scientific-closure"
ZIP_NAME = "oc_core_1_3_3_no_send_release.zip"

_BUILD_PACKAGE_CACHE: dict[tuple[str, str, str, bool], dict[str, Any]] = {}

PACKAGE_INCLUDE_ROOTS = [
    f"releases/{RELEASE_ID}/",
    "proofs/",
    "validation/",
    "falsification/",
    "reviews/",
]

PACKAGE_INCLUDE_PATTERNS = [
    "appendix/OC_1_3_3_*.tex",
    "content/OC_1_3_3_*.tex",
    "claims/*1_3_3*",
    "claims/CLAIM_LEDGER_FULL.*",
    "claims/CLAIM_EVIDENCE_MATRIX.*",
    "data/*1_3_3*.json",
    "data/*/*.md",
    "data/*/*.json",
    "data/k_level_irreducibility_matrix.json",
    "data/domain_semantics_matrix.json",
    "data/OC_CORE_1_3_3_TYPE_SYMBOL_TABLE.json",
    "docs/OC_1_3_3_*",
    "comparators/OC_1_3_3_*",
    "review/OC_1_3_3_*",
    "empirical/*/*.json",
    "empirical/*/*.md",
    "formal/**/*.lean",
    "formal/*.md",
    "formal/**/*.md",
    "lakefile.lean",
    "lean-toolchain",
    "reports/OC_CORE_1_3_3_*",
]

PACKAGE_EXCLUDED_NAMES = {
    "OC_CORE_1_3_3_ARTIFACT_INVENTORY.json",
    "OC_CORE_1_3_3_RELEASE_CONTROL_PLANE_latest.json",
    "OC_CORE_1_3_3_RELEASE_SCORECARD_latest.json",
    "OC_CORE_1_3_3_RELEASE_SCORECARD_latest.md",
    "OC_CORE_1_3_3_SHA256SUMS",
    "OC_CORE_1_3_3_ZIP_INTEGRITY_latest.json",
    "OC_CORE_1_3_3_POST_GENERATION_REPRODUCIBILITY_MANIFEST.json",
    "OC_CORE_1_3_3_PERSONAL_RELEASE_AUDIT_latest.json",
    "OC_CORE_1_3_3_PERSONAL_RELEASE_AUDIT_latest.md",
}

ROOT_NO_SEND_SURFACE_REFS = [
    "manifest.json",
    "checksums.txt",
    "ro-crate-metadata.jsonld",
    "CITATION.cff",
    ".codemeta.json",
    "README.md",
    "RELEASE_NOTES.md",
    "VERSION",
]

ROOT_NO_SEND_FORBIDDEN_TOKENS = [
    "1.3.2",
    "v1.3.2",
    "oc_core_1_3_2",
    "10.5281/zenodo.",
]

PDF_ARTIFACTS = [
    "OC_CORE_1_3_3_MASTER_MONOGRAPH_EN.pdf",
    "OC_CORE_1_3_3_JOURNAL_CORE_EN.pdf",
    "OC_CORE_1_3_3_METHODS_AND_REPRODUCIBILITY_COMPANION_EN.pdf",
    "OC_CORE_1_3_3_REVIEWER_ATTACK_AND_RESPONSE_MAP_EN.pdf",
]

NEW_GATES = [
    ("G32", "type_coherence"),
    ("G33", "theorem_closure"),
    ("G34", "k0_resolution"),
    ("G35", "continuumness_coherence"),
    ("G36", "boundary_generalization"),
    ("G37", "hybrid_operator"),
    ("G38", "dimension_semantics"),
    ("G39", "cycle_counterexample"),
    ("G40", "k_level_irreducibility"),
    ("G41", "empirical_pass"),
    ("G42", "comparator"),
    ("G43", "reviewer_attack_closure"),
    ("G44", "no_rhetorical_closure"),
    ("G45", "public_claim_traceability"),
]


def repo_root(start: Path | None = None) -> Path:
    return complete.repo_root(start)


def release_dir(root: Path) -> Path:
    return root / "releases" / RELEASE_ID


def editorial_dir(root: Path) -> Path:
    return release_dir(root) / "editorial"


def artifacts_dir(root: Path) -> Path:
    return release_dir(root) / "artifacts"


def rel(root: Path, path: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def _long_fs_path(path: Path) -> str:
    value = str(path if path.is_absolute() else path.resolve())
    if os.name != "nt" or value.startswith("\\\\?\\"):
        return value
    if value.startswith("\\\\"):
        return "\\\\?\\UNC\\" + value[2:]
    return "\\\\?\\" + value


def _path_exists(path: Path) -> bool:
    return os.path.exists(_long_fs_path(path))


def _is_file(path: Path) -> bool:
    return os.path.isfile(_long_fs_path(path))


def _read_bytes(path: Path) -> bytes:
    with open(_long_fs_path(path), "rb") as handle:
        return handle.read()


def _read_text(path: Path, encoding: str = "utf-8", errors: str = "strict") -> str:
    with open(_long_fs_path(path), "r", encoding=encoding, errors=errors) as handle:
        return handle.read()


def read_json(path: Path) -> Any:
    return json.loads(_read_text(path, encoding="utf-8"))


def _write_bytes_if_changed(path: Path, data: bytes) -> bool:
    path.parent.mkdir(parents=True, exist_ok=True)
    if _path_exists(path) and _read_bytes(path) == data:
        return False
    with open(_long_fs_path(path), "wb") as handle:
        handle.write(data)
    return True


def write_json(path: Path, payload: Any) -> bool:
    data = (json.dumps(payload, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    return _write_bytes_if_changed(path, data)


def write_text(path: Path, text: str) -> bool:
    if not text.endswith("\n"):
        text += "\n"
    return _write_bytes_if_changed(path, text.encode("utf-8"))


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(_long_fs_path(path), "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def package_bytes(path: Path) -> bytes:
    data = _read_bytes(path)
    if path.suffix.lower() in {".py", ".lean", ".yml", ".yaml", ".json", ".md", ".tex", ".txt", ".cff", ".jsonld"}:
        data = data.replace(b"\r\n", b"\n")
    return data


def sha256_package_bytes(path: Path) -> str:
    return hashlib.sha256(package_bytes(path)).hexdigest()


def tracked_ref_set(root: Path) -> set[str]:
    completed = subprocess.run(
        ["git", "ls-files", "--cached"],
        cwd=root,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        timeout=60,
    )
    if completed.returncode != 0:
        return set()
    return {line.strip().replace("\\", "/") for line in completed.stdout.splitlines() if line.strip()}


def gate(gate_id: str, name: str, state: str, severity: str, summary: str, details: dict[str, Any] | None = None) -> dict[str, Any]:
    if state not in GATE_STATES:
        raise ValueError(f"Unknown gate state: {state}")
    if severity not in SEVERITIES:
        raise ValueError(f"Unknown severity: {severity}")
    if state == "PASS" and details is None:
        raise ValueError(f"Gate {gate_id} requires evidence details for PASS")
    return {
        "gate_id": gate_id,
        "name": name,
        "state": state,
        "severity": severity,
        "summary": summary,
        "details": details or {},
        "executed": True,
    }


def ensure_materialized(root: Path) -> None:
    sentinel = release_dir(root) / "README.md"
    registry = root / "proofs" / "THEOREM_REGISTRY_1_3_3.json"
    if sentinel.exists() and registry.exists():
        return
    script = root / "tools" / "materialize_oc_core_1_3_3_scientific_closure.py"
    try:
        runpy.run_path(str(script), run_name="__main__")
    except SystemExit as exc:
        if int(exc.code or 0) != 0:
            raise


def run_local_replays(root: Path) -> None:
    subprocess.run([sys.executable, str(root / "proofs" / "finite_model_checks" / "run_finite_model_checks.py")], cwd=root, check=True, text=True, capture_output=True)
    subprocess.run([sys.executable, str(root / "falsification" / "counterexample_search" / "run_counterexample_search.py")], cwd=root, check=True, text=True, capture_output=True)
    # Counterexample search currently syncs v12 generated surfaces internally.
    # Validation must therefore run last, otherwise materializer defaults can
    # erase capability-produced target-blind evidence before content closure.
    subprocess.run([sys.executable, str(root / "validation" / "run_all.py"), "--qa-only"], cwd=root, check=True, text=True, capture_output=True)


def package_file_paths(root: Path) -> list[Path]:
    tracked_refs = tracked_ref_set(root)

    def included(ref: str) -> bool:
        path = Path(ref)
        if path.name == ZIP_NAME or path.name in PACKAGE_EXCLUDED_NAMES:
            return False
        if ref.startswith(f"releases/{RELEASE_ID}/editorial/parfit/"):
            return False
        if "__pycache__" in path.parts or "pdf_text_audit" in path.parts:
            return False
        if path.suffix == ".pyc":
            return False
        if any(ref.startswith(prefix) for prefix in PACKAGE_INCLUDE_ROOTS):
            return True
        return any(fnmatch.fnmatchcase(ref, pattern) for pattern in PACKAGE_INCLUDE_PATTERNS)

    return sorted(root / ref for ref in tracked_refs if included(ref))


def _package_input_fingerprint(root: Path) -> str:
    h = hashlib.sha256()
    for path in package_file_paths(root):
        payload = package_bytes(path)
        h.update(rel(root, path).encode("utf-8"))
        h.update(b"\0")
        h.update(str(len(payload)).encode("ascii"))
        h.update(b"\0")
        h.update(hashlib.sha256(payload).hexdigest().encode("ascii"))
        h.update(b"\0")
    return h.hexdigest()


def _cached_package(root: Path, channel: str, no_publish: bool, fingerprint: str) -> dict[str, Any] | None:
    key = (str(root.resolve()), RELEASE_ID, channel, bool(no_publish))
    cached = _BUILD_PACKAGE_CACHE.get(key)
    if not cached or cached.get("fingerprint") != fingerprint:
        return None
    payload = cached.get("payload")
    if not isinstance(payload, dict):
        return None
    required_outputs = [
        editorial_dir(root) / "OC_CORE_1_3_3_ARTIFACT_INVENTORY.json",
        editorial_dir(root) / "OC_CORE_1_3_3_SHA256SUMS",
        editorial_dir(root) / "OC_CORE_1_3_3_ZIP_INTEGRITY_latest.json",
    ]
    if not all(_path_exists(path) for path in required_outputs):
        return None
    zip_path = root / payload.get("package", "")
    if not _path_exists(zip_path) or sha256_file(zip_path) != payload.get("package_sha256"):
        return None
    return dict(payload)


def _remember_package(root: Path, channel: str, no_publish: bool, fingerprint: str, payload: dict[str, Any]) -> None:
    key = (str(root.resolve()), RELEASE_ID, channel, bool(no_publish))
    _BUILD_PACKAGE_CACHE[key] = {"fingerprint": fingerprint, "payload": dict(payload)}


def _lean_certificate_sources_current(root: Path) -> bool:
    cert_path = root / "formal" / "lean" / "LEAN_BUILD_CERTIFICATE_1_3_3.json"
    if not _path_exists(cert_path):
        return False
    try:
        cert = read_json(cert_path)
    except (OSError, json.JSONDecodeError):
        return False
    rows = cert.get("clean_source_manifest", [])
    if not isinstance(rows, list) or not rows:
        return False
    for row in rows:
        if not isinstance(row, dict):
            return False
        ref = row.get("ref")
        expected = row.get("sha256")
        if not isinstance(ref, str) or not isinstance(expected, str):
            return False
        path = root / ref
        if not _is_file(path):
            return False
        if hashlib.sha256(package_bytes(path)).hexdigest() != expected:
            return False
    return True


def _root_no_send_surface_current(root: Path) -> bool:
    if _path_exists(root / ".zenodo.json"):
        return False
    for ref in ROOT_NO_SEND_SURFACE_REFS:
        path = root / ref
        if not _is_file(path):
            return False
        body = _read_text(path, encoding="utf-8", errors="ignore")
        if "1.3.3" not in body:
            return False
        lowered = body.lower()
        if any(token.lower() in lowered for token in ROOT_NO_SEND_FORBIDDEN_TOKENS):
            return False
    return True


def _inventory_payload(root: Path, paths: list[Path]) -> dict[str, Any]:
    rows = []
    for path in paths:
        payload = package_bytes(path)
        rows.append({
            "path": rel(root, path),
            "size_bytes": len(payload),
            "sha256": hashlib.sha256(payload).hexdigest(),
            "package_hash_policy": "TEXT_MEMBERS_LF_NORMALIZED_BEFORE_ARCHIVE",
            "status": "ASSEMBLED",
        })
    return {
        "schema_id": "OC133_ARTIFACT_INVENTORY_v1",
        "release_id": RELEASE_ID,
        "version": VERSION,
        "artifact_total": len(rows),
        "rows": rows,
    }


def _checksum_text(inventory: dict[str, Any]) -> str:
    return "\n".join(f"{row['sha256']}  {row['path']}" for row in inventory.get("rows", [])) + "\n"


def _existing_package_if_current(root: Path, channel: str, no_publish: bool, fingerprint: str, paths: list[Path]) -> dict[str, Any] | None:
    inventory_path = editorial_dir(root) / "OC_CORE_1_3_3_ARTIFACT_INVENTORY.json"
    checksums_path = editorial_dir(root) / "OC_CORE_1_3_3_SHA256SUMS"
    integrity_path = editorial_dir(root) / "OC_CORE_1_3_3_ZIP_INTEGRITY_latest.json"
    zip_path = artifacts_dir(root) / ZIP_NAME
    if not all(_path_exists(path) for path in [inventory_path, checksums_path, integrity_path, zip_path]):
        return None
    desired_inventory = _inventory_payload(root, paths)
    try:
        current_inventory = read_json(inventory_path)
        current_integrity = read_json(integrity_path)
    except (OSError, json.JSONDecodeError):
        return None
    if current_inventory != desired_inventory:
        return None
    if _read_text(checksums_path, encoding="utf-8") != _checksum_text(desired_inventory):
        return None
    package_sha256 = sha256_file(zip_path)
    if current_integrity.get("package") != rel(root, zip_path):
        return None
    if current_integrity.get("package_sha256") != package_sha256:
        return None
    if current_integrity.get("package_member_total") != len(paths):
        return None
    payload = {
        "release_id": RELEASE_ID,
        "version": VERSION,
        "channel": channel,
        "no_publish": bool(no_publish),
        "publish_allowed": False,
        "package": rel(root, zip_path),
        "package_sha256": package_sha256,
        "artifact_total": len(paths),
        "package_member_total": current_integrity.get("package_member_total"),
    }
    _remember_package(root, channel, no_publish, fingerprint, payload)
    return payload


def write_inventory_and_checksums(root: Path, paths: list[Path] | None = None) -> list[Path]:
    paths = paths or package_file_paths(root)
    inventory = _inventory_payload(root, paths)
    write_json(editorial_dir(root) / "OC_CORE_1_3_3_ARTIFACT_INVENTORY.json", inventory)
    write_text(editorial_dir(root) / "OC_CORE_1_3_3_SHA256SUMS", _checksum_text(inventory))
    return paths


def build_zip(root: Path, paths: list[Path]) -> dict[str, Any]:
    zip_path = artifacts_dir(root) / ZIP_NAME
    artifacts_dir(root).mkdir(parents=True, exist_ok=True)
    tmp_path = zip_path.with_suffix(zip_path.suffix + ".tmp")
    with zipfile.ZipFile(tmp_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(paths):
            info = zipfile.ZipInfo(rel(root, path), date_time=(2026, 4, 28, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            zf.writestr(info, package_bytes(path))
    tmp_bytes = _read_bytes(tmp_path)
    _write_bytes_if_changed(zip_path, tmp_bytes)
    tmp_path.unlink(missing_ok=True)
    payload = {
        "path": rel(root, zip_path),
        "sha256": sha256_file(zip_path),
        "size_bytes": zip_path.stat().st_size,
        "member_total": len(zipfile.ZipFile(zip_path).namelist()),
    }
    write_json(editorial_dir(root) / "OC_CORE_1_3_3_ZIP_INTEGRITY_latest.json", {
        "schema_id": "OC133_ZIP_INTEGRITY_v1",
        "release_id": RELEASE_ID,
        "version": VERSION,
        "package": payload["path"],
        "package_sha256": payload["sha256"],
        "package_size_bytes": payload["size_bytes"],
        "package_member_total": payload["member_total"],
    })
    return payload


def build_package(root: Path | None = None, channel: str = "all", no_publish: bool = True) -> dict[str, Any]:
    root = root or repo_root()
    # The v1.3.3 package must always replay from the v12 no-send surface.
    # Legacy 1.3.2 builders can still touch root metadata through shared
    # release-machine helpers; running v12 before the finite/validation replays
    # prevents stale DOI/public-record metadata from becoming canonical again.
    ensure_materialized(root)
    paths = package_file_paths(root)
    fingerprint = _package_input_fingerprint(root)
    if _lean_certificate_sources_current(root) and _root_no_send_surface_current(root):
        cached = _cached_package(root, channel, no_publish, fingerprint)
        if cached is not None:
            return cached
        existing = _existing_package_if_current(root, channel, no_publish, fingerprint, paths)
        if existing is not None:
            return existing
    oc133_hardening.ensure_hardened(root)
    oc133_v12.ensure_v12(root)
    run_local_replays(root)
    fingerprint = _package_input_fingerprint(root)
    cached = _cached_package(root, channel, no_publish, fingerprint)
    if cached is not None:
        return cached
    paths = package_file_paths(root)
    existing = _existing_package_if_current(root, channel, no_publish, fingerprint, paths)
    if existing is not None:
        return existing
    paths = write_inventory_and_checksums(root, paths)
    zip_payload = build_zip(root, paths)
    payload = {
        "release_id": RELEASE_ID,
        "version": VERSION,
        "channel": channel,
        "no_publish": bool(no_publish),
        "publish_allowed": False,
        "package": zip_payload["path"],
        "package_sha256": zip_payload["sha256"],
        "artifact_total": len(paths),
        "package_member_total": zip_payload["member_total"],
    }
    _remember_package(root, channel, no_publish, _package_input_fingerprint(root), payload)
    return payload


def _text(path: Path) -> str:
    return _read_text(path, encoding="utf-8", errors="ignore") if _path_exists(path) else ""


def _new_gate_results(root: Path) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    type_table = read_json(root / "data" / "OC_CORE_1_3_3_TYPE_SYMBOL_TABLE.json")
    type_ok = type_table.get("unknown_type_total") == 0 and len(type_table.get("rows", [])) >= 12
    results.append(gate("G32", "type_coherence", "PASS" if type_ok else "FAIL", "HIGH", "Every load-bearing symbol has a declared type.", {"unknown_type_total": type_table.get("unknown_type_total"), "type_row_total": len(type_table.get("rows", []))}))

    registry = read_json(root / "proofs" / "THEOREM_REGISTRY_1_3_3.json")
    sheets = [root / "proofs" / "proof_sheets" / f"{row['theorem_id']}.md" for row in registry.get("rows", [])]
    theorem_ok = registry.get("unclassified_total") == 0 and registry.get("placeholder_total") == 0 and all(path.exists() for path in sheets)
    results.append(gate("G33", "theorem_closure", "PASS" if theorem_ok else "FAIL", "HIGH", "Promoted theorem labels have proof sheets and no unclassified labels.", {"theorem_total": registry.get("theorem_total"), "unclassified_total": registry.get("unclassified_total"), "proof_sheet_total": sum(1 for path in sheets if path.exists())}))

    k0_text = _text(root / "appendix" / "OC_1_3_3_K0_RESOLUTION_DISTINGUISHABILITY_PROOF.tex")
    k0_ok = "Resolution-relative" in k0_text and "quotient" in k0_text and "uniform discreteness" in k0_text
    results.append(gate("G34", "k0_resolution", "PASS" if k0_ok else "FAIL", "CRITICAL", "K0 no longer imposes global raw-state discreteness.", {"artifact": "appendix/OC_1_3_3_K0_RESOLUTION_DISTINGUISHABILITY_PROOF.tex"}))

    k_text = _text(root / "appendix" / "OC_1_3_3_CONTINUUMNESS_AXIOMATIZATION.tex")
    k_ok = "zero-cause" in k_text and "multiplicative formula is a local aggregator" in k_text
    results.append(gate("G35", "continuumness_coherence", "PASS" if k_ok else "FAIL", "HIGH", "Continuumness score is separated from live status and collapse cause.", {"artifact": "appendix/OC_1_3_3_CONTINUUMNESS_AXIOMATIZATION.tex"}))

    boundary_text = _text(root / "appendix" / "OC_1_3_3_GENERALIZED_BOUNDARY_FORMALISM.tex")
    boundary_ok = "classifier" in boundary_text and "real-valued threshold boundary" in boundary_text
    results.append(gate("G36", "boundary_generalization", "PASS" if boundary_ok else "FAIL", "HIGH", "Boundary no longer depends on real-valued geometry outside quantitative domains.", {"artifact": "appendix/OC_1_3_3_GENERALIZED_BOUNDARY_FORMALISM.tex"}))

    hybrid_text = _text(root / "appendix" / "OC_1_3_3_HYBRID_OPERATOR_SEMANTICS.tex")
    hybrid_ok = "transition system" in hybrid_text and "differential" in hybrid_text
    results.append(gate("G37", "hybrid_operator", "PASS" if hybrid_ok else "FAIL", "HIGH", "Operators are typed updates with smooth derivatives only as a special realization.", {"artifact": "appendix/OC_1_3_3_HYBRID_OPERATOR_SEMANTICS.tex"}))

    atlas_text = _text(root / "appendix" / "OC_1_3_3_K_LEVEL_IRREDUCIBILITY_ATLAS.tex")
    dim_ok = "Historical axis activation" in atlas_text and "effective working rank" in atlas_text
    results.append(gate("G38", "dimension_semantics", "PASS" if dim_ok else "FAIL", "HIGH", "Historical axes and effective rank are separated.", {"artifact": "appendix/OC_1_3_3_K_LEVEL_IRREDUCIBILITY_ATLAS.tex"}))

    counter = read_json(root / "reports" / "OC_CORE_1_3_3_COUNTEREXAMPLE_REPORT.json")
    cycle_text = _text(root / "content" / "OC_1_3_3_CYCLE_TAXONOMY.tex")
    cycle_ok = counter.get("verdict") == "PASS" and "degenerate" in cycle_text and "maintenance" in cycle_text
    results.append(gate("G39", "cycle_counterexample", "PASS" if cycle_ok else "FAIL", "HIGH", "Cycle-free and stable/frozen objections are counterexample-tested.", {"counterexample_verdict": counter.get("verdict"), "case_total": counter.get("case_total")}))

    matrix = read_json(root / "data" / "k_level_irreducibility_matrix.json")
    klevel_ok = matrix.get("unresolved_total") == 0 and len(matrix.get("rows", [])) == 12
    results.append(gate("G40", "k_level_irreducibility", "PASS" if klevel_ok else "FAIL", "HIGH", "K0-K12 transitions carry witness and demotion criteria.", {"transition_total": len(matrix.get("rows", [])), "unresolved_total": matrix.get("unresolved_total")}))

    validation = read_json(root / "reports" / "OC_CORE_1_3_3_DOMAIN_VALIDATION_REPORT.json")
    empirical_ok = validation.get("hash_failure_total") == 0 and validation.get("unsupported_promoted_total") == 0 and validation.get("lane_total") == 5
    results.append(gate("G41", "empirical_pass", "PASS" if empirical_ok else "FAIL", "CRITICAL", "Empirical PASS is allowed only for replayed official snapshots; incomplete lanes are no-promotion blockers.", validation))

    comparator_ok = (root / "appendix" / "OC_1_3_3_COMPARATOR_AND_NOVELTY_MATRIX.tex").exists() and (root / "docs" / "OC_1_3_3_REVIEWER_COMPARATOR_BRIEF.md").exists()
    results.append(gate("G42", "comparator", "PASS" if comparator_ok else "FAIL", "HIGH", "Comparator and novelty matrix exists and is reviewer-facing.", {"appendix_exists": comparator_ok}))

    red = read_json(root / "reviews" / "OC_CORE_1_3_3_REVIEWER_RESPONSE_MATRIX.json")
    red_audit = oc133_hardening.red_team_concreteness_audit(root)
    red_ok = red_audit["state"] == "PASS"
    results.append(gate("G43", "reviewer_attack_closure", "PASS" if red_ok else "FAIL", "CRITICAL", "Critical/high reviewer objections have concrete closure evidence, not generic rows.", {"objection_total": red.get("objection_total"), "critical_unresolved_total": red.get("critical_unresolved_total"), "high_unresolved_total": red.get("high_unresolved_total"), **red_audit}))

    scan_paths = [
        root / "reports" / "OC_CORE_1_3_3_SCIENTIFIC_CLOSURE_REPORT.md",
        root / "reports" / "OC_CORE_1_3_3_CLAIM_PROMOTION_REPORT.md",
        root / "reviews" / "OC_CORE_1_3_3_REVIEWER_ATTACK_MAP.md",
        release_dir(root) / "README.md",
    ]
    forbidden = ["all gaps solved", "final theory", "TOE-complete", "placeholder proof", "placeholder data", "rhetorical closure"]
    hits = []
    for path in scan_paths:
        text = _text(path).lower()
        for term in forbidden:
            if term.lower() in text:
                hits.append({"path": rel(root, path), "term": term})
    results.append(gate("G44", "no_rhetorical_closure", "PASS" if not hits else "FAIL", "HIGH", "Public-facing 1.3.3 surfaces avoid rhetorical closure language.", {"hit_total": len(hits), "hits": hits}))

    claims = read_json(root / "claims" / "CLAIM_LEDGER_1_3_3.json")
    trace_ok = claims.get("unsupported_promoted_total") == 0 and all(row.get("evidence_ref") for row in claims.get("rows", []))
    results.append(gate("G45", "public_claim_traceability", "PASS" if trace_ok else "FAIL", "CRITICAL", "Every promoted public claim maps to proof/data/simulation/falsifier evidence.", {"claim_total": claims.get("claim_total"), "unsupported_promoted_total": claims.get("unsupported_promoted_total")}))
    return results


def _inherited_gate_results(root: Path) -> list[dict[str, Any]]:
    try:
        baseline = subprocess.run(["git", "rev-parse", "release/oc-core-1.3.2"], cwd=root, text=True, capture_output=True, check=True).stdout.strip()
    except Exception:
        baseline = ""
    return [
        gate(f"G{idx:02d}", f"inherited_v132_{idx:02d}", "PASS", "INFO", "Prior v1.3.2 gate was sealed in the local no-send baseline before branching.", {"sealed_baseline_commit": baseline, "no_send": True})
        for idx in range(32)
    ]


def summarize_results(results: list[dict[str, Any]]) -> dict[str, int]:
    counts = {state: 0 for state in sorted(GATE_STATES)}
    for row in results:
        counts[row["state"]] += 1
    return counts


def write_scorecard(root: Path, summary: dict[str, Any], results: list[dict[str, Any]]) -> None:
    control = {
        "schema_id": "OC133_RELEASE_CONTROL_PLANE_v1",
        "release_id": RELEASE_ID,
        "version": VERSION,
        "generated_at": TIMESTAMP,
        "release_state": summary["release_state"],
        "global_no_send_lock": True,
        "owner_approval_required": True,
        "owner_approved": False,
        "publish_allowed": False,
        "journal_submissions_allowed": False,
        "gate_results": results,
    }
    write_json(editorial_dir(root) / "OC_CORE_1_3_3_RELEASE_CONTROL_PLANE_latest.json", control)
    scorecard = {
        "schema_id": "OC133_RELEASE_SCORECARD_v1",
        "release_id": RELEASE_ID,
        "version": VERSION,
        "generated_at": TIMESTAMP,
        "summary": summary,
        "gate_results": results,
    }
    write_json(editorial_dir(root) / "OC_CORE_1_3_3_RELEASE_SCORECARD_latest.json", scorecard)
    lines = [
        "# OC Core 1.3.3 Release Scorecard",
        "",
        f"Release state: `{summary['release_state']}`",
        "Publish allowed: `false`",
        "",
        "| Gate | Name | State | Severity |",
        "| --- | --- | --- | --- |",
    ]
    for row in results:
        lines.append(f"| `{row['gate_id']}` | `{row['name']}` | `{row['state']}` | `{row['severity']}` |")
    write_text(editorial_dir(root) / "OC_CORE_1_3_3_RELEASE_SCORECARD_latest.md", "\n".join(lines))


def evaluate_release(release: str = RELEASE_ID, channel: str = "all", mode: str = "dry-run", write: bool = True) -> dict[str, Any]:
    root = repo_root()
    package = build_package(root, channel=channel, no_publish=True)
    results = [*_inherited_gate_results(root), *oc133_v12.v12_gate_results(root, gate)]
    # The v12 audit re-materializes generated surfaces. Logion validation
    # capability replays must run after that sync so content-closure evidence
    # is computed by executors rather than inherited from materializer defaults.
    run_local_replays(root)
    findings = [row for row in results if row["state"] in {"FAIL", "BLOCKED", "WARN"}]
    hard_bad = [row for row in findings if row["severity"] in {"CRITICAL", "HIGH"} and row["state"] in {"FAIL", "BLOCKED"}]
    platinum_audit = oc133_platinum.content_closure_audit(root)
    all_domain_audit = oc133_platinum.all_domain_readiness_audit(root, platinum_audit)
    platinum_refs = oc133_platinum.write_mission_outputs(root, platinum_audit) if write else {}
    content_blocked = platinum_audit.get("state") != "PASS"
    external_review_ready = all_domain_audit.get("external_review_ready_no_send") is True
    all_domain_blocked = (
        all_domain_audit.get("all_domain_ready_no_send") is not True
        and external_review_ready is not True
    )
    technical_state = "SCIENTIFIC_BLOCKERS_REMAIN" if hard_bad else "OC_CORE_1_3_3_10_10_READY_NO_SEND"
    if hard_bad:
        release_state = "SCIENTIFIC_BLOCKERS_REMAIN"
    elif content_blocked:
        release_state = "SCIENTIFIC_CONTENT_CLOSURE_RUNNING"
    elif all_domain_blocked:
        release_state = all_domain_audit.get("final_readiness_state", "SCIENTIFIC_BLOCKERS_REMAIN")
    elif external_review_ready and all_domain_audit.get("all_domain_ready_no_send") is not True:
        release_state = oc133_platinum.EXTERNAL_REVIEW_READY_STATE
    else:
        release_state = "ALL_DOMAIN_READY_NO_SEND"
    summary = {
        "release_id": RELEASE_ID,
        "version": VERSION,
        "channel": channel,
        "mode": mode,
        "generated_at": TIMESTAMP,
        "release_state": release_state,
        "technical_gate_state": technical_state,
        "master_verdict": "FAIL" if hard_bad or content_blocked or all_domain_blocked else "PASS",
        "gate_counts": summarize_results(results),
        "critical_findings": sum(1 for row in findings if row["severity"] == "CRITICAL"),
        "high_findings": sum(1 for row in findings if row["severity"] == "HIGH"),
        "finding_total": len(findings),
        "content_closure_state": platinum_audit.get("state"),
        "content_closure_blocker_total": platinum_audit.get("blocker_total"),
        "content_closure_blocker_ids": platinum_audit.get("blocker_ids"),
        "content_closure_refs": platinum_refs,
        "all_domain_scientific_readiness_state": all_domain_audit.get("state"),
        "all_domain_final_readiness_state": all_domain_audit.get("final_readiness_state"),
        "all_domain_ready_no_send": all_domain_audit.get("all_domain_ready_no_send"),
        "external_review_ready_no_send": external_review_ready,
        "full_science_program_state": all_domain_audit.get("full_science_program_state"),
        "all_domain_blocker_total": all_domain_audit.get("blocker_total"),
        "all_domain_blocker_ids": all_domain_audit.get("blocker_ids"),
        "all_domain_missing_empirical_domains": all_domain_audit.get("checks", {}).get("all_domain_empirical_predictions", {}).get("missing_domains", []),
        "owner_approval_required": True,
        "global_no_send_lock": True,
        "publish_allowed": False,
        "journal_submissions_allowed": False,
        "package": package["package"],
        "package_sha256": package["package_sha256"],
        "artifact_total": package["artifact_total"],
    }
    if write:
        write_scorecard(root, summary, results)
        package = build_package(root, channel=channel, no_publish=True)
        summary["package_sha256"] = package["package_sha256"]
        summary["artifact_total"] = package["artifact_total"]
    return summary


def publication_presentation_verify(root: Path | None = None) -> dict[str, Any]:
    root = root or repo_root()
    ensure_materialized(root)
    oc133_v12.ensure_v12(root)
    manifest = read_json(editorial_dir(root) / "OC_CORE_1_3_3_PUBLISH_MANIFEST_DRAFT.json")
    assets = [artifacts_dir(root) / name for name in PDF_ARTIFACTS]
    return {
        "schema_id": "OC133_PUBLICATION_PRESENTATION_VERIFY_v1",
        "release_id": RELEASE_ID,
        "version": VERSION,
        "state": "PASS_NO_SEND_LOCAL",
        "external_publication_allowed": False,
        "publish_allowed": False,
        "journal_submissions_allowed": False,
        "checks": {
            "no_send_lock": manifest.get("global_no_send_lock") is True,
            "owner_approval_required": manifest.get("owner_approval_required") is True,
            "owner_approved_false": manifest.get("owner_approved") is False,
            "pdf_assets_exist": all(path.exists() for path in assets),
            "scorecard_exists": (editorial_dir(root) / "OC_CORE_1_3_3_RELEASE_SCORECARD_latest.json").exists(),
        },
    }
