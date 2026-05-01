from __future__ import annotations

import argparse
import hashlib
import json
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any


RELEASE_ID = "oc_core_1_3_3"
VERSION = "1.3.3"
CAPABILITY_OWNER = "Logion IT/Research"
SCHEMA_ID = "OC133_BIOLOGY_SYSTEMS_ACQUISITION_PLAN_v1"
REPORT_SCHEMA_ID = "OC133_BIOLOGY_SYSTEMS_ACQUISITION_REPORT_v1"
BLOCKER_ID = "grand_toe_empirical_superiority"
PLANNER_REF = "tools/oc133_biology_systems_acquisition_planner.py"
ROOT = Path(__file__).resolve().parents[1]

REQUIREMENTS_REL = "benchmarks/grand_science/domain_requirements.json"
EVIDENCE_SCHEMA_REL = "validation/grand_science/grand_empirical_evidence.schema.json"
PROTOCOL_SCHEMA_REL = "validation/grand_science/grand_empirical_protocol.schema.json"
BIOLOGY_DEFAULT_SNAPSHOT_REL = "validation/_raw/biology_ncbi_geo_platform.txt"
SYSTEMS_DEFAULT_SNAPSHOT_REL = "validation/_raw/systems_world_bank_gdp.txt"
REGISTRY_REL = "validation/heldout/grand_science_evidence_registry.json"

OUTPUT_ROOT_REL = "validation/heldout/acquisition_plans/biology_systems"
PLAN_REL = f"{OUTPUT_ROOT_REL}/OC133_BIOLOGY_SYSTEMS_ACQUISITION_PLAN.json"
REPORT_REL = f"{OUTPUT_ROOT_REL}/OC133_BIOLOGY_SYSTEMS_ACQUISITION_REPORT.json"
BIOLOGY_TEMPLATE_REL = f"{OUTPUT_ROOT_REL}/biology_candidate_pack_template.json"
SYSTEMS_TEMPLATE_REL = f"{OUTPUT_ROOT_REL}/systems_candidate_pack_template.json"


KNOWN_ENDPOINTS: dict[str, list[dict[str, str]]] = {
    "biology": [
        {
            "name": "NCBI GEO ESearch API endpoint",
            "url": "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi",
            "query_hint": "term=GPL96[Accession]&retmode=json&retmax=20&retstart=0&db=gds",
            "official_ref": "https://www.ncbi.nlm.nih.gov",
        }
    ],
    "systems": [
        {
            "name": "World Bank WDI API endpoint",
            "url": "https://api.worldbank.org/v2/country/1W/indicator/NY.GDP.MKTP.CD",
            "query_hint": "format=json&per_page=5",
            "official_ref": "https://api.worldbank.org/",
        }
    ],
}


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def ordered_unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result


def resolve_under_root(root: Path, ref: str) -> Path | None:
    try:
        path = (root / ref).resolve()
        path.relative_to(root.resolve())
        return path
    except (OSError, ValueError):
        return None


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def lf_normalized_bytes(path: Path) -> bytes:
    return path.read_bytes().replace(b"\r\n", b"\n")


def sha256_of_file(path: Path) -> str:
    return hashlib.sha256(lf_normalized_bytes(path)).hexdigest()


def default_requirements() -> dict[str, Any]:
    return {
        "schema_id": "OC133_GRAND_EMPIRICAL_DOMAIN_REQUIREMENTS_v1",
        "release_id": RELEASE_ID,
        "capability_owner": "Research/EmpiricalScience",
        "minimum_per_domain_n": 20,
        "required_source_separation_modes": ["target_blind", "prospective"],
        "required_domains": ["biology", "chemistry", "mathematics", "physics", "systems"],
        "support_policy": "source separation and preregistration must be verifiable before target scoring; bounded snapshots are blocked.",
    }


def load_requirements(root: Path) -> dict[str, Any]:
    path = resolve_under_root(root, REQUIREMENTS_REL)
    if path is None or not path.exists():
        return default_requirements()
    return read_json(path)


def load_schema_fields(root: Path, ref: str) -> dict[str, Any]:
    path = resolve_under_root(root, ref)
    if path is None or not path.exists():
        return {}
    return read_json(path)


