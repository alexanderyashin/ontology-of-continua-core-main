from __future__ import annotations

import base64
import dataclasses
import hashlib
import html
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
    r"ghp_[A-Za-z0-9_]{20,}|sk-[A-Za-z0-9]{20,}|Bearer\s+[A-Za-z0-9_.-]{20,}|"
    r"[A-Za-z]:\\Users\\|/home/|estra-private-work)",
    re.IGNORECASE,
)

PUBLIC_FORBIDDEN_RE = re.compile(
    r"\bNO_SEND\b|no-send|no_send|"
    r"publish_allowed\s*[:=]\s*false|owner_approved\s*[:=]\s*false|"
    r"\"publish_allowed\"\s*:\s*false|\"owner_approved\"\s*:\s*false|"
    r"not a public release|manifest_kind[^\n]+NOT_PUBLIC_RELEASE|public release record:\s*none|release DOI:\s*none assigned",
    re.IGNORECASE,
)

MARKDOWN_HEADING_RE = re.compile(r"(?m)^\s{0,3}#{1,6}\s+\S+")
SHA256_HEX_RE = re.compile(r"\b[a-f0-9]{64}\b", re.IGNORECASE)
HTML_STRUCTURE_RE = re.compile(r"</?(p|ul|ol|li|strong|em|a|h2|h3)\b", re.IGNORECASE)


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
    zenodo_assets: list[ReleaseAsset] | None = None
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
        subtitle="Bounded external-review scientific release with typed foundations, proof/evidence ledgers, reproducibility package, and journal owner-review packets",
        release_state="OC_CORE_1_3_3_PUBLIC_GITHUB_ZENODO_RELEASE",
        expected_gate_pass_total=71,
        expected_package_sha256="",
        previous_zenodo_record_id="19851694",
        previous_zenodo_doi="10.5281/zenodo.19851694",
        concept_doi="10.5281/zenodo.17899134",
        creators=[{"name": "Yashin, Alexander", "affiliation": "Independent Researcher", "orcid": "0009-0008-6166-0914"}],
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
                "releases/oc_core_1_3_3/artifacts/oc_core_1_3_3_public_release.zip",
                "Public reproducibility package",
                "Canonical public GitHub/Zenodo reproducibility package; journal submissions require separate approval.",
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
    def parse_assets(items: list[dict[str, Any]] | None) -> list[ReleaseAsset] | None:
        if items is None:
            return None
        return [
            ReleaseAsset(
                path=str(item["path"]),
                label=str(item.get("label", Path(str(item["path"])).name)),
                description=str(item.get("description", "")),
            )
            for item in items
        ]

    payload = dict(payload)
    payload["assets"] = parse_assets(payload.get("assets", [])) or []
    payload["zenodo_assets"] = parse_assets(payload.get("zenodo_assets"))
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
    return _asset_records_for(root, profile.assets)


def _zenodo_assets(profile: ReleaseProfile) -> list[ReleaseAsset]:
    return profile.zenodo_assets if profile.zenodo_assets is not None else profile.assets


def _zenodo_asset_records(root: Path, profile: ReleaseProfile) -> list[dict[str, Any]]:
    return _asset_records_for(root, _zenodo_assets(profile))


