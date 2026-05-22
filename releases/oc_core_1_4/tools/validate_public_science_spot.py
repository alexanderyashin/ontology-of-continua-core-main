from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


RELEASE_REL = Path("releases/oc_core_1_4")
SPOT_REL = RELEASE_REL / "science_spot"
ADMIN_REL = RELEASE_REL / "admin"

GRAPH_REL = SPOT_REL / "OC_CORE_1_4_PUBLIC_SCIENCE_SPOT_GRAPH.json"
INVENTORY_REL = ADMIN_REL / "OC_CORE_1_4_PUBLIC_SCIENCE_SPOT_INVENTORY.json"
CHECKLIST_REL = ADMIN_REL / "OC_CORE_1_4_PUBLIC_SCIENCE_SPOT_CHECKLIST.json"
QUALITY_REL = ADMIN_REL / "OC_CORE_1_4_PUBLIC_SCIENCE_SPOT_QUALITY_CONTRACT.json"
MANIFEST_REL = RELEASE_REL / "OC_CORE_1_4_FILE_MANIFEST.json"
CHECKSUM_REL = RELEASE_REL / "SHA256SUMS.txt"

_BS = "\\"
_USER = "Mega" + "port"
_SOURCE_REPO = "estra-" + "private-work"
_TMP_PUBLIC = "_tmp_oc_core_" + "public"
_REMOTE_REPO = "ESTRA-" + "Private"
_PRIVATE_STATUS = "LOGION_" + "PRIVATE_BUSINESS_PLAN"

HARD_LEAK_TOKENS = [
    "C:" + _BS + "Users",
    "C:" + (_BS * 2) + "Users",
    _USER,
    _SOURCE_REPO,
    _TMP_PUBLIC,
    _REMOTE_REPO,
    _PRIVATE_STATUS,
]

REQUIRED_PACKAGES = {f"{i:03d}" for i in range(24, 47)}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def manifest_path_to_file(repo: Path, rel: str) -> Path:
    if rel == ".gitattributes":
        return repo / rel
    return repo / RELEASE_REL / rel


def active_manifest_files(repo: Path) -> list[Path]:
    manifest = load_json(repo / MANIFEST_REL)
    return [manifest_path_to_file(repo, row["path"]) for row in manifest["files"]]


def validate_json_parse(repo: Path, failures: list[str]) -> None:
    for path in active_manifest_files(repo):
        if path.suffix.lower() != ".json":
            continue
        try:
            load_json(path)
        except Exception as exc:  # pragma: no cover - failure report path
            failures.append(f"{path.relative_to(repo).as_posix()}: {exc}")


def validate_no_hard_leaks(repo: Path, leaks: list[str]) -> None:
    for path in active_manifest_files(repo):
        if path.suffix.lower() not in {".json", ".md", ".py", ".lean", ".txt", ".cff", ".toml", ".csv", ".bib", ".tex"}:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for token in HARD_LEAK_TOKENS:
            if token in text:
                leaks.append(f"{path.relative_to(repo).as_posix()}: {token}")


def validate_graph(repo: Path, problems: list[str]) -> None:
    graph_path = repo / GRAPH_REL
    if not graph_path.exists():
        problems.append("missing science SPOT graph")
        return
    graph = load_json(graph_path)
    nodes = graph.get("nodes", [])
    edges = graph.get("edges", [])
    ids = set()
    for node in nodes:
        for key in ["id", "kind", "status", "source_ref", "hash"]:
            if key not in node or node[key] in ("", None):
                problems.append(f"node missing {key}: {node.get('id', '<unknown>')}")
        if node.get("id") in ids:
            problems.append(f"duplicate node id: {node.get('id')}")
        ids.add(node.get("id"))
    for edge in edges:
        if edge.get("source") not in ids:
            problems.append(f"edge missing source endpoint: {edge}")
        if edge.get("target") not in ids:
            problems.append(f"edge missing target endpoint: {edge}")
    claim_nodes = [n for n in nodes if n.get("kind") == "absolute_proof_claim"]
    if len(claim_nodes) != 807:
        problems.append(f"absolute proof claim node count mismatch: {len(claim_nodes)} != 807")
    status_counts: dict[str, int] = {}
    proof_counts: dict[str, int] = {}
    for node in claim_nodes:
        status_counts[str(node.get("status"))] = status_counts.get(str(node.get("status")), 0) + 1
        proof_counts[str(node.get("proof_mode"))] = proof_counts.get(str(node.get("proof_mode")), 0) + 1
    expected_status = {
        "PROVED_CLOSED_WITH_PROOFS": 664,
        "REFUTED_REPAIRED_AND_PROVED_WITH_PROOFS": 130,
        "REFUTED_WITH_COUNTERPROOF": 13,
    }
    if status_counts != expected_status:
        problems.append(f"absolute proof status counts mismatch: {status_counts}")
    if proof_counts.get("empirical") != 134:
        problems.append(f"empirical proof-mode count mismatch: {proof_counts}")
    if graph.get("summary", {}).get("manual_claim_campaign_023") != "excluded_nonfoundational_zero_terminal_bindings":
        problems.append("023 manual claim campaign boundary missing or incorrect")


