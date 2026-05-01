from __future__ import annotations

import base64
import dataclasses
import hashlib
import json
import mimetypes
import os
import re
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

from . import complete


TEXT_SUFFIXES = {
    ".bib",
    ".cff",
    ".json",
    ".jsonld",
    ".md",
    ".tex",
    ".txt",
    ".yaml",
    ".yml",
}

SECRET_PATTERN = re.compile(
    r"(OPENAI_API_KEY|GITHUB_TOKEN|GH_TOKEN|ZENODO_ACCESS_TOKEN|ZENODO_TOKEN|password\s*=|secret\s*=|token\s*=|"
    r"[A-Za-z]:\\Users\\|/home/|estra-private-work)",
    re.IGNORECASE,
)


@dataclasses.dataclass(frozen=True)
class ReleaseAsset:
    path: str
    label: str
    description: str


@dataclasses.dataclass(frozen=True)
class ReleaseProfile:
    release_id: str
    version: str
    tag: str
    branch: str
    repository: str
    title: str
    subtitle: str
    release_state: str
    expected_gate_pass_total: int
    expected_package_sha256: str
    previous_zenodo_record_id: str
    previous_zenodo_doi: str
    concept_doi: str
    creators: list[dict[str, str]]
    license: str
    keywords: list[str]
    github_topics: list[str]
    hashtags: list[str]
    assets: list[ReleaseAsset]
    journal_submissions_allowed: bool = False
    software_heritage_allowed: bool = False

    @property
    def release_root_ref(self) -> str:
        return f"releases/{self.release_id}"

    @property
    def editorial_ref(self) -> str:
        return f"{self.release_root_ref}/editorial"


def repo_root(start: Path | None = None) -> Path:
    return complete.repo_root(start)


def _read_json(path: Path, default: Any | None = None) -> Any:
    if not path.exists():
        return {} if default is None else default
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: Any) -> bool:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    if path.exists() and path.read_text(encoding="utf-8") == text:
        return False
    path.write_text(text, encoding="utf-8")
    return True


def _write_text(path: Path, text: str) -> bool:
    path.parent.mkdir(parents=True, exist_ok=True)
    normalized = text.rstrip() + "\n"
    if path.exists() and path.read_text(encoding="utf-8") == normalized:
        return False
    path.write_text(normalized, encoding="utf-8")
    return True


def _run(root: Path, args: list[str], *, check: bool = True, timeout: int = 120) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=root, text=True, capture_output=True, check=check, timeout=timeout)


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _utc_timestamp() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _profile_path(root: Path, release_id: str) -> Path:
    return root / "releases" / release_id / "editorial" / "PUBLIC_RELEASE_PROFILE.json"


def _default_oc133_profile() -> ReleaseProfile:
    return ReleaseProfile(
        release_id="oc_core_1_3_3",
        version="1.3.3",
        tag="v1.3.3",
        branch="release/oc-core-1.3.3-total-scientific-closure",
        repository="alexanderyashin/ontology-of-continua-core-main",
        title="Ontology of Continua Core 1.3.3",
        subtitle="Bounded external-review release with typed foundations, proof/evidence ledgers, reproducibility package, and no-send journal owner-review packets",
        release_state="OC_CORE_1_3_3_EXTERNAL_REVIEW_READY_NO_SEND",
        expected_gate_pass_total=71,
        expected_package_sha256="",
        previous_zenodo_record_id="19851694",
        previous_zenodo_doi="10.5281/zenodo.19851694",
        concept_doi="10.5281/zenodo.17899134",
        creators=[{"name": "Yashin, Alexander", "affiliation": "Logion / Estra"}],
        license="cc-by-4.0",
        keywords=[
            "Ontology of Continua",
            "OC Core",
            "systems theory",
            "formal methods",
            "reproducible research",
            "mathematical modeling",
            "scientific release engineering",
            "cross-domain modeling",
            "proof governance",
            "target-blind validation",
            "journal owner-review package",
        ],
        github_topics=[
            "ontology-of-continua",
            "oc-core",
            "systems-theory",
            "formal-methods",
            "reproducible-research",
            "mathematical-modeling",
            "scientific-release",
            "proof-governance",
            "target-blind-validation",
        ],
        hashtags=[
            "#OntologyOfContinua",
            "#OCCore",
            "#SystemsTheory",
            "#FormalMethods",
            "#ReproducibleResearch",
            "#MathematicalModeling",
            "#ScientificRelease",
            "#ProofGovernance",
            "#TargetBlindValidation",
        ],
        assets=[
            ReleaseAsset(
                "releases/oc_core_1_3_3/artifacts/OC_CORE_1_3_3_MASTER_MONOGRAPH_EN.pdf",
                "Master monograph",
                "Canonical long-form scientific reference for OC Core 1.3.3.",
            ),
            ReleaseAsset(
                "releases/oc_core_1_3_3/artifacts/OC_CORE_1_3_3_JOURNAL_CORE_EN.pdf",
                "Journal core",
                "Compact article-style entry point for external scientific review.",
            ),
            ReleaseAsset(
                "releases/oc_core_1_3_3/artifacts/OC_CORE_1_3_3_METHODS_AND_REPRODUCIBILITY_COMPANION_EN.pdf",
                "Methods and reproducibility companion",
                "Reproducibility, validation, and audit navigation companion.",
            ),
            ReleaseAsset(
                "releases/oc_core_1_3_3/artifacts/OC_CORE_1_3_3_REVIEWER_ATTACK_AND_RESPONSE_MAP_EN.pdf",
                "Reviewer attack and response map",
                "Adversarial review, objections, boundaries, and response map.",
            ),
            ReleaseAsset(
                "releases/oc_core_1_3_3/artifacts/oc_core_1_3_3_no_send_release.zip",
                "Frozen release package",
                "Canonical reproducibility package; journal submissions remain locked unless separately approved.",
            ),
            ReleaseAsset("manifest.json", "Root artifact manifest", "Machine-readable package manifest."),
            ReleaseAsset("checksums.txt", "Root checksums", "Root checksum list for public assets."),
            ReleaseAsset("CITATION.cff", "Citation metadata", "Software citation metadata."),
            ReleaseAsset(".codemeta.json", "CodeMeta metadata", "CodeMeta metadata for the release."),
            ReleaseAsset("ro-crate-metadata.jsonld", "RO-Crate metadata", "RO-Crate metadata for the release."),
            ReleaseAsset("releases/oc_core_1_3_3/RELEASE_NOTES.md", "Release notes", "Human-readable release notes."),
            ReleaseAsset("releases/oc_core_1_3_3/CHANGELOG.md", "Changelog", "Release changelog summary."),
            ReleaseAsset(
                "releases/oc_core_1_3_3/editorial/OC_CORE_1_3_3_RELEASE_SCORECARD_latest.json",
                "Release scorecard",
                "Machine-readable final release gate scorecard.",
            ),
            ReleaseAsset(
                "releases/oc_core_1_3_3/editorial/OC_CORE_1_3_3_PERSONAL_RELEASE_AUDIT_latest.json",
                "Owner-review audit",
                "Personal release audit and owner-review readiness result.",
            ),
            ReleaseAsset(
                "releases/oc_core_1_3_3/editorial/OC_CORE_1_3_3_ZIP_INTEGRITY_latest.json",
                "ZIP integrity manifest",
                "Frozen release-package SHA-256 and integrity manifest.",
            ),
        ],
    )