def read_bounded_float(value: Any) -> float | None:
    try:
        if isinstance(value, bool):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def parse_biology_snapshot(snapshot_ref: str, path: Path) -> tuple[dict[str, Any], list[str], int]:
    payload = read_json(path)
    blockers: list[str] = []
    if not isinstance(payload, dict):
        return {}, [f"SNAPSHOT_NOT_OBJECT::{path}"], 0
    esearch = payload.get("esearchresult")
    if not isinstance(esearch, dict):
        return {}, [f"SNAPSHOT_MISSING_ESEARCHRESULT::{path}"], 0

    idlist = esearch.get("idlist")
    if not isinstance(idlist, list):
        blockers.append("SNAPSHOT_BIOLOGY_IDLIST_MISSING_OR_INVALID")
        idlist = []

    try:
        retstart = int(esearch.get("retstart", 0))
    except (TypeError, ValueError):
        blockers.append("SNAPSHOT_BIOLOGY_RETSTART_INVALID")
        retstart = 0

    try:
        retmax = int(esearch.get("retmax", 0))
    except (TypeError, ValueError):
        blockers.append("SNAPSHOT_BIOLOGY_RETMAX_INVALID")
        retmax = len(idlist)

    try:
        total_count = int(esearch.get("count", retmax))
    except (TypeError, ValueError):
        blockers.append("SNAPSHOT_BIOLOGY_TOTAL_COUNT_INVALID")
        total_count = retmax

    predicted = float(retstart + len(idlist))
    observed = float(retmax)
    comparator_prediction = float(total_count)
    formula = "retstart + len(idlist)"
    uncertainty = max(0.0, observed * 0.02)
    model_residual = abs(predicted - observed)
    comparator_residual = abs(comparator_prediction - observed)
    training_source = f"{snapshot_ref}::visible_fields(retstart,idlist)"
    target_source = f"{snapshot_ref}::withheld_field(retmax)"

    observation_rows = [
        {
            "observation_id": "BIOLOGY-BOUNDED-NCBI-GEO-001",
            "training_source": training_source,
            "target_source": target_source,
            "formula": formula,
            "predicted_value": predicted,
            "observed_value": observed,
            "comparator_prediction": comparator_prediction,
            "uncertainty": uncertainty,
            "negative_control_id": "biology-gene-expression-count-bounded-control",
            "negative_control_description": "if target-blind replay exceeds comparator residual, the comparator is not rejected",
            "falsifier": "comparator residual not worse than model residual",
        }
    ]

    return {
        "snapshot_kind": "bounded_ncbi_geo_replay",
        "source_mode": "target_blind",
        "model_under_test": formula,
        "comparator_baseline": {
            "name": "NCBI GEO total hit count",
            "prediction_rule": "use esearchresult.count as the GEO count baseline prediction",
            "pre_registered": False,
        },
        "uncertainty_metric": "mean absolute residual",
        "uncertainty_method": "bounded replay residual budget",
        "model_residual": model_residual,
        "comparator_residual": comparator_residual,
        "training_sources": [
            training_source,
        ],
        "target_sources": [target_source],
        "observation_rows": observation_rows,
    }, blockers, 1


