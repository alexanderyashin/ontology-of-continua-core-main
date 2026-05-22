from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]


def _repo_root() -> Path:
    for parent in [ROOT] + list(ROOT.parents):
        if (parent / "AGENTS.md").exists() or (parent / ".git").exists():
            return parent
    return ROOT.parents[9]


REPO_ROOT = _repo_root()
DEMO_DATA = ROOT / "oc_core_demo" / "data"
TARGETS_PATH = DEMO_DATA / "public_targets.json"
GRAPH_PATH = DEMO_DATA / "interactive_graph.json"
LEDGER_PATH = DEMO_DATA / "proof_placeholder_closure_ledger.json"
DOSSIERS_PATH = REPO_ROOT / "logion" / "k0" / "governance" / "status" / "LOGION_SCIENCE_TARGET_TERMINAL_DOSSIERS_V540_latest.json"
DEMO_VERSION = "V010"
RELEASE_ORDINAL = "010"

PLACEHOLDER_MARKERS = (
    "Frozen proof/refute target",
    "Frozen 019 proof/refute target",
)


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, allow_nan=False, indent=2), encoding="utf-8")


def _canonical(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=False, allow_nan=False, sort_keys=True, separators=(",", ":"))


def _hash(payload: Any) -> str:
    return hashlib.sha256(_canonical(payload).encode("utf-8")).hexdigest()


def _clean(value: Any, limit: int = 900) -> str:
    text = str(value or "")
    replacements = {
        "\ufb00": "ff",
        "\ufb01": "fi",
        "\ufb02": "fl",
        "\ufb03": "ffi",
        "\ufb04": "ffl",
        "\u2018": "'",
        "\u2019": "'",
        "\u201c": '"',
        "\u201d": '"',
        "\u0001": "",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) > limit:
        return text[: limit - 1].rstrip() + "..."
    return text


def _is_placeholder(value: Any) -> bool:
    text = _clean(value, 10_000)
    return not text or any(marker in text for marker in PLACEHOLDER_MARKERS)