def _profile_from_json(payload: dict[str, Any]) -> ReleaseProfile:
    payload = {key: value for key, value in payload.items() if key != "schema_id"}
    assets = [
        ReleaseAsset(
            path=str(item["path"]),
            label=str(item.get("label", Path(str(item["path"])).name)),
            description=str(item.get("description", "")),
        )
        for item in payload.get("assets", [])
    ]
    payload = dict(payload)
    payload["assets"] = assets
    return ReleaseProfile(**payload)


def _profile_to_json(profile: ReleaseProfile) -> dict[str, Any]:
    payload = dataclasses.asdict(profile)
    payload["schema_id"] = "LOGION_PUBLIC_RELEASE_PROFILE_v1"
    return payload


def load_profile(root: Path, release_id: str) -> ReleaseProfile:
    path = _profile_path(root, release_id)
    if path.exists():
        return _profile_from_json(_read_json(path))
    if release_id == "oc_core_1_3_3":
        return _default_oc133_profile()
    raise ValueError(
        f"No public release profile for {release_id}. "
        f"Create {path.relative_to(root).as_posix()} or add a generated release profile."
    )


def write_profile(root: Path, profile: ReleaseProfile) -> bool:
    return _write_json(_profile_path(root, profile.release_id), _profile_to_json(profile))


def release_root(root: Path, profile: ReleaseProfile) -> Path:
    return root / "releases" / profile.release_id


def editorial_root(root: Path, profile: ReleaseProfile) -> Path:
    return release_root(root, profile) / "editorial"


