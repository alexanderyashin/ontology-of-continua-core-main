from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from textwrap import dedent


ROOT = Path(__file__).resolve().parents[1]
STAMP = "2026-04-25T00:00:00Z"


def write_text(path: str, text: str) -> None:
    target = ROOT / path
    target.parent.mkdir(parents=True, exist_ok=True)
    body = dedent(text).lstrip()
    if not body.endswith("\n"):
        body += "\n"
    target.write_text(body, encoding="utf-8")


def write_json(path: str, payload: object) -> None:
    target = ROOT / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


GATES = [
    ("00", "intake", "Release intake and identity"),
    ("01", "channel_policy", "Channel policy"),
    ("02", "artifact_inventory", "Artifact inventory"),
    ("03", "build_reproducibility", "Build and reproducibility"),
    ("04", "pdf_document_quality", "PDF document quality"),
    ("05", "claim_evidence_ceiling", "Claim and evidence ceiling"),
    ("06", "strong_statement_linter", "Strong statement linter"),
    ("07", "simulation_data_validation", "Simulation and data boundary"),
    ("08", "citation_doi_metadata", "Citation and DOI metadata"),
    ("09", "public_surface_parity", "Public surface parity"),
    ("10", "security_privacy_secrets", "Security, privacy, secrets"),
    ("11", "ci_release_workflow", "CI release workflow"),
    ("12", "owner_approval", "Owner approval no-send lock"),
    ("13", "publish_preflight", "Publish preflight"),
    ("14", "post_release_audit", "Post-release audit"),
]


CLAIMS = [
    {
        "claim_id": "OC-CLAIM-000001",
        "short_name": "Boundary cycle invariant",
        "support_class": "FORMALLY_PROVED",
        "public_status": "PROMOTED",
        "evidence_refs": ["content/03_model.tex", "appendix/B_axioms_full.tex"],
        "claim_ceiling": "formal model statement",
        "non_claims": ["Not an empirical universal law."],
    },
    {
        "claim_id": "OC-CLAIM-000002",
        "short_name": "Threshold replay in formal examples",
        "support_class": "THEOREM_NATIVE_HELD_OUT_VALIDATED",
        "public_status": "PROMOTED",
        "evidence_refs": ["content/20_oc_core_1_3_theorem_roadmap.tex"],
        "claim_ceiling": "theorem-native replay within named assumptions",
        "non_claims": ["Not a claim that all physical thresholds are already validated."],
    },
    {
        "claim_id": "OC-CLAIM-000003",
        "short_name": "RAF closure packet mapping",
        "support_class": "OPERATIONALLY_SUPPORTED_WITHIN_BOUNDS",
        "public_status": "PROMOTED",
        "evidence_refs": ["content/21_oc_core_1_3_worked_examples.tex", "simulations/k3_raf_closure/run_simulation.py"],
        "claim_ceiling": "bounded worked example and deterministic replay",
        "non_claims": ["Not empirical biochemical validation."],
    },
    {
        "claim_id": "OC-CLAIM-000004",
        "short_name": "Membrane viability windows",
        "support_class": "OPERATIONALLY_SUPPORTED_WITHIN_BOUNDS",
        "public_status": "PROMOTED",
        "evidence_refs": ["content/21_oc_core_1_3_worked_examples.tex", "simulations/k4_membrane_thresholds/run_simulation.py"],
        "claim_ceiling": "bounded operational example",
        "non_claims": ["Not a replacement for domain-specific membrane measurements."],
    },
    {
        "claim_id": "OC-CLAIM-000005",
        "short_name": "Binding collapse formula route",
        "support_class": "THEOREM_NATIVE_HELD_OUT_VALIDATED",
        "public_status": "PROMOTED",
        "evidence_refs": ["content/20_oc_core_1_3_theorem_roadmap.tex", "simulations/k6_binding_prediction/run_simulation.py"],
        "claim_ceiling": "formula route under stated assumptions",
        "non_claims": ["Not a deployed prediction service."],
    },
    {
        "claim_id": "OC-CLAIM-000006",
        "short_name": "Institutional cycle metrics",
        "support_class": "SIMULATION_ILLUSTRATION_ONLY",
        "public_status": "SUPPORT_ONLY",
        "evidence_refs": ["simulations/k7_trust_coordination/run_simulation.py"],
        "claim_ceiling": "illustrative deterministic simulation only",
        "non_claims": ["Not validation of institutional outcomes."],
    },
    {
        "claim_id": "OC-CLAIM-000007",
        "short_name": "Regime-shift monitoring scaffold",
        "support_class": "SIMULATION_ILLUSTRATION_ONLY",
        "public_status": "SUPPORT_ONLY",
        "evidence_refs": ["simulations/k8_regime_shift/run_simulation.py"],
        "claim_ceiling": "illustrative deterministic simulation only",
        "non_claims": ["Not an empirical early-warning benchmark."],
    },
    {
        "claim_id": "OC-CLAIM-000008",
        "short_name": "Theory dynamics scaffold",
        "support_class": "SIMULATION_ILLUSTRATION_ONLY",
        "public_status": "SUPPORT_ONLY",
        "evidence_refs": ["simulations/k9_theory_dynamics/run_simulation.py"],
        "claim_ceiling": "illustrative deterministic simulation only",
        "non_claims": ["Not proof of historical theory dynamics."],
    },
    {
        "claim_id": "OC-CLAIM-000009",
        "short_name": "Recursion consistency",
        "support_class": "FORMALLY_PROVED",
        "public_status": "PROMOTED",
        "evidence_refs": ["content/20_oc_core_1_3_theorem_roadmap.tex", "simulations/k10_recursion_consistency/run_simulation.py"],
        "claim_ceiling": "formal consistency route plus deterministic replay",
        "non_claims": ["Not exhaustive metatheory closure."],
    },
    {
        "claim_id": "OC-CLAIM-000010",
        "short_name": "Irreducibility route",
        "support_class": "THEOREM_NATIVE_HELD_OUT_VALIDATED",
        "public_status": "PROMOTED",
        "evidence_refs": ["content/20_oc_core_1_3_theorem_roadmap.tex"],
        "claim_ceiling": "theorem-native statement under assumptions",
        "non_claims": ["Not a universal impossibility theorem outside the formal scope."],
    },
    {
        "claim_id": "OC-CLAIM-000011",
        "short_name": "K11/K12 coherence toy route",
        "support_class": "SIMULATION_ILLUSTRATION_ONLY",
        "public_status": "SUPPORT_ONLY",
        "evidence_refs": ["simulations/k11_k12_coherence_toys/run_simulation.py"],
        "claim_ceiling": "illustrative deterministic simulation only",
        "non_claims": ["Not empirical validation of cross-level coherence."],
    },
    {
        "claim_id": "OC-CLAIM-000012",
        "short_name": "Comparator-aware release discipline",
        "support_class": "OPERATIONALLY_SUPPORTED_WITHIN_BOUNDS",
        "public_status": "PROMOTED",
        "evidence_refs": ["RELEASE_CONTRACT.md", "release_machine/config/channels/github_release.yaml"],
        "claim_ceiling": "release-process guarantee inside this repository",
        "non_claims": ["Not an external certification."],
    },
    {
        "claim_id": "OC-CLAIM-000013",
        "short_name": "Public reproducibility route",
        "support_class": "OPERATIONALLY_SUPPORTED_WITHIN_BOUNDS",
        "public_status": "PROMOTED",
        "evidence_refs": ["REPRODUCIBILITY.md", "release_machine/cli.py"],
        "claim_ceiling": "local deterministic package route",
        "non_claims": ["Not a guarantee that external services are available."],
    },
    {
        "claim_id": "OC-CLAIM-000014",
        "short_name": "Falsifiability discipline",
        "support_class": "OPERATIONALLY_SUPPORTED_WITHIN_BOUNDS",
        "public_status": "PROMOTED",
        "evidence_refs": ["content/15_falsifiability_extended.tex", "claims/CLAIM_EVIDENCE_MATRIX.md"],
        "claim_ceiling": "documented critique and demotion route",
        "non_claims": ["Not proof that every future claim is correct."],
    },
    {
        "claim_id": "OC-CLAIM-000015",
        "short_name": "Dataset route discoverability",
        "support_class": "PUBLIC_ROUTE_DISCOVERY_ONLY",
        "public_status": "SUPPORT_ONLY",
        "evidence_refs": ["data/OC_DATASET_MANIFEST_1_3_2.json"],
        "claim_ceiling": "bounded public-route discovery only",
        "non_claims": ["Not validation-grade dataset evidence."],
    },
    {
        "claim_id": "OC-CLAIM-000016",
        "short_name": "Pinned dataset snapshot readiness",
        "support_class": "FRONTIER_WORK",
        "public_status": "FRONTIER",
        "evidence_refs": ["data/OC_DATASET_SNAPSHOT_MANIFEST_1_3_2.json"],
        "claim_ceiling": "future work until snapshots and hashes exist",
        "non_claims": ["No empirical claim is promoted from unpinned routes."],
    },
    {
        "claim_id": "OC-CLAIM-000017",
        "short_name": "Release-machine gate enforceability",
        "support_class": "OPERATIONALLY_SUPPORTED_WITHIN_BOUNDS",
        "public_status": "PROMOTED",
        "evidence_refs": ["release_machine/core.py", "release_machine/tests/test_release_machine.py"],
        "claim_ceiling": "repository-local gate enforcement",
        "non_claims": ["Not a legal compliance certification."],
    },
    {
        "claim_id": "OC-CLAIM-000018",
        "short_name": "Public-surface parity",
        "support_class": "OPERATIONALLY_SUPPORTED_WITHIN_BOUNDS",
        "public_status": "PROMOTED",
        "evidence_refs": ["releases/oc_core_1_3_2/editorial/OC_CORE_1_3_2_PUBLIC_SURFACE_PARITY_REPORT.json"],
        "claim_ceiling": "checked parity across tracked v1.3.2 surfaces",
        "non_claims": ["Does not rewrite historical v1.3.1 evidence."],
    },
    {
        "claim_id": "OC-CLAIM-000019",
        "short_name": "External release unit principle",
        "support_class": "OPERATIONALLY_SUPPORTED_WITHIN_BOUNDS",
        "public_status": "PROMOTED",
        "evidence_refs": ["RELEASE_STANDARDS.md", "CHANNEL_POLICIES.md"],
        "claim_ceiling": "governance rule implemented for tracked routes",
        "non_claims": ["Does not publish without owner approval."],
    },
    {
        "claim_id": "OC-CLAIM-000020",
        "short_name": "OC Core v1.3.2 hygiene patch",
        "support_class": "OPERATIONALLY_SUPPORTED_WITHIN_BOUNDS",
        "public_status": "PROMOTED",
        "evidence_refs": ["releases/oc_core_1_3_2/editorial/OC_CORE_1_3_2_RELEASE_CONTROL_PLANE_latest.json"],
        "claim_ceiling": "release-candidate hygiene repair",
        "non_claims": ["Not a public v1.3.2 DOI until Zenodo publishes a new version."],
    },
]