def _release_text(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _release_text(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_release_text(item) for item in value]
    if isinstance(value, str):
        return (
            value.replace("Version 004", "Version 010")
            .replace("Version 005", "Version 010")
            .replace("Version 006", "Version 010")
            .replace("Version 007", "Version 010")
            .replace("Version 008", "Version 010")
            .replace("Version 009", "Version 010")
            .replace("V007", DEMO_VERSION)
            .replace("V004", DEMO_VERSION)
            .replace("V005", DEMO_VERSION)
            .replace("V006", DEMO_VERSION)
            .replace("V008", DEMO_VERSION)
            .replace("V009", DEMO_VERSION)
        )
    return value


def _target_index(public_target_id: str) -> int:
    match = re.fullmatch(r"OC14-N(\d{3})", public_target_id)
    if not match:
        raise ValueError(f"unsupported public target id: {public_target_id}")
    return int(match.group(1)) - 1


def _statement_from_dossier(row: dict[str, Any]) -> str:
    statement = row.get("exact_statement", "")
    if isinstance(statement, dict):
        statement = statement.get("statement", "")
    return _clean(statement, 900)


def _replacement_for(row: dict[str, Any], public_target_id: str) -> tuple[str, str]:
    source_target_id = str(row.get("target_id") or public_target_id)
    candidate = _statement_from_dossier(row)
    if candidate and not _is_placeholder(candidate):
        return candidate, "CLOSED_SOURCE_REPAIRED"
    return (
        "Public proof/refute obligation for "
        f"{source_target_id}: the exact frozen 019 source proposition is not available as a public-safe statement in this bundle; "
        f"{DEMO_VERSION} records the proof-workbench boundary instead of presenting a solved claim.",
        "DEMOTED_NON_RELEASE_ROW",
    )


def close_placeholders() -> dict[str, Any]:
    targets_payload = _read_json(TARGETS_PATH)
    graph_payload = _read_json(GRAPH_PATH)
    dossiers = _read_json(DOSSIERS_PATH).get("dossier_rows", [])
    if not isinstance(dossiers, list) or len(dossiers) < len(targets_payload.get("targets", [])):
        raise RuntimeError("terminal dossier ledger does not cover public target rows")

    graph_nodes = {str(row.get("id")): row for row in graph_payload.get("nodes", []) if isinstance(row, dict)}
    rows: list[dict[str, Any]] = []
    changed = 0
    for target in targets_payload.get("targets", []):
        if not isinstance(target, dict):
            continue
        public_id = str(target.get("public_target_id", ""))
        original = target.get("public_statement_excerpt", "")
        if not _is_placeholder(original):
            target.update(_release_text(target))
            original = target.get("public_statement_excerpt", "")
            node = graph_nodes.get(public_id)
            if node is not None:
                node.update(_release_text(node))
            if str(target.get("closure_status", "")).startswith("CLOSED_") and target.get("source_target_id"):
                rows.append(
                    {
                        "gap_id": f"GAP-PROOF-PLACEHOLDER-{public_id}",
                        "public_target_id": public_id,
                        "source_target_id": target.get("source_target_id", ""),
                        "closure_status": target.get("closure_status", ""),
                        "closure_basis": target.get("closure_basis", "proof placeholder closure"),
                        "source_refs": target.get("closure_source_refs", []),
                        "evidence_hash": target.get("closure_evidence_hash", _hash(target)),
                        "closed_at_build": DEMO_VERSION,
                        "replacement_statement": original,
                        "nonclaim_boundary": target.get("nonclaim_boundary", ""),
                    }
                )
            continue
        dossier = dossiers[_target_index(public_id)]
        source_target_id = str(dossier.get("target_id") or public_id)
        replacement, status = _replacement_for(dossier, public_id)
        basis = "terminal dossier exact statement" if status == "CLOSED_SOURCE_REPAIRED" else "non-release research backlog row"
        nonclaim = (
            f"This {DEMO_VERSION} closure removes a demonstrator display placeholder only; it does not prove or refute the external target, "
            "does not claim external peer review, and does not promote unresolved proof work."
        )
        source_refs = [
            "logion/k0/governance/status/LOGION_SCIENCE_TARGET_TERMINAL_DOSSIERS_V540_latest.json",
            "logion/k0/governance/status/PROOF_OR_REFUTE_FULL_BURNDOWN_EXECUTION_LEDGER_019_latest.json",
        ]
        evidence_hash = _hash(
            {
                "public_target_id": public_id,
                "source_target_id": source_target_id,
                "replacement": replacement,
                "closure_status": status,
                "terminal_verdict": dossier.get("terminal_verdict", {}),
            }
        )
        target["public_statement_excerpt"] = replacement
        target["source_target_id"] = source_target_id
        target["closure_status"] = status
        target["closure_basis"] = basis
        target["closure_evidence_hash"] = evidence_hash
        target["nonclaim_boundary"] = nonclaim
        target["closure_source_refs"] = source_refs

        node = graph_nodes.get(public_id)
        if node is not None:
            node["statement"] = replacement
            node["source_target_id"] = source_target_id
            node["closure_status"] = status
            node["closure_basis"] = basis
            node["closure_evidence_hash"] = evidence_hash

        rows.append(
            {
                "gap_id": f"GAP-PROOF-PLACEHOLDER-{public_id}",
                "public_target_id": public_id,
                "source_target_id": source_target_id,
                "closure_status": status,
                "closure_basis": basis,
                "source_refs": source_refs,
                "evidence_hash": evidence_hash,
                "closed_at_build": DEMO_VERSION,
                "replacement_statement": replacement,
                "nonclaim_boundary": nonclaim,
            }
        )
        changed += 1

    payload = {
        "schema_version": "oc-core-demo-proof-placeholder-closure.v010",
        "demo_version": DEMO_VERSION,
        "release_ordinal": RELEASE_ORDINAL,
        "status": "PASS",
        "placeholder_rows_closed": len(rows),
        "open_placeholder_rows": 0,
        "newly_repaired_rows": changed,
        "rows": rows,
    }
    payload["ledger_hash"] = _hash(payload)
    _write_json(TARGETS_PATH, targets_payload)
    _write_json(GRAPH_PATH, graph_payload)
    _write_json(LEDGER_PATH, payload)
    return payload


def main() -> int:
    payload = close_placeholders()
    print(json.dumps(payload, ensure_ascii=False, allow_nan=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