def parse_systems_snapshot(snapshot_ref: str, path: Path) -> tuple[dict[str, Any], list[str], int]:
    payload = read_json(path)
    blockers: list[str] = []
    if not isinstance(payload, list) or len(payload) < 2:
        return {}, ["SNAPSHOT_SYSTEMS_STRUCTURE_INVALID"], 0
    rows = payload[1]
    if not isinstance(rows, list):
        return {}, ["SNAPSHOT_SYSTEMS_DATA_INVALID"], 0

    values: dict[int, float] = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        year_raw = row.get("date")
        converted_value = read_bounded_float(row.get("value"))
        try:
            year = int(year_raw)
        except (TypeError, ValueError):
            continue
        if converted_value is not None:
            values[year] = converted_value

    if not values:
        return {}, ["SNAPSHOT_SYSTEMS_NO_NUMERIC_VALUE_ROWS"], 0

    available_years = sorted(values)
    target_year = available_years[-1]
    target_source = f"{snapshot_ref}::year:{target_year}"
    if target_year < 2:
        return {}, ["SNAPSHOT_SYSTEMS_TARGET_YEAR_INVALID"], 0
    comparator_year = target_year - 1
    training_years = [target_year - 3, target_year - 2, target_year - 1]
    training_values = [values.get(year) for year in training_years]
    observed = values[target_year]
    comparator = values.get(comparator_year)
    if comparator is None:
        blockers.append(f"SNAPSHOT_SYSTEMS_COMPARATOR_YEAR_MISSING::{comparator_year}")
        comparator = observed
    if any(value is None for value in training_values):
        blockers.append(f"SNAPSHOT_SYSTEMS_TRAINING_YEARS_MISSING::{','.join(map(str, training_years))}")
        predicted = observed
    else:
        base, _, _ = training_values
        predicted = comparator + (comparator - base) / 2.0
    formula = f"GDP_{comparator_year} + (GDP_{comparator_year} - GDP_{training_years[0]}) / 2"
    uncertainty = observed * 0.01
    observation_rows = [
        {
            "observation_id": f"SYSTEMS-BOUNDED-WDI-GDP-{target_year}",
            "training_source": f"{snapshot_ref}::years({training_years[0]},{training_years[1]},{training_years[2]})",
            "target_source": target_source,
            "formula": formula,
            "predicted_value": float(predicted),
            "observed_value": float(observed),
            "comparator_prediction": float(comparator),
            "uncertainty": float(uncertainty),
            "negative_control_id": "systems-wdi-gdp-last-observation-control",
            "negative_control_description": "GDP carry-forward baseline should remain a valid comparator only if it is worse than the model on held-out horizon",
            "falsifier": "comparator residual not worse than model residual",
        }
    ]
    if uncertainty == 0.0:
        blockers.append("SNAPSHOT_SYSTEMS_ZERO_UNCERTAINTY")

    return {
        "snapshot_kind": "bounded_world_bank_wdi_replay",
        "source_mode": "target_blind",
        "model_under_test": formula,
        "comparator_baseline": {
            "name": "World Bank GDP carry-forward comparator",
            "prediction_rule": "predict next year as previous year",
            "pre_registered": False,
        },
        "uncertainty_metric": "mean absolute residual",
        "uncertainty_method": "bounded replay budget over one held-out GDP year",
        "model_residual": abs(float(predicted) - float(observed)),
        "comparator_residual": abs(float(comparator) - float(observed)),
        "training_sources": [
            f"{snapshot_ref}::years({training_years[0]},{training_years[1]},{training_years[2]})",
            f"{snapshot_ref}::years({training_years[0]-1},{training_years[0]},{training_years[1]})",
        ],
        "target_sources": [target_source],
        "observation_rows": observation_rows,
    }, blockers, 1


def required_source_separation(requirements: dict[str, Any]) -> dict[str, Any]:
    return {
        "mode_options": list(requirements.get("required_source_separation_modes", ["target_blind", "prospective"])),
        "pre_target_lock": True,
        "target_hidden_until_scoring": True,
    }


def validate_source_separation(source: dict[str, Any], allowed_modes: list[str]) -> tuple[dict[str, Any], list[str]]:
    if not isinstance(source, dict):
        return {
            "mode": None,
            "pre_target_lock": None,
            "target_hidden_until_scoring": None,
            "training_sources": [],
            "target_sources": [],
        }, ["SOURCE_SEPARATION_NOT_OBJECT"]

    current = {
        "mode": source.get("mode"),
        "pre_target_lock": source.get("pre_target_lock"),
        "target_hidden_until_scoring": source.get("target_hidden_until_scoring"),
        "training_sources": source.get("training_sources", []),
        "target_sources": source.get("target_sources", []),
    }

    blockers: list[str] = []
    if not isinstance(current["training_sources"], list) or not current["training_sources"]:
        blockers.append("TRAINING_SOURCES_MISSING")
    if not isinstance(current["target_sources"], list) or not current["target_sources"]:
        blockers.append("TARGET_SOURCES_MISSING")
    else:
        if any(not isinstance(item, str) or not item.strip() for item in current["target_sources"]):
            blockers.append("SOURCE_REFERENCES_MUST_BE_STRINGS")
        if any(
            item in current["target_sources"]
            for item in current["training_sources"]
            if isinstance(current["training_sources"], list)
        ):
            blockers.append("TRAINING_TARGET_SOURCE_OVERLAP")

    if current["pre_target_lock"] is not True:
        blockers.append("PRE_TARGET_LOCK_REQUIRED")
    if current["target_hidden_until_scoring"] is not True:
        blockers.append("TARGET_HIDDEN_UNTIL_SCORING_REQUIRED")

    if current["mode"] and current["mode"] not in allowed_modes:
        blockers.append(f"SOURCE_SEPARATION_MODE_NOT_ALLOWED::{current['mode']}")

    return current, ordered_unique(blockers)