def _rel(root: Path, path: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def _git_status(root: Path) -> list[str]:
    status = _run(root, ["git", "status", "--porcelain"], timeout=60).stdout.splitlines()
    return [line for line in status if line.strip()]


def _git_branch(root: Path) -> str:
    return _run(root, ["git", "branch", "--show-current"], timeout=60).stdout.strip()


def _git_head(root: Path) -> str:
    return _run(root, ["git", "rev-parse", "HEAD"], timeout=60).stdout.strip()


def _git_tag_exists(root: Path, tag: str) -> dict[str, Any]:
    local = _run(root, ["git", "tag", "--list", tag], timeout=60).stdout.strip()
    remote = _run(root, ["git", "ls-remote", "--tags", "origin", tag], timeout=120).stdout.strip()
    return {"local_exists": bool(local), "remote_exists": bool(remote), "remote_output": remote}


def _asset_records(root: Path, profile: ReleaseProfile) -> list[dict[str, Any]]:
    records = []
    for asset in profile.assets:
        path = root / asset.path
        records.append(
            {
                "path": asset.path,
                "filename": path.name,
                "label": asset.label,
                "description": asset.description,
                "exists": path.is_file(),
                "size_bytes": path.stat().st_size if path.is_file() else 0,
                "sha256": _sha256(path) if path.is_file() else None,
            }
        )
    return records


def _find_secret_hits(root: Path, profile: ReleaseProfile) -> list[dict[str, str]]:
    hits: list[dict[str, str]] = []
    for asset in profile.assets:
        path = root / asset.path
        if not path.is_file() or path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            hits.append({"path": asset.path, "issue": f"read_failed:{exc}"})
            continue
        match = SECRET_PATTERN.search(text)
        if match:
            hits.append({"path": asset.path, "issue": f"secret_or_local_path_pattern:{match.group(0)[:60]}"})
    return hits


def _scorecard_ok(root: Path, profile: ReleaseProfile) -> dict[str, Any]:
    path = editorial_root(root, profile) / f"OC_CORE_{profile.version.replace('.', '_')}_RELEASE_SCORECARD_latest.json"
    if not path.exists() and profile.release_id == "oc_core_1_3_3":
        path = editorial_root(root, profile) / "OC_CORE_1_3_3_RELEASE_SCORECARD_latest.json"
    payload = _read_json(path)
    summary = payload.get("summary", payload)
    gate_counts = summary.get("gate_counts", {})
    pass_total = int(gate_counts.get("PASS", 0))
    fail_total = int(gate_counts.get("FAIL", 0))
    state = summary.get("release_state")
    return {
        "path": _rel(root, path) if path.exists() else str(path),
        "exists": path.exists(),
        "release_state": state,
        "pass_total": pass_total,
        "fail_total": fail_total,
        "master_verdict": summary.get("master_verdict"),
        "external_review_ready_no_send": bool(summary.get("external_review_ready_no_send", state == profile.release_state)),
        "all_domain_ready_no_send": bool(summary.get("all_domain_ready_no_send", False)),
        "ok": path.exists()
        and pass_total == profile.expected_gate_pass_total
        and fail_total == 0
        and summary.get("master_verdict") == "PASS"
        and state == profile.release_state,
    }


def _owner_audit_ok(root: Path, profile: ReleaseProfile) -> dict[str, Any]:
    path = editorial_root(root, profile) / f"OC_CORE_{profile.version.replace('.', '_')}_PERSONAL_RELEASE_AUDIT_latest.json"
    if not path.exists() and profile.release_id == "oc_core_1_3_3":
        path = editorial_root(root, profile) / "OC_CORE_1_3_3_PERSONAL_RELEASE_AUDIT_latest.json"
    payload = _read_json(path)
    blocker_total = int(payload.get("blocker_total", payload.get("summary", {}).get("blocker_total", 0)))
    verdict = payload.get("verdict", payload.get("summary", {}).get("verdict"))
    return {
        "path": _rel(root, path) if path.exists() else str(path),
        "exists": path.exists(),
        "verdict": verdict,
        "blocker_total": blocker_total,
        "ok": path.exists() and blocker_total == 0 and str(verdict).upper() in {"READY_FOR_FINAL_OWNER_APPROVAL_NO_SEND", "PASS", "READY_NO_SEND"},
    }


def _cerberus_ok(root: Path) -> dict[str, Any]:
    candidates = [
        root / "reviews" / "oc133_llm_cerberus" / "OC133_LLM_CERBERUS_SUMMARY.json",
        root / "releases" / "oc_core_1_3_3" / "editorial" / "OC133_LLM_CERBERUS_SUMMARY.json",
    ]
    path = next((candidate for candidate in candidates if candidate.exists()), candidates[0])
    payload = _read_json(path, {})
    critical = int(payload.get("critical_open_total", 0))
    high = int(payload.get("high_open_total", 0))
    parse = int(payload.get("parse_failure_total", 0))
    return {
        "path": _rel(root, path) if path.exists() else str(path),
        "exists": path.exists(),
        "critical_open_total": critical,
        "high_open_total": high,
        "parse_failure_total": parse,
        "ok": path.exists() and critical == 0 and high == 0 and parse == 0,
    }


def _journal_lock_ok(root: Path, profile: ReleaseProfile) -> dict[str, Any]:
    path = release_root(root, profile) / "submission_packages" / "SUBMISSION_PACKAGE_INDEX.json"
    payload = _read_json(path, {})
    total = int(payload.get("package_total", 0))
    counts = payload.get("package_status_counts", {})
    ready = int(counts.get("OWNER_REVIEW_READY_NO_SEND", 0))
    submission_allowed = bool(payload.get("submission_allowed", False))
    journal_allowed = bool(payload.get("journal_submissions_allowed", False))
    return {
        "path": _rel(root, path) if path.exists() else str(path),
        "exists": path.exists(),
        "package_total": total,
        "owner_review_ready_total": ready,
        "submission_allowed": submission_allowed,
        "journal_submissions_allowed": journal_allowed,
        "ok": path.exists() and total == ready and total > 0 and not submission_allowed and not journal_allowed,
    }


def _delta_ok(root: Path) -> dict[str, Any]:
    path = root / "operations" / "project_control" / "LOGION_DELTA_QUEUE_LEDGER.json"
    payload = _read_json(path, {})
    significant = bool(payload.get("significant_delta", False))
    trigger = bool(payload.get("downstream_trigger_allowed", False))
    return {
        "path": _rel(root, path) if path.exists() else str(path),
        "exists": path.exists(),
        "significant_delta": significant,
        "downstream_trigger_allowed": trigger,
        "ok": path.exists() and not significant and not trigger,
    }


def _zip_integrity_ok(root: Path, profile: ReleaseProfile) -> dict[str, Any]:
    path = editorial_root(root, profile) / f"OC_CORE_{profile.version.replace('.', '_')}_ZIP_INTEGRITY_latest.json"
    if not path.exists() and profile.release_id == "oc_core_1_3_3":
        path = editorial_root(root, profile) / "OC_CORE_1_3_3_ZIP_INTEGRITY_latest.json"
    payload = _read_json(path, {})
    package_ref = payload.get("package_ref") or f"{profile.release_root_ref}/artifacts/oc_core_{profile.version.replace('.', '_')}_no_send_release.zip"
    package_path = root / str(package_ref)
    manifest_sha = payload.get("package_sha256") or payload.get("sha256")
    actual_sha = _sha256(package_path) if package_path.is_file() else None
    expected_sha = profile.expected_package_sha256 or manifest_sha
    return {
        "path": _rel(root, path) if path.exists() else str(path),
        "package_ref": str(package_ref),
        "exists": path.exists() and package_path.is_file(),
        "manifest_sha256": manifest_sha,
        "actual_sha256": actual_sha,
        "expected_sha256": expected_sha,
        "profile_pins_package_sha256": bool(profile.expected_package_sha256),
        "ok": path.exists()
        and package_path.is_file()
        and actual_sha == manifest_sha
        and (not profile.expected_package_sha256 or actual_sha == profile.expected_package_sha256),
    }


def _owner_approval_state(root: Path, profile: ReleaseProfile) -> dict[str, Any]:
    path = editorial_root(root, profile) / f"OWNER_RELEASE_APPROVAL_v{profile.version}.json"
    payload = _read_json(path, {})
    return {
        "path": _rel(root, path) if path.exists() else str(path),
        "exists": path.exists(),
        "decision": payload.get("decision"),
        "owner_approved": bool(payload.get("owner_approved", False)),
        "publish_allowed": bool(payload.get("publish_allowed", False)),
        "github_release_allowed": bool(payload.get("github_release_allowed", False)),
        "zenodo_deposit_allowed": bool(payload.get("zenodo_deposit_allowed", False)),
        "journal_submissions_allowed": bool(payload.get("journal_submissions_allowed", False)),
        "software_heritage_deposit_allowed": bool(payload.get("software_heritage_deposit_allowed", False)),
    }


def _zenodo_record(record_id: str) -> dict[str, Any]:
    url = f"https://zenodo.org/api/records/{urllib.parse.quote(record_id)}"
    with urllib.request.urlopen(url, timeout=60) as response:
        return json.loads(response.read().decode("utf-8"))


def _tokens_ok() -> dict[str, Any]:
    gh = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    zen = os.environ.get("ZENODO_ACCESS_TOKEN") or os.environ.get("ZENODO_TOKEN")
    return {
        "github_token_present": bool(gh),
        "zenodo_production_token_present": bool(zen),
        "ok": bool(gh) and bool(zen),
    }


def _release_body(profile: ReleaseProfile, checksums: list[dict[str, Any]], zenodo_doi: str | None = None) -> str:
    asset_lines = "\n".join(
        f"- `{row['filename']}`: {row['label']} ({row['sha256']})"
        for row in checksums
        if row.get("exists") and row.get("sha256")
    )
    doi_line = zenodo_doi or "Pending until Zenodo publication completes"
    keywords = ", ".join(profile.keywords)
    hashtags = " ".join(profile.hashtags)
    return f"""# {profile.title} v{profile.version}

{profile.subtitle}

## Table of Contents

1. Scope and release boundary
2. Core scientific artifacts
3. Reproducibility and checksums
4. Journal package status
5. Zenodo DOI and citation
6. Release governance

## Scope

This is the public GitHub and Zenodo release of OC Core {profile.version}. It is a bounded external-review release: the release surface promotes the model-core claims supported by the included proof, finite-model, validation, reproducibility, and adversarial-review artifacts. Broader full-domain TOE and all-modern-science-superiority obligations remain in the background science program unless explicitly evidenced in this release package.

## Core Assets

{asset_lines}

## Journal Packages

The eight journal packages are included as owner-review-ready no-send material. Journal submissions remain locked and require a separate owner approval.

## Zenodo

DOI: {doi_line}

Concept DOI: {profile.concept_doi}

Previous version DOI: {profile.previous_zenodo_doi}

## Keywords

{keywords}

{hashtags}

## Governance

GitHub Release and Zenodo publication were owner-approved for this release phase. Journal submission, email, and Software Heritage deposit are not enabled by this release action.
"""


def _zenodo_metadata(profile: ReleaseProfile, description: str, *, doi: str | None = None) -> dict[str, Any]:
    related = [
        {"identifier": profile.concept_doi, "relation": "isVersionOf", "scheme": "doi"},
        {"identifier": profile.previous_zenodo_doi, "relation": "isNewVersionOf", "scheme": "doi"},
    ]
    if doi:
        related.append({"identifier": doi, "relation": "isIdenticalTo", "scheme": "doi"})
    return {
        "title": f"{profile.title} v{profile.version}",
        "upload_type": "publication",
        "publication_type": "other",
        "description": description,
        "creators": profile.creators,
        "license": profile.license,
        "keywords": profile.keywords,
        "version": profile.version,
        "related_identifiers": related,
    }


def build_public_metadata(
    root: Path,
    profile: ReleaseProfile,
    *,
    zenodo_doi: str | None = None,
    zenodo_record_url: str | None = None,
    github_release_url: str | None = None,
    write: bool = True,
) -> dict[str, Any]:
    assets = _asset_records(root, profile)
    body = _release_body(profile, assets, zenodo_doi=zenodo_doi)
    zenodo = _zenodo_metadata(profile, body, doi=zenodo_doi)
    metadata = {
        "schema_id": "LOGION_PUBLIC_RELEASE_PRESENTATION_v1",
        "release_id": profile.release_id,
        "version": profile.version,
        "tag": profile.tag,
        "repository": profile.repository,
        "title": profile.title,
        "subtitle": profile.subtitle,
        "github_release_url": github_release_url,
        "zenodo_record_url": zenodo_record_url,
        "zenodo_doi": zenodo_doi,
        "concept_doi": profile.concept_doi,
        "previous_zenodo_doi": profile.previous_zenodo_doi,
        "keywords": profile.keywords,
        "github_topics": profile.github_topics,
        "hashtags": profile.hashtags,
        "release_body": body,
        "zenodo_metadata": zenodo,
        "assets": assets,
        "journal_submissions_allowed": profile.journal_submissions_allowed,
        "software_heritage_allowed": profile.software_heritage_allowed,
    }
    if write:
        write_profile(root, profile)
        editorial = editorial_root(root, profile)
        _write_json(editorial / f"PUBLIC_RELEASE_PRESENTATION_{profile.version}_latest.json", metadata)
        _write_text(editorial / f"PUBLIC_RELEASE_PRESENTATION_{profile.version}_latest.md", body)
        _write_json(root / ".zenodo.json", zenodo)
    return metadata


def _preflight_common(root: Path, profile: ReleaseProfile, *, require_approval: bool) -> dict[str, Any]:
    status = _git_status(root)
    branch = _git_branch(root)
    head = _git_head(root)
    tag_state = _git_tag_exists(root, profile.tag)
    assets = _asset_records(root, profile)
    secret_hits = _find_secret_hits(root, profile)
    scorecard = _scorecard_ok(root, profile)
    owner_audit = _owner_audit_ok(root, profile)
    cerberus = _cerberus_ok(root)
    journal = _journal_lock_ok(root, profile)
    delta = _delta_ok(root)
    zip_integrity = _zip_integrity_ok(root, profile)
    owner = _owner_approval_state(root, profile)
    token_state = _tokens_ok()
    previous_record_ok = False
    previous_record_error = None
    try:
        previous_record = _zenodo_record(profile.previous_zenodo_record_id)
        previous_record_ok = bool(previous_record.get("id"))
    except Exception as exc:  # network/API detail belongs in evidence packet
        previous_record_error = str(exc)

    checks = {
        "clean_tree": {"ok": not status, "dirty_rows": status},
        "expected_branch": {"ok": branch == profile.branch, "actual_branch": branch, "expected_branch": profile.branch},
        "tag_absent": {"ok": not tag_state["local_exists"] and not tag_state["remote_exists"], **tag_state},
        "scorecard": scorecard,
        "owner_audit": owner_audit,
        "cerberus": cerberus,
        "journal_lock": journal,
        "delta_queue": delta,
        "zip_integrity": zip_integrity,
        "assets": {"ok": all(row["exists"] for row in assets), "missing": [row["path"] for row in assets if not row["exists"]]},
        "secret_scan": {"ok": not secret_hits, "hits": secret_hits},
        "production_tokens": token_state,
        "previous_zenodo_record": {"ok": previous_record_ok, "error": previous_record_error, "record_id": profile.previous_zenodo_record_id},
    }
    if require_approval:
        checks["owner_publication_approval"] = {
            "ok": owner["owner_approved"]
            and owner["publish_allowed"]
            and owner["github_release_allowed"]
            and owner["zenodo_deposit_allowed"]
            and not owner["journal_submissions_allowed"]
            and not owner["software_heritage_deposit_allowed"],
            **owner,
        }
    ok = all(item.get("ok") for item in checks.values())
    return {
        "schema_id": "LOGION_PUBLICATION_PREFLIGHT_v1",
        "release_id": profile.release_id,
        "version": profile.version,
        "tag": profile.tag,
        "repository": profile.repository,
        "head": head,
        "generated_at": _utc_timestamp(),
        "require_approval": require_approval,
        "checks": checks,
        "assets": assets,
        "preflight_ok": ok,
        "blocked": not ok,
    }


def publication_preflight(root: Path, *, release_id: str, write: bool = True, require_approval: bool = True) -> dict[str, Any]:
    profile = load_profile(root, release_id)
    payload = _preflight_common(root, profile, require_approval=require_approval)
    if write:
        _write_json(editorial_root(root, profile) / f"PUBLICATION_PREFLIGHT_{profile.version}_latest.json", payload)
    return payload


def grant_owner_approval(root: Path, *, release_id: str, owner_identity: str) -> dict[str, Any]:
    profile = load_profile(root, release_id)
    readiness = _preflight_common(root, profile, require_approval=False)
    if not readiness["preflight_ok"]:
        payload = {
            "schema_id": "LOGION_OWNER_APPROVAL_ATTEMPT_v1",
            "release_id": profile.release_id,
            "version": profile.version,
            "decision": "BLOCKED",
            "owner_identity": owner_identity,
            "reason": "Release readiness preflight failed before owner approval.",
            "readiness": readiness,
        }
        _write_json(editorial_root(root, profile) / f"OWNER_APPROVAL_BLOCKED_{profile.version}.json", payload)
        return payload

    now = _utc_timestamp()
    approval = {
        "schema_id": "LOGION_OWNER_RELEASE_APPROVAL_v1",
        "release_id": profile.release_id,
        "version": profile.version,
        "decision": "APPROVED_FOR_GITHUB_AND_ZENODO_PUBLIC_RELEASE_ONLY",
        "owner_identity": owner_identity,
        "owner_approved": True,
        "approval_timestamp": now,
        "publish_allowed": True,
        "github_release_allowed": True,
        "zenodo_deposit_allowed": True,
        "doi_minting_allowed": True,
        "journal_submissions_allowed": False,
        "journal_submission_allowed": False,
        "software_heritage_deposit_allowed": False,
        "email_allowed": False,
        "release_scope": ["github_release", "zenodo_production_deposit"],
        "excluded_scope": ["journal_submission", "email", "software_heritage"],
    }
    manifest = {
        "schema_id": "LOGION_PUBLIC_PUBLISH_MANIFEST_v1",
        "release_id": profile.release_id,
        "version": profile.version,
        "owner_approved": True,
        "owner_approval_required": True,
        "publish_allowed": True,
        "github_release_allowed": True,
        "zenodo_deposit_allowed": True,
        "doi_minting_allowed": True,
        "journal_submissions_allowed": False,
        "journal_submission_allowed": False,
        "software_heritage_deposit_allowed": False,
        "global_no_send_lock": False,
        "journal_no_send_lock": True,
        "release_scope": approval["release_scope"],
        "tag": profile.tag,
        "expected_package_sha256": readiness["checks"]["zip_integrity"]["expected_sha256"],
        "package_sha256_source": "OC_CORE_1_3_3_ZIP_INTEGRITY_latest.json",
        "approval_timestamp": now,
    }
    metadata = build_public_metadata(root, profile, write=True)
    editorial = editorial_root(root, profile)
    _write_json(editorial / f"OWNER_RELEASE_APPROVAL_v{profile.version}.json", approval)
    _write_json(editorial / f"OC_CORE_{profile.version.replace('.', '_')}_PUBLISH_MANIFEST_DRAFT.json", manifest)
    _write_json(editorial / f"OWNER_APPROVAL_GRANTED_{profile.version}.json", {"approval": approval, "manifest": manifest, "metadata": metadata})
    _write_text(
        editorial / f"OWNER_APPROVAL_GRANTED_{profile.version}.md",
        f"# Owner Approval Granted\n\nRelease: `{profile.release_id}` v{profile.version}\n\nScope: GitHub Release + Zenodo production deposit only.\n\nJournal submissions: locked.\n\nSoftware Heritage: locked.\n",
    )
    return {
        "schema_id": "LOGION_OWNER_APPROVAL_RESULT_v1",
        "release_id": profile.release_id,
        "version": profile.version,
        "approval": approval,
        "manifest": manifest,
        "metadata_written": True,
        "ready_for_publication_preflight": True,
    }


def _http_json(method: str, url: str, *, token: str | None = None, payload: Any | None = None, headers: dict[str, str] | None = None) -> dict[str, Any]:
    data = None
    request_headers = {"Accept": "application/json"}
    if headers:
        request_headers.update(headers)
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        request_headers["Content-Type"] = "application/json"
    if token:
        request_headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(url, data=data, headers=request_headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=180) as response:
            body = response.read().decode("utf-8")
            return json.loads(body) if body else {}
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"{method} {url} failed: HTTP {exc.code}: {body}") from exc


