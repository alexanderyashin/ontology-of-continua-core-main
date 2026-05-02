from __future__ import annotations

import json
import hashlib
import importlib.util
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
import zipfile

import release_machine
from release_machine import core
from release_machine import complete
from release_machine import oc133
from release_machine import oc133_platinum
from release_machine import oc133_v12
from release_machine import publication
from release_machine import public_release
from release_machine import science_monolith
from release_machine import versioning
from tools import oc133_public_release_payload


def _load_grand_science_loop_module():
    root = complete.repo_root()
    module_path = root / "tools" / "oc133_grand_science_research_loop.py"
    spec = importlib.util.spec_from_file_location("oc133_grand_science_research_loop", module_path)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _load_delta_queue_module():
    root = complete.repo_root()
    module_path = root / "tools" / "logion_delta_queue.py"
    spec = importlib.util.spec_from_file_location("logion_delta_queue", module_path)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _load_process_coherence_guard_module():
    root = complete.repo_root()
    module_path = root / "tools" / "logion_process_coherence_guard.py"
    spec = importlib.util.spec_from_file_location("logion_process_coherence_guard", module_path)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _load_incident_pipeline_module():
    root = complete.repo_root()
    module_path = root / "tools" / "logion_incident_pipeline.py"
    spec = importlib.util.spec_from_file_location("logion_incident_pipeline", module_path)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _load_escalation_matrix_module():
    root = complete.repo_root()
    module_path = root / "tools" / "logion_escalation_matrix.py"
    spec = importlib.util.spec_from_file_location("logion_escalation_matrix", module_path)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _load_service_architecture_module():
    root = complete.repo_root()
    module_path = root / "tools" / "logion_service_architecture.py"
    spec = importlib.util.spec_from_file_location("logion_service_architecture", module_path)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _load_release_spaces_module():
    root = complete.repo_root()
    module_path = root / "tools" / "logion_release_spaces.py"
    spec = importlib.util.spec_from_file_location("logion_release_spaces", module_path)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _load_function_product_module():
    root = complete.repo_root()
    module_path = root / "tools" / "logion_function_product_separation.py"
    spec = importlib.util.spec_from_file_location("logion_function_product_separation", module_path)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _load_reproducibility_verifier_module():
    root = complete.repo_root()
    module_path = root / "tools" / "verify_oc133_reproducible_temp_tree.py"
    spec = importlib.util.spec_from_file_location("verify_oc133_reproducible_temp_tree", module_path)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class ReleaseMachineTests(unittest.TestCase):
    def _ensure_oc133_v12_surface(self) -> Path:
        root = complete.repo_root()
        oc133_v12.ensure_v12(root)
        return root

    def _write_fixture_json(self, root: Path, rel_path: str, payload: dict) -> None:
        path = root / rel_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    def test_oc133_delta_writers_skip_identical_content(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            text_path = root / "artifact.md"
            json_path = root / "artifact.json"
            self.assertTrue(oc133.write_text(text_path, "stable\n"))
            self.assertFalse(oc133.write_text(text_path, "stable\n"))
            self.assertTrue(oc133.write_json(json_path, {"stable": True}))
            self.assertFalse(oc133.write_json(json_path, {"stable": True}))

    def test_public_release_profile_is_serialized_and_reloaded(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = public_release.load_profile(root, "oc_core_1_3_3")
            self.assertTrue(public_release.write_profile(root, profile))
            reloaded = public_release.load_profile(root, "oc_core_1_3_3")
            self.assertEqual(reloaded.release_id, "oc_core_1_3_3")
            self.assertEqual(reloaded.version, "1.3.3")
            self.assertEqual(reloaded.tag, "v1.3.3")
            self.assertGreater(len(reloaded.assets), 5)

    def test_public_release_metadata_can_be_built_without_dirtying_tree(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = public_release.load_profile(root, "oc_core_1_3_3")
            payload = public_release.build_public_metadata(root, profile, write=False)
            self.assertEqual(payload["release_id"], "oc_core_1_3_3")
            self.assertIn("This is the public GitHub and Zenodo release", payload["release_body"])
            self.assertIn("Journal submissions require a separate owner approval", payload["release_body"])
            self.assertIn("<p><strong>", payload["zenodo_metadata"]["description"])
            self.assertNotIn("# Ontology", payload["zenodo_metadata"]["description"])
            self.assertFalse((root / ".zenodo.json").exists())
            self.assertFalse((root / "releases/oc_core_1_3_3/editorial/PUBLIC_RELEASE_PROFILE.json").exists())

    def test_oc133_public_payload_check_is_non_mutating(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            editorial = root / "releases" / "oc_core_1_3_3" / "editorial"
            sources = root / "releases" / "oc_core_1_3_3" / "public_payload" / "sources"
            zip_path = root / "releases" / "oc_core_1_3_3" / "artifacts" / "oc_core_1_3_3_public_release.zip"
            zip_path.parent.mkdir(parents=True, exist_ok=True)
            zip_path.write_bytes(b"zip-placeholder")

            original_editorial = oc133_public_release_payload.EDITORIAL
            original_sources = oc133_public_release_payload.PUBLIC_SOURCES
            original_zip = oc133_public_release_payload.PUBLIC_ZIP
            original_root = oc133_public_release_payload.ROOT
            original_assets = oc133_public_release_payload.public_assets
            original_pdf_audit = oc133_public_release_payload.public_pdf_audit
            original_surface_scan = oc133_public_release_payload.public_surface_scan
            original_zip_scan = oc133_public_release_payload.zip_public_scan
            original_monolith_audit = science_monolith.audit_monolith
            try:
                oc133_public_release_payload.EDITORIAL = editorial
                oc133_public_release_payload.PUBLIC_SOURCES = sources
                oc133_public_release_payload.PUBLIC_ZIP = zip_path
                oc133_public_release_payload.ROOT = root
                oc133_public_release_payload.public_assets = lambda: []  # type: ignore[assignment]
                oc133_public_release_payload.public_pdf_audit = lambda *, persist_audit_text=True: {  # type: ignore[assignment]
                    "state": "PASS",
                    "rows": [],
                    "failure_total": 0,
                }
                oc133_public_release_payload.public_surface_scan = lambda paths: []  # type: ignore[assignment]
                oc133_public_release_payload.zip_public_scan = lambda: {"state": "PASS", "failure_total": 0, "failures": []}  # type: ignore[assignment]
                science_monolith.audit_monolith = lambda repo_root: {"state": "PASS"}  # type: ignore[assignment]

                payload = oc133_public_release_payload.audit_public_payload(write=False)
            finally:
                oc133_public_release_payload.EDITORIAL = original_editorial
                oc133_public_release_payload.PUBLIC_SOURCES = original_sources
                oc133_public_release_payload.PUBLIC_ZIP = original_zip
                oc133_public_release_payload.ROOT = original_root
                oc133_public_release_payload.public_assets = original_assets  # type: ignore[assignment]
                oc133_public_release_payload.public_pdf_audit = original_pdf_audit  # type: ignore[assignment]
                oc133_public_release_payload.public_surface_scan = original_surface_scan  # type: ignore[assignment]
                oc133_public_release_payload.zip_public_scan = original_zip_scan  # type: ignore[assignment]
                science_monolith.audit_monolith = original_monolith_audit  # type: ignore[assignment]

            self.assertEqual(payload["state"], "PASS")
            self.assertFalse((editorial / "PUBLIC_PAYLOAD_SUITABILITY_1.3.3_latest.json").exists())
            self.assertFalse((editorial / "pdf_text_audit").exists())

    def test_oc133_zenodo_metadata_uses_html_not_github_markdown(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = public_release.load_profile(root, "oc_core_1_3_3")
            payload = public_release.build_public_metadata(
                root,
                profile,
                zenodo_doi="10.5281/zenodo.19957779",
                zenodo_record_url="https://zenodo.org/records/19957779",
                github_release_url="https://github.com/alexanderyashin/ontology-of-continua-core-main/releases/tag/v1.3.3",
                write=False,
            )
            description = payload["zenodo_metadata"]["description"]
            self.assertTrue(payload["zenodo_presentation_gate"]["ok"])
            self.assertIn("Recommended reading order", description)
            self.assertIn("<ol>", description)
            self.assertNotRegex(description, r"(?m)^\s*#")
            self.assertLessEqual(len(public_release.SHA256_HEX_RE.findall(description)), 1)

    def test_oc133_zenodo_presentation_gate_rejects_markdown(self) -> None:
        profile = public_release.load_profile(complete.repo_root(), "oc_core_1_3_3")
        metadata = public_release._zenodo_metadata(
            profile,
            "# Raw Markdown\n\n- `artifact.pdf`: abcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789\n",
            doi="10.5281/zenodo.19957779",
        )
        gate = public_release._zenodo_metadata_suitability(
            profile,
            metadata,
            expected_doi="10.5281/zenodo.19957779",
        )
        self.assertFalse(gate["ok"])
        self.assertFalse(gate["checks"]["no_markdown_headings"])
        self.assertFalse(gate["checks"]["html_structure_ok"])

    def test_oc133_public_file_set_gate_rejects_metadata_first(self) -> None:
        profile = public_release.load_profile(complete.repo_root(), "oc_core_1_3_3")
        records = [
            {
                "filename": Path(asset.path).name,
                "size_bytes": 100_000 if asset.path.lower().endswith(".pdf") else 10_000,
            }
            for asset in profile.assets
        ]
        records.sort(key=lambda row: 0 if row["filename"] == ".codemeta.json" else 1)
        gate = public_release._public_file_set_gate(complete.repo_root(), profile, records)
        self.assertFalse(gate["ok"])
        self.assertFalse(gate["checks"]["metadata_not_first"])

    def test_oc133_public_release_profile_uses_public_payload_asset(self) -> None:
        profile = public_release.load_profile(complete.repo_root(), "oc_core_1_3_3")
        asset_paths = [asset.path for asset in profile.assets]
        self.assertIn("releases/oc_core_1_3_3/artifacts/oc_core_1_3_3_public_release.zip", asset_paths)
        self.assertNotIn("releases/oc_core_1_3_3/artifacts/oc_core_1_3_3_no_send_release.zip", asset_paths)

    def test_oc133_science_monolith_corpus_ledger_has_required_science_refs(self) -> None:
        root = complete.repo_root()
        ledger = science_monolith.build_corpus_ledger(root)
        self.assertEqual(ledger["version"], "1.3.3")
        self.assertEqual(ledger["missing_total"], 0)
        refs = {row["ref"] for row in ledger["rows"]}
        self.assertIn("claims/CLAIM_LEDGER_1_3_3.json", refs)
        self.assertIn("formal/lean/OC133V12.lean", refs)
        self.assertIn("validation/target_blind/OC133_TARGET_BLIND_PREDICTION_TABLE.json", refs)
        self.assertIn("releases/oc_core_1_3_3/public_payload/sources/OC_CORE_1_3_3_MASTER_MONOGRAPH_EN.md", refs)

    def test_oc133_public_payload_suitability_requires_science_monolith_gate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = public_release.load_profile(root, "oc_core_1_3_3")
            audit = root / "releases" / "oc_core_1_3_3" / "editorial" / "PUBLIC_PAYLOAD_SUITABILITY_1.3.3_latest.json"
            audit.parent.mkdir(parents=True, exist_ok=True)
            audit.write_text(
                json.dumps(
                    {
                        "state": "PASS",
                        "pdf_audit": {"failure_total": 0},
                        "public_surface_forbidden_hit_total": 0,
                        "zip_scan": {"state": "PASS"},
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            gate = public_release._public_payload_suitability_ok(root, profile)
            self.assertFalse(gate["ok"])
            self.assertIsNone(gate["science_monolith_state"])

    def test_logion_incident_pipeline_routes_public_release_failure_to_capabilities(self) -> None:
        incident = _load_incident_pipeline_module()
        payload = incident.build_incident_payload()
        self.assertEqual(payload["incident_id"], "INC_OC133_PUBLIC_RELEASE_MONOGRAPH_SURROGATE_20260501")
        self.assertEqual(payload["severity"], "P0")
        self.assertFalse(payload["manual_repair_allowed"])
        owners = {row["owner_capability"] for row in payload["work_orders"]}
        self.assertIn("Research/ManuscriptIntegration", owners)
        self.assertIn("IT/ReleaseAutomation", owners)
        self.assertIn("Review/Cerberus", owners)
        self.assertIn("Publication/PublicRecords", owners)
        self.assertGreaterEqual(len(payload["root_causes"]), 4)

    def test_logion_escalation_matrix_classifies_current_release_incident_as_p0(self) -> None:
        escalation = _load_escalation_matrix_module()
        outputs = escalation.build_outputs(complete.repo_root())
        validation = escalation.validate(outputs)
        self.assertEqual(validation["state"], "PASS")
        self.assertFalse(outputs["matrix"]["manual_repair_policy"]["codex_direct_hand_fix_allowed"])
        incident = next(
            row for row in outputs["queue"]["rows"]
            if row["incident_id"] == "INC_OC133_PUBLIC_RELEASE_MONOGRAPH_SURROGATE_20260501"
        )
        self.assertEqual(incident["severity"], "P0")
        self.assertEqual(incident["signal_class"], "bad_public_release_record")
        self.assertIn("IT/ReleaseAutomation", incident["capability_owners"])

    def test_logion_service_architecture_keeps_core_functions_independent(self) -> None:
        services = _load_service_architecture_module()
        outputs = services.build_registry()
        validation = services.validate(outputs)
        self.assertEqual(validation["state"], "PASS")
        service_ids = {row["service_id"] for row in outputs["registry"]["services"]}
        self.assertIn("incident_management", service_ids)
        self.assertIn("editorial_manuscript", service_ids)
        self.assertIn("research_science", service_ids)
        self.assertIn("release_engineering", service_ids)
        self.assertIn("publication_records", service_ids)
        self.assertNotEqual("incident_management", "editorial_manuscript")
        bad_public_route = next(row for row in outputs["router"]["routes"] if row["signal"] == "bad_public_release_record")
        self.assertEqual(bad_public_route["primary_service"], "incident_management")
        self.assertIn("editorial_manuscript", bad_public_route["downstream_services"])
        self.assertIn("publication_records", bad_public_route["downstream_services"])

    def test_logion_release_spaces_separate_development_verification_and_release(self) -> None:
        spaces = _load_release_spaces_module()
        model = spaces.build_space_model()
        ids = {row["space_id"] for row in model["spaces"]}
        self.assertEqual(ids, {"development", "verification", "release"})
        migrations = {row["migration_id"]: row for row in model["migrations"]}
        self.assertFalse(migrations["development_to_verification"]["may_write_public_release_space"])
        self.assertTrue(migrations["verification_to_release"]["may_write_public_release_space"])
        release_space = next(row for row in model["spaces"] if row["space_id"] == "release")
        self.assertIn("NO_SEND", release_space["forbidden_control_language"])
        self.assertTrue(model["delta_queue_contract"]["semantic_delta_required_for_downstream_trigger"])

    def test_logion_function_product_separation_keeps_product_outcomes_out_of_functions(self) -> None:
        module = _load_function_product_module()
        outputs = module.build_outputs()
        audit = module.validate(outputs)
        self.assertEqual(audit["state"], "PASS")
        metrics = audit["quantitative_metrics"]
        self.assertEqual(metrics["function_registry_product_token_hit_total"], 0)
        self.assertEqual(metrics["production_line_product_token_hit_total"], 0)
        products = outputs["products"]["products"]
        self.assertEqual(len(products), 1)
        self.assertEqual(products[0]["layer_id"], "product_layer")
        line_ids = {row["line_id"] for row in outputs["production_lines"]["production_lines"]}
        self.assertIn(products[0]["production_line_id"], line_ids)

    def test_oc133_existing_package_reused_when_fingerprint_inputs_match(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            payload_path = root / "proofs" / "fixture_1_3_3.json"
            payload_path.parent.mkdir(parents=True, exist_ok=True)
            payload_path.write_text('{"stable": true}\n', encoding="utf-8")
            paths = [payload_path]
            oc133.write_inventory_and_checksums(root, paths)
            zip_payload = oc133.build_zip(root, paths)
            reused = oc133._existing_package_if_current(root, "all", True, "fixture", paths)
            self.assertIsNotNone(reused)
            assert reused is not None
            self.assertEqual(reused["package_sha256"], zip_payload["sha256"])
            self.assertEqual(reused["artifact_total"], 1)

    def test_oc133_package_excludes_self_referential_audit_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            subprocess.run(["git", "init"], cwd=root, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            audit = root / "releases" / "oc_core_1_3_3" / "editorial" / "OC_CORE_1_3_3_PERSONAL_RELEASE_AUDIT_latest.json"
            pdf_text = root / "releases" / "oc_core_1_3_3" / "editorial" / "pdf_text_audit" / "OC_CORE_1_3_3_MASTER_MONOGRAPH_EN.txt"
            proof = root / "proofs" / "FINITE_MODEL_CHECKS_1_3_3.json"
            for path in [audit, pdf_text, proof]:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("{}\n", encoding="utf-8")
            subprocess.run(["git", "add", "."], cwd=root, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            refs = {path.relative_to(root).as_posix() for path in oc133.package_file_paths(root)}
            self.assertIn("proofs/FINITE_MODEL_CHECKS_1_3_3.json", refs)
            self.assertNotIn("releases/oc_core_1_3_3/editorial/OC_CORE_1_3_3_PERSONAL_RELEASE_AUDIT_latest.json", refs)
            self.assertNotIn("releases/oc_core_1_3_3/editorial/pdf_text_audit/OC_CORE_1_3_3_MASTER_MONOGRAPH_EN.txt", refs)

    def test_oc133_package_candidates_are_tracked_ref_driven_for_windows_long_paths(self) -> None:
        long_ref = (
            "validation/heldout/grand_science/formal_mathematics/coverage_work_orders/"
            "planned_corpora/computational_complexity_algorithmic_proof/"
            "OC133_COMPLEXITY_ALGORITHMIC_WITHHELD_AGGREGATES.lock.json"
        )
        original_tracked_ref_set = oc133.tracked_ref_set
        try:
            oc133.tracked_ref_set = lambda root: {long_ref, "formal/README.md"}  # type: ignore[assignment]
            refs = {path.as_posix() for path in oc133.package_file_paths(Path("."))}
        finally:
            oc133.tracked_ref_set = original_tracked_ref_set  # type: ignore[assignment]
        self.assertIn(long_ref, refs)
        self.assertIn("formal/README.md", refs)

    def test_oc133_repro_verifier_treats_stale_previous_manifest_as_delta_not_blocker(self) -> None:
        verifier = _load_reproducibility_verifier_module()
        self.assertFalse(verifier.previous_manifest_blocks_release(True))
        self.assertFalse(verifier.previous_manifest_blocks_release(None))
        self.assertTrue(verifier.previous_manifest_blocks_release(False))

    def test_oc133_lean_certificate_source_guard_detects_delta(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source_path = root / "release_machine" / "oc133.py"
            source_path.parent.mkdir(parents=True, exist_ok=True)
            source_path.write_text("stable\n", encoding="utf-8")
            cert_path = root / "formal" / "lean" / "LEAN_BUILD_CERTIFICATE_1_3_3.json"
            cert_path.parent.mkdir(parents=True, exist_ok=True)
            cert_path.write_text(
                json.dumps(
                    {
                        "clean_source_manifest": [
                            {
                                "ref": "release_machine/oc133.py",
                                "sha256": hashlib.sha256(b"stable\n").hexdigest(),
                            }
                        ]
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            self.assertTrue(oc133._lean_certificate_sources_current(root))
            source_path.write_text("changed\n", encoding="utf-8")
            self.assertFalse(oc133._lean_certificate_sources_current(root))

    def test_oc133_root_no_send_surface_guard_detects_stale_legacy_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for ref in oc133.ROOT_NO_SEND_SURFACE_REFS:
                path = root / ref
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("OC Core 1.3.3 no-send review package\n", encoding="utf-8")
            self.assertTrue(oc133._root_no_send_surface_current(root))
            (root / "manifest.json").write_text("oc_core_1_3_2 v1.3.2 10.5281/zenodo.123\n", encoding="utf-8")
            self.assertFalse(oc133._root_no_send_surface_current(root))
            (root / "manifest.json").write_text("OC Core 1.3.3 no-send review package\n", encoding="utf-8")
            (root / ".zenodo.json").write_text('{"version":"1.3.2"}\n', encoding="utf-8")
            self.assertFalse(oc133._root_no_send_surface_current(root))

    def test_logion_delta_queue_blocks_downstream_when_snapshot_unchanged(self) -> None:
        delta_queue = _load_delta_queue_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_fixture_json(
                root,
                "releases/oc_core_1_3_3/editorial/OC_CORE_1_3_3_RELEASE_SCORECARD_latest.json",
                {
                    "summary": {
                        "release_state": "OC_CORE_1_3_3_EXTERNAL_REVIEW_READY_NO_SEND",
                        "technical_gate_state": "OC_CORE_1_3_3_10_10_READY_NO_SEND",
                        "master_verdict": "PASS",
                        "gate_counts": {"PASS": 71, "FAIL": 0},
                        "publish_allowed": False,
                        "journal_submissions_allowed": False,
                        "all_domain_blocker_ids": ["grand_toe_claim_ledger_evidence"],
                    }
                },
            )
            self._write_fixture_json(
                root,
                "reviews/oc133_llm_cerberus/OC133_LLM_CERBERUS_SUMMARY.json",
                {"critical_open_total": 0, "high_open_total": 0, "parse_failure_total": 0},
            )
            self._write_fixture_json(
                root,
                "releases/oc_core_1_3_3/submission_packages/SUBMISSION_PACKAGE_INDEX.json",
                {"package_total": 8, "package_status_counts": {"OWNER_REVIEW_READY_NO_SEND": 8}, "submission_allowed": False, "journal_submissions_allowed": False},
            )
            self._write_fixture_json(
                root,
                "operations/project_control/LOGION_DIRTY_TREE_GOVERNANCE_LEDGER.json",
                {"governance_state": "GOVERNED_DIRTY_TREE", "public_dirty_total": 0, "public_unclassified_total": 0, "private_dirty_total": 0, "private_unknown_total": 0},
            )
            self._write_fixture_json(
                root,
                "releases/oc_core_1_3_3/editorial/OC_CORE_1_3_3_ZIP_INTEGRITY_latest.json",
                {"package_sha256": "a" * 64, "package_size_bytes": 1, "package_member_total": 1},
            )
            first = delta_queue.evaluate(root, "release")
            delta_queue.write_json_if_changed(root / delta_queue.LEDGER_REL, first)
            second = delta_queue.evaluate(root, "release")
            self.assertFalse(second["significant_delta"])
            self.assertFalse(second["downstream_trigger_allowed"])

    def test_logion_delta_queue_ignores_project_control_self_telemetry_dirty(self) -> None:
        delta_queue = _load_delta_queue_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            subprocess.run(["git", "init"], cwd=root, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            telemetry = root / "operations" / "project_control" / "LOGION_DELTA_QUEUE_LEDGER.json"
            release_delta = root / "releases" / "oc_core_1_3_3" / "editorial" / "release_delta.json"
            telemetry.parent.mkdir(parents=True, exist_ok=True)
            release_delta.parent.mkdir(parents=True, exist_ok=True)
            telemetry.write_text("{}\n", encoding="utf-8")
            release_delta.write_text("{}\n", encoding="utf-8")
            status = delta_queue.git_status_summary(root)
            self.assertEqual(status["dirty_total"], 1)
            self.assertEqual(status["dirty_paths"], ["releases/oc_core_1_3_3/editorial/release_delta.json"])

    def test_logion_process_coherence_guard_blocks_self_referential_package(self) -> None:
        guard = _load_process_coherence_guard_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            package = root / "releases" / "oc_core_1_3_3" / "artifacts" / "oc_core_1_3_3_no_send_release.zip"
            package.parent.mkdir(parents=True, exist_ok=True)
            package.write_bytes(b"zip")
            self._write_fixture_json(
                root,
                "releases/oc_core_1_3_3/editorial/OC_CORE_1_3_3_RELEASE_SCORECARD_latest.json",
                {"summary": {"release_state": "OC_CORE_1_3_3_EXTERNAL_REVIEW_READY_NO_SEND", "all_domain_ready_no_send": False}},
            )
            self._write_fixture_json(
                root,
                "releases/oc_core_1_3_3/editorial/OC_CORE_1_3_3_PUBLISH_MANIFEST_DRAFT.json",
                {"publish_allowed": False, "journal_submissions_allowed": False, "owner_approved": False},
            )
            self._write_fixture_json(
                root,
                "releases/oc_core_1_3_3/editorial/OWNER_RELEASE_APPROVAL_v1.3.3.json",
                {"decision": "PENDING", "publish_allowed": False},
            )
            self._write_fixture_json(
                root,
                "releases/oc_core_1_3_3/submission_packages/SUBMISSION_PACKAGE_INDEX.json",
                {"submission_allowed": False, "journal_submissions_allowed": False},
            )
            self._write_fixture_json(
                root,
                "releases/oc_core_1_3_3/editorial/OC_CORE_1_3_3_ZIP_INTEGRITY_latest.json",
                {"package": "releases/oc_core_1_3_3/artifacts/oc_core_1_3_3_no_send_release.zip", "package_sha256": hashlib.sha256(b"zip").hexdigest()},
            )
            self._write_fixture_json(
                root,
                "releases/oc_core_1_3_3/editorial/OC_CORE_1_3_3_ARTIFACT_INVENTORY.json",
                {"rows": [{"path": "releases/oc_core_1_3_3/editorial/OC_CORE_1_3_3_PERSONAL_RELEASE_AUDIT_latest.json"}]},
            )
            self._write_fixture_json(
                root,
                "operations/project_control/LOGION_DIRTY_TREE_GOVERNANCE_LEDGER.json",
                {"public_unclassified_total": 0, "private_unknown_total": 0},
            )
            report = guard.build_report(root)
            self.assertEqual(report["state"], "FAIL")
            self.assertIn("COHERENCE-SELF-REFERENTIAL-PACKAGE", {row["issue_id"] for row in report["issues"]})

    def test_logion_process_coherence_guard_blocks_materializer_package_ownership(self) -> None:
        guard = _load_process_coherence_guard_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            package = root / "releases" / "oc_core_1_3_3" / "artifacts" / "oc_core_1_3_3_no_send_release.zip"
            package.parent.mkdir(parents=True, exist_ok=True)
            package.write_bytes(b"zip")
            self._write_fixture_json(
                root,
                "releases/oc_core_1_3_3/editorial/OC_CORE_1_3_3_RELEASE_SCORECARD_latest.json",
                {"summary": {"release_state": "OC_CORE_1_3_3_EXTERNAL_REVIEW_READY_NO_SEND", "all_domain_ready_no_send": False}},
            )
            self._write_fixture_json(
                root,
                "releases/oc_core_1_3_3/editorial/OC_CORE_1_3_3_PUBLISH_MANIFEST_DRAFT.json",
                {"publish_allowed": False, "journal_submissions_allowed": False, "owner_approved": False},
            )
            self._write_fixture_json(
                root,
                "releases/oc_core_1_3_3/editorial/OWNER_RELEASE_APPROVAL_v1.3.3.json",
                {"decision": "PENDING", "publish_allowed": False},
            )
            self._write_fixture_json(
                root,
                "releases/oc_core_1_3_3/submission_packages/SUBMISSION_PACKAGE_INDEX.json",
                {"submission_allowed": False, "journal_submissions_allowed": False},
            )
            self._write_fixture_json(
                root,
                "releases/oc_core_1_3_3/editorial/OC_CORE_1_3_3_ZIP_INTEGRITY_latest.json",
                {"package": "releases/oc_core_1_3_3/artifacts/oc_core_1_3_3_no_send_release.zip", "package_sha256": hashlib.sha256(b"zip").hexdigest()},
            )
            self._write_fixture_json(root, "releases/oc_core_1_3_3/editorial/OC_CORE_1_3_3_ARTIFACT_INVENTORY.json", {"rows": []})
            self._write_fixture_json(root, "operations/project_control/LOGION_DIRTY_TREE_GOVERNANCE_LEDGER.json", {"public_unclassified_total": 0, "private_unknown_total": 0})
            script = root / "tools" / "materialize_oc_core_1_3_3_v12_closure.py"
            script.parent.mkdir(parents=True, exist_ok=True)
            script.write_text(
                "REPRODUCIBLE_GENERATED_OUTPUTS_TO_CLEAR = [\n"
                "    'releases/oc_core_1_3_3/artifacts/oc_core_1_3_3_no_send_release.zip',\n"
                "]\n",
                encoding="utf-8",
            )
            report = guard.build_report(root)
            self.assertEqual(report["state"], "FAIL")
            self.assertIn("COHERENCE-MATERIALIZER-PACKAGE-OWNERSHIP", {row["issue_id"] for row in report["issues"]})

    def test_logion_process_coherence_guard_blocks_stale_root_metadata(self) -> None:
        guard = _load_process_coherence_guard_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            package = root / "releases" / "oc_core_1_3_3" / "artifacts" / "oc_core_1_3_3_no_send_release.zip"
            package.parent.mkdir(parents=True, exist_ok=True)
            package.write_bytes(b"zip")
            self._write_fixture_json(root, "releases/oc_core_1_3_3/editorial/OC_CORE_1_3_3_RELEASE_SCORECARD_latest.json", {"summary": {"release_state": "OC_CORE_1_3_3_EXTERNAL_REVIEW_READY_NO_SEND", "all_domain_ready_no_send": False}})
            self._write_fixture_json(root, "releases/oc_core_1_3_3/editorial/OC_CORE_1_3_3_PUBLISH_MANIFEST_DRAFT.json", {"publish_allowed": False, "journal_submissions_allowed": False, "owner_approved": False})
            self._write_fixture_json(root, "releases/oc_core_1_3_3/editorial/OWNER_RELEASE_APPROVAL_v1.3.3.json", {"decision": "PENDING", "publish_allowed": False})
            self._write_fixture_json(root, "releases/oc_core_1_3_3/submission_packages/SUBMISSION_PACKAGE_INDEX.json", {"submission_allowed": False, "journal_submissions_allowed": False})
            self._write_fixture_json(root, "releases/oc_core_1_3_3/editorial/OC_CORE_1_3_3_ZIP_INTEGRITY_latest.json", {"package": "releases/oc_core_1_3_3/artifacts/oc_core_1_3_3_no_send_release.zip", "package_sha256": hashlib.sha256(b"zip").hexdigest()})
            self._write_fixture_json(root, "releases/oc_core_1_3_3/editorial/OC_CORE_1_3_3_ARTIFACT_INVENTORY.json", {"rows": []})
            self._write_fixture_json(root, "operations/project_control/LOGION_DIRTY_TREE_GOVERNANCE_LEDGER.json", {"public_unclassified_total": 0, "private_unknown_total": 0})
            for ref in guard.ROOT_NO_SEND_SURFACE_REFS:
                path = root / ref
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("OC Core 1.3.3 no-send review package\n", encoding="utf-8")
            (root / ".zenodo.json").write_text('{"version":"1.3.2"}\n', encoding="utf-8")
            report = guard.build_report(root)
            self.assertEqual(report["state"], "FAIL")
            self.assertIn("COHERENCE-ROOT-METADATA-STALE", {row["issue_id"] for row in report["issues"]})

    def _write_grand_science_loop_fixture(self, root: Path) -> Path:
        mission_dir = root / "operations" / "logion_release_mission" / "oc_core_1_3_3"
        mission_dir.mkdir(parents=True, exist_ok=True)
        obligations = [
            {
                "obligation_id": "OC133-GRAND-FORMAL-001",
                "owner_capability": "Research/FormalScience",
                "title": "Formal fixture",
                "blocker_check": "grand_toe_claim_ledger_evidence",
                "artifact_exists_is_not_closure": True,
                "no_send": True,
            },
            {
                "obligation_id": "OC133-GRAND-EMPIRICAL-001",
                "owner_capability": "Research/EmpiricalScience",
                "title": "Empirical fixture",
                "blocker_check": "grand_toe_empirical_superiority",
                "artifact_exists_is_not_closure": True,
                "no_send": True,
            },
            {
                "obligation_id": "OC133-GRAND-PRIORART-001",
                "owner_capability": "Research/PriorArt",
                "title": "Prior-art fixture",
                "blocker_check": "modern_science_comparator_superiority",
                "artifact_exists_is_not_closure": True,
                "no_send": True,
            },
        ]
        self._write_fixture_json(
            root,
            "operations/logion_release_mission/oc_core_1_3_3/OC133_GRAND_SCIENCE_RESEARCH_PROGRAM.json",
            {
                "schema_id": "OC133_GRAND_SCIENCE_RESEARCH_PROGRAM_v1",
                "release_id": "oc_core_1_3_3",
                "version": "1.3.3",
                "blocker_ids": [
                    "grand_toe_claim_ledger_evidence",
                    "grand_toe_empirical_superiority",
                    "modern_science_comparator_superiority",
                ],
                "checks": {
                    "grand_toe_claim_ledger_evidence": {"state": "FAIL"},
                    "grand_toe_empirical_superiority": {"state": "FAIL"},
                    "modern_science_comparator_superiority": {"state": "FAIL"},
                },
                "all_obligations": obligations,
                "no_send": True,
                "publish_allowed": False,
                "journal_submissions_allowed": False,
            },
        )
        self._write_fixture_json(
            root,
            "operations/logion_release_mission/oc_core_1_3_3/OC133_ALL_DOMAIN_READINESS_SCORECARD.json",
            {
                "blocker_ids": [
                    "grand_toe_claim_ledger_evidence",
                    "grand_toe_empirical_superiority",
                    "modern_science_comparator_superiority",
                ],
                "all_domain_ready_no_send": False,
                "no_send": True,
                "publish_allowed": False,
                "journal_submissions_allowed": False,
            },
        )
        return mission_dir

    def _make_bounded_grand_ambition_fixture(self, root: Path) -> None:
        component_files = [
            "SUBMISSION_PACKAGE.json",
            "REQUIRED_COMPONENT_MANIFEST.json",
            "REQUIRED_COMPONENT_MANIFEST.md",
            "COVER_LETTER_DRAFT.md",
            "CHECKLIST.md",
            "REPRODUCIBILITY_AND_DATA_STATEMENT.md",
            "AI_ASSISTANCE_DISCLOSURE.md",
            "CONFLICT_AND_FUNDING_STATEMENT.md",
            "VENUE_FIT_VERDICT.md",
        ]
        venues = [f"VENUE_{idx:02d}" for idx in range(1, 9)]
        for venue in venues:
            venue_dir = root / "releases" / "oc_core_1_3_3" / "submission_packages" / venue
            venue_dir.mkdir(parents=True, exist_ok=True)
            for filename in component_files:
                (venue_dir / filename).write_text("owner-review no-send fixture\n", encoding="utf-8")
        self._write_fixture_json(
            root,
            "releases/oc_core_1_3_3/submission_packages/SUBMISSION_PACKAGE_INDEX.json",
            {
                "release_id": "oc_core_1_3_3",
                "version": "1.3.3",
                "package_total": 8,
                "recommended_package_total": 2,
                "no_send": True,
                "submission_allowed": False,
                "journal_submissions_allowed": False,
                "package_status_counts": {"OWNER_REVIEW_READY_NO_SEND": 8},
                "rows": [
                    {
                        "venue_id": venue,
                        "package_status": "OWNER_REVIEW_READY_NO_SEND",
                        "submission_allowed": False,
                        "journal_submissions_allowed": False,
                    }
                    for venue in venues
                ],
            },
        )

        rows = []
        for idx, domain in enumerate(oc133_platinum.REQUIRED_EMPIRICAL_DOMAINS, start=1):
            snapshot = f"data/target_blind/{domain}.snapshot.json"
            self._write_fixture_json(root, snapshot, {"domain": domain, "fixture": idx})
            rows.append(
                {
                    "claim_id": f"TB-{domain.upper()}",
                    "lane": domain,
                    "dataset_snapshot_ref": snapshot,
                    "target_blind_split": "heldout_fixture",
                    "formula": "x + 1",
                    "predicted_value": idx + 1,
                    "observed_value": idx + 1,
                    "uncertainty": 0.1,
                    "comparator_baseline": "modern_science_baseline_fixture",
                    "comparator_prediction": idx + 2,
                    "residual": 0.0,
                    "comparator_residual": 1.0,
                    "negative_control": "permuted_labels",
                    "negative_control_rejected": True,
                    "falsifier": "residual_exceeds_uncertainty",
                    "snapshot_sha256": "0" * 64,
                    "replay_hash": "1" * 64,
                    "support_scope": "bounded_target_blind_all_domain_evidence_not_toe_or_modern_science_certification",
                    "prediction_support_allowed": True,
                    "empirical_support_allowed": True,
                }
            )
        self._write_fixture_json(
            root,
            "validation/target_blind/OC133_TARGET_BLIND_PREDICTION_TABLE.json",
            {
                "generated_by": "LOGION_CAPABILITY_WORKER",
                "capability_owner": "Research/EmpiricalScience",
                "failure_total": 0,
                "grand_scientific_ambition": True,
                "requested_ambition_level": "numerically proven TOE across all domains and better than modern science",
                "evidence_scope": "bounded_target_blind_all_domain_evidence_only",
                "rows": rows,
            },
        )
        self._write_fixture_json(
            root,
            "reports/OC_CORE_1_3_3_DOMAIN_VALIDATION_REPORT.json",
            {
                "domain_validation_promoted": False,
                "broad_domain_validation_promoted": False,
                "grand_scientific_ambition": True,
                "requested_ambition_level": "better than modern science",
                "evidence_scope": "bounded_target_blind_all_domain_evidence_only",
            },
        )
        self._write_fixture_json(root, "claims/CLAIM_LEDGER_1_3_3.json", {"unsupported_promoted_total": 0})
        self._write_fixture_json(
            root,
            "proofs/THEOREM_INVENTORY_1_3_3.json",
            {"theorem_total": 1, "machine_checked_subset_total": 1, "scientific_promotion_allowed_total": 1},
        )
        self._write_fixture_json(
            root,
            "reviews/oc133_llm_cerberus/OC133_LLM_CERBERUS_SUMMARY.json",
            {"critical_open_total": 0, "high_open_total": 0, "parse_failure_total": 0, "execution_bad_total": 0},
        )

    def _make_mathematics_formal_support_fixture(
        self,
        root: Path,
        *,
        allowed: bool = True,
        include_refs: bool = True,
        high_open_total: int = 0,
        stale_report_hash: bool = False,
    ) -> None:
        theorem_ids = ["T-MATH-FORMAL-1"] if include_refs else []
        proof_refs = ["proofs/proof_sheets/T-MATH-FORMAL-1.md"] if include_refs else []
        lean_refs = ["formal/lean/OC133V12.lean::math_formal_fixture"] if include_refs else []
        finite_refs = ["FM-MATH-FORMAL-POS", "FM-MATH-FORMAL-NEG"] if include_refs else []
        for proof_ref in proof_refs:
            (root / proof_ref).parent.mkdir(parents=True, exist_ok=True)
            (root / proof_ref).write_text("# Fixture proof\n", encoding="utf-8")
        if lean_refs:
            (root / "formal/lean").mkdir(parents=True, exist_ok=True)
            (root / "formal/lean/OC133V12.lean").write_text("theorem math_formal_fixture : True := by trivial\n", encoding="utf-8")

        pack = {
            "schema_id": "OC133_FORMAL_SUPPORT_EVIDENCE_v1",
            "release_id": "oc_core_1_3_3",
            "capability_owner": "Research/FormalScience",
            "domain": "mathematics",
            "support_route": "formal",
            "formal_support_allowed": allowed,
            "formal_support_verdict": "FORMAL_SUPPORT_ACCEPTED" if allowed else "FORMAL_SUPPORT_BLOCKED",
            "empirical_support_allowed": False,
            "grand_empirical_support_allowed": False,
            "theorem_ids": theorem_ids,
            "proof_sheet_refs": proof_refs,
            "lean_refs": lean_refs,
            "finite_case_ids": finite_refs,
            "blockers": [] if allowed else ["FORMAL_ROUTE_BLOCKED"],
            "high_open_total": high_open_total,
        }
        pack_ref = "validation/heldout/grand_science/mathematics/mathematics_candidate_evidence_pack.json"
        self._write_fixture_json(root, pack_ref, pack)
        pack_sha256 = oc133_platinum.sha256_object(pack)

        report_row = {
            "domain": "mathematics",
            "status": "FORMAL_SUPPORT_ACCEPTED" if allowed else "BLOCKED_PENDING_MATHEMATICS_FORMAL_EVIDENCE_REPAIR",
            "candidate_pack_ref": pack_ref,
            "candidate_pack_sha256": pack_sha256,
            "support_route": "formal",
            "formal_support_allowed": allowed,
            "formal_support_verdict": "FORMAL_SUPPORT_ACCEPTED" if allowed else "FORMAL_SUPPORT_BLOCKED",
            "empirical_support_allowed": False,
            "formal_theorem_ids": theorem_ids,
            "formal_proof_sheet_refs": proof_refs,
            "formal_lean_refs": lean_refs,
            "formal_finite_case_ids": finite_refs,
            "blockers": [] if allowed else ["FORMAL_ROUTE_BLOCKED"],
            "high_open_total": high_open_total,
        }
        report = {
            "schema_id": "OC133_MATHEMATICS_FORMAL_EVIDENCE_EXECUTION_REPORT_v3",
            "release_id": "oc_core_1_3_3",
            "version": "1.3.3",
            "capability_owner": "Research/FormalScience",
            "formal_support_allowed_total": 1 if allowed else 0,
            "valid_under_executor_total": 1 if allowed else 0,
            "valid_pack_total": 1 if allowed else 0,
            "blocked_pack_total": 0 if allowed else 1,
            "blocked_domain_total": 0 if allowed else 1,
            "domains": [report_row],
            "verdict": "MATHEMATICS_FORMAL_SUPPORT_ROUTE_READY" if allowed else "BLOCKED_PENDING_MATHEMATICS_FORMAL_EVIDENCE",
            "empirical_grand_gate_verdict": "REJECTED_FORMAL_ONLY_NOT_EMPIRICAL",
            "route_separation_policy": "Formal mathematics support is audited separately from grand empirical support.",
            "high_open_total": high_open_total,
        }
        report["report_sha256"] = (
            "f" * 64 if stale_report_hash else oc133_platinum.sha256_object(report)
        )
        self._write_fixture_json(
            root,
            "validation/heldout/grand_science/mathematics/OC133_MATHEMATICS_EVIDENCE_EXECUTION_REPORT.json",
            report,
        )

    def _make_strict_grand_empirical_report_fixture(
        self,
        root: Path,
        *,
        allowed: bool = True,
        missing_domain: str | None = None,
        missing_hash_domain: str | None = None,
    ) -> None:
        domains = [domain for domain in oc133_platinum.REQUIRED_EMPIRICAL_DOMAINS if domain != missing_domain]
        domain_rows = []
        candidate_rows = []
        for idx, domain in enumerate(domains, start=1):
            pack_ref = f"validation/heldout/grand_science/{domain}/fixture/{domain}_strict_pack.json"
            pack = {
                "schema_id": "OC133_GRAND_EMPIRICAL_EVIDENCE_v1",
                "release_id": "oc_core_1_3_3",
                "domain": domain,
                "evidence_pack_id": f"STRICT-{domain.upper()}",
                "n": 20 + idx,
                "source_separation": {"mode": "target_blind"},
                "grand_toe_support_allowed": allowed,
                "residuals": {"model": 0.1, "comparator": 1.0, "superiority_margin": 0.9},
            }
            self._write_fixture_json(root, pack_ref, pack)
            pack_sha256 = oc133_platinum.sha256_object(pack)
            candidate_sha256 = "" if domain == missing_hash_domain else pack_sha256
            domain_allowed = allowed and domain != missing_hash_domain
            domain_rows.append(
                {
                    "domain": domain,
                    "valid_pack_total": 1 if domain_allowed else 0,
                    "valid_pack_refs": [pack_ref],
                    "valid_n": 20 + idx,
                    "minimum_n": 20,
                    "bounded_baseline_row_total": 1,
                    "bounded_baseline_refs": [f"OC133-TARGETBLIND-{domain.upper()}-001"],
                    "grand_toe_support_allowed": domain_allowed,
                    "status": "EVIDENCE_SUFFICIENT_PENDING_REVIEW" if domain_allowed else "BLOCKED",
                    "blockers": [] if domain_allowed else ["STRICT_FIXTURE_BLOCKED"],
                }
            )
            candidate_rows.append(
                {
                    "source_ref": pack_ref,
                    "evidence_pack_id": f"STRICT-{domain.upper()}",
                    "domain": domain,
                    "formal_only_pack": False,
                    "n": 20 + idx,
                    "grand_toe_support_allowed": domain_allowed,
                    "candidate_sha256": candidate_sha256,
                    "valid_for_grand_support": domain_allowed,
                    "failure_total": 0 if domain_allowed else 1,
                    "failures": [] if domain_allowed else ["STRICT_FIXTURE_BLOCKED"],
                    "supersession_status": "current",
                    "selected_for_domain_support": True,
                }
            )

        blocked_total = 0 if allowed and missing_domain is None and missing_hash_domain is None else 1
        report = {
            "schema_id": "OC133_GRAND_EMPIRICAL_REPORT_v1",
            "release_id": "oc_core_1_3_3",
            "version": "1.3.3",
            "empirical_required_domains": list(oc133_platinum.REQUIRED_EMPIRICAL_DOMAINS),
            "required_domains": list(oc133_platinum.REQUIRED_EMPIRICAL_DOMAINS),
            "formal_required_domains": ["mathematics"],
            "formal_route_status": [
                {
                    "domain": "mathematics",
                    "support_route": "formal",
                    "status": "ROUTED_TO_FORMAL_SUPPORT",
                    "empirical_support_allowed": False,
                    "grand_empirical_support_allowed": False,
                }
            ],
            "candidate_rows": candidate_rows,
            "domains": domain_rows,
            "blocked_domain_total": blocked_total,
            "blocked_empirical_domain_total": blocked_total,
            "registry_failure_total": 0,
            "valid_evidence_pack_total": len(domains) if blocked_total == 0 else len(domains) - 1,
            "evidence_pack_total": len(domains),
            "grand_toe_support_allowed": blocked_total == 0,
            "domain_predictive_superiority_supported": blocked_total == 0,
            "verdict": "GRAND_EMPIRICAL_SUPPORT_ALLOWED" if blocked_total == 0 else "BLOCKED_PENDING_GENUINE_PER_DOMAIN_EVIDENCE",
        }
        self._write_fixture_json(root, oc133_platinum.GRAND_EMPIRICAL_REPORT_REL, report)

    def test_fake_pass_prevention(self) -> None:
        with self.assertRaises(ValueError):
            core.gate_result("gate_x", "fake", "PASS", executed=False)

    def test_current_release_resolver_tracks_active_branch(self) -> None:
        root = complete.repo_root()
        identity = versioning.current_release(root)
        self.assertEqual(identity.release_id, "oc_core_1_3_3")
        self.assertEqual(identity.version, "1.3.3")
        self.assertIn(identity.source.split(":", 1)[0], {"git_branch", "marker", "root_version", "latest_release_dir"})
        self.assertEqual(versioning.release_id_from_version(identity.version), identity.release_id)
        self.assertEqual(release_machine.__version__, identity.version)

    def test_current_release_env_override_requires_explicit_unlock(self) -> None:
        root = complete.repo_root()
        old = {name: os.environ.get(name) for name in ("OC_RELEASE_ID", "OC_RELEASE_VERSION", versioning.ENV_OVERRIDE_UNLOCK)}
        try:
            os.environ["OC_RELEASE_ID"] = "oc_core_1_3_2"
            os.environ.pop("OC_RELEASE_VERSION", None)
            os.environ.pop(versioning.ENV_OVERRIDE_UNLOCK, None)
            locked = versioning.current_release(root)
            self.assertEqual(locked.release_id, "oc_core_1_3_3")
            self.assertNotEqual(locked.source, "env:OC_RELEASE_ID")

            os.environ[versioning.ENV_OVERRIDE_UNLOCK] = "1"
            unlocked = versioning.current_release(root)
            self.assertEqual(unlocked.release_id, "oc_core_1_3_2")
            self.assertEqual(unlocked.version, "1.3.2")
            self.assertEqual(unlocked.source, "env:OC_RELEASE_ID")
        finally:
            for name, value in old.items():
                if value is None:
                    os.environ.pop(name, None)
                else:
                    os.environ[name] = value

    def test_oc133_grand_science_loop_round_robins_open_obligations(self) -> None:
        module = _load_grand_science_loop_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_grand_science_loop_fixture(root)
            calls: list[list[str]] = []

            def fake_runner(cmd: list[str], timeout: int) -> dict:
                calls.append(cmd)
                return {"cmd": cmd, "returncode": 0, "stdout_tail": "", "stderr_tail": ""}

            first = module.run_loop(root, max_obligations=1, runner=fake_runner)
            second = module.run_loop(root, max_obligations=1, runner=fake_runner)

            self.assertEqual(first["selected_obligation_ids"], ["OC133-GRAND-FORMAL-001"])
            self.assertEqual(second["selected_obligation_ids"], ["OC133-GRAND-EMPIRICAL-001"])
            self.assertEqual(first["next_cursor_obligation_id"], "OC133-GRAND-EMPIRICAL-001")
            self.assertEqual(second["next_cursor_obligation_id"], "OC133-GRAND-PRIORART-001")
            self.assertEqual(len(calls), 2)

    def test_oc133_grand_science_loop_reuses_all_domain_dispatch_order_when_present(self) -> None:
        module = _load_grand_science_loop_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_grand_science_loop_fixture(root)
            self._write_fixture_json(
                root,
                "operations/logion_release_mission/oc_core_1_3_3/OC133_ALL_DOMAIN_WORK_ORDERS.json",
                {
                    "queue_sha256": "dispatch-fixture-v1",
                    "rows": [
                        {"work_order_id": "OC133-PLATINUM-WO-002", "owner_capability": "Research/EmpiricalScience"},
                        {"work_order_id": "OC133-PLATINUM-WO-003", "owner_capability": "Research/PriorArt"},
                        {"work_order_id": "OC133-PLATINUM-WO-001", "owner_capability": "Research/FormalScience"},
                    ]
                },
            )
            self._write_fixture_json(
                root,
                "operations/logion_release_mission/oc_core_1_3_3/OC133_GRAND_SCIENCE_LOOP_STATE.json",
                {
                    "next_cursor_obligation_id": "OC133-GRAND-FORMAL-001",
                    "dispatch_queue_sha256": "stale-dispatch",
                },
            )

            def fake_runner(cmd: list[str], timeout: int) -> dict:
                return {"cmd": cmd, "returncode": 0, "stdout_tail": "", "stderr_tail": ""}

            first = module.run_loop(root, max_obligations=1, runner=fake_runner)
            self.assertEqual(first["selected_obligation_ids"], ["OC133-GRAND-EMPIRICAL-001"])
            self.assertEqual(first["next_cursor_obligation_id"], "OC133-GRAND-PRIORART-001")

    def test_oc133_grand_science_loop_blocks_pass_while_all_domain_blockers_remain(self) -> None:
        module = _load_grand_science_loop_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            mission_dir = self._write_grand_science_loop_fixture(root)

            def fake_runner(cmd: list[str], timeout: int) -> dict:
                return {"cmd": cmd, "returncode": 0, "stdout_tail": "profile PASS", "stderr_tail": ""}

            result = module.run_loop(root, runner=fake_runner)

            self.assertEqual(result["verdict"], "SCIENTIFIC_BLOCKERS_REMAIN")
            self.assertEqual(result["all_domain_blocker_total_after"], 3)
            self.assertFalse(result["publish_allowed"])
            self.assertFalse(result["journal_submissions_allowed"])
            self.assertTrue(result["no_send"])
            self.assertTrue((mission_dir / "OC133_GRAND_SCIENCE_LOOP_STATE.json").exists())
            self.assertTrue((mission_dir / "OC133_GRAND_SCIENCE_LOOP_latest.json").exists())

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
        self.assertIn(summary["release_state"], {"RELEASE_READY_NO_SEND", "REMEDIATION_REQUIRED"})
        self.assertFalse(summary["publish_allowed"])
        self.assertTrue(summary["owner_approval_required"])
        if summary["release_state"] == "REMEDIATION_REQUIRED":
            self.assertEqual(summary["master_verdict"], "FAIL")
            self.assertGreater(summary["gate_counts"].get("FAIL", 0), 0)

    def test_completed_gate_set_records_terminal_science_and_keeps_no_send_lock(self) -> None:
        summary = core.evaluate_release("oc_core_1_3_2", "all", "pre_publish", write=True)
        self.assertIn(summary["master_verdict"], {"PASS", "FAIL"})
        if summary["master_verdict"] == "PASS":
            self.assertEqual(summary["gate_counts"]["PASS"], 32)
            self.assertEqual(summary["gate_counts"].get("FAIL", 0), 0)
        else:
            self.assertEqual(summary["release_state"], "REMEDIATION_REQUIRED")
            self.assertGreater(summary["gate_counts"].get("FAIL", 0), 0)
        self.assertFalse(summary["publish_allowed"])
        scorecard = json.loads((complete.repo_root() / "releases/oc_core_1_3_2/editorial/OC_CORE_1_3_2_RELEASE_SCORECARD_latest.json").read_text(encoding="utf-8"))
        g28 = next(row for row in scorecard["gate_results"] if row["gate_id"] == "G28")
        self.assertEqual(g28["name"], "science_terminality_82")
        self.assertEqual(g28["details"]["open_blocker_total"], 0)
        self.assertEqual(g28["details"]["terminal_blocker_total"], 82)
        g29 = next(row for row in scorecard["gate_results"] if row["gate_id"] == "G29")
        self.assertEqual(g29["name"], "release_human_quality")
        self.assertEqual(g29["state"], "PASS")
        g30 = next(row for row in scorecard["gate_results"] if row["gate_id"] == "G30")
        self.assertEqual(g30["name"], "platinum_science_readiness")
        self.assertEqual(g30["state"], "PASS")
        self.assertEqual(g30["details"]["benchmark_failure_total"], 0)
        self.assertEqual(g30["details"]["minimality_witness_row_total"], 8)
        g31 = next(row for row in scorecard["gate_results"] if row["gate_id"] == "G31")
        self.assertEqual(g31["name"], "llm_readability_integrity")
        self.assertEqual(g31["state"], "PASS")

    def test_missing_swhid_is_owner_action_not_invented_identifier(self) -> None:
        root = complete.repo_root()
        payload = json.loads((root / "releases/oc_core_1_3_2/editorial/OC_CORE_1_3_2_PUBLISH_MANIFEST_DRAFT.json").read_text(encoding="utf-8"))
        swh = payload["software_heritage"]
        self.assertEqual(swh["policy"], "EXISTING_ONLY")
        if swh["swhid"] is None:
            self.assertEqual(swh["status"], "owner_action_required")
            self.assertTrue(swh["owner_exception_required_for_publish"])

    def test_zip_manifest_and_checksums_are_consistent(self) -> None:
        root = complete.repo_root()
        manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
        checksums = (root / "checksums.txt").read_text(encoding="utf-8")
        zip_path = root / "releases/oc_core_1_3_2/artifacts/oc_core_1_3_2_zenodo_release.zip"
        with zipfile.ZipFile(zip_path) as zf:
            names = set(zf.namelist())
        self.assertIn("manifest.json", names)
        self.assertIn("checksums.txt", names)
        for row in manifest["files"][:25]:
            self.assertIn(row["path"], names)
            self.assertIn(row["sha256"], checksums)

    def test_package_zip_reuses_existing_content_addressed_archive(self) -> None:
        root = Path(self._testMethodName)
        root.mkdir(exist_ok=True)
        try:
            source = root / "source.txt"
            source.write_text("alpha\n", encoding="utf-8")
            (root / "manifest.json").write_text('{"files":[]}\n', encoding="utf-8")
            (root / "checksums.txt").write_text("fixture\n", encoding="utf-8")
            entry = complete.BundleEntry("payload/source.txt", source, "fixture")

            first = complete.build_zip(root, [entry])
            second = complete.build_zip(root, [entry])

            self.assertFalse(first["reused"])
            self.assertTrue(second["reused"])
            self.assertEqual(first["sha256"], second["sha256"])
        finally:
            import shutil

            shutil.rmtree(root, ignore_errors=True)

    def test_release_machine_lock_recovers_from_stale_pid(self) -> None:
        root = Path(self._testMethodName)
        lock_dir = root / "release_machine"
        lock_dir.mkdir(parents=True, exist_ok=True)
        lock_path = lock_dir / ".release_machine.lock"
        lock_path.write_text("pid=999999999\nts=0\n", encoding="utf-8")
        try:
            with complete.release_machine_lock(root, timeout_seconds=1.0):
                self.assertTrue(lock_path.exists())
                self.assertIn(f"pid={os.getpid()}", lock_path.read_text(encoding="utf-8"))
            self.assertFalse(lock_path.exists())
        finally:
            import shutil

            shutil.rmtree(root, ignore_errors=True)

    def test_research_packets_are_bounded_no_send_material(self) -> None:
        root = complete.repo_root()
        audit = json.loads((root / "releases/oc_core_1_3_2/editorial/research_packets/PUBLIC_RESEARCH_PACKET_AUDIT_v1.json").read_text(encoding="utf-8"))
        self.assertGreaterEqual(audit["packet_total"], 1)
        self.assertEqual(audit["packet_total"], audit["pass_total"])
        self.assertFalse(audit["canonical_claim_ledger_change"])

    def test_v132_tag_is_backed_by_publication_report_and_publish_lock(self) -> None:
        root = complete.repo_root()
        tag = subprocess.run(
            ["git", "show-ref", "--verify", "--quiet", "refs/tags/v1.3.2"],
            cwd=root,
            text=True,
            capture_output=True,
            timeout=30,
        )
        self.assertEqual(tag.returncode, 0)
        report = json.loads((root / "releases/oc_core_1_3_2/editorial/PUBLICATION_EXECUTION_REPORT_latest.json").read_text(encoding="utf-8"))
        self.assertEqual(report["state"], "PUBLISHED")
        self.assertIn("github.com", report["github_release_url"])
        self.assertIn("zenodo.org", report["zenodo_record_url"])
        manifest = json.loads((root / "releases/oc_core_1_3_2/editorial/OC_CORE_1_3_2_PUBLISH_MANIFEST_DRAFT.json").read_text(encoding="utf-8"))
        self.assertFalse(manifest["publish_allowed"])
        self.assertTrue(manifest["global_no_send_lock"])

    def test_primary_pdfs_are_substantive_bound_artifacts_not_templates(self) -> None:
        root = complete.repo_root()
        core.evaluate_release("oc_core_1_3_2", "all", "dry-run", write=True)
        quality = json.loads((root / "releases/oc_core_1_3_2/editorial/OC_CORE_1_3_2_PDF_QUALITY_latest.json").read_text(encoding="utf-8"))
        self.assertEqual(quality["summary"]["pdf_total"], 6)
        self.assertEqual(quality["summary"]["nonpublic_template_or_bad_total"], 0)
        for row in quality["rows"]:
            self.assertGreaterEqual(row["bytes"], complete.MIN_SUBSTANTIVE_PDF_BYTES)
            self.assertTrue(row["starts_with_pdf_header"])
            self.assertGreaterEqual(row["page_estimate"], complete.MIN_SUBSTANTIVE_PDF_PAGES)
            self.assertTrue(
                row["source"].startswith("releases/oc_core_1_3/")
                or row["source"].startswith("releases/oc_core_1_3_2/pdf_sources/")
            )
            self.assertEqual(row.get("text_quality_findings"), [])

    def test_science_terminality_rows_are_release_traceable(self) -> None:
        root = complete.repo_root()
        core.evaluate_release("oc_core_1_3_2", "all", "dry-run", write=True)
        scorecard = json.loads((root / "releases/oc_core_1_3_2/editorial/OC_CORE_1_3_2_RELEASE_SCORECARD_latest.json").read_text(encoding="utf-8"))
        g28 = next(row for row in scorecard["gate_results"] if row["gate_id"] == "G28")
        self.assertEqual(g28["details"]["row_completeness_gap_total"], 0)
        ledger = json.loads((root / "releases/oc_core_1_3_2/editorial/OC_CORE_1_3_2_SCIENCE_BLOCKER_CLOSURE_LEDGER_latest.json").read_text(encoding="utf-8"))
        self.assertEqual(len(ledger["blocker_rows"]), 82)
        for row in ledger["blocker_rows"]:
            self.assertTrue(row["axis"])
            self.assertTrue(row["support_class"])
            self.assertTrue(row["evidence_refs"])
            self.assertTrue(row["manuscript_refs"])
            self.assertTrue(row["release_refs"])
            self.assertTrue(row["terminality_rationale"])
        self.assertEqual(ledger["summary"]["claim_demotion_used_total"], 0)

    def test_support_map_and_package_composition_are_human_quality(self) -> None:
        root = complete.repo_root()
        core.evaluate_release("oc_core_1_3_2", "all", "dry-run", write=True)
        support = json.loads((root / "releases/oc_core_1_3_2/editorial/OC_CORE_1_3_2_PREDICTION_AND_PROMOTION_SUPPORT_MAP_latest.json").read_text(encoding="utf-8"))
        self.assertGreater(support["summary"]["strong_claim_row_total"], 0)
        self.assertEqual(support["summary"]["unsupported_promoted_total"], 0)
        manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
        forbidden_source_pdfs = [
            row["path"]
            for row in manifest["files"]
            if (
                row["path"].startswith("source_material/releases/oc_core_1_3/journal_core/")
                or row["path"].startswith("source_material/releases/oc_core_1_3/manuscripts/")
            )
            and row["path"].endswith(".pdf")
        ]
        self.assertEqual(forbidden_source_pdfs, [])

    def test_release_human_quality_blocks_overclaim_and_unqualified_ceiling(self) -> None:
        findings = complete.human_quality_findings_for_text(
            "What It Proves\nThis release widens claim ceilings and says all gaps solved.",
            "primary_pdfs/fixture.pdf",
            role="primary_pdf",
        )
        self.assertEqual({row["kind"] for row in findings}, {"overclaim_title", "unqualified_claim_ceiling_language", "all_gaps_solved_language"})

    def test_release_human_quality_allows_negated_or_diagnostic_context(self) -> None:
        negated = complete.human_quality_findings_for_text(
            "This package does not claim unrestricted prediction and must not be framed as TOE-complete or final theory.",
            "releases/oc_core_1_3_2/editorial/fixture.md",
        )
        diagnostic = complete.human_quality_findings_for_text(
            "Replaced 'What It Proves' and old claim ceiling wording.",
            "releases/oc_core_1_3_2/editorial/OC_CORE_1_3_2_RELEASE_QUALITY_FAILURE_ANALYSIS.md",
        )
        self.assertEqual(negated, [])
        self.assertEqual(diagnostic, [])

    def test_boundary_gate_blocks_private_review_archive_labels(self) -> None:
        hits = complete.boundary_hits_for_text(
            "source_filename: claude_feedback/predictive.md",
            "releases/oc_core_1_3_2/editorial/research_packets/fixture/PUBLIC_SOURCE_MANIFEST.yaml",
        )
        self.assertIn("private_review_archive_label", {row["kind"] for row in hits})

    def test_acknowledgement_registry_sorted_and_no_endorsement(self) -> None:
        root = complete.repo_root()
        core.evaluate_release("oc_core_1_3_2", "all", "dry-run", write=True)
        details = complete.acknowledgement_gate_details(root)
        self.assertTrue(details["ok"])
        self.assertEqual(details["observed_names"], [
            "G. V. Apostolov",
            "Eduard Fadeev",
            "Gennady Alekseevich Nosov",
            "Sergey Shpadyrev",
            "Stanislav Tsukrov",
        ])
        self.assertTrue(details["author_owner_separate"])
        self.assertEqual(details["endorsement_violation_names"], [])

    def test_legacy_placeholder_pdf_generation_is_disabled_for_v132(self) -> None:
        self.assertTrue(core.LEGACY_PLACEHOLDER_PDF_GENERATION_DISABLED)

    def test_platinum_science_gate_tracks_benchmarks_and_minimality(self) -> None:
        root = complete.repo_root()
        core.evaluate_release("oc_core_1_3_2", "all", "dry-run", write=True)
        scorecard = json.loads((root / "releases/oc_core_1_3_2/editorial/OC_CORE_1_3_2_RELEASE_SCORECARD_latest.json").read_text(encoding="utf-8"))
        g30 = next(row for row in scorecard["gate_results"] if row["gate_id"] == "G30")
        self.assertEqual(g30["state"], "PASS")
        self.assertEqual(g30["details"]["benchmark_task_total"], 10)
        self.assertEqual(g30["details"]["benchmark_failure_total"], 0)
        self.assertEqual(g30["details"]["benchmark_accepted_baseline_total"], 9)
        self.assertEqual(g30["details"]["no_signalling_violation_score_max"], 0.0)
        self.assertEqual(g30["details"]["minimality_theorem_status"], "PROVED_FOR_OC_VERDICT_CLASS")
        self.assertEqual(g30["details"]["unsafe_direct_promotion_total"], 0)

    def test_llm_readability_gate_is_claim_bounded(self) -> None:
        root = complete.repo_root()
        publication.generate_llm_readability(root)
        gate = publication.llm_readability_gate(root)
        self.assertEqual(gate["state"], "PASS")
        self.assertEqual(gate["details"]["unsupported_promoted_total"], 0)

    def test_public_release_presentation_has_navigation_metadata_and_assets(self) -> None:
        root = complete.repo_root()
        payload = publication.build_public_release_presentation(root)
        body = payload["github_release_body"]
        self.assertIn("## Table Of Contents", body)
        self.assertIn("## Separate PDF Files", body)
        self.assertIn("OC_CORE_1_3_2_MASTER_MONOGRAPH_EN.pdf", body)
        self.assertIn("oc_core_1_3_2_zenodo_release.zip", body)
        self.assertIn("#OntologyOfContinua", body)
        self.assertIn("LLM-readable science", payload["groups"])
        self.assertIn("reproducible research", payload["keywords"])
        self.assertTrue(all(row["exists"] for row in payload["assets"]))

    def test_journal_submission_packages_are_review_ready_no_send(self) -> None:
        root = complete.repo_root()
        index = publication.generate_submission_packages(root, release_id=oc133.RELEASE_ID)
        self.assertEqual(index["release_id"], "oc_core_1_3_3")
        self.assertEqual(index["version"], "1.3.3")
        self.assertTrue(index["no_send"])
        self.assertFalse(index["submission_allowed"])
        self.assertTrue(index["owner_approval_required"])
        self.assertFalse(index["journal_submissions_allowed"])
        self.assertEqual(index["package_total"], 8)
        self.assertEqual(index["recommended_package_total"], 2)
        self.assertEqual(index["package_status_counts"], {"OWNER_REVIEW_READY_NO_SEND": 8})

        recommended = [row["venue_id"] for row in index["rows"] if row["submit_recommended"]]
        self.assertEqual(recommended, ["FOUNDATIONS_OF_SCIENCE", "SYNTHESE"])
        expected_artifact_roles = {"primary_manuscript", "supporting_monograph", "release_archive", "reader_guide"}
        expected_component_files = {
            "SUBMISSION_PACKAGE.json",
            "REQUIRED_COMPONENT_MANIFEST.json",
            "REQUIRED_COMPONENT_MANIFEST.md",
            "COVER_LETTER_DRAFT.md",
            "CHECKLIST.md",
            "REPRODUCIBILITY_AND_DATA_STATEMENT.md",
            "AI_ASSISTANCE_DISCLOSURE.md",
            "CONFLICT_AND_FUNDING_STATEMENT.md",
            "VENUE_FIT_VERDICT.md",
        }

        for row in index["rows"]:
            self.assertEqual(row["package_status"], "OWNER_REVIEW_READY_NO_SEND")
            self.assertTrue(row["no_send"])
            self.assertFalse(row["submission_allowed"])
            self.assertTrue(row["owner_approval_required"])
            self.assertFalse(row["journal_submissions_allowed"])
            self.assertEqual(row["doi_policy"]["status"], "PENDING_PUBLIC_RELEASE_AND_SEPARATE_OWNER_SUBMISSION_APPROVAL")
            self.assertFalse(row["doi_policy"]["journal_submission_doi_insert_allowed"])
            self.assertEqual({artifact["role"] for artifact in row["artifact_refs"]}, expected_artifact_roles)
            for artifact in row["artifact_refs"]:
                self.assertTrue(artifact["exists"], artifact["path"])
                self.assertTrue((root / artifact["path"]).exists(), artifact["path"])
                self.assertNotIn("oc_core_1_3_2", artifact["path"])
                self.assertNotIn("1_3_2", artifact["path"])
                if artifact["role"] == "release_archive":
                    self.assertEqual(artifact["sha256"], "")
                    self.assertEqual(artifact["checksum_ref"], "releases/oc_core_1_3_3/editorial/OC_CORE_1_3_3_ZIP_INTEGRITY_latest.json")
                    self.assertEqual(artifact["checksum_status"], "RECORDED_AFTER_PACKAGE_BUILD_TO_AVOID_SELF_REFERENCE")
                else:
                    self.assertEqual(len(artifact["sha256"]), 64)
            component_files = {Path(component["path"]).name for component in row["required_components"]}
            self.assertEqual(component_files, expected_component_files)
            for component in row["required_components"]:
                self.assertEqual(component["status"], "READY_NO_SEND")
                self.assertTrue((root / component["path"]).exists(), component["path"])

    def test_lrgef_state_records_no_send_external_blockers(self) -> None:
        root = complete.repo_root()
        summary = core.evaluate_release("oc_core_1_3_2", "all", "dry-run", write=True)
        state_text = (root / "releases/oc_core_1_3_2/editorial/LRGEF_RELEASE_STATE_latest.json").read_text(encoding="utf-8")
        state = json.loads(state_text)
        self.assertEqual(state["schema_id"], "LRGEF_RELEASE_STATE_v1")
        self.assertEqual(state["release_machine_state"], summary["release_state"])
        self.assertFalse(state["publish_allowed"])
        self.assertFalse(state["hard_green_external"])
        self.assertNotIn("SCIENCE_TERMINALITY_82_OPEN", state["external_publication_blockers"])
        self.assertIn("OWNER_APPROVAL_REQUIRED", state["external_publication_blockers"])
        self.assertIn("OWNER_APPROVAL_REQUIRED", state["external_publication_blockers"])
        self.assertGreaterEqual(state["k_R"], 0.85)
        self.assertNotIn("C:\\", state_text)
        self.assertNotIn("/Users/", state_text)
        self.assertTrue(all("path" not in row for row in state["toolchain"]["tools"].values()))

    def test_oc133_grand_science_ambition_blocks_bounded_evidence_certification(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._make_bounded_grand_ambition_fixture(root)

            audit = oc133_platinum.all_domain_readiness_audit(root, {"state": "PASS", "blocker_total": 0})

        empirical = audit["checks"]["all_domain_empirical_predictions"]
        self.assertEqual(empirical["state"], "PASS")
        self.assertEqual(empirical["missing_domain_total"], 0)
        self.assertEqual(set(empirical["passed_domains"]), set(oc133_platinum.REQUIRED_EMPIRICAL_DOMAINS))

        self.assertFalse(audit["all_domain_ready_no_send"])
        self.assertNotEqual(audit["final_readiness_state"], oc133_platinum.ALL_DOMAIN_READY_STATE)
        self.assertGreater(audit["blocker_total"], 0)
        ambition_checks = {
            key: row
            for key, row in audit["checks"].items()
            if "ambition" in key.lower()
            or "toe" in key.lower()
            or "modern_science" in key.lower()
            or "better_than_modern_science" in key.lower()
        }
        self.assertTrue(ambition_checks, audit["checks"].keys())
        self.assertTrue(any(row.get("state") != "PASS" for row in ambition_checks.values()))

        audit_text = json.dumps(audit, sort_keys=True).lower()
        self.assertIn("numerically proven toe", audit_text)
        self.assertIn("better than modern science", audit_text)
        self.assertIn("bounded", audit_text)
        self.assertIn("target", audit_text)
        grand_empirical = audit["checks"]["grand_toe_empirical_superiority"]
        self.assertEqual(grand_empirical["state"], "FAIL")
        self.assertFalse(grand_empirical["grand_empirical_report_exists"])
        self.assertEqual(
            set(grand_empirical["missing_or_not_superior_domains"]),
            set(oc133_platinum.REQUIRED_EMPIRICAL_DOMAINS),
        )
        self.assertEqual(
            set(grand_empirical["bounded_target_blind_diagnostics"]),
            set(oc133_platinum.REQUIRED_EMPIRICAL_DOMAINS),
        )

    def test_oc133_strict_grand_empirical_report_closes_empirical_blocker(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._make_bounded_grand_ambition_fixture(root)
            self._make_strict_grand_empirical_report_fixture(root)

            audit = oc133_platinum.all_domain_readiness_audit(root, {"state": "PASS", "blocker_total": 0})

        grand_empirical = audit["checks"]["grand_toe_empirical_superiority"]
        self.assertEqual(grand_empirical["state"], "PASS")
        self.assertEqual(grand_empirical["missing_or_not_superior_domains"], [])
        self.assertEqual(
            set(grand_empirical["grand_empirical_supported_domains"]),
            set(oc133_platinum.REQUIRED_EMPIRICAL_DOMAINS),
        )
        self.assertTrue(grand_empirical["grand_empirical_route_split_ok"])
        self.assertTrue(grand_empirical["grand_empirical_mathematics_formal_route_present"])
        self.assertNotIn("mathematics", grand_empirical["strict_domain_results"])
        self.assertEqual(
            set(grand_empirical["bounded_target_blind_diagnostics"]),
            set(oc133_platinum.REQUIRED_EMPIRICAL_DOMAINS),
        )
        for row in grand_empirical["strict_domain_results"].values():
            self.assertTrue(row["passes_strict_predictive_superiority"])
            self.assertTrue(row["selected_pack_refs_present"])
            self.assertTrue(row["selected_pack_hashes_valid"])
            self.assertTrue(row["selected_pack_refs_registered_valid"])

    def test_oc133_missing_or_blocked_grand_empirical_report_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._make_bounded_grand_ambition_fixture(root)
            self._make_strict_grand_empirical_report_fixture(root, allowed=False)

            blocked_audit = oc133_platinum.all_domain_readiness_audit(root, {"state": "PASS", "blocker_total": 0})

        blocked = blocked_audit["checks"]["grand_toe_empirical_superiority"]
        self.assertEqual(blocked["state"], "FAIL")
        self.assertFalse(blocked["grand_empirical_support_allowed"])
        self.assertGreater(blocked["grand_empirical_blocked_domain_total"], 0)

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._make_bounded_grand_ambition_fixture(root)
            self._make_strict_grand_empirical_report_fixture(root, missing_domain="physics")

            missing_domain_audit = oc133_platinum.all_domain_readiness_audit(root, {"state": "PASS", "blocker_total": 0})

        missing_domain = missing_domain_audit["checks"]["grand_toe_empirical_superiority"]
        self.assertEqual(missing_domain["state"], "FAIL")
        self.assertIn("physics", missing_domain["missing_or_not_superior_domains"])

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._make_bounded_grand_ambition_fixture(root)
            self._make_strict_grand_empirical_report_fixture(root, missing_hash_domain="chemistry")

            missing_hash_audit = oc133_platinum.all_domain_readiness_audit(root, {"state": "PASS", "blocker_total": 0})

        missing_hash = missing_hash_audit["checks"]["grand_toe_empirical_superiority"]
        self.assertEqual(missing_hash["state"], "FAIL")
        self.assertFalse(missing_hash["strict_domain_results"]["chemistry"]["selected_pack_hashes_valid"])

    def test_oc133_mathematics_empirical_absence_does_not_block_when_formal_route_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._make_bounded_grand_ambition_fixture(root)
            self._make_mathematics_formal_support_fixture(root)

            audit = oc133_platinum.all_domain_readiness_audit(root, {"state": "PASS", "blocker_total": 0})

        empirical = audit["checks"]["all_domain_empirical_predictions"]
        mathematics = audit["checks"]["mathematics_formal_support"]
        self.assertEqual(empirical["state"], "PASS")
        self.assertNotIn("mathematics", empirical["required_domains"])
        self.assertNotIn("mathematics", empirical["missing_domains"])
        self.assertNotIn("mathematics", empirical["passed_domains"])
        self.assertEqual(mathematics["state"], "PASS")
        self.assertTrue(mathematics["exact_formal_refs_present"])
        self.assertFalse(mathematics["empirical_support_allowed"])
        self.assertNotIn("all_domain_empirical_predictions", audit["blocker_ids"])
        self.assertNotIn("mathematics_formal_support", audit["blocker_ids"])

    def test_oc133_missing_or_bad_mathematics_formal_route_blocks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._make_bounded_grand_ambition_fixture(root)

            missing_audit = oc133_platinum.all_domain_readiness_audit(root, {"state": "PASS", "blocker_total": 0})

        self.assertEqual(missing_audit["checks"]["mathematics_formal_support"]["state"], "FAIL")
        self.assertIn("mathematics_formal_support", missing_audit["blocker_ids"])

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._make_bounded_grand_ambition_fixture(root)
            self._make_mathematics_formal_support_fixture(root, include_refs=False)

            bad_refs_audit = oc133_platinum.all_domain_readiness_audit(root, {"state": "PASS", "blocker_total": 0})

        mathematics = bad_refs_audit["checks"]["mathematics_formal_support"]
        self.assertEqual(mathematics["state"], "FAIL")
        self.assertFalse(mathematics["exact_formal_refs_present"])
        self.assertIn("mathematics_formal_support", bad_refs_audit["blocker_ids"])

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._make_bounded_grand_ambition_fixture(root)
            self._make_mathematics_formal_support_fixture(root, high_open_total=1)

            high_blocker_audit = oc133_platinum.all_domain_readiness_audit(root, {"state": "PASS", "blocker_total": 0})

        mathematics = high_blocker_audit["checks"]["mathematics_formal_support"]
        self.assertEqual(mathematics["state"], "FAIL")
        self.assertGreater(mathematics["critical_high_blocker_total"], 0)
        self.assertIn("mathematics_formal_support", high_blocker_audit["blocker_ids"])

    def test_oc133_grand_science_ambition_routes_to_work_order_no_send(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._make_bounded_grand_ambition_fixture(root)

            audit = oc133_platinum.all_domain_readiness_audit(root, {"state": "PASS", "blocker_total": 0})

        self.assertTrue(audit["no_send"])
        self.assertFalse(audit["publish_allowed"])
        self.assertFalse(audit["journal_submissions_allowed"])
        self.assertNotEqual(audit["state"], oc133_platinum.ALL_DOMAIN_READY_STATE)
        self.assertNotEqual(audit["final_readiness_state"], oc133_platinum.ALL_DOMAIN_READY_STATE)
        self.assertNotEqual(audit["next_automatic_action"], "OWNER_REVIEW_NO_SEND")
        self.assertGreater(audit["work_order_total"], 0)
        self.assertEqual(audit["work_order_total"], len(audit["work_orders"]))
        self.assertTrue(audit["next_automatic_action"].startswith("OC133-PLATINUM-WO-"))

        work_order_text = json.dumps(audit["work_orders"], sort_keys=True).lower()
        self.assertTrue(
            "ambition" in work_order_text
            or "toe" in work_order_text
            or "modern science" in work_order_text
        )
        for row in audit["work_orders"]:
            self.assertTrue(row["no_send"])
            self.assertIn(row["severity"], {"CRITICAL", "HIGH"})
            self.assertTrue(row["verification_command"])

    def test_oc133_all_domain_queue_defers_grand_formal_claim_until_evidence_dependencies(self) -> None:
        blockers = {
            "grand_toe_claim_ledger_evidence": {"state": "FAIL"},
            "grand_toe_empirical_superiority": {"state": "FAIL", "missing_or_not_superior_domains": ["physics"]},
            "modern_science_comparator_superiority": {"state": "FAIL"},
        }
        orders = oc133_platinum.build_all_domain_work_orders(blockers)
        self.assertEqual(orders[0]["owner_capability"], "Research/EmpiricalScience")
        formal = next(row for row in orders if row["owner_capability"] == "Research/FormalScience")
        self.assertEqual(
            formal["open_dependency_blocker_ids"],
            ["grand_toe_empirical_superiority", "modern_science_comparator_superiority"],
        )
        self.assertGreater(formal["blocked_by_open_dependency_total"], 0)
        self.assertIn("--allow-blocked-exit-zero", " ".join(row["verification_command"] for row in orders))

    def test_oc133_scientific_closure_gates_are_no_send(self) -> None:
        root = complete.repo_root()
        summary = oc133.evaluate_release("oc_core_1_3_3", "all", "dry-run", write=True)
        self.assertIn(summary["release_state"], {"OC_CORE_1_3_3_PLATINUM_READY_NO_SEND", "ALL_DOMAIN_READY_NO_SEND", "OC_CORE_1_3_3_EXTERNAL_REVIEW_READY_NO_SEND", "SCIENTIFIC_BLOCKERS_REMAIN", "JOURNAL_PACKAGE_REPAIR_REQUIRED", "SCIENTIFIC_CONTENT_CLOSURE_RUNNING"})
        self.assertIn(summary["master_verdict"], {"PASS", "FAIL"})
        self.assertFalse(summary["publish_allowed"])
        self.assertFalse(summary["journal_submissions_allowed"])

        scorecard = json.loads((root / "releases/oc_core_1_3_3/editorial/OC_CORE_1_3_3_RELEASE_SCORECARD_latest.json").read_text(encoding="utf-8"))
        gates = {row["gate_id"]: row for row in scorecard["gate_results"]}
        always_pass_gates = [f"G{idx}" for idx in range(32, 57)] + [f"G{idx}" for idx in range(60, 70)]
        for gate_id in always_pass_gates:
            self.assertEqual(gates[gate_id]["state"], "PASS", gate_id)
        repro_manifest_path = root / "reports" / "OC_CORE_1_3_3_POST_GENERATION_REPRODUCIBILITY_MANIFEST.json"
        repro_manifest = json.loads(repro_manifest_path.read_text(encoding="utf-8")) if repro_manifest_path.exists() else {}
        if repro_manifest.get("git_state", {}).get("strict_head_replay_clean") is True and repro_manifest.get("verdict") == "PASS":
            self.assertEqual(gates["G59"]["state"], "PASS")
        else:
            self.assertEqual(gates["G59"]["state"], "FAIL")
        if summary["master_verdict"] == "PASS":
            self.assertEqual(gates["G57"]["state"], "PASS")
            self.assertEqual(gates["G58"]["state"], "PASS")
            self.assertEqual(gates["G70"]["state"], "PASS")
            self.assertEqual(summary["gate_counts"]["PASS"], 71)
            self.assertEqual(summary["content_closure_state"], "PASS")
            self.assertTrue(summary["all_domain_ready_no_send"] or summary["external_review_ready_no_send"])
            if summary["release_state"] == "OC_CORE_1_3_3_EXTERNAL_REVIEW_READY_NO_SEND":
                self.assertFalse(summary["all_domain_ready_no_send"])
                self.assertTrue(summary["external_review_ready_no_send"])
                self.assertIn("grand_toe_claim_ledger_evidence", summary["all_domain_blocker_ids"])
                self.assertIn("modern_science_comparator_superiority", summary["all_domain_blocker_ids"])
                self.assertEqual(len(summary["all_domain_missing_empirical_domains"]), 0)
        elif summary["release_state"] == "SCIENTIFIC_CONTENT_CLOSURE_RUNNING":
            self.assertEqual(summary["technical_gate_state"], "OC_CORE_1_3_3_10_10_READY_NO_SEND")
            self.assertEqual(gates["G57"]["state"], "PASS")
            self.assertEqual(gates["G58"]["state"], "PASS")
            self.assertEqual(gates["G70"]["state"], "PASS")
            self.assertGreater(summary["content_closure_blocker_total"], 0)
            self.assertIn("empirical_prediction_promotion", summary["content_closure_blocker_ids"])
            mission_ref = root / summary["content_closure_refs"]["mission_ref"]
            cockpit_ref = root / summary["content_closure_refs"]["cockpit_ref"]
            self.assertTrue(mission_ref.exists())
            self.assertTrue(cockpit_ref.exists())
        elif summary.get("all_domain_blocker_total", 0) > 0:
            self.assertEqual(summary["technical_gate_state"], "OC_CORE_1_3_3_10_10_READY_NO_SEND")
            self.assertEqual(summary["content_closure_state"], "PASS")
            self.assertEqual(gates["G57"]["state"], "PASS")
            self.assertEqual(gates["G58"]["state"], "PASS")
            self.assertEqual(gates["G70"]["state"], "PASS")
            self.assertEqual(summary["release_state"], "SCIENTIFIC_BLOCKERS_REMAIN")
            self.assertIn("grand_toe_claim_ledger_evidence", summary["all_domain_blocker_ids"])
            self.assertIn("grand_toe_empirical_superiority", summary["all_domain_blocker_ids"])
            self.assertIn("modern_science_comparator_superiority", summary["all_domain_blocker_ids"])
            self.assertEqual(len(summary["all_domain_missing_empirical_domains"]), 0)
            all_domain_ref = root / summary["content_closure_refs"]["all_domain_scorecard_ref"]
            self.assertTrue(all_domain_ref.exists())
            all_domain_scorecard = json.loads(all_domain_ref.read_text(encoding="utf-8"))
            self.assertFalse(all_domain_scorecard["all_domain_ready_no_send"])
            self.assertTrue(all_domain_scorecard["bounded_all_domain_ready_no_send"])
        else:
            self.assertIn(gates["G57"]["state"], {"PASS", "FAIL"})
            if (
                gates["G58"]["details"]["critical_open_total"] == 0
                and gates["G58"]["details"]["high_open_total"] == 0
                and gates["G58"]["details"]["parse_failure_total"] == 0
            ):
                self.assertEqual(gates["G58"]["state"], "PASS")
            else:
                self.assertEqual(gates["G58"]["state"], "BLOCKED")
            self.assertEqual(gates["G70"]["state"], "FAIL")
            self.assertEqual(summary["release_state"], "SCIENTIFIC_BLOCKERS_REMAIN")
        self.assertEqual(gates["G36"]["details"]["theorem_total"], 10)
        self.assertEqual(gates["G46"]["details"]["unwitnessed_component_total"], 0)
        self.assertEqual(gates["G47"]["details"]["machine_checked_subset_total"], 10)
        self.assertEqual(gates["G58"]["details"]["role_total"], 14)
        self.assertEqual(gates["G60"]["details"]["hit_total"], 0)
        self.assertEqual(gates["G64"]["details"]["scope_hit_total"], 0)

        validation = json.loads((root / "reports/OC_CORE_1_3_3_DOMAIN_VALIDATION_REPORT.json").read_text(encoding="utf-8"))
        self.assertEqual(validation["unsupported_promoted_total"], 0)
        self.assertEqual(validation["hash_failure_total"], 0)
        self.assertEqual(validation["lane_total"], 5)
        self.assertEqual(validation["numeric_replay_lane_total"], 5)
        self.assertGreaterEqual(validation["numeric_replay_row_total"], 5)
        self.assertTrue(all(row["result_verdict"] == "NUMERIC_REPLAY_QA_NOT_DOMAIN_VALIDATION" for row in validation["lanes"]))

        numeric = json.loads((root / "validation/numeric_predictions/OC133_NUMERIC_PREDICTION_TABLE.json").read_text(encoding="utf-8"))
        self.assertEqual(numeric["unsupported_promoted_total"], 0)
        self.assertEqual(numeric["blocked_for_promotion_total"], 0)

        red_team = json.loads((root / "review/OC_1_3_3_TOTAL_ATTACK_MATRIX.json").read_text(encoding="utf-8"))
        self.assertEqual(red_team["generic_row_total"], 0)
        self.assertGreaterEqual(red_team["objection_total"], 200)
        self.assertTrue(all(row.get("attacked_claim") and row.get("failure_mode") and row.get("closure_evidence") for row in red_team["rows"]))

        theorem_inventory = json.loads((root / "proofs/THEOREM_INVENTORY_1_3_3.json").read_text(encoding="utf-8"))
        self.assertEqual(theorem_inventory["demoted_route_total"], 0)
        self.assertEqual(theorem_inventory["machine_checked_subset_total"], theorem_inventory["theorem_total"])
        self.assertGreater(theorem_inventory["scientific_promotion_allowed_total"], 0)

        metadata_paths = [
            root / "README.md",
            root / "RELEASE_NOTES.md",
            root / "manifest.json",
            root / "checksums.txt",
            root / "releases/oc_core_1_3_3/editorial/metadata_drafts/zenodo.no_send.draft.json",
            root / "CITATION.cff",
            root / ".codemeta.json",
            root / "ro-crate-metadata.jsonld",
        ]
        for path in metadata_paths:
            body = path.read_text(encoding="utf-8")
            self.assertIn("1.3.3", body, path.name)
            self.assertNotIn("1.3.2", body, path.name)
            self.assertNotIn("v1.3.2", body, path.name)
            self.assertNotIn("oc_core_1_3_2", body, path.name)
        self.assertFalse((root / ".zenodo.json").exists())
        zenodo_draft = root / "releases/oc_core_1_3_3/editorial/metadata_drafts/zenodo.no_send.draft.json"
        self.assertEqual(json.loads(zenodo_draft.read_text(encoding="utf-8"))["version"], "1.3.3")
        self.assertEqual(json.loads((root / ".codemeta.json").read_text(encoding="utf-8"))["version"], "1.3.3")
        zenodo = json.loads(zenodo_draft.read_text(encoding="utf-8"))
        citation = (root / "CITATION.cff").read_text(encoding="utf-8")
        ro_crate = (root / "ro-crate-metadata.jsonld").read_text(encoding="utf-8")
        self.assertNotIn("publication_date", zenodo)
        self.assertNotEqual(zenodo.get("access_right"), "open")
        self.assertNotIn("date-released:", citation.lower())
        self.assertNotIn("type: doi", citation.lower())
        self.assertNotIn("datePublished", ro_crate)
        self.assertNotIn("doi:", ro_crate.lower())
        self.assertEqual(gates["G66"]["details"]["stale_hit_total"], 0)
        self.assertEqual(gates["G67"]["details"]["stale_hit_total"], 0)
        self.assertIn("README.md", gates["G66"]["details"]["scanned_metadata_paths"])
        self.assertIn("RELEASE_NOTES.md", gates["G66"]["details"]["scanned_metadata_paths"])
        self.assertTrue(all(gates["G66"]["details"]["no_send_checks"].values()))

        approval = json.loads((root / "releases/oc_core_1_3_3/editorial/OWNER_RELEASE_APPROVAL_v1.3.3.json").read_text(encoding="utf-8"))
        self.assertEqual(approval["decision"], "PENDING")
        self.assertFalse(approval["publish_allowed"])
        self.assertFalse(approval["journal_submissions_allowed"])

    def test_oc133_context_vs_release_matrix_counters(self) -> None:
        root = self._ensure_oc133_v12_surface()
        release_matrix = json.loads((root / "review/OC_1_3_3_TOTAL_ATTACK_MATRIX.json").read_text(encoding="utf-8"))
        context_matrix = json.loads(
            (
                root
                / "reviews/oc133_llm_cerberus/context_v12/claim_boundary_auditor/review/OC_1_3_3_TOTAL_ATTACK_MATRIX.json"
            ).read_text(encoding="utf-8")
        )
        finite = json.loads((root / "proofs/FINITE_MODEL_CHECKS_1_3_3.json").read_text(encoding="utf-8"))
        publish_control = next(row for row in finite["rows"] if row["case_id"] == "ADV-NOSEND-PUBLISH")

        summary = json.loads((root / "reviews/oc133_llm_cerberus/OC133_LLM_CERBERUS_SUMMARY.json").read_text(encoding="utf-8"))
        self.assertEqual(release_matrix["critical_unresolved_total"], summary["critical_open_total"])
        self.assertEqual(release_matrix["high_unresolved_total"], summary["high_open_total"])
        self.assertEqual(release_matrix["release_closure_matrix_kind"], "INTEGRATED_RELEASE_ATTACK_MATRIX_NOT_ROLE_CONTEXT_VIEW")
        if release_matrix["fresh_cerberus_review_satisfied"] is True:
            self.assertEqual(release_matrix["post_role_integration_required"], False)
            self.assertEqual(release_matrix["critical_unresolved_total"], 0)
            self.assertEqual(release_matrix["high_unresolved_total"], 0)
        else:
            self.assertEqual(release_matrix["post_role_integration_required"], True)

        self.assertEqual(context_matrix["critical_unresolved_total"], context_matrix["fresh_cerberus_critical_open_total"])
        self.assertEqual(context_matrix["high_unresolved_total"], context_matrix["fresh_cerberus_high_open_total"])
        self.assertEqual(context_matrix["deterministic_context_critical_unresolved_total"], 0)
        self.assertEqual(context_matrix["deterministic_context_high_unresolved_total"], 0)
        self.assertIn("fresh_context_counter_policy", context_matrix)

        self.assertEqual(publish_control["model"]["critical_open_total"], release_matrix["critical_unresolved_total"])
        self.assertEqual(publish_control["model"]["high_open_total"], release_matrix["high_unresolved_total"])
        self.assertTrue(publish_control["model"]["publish_requested"])

        self.assertNotEqual(
            (
                context_matrix["critical_unresolved_total"],
                context_matrix["high_unresolved_total"],
            ),
            (
                release_matrix["critical_unresolved_total"],
                release_matrix["high_unresolved_total"],
            ),
        )

    def test_oc133_nosend_owner_only_not_enough_control(self) -> None:
        root = self._ensure_oc133_v12_surface()
        claims = json.loads((root / "claims/CLAIM_LEDGER_1_3_3.json").read_text(encoding="utf-8"))
        nosend = next(row for row in claims["rows"] if row["claim_id"] == "OC133-NOSEND-001")
        self.assertFalse(nosend["release_promotion_allowed"])
        self.assertFalse(nosend["scientific_promotion_allowed"])
        self.assertTrue(nosend["governance_control_allowed"])
        self.assertEqual(nosend["public_status"], "GOVERNANCE_CONTROL_NO_SEND_NOT_SCIENTIFIC_PROMOTION")
        scope_limit = nosend["scope_limit"].lower()
        self.assertIn("owner approval alone is insufficient", scope_limit)
        self.assertIn("deposit-ready metadata", scope_limit)
        self.assertIn("public-record", scope_limit)
        self.assertIn("every channel lock", scope_limit)
        self.assertEqual(nosend["evidence_ref"], "releases/oc_core_1_3_3/editorial/OC_CORE_1_3_3_PUBLISH_MANIFEST_DRAFT.json")
        self.assertIn("releases/oc_core_1_3_3/editorial/OWNER_RELEASE_APPROVAL_v1.3.3.json", nosend["supporting_evidence_refs"])
        self.assertIn(
            "proofs/FINITE_MODEL_CHECKS_1_3_3.json::ADV-NOSEND-PUBLISH",
            nosend["supporting_evidence_refs"],
        )
        self.assertIn(
            "proofs/FINITE_MODEL_CHECKS_1_3_3.json::ADV-NOSEND-PUBLISH-HYPOTHETICAL-OWNER-APPROVED-CONTROL",
            nosend["supporting_evidence_refs"],
        )

        finite = json.loads((root / "proofs/FINITE_MODEL_CHECKS_1_3_3.json").read_text(encoding="utf-8"))
        owner_approved_only = next(
            row
            for row in finite["rows"]
            if row["case_id"] == "ADV-NOSEND-PUBLISH-HYPOTHETICAL-OWNER-APPROVED-CONTROL"
        )
        self.assertEqual(owner_approved_only["expected_verdict"], "REJECT_PUBLIC_ACTION")
        self.assertEqual(owner_approved_only["observed_verdict"], "REJECT_PUBLIC_ACTION")
        self.assertIn("deposit_ready_metadata", owner_approved_only["failed_gate_predicates"])
        self.assertIn("public_record_present", owner_approved_only["failed_gate_predicates"])
        self.assertTrue(owner_approved_only["model"]["owner_approved"])
        self.assertFalse(owner_approved_only["model"]["deposit_ready_metadata"])
        self.assertFalse(owner_approved_only["model"]["public_record_present"])

    def test_oc133_all_gates_open_control_approves_public_action(self) -> None:
        root = self._ensure_oc133_v12_surface()
        finite = json.loads((root / "proofs/FINITE_MODEL_CHECKS_1_3_3.json").read_text(encoding="utf-8"))
        all_gates_open = next(
            row for row in finite["rows"] if row["case_id"] == "ADV-NOSEND-PUBLISH-ALL-GATES-OPEN-CONTROL"
        )
        self.assertEqual(all_gates_open["expected_verdict"], "ACCEPT_PUBLIC_ACTION")
        self.assertEqual(all_gates_open["observed_verdict"], "ACCEPT_PUBLIC_ACTION")
        self.assertEqual(all_gates_open["failed_gate_predicates"], [])
        self.assertEqual(all_gates_open["control_label"], "ALL_OWNER_METADATA_RECORD_REVIEW_AND_CHANNEL_GATES_OPEN_HYPOTHETICAL_ACCEPT")

        self.assertTrue(all(all_gates_open["model"].get(flag) is True for flag in [
            "github_release_allowed",
            "zenodo_deposit_allowed",
            "software_heritage_deposit_allowed",
            "journal_submission_allowed",
            "doi_minting_allowed",
            "publish_allowed",
            "deposit_ready_metadata",
            "public_record_present",
        ]))
        self.assertFalse(all_gates_open["model"]["global_no_send_lock"])
        self.assertEqual(all_gates_open["model"]["requested_channels"], [
            "github_release",
            "zenodo_deposit",
            "software_heritage_deposit",
            "journal_submission",
            "doi_minting",
        ])

    def test_oc133_split_evidence_ref_totals(self) -> None:
        root = self._ensure_oc133_v12_surface()
        finite = json.loads((root / "proofs/FINITE_MODEL_CHECKS_1_3_3.json").read_text(encoding="utf-8"))
        self.assertEqual(finite["finite_row_theorem_ref_total"], finite["finite_row_theorem_ref_bound_total"])
        self.assertEqual(finite["finite_row_evidence_ref_total"], finite["finite_row_evidence_ref_bound_total"])
        self.assertEqual(finite["finite_row_theorem_ref_missing_total"], 0)
        self.assertEqual(finite["finite_row_evidence_ref_missing_total"], 0)
        self.assertEqual(
            finite["lean_theorem_ref_total"] + finite["semantic_evaluator_ref_total"] + finite["governance_or_artifact_ref_total"],
            finite["finite_row_theorem_ref_total"],
        )

    def test_oc133_manifest_checksums_inventory_exception(self) -> None:
        root = self._ensure_oc133_v12_surface()
        manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
        checksum_inventory = (root / "checksums.txt").read_text(encoding="utf-8")
        self.assertEqual(manifest["checksum_file_ref"], "checksums.txt")
        self.assertIn("checksums.txt", manifest["inventory_policy"])
        self.assertIn("nonrecursive_manifest_exceptions", manifest)
        no_send_exception = next(
            row for row in manifest["nonrecursive_manifest_exceptions"] if row["path"] == "checksums.txt"
        )
        self.assertIn("self-referential checksum cycle", no_send_exception["reason"].lower())
        self.assertNotIn("checksums.txt", [row["path"] for row in manifest["files"]])
        self.assertNotIn("checksums.txt", checksum_inventory)

    def test_oc133_root_public_surface_is_current_no_send(self) -> None:
        root = self._ensure_oc133_v12_surface()
        manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
        manifest_paths = {row["path"] for row in manifest["files"]}
        self.assertIn("README.md", manifest_paths)
        self.assertIn("RELEASE_NOTES.md", manifest_paths)

        forbidden_tokens = [
            "v1.3.2",
            "1.3.2",
            "oc_core_1_3_2",
            "10.5281/zenodo.",
            "published in the concept DOI chain",
            "public v1.3.2 record",
        ]
        for rel_path in ["README.md", "RELEASE_NOTES.md"]:
            body = (root / rel_path).read_text(encoding="utf-8", errors="ignore")
            self.assertIn("1.3.3", body, rel_path)
            self.assertIn("no-send", body.lower(), rel_path)
            self.assertIn("no public release", body.lower(), rel_path)
            for token in forbidden_tokens:
                self.assertNotIn(token, body, rel_path)

    def test_oc133_public_metadata_scan_covers_manifest_public_surface(self) -> None:
        root = self._ensure_oc133_v12_surface()
        g66 = oc133_v12.audit(root)["zenodo"]
        scanned_paths = set(g66["scanned_metadata_paths"])
        for rel_path in ["README.md", "RELEASE_NOTES.md"]:
            self.assertIn(rel_path, scanned_paths)
        self.assertEqual(g66["stale_hit_total"], 0)

    def test_oc133_cross_artifact_hash_bindings_are_current(self) -> None:
        root = self._ensure_oc133_v12_surface()
        oc133.build_package(root, channel="all", no_publish=True)

        def sha256(path: Path) -> str:
            h = hashlib.sha256()
            with path.open("rb") as handle:
                for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                    h.update(chunk)
            return h.hexdigest()

        finite = json.loads((root / "proofs/FINITE_MODEL_CHECKS_1_3_3.json").read_text(encoding="utf-8"))
        lean_cert = root / "formal/lean/LEAN_BUILD_CERTIFICATE_1_3_3.json"
        self.assertEqual(finite["lean_build_certificate_sha256"], sha256(lean_cert))

        zip_integrity = json.loads(
            (
                root
                / "releases/oc_core_1_3_3/editorial/OC_CORE_1_3_3_ZIP_INTEGRITY_latest.json"
            ).read_text(encoding="utf-8")
        )
        package_path = root / zip_integrity["package"]
        self.assertEqual(zip_integrity["package_sha256"], sha256(package_path))

    def test_zz_oc133_suite_restores_current_no_send_surface(self) -> None:
        root = complete.repo_root()
        oc133_v12.ensure_v12(root)
        package = oc133.build_package(root, channel="all", no_publish=True)
        self.assertTrue(oc133._root_no_send_surface_current(root))
        self.assertTrue((root / package["package"]).exists())


if __name__ == "__main__":
    unittest.main()