def _resolve_endpoint_rows(endpoints: list[dict[str, str]], run_check: bool, timeout: float) -> list[dict[str, Any]]:
    if not endpoints:
        return []
    rows: list[dict[str, Any]] = []
    for endpoint in endpoints:
        url_base = endpoint.get("url", "")
        if not url_base:
            continue
        split = urllib.parse.urlsplit(url_base)
        target = urllib.parse.urlunsplit((split.scheme, split.netloc, split.path, endpoint.get("query_hint", ""), ""))
        row = {
            "name": endpoint.get("name", "official_endpoint"),
            "url": target,
            "official_ref": endpoint.get("official_ref", ""),
            "reachable": None,
        }
        if run_check:
            try:
                request = urllib.request.Request(target, method="HEAD")
                with urllib.request.urlopen(request, timeout=timeout) as response:
                    row["status"] = int(response.status)
                    row["reachable"] = str(response.status).startswith("2")
            except (OSError, urllib.error.URLError, ValueError):
                row["reachable"] = False
                row["status"] = None
        rows.append(row)
    return rows


def plan_row(
    root: Path,
    domain: str,
    snapshot_ref: str,
    minimum_n: int,
    requirements: dict[str, Any],
    evidence_schema: dict[str, Any],
    run_endpoint_checks: bool,
    endpoint_timeout: float,
) -> dict[str, Any]:
    snapshot_path = resolve_under_root(root, snapshot_ref)
    blockers: list[str] = []
    if snapshot_path is None:
        blockers.append(f"SNAPSHOT_REF_NOT_UNDER_ROOT::{snapshot_ref}")
        snapshot_payload: dict[str, Any] = {}
        current_n = 0
        source_snapshot: dict[str, Any] = {"training_sources": [], "target_sources": []}
    elif not snapshot_path.exists():
        blockers.append(f"SNAPSHOT_MISSING::{snapshot_ref}")
        snapshot_payload = {}
        current_n = 0
        source_snapshot = {"training_sources": [], "target_sources": []}
    else:
        if domain == "biology":
            snapshot_payload, parse_blockers, current_n = parse_biology_snapshot(snapshot_ref, snapshot_path)
        else:
            snapshot_payload, parse_blockers, current_n = parse_systems_snapshot(snapshot_ref, snapshot_path)
        blockers.extend(parse_blockers)
        source_snapshot = {
            "training_sources": snapshot_payload.get("training_sources", []),
            "target_sources": snapshot_payload.get("target_sources", []),
        }

    if current_n == 0:
        blockers.append(f"{domain.upper()}_CURRENT_N_NOT_AVAILABLE")
    if current_n < minimum_n:
        blockers.append(f"N_BELOW_MINIMUM::{current_n}/{minimum_n}")

    source_requirements = required_source_separation(requirements)
    current_source = {
        "mode": snapshot_payload.get("source_mode"),
        "pre_target_lock": False,
        "target_hidden_until_scoring": False,
        "training_sources": source_snapshot.get("training_sources", []),
        "target_sources": source_snapshot.get("target_sources", []),
    }
    validation_source, source_blockers = validate_source_separation(current_source, source_requirements["mode_options"])
    blockers.extend(source_blockers)
    if snapshot_payload.get("snapshot_kind") is None:
        blockers.append("SNAPSHOT_KIND_UNKNOWN")

    comparator = snapshot_payload.get("comparator_baseline", {})
    if not comparator.get("pre_registered"):
        blockers.append("COMPARATOR_BASELINE_NOT_PREREGISTERED")

    uncertainty_metric = str(snapshot_payload.get("uncertainty_metric", "mean absolute residual"))
    uncertainty_method = str(snapshot_payload.get("uncertainty_method", "unresolved"))
    snapshot_uncertainty = snapshot_payload.get("uncertainty", None)
    if isinstance(snapshot_uncertainty, (int, float)):
        interval = [max(0.0, float(snapshot_payload.get("model_residual", 0.0)) - float(snapshot_uncertainty)), float(snapshot_payload.get("model_residual", 0.0)) + float(snapshot_uncertainty)]
    else:
        interval = [max(0.0, float(snapshot_payload.get("model_residual", 0.0)) * 0.5), float(snapshot_payload.get("model_residual", 0.0)) * 1.5]
    if not snapshot_payload.get("uncertainty_metric"):
        blockers.append("UNCERTAINTY_METRIC_MISSING")
    if not snapshot_payload.get("uncertainty_method"):
        blockers.append("UNCERTAINTY_METHOD_MISSING")

    negative_controls = [
        {
            "id": "NORMED_RESIDUAL_NEGATIVE_CONTROL",
            "description": "comparator residual must be strictly larger than model residual",
        }
    ]
    falsifiers = [obs.get("falsifier") for obs in snapshot_payload.get("observation_rows", []) if isinstance(obs, dict)]
    if not falsifiers:
        falsifiers = ["comparator residual must exceed model residual for every target"]

    official_refs = [
        {
            "kind": "raw_snapshot",
            "ref": snapshot_ref,
            "sha256": sha256_of_file(snapshot_path) if snapshot_path and snapshot_path.exists() else "",
            "byte_count": snapshot_path.stat().st_size if snapshot_path and snapshot_path.exists() else 0,
        }
    ]
    if snapshot_path and snapshot_path.exists():
        official_refs.extend(_resolve_endpoint_rows(KNOWN_ENDPOINTS.get(domain, []), run_endpoint_checks, endpoint_timeout))

    schema_const = "OC133_GRAND_EMPIRICAL_EVIDENCE_v1"
    if isinstance(evidence_schema, dict):
        schema_const = evidence_schema.get("properties", {}).get("schema_id", {}).get("const", schema_const)

    candidate_pack_template = {
        "schema_id": schema_const,
        "release_id": RELEASE_ID,
        "capability_owner": "Research/EmpiricalScience",
        "evidence_pack_id": f"oc-core-1-3-3-{domain}-bounded-acquisition-template",
        "domain": domain,
        "source_separation": {
            "mode": validation_source.get("mode"),
            "pre_target_lock": bool(validation_source.get("pre_target_lock")),
            "target_hidden_until_scoring": bool(validation_source.get("target_hidden_until_scoring")),
            "training_sources": validation_source.get("training_sources", []),
            "target_sources": validation_source.get("target_sources", []),
        },
        "n": int(current_n),
        "model_under_test": str(snapshot_payload.get("model_under_test", "")),
        "comparator_baseline": {
            "name": str(comparator.get("name", "")),
            "prediction_rule": str(comparator.get("prediction_rule", "")),
            "pre_registered": bool(comparator.get("pre_registered")),
        },
        "uncertainty": {
            "metric": uncertainty_metric,
            "method": uncertainty_method,
            "interval": interval,
        },
        "residuals": {
            "model": float(snapshot_payload.get("model_residual", 0.0)),
            "comparator": float(snapshot_payload.get("comparator_residual", 0.0)),
            "superiority_margin": float(snapshot_payload.get("comparator_residual", 0.0)) - float(snapshot_payload.get("model_residual", 0.0)),
        },
        "negative_controls": [
            {
                "control_id": item["id"],
                "description": item["description"],
                "rejected": float(snapshot_payload.get("comparator_residual", 0.0)) > float(snapshot_payload.get("model_residual", 0.0)),
            }
            for item in negative_controls
        ],
        "falsifiers": [str(item) for item in falsifiers],
        "grand_toe_support_allowed": False,
    }

    blockers = ordered_unique(blockers)
    return {
        "domain": domain,
        "snapshot_ref": snapshot_ref,
        "snapshot_kind": snapshot_payload.get("snapshot_kind", "unavailable"),
        "snapshot_sha256": sha256_of_file(snapshot_path) if snapshot_path and snapshot_path.exists() else "",
        "snapshot_byte_count": snapshot_path.stat().st_size if snapshot_path and snapshot_path.exists() else 0,
        "schema_refs": {
            "evidence": EVIDENCE_SCHEMA_REL,
            "protocol": PROTOCOL_SCHEMA_REL,
            "requirements": REQUIREMENTS_REL,
        },
        "required_source_separation": source_requirements,
        "current_source_separation": validation_source,
        "required_n": minimum_n,
        "current_n": int(current_n),
        "missing_n": max(0, minimum_n - current_n),
        "model_under_test": str(snapshot_payload.get("model_under_test", "")),
        "comparator_choices": [snapshot_payload.get("comparator_baseline", {})],
        "residual_protocol": {
            "metric": uncertainty_metric,
            "method": uncertainty_method,
            "model_residual": float(snapshot_payload.get("model_residual", 0.0)),
            "comparator_residual": float(snapshot_payload.get("comparator_residual", 0.0)),
            "uncertainty_interval": interval,
        },
        "uncertainty_protocol": {
            "metric": uncertainty_metric,
            "method": uncertainty_method,
            "interval": interval,
        },
        "negative_controls": [f"{item['id']}: {item['description']}" for item in negative_controls],
        "falsifiers": [str(item) for item in falsifiers],
        "official_source_refs": official_refs,
        "observation_rows": snapshot_payload.get("observation_rows", []),
        "blockers": blockers,
        "candidate_pack_template": candidate_pack_template,
        "pack_template_ref": BIOLOGY_TEMPLATE_REL if domain == "biology" else SYSTEMS_TEMPLATE_REL,
        "evidence_schema_fields": evidence_schema.get("required", []),
        "protocol_schema_fields": load_schema_fields(root, PROTOCOL_SCHEMA_REL).get("required", []),
        "status": "BLOCKED_PENDING_GENUINE_EVIDENCE_PLAN" if blockers else "READY_FOR_ACQUISITION_REVIEW",
        "grand_toe_support_allowed": len(blockers) == 0,
    }


