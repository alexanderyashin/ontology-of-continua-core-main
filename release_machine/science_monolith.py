from __future__ import annotations

import hashlib
import json
import re
import shutil
import subprocess
import time
from pathlib import Path
from typing import Any

from pypdf import PdfReader, PdfWriter

from . import complete


RELEASE_ID = "oc_core_1_3_3"
VERSION = "1.3.3"
RELEASE_ROOT = Path("releases") / RELEASE_ID
ARTIFACTS_REF = RELEASE_ROOT / "artifacts"
EDITORIAL_REF = RELEASE_ROOT / "editorial"
MASTER_PDF_NAME = "OC_CORE_1_3_3_MASTER_MONOGRAPH_EN.pdf"
BASE_SOURCE_REF = Path("releases/oc_core_1_3/monograph/source")
BASE_ENTRYPOINT = "oc_core_1_3_master_monograph.tex"
DELTA_SOURCE_REF = RELEASE_ROOT / "public_payload/sources/OC_CORE_1_3_3_MASTER_MONOGRAPH_EN.md"
BUILD_REF = Path("build_oc_core_1_3_3_science_monolith")

MIN_MONOLITH_PAGES = 690
MIN_MONOLITH_TEXT_CHARS = 1_200_000

MANDATORY_REFS = [
    "claims/CLAIM_LEDGER_1_3_3.json",
    "proofs/THEOREM_REGISTRY_1_3_3.json",
    "proofs/PROOF_DEPENDENCY_GRAPH_1_3_3.json",
    "proofs/FINITE_MODEL_CHECKS_1_3_3.json",
    "formal/lean/OC133V12.lean",
    "formal/lean/LEAN_BUILD_CERTIFICATE_1_3_3.json",
    "validation/target_blind/OC133_TARGET_BLIND_PREDICTION_TABLE.json",
    "validation/numeric_replay_qa/OC133_NUMERIC_REPLAY_QA_TABLE.json",
    "reports/OC_CORE_1_3_3_DOMAIN_VALIDATION_REPORT.json",
    "reports/OC_CORE_1_3_3_COUNTEREXAMPLE_REPORT.json",
    "comparators/OC_1_3_3_NOVELTY_AND_PRIORITY_REGISTER.json",
    "reviews/oc133_llm_cerberus/OC133_LLM_CERBERUS_SUMMARY.json",
    "releases/oc_core_1_3_3/submission_packages/SUBMISSION_PACKAGE_INDEX.json",
    "releases/oc_core_1_3_3/editorial/OC_CORE_1_3_3_RELEASE_SCORECARD_latest.json",
    DELTA_SOURCE_REF.as_posix(),
]

ANCHORS = [
    "Dedicated to my dear wife Maria",
    "Core 1.3.3",
    "OC Core 1.3.3",
    "T133-K0-RES",
    "T133-OMEGA-STATUS",
    "T133-HYBRID",
    "T133-MIN",
    "Lean",
    "finite-model",
    "target-blind",
    "Cerberus",
    "Journal",
]

STALE_PUBLIC_IDENTITY = re.compile(r"\bv1\.3\.2\b|\bversion\s+1\.3\.2\b|oc_core_1_3_2", re.I)


def repo_root(start: Path | None = None) -> Path:
    return complete.repo_root(start)