def _asset_records_for(root: Path, assets: list[ReleaseAsset]) -> list[dict[str, Any]]:
    records = []
    for asset in assets:
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
    scan_paths = [root / asset.path for asset in profile.assets]
    scan_paths.extend((root / "reviews" / "oc133_llm_cerberus" / "logs").glob("*.log"))
    for path in scan_paths:
        rel_path = path.relative_to(root).as_posix() if path.is_absolute() and root in path.parents else path.as_posix()
        if not path.is_file() or path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            hits.append({"path": rel_path, "issue": f"read_failed:{exc}"})
            continue
        match = SECRET_PATTERN.search(text)
        if match:
            hits.append({"path": rel_path, "issue": f"secret_or_local_path_pattern:{match.group(0)[:60]}"})
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
    bounded_external_review_ready = bool(
        summary.get("external_review_ready_no_send")
        or state == "OC_CORE_1_3_3_EXTERNAL_REVIEW_READY_NO_SEND"
        or state == "OC_CORE_1_3_3_10_10_READY_NO_SEND"
    )
    return {
        "path": _rel(root, path) if path.exists() else str(path),
        "exists": path.exists(),
        "release_state": state,
        "pass_total": pass_total,
        "fail_total": fail_total,
        "master_verdict": summary.get("master_verdict"),
        "external_review_ready": bounded_external_review_ready,
        "all_domain_ready_no_send": bool(summary.get("all_domain_ready_no_send", False)),
        "ok": path.exists()
        and pass_total == profile.expected_gate_pass_total
        and fail_total == 0
        and summary.get("master_verdict") == "PASS"
        and bounded_external_review_ready,
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
        "ok": path.exists()
        and blocker_total == 0
        and str(verdict).upper()
        in {
            "READY_FOR_FINAL_OWNER_APPROVAL_NO_SEND",
            "PUBLIC_RELEASE_REPLACEMENT_READY",
            "PASS",
            "READY_NO_SEND",
        },
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
    public_zip_asset = next((asset for asset in profile.assets if asset.path.endswith("public_release.zip")), None)
    if public_zip_asset is not None:
        public_zip_path = root / public_zip_asset.path
        manifest = _read_json(root / "manifest.json", {})
        manifest_rows = manifest.get("files", []) if isinstance(manifest, dict) else []
        manifest_row = next(
            (row for row in manifest_rows if isinstance(row, dict) and row.get("path") == public_zip_asset.path),
            {},
        )
        actual_sha = _sha256(public_zip_path) if public_zip_path.is_file() else None
        expected_sha = manifest_row.get("sha256") or profile.expected_package_sha256 or actual_sha
        return {
            "path": "manifest.json",
            "package_ref": public_zip_asset.path,
            "exists": public_zip_path.is_file(),
            "manifest_sha256": manifest_row.get("sha256"),
            "actual_sha256": actual_sha,
            "expected_sha256": expected_sha,
            "profile_pins_package_sha256": bool(profile.expected_package_sha256),
            "ok": public_zip_path.is_file()
            and bool(manifest_row)
            and actual_sha == manifest_row.get("sha256")
            and (not profile.expected_package_sha256 or actual_sha == profile.expected_package_sha256),
        }
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


def _public_payload_suitability_ok(root: Path, profile: ReleaseProfile) -> dict[str, Any]:
    path = editorial_root(root, profile) / f"PUBLIC_PAYLOAD_SUITABILITY_{profile.version}_latest.json"
    payload = _read_json(path, {})
    state = payload.get("state")
    monolith = payload.get("science_monolith_audit", {}) if isinstance(payload.get("science_monolith_audit"), dict) else {}
    public_zip_assets = [asset.path for asset in profile.assets if asset.path.endswith("public_release.zip")]
    primary_no_send_assets = [
        asset.path
        for asset in profile.assets
        if "no_send" in Path(asset.path).name.lower() or "nosend" in Path(asset.path).name.lower()
    ]
    pdf_failure_total = int(payload.get("pdf_audit", {}).get("failure_total", 999))
    publication_grade = payload.get("publication_grade_text_gate", {}) if isinstance(payload.get("publication_grade_text_gate"), dict) else {}
    journal_editorial = payload.get("journal_editorial_board_gate", {}) if isinstance(payload.get("journal_editorial_board_gate"), dict) else {}
    scientific_spot = payload.get("scientific_process_spot_gate", {}) if isinstance(payload.get("scientific_process_spot_gate"), dict) else {}
    editorial_cerberus = payload.get("editorial_cerberus_gate", {}) if isinstance(payload.get("editorial_cerberus_gate"), dict) else {}
    forbidden_total = int(payload.get("public_surface_forbidden_hit_total", 999))
    zip_state = payload.get("zip_scan", {}).get("state")
    return {
        "path": _rel(root, path) if path.exists() else str(path),
        "exists": path.exists(),
        "state": state,
        "pdf_failure_total": pdf_failure_total,
        "publication_grade_text_gate_state": publication_grade.get("state"),
        "publication_grade_text_failure_total": publication_grade.get("failure_total"),
        "journal_editorial_board_gate_state": journal_editorial.get("state"),
        "journal_editorial_board_failure_total": journal_editorial.get("failure_total"),
        "scientific_process_spot_gate_state": scientific_spot.get("state"),
        "scientific_process_spot_blocker_total": scientific_spot.get("spot_blocker_total"),
        "scientific_process_spot_maturity": scientific_spot.get("maturity"),
        "editorial_cerberus_gate_state": editorial_cerberus.get("state"),
        "editorial_cerberus_critical_open_total": editorial_cerberus.get("critical_open_total"),
        "editorial_cerberus_high_open_total": editorial_cerberus.get("high_open_total"),
        "science_monolith_state": monolith.get("state"),
        "science_monolith_pages": monolith.get("pages"),
        "science_monolith_text_chars": monolith.get("text_chars"),
        "science_monolith_failure_total": monolith.get("failure_total"),
        "public_surface_forbidden_hit_total": forbidden_total,
        "zip_scan_state": zip_state,
        "public_zip_assets": public_zip_assets,
        "primary_no_send_assets": primary_no_send_assets,
        "ok": path.exists()
        and state == "PASS"
        and monolith.get("state") == "PASS"
        and pdf_failure_total == 0
        and publication_grade.get("state") == "PASS"
        and journal_editorial.get("state") == "PASS"
        and scientific_spot.get("state") == "PASS"
        and editorial_cerberus.get("state") == "PASS"
        and forbidden_total == 0
        and zip_state == "PASS"
        and len(public_zip_assets) == 1
        and not primary_no_send_assets,
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
    gh = (os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN") or "").strip()
    zen = (os.environ.get("ZENODO_ACCESS_TOKEN") or os.environ.get("ZENODO_TOKEN") or "").strip()
    return {
        "github_token_present": bool(gh),
        "zenodo_production_token_present": bool(zen),
        "ok": bool(gh) and bool(zen),
    }


def _github_release_body(profile: ReleaseProfile, checksums: list[dict[str, Any]], zenodo_doi: str | None = None) -> str:
    doi_line = zenodo_doi or "Pending until Zenodo publication completes"
    doi_link = f"https://doi.org/{doi_line}" if zenodo_doi else "Pending until Zenodo publication completes"
    keywords = ", ".join(profile.keywords)
    hashtags = " ".join(profile.hashtags)
    download_base = f"https://github.com/{profile.repository}/releases/download/{profile.tag}"
    primary = [
        ("00_OC_CORE_1_3_3_RELEASE_GUIDE_EN.pdf", "Release guide", "Public landing guide and recommended reading order."),
        ("OC_CORE_1_3_3_MASTER_MONOGRAPH_EN.pdf", "Master monograph", "Canonical long-form scientific reference."),
        ("OC_CORE_1_3_3_JOURNAL_CORE_EN.pdf", "Journal core article", "Compact article-style entry point."),
        (
            "OC_CORE_1_3_3_METHODS_AND_REPRODUCIBILITY_COMPANION_EN.pdf",
            "Methods and reproducibility companion",
            "Reproducibility, validation, and audit navigation.",
        ),
        (
            "OC_CORE_1_3_3_REVIEWER_ATTACK_AND_RESPONSE_MAP_EN.pdf",
            "Reviewer attack and response map",
            "Adversarial objections, boundaries, and responses.",
        ),
        ("oc_core_1_3_3_public_release.zip", "Public reproducibility package", "Proof/evidence corpus and journal owner-review material."),
        ("checksums.txt", "Checksums", "SHA-256 integrity list for all public assets."),
    ]
    asset_lines = "\n".join(
        f"| [{filename}]({download_base}/{urllib.parse.quote(filename)}) | {label} | {description} |"
        for filename, label, description in primary
    )
    return f"""# {profile.title} v{profile.version}

{profile.subtitle}

## Table of Contents

1. Scope and claim boundary
2. Core scientific artifacts
3. Public assets and checksums
4. Journal package status
5. Zenodo DOI and citation
6. Release governance

## Scope

This is the public GitHub and Zenodo release of OC Core {profile.version}. It is a bounded external-review scientific release: the release surface promotes the model-core claims supported by the included proof, finite-model, validation, reproducibility, and adversarial-review artifacts. Broader full-science and unbounded cross-science comparison obligations remain in the background research program unless explicitly evidenced in this release package.

## Public Assets

| Asset | Role | How to use it |
| --- | --- | --- |
{asset_lines}

Checksums for the complete public asset set are in [`checksums.txt`]({download_base}/checksums.txt). Machine-readable metadata is provided as `manifest.json`, `CITATION.cff`, `default.codemeta.json`, and `ro-crate-metadata.jsonld`.

## Journal Packages

The eight journal packages are included as owner-review material. Journal submissions require a separate owner approval before outbound use.

## Zenodo

DOI: {doi_line}

DOI link: {doi_link}

Concept DOI: {profile.concept_doi}

Previous version DOI: {profile.previous_zenodo_doi}

## Keywords

{keywords}

{hashtags}

## Governance

GitHub Release and Zenodo publication were owner-approved for this release phase. Journal submission, email, and Software Heritage deposit are not enabled by this release action.
"""


def _release_body(profile: ReleaseProfile, checksums: list[dict[str, Any]], zenodo_doi: str | None = None) -> str:
    return _github_release_body(profile, checksums, zenodo_doi=zenodo_doi)


def _asset_by_filename(checksums: list[dict[str, Any]], filename: str) -> dict[str, Any]:
    return next((row for row in checksums if row.get("filename") == filename), {})


def _html_link(url: str, label: str) -> str:
    safe_url = html.escape(url, quote=True)
    safe_label = html.escape(label)
    return f'<a href="{safe_url}">{safe_label}</a>'


def _zenodo_html_description(
    profile: ReleaseProfile,
    checksums: list[dict[str, Any]],
    *,
    zenodo_doi: str | None = None,
    zenodo_record_url: str | None = None,
    github_release_url: str | None = None,
) -> str:
    doi = zenodo_doi or "pending"
    doi_url = f"https://doi.org/{doi}" if doi != "pending" else ""
    record_url = zenodo_record_url or (
        f"https://zenodo.org/records/{doi.rsplit('.', 1)[-1]}" if doi.startswith("10.5281/zenodo.") else ""
    )
    github_url = github_release_url or f"https://github.com/{profile.repository}/releases/tag/{profile.tag}"
    pdf_names = [
        "00_OC_CORE_1_3_3_RELEASE_GUIDE_EN.pdf",
        "OC_CORE_1_3_3_MASTER_MONOGRAPH_EN.pdf",
        "OC_CORE_1_3_3_JOURNAL_CORE_EN.pdf",
        "OC_CORE_1_3_3_METHODS_AND_REPRODUCIBILITY_COMPANION_EN.pdf",
        "OC_CORE_1_3_3_REVIEWER_ATTACK_AND_RESPONSE_MAP_EN.pdf",
    ]
    reading_rows = []
    for filename in pdf_names:
        row = _asset_by_filename(checksums, filename)
        label = row.get("label") or filename
        reading_rows.append(f"<li><strong>{html.escape(str(label))}</strong> - {html.escape(filename)}</li>")
    package = _asset_by_filename(checksums, "oc_core_1_3_3_public_release.zip")
    package_label = package.get("label") or "Public reproducibility package"
    reading_rows.append(
        f"<li><strong>{html.escape(str(package_label))}</strong> - "
        "proof, finite-model, validation, review, metadata, and checksum artifacts.</li>"
    )
    doi_html = _html_link(doi_url, doi) if doi_url else html.escape(doi)
    record_html = _html_link(record_url, "Zenodo record") if record_url else "Zenodo record assigned during publication"
    github_html = _html_link(github_url, "GitHub release")
    concept_html = _html_link(f"https://doi.org/{profile.concept_doi}", profile.concept_doi)
    checksum_note = "Checksums are provided in the uploaded checksums.txt file and inside the public release package."
    keywords = ", ".join(profile.keywords[:8])
    return (
        f"<p><strong>{html.escape(profile.title)} v{html.escape(profile.version)}</strong> is a bounded "
        "external-review scientific release of the Ontology of Continua core model. The release packages the typed "
        "foundation, theorem and proof ledgers, Lean/finite-model evidence, target-blind validation summaries, "
        "reproducibility material, and adversarial-review closure artifacts used for external scientific review.</p>"
        "<p>The promoted release claims are bounded by the included evidence. Broader full-science completion and "
        "unbounded cross-science comparison obligations remain part of the continuing research program unless "
        "explicitly evidenced in this package.</p>"
        "<h2>Recommended reading order</h2>"
        f"<ol>{''.join(reading_rows)}</ol>"
        "<h2>Release contents</h2>"
        "<ul>"
        "<li>Five substantive English PDF documents: release guide, master monograph, journal core article, methods companion, and reviewer response map.</li>"
        "<li>One public reproducibility package containing proof, validation, review, metadata, and journal owner-review materials.</li>"
        f"<li>{html.escape(checksum_note)}</li>"
        "</ul>"
        "<h2>Citation and links</h2>"
        "<ul>"
        f"<li>Version DOI: {doi_html}</li>"
        f"<li>Concept DOI: {concept_html}</li>"
        f"<li>{record_html}</li>"
        f"<li>{github_html}</li>"
        "</ul>"
        "<h2>Governance boundary</h2>"
        "<p>GitHub Release and Zenodo publication are approved for OC Core v1.3.3. Journal packages are included "
        "as owner-review material only; journal submission, email campaigns, and Software Heritage deposit require "
        "separate approval.</p>"
        f"<p><strong>Keywords:</strong> {html.escape(keywords)}</p>"
    )


def _zenodo_metadata_suitability(
    profile: ReleaseProfile,
    metadata: dict[str, Any],
    *,
    expected_doi: str | None = None,
    expected_record_url: str | None = None,
) -> dict[str, Any]:
    description = str(metadata.get("description") or "")
    license_value = metadata.get("license")
    license_id = str(license_value.get("id")) if isinstance(license_value, dict) else str(license_value or "")
    related = metadata.get("related_identifiers", [])
    related_identifiers = {str(row.get("identifier")) for row in related if isinstance(row, dict)}
    creators = metadata.get("creators", [])
    creator_has_name = any(isinstance(row, dict) and row.get("name") for row in creators)
    creator_has_orcid = any(isinstance(row, dict) and row.get("orcid") for row in creators)
    creator_affiliation_ok = all(
        not re.search(r"\b(Logion|Estra|ESTRA)\b", str(row.get("affiliation", "")), re.IGNORECASE)
        for row in creators
        if isinstance(row, dict)
    )
    markdown_heading_total = len(MARKDOWN_HEADING_RE.findall(description))
    sha256_total = len(SHA256_HEX_RE.findall(description))
    backtick_total = description.count("`")
    forbidden_hits = PUBLIC_FORBIDDEN_RE.findall(description)
    stale_132 = bool(re.search(r"\b1\.3\.2\b|oc_core_1_3_2", description, re.IGNORECASE))
    html_structure = bool(HTML_STRUCTURE_RE.search(description))
    length = len(description)
    required_phrases = [
        "Recommended reading order",
        "Release contents",
        "Citation and links",
        "Governance boundary",
    ]
    missing_phrases = [phrase for phrase in required_phrases if phrase not in description]
    doi_ok = not expected_doi or expected_doi in description or expected_doi in related_identifiers
    record_ok = not expected_record_url or expected_record_url in description
    concept_ok = profile.concept_doi in description and profile.concept_doi in related_identifiers
    keyword_set = {str(row).lower() for row in metadata.get("keywords", []) if row}
    expected_keywords = {str(row).lower() for row in profile.keywords[:6]}
    missing_keywords = sorted(expected_keywords - keyword_set)
    checks = {
        "title_ok": metadata.get("title") in {f"{profile.title} v{profile.version}", profile.title},
        "version_ok": metadata.get("version") == profile.version,
        "license_ok": license_id == profile.license,
        "creator_has_name": creator_has_name,
        "creator_has_orcid": creator_has_orcid,
        "creator_affiliation_not_instrument_or_method": creator_affiliation_ok,
        "html_structure_ok": html_structure,
        "no_markdown_headings": markdown_heading_total == 0,
        "no_backticks": backtick_total == 0,
        "no_checksum_wall": sha256_total <= 1,
        "description_length_ok": 700 <= length <= 2600,
        "required_sections_ok": not missing_phrases,
        "no_forbidden_public_tokens": not forbidden_hits,
        "no_stale_1_3_2": not stale_132,
        "doi_ok": doi_ok,
        "record_ok": record_ok,
        "concept_doi_ok": concept_ok,
        "keywords_ok": not missing_keywords,
    }
    return {
        "gate_id": "ZENODO_PRESENTATION_SUITABILITY_GATE",
        "description_length": length,
        "markdown_heading_total": markdown_heading_total,
        "sha256_hex_total": sha256_total,
        "backtick_total": backtick_total,
        "missing_required_sections": missing_phrases,
        "missing_keywords": missing_keywords,
        "forbidden_hit_total": len(forbidden_hits),
        "checks": checks,
        "ok": all(checks.values()),
    }


def _public_file_set_gate(root: Path, profile: ReleaseProfile, records: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    expected_assets = _zenodo_assets(profile)
    rows = records or _asset_records_for(root, expected_assets)
    names = [str(row.get("filename") or Path(str(row.get("path", ""))).name) for row in rows]
    expected = {Path(asset.path).name for asset in expected_assets}
    present = {name for name in names if name}
    missing = sorted(expected - present)
    pdf_rows = [row for row in rows if str(row.get("filename", "")).lower().endswith(".pdf")]
    tiny_pdfs = [
        {"filename": row.get("filename"), "size_bytes": row.get("size_bytes", 0)}
        for row in pdf_rows
        if int(row.get("size_bytes") or 0) < 50_000
    ]
    first_name = names[0] if names else ""
    metadata_first = bool(first_name.startswith(".") or first_name.lower() in {"manifest.json", "checksums.txt", "citation.cff"})
    text_metadata_suffixes = {".json", ".jsonld", ".md", ".txt", ".cff", ".yaml", ".yml"}
    text_metadata_files = [
        name
        for name in names
        if Path(name).suffix.lower() in text_metadata_suffixes or name.startswith(".")
    ]
    first_file_text_metadata = bool(first_name and (Path(first_name).suffix.lower() in text_metadata_suffixes or first_name.startswith(".")))
    public_zip_total = sum(1 for name in names if name == "oc_core_1_3_3_public_release.zip")
    no_send_names = [name for name in names if "no_send" in name.lower() or "nosend" in name.lower()]
    checks = {
        "all_expected_files_present": not missing,
        "public_zip_present_once": public_zip_total == 1,
        "pdf_total_ok": len(pdf_rows) >= 4,
        "pdfs_not_tiny": not tiny_pdfs,
        "metadata_not_first": not metadata_first,
        "no_text_metadata_preview_files": not text_metadata_files,
        "first_file_not_text_metadata": not first_file_text_metadata,
        "no_no_send_assets": not no_send_names,
    }
    return {
        "gate_id": "PUBLIC_FILE_SET_GATE",
        "file_total": len(names),
        "first_file": first_name,
        "missing_files": missing,
        "tiny_pdfs": tiny_pdfs,
        "text_metadata_files": text_metadata_files,
        "no_send_asset_names": no_send_names,
        "checks": checks,
        "ok": all(checks.values()),
    }


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
        "access_right": "open",
        "publication_date": "2026-05-01",
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
    body = _github_release_body(profile, assets, zenodo_doi=zenodo_doi)
    zenodo_description = _zenodo_html_description(
        profile,
        assets,
        zenodo_doi=zenodo_doi,
        zenodo_record_url=zenodo_record_url,
        github_release_url=github_release_url,
    )
    zenodo = _zenodo_metadata(profile, zenodo_description, doi=zenodo_doi)
    zenodo_gate = _zenodo_metadata_suitability(
        profile,
        zenodo,
        expected_doi=zenodo_doi,
        expected_record_url=zenodo_record_url,
    )
    file_gate = _public_file_set_gate(root, profile, _zenodo_asset_records(root, profile))
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
        "github_release_body": body,
        "zenodo_html_description": zenodo_description,
        "zenodo_metadata": zenodo,
        "zenodo_presentation_gate": zenodo_gate,
        "public_file_set_gate": file_gate,
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


def _preflight_common(root: Path, profile: ReleaseProfile, *, require_approval: bool, replace_existing: bool = False) -> dict[str, Any]:
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
    public_payload = _public_payload_suitability_ok(root, profile)
    public_metadata = build_public_metadata(root, profile, write=False)
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
        "tag_policy": {
            "ok": (tag_state["local_exists"] and tag_state["remote_exists"]) if replace_existing else (not tag_state["local_exists"] and not tag_state["remote_exists"]),
            "policy": "REPLACE_EXISTING_TAG" if replace_existing else "CREATE_NEW_TAG_ONLY",
            **tag_state,
        },
        "scorecard": scorecard,
        "owner_audit": owner_audit,
        "cerberus": cerberus,
        "journal_lock": journal,
        "delta_queue": delta,
        "zip_integrity": zip_integrity,
        "public_payload_suitability": public_payload,
        "zenodo_presentation_suitability": public_metadata["zenodo_presentation_gate"],
        "public_file_set": public_metadata["public_file_set_gate"],
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
    readiness = _preflight_common(root, profile, require_approval=False, replace_existing=True)
    approval_blocking_checks = {
        key: value
        for key, value in readiness["checks"].items()
        if key not in {"clean_tree", "tag_policy", "owner_publication_approval"}
    }
    approval_ready = all(value.get("ok") for value in approval_blocking_checks.values() if isinstance(value, dict))
    if not approval_ready:
        payload = {
            "schema_id": "LOGION_OWNER_APPROVAL_ATTEMPT_v1",
            "release_id": profile.release_id,
            "version": profile.version,
            "decision": "BLOCKED",
            "owner_identity": owner_identity,
            "reason": "Release readiness preflight failed before owner approval.",
            "readiness": readiness,
            "approval_blocking_checks": approval_blocking_checks,
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
    clean_token = token.strip() if token else ""
    if clean_token:
        request_headers["Authorization"] = f"Bearer {clean_token}"
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
    clean_token = token.strip() if token else ""
    if clean_token:
        headers["Authorization"] = f"Bearer {clean_token}"
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


def _github_asset_upload_name(filename: str) -> str:
    return f"default{filename}" if filename.startswith(".") else filename


def _github_list_release_assets(profile: ReleaseProfile, token: str, release_id: int | str) -> list[dict[str, Any]]:
    payload = _http_json(
        "GET",
        _github_api_url(profile, f"/releases/{release_id}/assets?per_page=100"),
        token=token,
        headers={"Accept": "application/vnd.github+json"},
    )
    return payload if isinstance(payload, list) else []


def _github_delete_asset_if_present(profile: ReleaseProfile, token: str, release_id: int | str, filename: str) -> bool:
    assets = _github_list_release_assets(profile, token, release_id)
    deleted = False
    for item in assets:
        if item.get("name") == filename:
            _http_json(
                "DELETE",
                _github_api_url(profile, f"/releases/assets/{item['id']}"),
                token=token,
                headers={"Accept": "application/vnd.github+json"},
            )
            deleted = True
    return deleted


def _github_upload_assets(root: Path, profile: ReleaseProfile, token: str, release: dict[str, Any]) -> list[dict[str, Any]]:
    uploaded: list[dict[str, Any]] = []
    release_id = release["id"]
    upload_url = str(release["upload_url"]).split("{", 1)[0]
    for asset in profile.assets:
        path = root / asset.path
        filename = path.name
        upload_name = _github_asset_upload_name(filename)
        _github_delete_asset_if_present(profile, token, release_id, upload_name)
        content_type = mimetypes.guess_type(filename)[0] or "application/octet-stream"
        try:
            result = _http_upload(
                "POST",
                f"{upload_url}?name={urllib.parse.quote(upload_name)}",
                token=token,
                data=path.read_bytes(),
                content_type=content_type,
            )
        except RuntimeError as exc:
            if "already_exists" not in str(exc):
                raise
            _github_delete_asset_if_present(profile, token, release_id, upload_name)
            result = _http_upload(
                "POST",
                f"{upload_url}?name={urllib.parse.quote(upload_name)}",
                token=token,
                data=path.read_bytes(),
                content_type=content_type,
            )
        uploaded.append(
            {
                "name": upload_name,
                "source_filename": filename,
                "browser_download_url": result.get("browser_download_url"),
                "id": result.get("id"),
            }
        )
    return uploaded


def _github_replace_assets(root: Path, profile: ReleaseProfile, token: str, release: dict[str, Any]) -> list[dict[str, Any]]:
    release_id = release["id"]
    for item in _github_list_release_assets(profile, token, release_id):
        _http_json(
            "DELETE",
            _github_api_url(profile, f"/releases/assets/{item['id']}"),
            token=token,
            headers={"Accept": "application/vnd.github+json"},
        )
    return _github_upload_assets(root, profile, token, release)


def _github_update_topics(profile: ReleaseProfile, token: str) -> dict[str, Any]:
    try:
        payload = _http_json(
            "PUT",
            _github_api_url(profile, "/topics"),
            token=token,
            payload={"names": profile.github_topics},
            headers={"Accept": "application/vnd.github+json"},
        )
        payload["ok"] = True
        return payload
    except RuntimeError as exc:
        if "HTTP 403" in str(exc):
            return {
                "ok": False,
                "state": "TOPICS_UPDATE_BLOCKED_TOKEN_SCOPE",
                "requested_topics": profile.github_topics,
                "warning": "GitHub release body and Zenodo keywords contain the release keywords/hashtags; repository topic mutation requires a broader token scope.",
            }
        raise


def _zenodo_token() -> str:
    token = (os.environ.get("ZENODO_ACCESS_TOKEN") or os.environ.get("ZENODO_TOKEN") or "").strip()
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


def _zenodo_delete_draft_files(draft: dict[str, Any], token: str) -> list[dict[str, Any]]:
    deleted: list[dict[str, Any]] = []
    draft_id = str(draft["id"])
    for item in draft.get("files", []) or []:
        file_id = item.get("id")
        filename = item.get("filename") or item.get("key")
        delete_url = item.get("links", {}).get("self")
        if delete_url:
            _zenodo_json("DELETE", delete_url, token)
        elif file_id:
            _zenodo_json("DELETE", f"/{draft_id}/files/{file_id}", token)
        else:
            continue
        deleted.append({"id": file_id, "filename": filename})
    return deleted


def _zenodo_publish(root: Path, profile: ReleaseProfile, metadata: dict[str, Any], *, previous_record_id: str | None = None) -> dict[str, Any]:
    token = _zenodo_token()
    source_record_id = previous_record_id or profile.previous_zenodo_record_id
    new_version = _zenodo_json("POST", f"/{source_record_id}/actions/newversion", token)
    latest_draft_url = new_version.get("links", {}).get("latest_draft")
    draft = _zenodo_json("GET", latest_draft_url, token) if latest_draft_url else new_version
    draft_id = str(draft["id"])
    deleted_inherited_files = _zenodo_delete_draft_files(draft, token)
    bucket = draft["links"]["bucket"]
    _zenodo_json("PUT", f"/{draft_id}", token, {"metadata": metadata["zenodo_metadata"]})
    uploaded = []
    for asset in _zenodo_assets(profile):
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
        "source_record_id": source_record_id,
        "deleted_inherited_files": deleted_inherited_files,
        "uploaded": uploaded,
        "published": published,
    }


def _zenodo_reserved_doi(draft: dict[str, Any]) -> str | None:
    metadata = draft.get("metadata", {}) if isinstance(draft, dict) else {}
    prereserved = metadata.get("prereserve_doi", {}) if isinstance(metadata, dict) else {}
    if isinstance(prereserved, dict) and prereserved.get("doi"):
        return str(prereserved["doi"])
    draft_id = draft.get("record_id") or draft.get("id")
    return f"10.5281/zenodo.{draft_id}" if draft_id else None


def prepare_zenodo_replacement_draft(root: Path, *, release_id: str) -> dict[str, Any]:
    profile = load_profile(root, release_id)
    token = _zenodo_token()
    editorial = editorial_root(root, profile)
    presentation = _read_json(editorial / f"PUBLIC_RELEASE_PRESENTATION_{profile.version}_latest.json", {})
    current_record_url = str(presentation.get("zenodo_record_url") or "")
    source_record_id = current_record_url.rstrip("/").split("/")[-1] if current_record_url else profile.previous_zenodo_record_id
    new_version = _zenodo_json("POST", f"/{source_record_id}/actions/newversion", token)
    latest_draft_url = new_version.get("links", {}).get("latest_draft")
    draft = _zenodo_json("GET", latest_draft_url, token) if latest_draft_url else new_version
    deleted_inherited_files = _zenodo_delete_draft_files(draft, token)
    payload = {
        "schema_id": "LOGION_ZENODO_REPLACEMENT_DRAFT_v1",
        "release_id": profile.release_id,
        "version": profile.version,
        "source_record_id": source_record_id,
        "draft_id": str(draft["id"]),
        "draft_record_id": str(draft.get("record_id") or draft["id"]),
        "reserved_doi": _zenodo_reserved_doi(draft),
        "latest_draft_url": latest_draft_url,
        "bucket_url": draft.get("links", {}).get("bucket"),
        "deleted_inherited_files": deleted_inherited_files,
        "inherited_file_delete_total": len(deleted_inherited_files),
        "created_at": _utc_timestamp(),
    }
    _write_json(editorial / f"ZENODO_REPLACEMENT_DRAFT_{profile.version}_latest.json", payload)
    return payload


def _zenodo_publish_prepared_draft(root: Path, profile: ReleaseProfile, metadata: dict[str, Any], draft_payload: dict[str, Any]) -> dict[str, Any]:
    token = _zenodo_token()
    draft_id = str(draft_payload["draft_id"])
    draft = _zenodo_json("GET", f"/{draft_id}", token)
    deleted_inherited_files = _zenodo_delete_draft_files(draft, token)
    bucket = draft.get("links", {}).get("bucket") or draft_payload.get("bucket_url")
    if not bucket:
        raise RuntimeError("Zenodo draft bucket URL is missing.")
    _zenodo_json("PUT", f"/{draft_id}", token, {"metadata": metadata["zenodo_metadata"]})
    uploaded = []
    for asset in _zenodo_assets(profile):
        result = _zenodo_upload_file(bucket, token, root / asset.path)
        uploaded.append({"filename": (root / asset.path).name, "result": result})
    published = _zenodo_json("POST", f"/{draft_id}/actions/publish", token)
    record_id = str(published.get("record_id") or published.get("id") or draft_id)
    doi = published.get("doi") or published.get("metadata", {}).get("doi") or draft_payload.get("reserved_doi")
    return {
        "draft_id": draft_id,
        "record_id": record_id,
        "record_url": f"https://zenodo.org/records/{record_id}",
        "doi": doi,
        "source_record_id": draft_payload.get("source_record_id"),
        "deleted_inherited_files": [*draft_payload.get("deleted_inherited_files", []), *deleted_inherited_files],
        "uploaded": uploaded,
        "published": published,
    }


def _zenodo_mark_superseded(record_id: str, corrected_doi: str, corrected_record_url: str) -> dict[str, Any]:
    token = _zenodo_token()
    try:
        edit = _zenodo_json("POST", f"/{record_id}/actions/edit", token)
        draft_id = str(edit.get("id") or record_id)
        draft = _zenodo_json("GET", f"/{draft_id}", token)
        metadata = draft.get("metadata", {})
        description = str(metadata.get("description", ""))
        note = (
            f"\n\n<p><strong>Superseded release notice:</strong> This record is superseded by "
            f"the corrected OC Core v1.3.3 public release {corrected_doi} at {corrected_record_url}.</p>"
        )
        if corrected_doi not in description:
            metadata["description"] = description + note
        related = metadata.get("related_identifiers", [])
        if not isinstance(related, list):
            related = []
        if not any(isinstance(row, dict) and row.get("identifier") == corrected_doi for row in related):
            related.append({"identifier": corrected_doi, "relation": "isPreviousVersionOf", "scheme": "doi"})
        metadata["related_identifiers"] = related
        _zenodo_json("PUT", f"/{draft_id}", token, {"metadata": metadata})
        published = _zenodo_json("POST", f"/{draft_id}/actions/publish", token)
        return {"record_id": record_id, "state": "SUPERSEDED_METADATA_UPDATED", "published": bool(published)}
    except Exception as exc:
        return {"record_id": record_id, "state": "METADATA_EDIT_BLOCKED_BY_ZENODO", "error": str(exc)[:1000]}


def _zenodo_update_published_metadata(record_id: str, metadata: dict[str, Any]) -> dict[str, Any]:
    token = _zenodo_token()
    edit = _zenodo_json("POST", f"/{record_id}/actions/edit", token)
    draft_id = str(edit.get("id") or record_id)
    draft = _zenodo_json("GET", f"/{draft_id}", token)
    current_metadata = draft.get("metadata", {})
    if not isinstance(current_metadata, dict):
        current_metadata = {}
    merged_metadata = dict(current_metadata)
    for key in [
        "title",
        "upload_type",
        "publication_type",
        "description",
        "creators",
        "license",
        "keywords",
        "version",
        "related_identifiers",
    ]:
        if key in metadata:
            merged_metadata[key] = metadata[key]
    _zenodo_json("PUT", f"/{draft_id}", token, {"metadata": merged_metadata})
    published = _zenodo_json("POST", f"/{draft_id}/actions/publish", token)
    return {
        "record_id": record_id,
        "draft_id": draft_id,
        "updated_metadata_keys": sorted(set(metadata) & set(merged_metadata)),
        "published": bool(published),
        "doi": published.get("doi") or published.get("metadata", {}).get("doi"),
    }


def repair_zenodo_presentation_in_place(root: Path, *, release_id: str) -> dict[str, Any]:
    profile = load_profile(root, release_id)
    editorial = editorial_root(root, profile)
    presentation = _read_json(editorial / f"PUBLIC_RELEASE_PRESENTATION_{profile.version}_latest.json", {})
    report = _read_json(editorial / f"PUBLICATION_EXECUTION_REPORT_{profile.version}_latest.json", {})
    zenodo_record_url = str(presentation.get("zenodo_record_url") or report.get("zenodo_record_url") or "")
    zenodo_doi = str(presentation.get("zenodo_doi") or report.get("zenodo_doi") or "")
    github_release_url = str(presentation.get("github_release_url") or report.get("github_release_url") or "")
    record_id = zenodo_record_url.rstrip("/").split("/")[-1] if zenodo_record_url else str(report.get("zenodo_record_id") or "")
    if not record_id:
        raise RuntimeError("Cannot repair Zenodo presentation: record id is missing.")
    metadata = build_public_metadata(
        root,
        profile,
        zenodo_doi=zenodo_doi or None,
        zenodo_record_url=zenodo_record_url or None,
        github_release_url=github_release_url or None,
        write=True,
    )
    gate = metadata["zenodo_presentation_gate"]
    if not gate["ok"]:
        raise RuntimeError(f"Zenodo presentation gate failed locally: {gate}")
    remote_update = _zenodo_update_published_metadata(record_id, metadata["zenodo_metadata"])
    live = _zenodo_verify(profile, record_id)
    now = _utc_timestamp()
    payload = {
        "schema_id": "LOGION_ZENODO_PRESENTATION_REPAIR_v1",
        "release_id": profile.release_id,
        "version": profile.version,
        "repair_policy": "IN_PLACE_FIRST",
        "record_id": record_id,
        "zenodo_record_url": zenodo_record_url or f"https://zenodo.org/records/{record_id}",
        "zenodo_doi": zenodo_doi or live.get("doi"),
        "github_release_url": github_release_url,
        "local_zenodo_presentation_gate": gate,
        "local_public_file_set_gate": metadata["public_file_set_gate"],
        "remote_update": remote_update,
        "live_zenodo_verification": live,
        "fallback_required": not bool(live.get("ok")),
        "generated_at": now,
    }
    _write_json(editorial / f"ZENODO_PRESENTATION_REPAIR_{profile.version}_latest.json", payload)
    _write_text(
        editorial / f"ZENODO_PRESENTATION_REPAIR_{profile.version}_latest.md",
        "\n".join(
            [
                "# Zenodo Presentation Repair",
                "",
                f"Release: `{profile.release_id}` v{profile.version}",
                "",
                f"Record: {payload['zenodo_record_url']}",
                "",
                f"DOI: {payload['zenodo_doi']}",
                "",
                f"Local presentation gate: {'PASS' if gate.get('ok') else 'FAIL'}",
                "",
                f"Live Zenodo gate: {'PASS' if live.get('ok') else 'FAIL'}",
                "",
                f"Fallback required: `{str(payload['fallback_required']).lower()}`",
            ]
        ),
    )
    return payload


def repair_github_presentation(root: Path, *, release_id: str) -> dict[str, Any]:
    profile = load_profile(root, release_id)
    editorial = editorial_root(root, profile)
    presentation = _read_json(editorial / f"PUBLIC_RELEASE_PRESENTATION_{profile.version}_latest.json", {})
    report = _read_json(editorial / f"PUBLICATION_EXECUTION_REPORT_{profile.version}_latest.json", {})
    zenodo_doi = str(presentation.get("zenodo_doi") or report.get("zenodo_doi") or "")
    zenodo_record_url = str(presentation.get("zenodo_record_url") or report.get("zenodo_record_url") or "")
    github_release_url = str(presentation.get("github_release_url") or report.get("github_release_url") or "")
    metadata = build_public_metadata(
        root,
        profile,
        zenodo_doi=zenodo_doi or None,
        zenodo_record_url=zenodo_record_url or None,
        github_release_url=github_release_url or None,
        write=True,
    )
    body = metadata["github_release_body"]
    if PUBLIC_FORBIDDEN_RE.search(body) or re.search(r"\b1\.3\.2\b|oc_core_1_3_2", body, re.IGNORECASE):
        raise RuntimeError("GitHub release body failed public-surface scan.")
    token = (os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN") or "").strip()
    if not token:
        raise RuntimeError("GITHUB_TOKEN or GH_TOKEN is required for GitHub presentation repair.")
    release = _github_create_or_update_release(profile, token, body)
    live = _github_release_verify(profile, token)
    now = _utc_timestamp()
    payload = {
        "schema_id": "LOGION_GITHUB_PRESENTATION_REPAIR_v1",
        "release_id": profile.release_id,
        "version": profile.version,
        "github_release_url": release.get("html_url") or github_release_url,
        "release_id_remote": release.get("id"),
        "live_github_verification": live,
        "assets_touched": False,
        "tag_touched": False,
        "generated_at": now,
    }
    _write_json(editorial / f"GITHUB_PRESENTATION_REPAIR_{profile.version}_latest.json", payload)
    _write_text(
        editorial / f"GITHUB_PRESENTATION_REPAIR_{profile.version}_latest.md",
        "\n".join(
            [
                "# GitHub Presentation Repair",
                "",
                f"Release: `{profile.release_id}` v{profile.version}",
                "",
                f"GitHub: {payload['github_release_url']}",
                "",
                f"Live GitHub gate: {'PASS' if live.get('ok') else 'FAIL'}",
                "",
                "Assets touched: `false`",
                "",
                "Tag touched: `false`",
            ]
        ),
    )
    return payload


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


def _replace_tag_and_push(root: Path, profile: ReleaseProfile) -> dict[str, Any]:
    head = _git_head(root)
    existing_local = _run(root, ["git", "tag", "--list", profile.tag], timeout=60).stdout.strip()
    existing_remote = _run(root, ["git", "ls-remote", "--tags", "origin", profile.tag], timeout=120).stdout.strip()
    if existing_local:
        _run(root, ["git", "tag", "-d", profile.tag], timeout=60)
    _run(root, ["git", "tag", "-a", profile.tag, "-m", f"{profile.title} v{profile.version} corrected public release", head], timeout=60)
    branch_push = _run(root, ["git", "push", "-u", "origin", f"HEAD:{profile.branch}"], timeout=300)
    tag_push = _run(root, ["git", "push", "--force", "origin", profile.tag], timeout=300)
    return {
        "tag": profile.tag,
        "head": head,
        "previous_local_tag_present": bool(existing_local),
        "previous_remote_tag_present": bool(existing_remote),
        "tag_sha": _run(root, ["git", "rev-parse", profile.tag], timeout=60).stdout.strip(),
        "tag_commit": _run(root, ["git", "rev-parse", f"{profile.tag}^{{}}"], timeout=60).stdout.strip(),
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

    github_token = (os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN") or "").strip()
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


def replace_public_release(root: Path, *, release_id: str) -> dict[str, Any]:
    profile = load_profile(root, release_id)
    preflight = _preflight_common(root, profile, require_approval=True, replace_existing=True)
    if not preflight["preflight_ok"]:
        raise RuntimeError("Replacement publication preflight failed; refusing to replace public release.")
    draft_payload = _read_json(editorial_root(root, profile) / f"ZENODO_REPLACEMENT_DRAFT_{profile.version}_latest.json", {})
    if not draft_payload.get("draft_id") or not draft_payload.get("reserved_doi"):
        raise RuntimeError("Zenodo replacement draft is missing; run publication-replacement-draft before replacement.")
    reserved_doi = str(draft_payload["reserved_doi"])
    reserved_record_url = f"https://zenodo.org/records/{draft_payload.get('draft_record_id') or draft_payload['draft_id']}"
    metadata = build_public_metadata(
        root,
        profile,
        zenodo_doi=reserved_doi,
        zenodo_record_url=reserved_record_url,
        write=False,
    )
    if PUBLIC_FORBIDDEN_RE.search(metadata["release_body"]):
        raise RuntimeError("GitHub/Zenodo public release body contains forbidden no-send contradiction language.")
    if _git_status(root):
        raise RuntimeError("Working tree must be clean before tag replacement and public upload.")
    tag_result = _replace_tag_and_push(root, profile)
    zenodo_result = _zenodo_publish_prepared_draft(root, profile, metadata, draft_payload)
    if zenodo_result.get("doi") != reserved_doi:
        raise RuntimeError(
            f"Zenodo DOI changed after publish: reserved={reserved_doi}, actual={zenodo_result.get('doi')}. "
            "Do not update GitHub until a corrected DOI-bound payload is rebuilt."
        )
    github_token = (os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN") or "").strip()
    if not github_token:
        raise RuntimeError("GITHUB_TOKEN or GH_TOKEN is required for GitHub Release replacement.")
    metadata = build_public_metadata(
        root,
        profile,
        zenodo_doi=zenodo_result.get("doi"),
        zenodo_record_url=zenodo_result.get("record_url"),
        write=False,
    )
    github_release = _github_create_or_update_release(profile, github_token, metadata["release_body"])
    uploaded_assets = _github_replace_assets(root, profile, github_token, github_release)
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
    supersession_record_ids = {
        "19956748",
        "19956854",
        "19957779",
        "19964204",
        str(zenodo_result.get("source_record_id") or ""),
        str(draft_payload.get("source_record_id") or ""),
    }
    supersession = [
        _zenodo_mark_superseded(record_id, str(zenodo_result.get("doi")), str(zenodo_result.get("record_url")))
        for record_id in sorted(record for record in supersession_record_ids if record)
        if str(record_id) != str(zenodo_result.get("record_id"))
    ]
    now = _utc_timestamp()
    report = {
        "schema_id": "LOGION_PUBLICATION_EXECUTION_REPORT_v2",
        "release_id": profile.release_id,
        "version": profile.version,
        "tag": profile.tag,
        "replacement_mode": "REPLACE_BAD_PUBLIC_V1_3_3_IN_PLACE",
        "tag_result": tag_result,
        "github_release_url": github_url,
        "github_release_id": github_release.get("id"),
        "github_uploaded_assets": uploaded_assets,
        "github_topics": topics,
        "zenodo_record_url": zenodo_result.get("record_url"),
        "zenodo_record_id": zenodo_result.get("record_id"),
        "zenodo_doi": zenodo_result.get("doi"),
        "zenodo_source_record_id": zenodo_result.get("source_record_id"),
        "zenodo_deleted_inherited_files": zenodo_result.get("deleted_inherited_files"),
        "zenodo_uploaded": zenodo_result.get("uploaded"),
        "superseded_records": supersession,
        "asset_checksums": _asset_records(root, profile),
        "publication_timestamp": now,
        "journal_submissions_allowed": False,
        "software_heritage_deposit_allowed": False,
    }
    editorial = editorial_root(root, profile)
    _write_json(editorial / f"PUBLICATION_EXECUTION_REPORT_{profile.version}_latest.json", report)
    _write_text(
        editorial / f"PUBLICATION_EXECUTION_REPORT_{profile.version}_latest.md",
        f"# Public Release Execution Report\n\nRelease: `{profile.release_id}` v{profile.version}\n\nReplacement mode: replace invalid public v1.3.3 in place.\n\nGitHub: {github_url}\n\nZenodo: {zenodo_result.get('record_url')}\n\nDOI: {zenodo_result.get('doi')}\n\nJournal submissions: require separate approval.\n",
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


def resume_github_after_zenodo(root: Path, *, release_id: str) -> dict[str, Any]:
    profile = load_profile(root, release_id)
    status = _git_status(root)
    if status:
        raise RuntimeError(f"Working tree must be clean before publication recovery: {status}")
    tag_state = _git_tag_exists(root, profile.tag)
    if not tag_state["local_exists"] or not tag_state["remote_exists"]:
        raise RuntimeError(f"Cannot resume GitHub publication; tag {profile.tag} is not present locally and remotely.")
    editorial = editorial_root(root, profile)
    presentation = _read_json(editorial / f"PUBLIC_RELEASE_PRESENTATION_{profile.version}_latest.json", {})
    zenodo_doi = presentation.get("zenodo_doi")
    zenodo_record_url = presentation.get("zenodo_record_url")
    if not zenodo_doi or not zenodo_record_url:
        raise RuntimeError("Cannot resume GitHub publication; Zenodo DOI/record URL is missing from public release presentation.")
    github_token = (os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN") or "").strip()
    if not github_token:
        raise RuntimeError("GITHUB_TOKEN or GH_TOKEN is required for GitHub Release publication.")
    metadata = build_public_metadata(
        root,
        profile,
        zenodo_doi=zenodo_doi,
        zenodo_record_url=zenodo_record_url,
        write=False,
    )
    github_release = _github_create_or_update_release(profile, github_token, metadata["release_body"])
    uploaded_assets = _github_upload_assets(root, profile, github_token, github_release)
    topics = _github_update_topics(profile, github_token)
    github_url = github_release.get("html_url") or f"https://github.com/{profile.repository}/releases/tag/{profile.tag}"
    metadata = build_public_metadata(
        root,
        profile,
        zenodo_doi=zenodo_doi,
        zenodo_record_url=zenodo_record_url,
        github_release_url=github_url,
        write=True,
    )
    now = _utc_timestamp()
    tag_object = _run(root, ["git", "rev-parse", profile.tag], timeout=60).stdout.strip()
    tag_commit = _run(root, ["git", "rev-parse", f"{profile.tag}^{{}}"], timeout=60).stdout.strip()
    report = {
        "schema_id": "LOGION_PUBLICATION_EXECUTION_REPORT_v1",
        "release_id": profile.release_id,
        "version": profile.version,
        "tag": profile.tag,
        "recovery_mode": "RESUME_GITHUB_AFTER_ZENODO",
        "tag_result": {
            "tag": profile.tag,
            "tag_sha": tag_object,
            "tag_commit": tag_commit,
            "remote_tag_present": tag_state["remote_exists"],
        },
        "github_release_url": github_url,
        "github_release_id": github_release.get("id"),
        "github_uploaded_assets": uploaded_assets,
        "github_topics": topics,
        "zenodo_record_url": zenodo_record_url,
        "zenodo_record_id": str(zenodo_record_url).rstrip("/").split("/")[-1],
        "zenodo_doi": zenodo_doi,
        "asset_checksums": _asset_records(root, profile),
        "publication_timestamp": now,
        "journal_submissions_allowed": False,
        "software_heritage_deposit_allowed": False,
    }
    _write_json(editorial / f"PUBLICATION_EXECUTION_REPORT_{profile.version}_latest.json", report)
    _write_text(
        editorial / f"PUBLICATION_EXECUTION_REPORT_{profile.version}_latest.md",
        f"# Public Release Execution Report\n\nRelease: `{profile.release_id}` v{profile.version}\n\nGitHub: {github_url}\n\nZenodo: {zenodo_record_url}\n\nDOI: {zenodo_doi}\n\nRecovery mode: resume GitHub after successful Zenodo publication.\n\nJournal submissions: locked.\n",
    )

    approval_path = editorial / f"OWNER_RELEASE_APPROVAL_v{profile.version}.json"
    approval = _read_json(approval_path, {})
    approval.update(
        {
            "published": True,
            "publication_timestamp": now,
            "github_release_url": github_url,
            "zenodo_record_url": zenodo_record_url,
            "zenodo_doi": zenodo_doi,
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
            "zenodo_record_url": zenodo_record_url,
            "zenodo_doi": zenodo_doi,
            "journal_submissions_allowed": False,
        }
    )
    _write_json(manifest_path, manifest)
    return report


def republish_clean_zenodo_and_update_github(root: Path, *, release_id: str) -> dict[str, Any]:
    profile = load_profile(root, release_id)
    status = _git_status(root)
    if status:
        raise RuntimeError(f"Working tree must be clean before Zenodo clean republish: {status}")
    editorial = editorial_root(root, profile)
    presentation = _read_json(editorial / f"PUBLIC_RELEASE_PRESENTATION_{profile.version}_latest.json", {})
    current_record_url = str(presentation.get("zenodo_record_url") or "")
    current_record_id = current_record_url.rstrip("/").split("/")[-1] if current_record_url else profile.previous_zenodo_record_id
    metadata = build_public_metadata(root, profile, write=False)
    zenodo_result = _zenodo_publish(root, profile, metadata, previous_record_id=current_record_id)
    github_token = (os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN") or "").strip()
    if not github_token:
        raise RuntimeError("GITHUB_TOKEN or GH_TOKEN is required for GitHub Release metadata update.")
    metadata = build_public_metadata(
        root,
        profile,
        zenodo_doi=zenodo_result.get("doi"),
        zenodo_record_url=zenodo_result.get("record_url"),
        write=False,
    )
    github_release = _github_create_or_update_release(profile, github_token, metadata["release_body"])
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
        "recovery_mode": "ZENODO_CLEAN_REPUBLISH_AFTER_INHERITED_FILE_DETECTION",
        "github_release_url": github_url,
        "github_release_id": github_release.get("id"),
        "zenodo_record_url": zenodo_result.get("record_url"),
        "zenodo_record_id": zenodo_result.get("record_id"),
        "zenodo_doi": zenodo_result.get("doi"),
        "zenodo_source_record_id": zenodo_result.get("source_record_id"),
        "zenodo_deleted_inherited_files": zenodo_result.get("deleted_inherited_files"),
        "zenodo_uploaded": zenodo_result.get("uploaded"),
        "asset_checksums": _asset_records(root, profile),
        "publication_timestamp": now,
        "journal_submissions_allowed": False,
        "software_heritage_deposit_allowed": False,
    }
    _write_json(editorial / f"PUBLICATION_EXECUTION_REPORT_{profile.version}_latest.json", report)
    _write_text(
        editorial / f"PUBLICATION_EXECUTION_REPORT_{profile.version}_latest.md",
        f"# Public Release Execution Report\n\nRelease: `{profile.release_id}` v{profile.version}\n\nGitHub: {github_url}\n\nZenodo: {zenodo_result.get('record_url')}\n\nDOI: {zenodo_result.get('doi')}\n\nRecovery mode: clean Zenodo republish after inherited-file detection.\n\nJournal submissions: locked.\n",
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
    expected = {_github_asset_upload_name(Path(asset.path).name) for asset in profile.assets}
    missing = sorted(expected - names)
    unexpected = sorted(names - expected)
    body = str(release.get("body") or "")
    forbidden_hits = PUBLIC_FORBIDDEN_RE.findall(body)
    stale_132 = bool(re.search(r"\b1\.3\.2\b|oc_core_1_3_2", body, re.IGNORECASE))
    return {
        "exists": True,
        "url": release.get("html_url"),
        "asset_total": len(assets),
        "missing_assets": missing,
        "unexpected_assets": unexpected,
        "body_has_markdown_toc": "## Table of Contents" in body,
        "body_has_hashtags": all(tag in body for tag in profile.hashtags[:3]),
        "body_has_checksums_link": "checksums.txt" in body,
        "forbidden_hit_total": len(forbidden_hits),
        "stale_1_3_2": stale_132,
        "ok": not missing
        and not unexpected
        and release.get("tag_name") == profile.tag
        and "## Table of Contents" in body
        and "checksums.txt" in body
        and len(forbidden_hits) == 0
        and not stale_132,
    }


def _zenodo_verify(profile: ReleaseProfile, record_id: str) -> dict[str, Any]:
    record = _zenodo_record(record_id)
    files = record.get("files", [])
    names = {item.get("key") for item in files}
    expected = {Path(asset.path).name for asset in _zenodo_assets(profile)}
    missing = sorted(expected - names)
    unexpected = sorted(names - expected)
    doi = record.get("doi")
    metadata = record.get("metadata", {})
    remote_records = [
        {
            "filename": item.get("key"),
            "size_bytes": item.get("size"),
            "sha256": str(item.get("checksum", "")).removeprefix("md5:").removeprefix("sha256:") or None,
        }
        for item in files
    ]
    presentation_gate = _zenodo_metadata_suitability(
        profile,
        metadata,
        expected_doi=str(doi) if doi else None,
        expected_record_url=f"https://zenodo.org/records/{record.get('id')}",
    )
    file_gate = _public_file_set_gate(Path.cwd(), profile, remote_records)
    return {
        "exists": bool(record.get("id")),
        "record_id": str(record.get("id")),
        "doi": doi,
        "file_total": len(files),
        "missing_files": missing,
        "unexpected_files": unexpected,
        "presentation_gate": presentation_gate,
        "public_file_set_gate": file_gate,
        "ok": bool(record.get("id"))
        and not missing
        and not unexpected
        and str(metadata.get("version")) == profile.version
        and presentation_gate["ok"]
        and file_gate["ok"],
    }


def _github_zenodo_parity_gate(profile: ReleaseProfile, github: dict[str, Any], zenodo: dict[str, Any]) -> dict[str, Any]:
    doi = str(zenodo.get("doi") or "")
    github_url = str(github.get("url") or "")
    checks = {
        "github_ok": bool(github.get("ok")),
        "zenodo_ok": bool(zenodo.get("ok")),
        "doi_present": doi.startswith("10.5281/zenodo."),
        "github_release_url_ok": profile.tag in github_url,
        "version_ok": profile.version == "1.3.3",
        "journal_submission_lock_preserved": profile.journal_submissions_allowed is False,
    }
    return {
        "gate_id": "GITHUB_ZENODO_PARITY_GATE",
        "doi": doi,
        "github_url": github_url,
        "checks": checks,
        "ok": all(checks.values()),
    }


def postflight(root: Path, *, release_id: str) -> dict[str, Any]:
    profile = load_profile(root, release_id)
    editorial = editorial_root(root, profile)
    report = _read_json(editorial / f"PUBLICATION_EXECUTION_REPORT_{profile.version}_latest.json", {})
    postflight_path = editorial / f"PUBLICATION_POSTFLIGHT_{profile.version}_latest.json"
    previous_postflight = _read_json(postflight_path, {})
    github_token = (os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN") or "").strip()
    if not github_token:
        raise RuntimeError("GITHUB_TOKEN or GH_TOKEN is required for postflight.")
    github = _github_release_verify(profile, github_token)
    record_id = str(report.get("zenodo_record_id", ""))
    zenodo = _zenodo_verify(profile, record_id) if record_id else {"ok": False, "missing": "record_id"}
    parity = _github_zenodo_parity_gate(profile, github, zenodo)
    checksums = _asset_records(root, profile)
    payload = {
        "schema_id": "LOGION_PUBLICATION_POSTFLIGHT_v1",
        "release_id": profile.release_id,
        "version": profile.version,
        "tag": profile.tag,
        "github": github,
        "zenodo": zenodo,
        "github_zenodo_parity_gate": parity,
        "asset_checksums": checksums,
        "journal_submissions_allowed": False,
        "software_heritage_deposit_allowed": False,
        "postflight_ok": bool(github.get("ok") and zenodo.get("ok") and parity.get("ok")),
        "generated_at": _utc_timestamp(),
    }
    comparable_previous = {key: value for key, value in previous_postflight.items() if key != "generated_at"}
    comparable_current = {key: value for key, value in payload.items() if key != "generated_at"}
    if comparable_previous == comparable_current and previous_postflight.get("generated_at"):
        payload["generated_at"] = previous_postflight["generated_at"]
    _write_json(postflight_path, payload)
    _write_text(
        editorial / f"PUBLICATION_POSTFLIGHT_{profile.version}_latest.md",
        f"# Public Release Postflight\n\nGitHub: {'PASS' if github.get('ok') else 'FAIL'}\n\nZenodo: {'PASS' if zenodo.get('ok') else 'FAIL'}\n\nJournal submissions: locked.\n",
    )
    return payload
