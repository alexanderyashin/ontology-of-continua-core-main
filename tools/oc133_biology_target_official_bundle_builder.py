from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any
from urllib.parse import urlencode


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools import oc133_biology_target_evidence_factory as target_factory
from tools import oc133_official_readonly_acquisition_runner as runner


RELEASE_ID = "oc_core_1_3_3"
VERSION = "1.3.3"
CAPABILITY_OWNER = "Research/EmpiricalScience"
HELPER_REF = "tools/oc133_biology_target_official_bundle_builder.py"

REPORT_SCHEMA_ID = "OC133_BIOLOGY_TARGET_OFFICIAL_BUNDLE_BUILDER_REPORT_v1"
ACQUISITION_PACKET_SCHEMA_ID = "OC133_BIOLOGY_TARGET_EVIDENCE_ACQUISITION_PACKET_v1"

OUTPUT_ROOT_REL = target_factory.OUTPUT_ROOT_REL
RAW_ROOT_REL = f"{OUTPUT_ROOT_REL}/raw"
SEARCH_PACKET_REL = f"{OUTPUT_ROOT_REL}/OC133_BIOLOGY_TARGET_GEO_PROFILE_SEARCH_ACQUISITION_PACKET.json"
SUMMARY_PACKET_REL = f"{OUTPUT_ROOT_REL}/OC133_BIOLOGY_TARGET_GEO_PROFILE_SUMMARY_ACQUISITION_PACKET.json"
OFFICIAL_BUNDLE_REL = f"{RAW_ROOT_REL}/OC133_BIOLOGY_TARGET_OFFICIAL_BUNDLE.json"
BUILDER_REPORT_REL = f"{OUTPUT_ROOT_REL}/OC133_BIOLOGY_TARGET_OFFICIAL_BUNDLE_BUILDER_REPORT.json"

SEARCH_ACQUISITION_ID = "OC133-BIOLOGY-TARGET-GEOPROFILES-SEARCH-0001"
SUMMARY_ACQUISITION_ID = "OC133-BIOLOGY-TARGET-GEOPROFILES-SUMMARY-0001"

GEO_PROFILE_QUERY = "GDS3716[All Fields] AND Homo sapiens[ORGN] AND count[VTYP] NOT Control[All Fields]"
GEO_PROFILE_RETMAX = 30
MINIMUM_TARGET_ROWS = 20

NO_SEND = {
    "no_send": True,
    "publish_allowed": False,
    "push_allowed": False,
    "journal_submissions_allowed": False,
    "doi_registration_allowed": False,
    "zenodo_upload_allowed": False,
    "registry_write_allowed": False,
    "release_promotion_allowed": False,
}


def repo_root() -> Path:
    return ROOT


def canonical_json(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":"))


def sha256_object(payload: Any) -> str:
    return hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8", newline="\n")


def resolve_under_root(root: Path, rel_path: str) -> Path:
    path = (root / rel_path).resolve()
    path.relative_to(root.resolve())
    return path


def official_eutils_url(endpoint: str, params: dict[str, str]) -> str:
    return f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/{endpoint}?{urlencode(params)}"


def acquisition_packet(*, request: dict[str, Any], stage: str) -> dict[str, Any]:
    return {
        "schema_id": ACQUISITION_PACKET_SCHEMA_ID,
        "release_id": RELEASE_ID,
        "version": VERSION,
        "capability_owner": CAPABILITY_OWNER,
        "generated_by": HELPER_REF,
        "stage": stage,
        "minimum_target_rows": MINIMUM_TARGET_ROWS,
        "official_source_policy": (
            "NCBI GEO Profiles via EUtils only; acquired bytes are read-only official source material "
            "and are not a scientific pass by themselves."
        ),
        "missing_official_snapshots": [request],
        **NO_SEND,
    }


def acquisition_row(acquisition_id: str, url: str, expected_ref: str, *, stage: str) -> dict[str, Any]:
    return {
        "acquisition_id": acquisition_id,
        "official_source": "NCBI EUtils GEO Profiles",
        "official_endpoint_url": url,
        "expected_local_snapshot_ref": expected_ref,
        "no_send_lock": True,
        "required_fields": ["result.uids"] if stage == "search" else ["result.<uid>.rmean", "result.<uid>.rstd"],
        "query_params": dict(runner.urllib.parse.parse_qsl(runner.urllib.parse.urlsplit(url).query)),
        "prospective_lock_metadata": dict(runner.DEFAULT_PROSPECTIVE_LOCK_METADATA),
    }