def _http_upload(method: str, url: str, *, token: str | None = None, data: bytes, content_type: str) -> dict[str, Any]:
    headers = {"Content-Type": content_type, "Accept": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=600) as response:
            body = response.read().decode("utf-8")
            return json.loads(body) if body else {}
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"{method} {url} failed: HTTP {exc.code}: {body}") from exc


def _github_api_url(profile: ReleaseProfile, suffix: str) -> str:
    return f"https://api.github.com/repos/{profile.repository}{suffix}"


def _github_get_release(profile: ReleaseProfile, token: str) -> dict[str, Any] | None:
    url = _github_api_url(profile, f"/releases/tags/{urllib.parse.quote(profile.tag)}")
    try:
        return _http_json("GET", url, token=token, headers={"Accept": "application/vnd.github+json"})
    except RuntimeError as exc:
        if "HTTP 404" in str(exc):
            return None
        raise


def _github_create_or_update_release(profile: ReleaseProfile, token: str, body: str) -> dict[str, Any]:
    existing = _github_get_release(profile, token)
    payload = {
        "tag_name": profile.tag,
        "target_commitish": profile.branch,
        "name": f"{profile.title} v{profile.version}",
        "body": body,
        "draft": False,
        "prerelease": False,
    }
    if existing:
        return _http_json(
            "PATCH",
            _github_api_url(profile, f"/releases/{existing['id']}"),
            token=token,
            payload=payload,
            headers={"Accept": "application/vnd.github+json"},
        )
    return _http_json(
        "POST",
        _github_api_url(profile, "/releases"),
        token=token,
        payload=payload,
        headers={"Accept": "application/vnd.github+json"},
    )