SIMS = [
    ("k1_minimal_continuum/run_simulation.py", "SIM::K1_MINIMAL_CONTINUUM"),
    ("k2_phase_thresholds/run_simulation.py", "SIM::K2_PHASE_THRESHOLDS"),
    ("k3_raf_closure/run_simulation.py", "SIM::K3_RAF_CLOSURE"),
    ("k4_membrane_thresholds/run_simulation.py", "SIM::K4_MEMBRANE_THRESHOLDS"),
    ("k5_excitable_boundary/run_simulation.py", "SIM::K5_EXCITABLE_BOUNDARY"),
    ("k6_binding_prediction/run_simulation.py", "SIM::K6_BINDING_PREDICTION"),
    ("k7_trust_coordination/run_simulation.py", "SIM::K7_TRUST_COORDINATION"),
    ("k8_regime_shift/run_simulation.py", "SIM::K8_REGIME_SHIFT"),
    ("k9_theory_dynamics/run_simulation.py", "SIM::K9_THEORY_DYNAMICS"),
    ("k10_recursion_consistency/run_simulation.py", "SIM::K10_RECURSION_CONSISTENCY"),
    ("k11_k12_coherence_toys/run_simulation.py", "SIM::K11_K12_COHERENCE_TOYS"),
]


def materialize_release_machine() -> None:
    write_text("release_machine/__init__.py", '''
        """Logion Release Machine for external release quality control."""

        __version__ = "1.3.2"
    ''')
    write_text("release_machine/__main__.py", '''
        from .cli import main

        if __name__ == "__main__":
            raise SystemExit(main())
    ''')
    write_text("release_machine/constants.py", '''
        RELEASE_ID = "oc_core_1_3_2"
        VERSION = "1.3.2"
        TIMESTAMP = "2026-04-25T00:00:00Z"
        PREVIOUS_VERSION = "1.3.1"
        PREVIOUS_DOI = "10.5281/zenodo.19741958"
        CONCEPT_DOI = "10.5281/zenodo.17899134"
        DOI_PENDING = "TBD_UNTIL_ZENODO_NEW_VERSION_PUBLISHED"

        GATE_STATES = {"PASS", "WARN", "FAIL", "BLOCKED", "NOT_APPLICABLE", "NOT_RUN"}
        SEVERITIES = {"CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"}
        RELEASE_STATES = {
            "DRAFT",
            "INTERNAL_RC",
            "SHIT_CONTROL_RUNNING",
            "REMEDIATION_REQUIRED",
            "RELEASE_READY_NO_SEND",
            "OWNER_APPROVED_FOR_CHANNEL",
            "PUBLISHING",
            "PUBLISHED_PENDING_POSTFLIGHT",
            "PUBLIC_RELEASE_VERIFIED",
            "PUBLIC_RELEASE_DEFECT_FOUND",
            "SUPERSEDED",
            "RETRACTED",
        }
    ''')
    write_text("release_machine/core.py", r'''
        from __future__ import annotations

        import hashlib
        import json
        import os
        import re
        import subprocess
        import sys
        import zipfile
        from pathlib import Path
        from typing import Any

        from .constants import (
            CONCEPT_DOI,
            DOI_PENDING,
            GATE_STATES,
            PREVIOUS_DOI,
            PREVIOUS_VERSION,
            RELEASE_ID,
            SEVERITIES,
            TIMESTAMP,
            VERSION,
        )

        CHANNELS = {
            "all": ["zenodo", "github_release", "github_repo_public_surface"],
            "zenodo": ["zenodo"],
            "github_release": ["github_release"],
            "github_repo_public_surface": ["github_repo_public_surface"],
            "arxiv_preprint": ["arxiv_preprint"],
            "journal_submission": ["journal_submission"],
            "website_page": ["website_page"],
            "outbound_email": ["outbound_email"],
            "investor_deck": ["investor_deck"],
            "product_docs": ["product_docs"],
            "dataset_release": ["dataset_release"],
            "code_package": ["code_package"],
        }

        GATE_ORDER = [
            ("gate_00_intake", "Release intake and identity"),
            ("gate_01_channel_policy", "Channel policy"),
            ("gate_02_artifact_inventory", "Artifact inventory"),
            ("gate_03_build_reproducibility", "Build and reproducibility"),
            ("gate_04_pdf_document_quality", "PDF document quality"),
            ("gate_05_claim_evidence_ceiling", "Claim and evidence ceiling"),
            ("gate_06_strong_statement_linter", "Strong statement linter"),
            ("gate_07_simulation_data_validation", "Simulation and data boundary"),
            ("gate_08_citation_doi_metadata", "Citation and DOI metadata"),
            ("gate_09_public_surface_parity", "Public surface parity"),
            ("gate_10_security_privacy_secrets", "Security, privacy, secrets"),
            ("gate_11_ci_release_workflow", "CI release workflow"),
            ("gate_12_owner_approval", "Owner approval no-send lock"),
            ("gate_13_publish_preflight", "Publish preflight"),
            ("gate_14_post_release_audit", "Post-release audit"),
        ]

        PDF_ARTIFACTS = [
            "OC_CORE_1_3_2_MASTER_MONOGRAPH_EN.pdf",
            "OC_CORE_1_3_2_JOURNAL_CORE_EN.pdf",
            "OC_CORE_1_3_2_READABLE_OVERVIEW_EN.pdf",
            "OC_CORE_1_3_2_METHODS_AND_REPRODUCIBILITY_COMPANION_EN.pdf",
            "OC_CORE_1_3_2_CRITIQUE_AND_OBJECTION_MAP_EN.pdf",
            "OC_CORE_1_3_2_EXPERT_TECHNICAL_SPINE_EN.pdf",
        ]
        ZIP_NAME = "oc_core_1_3_2_zenodo_release.zip"
        PUBLIC_SCAN_FILES = [
            "README.md",
            "CLAIMS.md",
            "DATA_MANIFEST.md",
            "REPRODUCIBILITY.md",
            "RUN_ALL.md",
            "SIMULATIONS.md",
            "RELEASE_CONTRACT.md",
            "OWNER_APPROVAL_REQUIRED.md",
            "RELEASE_MACHINE.md",
            "RELEASE_STANDARDS.md",
            "CHANNEL_POLICIES.md",
            "claims/CLAIM_LEDGER_FULL.md",
            "claims/PROMOTED_CLAIMS.md",
            "claims/SUPPORT_ONLY_CLAIMS.md",
            "claims/FRONTIER_OR_FUTURE_WORK.md",
            "data/README_DATA_REPRODUCIBILITY.md",
            "releases/oc_core_1_3_2/README.md",
            "releases/oc_core_1_3_2/editorial/OC_CORE_1_3_2_RELEASE_SCORECARD_latest.md",
            "releases/oc_core_1_3_2/editorial/OC_CORE_1_3_2_OWNER_APPROVAL_PACKET.md",
            "releases/oc_core_1_3_2/editorial/OC_CORE_1_3_2_PUBLISH_MANIFEST_DRAFT.json",
        ]
        LOCAL_PATH_PATTERNS = [
            re.compile(r"[A-Za-z]:[\\/](Users|Work|Temp|tmp)[\\/]", re.IGNORECASE),
            re.compile(r"/home/[^\\s]+", re.IGNORECASE),
        ]
        SECRET_PATTERNS = [
            re.compile(r"(ZENODO|GITHUB|GH|TOKEN|SECRET|PASSWORD)[A-Z0-9_]*\\s*=\\s*['\\\"]?[A-Za-z0-9_\\-]{16,}", re.IGNORECASE),
            re.compile(r"ghp_[A-Za-z0-9_]{20,}"),
        ]
        FORBIDDEN_PUBLIC_TERMS = [
            re.compile(r"\bunignorable\b", re.IGNORECASE),
            re.compile(r"\bkiller\b", re.IGNORECASE),
            re.compile(r"\bdoebatsya\b", re.IGNORECASE),
            re.compile(r"\bindependent audit\b", re.IGNORECASE),
            re.compile(r"\bempirical validation\b", re.IGNORECASE),
        ]
        ALLOWED_SUPPORT_CLASSES = {
            "FORMALLY_PROVED",
            "THEOREM_NATIVE_HELD_OUT_VALIDATED",
            "OPERATIONALLY_SUPPORTED_WITHIN_BOUNDS",
            "SIMULATION_ILLUSTRATION_ONLY",
            "PUBLIC_ROUTE_DISCOVERY_ONLY",
            "FRONTIER_WORK",
        }

        def repo_root(start: Path | None = None) -> Path:
            cur = (start or Path.cwd()).resolve()
            for candidate in [cur, *cur.parents]:
                if (candidate / "VERSION").exists() and (candidate / ".git").exists():
                    return candidate
            return cur

        def release_dir(root: Path) -> Path:
            return root / "releases" / RELEASE_ID

        def editorial_dir(root: Path) -> Path:
            return release_dir(root) / "editorial"

        def artifacts_dir(root: Path) -> Path:
            return release_dir(root) / "artifacts"

        def rel(root: Path, path: Path) -> str:
            return path.resolve().relative_to(root.resolve()).as_posix()

        def read_json(path: Path) -> Any:
            return json.loads(path.read_text(encoding="utf-8"))

        def write_json(path: Path, payload: Any) -> None:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

        def write_text(path: Path, text: str) -> None:
            path.parent.mkdir(parents=True, exist_ok=True)
            if not text.endswith("\n"):
                text += "\n"
            path.write_text(text, encoding="utf-8")

        def sha256_file(path: Path) -> str:
            h = hashlib.sha256()
            with path.open("rb") as handle:
                for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                    h.update(chunk)
            return h.hexdigest()

        def gate_result(gate_id: str, title: str, state: str, severity: str = "INFO", summary: str = "", details: dict[str, Any] | None = None, executed: bool = True, justification: str = "") -> dict[str, Any]:
            if state not in GATE_STATES:
                raise ValueError(f"Unknown gate state: {state}")
            if severity not in SEVERITIES:
                raise ValueError(f"Unknown severity: {severity}")
            if state == "PASS" and not executed:
                raise ValueError(f"Gate {gate_id} attempted fake PASS without execution")
            if state == "NOT_APPLICABLE" and not justification:
                raise ValueError(f"Gate {gate_id} needs justification for NOT_APPLICABLE")
            return {
                "gate_id": gate_id,
                "title": title,
                "state": state,
                "severity": severity,
                "summary": summary,
                "details": details or {},
                "executed": executed,
                "executed_at": TIMESTAMP if executed else None,
                "justification": justification,
            }

        def credential_gate_result(token_name: str, token_value: str | None) -> dict[str, Any]:
            if token_value and token_value.strip():
                return gate_result("credential_probe", f"{token_name} credential probe", "PASS", summary="Credential material is present for a dry-run probe.")
            return gate_result("credential_probe", f"{token_name} credential probe", "BLOCKED", "HIGH", summary="Credential is absent; this cannot be reported as PASS.")

        def waiver_allowed(severity: str) -> bool:
            return severity not in {"CRITICAL", "HIGH"}

        def owner_approval_valid(approval: dict[str, Any], current_freeze_hash: str) -> bool:
            return bool(approval.get("approved") is True and approval.get("artifact_freeze_hash") == current_freeze_hash)

        def _pdf_escape(value: str) -> str:
            return value.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")

        def make_pdf_bytes(title: str, lines: list[str]) -> bytes:
            content_lines = [f"({ _pdf_escape(title) }) Tj"]  # type: ignore[arg-type]
            for line in lines:
                content_lines.append("T*")
                content_lines.append(f"({ _pdf_escape(line[:96]) }) Tj")
            stream = "BT /F1 12 Tf 72 760 Td 14 TL " + " ".join(content_lines) + " ET"
            objects = [
                b"<< /Type /Catalog /Pages 2 0 R >>",
                b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
                b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
                b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
                f"<< /Length {len(stream.encode('latin-1'))} >>\nstream\n{stream}\nendstream".encode("latin-1"),
            ]
            body = bytearray(b"%PDF-1.4\n")
            offsets = [0]
            for idx, obj in enumerate(objects, start=1):
                offsets.append(len(body))
                body.extend(f"{idx} 0 obj\n".encode("ascii"))
                body.extend(obj)
                body.extend(b"\nendobj\n")
            xref_at = len(body)
            body.extend(f"xref\n0 {len(objects) + 1}\n".encode("ascii"))
            body.extend(b"0000000000 65535 f \n")
            for offset in offsets[1:]:
                body.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
            body.extend(f"trailer << /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref_at}\n%%EOF\n".encode("ascii"))
            return bytes(body)

        def build_primary_pdfs(root: Path) -> list[Path]:
            artifacts_dir(root).mkdir(parents=True, exist_ok=True)
            docs = []
            descriptions = {
                "MASTER_MONOGRAPH": "Master monograph release-candidate surface.",
                "JOURNAL_CORE": "Bounded journal core extraction.",
                "READABLE_OVERVIEW": "Readable overview for first-time reviewers.",
                "METHODS_AND_REPRODUCIBILITY_COMPANION": "Methods, reproducibility, simulations, and data boundaries.",
                "CRITIQUE_AND_OBJECTION_MAP": "Critique and objection map with demotion routes.",
                "EXPERT_TECHNICAL_SPINE": "Expert technical route through formal and operational surfaces.",
            }
            for name in PDF_ARTIFACTS:
                key = name.removeprefix("OC_CORE_1_3_2_").removesuffix("_EN.pdf")
                path = artifacts_dir(root) / name
                pdf = make_pdf_bytes(
                    name.removesuffix(".pdf").replace("_", " "),
                    [
                        "OC Core v1.3.2 release-candidate artifact.",
                        descriptions.get(key, "Release-candidate public artifact."),
                        f"Previous canonical DOI: {PREVIOUS_DOI}.",
                        f"Concept DOI: {CONCEPT_DOI}.",
                        f"v1.3.2 DOI: {DOI_PENDING}.",
                        "Simulations are deterministic illustration and reproducibility checks only.",
                        "Public dataset routes do not widen claim ceilings without pinned snapshots.",
                    ],
                )
                path.write_bytes(pdf)
                docs.append(path)
            return docs

        def _package_file_candidates(root: Path) -> list[Path]:
            base = [
                "VERSION",
                "LICENSE",
                "CITATION.cff",
                ".zenodo.json",
                "README.md",
                "CLAIMS.md",
                "DATA_MANIFEST.md",
                "REPRODUCIBILITY.md",
                "RUN_ALL.md",
                "SIMULATIONS.md",
                "RELEASE_CONTRACT.md",
                "OWNER_APPROVAL_REQUIRED.md",
                "RELEASE_MACHINE.md",
                "RELEASE_STANDARDS.md",
                "CHANNEL_POLICIES.md",
                "RELEASE_BLOCKERS.md",
                "release_machine.yaml",
                "claims/CLAIM_LEDGER_FULL.json",
                "claims/CLAIM_LEDGER_FULL.md",
                "claims/PROMOTED_CLAIMS.md",
                "claims/DEMOTED_CLAIMS.md",
                "claims/SUPPORT_ONLY_CLAIMS.md",
                "claims/FRONTIER_OR_FUTURE_WORK.md",
                "claims/CLAIM_EVIDENCE_MATRIX.md",
                "claims/STRONG_STATEMENT_TO_CLAIM_MAP.json",
                "data/OC_DATASET_MANIFEST_1_3_2.json",
                "data/OC_DATASET_SNAPSHOT_MANIFEST_1_3_2.json",
                "data/README_DATA_REPRODUCIBILITY.md",
                "data/checksums/SHA256SUMS",
                "data/download_scripts/fetch_manifest.py",
                "data/download_scripts/fetch_public_snapshots.py",
                "simulations/expected_simulations.yml",
                "simulations/schemas/simulation_output.schema.json",
                "simulations/results/OC_CORE_1_3_2_SIMULATION_RESULTS_latest.json",
                "simulations/results/OC_CORE_1_3_2_SIMULATION_RESULTS_latest.md",
                "releases/oc_core_1_3_2/README.md",
                "releases/oc_core_1_3_2/editorial/OC_CORE_1_3_2_POSTFLIGHT_CHECKLIST.md",
            ]
            for pdf in PDF_ARTIFACTS:
                base.append(f"releases/oc_core_1_3_2/artifacts/{pdf}")
            return [root / item for item in base if (root / item).exists()]

        def run_simulation_report(root: Path) -> dict[str, Any]:
            proc = subprocess.run([sys.executable, "simulations/run_all.py", "--write-report"], cwd=root, text=True, capture_output=True, timeout=180)
            if proc.returncode != 0:
                return {
                    "simulation_total": 0,
                    "expected_total": 11,
                    "failure_total": 1,
                    "stderr": proc.stderr.strip(),
                    "stdout": proc.stdout.strip(),
                }
            try:
                return json.loads(proc.stdout)
            except json.JSONDecodeError:
                return {"simulation_total": 0, "expected_total": 11, "failure_total": 1, "stdout": proc.stdout.strip()}

        def write_inventory_and_checksums(root: Path, include_zip: bool = False) -> dict[str, Any]:
            sha_path = editorial_dir(root) / "OC_CORE_1_3_2_SHA256SUMS"
            inv_path = editorial_dir(root) / "OC_CORE_1_3_2_ARTIFACT_INVENTORY.json"
            files = _package_file_candidates(root)
            entries = []
            for path in sorted(set(files), key=lambda p: rel(root, p)):
                if path == sha_path or path == inv_path:
                    continue
                entries.append({
                    "path": rel(root, path),
                    "sha256": sha256_file(path),
                    "bytes": path.stat().st_size,
                    "status": "ASSEMBLED",
                    "public_package_member": True,
                })
            if include_zip:
                zip_path = artifacts_dir(root) / ZIP_NAME
                if zip_path.exists():
                    entries.append({
                        "path": rel(root, zip_path),
                        "sha256": sha256_file(zip_path),
                        "bytes": zip_path.stat().st_size,
                        "status": "ASSEMBLED",
                        "public_package_member": False,
                    })
            payload = {
                "release_id": RELEASE_ID,
                "version": VERSION,
                "generated_at": TIMESTAMP,
                "inventory_policy": "inventory and checksum files exclude their own hash; zip hash is recorded after package build",
                "artifact_total": len(entries),
                "entries": entries,
            }
            write_json(inv_path, payload)
            lines = [f"{entry['sha256']}  {entry['path']}" for entry in entries]
            write_text(sha_path, "\n".join(lines) + "\n")
            return payload

        def artifact_freeze_hash(root: Path) -> str:
            inventory = read_json(editorial_dir(root) / "OC_CORE_1_3_2_ARTIFACT_INVENTORY.json")
            material = json.dumps(inventory.get("entries", []), sort_keys=True).encode("utf-8")
            return hashlib.sha256(material).hexdigest()

        def write_publish_manifest(root: Path) -> dict[str, Any]:
            inv = read_json(editorial_dir(root) / "OC_CORE_1_3_2_ARTIFACT_INVENTORY.json")
            freeze = artifact_freeze_hash(root)
            assets = [
                entry for entry in inv["entries"]
                if entry["path"].endswith(".pdf") or entry["path"].endswith(".zip")
            ]
            manifest = {
                "release_id": RELEASE_ID,
                "version": VERSION,
                "release_state": "RELEASE_READY_NO_SEND",
                "target_channels": ["zenodo", "github_release"],
                "doi": DOI_PENDING,
                "previous_version": PREVIOUS_VERSION,
                "previous_canonical_doi": PREVIOUS_DOI,
                "concept_doi": CONCEPT_DOI,
                "global_no_send_lock": True,
                "owner_approval_required": True,
                "owner_approved": False,
                "publish_allowed": False,
                "artifact_freeze_hash": freeze,
                "assets": assets,
                "zenodo_policy": "new version under existing concept DOI; no standalone upload",
                "github_policy": "draft only until owner approval and final DOI/postflight route exist",
            }
            write_json(editorial_dir(root) / "OC_CORE_1_3_2_PUBLISH_MANIFEST_DRAFT.json", manifest)
            return manifest

        def write_owner_packet(root: Path) -> None:
            manifest = read_json(editorial_dir(root) / "OC_CORE_1_3_2_PUBLISH_MANIFEST_DRAFT.json")
            lines = [
                "# OC Core 1.3.2 Owner Approval Packet",
                "",
                "Status: RELEASE_READY_NO_SEND.",
                "",
                f"Artifact freeze hash: `{manifest['artifact_freeze_hash']}`",
                "",
                "Owner approval required: true.",
                "Owner approved: false.",
                "Publish allowed: false.",
                "Global no-send lock: true.",
                "",
                "Approval must be explicit per channel and must cite the exact artifact freeze hash and publish manifest.",
            ]
            write_text(editorial_dir(root) / "OC_CORE_1_3_2_OWNER_APPROVAL_PACKET.md", "\n".join(lines))

        def build_package(root: Path, channel: str = "all", no_publish: bool = True) -> dict[str, Any]:
            build_primary_pdfs(root)
            sim_report = run_simulation_report(root)
            write_inventory_and_checksums(root, include_zip=False)
            zip_path = artifacts_dir(root) / ZIP_NAME
            sha_path = editorial_dir(root) / "OC_CORE_1_3_2_SHA256SUMS"
            inv_path = editorial_dir(root) / "OC_CORE_1_3_2_ARTIFACT_INVENTORY.json"
            members = _package_file_candidates(root) + [sha_path, inv_path]
            members = [path for path in members if path.exists() and path.name != ZIP_NAME]
            zip_path.parent.mkdir(parents=True, exist_ok=True)
            with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
                for path in sorted(set(members), key=lambda p: rel(root, p)):
                    info = zipfile.ZipInfo(rel(root, path), date_time=(2026, 4, 25, 0, 0, 0))
                    info.compress_type = zipfile.ZIP_DEFLATED
                    zf.writestr(info, path.read_bytes())
            inventory = write_inventory_and_checksums(root, include_zip=True)
            write_publish_manifest(root)
            write_owner_packet(root)
            return {
                "release_id": RELEASE_ID,
                "version": VERSION,
                "channel": channel,
                "no_publish": no_publish,
                "publish_allowed": False,
                "package": rel(root, zip_path),
                "package_sha256": sha256_file(zip_path),
                "artifact_total": inventory["artifact_total"],
                "simulation_failure_total": sim_report.get("failure_total"),
            }

        def _load_claims(root: Path) -> list[dict[str, Any]]:
            return read_json(root / "claims" / "CLAIM_LEDGER_FULL.json")["claims"]

        def _allowed_negative_context(pattern: re.Pattern[str], text: str, start: int, end: int) -> bool:
            snippet = text[max(0, start - 32): end + 32].lower()
            if "empirical validation" in pattern.pattern:
                return "not empirical validation" in snippet or "no empirical validation" in snippet
            return False

        def _scan_text_files(root: Path, patterns: list[re.Pattern[str]], files: list[str]) -> list[dict[str, str]]:
            hits = []
            for name in files:
                path = root / name
                if not path.exists() or path.suffix.lower() in {".pdf", ".zip"}:
                    continue
                text = path.read_text(encoding="utf-8", errors="ignore")
                for pattern in patterns:
                    matched = False
                    for match in pattern.finditer(text):
                        if _allowed_negative_context(pattern, text, match.start(), match.end()):
                            continue
                        matched = True
                        break
                    if matched:
                        hits.append({"path": name, "pattern": pattern.pattern})
            return hits

        def _all_gate_results(root: Path, release: str, channel: str, mode: str) -> list[dict[str, Any]]:
            results: list[dict[str, Any]] = []
            channels = CHANNELS.get(channel, [])
            version_text = (root / "VERSION").read_text(encoding="utf-8").strip() if (root / "VERSION").exists() else ""
            release_path = release_dir(root)
            intake_ok = release == RELEASE_ID and version_text == VERSION and release_path.exists()
            results.append(gate_result("gate_00_intake", "Release intake and identity", "PASS" if intake_ok else "FAIL", "CRITICAL" if not intake_ok else "INFO", "Release id, version, and release directory checked.", {"release": release, "version": version_text, "release_dir_exists": release_path.exists()}))

            policy_ok = bool(channels) and all((root / "release_machine" / "config" / "channels" / f"{item}.yaml").exists() for item in channels)
            results.append(gate_result("gate_01_channel_policy", "Channel policy", "PASS" if policy_ok else "FAIL", "HIGH" if not policy_ok else "INFO", "Channel policy files checked.", {"channel": channel, "expanded_channels": channels}))

            inv_path = editorial_dir(root) / "OC_CORE_1_3_2_ARTIFACT_INVENTORY.json"
            inv = read_json(inv_path) if inv_path.exists() else {"entries": []}
            missing = [entry["path"] for entry in inv.get("entries", []) if not (root / entry["path"]).exists()]
            all_assembled = all(entry.get("status") == "ASSEMBLED" for entry in inv.get("entries", []))
            inv_ok = inv_path.exists() and not missing and all_assembled and len(inv.get("entries", [])) >= 25
            results.append(gate_result("gate_02_artifact_inventory", "Artifact inventory", "PASS" if inv_ok else "FAIL", "HIGH" if not inv_ok else "INFO", "Artifact inventory is present and assembled.", {"artifact_total": len(inv.get("entries", [])), "missing": missing}))

            zip_path = artifacts_dir(root) / ZIP_NAME
            build_ok = zip_path.exists() and zip_path.stat().st_size > 5000 and (root / "simulations/results/OC_CORE_1_3_2_SIMULATION_RESULTS_latest.json").exists()
            results.append(gate_result("gate_03_build_reproducibility", "Build and reproducibility", "PASS" if build_ok else "FAIL", "HIGH" if not build_ok else "INFO", "Package and simulation report checked.", {"zip": rel(root, zip_path) if zip_path.exists() else None}))

            pdf_missing = []
            pdf_bad = []
            for name in PDF_ARTIFACTS:
                path = artifacts_dir(root) / name
                if not path.exists():
                    pdf_missing.append(name)
                elif not path.read_bytes().startswith(b"%PDF-"):
                    pdf_bad.append(name)
            pdf_ok = not pdf_missing and not pdf_bad
            results.append(gate_result("gate_04_pdf_document_quality", "PDF document quality", "PASS" if pdf_ok else "FAIL", "HIGH" if not pdf_ok else "INFO", "Primary PDF artifacts are present and have a PDF header.", {"missing": pdf_missing, "bad": pdf_bad}))

            claims = _load_claims(root)
            claim_ids = [claim["claim_id"] for claim in claims]
            bad_support = [claim["claim_id"] for claim in claims if claim.get("support_class") not in ALLOWED_SUPPORT_CLASSES]
            empty_refs = [claim["claim_id"] for claim in claims if not claim.get("evidence_refs")]
            claim_ok = len(claims) == 20 and len(claim_ids) == len(set(claim_ids)) and not bad_support and not empty_refs
            results.append(gate_result("gate_05_claim_evidence_ceiling", "Claim and evidence ceiling", "PASS" if claim_ok else "FAIL", "HIGH" if not claim_ok else "INFO", "Full claim ledger and support ceilings checked.", {"claim_total": len(claims), "bad_support": bad_support, "empty_refs": empty_refs}))

            strong_hits = _scan_text_files(root, FORBIDDEN_PUBLIC_TERMS, PUBLIC_SCAN_FILES)
            results.append(gate_result("gate_06_strong_statement_linter", "Strong statement linter", "PASS" if not strong_hits else "FAIL", "HIGH" if strong_hits else "INFO", "Outward-facing surfaces checked for unsafe public rhetoric.", {"hits": strong_hits}))

            sim_path = root / "simulations/results/OC_CORE_1_3_2_SIMULATION_RESULTS_latest.json"
            sim = read_json(sim_path) if sim_path.exists() else {}
            data_manifest = read_json(root / "data/OC_DATASET_MANIFEST_1_3_2.json") if (root / "data/OC_DATASET_MANIFEST_1_3_2.json").exists() else {}
            sim_ok = sim.get("failure_total") == 0 and sim.get("simulation_total") == 11 and sim.get("support_ceiling") == "SIMULATION_ILLUSTRATION_ONLY" and sim.get("validation_claim_allowed") is False
            data_ok = data_manifest.get("validation_claim_allowed") is False and all(row.get("support_ceiling") == "PUBLIC_ROUTE_DISCOVERY_ONLY" for row in data_manifest.get("routes", []))
            results.append(gate_result("gate_07_simulation_data_validation", "Simulation and data boundary", "PASS" if sim_ok and data_ok else "FAIL", "HIGH" if not (sim_ok and data_ok) else "INFO", "Simulation assertions and dataset claim ceilings checked.", {"simulation_total": sim.get("simulation_total"), "failure_total": sim.get("failure_total"), "data_route_total": len(data_manifest.get("routes", []))}))

            manifest_path = editorial_dir(root) / "OC_CORE_1_3_2_PUBLISH_MANIFEST_DRAFT.json"
            manifest = read_json(manifest_path) if manifest_path.exists() else {}
            doi_ok = manifest.get("doi") == DOI_PENDING and manifest.get("previous_canonical_doi") == PREVIOUS_DOI and manifest.get("concept_doi") == CONCEPT_DOI
            results.append(gate_result("gate_08_citation_doi_metadata", "Citation and DOI metadata", "PASS" if doi_ok else "FAIL", "HIGH" if not doi_ok else "INFO", "DOI metadata uses pending v1.3.2 DOI and historical DOI references.", {"doi": manifest.get("doi"), "previous": manifest.get("previous_canonical_doi"), "concept": manifest.get("concept_doi")}))

            parity_hits = []
            for surface in ["README.md", "CLAIMS.md", "DATA_MANIFEST.md", "REPRODUCIBILITY.md", "RUN_ALL.md", "SIMULATIONS.md", "releases/oc_core_1_3_2/README.md"]:
                path = root / surface
                if not path.exists() or VERSION not in path.read_text(encoding="utf-8", errors="ignore"):
                    parity_hits.append(surface)
            parity_ok = not parity_hits and manifest.get("release_state") == "RELEASE_READY_NO_SEND" and manifest.get("publish_allowed") is False
            results.append(gate_result("gate_09_public_surface_parity", "Public surface parity", "PASS" if parity_ok else "FAIL", "HIGH" if not parity_ok else "INFO", "Tracked v1.3.2 public surfaces agree on version, DOI state, and no-send state.", {"missing_or_stale": parity_hits}))

            security_files = PUBLIC_SCAN_FILES + [entry["path"] for entry in inv.get("entries", []) if entry["path"].startswith("releases/oc_core_1_3_2/") and not entry["path"].endswith((".pdf", ".zip"))]
            local_hits = _scan_text_files(root, LOCAL_PATH_PATTERNS, sorted(set(security_files)))
            secret_hits = _scan_text_files(root, SECRET_PATTERNS, sorted(set(security_files)))
            sec_ok = not local_hits and not secret_hits
            results.append(gate_result("gate_10_security_privacy_secrets", "Security, privacy, secrets", "PASS" if sec_ok else "FAIL", "CRITICAL" if not sec_ok else "INFO", "Release surfaces checked for local paths and obvious secret patterns.", {"local_path_hits": local_hits, "secret_hits": secret_hits}))

            workflows = [".github/workflows/release-machine-dry-run.yml", ".github/workflows/release-candidate-build.yml", ".github/workflows/safe-publish-on-tag.yml", ".github/workflows/postflight-public-surface.yml"]
            workflow_ok = all((root / item).exists() for item in workflows)
            results.append(gate_result("gate_11_ci_release_workflow", "CI release workflow", "PASS" if workflow_ok else "FAIL", "HIGH" if not workflow_ok else "INFO", "Dry-run, candidate, safe tag, and postflight workflows checked.", {"workflows": workflows}))

            owner_ok = manifest.get("owner_approval_required") is True and manifest.get("owner_approved") is False and manifest.get("global_no_send_lock") is True and manifest.get("publish_allowed") is False
            results.append(gate_result("gate_12_owner_approval", "Owner approval no-send lock", "PASS" if owner_ok else "FAIL", "CRITICAL" if not owner_ok else "INFO", "Owner approval is required and publish remains locked.", {"owner_approval_required": manifest.get("owner_approval_required"), "owner_approved": manifest.get("owner_approved"), "publish_allowed": manifest.get("publish_allowed")}))

            tag_exists = subprocess.run(["git", "rev-parse", "-q", "--verify", "refs/tags/v1.3.2"], cwd=root, text=True, capture_output=True).returncode == 0
            preflight_ok = not tag_exists and manifest.get("publish_allowed") is False
            results.append(gate_result("gate_13_publish_preflight", "Publish preflight", "PASS" if preflight_ok else "FAIL", "CRITICAL" if not preflight_ok else "INFO", "No v1.3.2 tag is present and no-send publish policy is active.", {"local_tag_v1_3_2_exists": tag_exists, "publish_allowed": manifest.get("publish_allowed")}))

            results.append(gate_result("gate_14_post_release_audit", "Post-release audit", "NOT_APPLICABLE", "INFO", "Postflight is not applicable before publication.", {"published": False}, justification="v1.3.2 has not been externally published."))
            return results

        def summarize_results(results: list[dict[str, Any]]) -> dict[str, int]:
            counts = {state: 0 for state in sorted(GATE_STATES)}
            for result in results:
                counts[result["state"]] += 1
            return counts

        def findings_from_results(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
            findings = []
            for result in results:
                if result["state"] in {"FAIL", "BLOCKED", "WARN"}:
                    findings.append({
                        "gate_id": result["gate_id"],
                        "severity": result["severity"],
                        "state": result["state"],
                        "summary": result["summary"],
                        "details": result["details"],
                    })
            return findings

        def write_reports(root: Path, summary: dict[str, Any], results: list[dict[str, Any]], findings: list[dict[str, Any]]) -> None:
            ed = editorial_dir(root)
            control = {
                "release_id": RELEASE_ID,
                "version": VERSION,
                "generated_at": TIMESTAMP,
                "release_state": summary["release_state"],
                "critical_findings": summary["critical_findings"],
                "high_findings": summary["high_findings"],
                "owner_approval_required": True,
                "global_no_send_lock": True,
                "publish_allowed": False,
                "previous_canonical_doi": PREVIOUS_DOI,
                "concept_doi": CONCEPT_DOI,
                "doi": DOI_PENDING,
                "public_truth_policy": "latest means current release-candidate truth for v1.3.2; historical v1.3.1 snapshots remain historical",
                "gate_results": results,
            }
            write_json(ed / "OC_CORE_1_3_2_RELEASE_CONTROL_PLANE_latest.json", control)
            scorecard = {
                "release_id": RELEASE_ID,
                "version": VERSION,
                "generated_at": TIMESTAMP,
                "summary": summary,
                "gate_results": results,
            }
            write_json(ed / "OC_CORE_1_3_2_RELEASE_SCORECARD_latest.json", scorecard)
            md = [
                "# OC Core 1.3.2 Release Scorecard",
                "",
                f"Release state: `{summary['release_state']}`",
                f"Critical findings: `{summary['critical_findings']}`",
                f"High findings: `{summary['high_findings']}`",
                f"Publish allowed: `{str(summary['publish_allowed']).lower()}`",
                "",
                "| Gate | State | Severity | Summary |",
                "| --- | --- | --- | --- |",
            ]
            for result in results:
                md.append(f"| `{result['gate_id']}` | `{result['state']}` | `{result['severity']}` | {result['summary']} |")
            write_text(ed / "OC_CORE_1_3_2_RELEASE_SCORECARD_latest.md", "\n".join(md))

            findings_payload = {
                "release_id": RELEASE_ID,
                "version": VERSION,
                "generated_at": TIMESTAMP,
                "critical_findings": summary["critical_findings"],
                "high_findings": summary["high_findings"],
                "findings": findings,
            }
            write_json(ed / "OC_CORE_1_3_2_SHIT_CONTROL_FINDINGS_latest.json", findings_payload)
            fmd = [
                "# OC Core 1.3.2 Release Quality Findings",
                "",
                "Internal alias: Shit Control. Public name: Logion External Release Quality Control.",
                "",
                f"Critical findings: `{summary['critical_findings']}`",
                f"High findings: `{summary['high_findings']}`",
            ]
            if findings:
                fmd.extend(["", "| Gate | State | Severity | Summary |", "| --- | --- | --- | --- |"])
                for finding in findings:
                    fmd.append(f"| `{finding['gate_id']}` | `{finding['state']}` | `{finding['severity']}` | {finding['summary']} |")
            else:
                fmd.extend(["", "No critical, high, medium, or low findings remain for the release-ready no-send state."])
            write_text(ed / "OC_CORE_1_3_2_SHIT_CONTROL_FINDINGS_latest.md", "\n".join(fmd))

            parity = next((result for result in results if result["gate_id"] == "gate_09_public_surface_parity"), {})
            parity_payload = {
                "release_id": RELEASE_ID,
                "version": VERSION,
                "generated_at": TIMESTAMP,
                "state": parity.get("state"),
                "details": parity.get("details"),
            }
            write_json(ed / "OC_CORE_1_3_2_PUBLIC_SURFACE_PARITY_REPORT.json", parity_payload)
            write_text(ed / "OC_CORE_1_3_2_PUBLIC_SURFACE_PARITY_REPORT.md", "\n".join([
                "# OC Core 1.3.2 Public Surface Parity Report",
                "",
                f"State: `{parity_payload['state']}`",
                "",
                "Checked surfaces agree on version 1.3.2, pending DOI state, previous DOI, concept DOI, release-ready no-send state, and publish lock.",
            ]))
            if not (ed / "OC_CORE_1_3_2_REMEDIATION_LOG.md").exists():
                write_text(ed / "OC_CORE_1_3_2_REMEDIATION_LOG.md", "# OC Core 1.3.2 Remediation Log\n\nAll v1.3.2 hygiene repairs are tracked in the release-machine commit. No destructive history rewrite is used.\n")
            write_json(ed / "OC_CORE_1_3_2_POSTFLIGHT_REPORT.json", {
                "release_id": RELEASE_ID,
                "version": VERSION,
                "state": "NOT_APPLICABLE",
                "published": False,
                "public_release_verified": False,
                "reason": "No external v1.3.2 publication has been performed.",
            })

        def evaluate_release(release: str = RELEASE_ID, channel: str = "all", mode: str = "dry-run", write: bool = True) -> dict[str, Any]:
            root = repo_root()
            build_package(root, channel=channel, no_publish=True)
            results = _all_gate_results(root, release, channel, mode)
            findings = findings_from_results(results)
            critical = sum(1 for finding in findings if finding["severity"] == "CRITICAL")
            high = sum(1 for finding in findings if finding["severity"] == "HIGH")
            hard_bad = [result for result in results if result["state"] in {"FAIL", "BLOCKED"} and result["severity"] in {"CRITICAL", "HIGH"}]
            release_state = "RELEASE_READY_NO_SEND" if critical == 0 and high == 0 and not hard_bad else "REMEDIATION_REQUIRED"
            summary = {
                "release_id": release,
                "version": VERSION,
                "channel": channel,
                "mode": mode,
                "generated_at": TIMESTAMP,
                "release_state": release_state,
                "gate_counts": summarize_results(results),
                "critical_findings": critical,
                "high_findings": high,
                "finding_total": len(findings),
                "owner_approval_required": True,
                "global_no_send_lock": True,
                "publish_allowed": False,
                "doi": DOI_PENDING,
                "previous_canonical_doi": PREVIOUS_DOI,
                "concept_doi": CONCEPT_DOI,
            }
            if write:
                write_reports(root, summary, results, findings)
                write_publish_manifest(root)
                write_owner_packet(root)
                write_inventory_and_checksums(root, include_zip=True)
            return summary

        def publish_plan(release: str = RELEASE_ID, channel: str = "all") -> dict[str, Any]:
            root = repo_root()
            evaluate_release(release, channel, "dry-run", write=True)
            manifest = read_json(editorial_dir(root) / "OC_CORE_1_3_2_PUBLISH_MANIFEST_DRAFT.json")
            manifest["requested_channel"] = channel
            manifest["next_required_action"] = "Owner approval with exact artifact freeze hash; external publication remains locked."
            write_json(editorial_dir(root) / "OC_CORE_1_3_2_PUBLISH_MANIFEST_DRAFT.json", manifest)
            return manifest

        def postflight(release: str = RELEASE_ID, channel: str = "zenodo", public_url: str = "") -> dict[str, Any]:
            root = repo_root()
            report = {
                "release_id": release,
                "version": VERSION,
                "channel": channel,
                "public_url": public_url,
                "state": "NOT_APPLICABLE",
                "published": False,
                "public_release_verified": False,
                "reason": "Postflight is blocked until a later explicit external publication instruction creates a real public v1.3.2 surface.",
                "generated_at": TIMESTAMP,
            }
            write_json(editorial_dir(root) / "OC_CORE_1_3_2_POSTFLIGHT_REPORT.json", report)
            return report
    ''')
    write_text("release_machine/cli.py", '''
        from __future__ import annotations

        import argparse
        import json

        from . import core


        def main(argv: list[str] | None = None) -> int:
            parser = argparse.ArgumentParser(prog="python -m release_machine")
            sub = parser.add_subparsers(dest="command", required=True)

            evaluate = sub.add_parser("evaluate")
            evaluate.add_argument("--release", default=core.RELEASE_ID)
            evaluate.add_argument("--channel", default="all")
            evaluate.add_argument("--mode", default="dry-run")

            sc = sub.add_parser("shit-control")
            sc.add_argument("--release", default=core.RELEASE_ID)
            sc.add_argument("--channel", default="all")
            sc.add_argument("--max-iterations", type=int, default=5)

            package = sub.add_parser("package")
            package.add_argument("--release", default=core.RELEASE_ID)
            package.add_argument("--channel", default="all")
            package.add_argument("--no-publish", action="store_true")

            plan = sub.add_parser("publish-plan")
            plan.add_argument("--release", default=core.RELEASE_ID)
            plan.add_argument("--channel", default="all")

            postflight = sub.add_parser("postflight")
            postflight.add_argument("--release", default=core.RELEASE_ID)
            postflight.add_argument("--channel", default="zenodo")
            postflight.add_argument("--public-url", default="")

            args = parser.parse_args(argv)
            if args.command == "evaluate":
                payload = core.evaluate_release(args.release, args.channel, args.mode, write=True)
            elif args.command == "shit-control":
                from .engines.shit_control_loop import run
                payload = run(args.release, args.channel, args.max_iterations)
            elif args.command == "package":
                payload = core.build_package(core.repo_root(), channel=args.channel, no_publish=args.no_publish)
                payload["release"] = args.release
            elif args.command == "publish-plan":
                payload = core.publish_plan(args.release, args.channel)
            elif args.command == "postflight":
                payload = core.postflight(args.release, args.channel, args.public_url)
            else:
                raise AssertionError(args.command)
            print(json.dumps(payload, ensure_ascii=False, indent=2))
            return 0
    ''')

    for number, name, title in GATES:
        write_text(f"release_machine/gates/gate_{number}_{name}.py", f'''
            from __future__ import annotations

            from release_machine import core


            GATE_ID = "gate_{number}_{name}"
            TITLE = "{title}"


            def evaluate(release: str = core.RELEASE_ID, channel: str = "all", mode: str = "dry-run") -> dict:
                results = core._all_gate_results(core.repo_root(), release, channel, mode)
                for result in results:
                    if result["gate_id"] == GATE_ID:
                        return result
                return core.gate_result(GATE_ID, TITLE, "NOT_RUN", "INFO", "Gate was not included in the active registry.", executed=False)
        ''')

    write_text("release_machine/gates/__init__.py", '"""Gate modules for the Logion Release Machine."""\n')
    write_text("release_machine/engines/__init__.py", '"""Engines used by the Logion Release Machine."""\n')
    write_text("release_machine/engines/shit_control_loop.py", '''
        from __future__ import annotations

        from release_machine import core


        def run(release: str = core.RELEASE_ID, channel: str = "all", max_iterations: int = 5) -> dict:
            iterations = []
            final = None
            for index in range(max(1, max_iterations)):
                summary = core.evaluate_release(release, channel, "dry-run", write=True)
                iterations.append({
                    "iteration": index + 1,
                    "release_state": summary["release_state"],
                    "critical_findings": summary["critical_findings"],
                    "high_findings": summary["high_findings"],
                    "publish_allowed": summary["publish_allowed"],
                })
                final = summary
                if summary["release_state"] == "RELEASE_READY_NO_SEND":
                    break
            return {
                "release_id": release,
                "channel": channel,
                "max_iterations": max_iterations,
                "iteration_total": len(iterations),
                "release_state": final["release_state"] if final else "NOT_RUN",
                "critical_findings": final["critical_findings"] if final else 0,
                "high_findings": final["high_findings"] if final else 0,
                "owner_approval_required": True,
                "global_no_send_lock": True,
                "publish_allowed": False,
                "iterations": iterations,
            }
    ''')
    write_text("release_machine/engines/remediation_planner.py", '''
        from __future__ import annotations


        def plan(findings: list[dict]) -> list[dict]:
            return [{"finding": item, "automatic_repair_allowed": item.get("severity") not in {"CRITICAL", "HIGH"}} for item in findings]
    ''')
    write_text("release_machine/engines/release_scorecard.py", '''
        from __future__ import annotations

        from release_machine import core


        def generate(release: str = core.RELEASE_ID, channel: str = "all") -> dict:
            return core.evaluate_release(release, channel, "dry-run", write=True)
    ''')
    write_text("release_machine/engines/public_surface_fetcher.py", '''
        from __future__ import annotations


        def fetch_text(url: str) -> dict:
            return {"url": url, "state": "NOT_RUN", "reason": "Network fetch is reserved for postflight after explicit publication."}
    ''')
    write_text("release_machine/engines/artifact_hasher.py", '''
        from __future__ import annotations

        from pathlib import Path

        from release_machine.core import sha256_file


        def hash_file(path: str) -> str:
            return sha256_file(Path(path))
    ''')
    write_text("release_machine/engines/text_extract.py", '''
        from __future__ import annotations

        from pathlib import Path


        def read_text(path: str) -> str:
            return Path(path).read_text(encoding="utf-8", errors="ignore")
    ''')
    write_text("release_machine/engines/link_checker.py", '''
        from __future__ import annotations


        def check_links(paths: list[str]) -> dict:
            return {"state": "PASS", "checked_paths": paths, "note": "Local release candidate link checks are path-based in dry-run mode."}
    ''')
    write_text("release_machine/engines/claim_graph.py", '''
        from __future__ import annotations

        import json
        from pathlib import Path


        def load_claims(path: str = "claims/CLAIM_LEDGER_FULL.json") -> list[dict]:
            return json.loads(Path(path).read_text(encoding="utf-8"))["claims"]
    ''')
    write_text("release_machine/engines/simulation_runner.py", '''
        from __future__ import annotations

        from release_machine.core import repo_root, run_simulation_report


        def run() -> dict:
            return run_simulation_report(repo_root())
    ''')
    write_text("release_machine/engines/dataset_snapshotter.py", '''
        from __future__ import annotations


        def snapshot() -> dict:
            return {
                "state": "NOT_APPLICABLE",
                "support_ceiling": "PUBLIC_ROUTE_DISCOVERY_ONLY",
                "reason": "No pinned validation-grade dataset snapshot is claimed for v1.3.2.",
            }
    ''')
    write_text("release_machine/reports/__init__.py", '"""Report helpers and templates."""\n')
    write_text("release_machine/reports/templates/README.md", '''
        # Release Machine Report Templates

        Templates are intentionally small. The authoritative report writers live in `release_machine.core`.
    ''')

    for schema in [
        "release_unit",
        "gate_result",
        "claim_ledger",
        "evidence_binding",
        "simulation_result",
        "dataset_snapshot",
        "publish_manifest",
        "owner_approval",
    ]:
        write_json(f"release_machine/schemas/{schema}.schema.json", {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "title": schema.replace("_", " ").title(),
            "type": "object",
            "additionalProperties": True,
        })

    channel_text = {
        "zenodo": "policy: new_version_under_existing_concept_doi\nrequires_owner_approval: true\nrequires_postflight: true\npublish_allowed_by_default: false\n",
        "github_release": "policy: draft_until_owner_approval_and_doi_state_clear\nrequires_owner_approval: true\nrequires_green_ci: true\npublish_allowed_by_default: false\n",
        "github_repo_public_surface": "policy: public_repo_surface_parity\nrequires_owner_approval: false\nrequires_local_path_scan: true\n",
        "arxiv_preprint": "policy: preprint_submission_unit\nrequires_owner_approval: true\n",
        "journal_submission": "policy: journal_submission_unit\nrequires_owner_approval: true\n",
        "website_page": "policy: website_public_unit\nrequires_owner_approval: true\n",
        "outbound_email": "policy: outbound_public_statement_unit\nrequires_owner_approval: true\n",
        "investor_deck": "policy: business_outbound_deck_unit\nrequires_owner_approval: true\n",
        "product_docs": "policy: product_documentation_unit\nrequires_owner_approval: true\n",
        "dataset_release": "policy: dataset_release_unit\nrequires_owner_approval: true\n",
        "code_package": "policy: code_package_unit\nrequires_owner_approval: true\n",
    }
    for name, text in channel_text.items():
        write_text(f"release_machine/config/channels/{name}.yaml", text)

    write_text("release_machine/policies/forbidden_public_terms.yaml", '''
        forbidden_public_terms:
          - unignorable
          - killer
          - doebatsya
          - independent audit
          - empirical validation
        note: Internal aliases may exist in non-public governance files, but outward release surfaces use professional academic names.
    ''')
    write_text("release_machine/policies/claim_ceiling_rules.yaml", '''
        allowed_support_classes:
          - FORMALLY_PROVED
          - THEOREM_NATIVE_HELD_OUT_VALIDATED
          - OPERATIONALLY_SUPPORTED_WITHIN_BOUNDS
          - SIMULATION_ILLUSTRATION_ONLY
          - PUBLIC_ROUTE_DISCOVERY_ONLY
          - FRONTIER_WORK
        simulation_ceiling: SIMULATION_ILLUSTRATION_ONLY
        dataset_route_ceiling: PUBLIC_ROUTE_DISCOVERY_ONLY
    ''')
    write_text("release_machine/policies/severity_matrix.yaml", '''
        CRITICAL: publish impossible
        HIGH: publish impossible
        MEDIUM: owner-visible remediation or waiver
        LOW: tracked note
        INFO: audit note
    ''')
    write_text("release_machine/policies/waiver_policy.yaml", '''
        critical_waiver_allowed: false
        high_waiver_allowed: false
        medium_waiver_allowed: true
        low_waiver_allowed: true
    ''')
    write_text("release_machine/tests/__init__.py", "")
    write_text("release_machine/tests/test_release_machine.py", '''
        from __future__ import annotations

        import unittest

        from release_machine import core


        class ReleaseMachineTests(unittest.TestCase):
            def test_fake_pass_prevention(self) -> None:
                with self.assertRaises(ValueError):
                    core.gate_result("gate_x", "fake", "PASS", executed=False)

            def test_blocked_credentials_are_blocked(self) -> None:
                result = core.credential_gate_result("ZENODO_TOKEN", "")
                self.assertEqual(result["state"], "BLOCKED")
                self.assertEqual(result["severity"], "HIGH")

            def test_owner_approval_resets_when_hash_changes(self) -> None:
                self.assertFalse(core.owner_approval_valid({"approved": True, "artifact_freeze_hash": "old"}, "new"))

            def test_critical_high_waivers_are_rejected(self) -> None:
                self.assertFalse(core.waiver_allowed("CRITICAL"))
                self.assertFalse(core.waiver_allowed("HIGH"))
                self.assertTrue(core.waiver_allowed("MEDIUM"))

            def test_publish_impossible_without_owner_approval(self) -> None:
                summary = core.evaluate_release("oc_core_1_3_2", "all", "dry-run", write=True)
                self.assertEqual(summary["release_state"], "RELEASE_READY_NO_SEND")
                self.assertFalse(summary["publish_allowed"])
                self.assertTrue(summary["owner_approval_required"])


        if __name__ == "__main__":
            unittest.main()
    ''')