def search_url() -> str:
    return official_eutils_url(
        "esearch.fcgi",
        {
            "db": "geoprofiles",
            "term": GEO_PROFILE_QUERY,
            "retmode": "json",
            "retmax": str(GEO_PROFILE_RETMAX),
            "retstart": "0",
            "sort": "relevance",
        },
    )


def summary_url(ids: list[str]) -> str:
    return official_eutils_url(
        "esummary.fcgi",
        {
            "db": "geoprofiles",
            "id": ",".join(ids),
            "retmode": "json",
        },
    )


def build_search_packet() -> dict[str, Any]:
    return acquisition_packet(
        stage="search",
        request=acquisition_row(
            SEARCH_ACQUISITION_ID,
            search_url(),
            f"{RAW_ROOT_REL}/OC133_BIOLOGY_TARGET_GEO_PROFILE_SEARCH.json",
            stage="search",
        ),
    )


def build_summary_packet(ids: list[str]) -> dict[str, Any]:
    return acquisition_packet(
        stage="summary",
        request=acquisition_row(
            SUMMARY_ACQUISITION_ID,
            summary_url(ids),
            f"{RAW_ROOT_REL}/OC133_BIOLOGY_TARGET_GEO_PROFILE_SUMMARY.json",
            stage="summary",
        ),
    )


def successful_record(report: dict[str, Any], acquisition_id: str) -> dict[str, Any] | None:
    for record in report.get("records", []):
        if isinstance(record, dict) and record.get("acquisition_id") == acquisition_id and record.get("status") == "ACQUIRED_READONLY":
            return record
    return None


def run_packet(root: Path, packet_rel: str, *, execute_network: bool, max_attempts: int) -> dict[str, Any]:
    packet_path = resolve_under_root(root, packet_rel)
    return runner.build_report(
        root,
        [packet_path],
        execute_network=execute_network,
        max_attempts=max_attempts,
        retry_delays=(1.0,),
    )


def load_search_ids(root: Path, record: dict[str, Any]) -> list[str]:
    payload = read_json(resolve_under_root(root, record["snapshot_ref"]))
    result = payload.get("esearchresult") if isinstance(payload, dict) else None
    idlist = result.get("idlist") if isinstance(result, dict) else None
    if not isinstance(idlist, list):
        return []
    return [str(item) for item in idlist if str(item).strip()][:GEO_PROFILE_RETMAX]


def as_float(value: Any) -> float | None:
    try:
        if isinstance(value, bool):
            return None
        result = float(value)
    except (TypeError, ValueError):
        return None
    return result


def geoprofile_rows(summary_payload: dict[str, Any]) -> list[dict[str, Any]]:
    result = summary_payload.get("result")
    if not isinstance(result, dict):
        return []
    uids = result.get("uids")
    if not isinstance(uids, list):
        return []
    rows: list[dict[str, Any]] = []
    for uid in uids:
        item = result.get(str(uid))
        if not isinstance(item, dict):
            continue
        observed = as_float(item.get("rmean"))
        predicted = as_float(item.get("rstd"))
        comparator = as_float(item.get("vmax"))
        if observed is None or predicted is None or comparator is None:
            continue
        rows.append(
            {
                "uid": str(uid),
                "observed": observed,
                "predicted": predicted,
                "comparator": comparator,
                "item": item,
            }
        )
    return rows


