from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from tools import oc133_biology_target_evidence_factory as factory


REPO_ROOT = Path(__file__).resolve().parents[1]


def write_json(root: Path, rel_path: str, payload: dict) -> None:
    path = root / rel_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8", newline="\n")


def requirements(minimum_n: int = 20) -> dict:
    return {
        "schema_id": "OC133_GRAND_EMPIRICAL_DOMAIN_REQUIREMENTS_v1",
        "release_id": "oc_core_1_3_3",
        "capability_owner": "Research/EmpiricalScience",
        "minimum_per_domain_n": minimum_n,
        "required_domains": ["biology", "chemistry", "mathematics", "physics", "systems"],
        "required_source_separation_modes": ["prospective", "target_blind"],
    }


def official_bundle(
    row_total: int = 20,
    *,
    target_leak: bool = False,
    trivial_comparator: bool = False,
    pagination_rows: bool = False,
    pre_target_lock: bool = True,
    bad_negative_control: bool = False,
) -> dict:
    training_sources = [f"official-geo-visible-projection-{idx + 1:04d}" for idx in range(row_total)]
    target_sources = [f"official-geo-target-projection-{idx + 1:04d}" for idx in range(row_total)]
    if target_leak:
        target_sources[0] = training_sources[0]
    rows = []
    for idx in range(row_total):
        observed = float(10 + idx)
        predicted = observed
        comparator = observed if bad_negative_control else observed + 3.0
        rows.append(
            {
                "biological_target_id": f"BIO-TARGET-{idx + 1:04d}",
                "biological_target_kind": "api_pagination_retmax_target"
                if pagination_rows
                else "gene_expression_response_target",
                "biological_observable": "NCBI/GEO ESearch retmax page-size"
                if pagination_rows
                else "official gene expression response observable",
                "source_ref": f"official://biology/target-row-{idx + 1:04d}",
                "source_sha256": f"{idx + 1:064x}"[-64:],
                "training_source": training_sources[idx],
                "target_source": target_sources[idx],
                "predicted_value": predicted,
                "observed_value": observed,
                "comparator_prediction": comparator,
                "uncertainty": 0.0,
                "negative_control_id": f"heldout-expression-control-{idx + 1:04d}",
                "negative_control_description": "pre-registered biological comparator must be worse than the model residual",
                "falsifier": "model residual exceeds uncertainty or biological comparator is not worse",
            }
        )
    return {
        "schema_id": factory.OFFICIAL_BUNDLE_SCHEMA_ID,
        "domain": "biology",
        "source_separation": {
            "mode": "target_blind",
            "pre_target_lock": pre_target_lock,
            "target_hidden_until_scoring": pre_target_lock,
            "training_sources": training_sources,
            "target_sources": target_sources,
        },
        "model_under_test": "pre-registered biological expression response scorer",
        "comparator_baseline": {
            "name": "constant zero null baseline"
            if trivial_comparator
            else "same gene expression training-cohort median biological baseline",
            "prediction_rule": "predict zero for every target"
            if trivial_comparator
            else "predict the training-cohort median expression response for the same biological assay family",
            "pre_registered": True,
        },
        "uncertainty_metric": "mean absolute residual",
        "uncertainty_method": "exact deterministic heldout expression residual interval",
        "biological_target_rows": rows,
    }


