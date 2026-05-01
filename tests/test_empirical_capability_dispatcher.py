from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from tools import oc133_empirical_capability_dispatcher as dispatcher
from tools import oc133_capability_repair_executor as repair_executor
from tools import oc133_empirical_capability_registry as registry


def write_json(root: Path, rel_path: str, payload: dict[str, object]) -> None:
    path = root / rel_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8", newline="\n")


def write_script(root: Path, rel_path: str, body: str) -> None:
    path = root / rel_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body + "\n", encoding="utf-8", newline="\n")


def no_send_locks(**overrides: object) -> dict[str, object]:
    locks: dict[str, object] = {
        "no_send": True,
        "publish_allowed": False,
        "journal_submissions_allowed": False,
        "external_network_allowed": False,
        "automatic_dispatch_allowed": False,
        "owner_approval_required": True,
    }
    locks.update(overrides)
    return locks


def component(ref: str, command: str, *, component_type: str = "factory") -> dict[str, object]:
    return {
        "component_ref": ref,
        "component_type": component_type,
        "resource_class": component_type,
        "resource_class_rank": 3,
        "command": command,
        "capability_owner": "Research/EmpiricalScience",
        "verdict": "BLOCKED",
        "open_blocker_total": 1,
        "candidate_pack_total": 1,
        "valid_pack_total": 0,
        "is_blocked": True,
        "unblock_value": 100,
        "next_action": "Run safe local dispatcher test action.",
        "no_send": True,
        "publish_allowed": False,
        "journal_submissions_allowed": False,
        "external_network_allowed": False,
        "automatic_dispatch_allowed": False,
        "effective_payload": {"verdict": "BLOCKED", "open_blocker_total": 1},
    }


def write_registry(root: Path, components: list[dict[str, object]], *, locks: dict[str, object] | None = None) -> None:
    locks = locks or no_send_locks()
    payload: dict[str, object] = {
        "schema_id": registry.SCHEMA_ID,
        "release_id": registry.RELEASE_ID,
        "version": registry.VERSION,
        "component_total": len(components),
        "components": components,
        "next_action_queue": [
            {
                "action_id": f"OC133-ECQ-{idx:03d}",
                "position": idx,
                "component_ref": row["component_ref"],
                "component_type": row["component_type"],
                "resource_class": row["resource_class"],
                "unblock_value": row["unblock_value"],
                "next_action": row["next_action"],
            }
            for idx, row in enumerate(components, start=1)
        ],
        "no_send_locks": locks,
        "no_send": locks["no_send"],
        "publish_allowed": locks["publish_allowed"],
        "journal_submissions_allowed": locks["journal_submissions_allowed"],
        "external_network_allowed": locks["external_network_allowed"],
        "automatic_dispatch_allowed": locks["automatic_dispatch_allowed"],
        "verdict": "CAPABILITY_REBALANCE_BLOCKED",
    }
    write_json(root, registry.REPORT_JSON_REL, payload)


SAFE_SCRIPT = "\n".join(
    [
        "from __future__ import annotations",
        "import argparse, json",
        "parser = argparse.ArgumentParser()",
        "parser.add_argument('--write', action='store_true')",
        "parser.add_argument('--allow-blocked-exit-zero', action='store_true')",
        "parser.parse_args()",
        "print(json.dumps({'verdict': 'READY_FOR_PARENT_REGISTRY_REVIEW', 'open_blocker_total': 0}))",
    ]
)


