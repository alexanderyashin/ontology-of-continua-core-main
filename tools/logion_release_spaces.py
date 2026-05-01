from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import time
import zipfile
from pathlib import Path
from typing import Any

from pypdf import PdfReader


ROOT = Path(__file__).resolve().parents[1]
RELEASE_ID = "oc_core_1_3_3"
VERSION = "1.3.3"
TAG = "v1.3.3"
GITHUB_RELEASE_URL = "https://github.com/alexanderyashin/ontology-of-continua-core-main/releases/tag/v1.3.3"
ZENODO_RECORD_URL = "https://zenodo.org/records/19957779"
ZENODO_DOI = "10.5281/zenodo.19957779"

CONTROL = ROOT / "operations" / "project_control"
SPACE_MODEL = CONTROL / "LOGION_RELEASE_SPACE_MODEL.json"
SPACE_AUDIT = CONTROL / "LOGION_RELEASE_SPACE_AUDIT.json"
SPACE_COCKPIT = CONTROL / "LOGION_RELEASE_SPACE_COCKPIT.md"

TEXT_SUFFIXES = {".cff", ".json", ".jsonld", ".md", ".tex", ".txt", ".yaml", ".yml"}
PUBLIC_FORBIDDEN_RE = re.compile(
    r"\bNO_SEND\b|no-send|no_send|"
    r"publish_allowed\s*[:=]\s*false|owner_approved\s*[:=]\s*false|"
    r"\"publish_allowed\"\s*:\s*false|\"owner_approved\"\s*:\s*false|"
    r"manifest_kind[^\n]+NOT_PUBLIC_RELEASE|not a public release|"
    r"release DOI:\s*none assigned|public release record:\s*none",
    re.IGNORECASE,
)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def read_json(path: Path, default: Any | None = None) -> Any:
    if not path.exists():
        return {} if default is None else default
    try:
        return json.loads(read_text(path))
    except Exception:
        return {} if default is None else default


def write_text_if_changed(path: Path, text: str) -> bool:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = text.rstrip() + "\n"
    if path.exists() and read_text(path) == data:
        return False
    path.write_text(data, encoding="utf-8", newline="\n")
    return True