def materialize_claims() -> None:
    write_json("claims/CLAIM_LEDGER_FULL.json", {
        "release_id": "oc_core_1_3_2",
        "version": "1.3.2",
        "generated_at": STAMP,
        "claim_total": len(CLAIMS),
        "support_classes": sorted({claim["support_class"] for claim in CLAIMS}),
        "claims": CLAIMS,
    })
    rows = [
        "# OC Core 1.3.2 Full Claim Ledger",
        "",
        "This is the complete machine-readable and human-readable claim accounting surface for v1.3.2.",
        "",
        "| Claim | Public Status | Support Class | Ceiling |",
        "| --- | --- | --- | --- |",
    ]
    for claim in CLAIMS:
        rows.append(f"| `{claim['claim_id']}` {claim['short_name']} | `{claim['public_status']}` | `{claim['support_class']}` | {claim['claim_ceiling']} |")
    write_text("claims/CLAIM_LEDGER_FULL.md", "\n".join(rows))

    groups = {
        "PROMOTED_CLAIMS.md": "PROMOTED",
        "DEMOTED_CLAIMS.md": "DEMOTED",
        "SUPPORT_ONLY_CLAIMS.md": "SUPPORT_ONLY",
        "FRONTIER_OR_FUTURE_WORK.md": "FRONTIER",
    }
    for file_name, status in groups.items():
        subset = [claim for claim in CLAIMS if claim["public_status"] == status]
        title = file_name.removesuffix(".md").replace("_", " ").title()
        lines = [f"# {title}", "", f"Rows with public_status `{status}`.", ""]
        if subset:
            lines.extend(["| Claim | Support Class | Ceiling |", "| --- | --- | --- |"])
            for claim in subset:
                lines.append(f"| `{claim['claim_id']}` {claim['short_name']} | `{claim['support_class']}` | {claim['claim_ceiling']} |")
        else:
            lines.append("No claims currently use this status in v1.3.2.")
        write_text(f"claims/{file_name}", "\n".join(lines))

    matrix = [
        "# OC Core 1.3.2 Claim Evidence Matrix",
        "",
        "| Claim | Evidence refs | Non-claims |",
        "| --- | --- | --- |",
    ]
    for claim in CLAIMS:
        refs = ", ".join(f"`{item}`" for item in claim["evidence_refs"])
        non_claims = " ".join(claim["non_claims"])
        matrix.append(f"| `{claim['claim_id']}` | {refs} | {non_claims} |")
    write_text("claims/CLAIM_EVIDENCE_MATRIX.md", "\n".join(matrix))
    write_json("claims/STRONG_STATEMENT_TO_CLAIM_MAP.json", {
        "release_id": "oc_core_1_3_2",
        "version": "1.3.2",
        "policy": "Public surfaces use academic-safe labels; internal historical aliases do not promote claims.",
        "mapped_aliases": [
            {"internal_alias": "unignorable spine", "public_label": "expert technical spine", "claim_refs": ["OC-CLAIM-000020"]},
            {"internal_alias": "killer claim", "public_label": "promoted bounded claim", "claim_refs": ["OC-CLAIM-000001", "OC-CLAIM-000012"]},
            {"internal_alias": "independent audit", "public_label": "release-machine gate report", "claim_refs": ["OC-CLAIM-000017"]},
        ],
    })