def _github_upload_assets(root: Path, profile: ReleaseProfile, token: str, release: dict[str, Any]) -> list[dict[str, Any]]:
    existing_assets = release.get("assets", [])
    by_name = {item.get("name"): item for item in existing_assets}
    uploaded: list[dict[str, Any]] = []
    upload_url = str(release["upload_url"]).split("{", 1)[0]
    for asset in profile.assets:
        path = root / asset.path
        filename = path.name
        if filename in by_name:
            _http_json(
                "DELETE",
                _github_api_url(profile, f"/releases/assets/{by_name[filename]['id']}"),
                token=token,
                headers={"Accept": "application/vnd.github+json"},
            )
        content_type = mimetypes.guess_type(filename)[0] or "application/octet-stream"
        result = _http_upload(
            "POST",
            f"{upload_url}?name={urllib.parse.quote(filename)}",
            token=token,
            data=path.read_bytes(),
            content_type=content_type,
        )
        uploaded.append({"name": filename, "browser_download_url": result.get("browser_download_url"), "id": result.get("id")})
    return uploaded


def _github_update_topics(profile: ReleaseProfile, token: str) -> dict[str, Any]:
    return _http_json(
        "PUT",
        _github_api_url(profile, "/topics"),
        token=token,
        payload={"names": profile.github_topics},
        headers={"Accept": "application/vnd.github+json"},
    )