def rel(root: Path, path: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def write_text_if_changed(path: Path, text: str) -> bool:
    path.parent.mkdir(parents=True, exist_ok=True)
    normalized = text.rstrip() + "\n"
    if path.exists() and read_text(path) == normalized:
        return False
    path.write_text(normalized, encoding="utf-8", newline="\n")
    return True


def write_json_if_changed(path: Path, payload: Any) -> bool:
    return write_text_if_changed(path, json.dumps(payload, ensure_ascii=False, indent=2))


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _safe_clear_build_dir(root: Path, build_dir: Path) -> None:
    resolved_root = root.resolve()
    resolved_build = build_dir.resolve()
    if resolved_root not in resolved_build.parents:
        raise RuntimeError(f"Refusing to clear build directory outside repo: {resolved_build}")
    if build_dir.exists():
        shutil.rmtree(build_dir)
    build_dir.mkdir(parents=True, exist_ok=True)


def _replace_version_tokens(path: Path) -> None:
    if path.suffix.lower() not in {"", ".tex", ".bib", ".md", ".txt", ".yaml", ".yml"}:
        return
    text = read_text(path)
    replacements = {
        "Core~1.3.2": "Core~1.3.3",
        "Core 1.3.2": "Core 1.3.3",
        "Core v1.3.2": "Core v1.3.3",
        "v1.3.2": "v1.3.3",
        "Version 1.3.2": "Version 1.3.3",
        "OC_CORE_1_3_2": "OC_CORE_1_3_3",
        "oc_core_1_3_2": "oc_core_1_3_3",
        "1_3_2": "1_3_3",
        r"OC\_CORE\_1\_3\_2": r"OC\_CORE\_1\_3\_3",
        r"oc\_core\_1\_3\_2": r"oc\_core\_1\_3\_3",
        r"1\_3\_2": r"1\_3\_3",
        "1.3.2": "1.3.3",
        "NO_SEND": "OWNER_REVIEW_LOCKED",
        "NO-SEND": "OWNER-REVIEW-GATED",
        "No-Send": "Owner-Review-Gated",
        "no-send": "owner-review-gated",
        "no_send": "owner_review_locked",
        "28.04.2026": "01.05.2026",
        "28 April 2026": "1 May 2026",
        "XeLaTeX with OC Core 1.3.2 build scripts": "XeLaTeX with OC Core 1.3.3 monolith build scripts",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    path.write_text(text, encoding="utf-8", newline="\n")


def _run(args: list[str], cwd: Path, *, timeout: int) -> dict[str, Any]:
    completed = subprocess.run(
        args,
        cwd=cwd,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        timeout=timeout,
    )
    command = " ".join(args)
    for token in {str(repo_root().resolve()), str(cwd.resolve())}:
        command = command.replace(token, "<REPO_ROOT>")
    stdout_tail = completed.stdout[-3000:].replace(str(repo_root().resolve()), "<REPO_ROOT>").replace(str(cwd.resolve()), "<REPO_ROOT>")
    stderr_tail = completed.stderr[-3000:].replace(str(repo_root().resolve()), "<REPO_ROOT>").replace(str(cwd.resolve()), "<REPO_ROOT>")
    return {
        "command": command,
        "returncode": completed.returncode,
        "stdout_tail": stdout_tail,
        "stderr_tail": stderr_tail,
        "ok": completed.returncode == 0,
    }


def _prepare_base_source(root: Path, build_dir: Path) -> Path:
    src = root / BASE_SOURCE_REF
    dst = build_dir / "base_source"
    shutil.copytree(src, dst)
    for path in dst.rglob("*"):
        if path.is_file():
            _replace_version_tokens(path)
    return dst


def _build_base_pdf(source_dir: Path) -> tuple[Path, list[dict[str, Any]]]:
    commands = []
    entrypoint = BASE_ENTRYPOINT
    commands.append(_run(["xelatex", "-interaction=nonstopmode", "-halt-on-error", entrypoint], source_dir, timeout=900))
    biber = _run(["biber", Path(entrypoint).stem], source_dir, timeout=240)
    commands.append(biber)
    commands.append(_run(["xelatex", "-interaction=nonstopmode", "-halt-on-error", entrypoint], source_dir, timeout=900))
    commands.append(_run(["xelatex", "-interaction=nonstopmode", "-halt-on-error", entrypoint], source_dir, timeout=900))
    pdf = source_dir / f"{Path(entrypoint).stem}.pdf"
    return pdf, commands


def _build_delta_pdf(root: Path, build_dir: Path, doi: str | None, zenodo_record_url: str | None) -> tuple[Path, dict[str, Any]]:
    source = root / DELTA_SOURCE_REF
    output = build_dir / "oc_core_1_3_3_science_delta_appendix.pdf"
    metadata = [
        f"title=OC Core {VERSION} Science Delta Appendix",
        "author=Alexander Yashin",
        "geometry:margin=0.9in",
    ]
    cmd = [
        "pandoc",
        str(source),
        "--from",
        "markdown-raw_tex",
        "--toc",
        "--number-sections",
        "--pdf-engine=xelatex",
    ]
    for item in metadata:
        cmd.extend(["--metadata", item])
    if doi:
        cmd.extend(["--metadata", f"doi={doi}"])
    if zenodo_record_url:
        cmd.extend(["--metadata", f"zenodo-record={zenodo_record_url}"])
    cmd.extend(["-o", str(output)])
    return output, _run(cmd, root, timeout=900)


def _merge_pdfs(base_pdf: Path, delta_pdf: Path, output_pdf: Path) -> dict[str, Any]:
    output_pdf.parent.mkdir(parents=True, exist_ok=True)
    writer = PdfWriter()
    base_reader = PdfReader(str(base_pdf))
    delta_reader = PdfReader(str(delta_pdf))
    for page in base_reader.pages:
        writer.add_page(page)
    for page in delta_reader.pages:
        writer.add_page(page)
    writer.add_metadata(
        {
            "/Title": f"Ontology of Continua Core {VERSION} Science Monolith",
            "/Author": "Alexander Yashin",
            "/Subject": "OC Core 1.3.3 full monograph plus science delta appendix",
            "/Keywords": "Ontology of Continua, OC Core, formal methods, proof governance, target-blind validation",
        }
    )
    tmp = output_pdf.with_suffix(".pdf.tmp")
    with tmp.open("wb") as handle:
        writer.write(handle)
    if not output_pdf.exists() or output_pdf.read_bytes() != tmp.read_bytes():
        output_pdf.write_bytes(tmp.read_bytes())
    tmp.unlink(missing_ok=True)
    return {
        "base_pages": len(base_reader.pages),
        "delta_pages": len(delta_reader.pages),
        "merged_pages": len(PdfReader(str(output_pdf)).pages),
    }


def _pdf_text(path: Path) -> str:
    reader = PdfReader(str(path))
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def _artifact_row(root: Path, ref: str, role: str) -> dict[str, Any]:
    path = root / ref
    return {
        "ref": ref,
        "role": role,
        "exists": path.exists(),
        "sha256": sha256_file(path) if path.is_file() else None,
        "size_bytes": path.stat().st_size if path.is_file() else 0,
    }


def build_corpus_ledger(root: Path, *, output_pdf: Path | None = None) -> dict[str, Any]:
    base_files = sorted(path for path in (root / BASE_SOURCE_REF).rglob("*") if path.is_file() and path.suffix.lower() in {".tex", ".bib", ".md"})
    base_rows = [
        {
            "ref": rel(root, path),
            "role": "INCLUDED_BASELINE_FULL_MONOGRAPH_SOURCE",
            "exists": True,
            "sha256": sha256_file(path),
            "size_bytes": path.stat().st_size,
        }
        for path in base_files
    ]
    mandatory_rows = [_artifact_row(root, ref, "INCLUDED_1_3_3_SCIENCE_DELTA_SOURCE") for ref in MANDATORY_REFS]
    proof_rows = [
        _artifact_row(root, rel(root, path), "INCLUDED_1_3_3_PROOF_SHEET")
        for path in sorted((root / "proofs/proof_sheets").glob("T133-*.md"))
    ]
    missing = [row["ref"] for row in [*mandatory_rows, *proof_rows] if not row["exists"]]
    payload = {
        "schema_id": "OC133_SCIENCE_MONOLITH_CORPUS_LEDGER_v1",
        "release_id": RELEASE_ID,
        "version": VERSION,
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "baseline_source_root": BASE_SOURCE_REF.as_posix(),
        "baseline_entrypoint": (BASE_SOURCE_REF / BASE_ENTRYPOINT).as_posix(),
        "delta_source": DELTA_SOURCE_REF.as_posix(),
        "output_pdf": rel(root, output_pdf) if output_pdf and output_pdf.exists() else str(ARTIFACTS_REF / MASTER_PDF_NAME),
        "baseline_source_total": len(base_rows),
        "mandatory_delta_total": len(mandatory_rows),
        "proof_sheet_total": len(proof_rows),
        "missing_total": len(missing),
        "missing_refs": missing,
        "rows": [*base_rows, *mandatory_rows, *proof_rows],
        "exclusion_policy": {
            "private_material": "Private Logion/k7 material is read-only input only and is excluded unless sanitized into public refs.",
            "runtime_material": "Runtime, cache, draft, and local-path-bearing files are excluded from the public monolith.",
            "journal_packages": "Journal packages are owner-review material and are represented by the package index; no submission is performed here.",
        },
    }
    return payload


def audit_monolith(root: Path, output_pdf: Path | None = None) -> dict[str, Any]:
    path = output_pdf or root / ARTIFACTS_REF / MASTER_PDF_NAME
    ledger_path = root / EDITORIAL_REF / "SCIENCE_MONOLITH_CORPUS_LEDGER_1_3_3_latest.json"
    ledger = json.loads(read_text(ledger_path)) if ledger_path.exists() else build_corpus_ledger(root, output_pdf=path)
    if not path.exists():
        return {
            "schema_id": "OC133_SCIENCE_MONOLITH_AUDIT_v1",
            "state": "FAIL",
            "artifact": rel(root, path),
            "failure_total": 1,
            "failures": ["missing_master_monolith_pdf"],
        }
    text = _pdf_text(path)
    reader = PdfReader(str(path))
    anchor_hits = {anchor: (anchor in text) for anchor in ANCHORS}
    stale_hits = [
        {"match": match.group(0), "context": text[max(0, match.start() - 80) : match.end() + 120].replace("\n", " ")[:260]}
        for match in STALE_PUBLIC_IDENTITY.finditer(text)
    ][:20]
    failures = []
    if len(reader.pages) < MIN_MONOLITH_PAGES:
        failures.append("master_monolith_page_count_below_full_corpus_threshold")
    if len(text) < MIN_MONOLITH_TEXT_CHARS:
        failures.append("master_monolith_text_volume_below_full_corpus_threshold")
    if not all(anchor_hits.values()):
        failures.append("master_monolith_missing_required_text_anchors")
    if stale_hits:
        failures.append("master_monolith_contains_stale_1_3_2_public_identity")
    if ledger.get("missing_total", 1) != 0:
        failures.append("science_monolith_corpus_ledger_has_missing_refs")
    payload = {
        "schema_id": "OC133_SCIENCE_MONOLITH_AUDIT_v1",
        "release_id": RELEASE_ID,
        "version": VERSION,
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "state": "PASS" if not failures else "FAIL",
        "failure_total": len(failures),
        "failures": failures,
        "artifact": rel(root, path),
        "sha256": sha256_file(path),
        "size_bytes": path.stat().st_size,
        "pages": len(reader.pages),
        "text_chars": len(text),
        "min_pages": MIN_MONOLITH_PAGES,
        "min_text_chars": MIN_MONOLITH_TEXT_CHARS,
        "anchor_hits": anchor_hits,
        "stale_public_identity_hit_total": len(stale_hits),
        "stale_public_identity_hits": stale_hits,
        "corpus_ledger": {
            "path": rel(root, ledger_path) if ledger_path.exists() else str(ledger_path),
            "missing_total": ledger.get("missing_total"),
            "baseline_source_total": ledger.get("baseline_source_total"),
            "mandatory_delta_total": ledger.get("mandatory_delta_total"),
            "proof_sheet_total": ledger.get("proof_sheet_total"),
        },
    }
    return payload


def materialize_monolith(
    root: Path | None = None,
    *,
    doi: str | None = None,
    zenodo_record_url: str | None = None,
) -> dict[str, Any]:
    root = repo_root(root)
    build_dir = root / BUILD_REF
    _safe_clear_build_dir(root, build_dir)
    source_dir = _prepare_base_source(root, build_dir)
    base_pdf, base_commands = _build_base_pdf(source_dir)
    delta_pdf, delta_command = _build_delta_pdf(root, build_dir, doi, zenodo_record_url)
    output_pdf = root / ARTIFACTS_REF / MASTER_PDF_NAME
    build_failures = [row for row in [*base_commands, delta_command] if not row["ok"]]
    merge = {}
    if not build_failures and base_pdf.exists() and delta_pdf.exists():
        merge = _merge_pdfs(base_pdf, delta_pdf, output_pdf)
    ledger = build_corpus_ledger(root, output_pdf=output_pdf)
    ledger_path = root / EDITORIAL_REF / "SCIENCE_MONOLITH_CORPUS_LEDGER_1_3_3_latest.json"
    write_json_if_changed(ledger_path, ledger)
    audit = audit_monolith(root, output_pdf=output_pdf)
    audit_path = root / EDITORIAL_REF / "SCIENCE_MONOLITH_AUDIT_1_3_3_latest.json"
    write_json_if_changed(audit_path, audit)
    build_payload = {
        "schema_id": "OC133_SCIENCE_MONOLITH_BUILD_v1",
        "release_id": RELEASE_ID,
        "version": VERSION,
        "state": "PASS" if not build_failures and audit["state"] == "PASS" else "FAIL",
        "build_dir": BUILD_REF.as_posix(),
        "base_source_dir": rel(root, source_dir),
        "base_pdf": rel(root, base_pdf) if base_pdf.exists() else str(base_pdf),
        "delta_pdf": rel(root, delta_pdf) if delta_pdf.exists() else str(delta_pdf),
        "output_pdf": rel(root, output_pdf) if output_pdf.exists() else str(output_pdf),
        "base_commands": base_commands,
        "delta_command": delta_command,
        "build_failure_total": len(build_failures),
        "merge": merge,
        "ledger_path": rel(root, ledger_path),
        "audit_path": rel(root, audit_path),
        "audit": audit,
    }
    write_json_if_changed(root / EDITORIAL_REF / "SCIENCE_MONOLITH_BUILD_1_3_3_latest.json", build_payload)
    lines = [
        "# OC Core 1.3.3 Science Monolith Build",
        "",
        f"State: `{build_payload['state']}`",
        f"Output: `{build_payload['output_pdf']}`",
        f"Pages: `{audit.get('pages')}`",
        f"Text chars: `{audit.get('text_chars')}`",
        f"SHA-256: `{audit.get('sha256')}`",
        f"Failures: `{audit.get('failures')}`",
    ]
    write_text_if_changed(root / EDITORIAL_REF / "SCIENCE_MONOLITH_BUILD_1_3_3_latest.md", "\n".join(lines))
    return build_payload