class BiologyTargetEvidenceFactoryTests(unittest.TestCase):
    def test_missing_official_target_bundle_stays_blocked_with_work_order(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_json(root, factory.REQUIREMENTS_REL, requirements())

            payload = factory.build_payload(root)
            report = payload["report"]

            self.assertFalse(report["biology_support_closes"])
            self.assertEqual(report["verdict"], "BLOCKED_PENDING_OFFICIAL_BIOLOGICAL_TARGET_EVIDENCE")
            self.assertIn("NO_LOCAL_OFFICIAL_BIOLOGICAL_TARGET_BUNDLE_FOUND", report["blockers"])
            self.assertEqual(payload["work_order"]["required_final_bundle_schema_id"], factory.OFFICIAL_BUNDLE_SCHEMA_ID)
            self.assertIn("oc133_biology_target_official_bundle_builder.py", payload["work_order"]["preferred_local_helper"])
            self.assertTrue(payload["work_order"]["no_send"])

    def test_valid_official_biology_target_bundle_can_close_lane(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            bundle_ref = "validation/_raw/biology_target_bundle.json"
            write_json(root, factory.REQUIREMENTS_REL, requirements())
            write_json(root, bundle_ref, official_bundle())

            payload = factory.build_payload(root, bundle_refs=[bundle_ref])

            self.assertTrue(payload["report"]["biology_support_closes"])
            self.assertTrue(payload["candidate_pack"]["grand_toe_support_allowed"])
            self.assertEqual(payload["candidate_pack"]["n"], 20)
            self.assertEqual(payload["report"]["blockers"], [])

    def test_pagination_only_bundle_stays_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            bundle_ref = "validation/_raw/biology_pagination_bundle.json"
            write_json(root, factory.REQUIREMENTS_REL, requirements())
            write_json(root, bundle_ref, official_bundle(pagination_rows=True))

            report = factory.build_payload(root, bundle_refs=[bundle_ref])["report"]

            self.assertFalse(report["biology_support_closes"])
            blocker_text = " ".join(report["blockers"])
            self.assertIn("API_PAGINATION_ROW_NOT_BIOLOGICAL_TARGET", blocker_text)
            self.assertIn("BIOLOGY_PAGINATION_QA_NOT_GRAND_EVIDENCE", blocker_text)

    def test_target_leakage_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            bundle_ref = "validation/_raw/biology_target_leak_bundle.json"
            write_json(root, factory.REQUIREMENTS_REL, requirements())
            write_json(root, bundle_ref, official_bundle(target_leak=True))

            report = factory.build_payload(root, bundle_refs=[bundle_ref])["report"]

            self.assertFalse(report["biology_support_closes"])
            blocker_text = " ".join(report["blockers"])
            self.assertIn("TRAINING_TARGET_SOURCE_OVERLAP", blocker_text)
            self.assertIn("TARGET_LEAKAGE_TRAINING_EQUALS_TARGET", blocker_text)

    def test_comparator_triviality_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            bundle_ref = "validation/_raw/biology_trivial_comparator_bundle.json"
            write_json(root, factory.REQUIREMENTS_REL, requirements())
            write_json(root, bundle_ref, official_bundle(trivial_comparator=True))

            report = factory.build_payload(root, bundle_refs=[bundle_ref])["report"]

            self.assertFalse(report["biology_support_closes"])
            self.assertIn("BIOLOGY_COMPARATOR_TRIVIAL_OR_NONBIOLOGICAL", report["blockers"])

    def test_n_below_twenty_blocks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            bundle_ref = "validation/_raw/biology_19_target_bundle.json"
            write_json(root, factory.REQUIREMENTS_REL, requirements())
            write_json(root, bundle_ref, official_bundle(row_total=19))

            report = factory.build_payload(root, bundle_refs=[bundle_ref])["report"]

            self.assertFalse(report["biology_support_closes"])
            self.assertIn("N_BELOW_MINIMUM::19/20", report["blockers"])

    def test_missing_target_hidden_lock_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            bundle_ref = "validation/_raw/biology_no_target_hidden_lock_bundle.json"
            write_json(root, factory.REQUIREMENTS_REL, requirements())
            write_json(root, bundle_ref, official_bundle(pre_target_lock=False))

            report = factory.build_payload(root, bundle_refs=[bundle_ref])["report"]

            self.assertFalse(report["biology_support_closes"])
            self.assertIn("PRE_TARGET_LOCK_REQUIRED", report["blockers"])
            self.assertIn("TARGET_HIDDEN_UNTIL_SCORING_REQUIRED", report["blockers"])

    def test_valid_bundle_fails_when_negative_controls_not_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            bundle_ref = "validation/_raw/biology_bad_negative_control_bundle.json"
            write_json(root, factory.REQUIREMENTS_REL, requirements())
            write_json(root, bundle_ref, official_bundle(bad_negative_control=True))

            report = factory.build_payload(root, bundle_refs=[bundle_ref])["report"]

            self.assertFalse(report["biology_support_closes"])
            blocker_text = " ".join(report["blockers"])
            self.assertIn("NEGATIVE_CONTROL_NOT_REJECTED", blocker_text)


if __name__ == "__main__":
    unittest.main()
