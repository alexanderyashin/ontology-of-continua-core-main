from __future__ import annotations

import json
from pathlib import Path

import jsonschema
import pytest


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_DIR = ROOT / "schemas"
PUBLIC_DATA_DIR = ROOT / "web" / "public" / "data"


def load_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.mark.parametrize(
    ("schema_name", "data_name"),
    [
        ("oc_atlas.schema.json", "oc_atlas.json"),
        ("oc_universe_atlas.schema.json", "oc_universe_atlas.json"),
    ],
)
def test_public_data_files_validate_against_declared_schemas(schema_name: str, data_name: str) -> None:
    schema = load_json(SCHEMA_DIR / schema_name)
    data = load_json(PUBLIC_DATA_DIR / data_name)
    jsonschema.Draft202012Validator.check_schema(schema)
    jsonschema.validate(data, schema)


def test_all_public_data_json_files_parse_cleanly() -> None:
    failures: list[str] = []
    for path in sorted(PUBLIC_DATA_DIR.glob("*.json")):
        try:
            load_json(path)
        except Exception as exc:  # pragma: no cover - failure message path
            failures.append(f"{path.name}: {exc}")
    assert failures == []