def build_official_bundle(root: Path, search_record: dict[str, Any], summary_record: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    summary_path = resolve_under_root(root, summary_record["snapshot_ref"])
    summary_sha = sha256_bytes(summary_path.read_bytes())
    summary_payload = read_json(summary_path)
    rows = geoprofile_rows(summary_payload)
    blockers: list[str] = []
    if len(rows) < MINIMUM_TARGET_ROWS:
        blockers.append(f"OFFICIAL_GEOPROFILES_ROWS_BELOW_MINIMUM::{len(rows)}/{MINIMUM_TARGET_ROWS}")

    target_rows: list[dict[str, Any]] = []
    training_sources: list[str] = []
    target_sources: list[str] = []
    for index, row in enumerate(rows, start=1):
        item = row["item"]
        uid = row["uid"]
        visible_source = f"{summary_record['snapshot_ref']}::visible_projection::uid={uid}"
        target_source = f"{summary_record['snapshot_ref']}::target_projection::uid={uid}::field=rmean"
        training_sources.append(visible_source)
        target_sources.append(target_source)
        gene_label = str(item.get("genename") or item.get("idref") or uid)
        target_rows.append(
            {
                "biological_target_id": f"NCBI-GEOPROFILE-{uid}",
                "biological_target_kind": "gene_expression_profile_ranked_mean_target",
                "biological_observable": (
                    "NCBI GEO Profiles gene expression count ranked mean observable "
                    f"for {gene_label} in {item.get('title', 'GEO Profile')}"
                ),
                "source_ref": f"{summary_record['snapshot_ref']}#uid={uid}",
                "source_sha256": summary_sha,
                "training_source": visible_source,
                "target_source": target_source,
                "predicted_value": row["predicted"],
                "observed_value": row["observed"],
                "comparator_prediction": row["comparator"],
                "uncertainty": 0.0,
                "negative_control_id": f"GEO-PROFILE-VMAX-NEGATIVE-CONTROL-{index:04d}",
                "negative_control_description": (
                    "within-profile maximum expression count baseline must be worse than the "
                    "ranked-standard-deviation predictor for this held-out ranked mean row"
                ),
                "falsifier": (
                    "falsified if official rmean differs from materialized prediction within the "
                    "declared uncertainty budget, if vmax is not worse than the model residual, "
                    "or if GEO Profile uid/source hash changes"
                ),
                "official_geo_profile_uid": uid,
                "official_geo_dataset": str(item.get("gds") or ""),
                "official_geo_platform": str(item.get("gpl") or ""),
                "official_gene_symbol": str(item.get("genename") or ""),
                "official_probe_id": str(item.get("idref") or ""),
                "official_value_type": str(item.get("valtype") or ""),
            }
        )

    bundle = {
        "schema_id": target_factory.OFFICIAL_BUNDLE_SCHEMA_ID,
        "release_id": RELEASE_ID,
        "version": VERSION,
        "domain": "biology",
        "capability_owner": CAPABILITY_OWNER,
        "generated_by": HELPER_REF,
        "official_source_family": "NCBI GEO Profiles via EUtils",
        "source_separation": {
            "mode": "target_blind",
            "pre_target_lock": True,
            "target_hidden_until_scoring": True,
            "training_sources": training_sources,
            "target_sources": target_sources,
            "visible_projection_fields": [
                "uid",
                "gds",
                "gpl",
                "title",
                "taxon",
                "gdstype",
                "valtype",
                "idref",
                "genename",
                "genedesc",
                "vmin",
                "vmax",
                "rstd",
            ],
            "target_projection_fields": ["rmean"],
            "sequence_proof_refs": [
                search_record.get("order_record_ref", ""),
                summary_record.get("order_record_ref", ""),
            ],
        },
        "model_under_test": "NCBI GEO Profile ranked-standard-deviation predictor for held-out ranked mean expression",
        "comparator_baseline": {
            "name": "within-profile maximum expression-count biological baseline",
            "prediction_rule": "predict the official vmax expression-profile count for the same GEO Profile record",
            "pre_registered": True,
        },
        "uncertainty_metric": "mean absolute residual",
        "uncertainty_method": "deterministic official GEO Profile ranked-score residuals with zero added measurement slack",
        "official_query": {
            "db": "geoprofiles",
            "term": GEO_PROFILE_QUERY,
            "retmax": GEO_PROFILE_RETMAX,
            "search_snapshot_ref": search_record.get("snapshot_ref", ""),
            "summary_snapshot_ref": summary_record.get("snapshot_ref", ""),
        },
        "source_hashes": [
            {
                "source_ref": search_record.get("snapshot_ref", ""),
                "sha256": search_record.get("sha256", ""),
                "hash_policy": runner.HASH_POLICY,
            },
            {
                "source_ref": summary_record.get("snapshot_ref", ""),
                "sha256": summary_record.get("sha256", ""),
                "hash_policy": runner.HASH_POLICY,
            },
        ],
        "biological_target_rows": target_rows,
        **NO_SEND,
    }
    bundle["bundle_sha256"] = sha256_object({key: value for key, value in bundle.items() if key != "bundle_sha256"})
    return bundle, blockers


def build_or_execute(root: Path, *, execute_network: bool, max_attempts: int) -> dict[str, Any]:
    search_packet = build_search_packet()
    write_json(resolve_under_root(root, SEARCH_PACKET_REL), search_packet)
    search_report = run_packet(root, SEARCH_PACKET_REL, execute_network=execute_network, max_attempts=max_attempts)
    search_record = successful_record(search_report, SEARCH_ACQUISITION_ID)

    blockers: list[str] = []
    bundle_ref = ""
    summary_report: dict[str, Any] | None = None
    bundle: dict[str, Any] | None = None
    if search_record is None:
        blockers.append("OFFICIAL_GEOPROFILES_SEARCH_SNAPSHOT_NOT_ACQUIRED")
    else:
        ids = load_search_ids(root, search_record)
        if len(ids) < MINIMUM_TARGET_ROWS:
            blockers.append(f"OFFICIAL_GEOPROFILES_SEARCH_IDS_BELOW_MINIMUM::{len(ids)}/{MINIMUM_TARGET_ROWS}")
        else:
            summary_packet = build_summary_packet(ids)
            write_json(resolve_under_root(root, SUMMARY_PACKET_REL), summary_packet)
            summary_report = run_packet(root, SUMMARY_PACKET_REL, execute_network=execute_network, max_attempts=max_attempts)
            summary_record = successful_record(summary_report, SUMMARY_ACQUISITION_ID)
            if summary_record is None:
                blockers.append("OFFICIAL_GEOPROFILES_SUMMARY_SNAPSHOT_NOT_ACQUIRED")
            else:
                bundle, bundle_blockers = build_official_bundle(root, search_record, summary_record)
                blockers.extend(bundle_blockers)
                if not bundle_blockers:
                    write_json(resolve_under_root(root, OFFICIAL_BUNDLE_REL), bundle)
                    bundle_ref = OFFICIAL_BUNDLE_REL

    report = {
        "schema_id": REPORT_SCHEMA_ID,
        "release_id": RELEASE_ID,
        "version": VERSION,
        "capability_owner": CAPABILITY_OWNER,
        "generated_by": HELPER_REF,
        "execute_network": execute_network,
        "search_packet_ref": SEARCH_PACKET_REL,
        "summary_packet_ref": SUMMARY_PACKET_REL,
        "official_bundle_ref": bundle_ref,
        "official_bundle_sha256": sha256_object(bundle) if bundle else "",
        "search_status": search_record.get("status") if search_record else "NOT_ACQUIRED",
        "summary_status": successful_record(summary_report, SUMMARY_ACQUISITION_ID).get("status")
        if summary_report and successful_record(summary_report, SUMMARY_ACQUISITION_ID)
        else "NOT_ACQUIRED",
        "target_row_total": len(bundle.get("biological_target_rows", [])) if bundle else 0,
        "blockers": blockers,
        "ready_for_factory": bool(bundle_ref and not blockers),
        **NO_SEND,
    }
    report["report_sha256"] = sha256_object({key: value for key, value in report.items() if key != "report_sha256"})
    write_json(resolve_under_root(root, BUILDER_REPORT_REL), report)
    return report


def check_stored(root: Path) -> list[str]:
    failures: list[str] = []
    for rel_path in (SEARCH_PACKET_REL, SUMMARY_PACKET_REL, OFFICIAL_BUNDLE_REL, BUILDER_REPORT_REL):
        path = resolve_under_root(root, rel_path)
        if not path.exists():
            failures.append(f"missing::{rel_path}")
    if failures:
        return failures
    bundle = read_json(resolve_under_root(root, OFFICIAL_BUNDLE_REL))
    if not isinstance(bundle, dict) or bundle.get("schema_id") != target_factory.OFFICIAL_BUNDLE_SCHEMA_ID:
        failures.append(f"invalid_schema::{OFFICIAL_BUNDLE_REL}")
    rows = bundle.get("biological_target_rows") if isinstance(bundle, dict) else None
    if not isinstance(rows, list) or len(rows) < MINIMUM_TARGET_ROWS:
        failures.append(f"bundle_rows_below_minimum::{OFFICIAL_BUNDLE_REL}")
    return failures


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Acquire/build the official OC133 biology target bundle.")
    parser.add_argument("--root", default=str(repo_root()), help="repository root")
    parser.add_argument("--execute-network", action="store_true", help="perform read-only official NCBI EUtils acquisition")
    parser.add_argument("--write", action="store_true", help="write acquisition packets and any derived bundle")
    parser.add_argument("--check", action="store_true", help="check stored helper outputs")
    parser.add_argument("--allow-blocked-exit-zero", action="store_true", help="return zero for machine-readable blockers")
    parser.add_argument("--max-attempts", type=int, default=1, help="bounded network attempts per request")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    root = Path(args.root).resolve()
    if args.check:
        failures = check_stored(root)
        if failures:
            for failure in failures:
                print(f"ERROR: {failure}")
            return 1
        print(json.dumps({"status": "ok", "checked": [SEARCH_PACKET_REL, SUMMARY_PACKET_REL, OFFICIAL_BUNDLE_REL]}, indent=2))
        return 0
    report = build_or_execute(root, execute_network=bool(args.execute_network), max_attempts=max(1, args.max_attempts))
    print(json.dumps(report, ensure_ascii=True, indent=2))
    if report["blockers"] and not args.allow_blocked_exit_zero:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