def validate_inventory(repo: Path, problems: list[str]) -> None:
    inv_path = repo / INVENTORY_REL
    if not inv_path.exists():
        problems.append("missing SPOT inventory")
        return
    inventory = load_json(inv_path)
    rows = inventory.get("rows", [])
    packages = {str(row.get("package_id")) for row in rows if row.get("package_id")}
    missing = REQUIRED_PACKAGES - packages
    if missing:
        problems.append(f"inventory missing package ids: {sorted(missing)}")
    for raw_db in (repo / SPOT_REL).rglob("*.sqlite"):
        problems.append(f"raw sqlite present in public SPOT: {raw_db.relative_to(repo).as_posix()}")
    for rel in [CHECKLIST_REL, QUALITY_REL, SPOT_REL / "formal/FORMAL_PACKAGE_INDEX.json", SPOT_REL / "prior_art/PUBLIC_PRIOR_ART_COMPARATOR_MAP.json"]:
        if not (repo / rel).exists():
            problems.append(f"missing required SPOT/admin artifact: {rel.as_posix()}")


def validate_manifest_and_checksums(repo: Path, problems: list[str]) -> None:
    manifest_path = repo / MANIFEST_REL
    checksum_path = repo / CHECKSUM_REL
    root_manifest_path = repo / "PUBLIC_PAYLOAD_MANIFEST.json"
    root_checksum_path = repo / "checksums.txt"
    if not manifest_path.exists() or not checksum_path.exists():
        problems.append("missing manifest or checksum file")
        return
    manifest = load_json(manifest_path)
    root_manifest = load_json(root_manifest_path)
    if manifest != root_manifest:
        problems.append("root PUBLIC_PAYLOAD_MANIFEST.json differs from release manifest")
    checksum_text = checksum_path.read_text(encoding="utf-8")
    if checksum_text != root_checksum_path.read_text(encoding="utf-8"):
        problems.append("root checksums.txt differs from release SHA256SUMS.txt")
    checksum_map = {}
    for line in checksum_text.splitlines():
        if not line.strip():
            continue
        digest, rel = line.split("  ", 1)
        checksum_map[rel] = digest
    manifest_paths = {row["path"] for row in manifest.get("files", [])}
    if set(checksum_map) != manifest_paths:
        problems.append("manifest paths and checksum paths differ")
    for row in manifest.get("files", []):
        rel = row["path"]
        path = manifest_path_to_file(repo, rel)
        if not path.exists():
            problems.append(f"manifest file missing: {rel}")
            continue
        digest = sha256_file(path)
        if digest != row["sha256"] or digest != checksum_map.get(rel):
            problems.append(f"checksum mismatch: {rel}")
        if path.stat().st_size != row["size_bytes"]:
            problems.append(f"size mismatch: {rel}")
    required = {
        "science_spot/OC_CORE_1_4_PUBLIC_SCIENCE_SPOT_GRAPH.json",
        "admin/OC_CORE_1_4_PUBLIC_SCIENCE_SPOT_CHECKLIST.json",
        "admin/OC_CORE_1_4_PUBLIC_SCIENCE_SPOT_QUALITY_CONTRACT.json",
        "admin/OC_CORE_1_4_PUBLIC_SCIENCE_SPOT_INVENTORY.json",
    }
    missing_required = required - manifest_paths
    if missing_required:
        problems.append(f"manifest missing SPOT artifacts: {sorted(missing_required)}")


def main() -> int:
    repo = Path.cwd().resolve()
    failures: list[str] = []
    leaks: list[str] = []
    problems: list[str] = []
    validate_json_parse(repo, failures)
    validate_no_hard_leaks(repo, leaks)
    validate_graph(repo, problems)
    validate_inventory(repo, problems)
    validate_manifest_and_checksums(repo, problems)
    if failures or leaks or problems:
        print("FAIL public science SPOT validator")
        if failures:
            print("json_failures=" + json.dumps(failures[:20], ensure_ascii=False))
        if leaks:
            print("leaks=" + json.dumps(leaks[:20], ensure_ascii=False))
        if problems:
            print("problems=" + json.dumps(problems[:40], ensure_ascii=False))
        return 1
    graph = load_json(repo / GRAPH_REL)
    print(
        "PASS public science SPOT validator: "
        f"nodes={len(graph['nodes'])} edges={len(graph['edges'])} "
        f"claims=807 statuses={graph['summary']['absolute_proof_status_counts']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