def build_plan_payload(
    root: Path,
    biology_snapshot_ref: str = BIOLOGY_DEFAULT_SNAPSHOT_REL,
    systems_snapshot_ref: str = SYSTEMS_DEFAULT_SNAPSHOT_REL,
    run_endpoint_checks: bool = False,
    endpoint_timeout: float = 2.0,
) -> dict[str, Any]:
    requirements = load_requirements(root)
    evidence_schema = load_schema_fields(root, EVIDENCE_SCHEMA_REL)
    minimum_n = int(requirements.get("minimum_per_domain_n", 20))
    rows = [
        plan_row(
            root,
            "biology",
            biology_snapshot_ref,
            minimum_n,
            requirements,
            evidence_schema,
            run_endpoint_checks,
            endpoint_timeout,
        ),
        plan_row(
            root,
            "systems",
            systems_snapshot_ref,
            minimum_n,
            requirements,
            evidence_schema,
            run_endpoint_checks,
            endpoint_timeout,
        ),
    ]
    open_blocker_total = sum(1 for row in rows if row["status"] != "READY_FOR_ACQUISITION_REVIEW")
    blocker_total = sum(len(row["blockers"]) for row in rows)
    return {
        "schema_id": SCHEMA_ID,
        "release_id": RELEASE_ID,
        "version": VERSION,
        "planner": PLANNER_REF,
        "capability_owner": CAPABILITY_OWNER,
        "blocker_id": BLOCKER_ID,
        "requirements_ref": REQUIREMENTS_REL,
        "schema_refs": {
            "evidence": EVIDENCE_SCHEMA_REL,
            "protocol": PROTOCOL_SCHEMA_REL,
        },
        "output_root_ref": OUTPUT_ROOT_REL,
        "plan_ref": PLAN_REL,
        "required_n": minimum_n,
        "required_source_modes": list(requirements.get("required_source_separation_modes", ["target_blind", "prospective"])),
        "required_domains": ["biology", "systems"],
        "open_blocker_total": open_blocker_total,
        "blocker_total": blocker_total,
        "blocked_domain_total": open_blocker_total,
        "rows": rows,
        "source_endpoint_checks_requested": bool(run_endpoint_checks),
        "endpoint_timeout_seconds": endpoint_timeout,
        "no_send": True,
        "publish_allowed": False,
        "journal_submissions_allowed": False,
        "grand_toe_support_allowed": open_blocker_total == 0,
        "verdict": (
            "READY_FOR_REGISTRY_REVIEW_PENDING_PREREGISTRATION"
            if open_blocker_total == 0
            else "BLOCKED_PENDING_GENUINE_BIOLOGY_SYSTEMS_ACQUISITION"
        ),
    }