def _zenodo_token() -> str:
    token = os.environ.get("ZENODO_ACCESS_TOKEN") or os.environ.get("ZENODO_TOKEN")
    if not token:
        raise RuntimeError("ZENODO_ACCESS_TOKEN or ZENODO_TOKEN is required for production Zenodo publication.")
    return token


def _zenodo_deposition_url(path: str, token: str) -> str:
    return f"https://zenodo.org/api/deposit/depositions{path}"


def _zenodo_json(method: str, path_or_url: str, token: str, payload: Any | None = None) -> dict[str, Any]:
    url = path_or_url if path_or_url.startswith("http") else _zenodo_deposition_url(path_or_url, token)
    if not url.startswith("http"):
        raise ValueError(url)
    return _http_json(method, url, token=token, payload=payload)


def _zenodo_upload_file(bucket_url: str, token: str, path: Path) -> dict[str, Any]:
    url = f"{bucket_url.rstrip('/')}/{urllib.parse.quote(path.name)}"
    return _http_upload("PUT", url, token=token, data=path.read_bytes(), content_type="application/octet-stream")


def _zenodo_publish(root: Path, profile: ReleaseProfile, metadata: dict[str, Any]) -> dict[str, Any]:
    token = _zenodo_token()
    new_version = _zenodo_json("POST", f"/{profile.previous_zenodo_record_id}/actions/newversion", token)
    latest_draft_url = new_version.get("links", {}).get("latest_draft")
    draft = _zenodo_json("GET", latest_draft_url, token) if latest_draft_url else new_version
    draft_id = str(draft["id"])
    bucket = draft["links"]["bucket"]
    _zenodo_json("PUT", f"/{draft_id}", token, {"metadata": metadata["zenodo_metadata"]})
    uploaded = []
    for asset in profile.assets:
        result = _zenodo_upload_file(bucket, token, root / asset.path)
        uploaded.append({"filename": (root / asset.path).name, "result": result})
    published = _zenodo_json("POST", f"/{draft_id}/actions/publish", token)
    record_id = str(published.get("record_id") or published.get("id") or draft_id)
    doi = published.get("doi") or published.get("metadata", {}).get("doi")
    return {
        "draft_id": draft_id,
        "record_id": record_id,
        "record_url": f"https://zenodo.org/records/{record_id}",
        "doi": doi,
        "uploaded": uploaded,
        "published": published,
    }


