from __future__ import annotations

import json
from pathlib import Path

from benchmark.schemas import EXPORTED_MODELS, export_json_schemas


def test_all_schema_snapshots_export(tmp_path: Path) -> None:
    assert export_json_schemas(tmp_path) == len(EXPORTED_MODELS)
    assert {path.name for path in tmp_path.glob("*.json")} == set(EXPORTED_MODELS)


def test_unknown_schema_snapshot_has_no_leakage_fields(tmp_path: Path) -> None:
    export_json_schemas(tmp_path)
    schema = json.loads((tmp_path / "unknown-target-request.schema.json").read_text())
    properties = schema["properties"]
    assert not {"target_text", "intended_text", "context", "prompt"} & properties.keys()
    assert schema["additionalProperties"] is False
