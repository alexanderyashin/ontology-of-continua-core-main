from __future__ import annotations

import json
import hashlib
import os
from pathlib import Path
import subprocess
import unittest
import zipfile

import release_machine
from release_machine import core
from release_machine import complete
from release_machine import oc133
from release_machine import oc133_v12
from release_machine import publication
from release_machine import versioning


class ReleaseMachineTests(unittest.TestCase):
    def _ensure_oc133_v12_surface(self) -> Path:
        root = complete.repo_root()
        oc133_v12.ensure_v12(root)
        return root

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

    def test_completed_gate_set_records_terminal_science_and_keeps_no_send_lock(self) -> None:
        summary = core.evaluate_release("oc_core_1_3_2", "all", "pre_publish", write=True)
        self.assertEqual(summary["master_verdict"], "PASS")
        self.assertEqual(summary["gate_counts"]["PASS"], 32)
        self.assertEqual(summary["gate_counts"].get("FAIL", 0), 0)
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

    def test_oc133_scientific_closure_gates_are_no_send(self) -> None:
        root = complete.repo_root()
        summary = oc133.evaluate_release("oc_core_1_3_3", "all", "dry-run", write=True)
        self.assertIn(summary["release_state"], {"OC_CORE_1_3_3_PLATINUM_READY_NO_SEND", "SCIENTIFIC_BLOCKERS_REMAIN", "SCIENTIFIC_CONTENT_CLOSURE_RUNNING"})
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
        elif summary["release_state"] == "SCIENTIFIC_CONTENT_CLOSURE_RUNNING":
            self.assertEqual(summary["technical_gate_state"], "OC_CORE_1_3_3_10_10_READY_NO_SEND")
            self.assertEqual(gates["G57"]["state"], "PASS")
            self.assertEqual(gates["G58"]["state"], "PASS")
            self.assertEqual(gates["G70"]["state"], "PASS")
            self.assertGreater(summary["content_closure_blocker_total"], 0)
            self.assertIn("theorem_promotion", summary["content_closure_blocker_ids"])
            self.assertIn("empirical_prediction_promotion", summary["content_closure_blocker_ids"])
            mission_ref = root / summary["content_closure_refs"]["mission_ref"]
            cockpit_ref = root / summary["content_closure_refs"]["cockpit_ref"]
            self.assertTrue(mission_ref.exists())
            self.assertTrue(cockpit_ref.exists())
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
        self.assertTrue(release_matrix["fresh_cerberus_review_satisfied"] is False)
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


if __name__ == "__main__":
    unittest.main()
