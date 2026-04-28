from __future__ import annotations

import json
from pathlib import Path
import unittest
import zipfile

from release_machine import core
from release_machine import complete
from release_machine import publication


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

    def test_research_packets_are_bounded_no_send_material(self) -> None:
        root = complete.repo_root()
        audit = json.loads((root / "releases/oc_core_1_3_2/editorial/research_packets/PUBLIC_RESEARCH_PACKET_AUDIT_v1.json").read_text(encoding="utf-8"))
        self.assertGreaterEqual(audit["packet_total"], 1)
        self.assertEqual(audit["packet_total"], audit["pass_total"])
        self.assertFalse(audit["canonical_claim_ledger_change"])

    def test_v132_tag_is_backed_by_publication_report_and_publish_lock(self) -> None:
        root = complete.repo_root()
        self.assertTrue((root / ".git/refs/tags/v1.3.2").exists())
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
        index = publication.generate_submission_packages(root)
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
                if artifact["role"] == "release_archive":
                    self.assertEqual(artifact["sha256"], "")
                    self.assertEqual(artifact["checksum_ref"], "releases/oc_core_1_3_2/editorial/OC_CORE_1_3_2_ZIP_INTEGRITY_latest.json")
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


if __name__ == "__main__":
    unittest.main()
