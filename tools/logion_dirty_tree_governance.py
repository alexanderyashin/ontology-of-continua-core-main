from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from release_machine.constants import TIMESTAMP  # noqa: E402


PROJECT_CONTROL_REL = "operations/project_control"
LEDGER_REL = f"{PROJECT_CONTROL_REL}/LOGION_DIRTY_TREE_GOVERNANCE_LEDGER.json"
LEDGER_MD_REL = f"{PROJECT_CONTROL_REL}/LOGION_DIRTY_TREE_GOVERNANCE_LEDGER.md"
SELF_GENERATED_DIR_PREFIX = f"{PROJECT_CONTROL_REL}/"


def work_root(root: Path) -> Path:
    return root.parents[2]


def private_k7_root(root: Path) -> Path:
    return work_root(root) / "estra-private-work" / "logion" / "k7"


def canonical_sha256(payload: Any) -> str:
    return hashlib.sha256(
        json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not text.endswith("\n"):
        text += "\n"
    path.write_text(text, encoding="utf-8", newline="\n")


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def git_status_lines(root: Path) -> list[str]:
    completed = subprocess.run(
        ["git", "status", "--porcelain=v1"],
        cwd=root,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        timeout=30,
    )
    if completed.returncode != 0:
        return [f"!! GIT_STATUS_FAILED::{completed.stderr.strip()}"]
    return [line for line in completed.stdout.splitlines() if line]


def parse_status_line(line: str) -> dict[str, str]:
    status = line[:2]
    path = line[3:] if len(line) > 3 else ""
    if " -> " in path:
        path = path.split(" -> ", 1)[1]
    return {"status": status, "path": path.replace("\\", "/")}


def public_status_rows(root: Path) -> list[dict[str, str]]:
    rows = [parse_status_line(line) for line in git_status_lines(root)]
    return [row for row in rows if SELF_GENERATED_DIR_PREFIX not in row["path"]]


def private_status_rows(root: Path) -> list[dict[str, str]]:
    private = private_k7_root(root)
    if not private.exists():
        return [{"status": "!!", "path": "private_k7_root_missing"}]
    return [parse_status_line(line) for line in git_status_lines(private)]


def classify_public_path(path: str) -> str:
    path = path.replace("\\", "/")
    if path.startswith("operations/project_control/"):
        return "project_control"
    if path in {
        "tools/logion_dirty_tree_governance.py",
        "tools/logion_project_controller.py",
        "tools/logion_delta_queue.py",
        "tools/logion_process_coherence_guard.py",
    }:
        return "project_control"
    if "oc_core_1_3_2" in path or "v1.3.2" in path or path.startswith("reports/parfit/"):
        return "legacy_1_3_2"
    if (
        path.startswith("releases/oc_core_1_3_3/")
        or path in {"manifest.json", "checksums.txt", "ro-crate-metadata.jsonld", "CITATION.cff", ".codemeta.json", ".zenodo.json", "RELEASE_NOTES.md", "VERSION"}
        or path.startswith("formal/lean/")
        or path.startswith("proofs/")
        or path.startswith("falsification/counterexample_search/")
        or path.startswith("claims/")
        or path.startswith("operations/logion_release_mission/oc_core_1_3_3/")
        or path.startswith("release_machine/")
        or path.startswith("reviews/OC_CORE_1_3_3")
        or path.startswith("review/OC_1_3_3")
        or path.startswith("docs/OC_1_3_3")
        or path.startswith("validation/numeric_predictions/")
        or path.startswith("validation/target_blind/")
        or path in {"tools/materialize_oc_core_1_3_3_scientific_closure.py", "tools/materialize_oc_core_1_3_3_v12_closure.py", "tools/oc133_personal_release_audit.py"}
        or path in {"reports/OC_CORE_1_3_3_DOMAIN_VALIDATION_REPORT.json", "reports/OC_CORE_1_3_3_DOMAIN_VALIDATION_REPORT.md"}
    ):
        return "oc133_release_package"
    if (
        path.startswith("benchmarks/modern_science/")
        or path.startswith("comparators/modern_science/")
        or path.startswith("validation/heldout/")
        or path.startswith("validation/grand_science/")
        or path.startswith("reports/OC133_OFFICIAL")
        or path.startswith("reports/OC_CORE_1_3_3_ACQUISITION")
        or path.startswith("reports/OC_CORE_1_3_3_EMPIRICAL")
        or path.startswith("reports/OC_CORE_1_3_3_DOMAIN_EVIDENCE")
        or path.startswith("reports/OC_CORE_1_3_3_GRAND")
        or path.startswith("reports/OC_CORE_1_3_3_HARVESTER")
        or path.startswith("reports/OC_CORE_1_3_3_MODERN_SCIENCE")
        or path.startswith("reports/OC_CORE_1_3_3_STRICT_CLAIM")
        or path.startswith("reviews/oc133_llm_cerberus/repair/")
        or path.startswith("tools/oc133_")
        or path.startswith("tests/test_")
    ):
        return "background_science"
    return "unclassified"


def classify_private_path(path: str) -> str:
    path = path.replace("\\", "/")
    if path.startswith("logion/k0/governance/status/"):
        return "private_release_anchor_governance"
    return "private_unrelated_or_unknown"


def attach_classifications(rows: list[dict[str, str]], *, private: bool = False) -> list[dict[str, str]]:
    classifier = classify_private_path if private else classify_public_path
    result = []
    for row in rows:
        item = dict(row)
        item["classification"] = classifier(row["path"])
        result.append(item)
    return result


def group_counts(rows: list[dict[str, str]]) -> dict[str, int]:
    return dict(sorted(Counter(row["classification"] for row in rows).items()))


def build_ledger(root: Path = ROOT) -> dict[str, Any]:
    public_rows = attach_classifications(public_status_rows(root))
    private_rows = attach_classifications(private_status_rows(root), private=True)
    public_unclassified = [row for row in public_rows if row["classification"] == "unclassified"]
    private_unknown = [row for row in private_rows if row["classification"] == "private_unrelated_or_unknown"]
    fingerprint_payload = {
        "public_rows": public_rows,
        "private_rows": private_rows,
    }
    governed = not public_unclassified and not private_unknown
    ledger = {
        "schema_id": "LOGION_DIRTY_TREE_GOVERNANCE_LEDGER_v1",
        "generated_at": TIMESTAMP,
        "release_id": "oc_core_1_3_3",
        "governance_state": "GOVERNED_DIRTY_TREE" if governed else "DIRTY_TREE_REQUIRES_CLASSIFICATION",
        "public_dirty_total": len(public_rows),
        "public_class_counts": group_counts(public_rows),
        "public_unclassified_total": len(public_unclassified),
        "public_unclassified_rows": public_unclassified[:80],
        "private_dirty_total": len(private_rows),
        "private_class_counts": group_counts(private_rows),
        "private_unknown_total": len(private_unknown),
        "private_unknown_rows": private_unknown[:40],
        "policy": {
            "no_revert": True,
            "public_release_allowed": False,
            "governed_dirty_tree_acceptable_for_no_send_verification": governed,
            "commit_or_ledger_groups": [
                "oc133_release_package",
                "background_science",
                "legacy_1_3_2",
                "private_release_anchor_governance",
            ],
        },
        "public_rows": public_rows,
        "private_rows": private_rows,
        "dirty_tree_fingerprint": canonical_sha256(fingerprint_payload),
        "ledger_sha256": "",
    }
    ledger["ledger_sha256"] = canonical_sha256({key: value for key, value in ledger.items() if key != "ledger_sha256"})
    return ledger


def current_fingerprint(root: Path = ROOT) -> str:
    return canonical_sha256(
        {
            "public_rows": attach_classifications(public_status_rows(root)),
            "private_rows": attach_classifications(private_status_rows(root), private=True),
        }
    )


def render_markdown(ledger: dict[str, Any]) -> str:
    lines = [
        "# Logion Dirty Tree Governance Ledger",
        "",
        f"- State: `{ledger['governance_state']}`",
        f"- Public dirty total: `{ledger['public_dirty_total']}`",
        f"- Public unclassified: `{ledger['public_unclassified_total']}`",
        f"- Private dirty total: `{ledger['private_dirty_total']}`",
        f"- Private unknown: `{ledger['private_unknown_total']}`",
        f"- Fingerprint: `{ledger['dirty_tree_fingerprint']}`",
        "",
        "## Public Classes",
        "",
    ]
    for key, value in ledger["public_class_counts"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Private Classes", ""])
    for key, value in ledger["private_class_counts"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Policy", ""])
    lines.append("- No dirty row is reverted by this ledger.")
    lines.append("- No public action is unlocked by this ledger.")
    lines.append("- A dirty tree is acceptable for no-send verification only when every row is classified.")
    lines.append("")
    return "\n".join(lines)


def write_outputs(root: Path, ledger: dict[str, Any]) -> None:
    write_json(root / LEDGER_REL, ledger)
    write_text(root / LEDGER_MD_REL, render_markdown(ledger))


def check_outputs(root: Path, ledger: dict[str, Any]) -> list[str]:
    mismatches = []
    if read_json(root / LEDGER_REL) != ledger:
        mismatches.append(LEDGER_REL)
    md_path = root / LEDGER_MD_REL
    if not md_path.exists() or md_path.read_text(encoding="utf-8") != render_markdown(ledger):
        mismatches.append(LEDGER_MD_REL)
    return mismatches


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Classify and govern Logion dirty trees without reverting user work.")
    parser.add_argument("--root", default=str(ROOT))
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--check", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    root = Path(args.root).resolve()
    ledger = build_ledger(root)
    if args.write:
        write_outputs(root, ledger)
    if args.check:
        mismatches = check_outputs(root, ledger)
        if mismatches:
            print(json.dumps({"state": "FAIL", "mismatches": mismatches}, ensure_ascii=False, indent=2))
            return 1
    print(
        json.dumps(
            {
                "state": ledger["governance_state"],
                "public_dirty_total": ledger["public_dirty_total"],
                "public_unclassified_total": ledger["public_unclassified_total"],
                "private_dirty_total": ledger["private_dirty_total"],
                "private_unknown_total": ledger["private_unknown_total"],
                "ledger_ref": LEDGER_REL,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0 if ledger["governance_state"] == "GOVERNED_DIRTY_TREE" else 2


if __name__ == "__main__":
    raise SystemExit(main())