class EmpiricalCapabilityDispatcherTests(unittest.TestCase):
    def test_grand_empirical_repair_profile_routes_through_dispatcher(self) -> None:
        program = repair_executor.materialize_grand_science_program
        source = Path(program.__code__.co_filename).read_text(encoding="utf-8")
        self.assertIn("tools/oc133_empirical_capability_registry.py", source)
        self.assertIn("tools/oc133_empirical_capability_dispatcher.py", source)
        self.assertIn("--refresh-registry", source)
        self.assertIn("--execute", source)

    def test_ranked_action_selection_is_deterministic(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            alpha_ref = "tools/oc133_alpha_empirical_factory.py"
            beta_ref = "tools/oc133_beta_empirical_factory.py"
            write_script(root, alpha_ref, SAFE_SCRIPT)
            write_script(root, beta_ref, SAFE_SCRIPT)
            alpha = component(alpha_ref, f"python {alpha_ref} --write")
            beta = component(beta_ref, f"python {beta_ref} --write")
            write_registry(root, [alpha, beta])

            # Reverse the queue order in the file but keep positions authoritative.
            payload = json.loads((root / registry.REPORT_JSON_REL).read_text(encoding="utf-8"))
            payload["next_action_queue"] = [payload["next_action_queue"][1], payload["next_action_queue"][0]]
            write_json(root, registry.REPORT_JSON_REL, payload)

            first = dispatcher.build_payload(root, write=False, execute=False, max_actions=None)
            second = dispatcher.build_payload(root, write=False, execute=False, max_actions=None)

            self.assertEqual(first["selected_component_refs"], [alpha_ref, beta_ref])
            self.assertEqual(first["selected_component_refs"], second["selected_component_refs"])
            self.assertEqual([row["action_outcome"] for row in first["results"]], ["DRY_RUN_ALLOWED", "DRY_RUN_ALLOWED"])
            self.assertEqual(first["rejected_action_total"], 0)

    def test_direct_cli_entrypoint_can_import_registry(self) -> None:
        result = dispatcher.subprocess.run(
            [dispatcher.sys.executable, str(dispatcher.ROOT / "tools" / "oc133_empirical_capability_dispatcher.py"), "--max-actions", "0"],
            cwd=dispatcher.ROOT,
            text=True,
            encoding="utf-8",
            errors="replace",
            capture_output=True,
            timeout=60,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["schema_id"], dispatcher.SCHEMA_ID)
        self.assertEqual(payload["selected_action_total"], 0)

    def test_allowlist_rejects_publish_or_push_style_command(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ref = "tools/oc133_publish_empirical_factory.py"
            write_script(
                root,
                ref,
                "\n".join(
                    [
                        "from __future__ import annotations",
                        "from pathlib import Path",
                        "import argparse",
                        "parser = argparse.ArgumentParser()",
                        "parser.add_argument('--write', action='store_true')",
                        "parser.add_argument('--publish', action='store_true')",
                        "parser.parse_args()",
                        "Path('SHOULD_NOT_EXIST.txt').write_text('ran', encoding='utf-8')",
                    ]
                ),
            )
            row = component(ref, f"python {ref} --write --publish")
            write_registry(root, [row])

            payload = dispatcher.build_payload(root, write=False, execute=True, max_actions=None)
            result = payload["results"][0]

            self.assertEqual(payload["rejected_action_total"], 1)
            self.assertEqual(payload["executed_action_total"], 0)
            self.assertFalse((root / "SHOULD_NOT_EXIST.txt").exists())
            self.assertFalse(result["allowlist_pass"])
            self.assertTrue(any("forbidden" in reason for reason in result["rejection_reasons"]))

    def test_no_send_locks_block_execution(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ref = "tools/oc133_locked_empirical_factory.py"
            write_script(
                root,
                ref,
                "\n".join(
                    [
                        "from __future__ import annotations",
                        "from pathlib import Path",
                        "import argparse",
                        "parser = argparse.ArgumentParser()",
                        "parser.add_argument('--write', action='store_true')",
                        "parser.parse_args()",
                        "Path('LOCK_BYPASSED.txt').write_text('ran', encoding='utf-8')",
                    ]
                ),
            )
            row = component(ref, f"python {ref} --write")
            write_registry(root, [row], locks=no_send_locks(external_network_allowed=True))

            payload = dispatcher.build_payload(root, write=False, execute=True, max_actions=None)
            result = payload["results"][0]

            self.assertEqual(payload["rejected_action_total"], 1)
            self.assertEqual(payload["executed_action_total"], 0)
            self.assertFalse((root / "LOCK_BYPASSED.txt").exists())
            self.assertTrue(
                any("registry_lock::external_network_allowed" in reason for reason in result["rejection_reasons"])
            )

    def test_blocked_scientific_result_is_executor_success_not_pass(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ref = "tools/oc133_blocked_empirical_factory.py"
            write_script(
                root,
                ref,
                "\n".join(
                    [
                        "from __future__ import annotations",
                        "from pathlib import Path",
                        "import argparse, json",
                        "parser = argparse.ArgumentParser()",
                        "parser.add_argument('--write', action='store_true')",
                        "parser.add_argument('--allow-blocked-exit-zero', action='store_true')",
                        "parser.parse_args()",
                        "Path('validation/heldout/blocked_marker.json').parent.mkdir(parents=True, exist_ok=True)",
                        "Path('validation/heldout/blocked_marker.json').write_text('{\"ran\": true}\\n', encoding='utf-8')",
                        "print(json.dumps({",
                        "    'verdict': 'BLOCKED_PENDING_GENUINE_EVIDENCE',",
                        "    'open_blocker_total': 1,",
                        "    'candidate_pack_total': 1,",
                        "    'valid_pack_total': 0,",
                        "    'blockers': ['missing-heldout-evidence'],",
                        "}))",
                    ]
                ),
            )
            row = component(ref, f"python {ref} --write --allow-blocked-exit-zero")
            write_registry(root, [row])

            payload = dispatcher.build_payload(root, write=True, execute=True, max_actions=None)
            result = payload["results"][0]

            self.assertEqual(payload["executed_action_total"], 1)
            self.assertEqual(payload["executor_success_total"], 1)
            self.assertEqual(payload["command_failure_total"], 0)
            self.assertEqual(payload["scientific_blocked_total"], 1)
            self.assertEqual(payload["passed_action_total"], 0)
            self.assertEqual(payload["verdict"], "DISPATCH_RAN_WITH_SCIENTIFIC_BLOCKERS")
            self.assertTrue(result["command_success"])
            self.assertTrue(result["scientific_blocked"])
            self.assertFalse(result["scientific_pass"])
            self.assertEqual(result["action_outcome"], "SCIENTIFIC_BLOCKED")
            self.assertNotEqual(result["repo_hash_before"]["sha256"], result["repo_hash_after"]["sha256"])
            self.assertTrue((root / dispatcher.REPORT_JSON_REL).exists())
            self.assertIn("Scientific blockers", (root / dispatcher.REPORT_MD_REL).read_text(encoding="utf-8"))

    def test_structured_blocked_payload_with_legacy_nonzero_exit_is_not_command_failure(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ref = "tools/oc133_legacy_blocked_empirical_factory.py"
            write_script(
                root,
                ref,
                "\n".join(
                    [
                        "from __future__ import annotations",
                        "import argparse, json, sys",
                        "parser = argparse.ArgumentParser()",
                        "parser.add_argument('--write', action='store_true')",
                        "parser.parse_args()",
                        "print(json.dumps({'verdict': 'BLOCKED_PENDING_GENUINE_EVIDENCE', 'open_blocker_total': 2, 'grand_toe_support_allowed': False}))",
                        "sys.exit(2)",
                    ]
                ),
            )
            row = component(ref, f"python {ref} --write")
            write_registry(root, [row])

            payload = dispatcher.build_payload(root, write=False, execute=True, max_actions=None)
            result = payload["results"][0]

            self.assertEqual(payload["command_failure_total"], 0)
            self.assertEqual(payload["scientific_blocked_total"], 1)
            self.assertEqual(payload["verdict"], "DISPATCH_RAN_WITH_SCIENTIFIC_BLOCKERS")
            self.assertTrue(result["executor_success"])
            self.assertEqual(result["action_outcome"], "SCIENTIFIC_BLOCKED_LEGACY_NONZERO")

    def test_legacy_unrecognized_argument_is_retried_without_unsupported_arg(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ref = "validation/heldout/domain_evidence/legacy_evidence_executor.py"
            write_script(
                root,
                ref,
                "\n".join(
                    [
                        "from __future__ import annotations",
                        "import argparse, json",
                        "parser = argparse.ArgumentParser()",
                        "parser.add_argument('--write', action='store_true')",
                        "parser.parse_args()",
                        "print(json.dumps({'verdict': 'BLOCKED_PENDING_GENUINE_EVIDENCE', 'open_blocker_total': 1, 'grand_toe_support_allowed': False}))",
                    ]
                ),
            )
            row = component(ref, f"python {ref} --write --allow-blocked-exit-zero", component_type="executor")
            write_registry(root, [row])

            payload = dispatcher.build_payload(root, write=False, execute=True, max_actions=None)
            result = payload["results"][0]

            self.assertEqual(payload["command_failure_total"], 0)
            self.assertEqual(payload["scientific_blocked_total"], 1)
            self.assertTrue(result["retry_info"])
            self.assertEqual(result["retry_info"]["removed_args"], ["--allow-blocked-exit-zero"])
            self.assertEqual(result["action_outcome"], "SCIENTIFIC_BLOCKED")


if __name__ == "__main__":
    raise SystemExit(unittest.main())