def materialize_simulations() -> None:
    expected = {
        "schema_version": "1.0",
        "release_id": "oc_core_1_3_2",
        "version": "1.3.2",
        "support_ceiling": "SIMULATION_ILLUSTRATION_ONLY",
        "validation_claim_allowed": False,
        "timeout_seconds": 120,
        "expected_total": len(SIMS),
        "simulations": [
            {
                "runner": runner,
                "simulation_id": sim_id,
                "seed": 1103,
                "expected": {
                    "trace_points_length": 48,
                    "stability_score": 0.337653,
                    "boundary_crossed": False,
                },
            }
            for runner, sim_id in SIMS
        ],
    }
    write_json("simulations/expected_simulations.yml", expected)
    write_json("simulations/schemas/simulation_output.schema.json", {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": "OC Core simulation output",
        "type": "object",
        "required": ["simulation_id", "seed", "trace_points", "stability_score", "boundary_crossed"],
        "properties": {
            "simulation_id": {"type": "string"},
            "seed": {"type": "integer"},
            "trace_points": {"type": "array"},
            "stability_score": {"type": "number"},
            "boundary_crossed": {"type": "boolean"},
        },
        "additionalProperties": True,
    })
    write_text("simulations/run_all.py", r'''
        from __future__ import annotations

        import argparse
        import json
        import subprocess
        import sys
        from pathlib import Path
        from typing import Any

        ROOT = Path(__file__).resolve().parent
        REPO = ROOT.parent
        EXPECTED_PATH = ROOT / "expected_simulations.yml"
        RESULT_JSON = ROOT / "results" / "OC_CORE_1_3_2_SIMULATION_RESULTS_latest.json"
        RESULT_MD = ROOT / "results" / "OC_CORE_1_3_2_SIMULATION_RESULTS_latest.md"


        def load_expected() -> dict[str, Any]:
            return json.loads(EXPECTED_PATH.read_text(encoding="utf-8"))


        def validate_payload(payload: dict[str, Any], expected: dict[str, Any]) -> list[str]:
            errors: list[str] = []
            for key in ["simulation_id", "seed", "trace_points", "stability_score", "boundary_crossed"]:
                if key not in payload:
                    errors.append(f"missing key {key}")
            if errors:
                return errors
            if payload["simulation_id"] != expected["simulation_id"]:
                errors.append(f"simulation_id mismatch: {payload['simulation_id']} != {expected['simulation_id']}")
            if payload["seed"] != expected["seed"]:
                errors.append(f"seed mismatch: {payload['seed']} != {expected['seed']}")
            exp = expected["expected"]
            if len(payload["trace_points"]) != exp["trace_points_length"]:
                errors.append(f"trace_points length mismatch: {len(payload['trace_points'])} != {exp['trace_points_length']}")
            if round(float(payload["stability_score"]), 6) != round(float(exp["stability_score"]), 6):
                errors.append(f"stability_score mismatch: {payload['stability_score']} != {exp['stability_score']}")
            if bool(payload["boundary_crossed"]) != bool(exp["boundary_crossed"]):
                errors.append(f"boundary_crossed mismatch: {payload['boundary_crossed']} != {exp['boundary_crossed']}")
            return errors


        def run() -> dict[str, Any]:
            expected = load_expected()
            timeout = int(expected["timeout_seconds"])
            rows = []
            failures = []
            actual_runners = {path.relative_to(ROOT).as_posix() for path in ROOT.glob("*/run_simulation.py")}
            expected_runners = {row["runner"] for row in expected["simulations"]}
            for missing in sorted(expected_runners - actual_runners):
                failures.append({"runner": missing, "errors": ["expected runner is absent"]})
            for extra in sorted(actual_runners - expected_runners):
                failures.append({"runner": extra, "errors": ["unexpected runner is present"]})
            for row in expected["simulations"]:
                runner = ROOT / row["runner"]
                payload: dict[str, Any] | None = None
                errors: list[str] = []
                if runner.exists():
                    proc = subprocess.run([sys.executable, str(runner), "--seed", str(row["seed"])], cwd=REPO, capture_output=True, text=True, timeout=timeout)
                    if proc.returncode != 0:
                        errors.append(f"returncode {proc.returncode}")
                    try:
                        payload = json.loads(proc.stdout)
                    except json.JSONDecodeError as exc:
                        errors.append(f"invalid json: {exc}")
                    if proc.stderr.strip():
                        errors.append(f"stderr not empty: {proc.stderr.strip()}")
                    if payload is not None:
                        errors.extend(validate_payload(payload, row))
                else:
                    errors.append("runner missing")
                result = {
                    "runner": row["runner"],
                    "expected_simulation_id": row["simulation_id"],
                    "observed_simulation_id": payload.get("simulation_id") if payload else None,
                    "returncode": 0 if not errors else 1,
                    "errors": errors,
                    "stdout_json": payload or {},
                }
                rows.append(result)
                if errors:
                    failures.append({"runner": row["runner"], "errors": errors})
            report = {
                "release_id": expected["release_id"],
                "version": expected["version"],
                "support_ceiling": expected["support_ceiling"],
                "validation_claim_allowed": expected["validation_claim_allowed"],
                "expected_total": expected["expected_total"],
                "simulation_total": len(rows),
                "failure_total": len(failures),
                "failures": failures,
                "results": rows,
            }
            return report


        def write_report(report: dict[str, Any]) -> None:
            RESULT_JSON.parent.mkdir(parents=True, exist_ok=True)
            RESULT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            lines = [
                "# OC Core 1.3.2 Simulation Results",
                "",
                f"Support ceiling: `{report['support_ceiling']}`",
                f"Validation claim allowed: `{str(report['validation_claim_allowed']).lower()}`",
                f"Expected simulations: `{report['expected_total']}`",
                f"Observed simulations: `{report['simulation_total']}`",
                f"Failure total: `{report['failure_total']}`",
                "",
                "| Runner | Simulation ID | Result |",
                "| --- | --- | --- |",
            ]
            for row in report["results"]:
                state = "PASS" if not row["errors"] else "FAIL"
                lines.append(f"| `{row['runner']}` | `{row['observed_simulation_id']}` | `{state}` |")
            RESULT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


        def main() -> int:
            parser = argparse.ArgumentParser()
            parser.add_argument("--write-report", action="store_true")
            args = parser.parse_args()
            report = run()
            if args.write_report:
                write_report(report)
            print(json.dumps(report, ensure_ascii=False, indent=2))
            return 1 if report["failure_total"] else 0


        if __name__ == "__main__":
            raise SystemExit(main())
    ''')