def build_report_payload(plan_payload: dict[str, Any]) -> dict[str, Any]:
    rows = []
    for row in plan_payload.get("rows", []):
        rows.append(
            {
                "domain": row.get("domain"),
                "status": row.get("status"),
                "required_n": row.get("required_n"),
                "current_n": row.get("current_n"),
                "missing_n": row.get("missing_n"),
                "snapshot_ref": row.get("snapshot_ref"),
                "template_ref": row.get("pack_template_ref"),
                "blocker_total": len(row.get("blockers", [])),
                "blockers": row.get("blockers", []),
                "grand_toe_support_allowed": row.get("grand_toe_support_allowed"),
            }
        )
    blocked_rows = [row for row in rows if row["status"] != "READY_FOR_ACQUISITION_REVIEW"]
    return {
        "schema_id": REPORT_SCHEMA_ID,
        "release_id": RELEASE_ID,
        "version": VERSION,
        "planner": PLANNER_REF,
        "capability_owner": CAPABILITY_OWNER,
        "requirements_ref": REQUIREMENTS_REL,
        "output_root_ref": OUTPUT_ROOT_REL,
        "required_domain_total": len(rows),
        "blocked_domain_total": len(blocked_rows),
        "open_blocker_total": len(blocked_rows),
        "grand_toe_support_allowed": len(blocked_rows) == 0,
        "rows": rows,
        "plan_ref": PLAN_REL,
        "report_ref": REPORT_REL,
        "registry_ref": REGISTRY_REL,
        "verdict": (
            "READY_WITH_OPEN_ACQUISITION_PLAN"
            if len(blocked_rows) == 0
            else "BLOCKED_PENDING_GENUINE_BIOLOGY_SYSTEMS_EVIDENCE"
        ),
        "no_send": True,
        "publish_allowed": False,
        "journal_submissions_allowed": False,
    }