def _create_tag_and_push(root: Path, profile: ReleaseProfile, body: str) -> dict[str, Any]:
    tag_state = _git_tag_exists(root, profile.tag)
    if tag_state["local_exists"] or tag_state["remote_exists"]:
        raise RuntimeError(f"Tag {profile.tag} already exists; refusing to create duplicate public release tag.")
    _run(root, ["git", "tag", "-a", profile.tag, "-m", f"{profile.title} v{profile.version}"], timeout=60)
    branch_push = _run(root, ["git", "push", "-u", "origin", f"HEAD:{profile.branch}"], timeout=300)
    tag_push = _run(root, ["git", "push", "origin", profile.tag], timeout=300)
    return {
        "tag": profile.tag,
        "tag_sha": _run(root, ["git", "rev-parse", profile.tag], timeout=60).stdout.strip(),
        "head": _git_head(root),
        "branch_push_stdout": branch_push.stdout,
        "branch_push_stderr": branch_push.stderr,
        "tag_push_stdout": tag_push.stdout,
        "tag_push_stderr": tag_push.stderr,
    }


def publish_execute(root: Path, *, release_id: str) -> dict[str, Any]:
    profile = load_profile(root, release_id)
    preflight = publication_preflight(root, release_id=release_id, write=False, require_approval=True)
    if not preflight["preflight_ok"]:
        raise RuntimeError("Publication preflight failed; refusing public release.")
    metadata = build_public_metadata(root, profile, write=False)
    if _git_status(root):
        raise RuntimeError("Public metadata generation changed the tree before tag creation; aborting release.")
    tag_result = _create_tag_and_push(root, profile, metadata["release_body"])

    zenodo_result = _zenodo_publish(root, profile, metadata)
    metadata = build_public_metadata(
        root,
        profile,
        zenodo_doi=zenodo_result.get("doi"),
        zenodo_record_url=zenodo_result.get("record_url"),
        write=True,
    )

    github_token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if not github_token:
        raise RuntimeError("GITHUB_TOKEN or GH_TOKEN is required for GitHub Release publication.")
    github_release = _github_create_or_update_release(profile, github_token, metadata["release_body"])
    uploaded_assets = _github_upload_assets(root, profile, github_token, github_release)
    topics = _github_update_topics(profile, github_token)
    github_url = github_release.get("html_url") or f"https://github.com/{profile.repository}/releases/tag/{profile.tag}"

    metadata = build_public_metadata(
        root,
        profile,
        zenodo_doi=zenodo_result.get("doi"),
        zenodo_record_url=zenodo_result.get("record_url"),
        github_release_url=github_url,
        write=True,
    )
    now = _utc_timestamp()
    report = {
        "schema_id": "LOGION_PUBLICATION_EXECUTION_REPORT_v1",
        "release_id": profile.release_id,
        "version": profile.version,
        "tag": profile.tag,
        "tag_result": tag_result,
        "github_release_url": github_url,
        "github_release_id": github_release.get("id"),
        "github_uploaded_assets": uploaded_assets,
        "github_topics": topics,
        "zenodo_record_url": zenodo_result.get("record_url"),
        "zenodo_record_id": zenodo_result.get("record_id"),
        "zenodo_doi": zenodo_result.get("doi"),
        "zenodo_uploaded": zenodo_result.get("uploaded"),
        "asset_checksums": _asset_records(root, profile),
        "publication_timestamp": now,
        "journal_submissions_allowed": False,
        "software_heritage_deposit_allowed": False,
    }
    editorial = editorial_root(root, profile)
    _write_json(editorial / f"PUBLICATION_EXECUTION_REPORT_{profile.version}_latest.json", report)
    _write_text(
        editorial / f"PUBLICATION_EXECUTION_REPORT_{profile.version}_latest.md",
        f"# Public Release Execution Report\n\nRelease: `{profile.release_id}` v{profile.version}\n\nGitHub: {github_url}\n\nZenodo: {zenodo_result.get('record_url')}\n\nDOI: {zenodo_result.get('doi')}\n\nJournal submissions: locked.\n",
    )

    approval_path = editorial / f"OWNER_RELEASE_APPROVAL_v{profile.version}.json"
    approval = _read_json(approval_path, {})
    approval.update(
        {
            "published": True,
            "publication_timestamp": now,
            "github_release_url": github_url,
            "zenodo_record_url": zenodo_result.get("record_url"),
            "zenodo_doi": zenodo_result.get("doi"),
            "journal_submissions_allowed": False,
        }
    )
    _write_json(approval_path, approval)
    manifest_path = editorial / f"OC_CORE_{profile.version.replace('.', '_')}_PUBLISH_MANIFEST_DRAFT.json"
    manifest = _read_json(manifest_path, {})
    manifest.update(
        {
            "published": True,
            "publication_timestamp": now,
            "github_release_url": github_url,
            "zenodo_record_url": zenodo_result.get("record_url"),
            "zenodo_doi": zenodo_result.get("doi"),
            "journal_submissions_allowed": False,
        }
    )
    _write_json(manifest_path, manifest)
    return report