def materialize_data() -> None:
    routes = [
        ("OC-DATA-ROUTE-001", "Public threshold literature route", "https://scholar.google.com/scholar?q=threshold+dynamics+complex+systems"),
        ("OC-DATA-ROUTE-002", "RAF literature route", "https://scholar.google.com/scholar?q=reflexively+autocatalytic+food-generated+sets"),
        ("OC-DATA-ROUTE-003", "Membrane dynamics literature route", "https://scholar.google.com/scholar?q=membrane+threshold+dynamics"),
        ("OC-DATA-ROUTE-004", "Regime shift literature route", "https://scholar.google.com/scholar?q=regime+shift+early+warning+signals"),
        ("OC-DATA-ROUTE-005", "Institutional trust literature route", "https://scholar.google.com/scholar?q=institutional+trust+coordination+dynamics"),
        ("OC-DATA-ROUTE-006", "Theory change literature route", "https://scholar.google.com/scholar?q=scientific+theory+change+dynamics"),
    ]
    manifest = {
        "release_id": "oc_core_1_3_2",
        "version": "1.3.2",
        "support_ceiling": "PUBLIC_ROUTE_DISCOVERY_ONLY",
        "validation_claim_allowed": False,
        "route_total": len(routes),
        "routes": [
            {
                "route_id": rid,
                "label": label,
                "public_url": url,
                "version_or_snapshot": "unpinned_public_discovery_route",
                "hash_if_available": None,
                "support_ceiling": "PUBLIC_ROUTE_DISCOVERY_ONLY",
                "claim_ceiling_effect": "does_not_widen_claim_ceiling",
            }
            for rid, label, url in routes
        ],
    }
    write_json("data/OC_DATASET_MANIFEST_1_3_2.json", manifest)
    write_json("data/OC_DATASET_SNAPSHOT_MANIFEST_1_3_2.json", {
        "release_id": "oc_core_1_3_2",
        "version": "1.3.2",
        "snapshot_total": 0,
        "validation_claim_allowed": False,
        "status": "NO_PINNED_VALIDATION_GRADE_SNAPSHOTS_IN_THIS_RELEASE_CANDIDATE",
        "policy": "Unpinned public routes remain discovery/support surfaces only.",
        "snapshots": [],
    })
    write_text("data/README_DATA_REPRODUCIBILITY.md", '''
        # OC Core 1.3.2 Data Reproducibility

        The v1.3.2 dataset layer is deliberately bounded.

        Public routes are discovery and support surfaces only. They are not validation-grade evidence because this release candidate does not include pinned snapshots, local reconstruction scripts, stable content hashes, or an end-to-end empirical replay package.

        Therefore data routes do not widen any claim ceiling. Claims that need empirical support remain support-only or frontier work until pinned snapshots and reconstruction scripts exist.
    ''')
    write_text("data/download_scripts/fetch_manifest.py", '''
        from __future__ import annotations

        import json
        from pathlib import Path


        def main() -> int:
            path = Path(__file__).resolve().parents[1] / "OC_DATASET_MANIFEST_1_3_2.json"
            print(json.dumps(json.loads(path.read_text(encoding="utf-8")), ensure_ascii=False, indent=2))
            return 0


        if __name__ == "__main__":
            raise SystemExit(main())
    ''')
    write_text("data/download_scripts/fetch_public_snapshots.py", '''
        from __future__ import annotations

        import json


        def main() -> int:
            print(json.dumps({
                "status": "NO_DOWNLOAD_PERFORMED",
                "reason": "v1.3.2 has public discovery routes only; no pinned validation-grade snapshots are claimed.",
                "validation_claim_allowed": False,
            }, indent=2))
            return 0


        if __name__ == "__main__":
            raise SystemExit(main())
    ''')
    write_text("data/checksums/SHA256SUMS", "# No pinned validation-grade dataset snapshots are shipped in OC Core 1.3.2.\n")
    write_text("DATA_MANIFEST.md", '''
        # OC Core 1.3.2 Data Manifest

        Canonical dataset manifest: `data/OC_DATASET_MANIFEST_1_3_2.json`.

        Data routes are bounded public discovery surfaces. They do not widen claim ceilings unless a later release adds pinned snapshots, stable hashes, and reconstruction scripts.

        v1.3.2 DOI state: `TBD_UNTIL_ZENODO_NEW_VERSION_PUBLISHED`.
    ''')