def write_json_if_changed(path: Path, payload: Any) -> bool:
    return write_text_if_changed(path, json.dumps(payload, ensure_ascii=False, indent=2))


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def sha256_object(payload: Any) -> str:
    return hashlib.sha256(
        json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def sha256_file(path: Path) -> str | None:
    if not path.is_file():
        return None
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def build_space_model() -> dict[str, Any]:
    spaces = [
        {
            "space_id": "development",
            "purpose": "Mutable science and engineering workbench.",
            "path_prefixes": [
                "content/",
                "appendix/",
                "claims/",
                "comparators/",
                "data/",
                "docs/",
                "formal/",
                "proofs/",
                "simulations/",
                "tools/",
                "release_machine/",
                "validation/",
            ],
            "allowed_control_language": ["draft", "candidate", "blocked", "owner approval required in transition contracts"],
            "public_record_allowed": False,
        },
        {
            "space_id": "verification",
            "purpose": "Evidence, review, gates, incident control, scorecards, and approval contracts.",
            "path_prefixes": [
                "operations/",
                "reports/",
                "reviews/",
                f"releases/{RELEASE_ID}/editorial/",
                f"releases/{RELEASE_ID}/submission_packages/",
            ],
            "allowed_control_language": ["approval locks", "journal submission locks", "failed gates", "no outbound action controls"],
            "public_record_allowed": False,
        },
        {
            "space_id": "release",
            "purpose": "Public-facing scientific artifacts and metadata only.",
            "path_prefixes": [
                "README.md",
                "CITATION.cff",
                ".codemeta.json",
                ".zenodo.json",
                "manifest.json",
                "checksums.txt",
                "ro-crate-metadata.jsonld",
                f"releases/{RELEASE_ID}/README.md",
                f"releases/{RELEASE_ID}/RELEASE_NOTES.md",
                f"releases/{RELEASE_ID}/CHANGELOG.md",
                f"releases/{RELEASE_ID}/artifacts/",
                f"releases/{RELEASE_ID}/public_payload/",
            ],
            "forbidden_control_language": [
                "NO_SEND",
                "no-send",
                "no_send",
                "owner_approved=false",
                "publish_allowed=false",
                "not a public release",
            ],
            "public_record_allowed": True,
        },
    ]
    migrations = [
        {
            "migration_id": "development_to_verification",
            "owner_capability": "Research/ManuscriptIntegration + IT/ReleaseAutomation",
            "source_space": "development",
            "target_space": "verification",
            "executor": "python tools/materialize_oc_core_1_3_3_v12_closure.py",
            "required_gates": ["Lean certificate current", "finite model source binding current", "scorecard regenerated"],
            "may_write_public_release_space": False,
        },
        {
            "migration_id": "verification_to_release",
            "owner_capability": "Publication/PublicRecords + IT/ReleaseAutomation",
            "source_space": "verification",
            "target_space": "release",
            "executor": "python tools/oc133_public_release_payload.py --doi <doi> --zenodo-record-url <url> --github-release-url <url>",
            "required_gates": [
                "science monolith PASS",
                "public payload suitability PASS",
                "release space contamination total = 0",
                "public metadata is HTML/Markdown appropriate per destination",
            ],
            "may_write_public_release_space": True,
        },
        {
            "migration_id": "release_to_public_records",
            "owner_capability": "Publication/PublicRecords",
            "source_space": "release",
            "target_space": "GitHub + Zenodo",
            "executor": "python -m release_machine publish-replace --release-id oc_core_1_3_3",
            "required_gates": [
                "exact public file set",
                "tag-to-HEAD check",
                "Zenodo inherited-file count = 0",
                "postflight PASS",
            ],
            "may_write_public_release_space": False,
        },
    ]
    payload = {
        "schema_id": "LOGION_RELEASE_SPACE_MODEL_v1",
        "release_id": RELEASE_ID,
        "version": VERSION,
        "authority_chain": [
            "Safety Directive",
            "LOGI",
            "K6 Strategy HQ",
            "Project Controller",
            "Capability Directors",
            "Space Migration Executors",
        ],
        "principle": (
            "Development, verification, and release are separate logical spaces. "
            "Approval and outbound-control predicates live in migration contracts and verification ledgers, "
            "not inside public scientific artifacts."
        ),
        "spaces": spaces,
        "migrations": migrations,
        "delta_queue_contract": {
            "semantic_delta_required_for_downstream_trigger": True,
            "read_only_checks_must_not_write_release_space": True,
            "release_space_writes_require_migration_id": "verification_to_release",
        },
    }
    payload["model_hash"] = sha256_object({key: value for key, value in payload.items() if key != "model_hash"})
    return payload


def release_space_paths() -> list[Path]:
    refs = [
        "README.md",
        "CITATION.cff",
        ".codemeta.json",
        ".zenodo.json",
        "manifest.json",
        "checksums.txt",
        "ro-crate-metadata.jsonld",
        f"releases/{RELEASE_ID}/README.md",
        f"releases/{RELEASE_ID}/RELEASE_NOTES.md",
        f"releases/{RELEASE_ID}/CHANGELOG.md",
        f"releases/{RELEASE_ID}/artifacts/OC_CORE_1_3_3_MASTER_MONOGRAPH_EN.pdf",
        f"releases/{RELEASE_ID}/artifacts/OC_CORE_1_3_3_JOURNAL_CORE_EN.pdf",
        f"releases/{RELEASE_ID}/artifacts/OC_CORE_1_3_3_METHODS_AND_REPRODUCIBILITY_COMPANION_EN.pdf",
        f"releases/{RELEASE_ID}/artifacts/OC_CORE_1_3_3_REVIEWER_ATTACK_AND_RESPONSE_MAP_EN.pdf",
        f"releases/{RELEASE_ID}/artifacts/oc_core_1_3_3_public_release.zip",
    ]
    refs.extend(path.relative_to(ROOT).as_posix() for path in sorted((ROOT / f"releases/{RELEASE_ID}/public_payload").rglob("*")) if path.is_file())
    return [ROOT / ref for ref in sorted(set(refs))]


def scan_text(path: Path) -> list[dict[str, Any]]:
    if not path.is_file() or path.suffix.lower() not in TEXT_SUFFIXES:
        return []
    text = read_text(path)
    hits = []
    for match in PUBLIC_FORBIDDEN_RE.finditer(text):
        hits.append(
            {
                "path": rel(path),
                "match": match.group(0),
                "context": text[max(0, match.start() - 80) : match.end() + 120].replace("\n", " ")[:260],
            }
        )
    return hits


def scan_pdf(path: Path) -> dict[str, Any]:
    if not path.is_file() or path.suffix.lower() != ".pdf":
        return {"path": rel(path), "kind": "not_pdf", "forbidden_hit_total": 0, "hits": []}
    reader = PdfReader(str(path))
    text = "\n".join(page.extract_text() or "" for page in reader.pages)
    hits = [
        {
            "path": rel(path),
            "match": match.group(0),
            "context": text[max(0, match.start() - 80) : match.end() + 120].replace("\n", " ")[:260],
        }
        for match in PUBLIC_FORBIDDEN_RE.finditer(text)
    ]
    return {
        "path": rel(path),
        "kind": "pdf",
        "pages": len(reader.pages),
        "text_chars": len(text),
        "sha256": sha256_file(path),
        "forbidden_hit_total": len(hits),
        "hits": hits[:50],
    }


def scan_zip(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {"path": rel(path), "exists": False, "state": "FAIL", "failure_total": 1, "failures": [{"issue": "missing_zip"}]}
    failures = []
    with zipfile.ZipFile(path) as zf:
        names = zf.namelist()
        for name in names:
            lowered = name.lower()
            if "no_send" in lowered or "no-send" in lowered or "nosend" in lowered:
                failures.append({"member": name, "issue": "forbidden_member_name"})
                continue
            suffix = Path(name).suffix.lower()
            if suffix in TEXT_SUFFIXES and not name.endswith("/"):
                text = zf.read(name).decode("utf-8", errors="ignore")
                hit = PUBLIC_FORBIDDEN_RE.search(text)
                if hit:
                    failures.append({"member": name, "issue": "forbidden_member_text", "match": hit.group(0)})
    return {
        "path": rel(path),
        "exists": True,
        "state": "PASS" if not failures else "FAIL",
        "member_total": len(names),
        "failure_total": len(failures),
        "failures": failures[:100],
        "sha256": sha256_file(path),
        "size_bytes": path.stat().st_size,
    }


def audit_spaces() -> dict[str, Any]:
    model = build_space_model()
    paths = release_space_paths()
    missing = [rel(path) for path in paths if not path.exists()]
    text_hits: list[dict[str, Any]] = []
    pdf_rows = []
    zip_rows = []
    for path in paths:
        if not path.exists():
            continue
        text_hits.extend(scan_text(path))
        if path.suffix.lower() == ".pdf":
            pdf_rows.append(scan_pdf(path))
        if path.suffix.lower() == ".zip":
            zip_rows.append(scan_zip(path))
    manifest = read_json(ROOT / "manifest.json", {})
    root_zenodo = ROOT / ".zenodo.json"
    public_manifest_ok = (
        manifest.get("manifest_kind") == "PUBLIC_GITHUB_ZENODO_RELEASE"
        and manifest.get("owner_approved") is True
        and manifest.get("publish_allowed") is True
    )
    pdf_failure_total = sum(1 for row in pdf_rows if row.get("forbidden_hit_total", 0) > 0)
    zip_failure_total = sum(row.get("failure_total", 0) for row in zip_rows)
    failures: list[str] = []
    if missing:
        failures.append("release_space_missing_required_paths")
    if text_hits:
        failures.append("release_space_control_language_contamination")
    if pdf_failure_total:
        failures.append("release_pdf_control_language_contamination")
    if zip_failure_total:
        failures.append("release_zip_control_language_contamination")
    if not root_zenodo.is_file():
        failures.append("release_space_missing_zenodo_metadata")
    if not public_manifest_ok:
        failures.append("root_manifest_is_not_public_release_manifest")
    return {
        "schema_id": "LOGION_RELEASE_SPACE_AUDIT_v1",
        "release_id": RELEASE_ID,
        "version": VERSION,
        "generated_at": "2026-05-01T00:00:00Z",
        "state": "PASS" if not failures else "FAIL",
        "failure_total": len(failures),
        "failures": failures,
        "model": model,
        "release_space_path_total": len(paths),
        "missing_paths": missing,
        "control_language_hit_total": len(text_hits),
        "control_language_hits": text_hits[:100],
        "pdf_rows": pdf_rows,
        "zip_rows": zip_rows,
        "root_manifest_public_ok": public_manifest_ok,
        "root_zenodo_exists": root_zenodo.is_file(),
    }


def run_command(args: list[str], timeout: int = 1200) -> dict[str, Any]:
    started = time.time()
    result = subprocess.run(
        args,
        cwd=ROOT,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        timeout=timeout,
    )
    return {
        "command": args,
        "returncode": result.returncode,
        "ok": result.returncode == 0,
        "elapsed_seconds": round(time.time() - started, 3),
        "stdout_tail": result.stdout[-4000:],
        "stderr_tail": result.stderr[-4000:],
    }


def repair_release_space() -> dict[str, Any]:
    rows = [
        run_command(
            [
                "python",
                "tools/oc133_public_release_payload.py",
                "--doi",
                ZENODO_DOI,
                "--zenodo-record-url",
                ZENODO_RECORD_URL,
                "--github-release-url",
                GITHUB_RELEASE_URL,
                "--skip-pdf",
            ],
            timeout=900,
        ),
        run_command(["python", "tools/oc133_public_release_payload.py", "--check"], timeout=600),
    ]
    audit = audit_spaces()
    return {
        "schema_id": "LOGION_RELEASE_SPACE_REPAIR_v1",
        "release_id": RELEASE_ID,
        "version": VERSION,
        "migration_id": "verification_to_release",
        "rows": rows,
        "audit": audit,
        "state": "PASS" if all(row["ok"] for row in rows) and audit["state"] == "PASS" else "FAIL",
    }


def render_cockpit(audit: dict[str, Any]) -> str:
    lines = [
        "# Logion Release Space Cockpit",
        "",
        f"- release: `{RELEASE_ID}` v`{VERSION}`",
        f"- state: `{audit['state']}`",
        f"- failures: `{audit['failure_total']}`",
        f"- release-space paths: `{audit['release_space_path_total']}`",
        f"- control-language hits: `{audit['control_language_hit_total']}`",
        f"- root manifest public: `{str(audit['root_manifest_public_ok']).lower()}`",
        f"- root Zenodo metadata: `{str(audit['root_zenodo_exists']).lower()}`",
        "",
        "## Spaces",
        "",
    ]
    for space in audit["model"]["spaces"]:
        lines.append(f"- `{space['space_id']}`: {space['purpose']}")
    lines.extend(["", "## Migrations", ""])
    for migration in audit["model"]["migrations"]:
        lines.append(
            f"- `{migration['migration_id']}` `{migration['source_space']}` -> `{migration['target_space']}` owner=`{migration['owner_capability']}`"
        )
    if audit["failures"]:
        lines.extend(["", "## Failures", ""])
        for failure in audit["failures"]:
            lines.append(f"- `{failure}`")
    return "\n".join(lines)


def write_outputs(audit: dict[str, Any]) -> list[str]:
    changed = []
    if write_json_if_changed(SPACE_MODEL, audit["model"]):
        changed.append(rel(SPACE_MODEL))
    if write_json_if_changed(SPACE_AUDIT, audit):
        changed.append(rel(SPACE_AUDIT))
    if write_text_if_changed(SPACE_COCKPIT, render_cockpit(audit)):
        changed.append(rel(SPACE_COCKPIT))
    return changed


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Logion development/verification/release space boundary controller.")
    parser.add_argument("--release-id", default=RELEASE_ID)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--repair", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    if args.release_id != RELEASE_ID:
        raise SystemExit(f"unsupported release id: {args.release_id}")
    repair = repair_release_space() if args.repair else None
    audit = repair["audit"] if repair else audit_spaces()
    payload: dict[str, Any] = dict(audit)
    if repair is not None:
        payload["repair"] = repair
    if args.write:
        payload["changed"] = write_outputs(audit)
    if args.check:
        if payload["state"] != "PASS":
            print(json.dumps(payload, ensure_ascii=False, indent=2))
            return 1
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload["state"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