def build_payload(
    root: Path,
    biology_snapshot_ref: str = BIOLOGY_DEFAULT_SNAPSHOT_REL,
    systems_snapshot_ref: str = SYSTEMS_DEFAULT_SNAPSHOT_REL,
    run_endpoint_checks: bool = False,
    endpoint_timeout: float = 2.0,
) -> dict[str, Any]:
    plan = build_plan_payload(
        root,
        biology_snapshot_ref=biology_snapshot_ref,
        systems_snapshot_ref=systems_snapshot_ref,
        run_endpoint_checks=run_endpoint_checks,
        endpoint_timeout=endpoint_timeout,
    )
    report = build_report_payload(plan)
    return {"plan": plan, "report": report}


def write_outputs(
    root: Path,
    biology_snapshot_ref: str = BIOLOGY_DEFAULT_SNAPSHOT_REL,
    systems_snapshot_ref: str = SYSTEMS_DEFAULT_SNAPSHOT_REL,
    run_endpoint_checks: bool = False,
    endpoint_timeout: float = 2.0,
) -> dict[str, Any]:
    payload = build_payload(
        root,
        biology_snapshot_ref=biology_snapshot_ref,
        systems_snapshot_ref=systems_snapshot_ref,
        run_endpoint_checks=run_endpoint_checks,
        endpoint_timeout=endpoint_timeout,
    )
    write_json(root / PLAN_REL, payload["plan"])
    write_json(root / REPORT_REL, payload["report"])
    for row in payload["plan"]["rows"]:
        write_json(root / row["pack_template_ref"], row["candidate_pack_template"])
    return payload["report"]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Plan official-data biology/systems acquisition blockers.")
    parser.add_argument("--root", default=str(ROOT), help="repository root")
    parser.add_argument("--write", action="store_true", help="write deterministic plan/report and templates")
    parser.add_argument("--allow-blocked-exit-zero", action="store_true", help="return zero even if blocked")
    parser.add_argument("--check-source-endpoints", action="store_true", help="perform read-only bounded endpoint checks")
    parser.add_argument("--endpoint-timeout", default=2.0, type=float, help="endpoint check timeout in seconds")
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    payload = build_payload(
        root,
        run_endpoint_checks=args.check_source_endpoints,
        endpoint_timeout=args.endpoint_timeout,
    )
    if args.write:
        write_outputs(
            root,
            run_endpoint_checks=args.check_source_endpoints,
            endpoint_timeout=args.endpoint_timeout,
        )
    print(json.dumps(payload["report"], ensure_ascii=False, indent=2))
    if payload["report"]["open_blocker_total"] == 0:
        return 0
    return 0 if args.allow_blocked_exit_zero else 2


if __name__ == "__main__":
    raise SystemExit(main())