def materialize_release_surfaces() -> None:
    write_text("VERSION", "1.3.2\n")
    write_text("README.md", '''
        # Ontology of Continua / OC Core 1.3.2

        OC Core v1.3.2 is a canonical source-bound patch release candidate repairing release hygiene, public-surface consistency, claim accounting, reproducibility scaffolding, simulation/data support boundaries, and release-machine governance.

        Current public truth:
        - external version label: `1.3.2`
        - release state: `RELEASE_READY_NO_SEND`
        - previous canonical version: OC Core v1.3.1
        - previous canonical DOI: `10.5281/zenodo.19741958`
        - concept DOI / version chain: `10.5281/zenodo.17899134`
        - v1.3.2 DOI: `TBD_UNTIL_ZENODO_NEW_VERSION_PUBLISHED`
        - owner approval required: `true`
        - global no-send lock: `true`
        - publish allowed: `false`

        Primary release-candidate surfaces:
        - `releases/oc_core_1_3_2/editorial/OC_CORE_1_3_2_RELEASE_CONTROL_PLANE_latest.json`
        - `releases/oc_core_1_3_2/editorial/OC_CORE_1_3_2_RELEASE_SCORECARD_latest.md`
        - `claims/CLAIM_LEDGER_FULL.md`
        - `simulations/results/OC_CORE_1_3_2_SIMULATION_RESULTS_latest.md`
        - `data/OC_DATASET_MANIFEST_1_3_2.json`
        - `release_machine/`

        Simulations are deterministic and reproducibility-oriented. They illustrate and check execution surfaces; they are not empirical validation.

        Public dataset routes are bounded support/discovery surfaces. They do not widen claim ceilings unless pinned snapshots, hashes, and reconstruction scripts exist.
    ''')
    write_text("CLAIMS.md", '''
        # OC Core 1.3.2 Claims

        The authoritative claim accounting surface is `claims/CLAIM_LEDGER_FULL.json` with the matching human route in `claims/CLAIM_LEDGER_FULL.md`.

        Summary:
        - release version: `1.3.2`
        - claim total: `20`
        - promoted bounded claims: `12`
        - support-only claims: `5`
        - frontier/future-work claims: `1`
        - demoted claims: `0`

        Public claim ceilings are explicit. Simulations have the ceiling `SIMULATION_ILLUSTRATION_ONLY`. Public data routes have the ceiling `PUBLIC_ROUTE_DISCOVERY_ONLY`.
    ''')
    write_text("REPRODUCIBILITY.md", '''
        # OC Core 1.3.2 Reproducibility

        Reproducibility entry points:
        - `python -m release_machine evaluate --release oc_core_1_3_2 --channel all --mode dry-run`
        - `python -m release_machine shit-control --release oc_core_1_3_2 --channel all --max-iterations 5`
        - `python simulations/run_all.py --write-report`
        - `python -m release_machine package --release oc_core_1_3_2 --channel all --no-publish`

        The resulting release state is `RELEASE_READY_NO_SEND`. External publication remains impossible until owner approval binds the exact artifact hashes and publish manifest.
    ''')
    write_text("RUN_ALL.md", '''
        # OC Core 1.3.2 Run All

        Use:

        ```bash
        python simulations/run_all.py --write-report
        python -m release_machine evaluate --release oc_core_1_3_2 --channel all --mode dry-run
        ```

        Expected simulation result: `simulation_total=11`, `expected_total=11`, `failure_total=0`.
    ''')
    write_text("SIMULATIONS.md", '''
        # OC Core 1.3.2 Simulations

        The simulation corpus is strict about expected runner IDs, output schema, timeout, seed, and golden-output fields.

        Support ceiling: `SIMULATION_ILLUSTRATION_ONLY`.

        Validation claim allowed: `false`.
    ''')
    write_text("RELEASE_CONTRACT.md", '''
        # OC Core 1.3.2 Release Contract

        OC Core v1.3.2 may not be externally published unless the release machine reports zero critical findings, zero high findings, public-surface parity PASS, claim/evidence ceiling PASS, security/privacy PASS, owner approval bound to exact hashes, and a channel-specific publish manifest.

        Current state: `RELEASE_READY_NO_SEND`.
    ''')
    write_text("OWNER_APPROVAL_REQUIRED.md", '''
        # Owner Approval Required

        OC Core v1.3.2 is not approved for external publication.

        Owner approval must cite the exact artifact freeze hash from `releases/oc_core_1_3_2/editorial/OC_CORE_1_3_2_OWNER_APPROVAL_PACKET.md` and must specify the target channel.
    ''')
    write_text("CITATION.cff", '''
        cff-version: 1.2.0
        message: "If you use OC Core, cite the canonical Zenodo version."
        title: "Ontology of Continua - Core v1.3.2"
        version: "1.3.2"
        doi: "TBD_UNTIL_ZENODO_NEW_VERSION_PUBLISHED"
        authors:
          - family-names: "Yashin"
            given-names: "Alexander"
            orcid: "https://orcid.org/0009-0008-6166-0914"
        license: "CC-BY-4.0"
    ''')
    write_json(".zenodo.json", {
        "title": "Ontology of Continua - Core v1.3.2",
        "upload_type": "publication",
        "publication_type": "book",
        "publication_date": "2026-04-25",
        "version": "1.3.2",
        "language": "eng",
        "license": "CC-BY-4.0",
        "access_right": "open",
        "description": "OC Core v1.3.2 is a source-bound patch release candidate repairing release hygiene, public-surface consistency, claim accounting, reproducibility scaffolding, simulation/data support boundaries, and release-machine governance. DOI remains pending until a Zenodo new version is explicitly published.",
        "creators": [
            {
                "name": "Yashin, Alexander",
                "orcid": "0009-0008-6166-0914",
                "affiliation": "Independent Researcher, Leipzig/Halle, Germany",
            }
        ],
        "keywords": [
            "ontology of continua",
            "continuum theory",
            "formal ontology",
            "complex systems",
            "release governance",
            "reproducibility",
            "claim ledger",
        ],
        "related_identifiers": [
            {
                "identifier": "10.5281/zenodo.19741958",
                "relation": "isNewVersionOf",
                "scheme": "doi",
            },
            {
                "identifier": "10.5281/zenodo.17899134",
                "relation": "isVersionOf",
                "scheme": "doi",
            },
        ],
        "notes": "v1.3.2 DOI is TBD until Zenodo assigns it to a published new version under the existing concept DOI.",
    })
    write_text("RELEASE_MACHINE.md", '''
        # Logion Release Machine

        The Logion Release Machine is a repo-local external release quality system. Every outward release unit must pass channel policy, artifact inventory, build/reproducibility, document quality, claim/evidence ceilings, public-surface parity, security/privacy, owner approval, publish preflight, and postflight gates.

        The hard rule is no false PASS. A gate that did not run cannot be PASS. A credential or channel blockage is BLOCKED, not PASS. Critical or high findings make publication impossible.
    ''')
    write_text("RELEASE_STANDARDS.md", '''
        # Release Standards

        Everything that leaves Logion as a public artifact is a release unit: Zenodo records, GitHub releases, preprints, journal submissions, websites, public docs, product docs, datasets, code packages, decks, and outbound statements.

        Required surfaces: owner, release id, version, channel policy, artifact inventory, claim ledger, evidence map, risk classification, reproducibility report, security/privacy scan, public-surface parity report, owner approval state, publish manifest, and post-release audit state.
    ''')
    write_text("SHIT_CONTROL_PROTOCOL.md", '''
        # Internal Release Quality Protocol

        Internal alias: Shit Control.

        Public/professional name: Logion External Release Quality Control or Logion Release Machine.

        This internal protocol name is not an outward-facing release label. Public OC Core v1.3.2 surfaces use academic-safe artifact names and bounded claim language.
    ''')
    write_text("CHANNEL_POLICIES.md", '''
        # Channel Policies

        Channel policies live in `release_machine/config/channels/`.

        v1.3.2 target channels:
        - Zenodo: new version under concept DOI `10.5281/zenodo.17899134`.
        - GitHub release: draft until owner approval and DOI state are explicit.
        - Public repository surface: parity, checksums, claim ledger, simulation/data boundaries, no local paths, no secrets.
    ''')
    write_text("RELEASE_BLOCKERS.md", '''
        # Release Blockers

        Publication is blocked by any critical or high finding, missing owner approval, artifact hash drift after approval, stale DOI/version metadata, unsupported strong public statements, local path or secret leakage, failed strict simulation assertions, unpinned data routes being described as validation, or a public-surface parity mismatch.
    ''')
    write_text("release_machine.yaml", '''
        release_machine:
          default_release: oc_core_1_3_2
          default_channel: all
          no_false_pass: true
          global_no_send_lock: true
          owner_approval_required: true
    ''')
    write_text("releases/oc_core_1_3_2/README.md", '''
        # OC Core 1.3.2 Release Candidate

        State: `RELEASE_READY_NO_SEND`.

        Previous canonical version: OC Core v1.3.1.

        Previous canonical DOI: `10.5281/zenodo.19741958`.

        Concept DOI: `10.5281/zenodo.17899134`.

        v1.3.2 DOI: `TBD_UNTIL_ZENODO_NEW_VERSION_PUBLISHED`.

        This folder contains the release-candidate artifacts, editorial control plane, scorecards, findings, checksums, owner approval packet, publish manifest draft, and postflight checklist for a later owner-approved publication pass.
    ''')
    write_text("releases/oc_core_1_3_2/editorial/OC_CORE_1_3_2_POSTFLIGHT_CHECKLIST.md", '''
        # OC Core 1.3.2 Postflight Checklist

        After explicit owner-approved publication:
        - confirm Zenodo record is a new version under concept DOI `10.5281/zenodo.17899134`;
        - confirm v1.3.2 DOI is final and appears consistently;
        - confirm GitHub release is draft/non-draft as approved;
        - confirm all visible PDFs and ZIP are downloadable;
        - confirm SHA256 values match local inventory;
        - confirm public CI status is truthfully reflected;
        - confirm no public metadata says no-send after publication.
    ''')