def _github_release_verify(profile: ReleaseProfile, token: str) -> dict[str, Any]:
    release = _github_get_release(profile, token)
    if not release:
        return {"exists": False, "ok": False}
    assets = release.get("assets", [])
    names = {asset.get("name") for asset in assets}
    expected = {Path(asset.path).name for asset in profile.assets}
    missing = sorted(expected - names)
    return {
        "exists": True,
        "url": release.get("html_url"),
        "asset_total": len(assets),
        "missing_assets": missing,
        "ok": not missing and release.get("tag_name") == profile.tag,
    }


def _zenodo_verify(profile: ReleaseProfile, record_id: str) -> dict[str, Any]:
    record = _zenodo_record(record_id)
    files = record.get("files", [])
    names = {item.get("key") for item in files}
    expected = {Path(asset.path).name for asset in profile.assets}
    missing = sorted(expected - names)
    doi = record.get("doi")
    return {
        "exists": bool(record.get("id")),
        "record_id": str(record.get("id")),
        "doi": doi,
        "file_total": len(files),
        "missing_files": missing,
        "ok": bool(record.get("id")) and not missing and str(record.get("metadata", {}).get("version")) == profile.version,
    }


def postflight(root: Path, *, release_id: str) -> dict[str, Any]:
    profile = load_profile(root, release_id)
    editorial = editorial_root(root, profile)
    report = _read_json(editorial / f"PUBLICATION_EXECUTION_REPORT_{profile.version}_latest.json", {})
    github_token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if not github_token:
        raise RuntimeError("GITHUB_TOKEN or GH_TOKEN is required for postflight.")
    github = _github_release_verify(profile, github_token)
    record_id = str(report.get("zenodo_record_id", ""))
    zenodo = _zenodo_verify(profile, record_id) if record_id else {"ok": False, "missing": "record_id"}
    checksums = _asset_records(root, profile)
    payload = {
        "schema_id": "LOGION_PUBLICATION_POSTFLIGHT_v1",
        "release_id": profile.release_id,
        "version": profile.version,
        "tag": profile.tag,
        "github": github,
        "zenodo": zenodo,
        "asset_checksums": checksums,
        "journal_submissions_allowed": False,
        "software_heritage_deposit_allowed": False,
        "postflight_ok": bool(github.get("ok") and zenodo.get("ok")),
        "generated_at": _utc_timestamp(),
    }
    _write_json(editorial / f"PUBLICATION_POSTFLIGHT_{profile.version}_latest.json", payload)
    _write_text(
        editorial / f"PUBLICATION_POSTFLIGHT_{profile.version}_latest.md",
        f"# Public Release Postflight\n\nGitHub: {'PASS' if github.get('ok') else 'FAIL'}\n\nZenodo: {'PASS' if zenodo.get('ok') else 'FAIL'}\n\nJournal submissions: locked.\n",
    )
    return payload