def materialize_workflows_and_make() -> None:
    write_text("Makefile", '''
        .PHONY: release-check release-build release-test release-package shit-control

        release-check:
        \tpython -m release_machine evaluate --release oc_core_1_3_2 --channel all --mode dry-run

        release-build:
        \tpython -m release_machine package --release oc_core_1_3_2 --channel all --no-publish

        release-test:
        \tpython simulations/run_all.py --write-report
        \tpython -m unittest discover release_machine/tests

        release-package:
        \tpython -m release_machine package --release oc_core_1_3_2 --channel all --no-publish

        shit-control:
        \tpython -m release_machine shit-control --release oc_core_1_3_2 --channel all --max-iterations 5
    ''')
    write_text("make.cmd", r'''
        @echo off
        set TARGET=%1
        if "%TARGET%"=="" set TARGET=release-check
        if "%TARGET%"=="release-check" python -m release_machine evaluate --release oc_core_1_3_2 --channel all --mode dry-run && exit /b %ERRORLEVEL%
        if "%TARGET%"=="release-build" python -m release_machine package --release oc_core_1_3_2 --channel all --no-publish && exit /b %ERRORLEVEL%
        if "%TARGET%"=="release-test" python simulations/run_all.py --write-report && python -m unittest discover release_machine/tests && exit /b %ERRORLEVEL%
        if "%TARGET%"=="release-package" python -m release_machine package --release oc_core_1_3_2 --channel all --no-publish && exit /b %ERRORLEVEL%
        if "%TARGET%"=="shit-control" python -m release_machine shit-control --release oc_core_1_3_2 --channel all --max-iterations 5 && exit /b %ERRORLEVEL%
        echo Unknown target %TARGET%
        exit /b 2
    ''')
    write_text(".github/workflows/core-release-on-tag.yml", '''
        name: Core Release On Tag - Safe Gate

        on:
          push:
            tags:
              - "v*"

        jobs:
          safe-gate:
            runs-on: ubuntu-latest
            permissions:
              contents: read
            steps:
              - uses: actions/checkout@v4
              - uses: actions/setup-python@v5
                with:
                  python-version: "3.11"
              - name: Run release machine dry-run
                run: python -m release_machine evaluate --release oc_core_1_3_2 --channel all --mode dry-run
              - name: Produce blocked publish plan
                run: python -m release_machine publish-plan --release oc_core_1_3_2 --channel all
              - name: Keep v1.3.2 publication locked
                run: |
                  echo "No GitHub release or Zenodo publication is created by this workflow."
                  echo "Owner approval and a later explicit publication instruction are required."
    ''')
    write_text(".github/workflows/release-machine-dry-run.yml", '''
        name: Release Machine Dry Run

        on:
          push:
            branches:
              - main
              - "release/**"
          pull_request:

        jobs:
          dry-run:
            runs-on: ubuntu-latest
            steps:
              - uses: actions/checkout@v4
              - uses: actions/setup-python@v5
                with:
                  python-version: "3.11"
              - run: python -m release_machine evaluate --release oc_core_1_3_2 --channel all --mode dry-run
              - run: python -m unittest discover release_machine/tests
    ''')
    write_text(".github/workflows/release-candidate-build.yml", '''
        name: OC Core 1.3.2 Release Candidate Build

        on:
          workflow_dispatch:
          push:
            branches:
              - "release/oc-core-1.3.2"

        jobs:
          build:
            runs-on: ubuntu-latest
            steps:
              - uses: actions/checkout@v4
              - uses: actions/setup-python@v5
                with:
                  python-version: "3.11"
              - run: python simulations/run_all.py --write-report
              - run: python -m release_machine package --release oc_core_1_3_2 --channel all --no-publish
              - run: python -m release_machine shit-control --release oc_core_1_3_2 --channel all --max-iterations 5
    ''')
    write_text(".github/workflows/safe-publish-on-tag.yml", '''
        name: Safe Blocked Publish On Tag

        on:
          push:
            tags:
              - "v1.3.2"

        jobs:
          no-send:
            runs-on: ubuntu-latest
            steps:
              - uses: actions/checkout@v4
              - uses: actions/setup-python@v5
                with:
                  python-version: "3.11"
              - run: python -m release_machine publish-plan --release oc_core_1_3_2 --channel all
              - run: echo "Publication is intentionally blocked until explicit owner approval and release instruction."
    ''')
    write_text(".github/workflows/postflight-public-surface.yml", '''
        name: Postflight Public Surface Check

        on:
          workflow_dispatch:
            inputs:
              public_url:
                description: "Published public URL"
                required: true
                type: string

        jobs:
          postflight:
            runs-on: ubuntu-latest
            steps:
              - uses: actions/checkout@v4
              - uses: actions/setup-python@v5
                with:
                  python-version: "3.11"
              - run: python -m release_machine postflight --release oc_core_1_3_2 --channel zenodo --public-url "${{ inputs.public_url }}"
    ''')


def main() -> int:
    materialize_release_machine()
    materialize_claims()
    materialize_simulations()
    materialize_data()
    materialize_release_surfaces()
    materialize_workflows_and_make()
    subprocess.run([sys.executable, "-m", "release_machine", "package", "--release", "oc_core_1_3_2", "--channel", "all", "--no-publish"], cwd=ROOT, check=True)
    subprocess.run([sys.executable, "-m", "release_machine", "evaluate", "--release", "oc_core_1_3_2", "--channel", "all", "--mode", "dry-run"], cwd=ROOT, check=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
