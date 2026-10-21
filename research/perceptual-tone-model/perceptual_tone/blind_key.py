"""Post-seal metadata join. Cannot select, order, render, score, or infer anything."""

from .blind_packet import LEARNER, NATIVE, OUTPUT, require
from .common import PACKAGE, digest, file_hash, read_json, read_rows, write_json

RESULTS = PACKAGE / "data/generated/learner-transfer-v1-20261019/primary"


def attach_key(destination=OUTPUT):
    seal = read_json(destination / "private/selection-seal.json")
    selection_path = destination / "private/selection.json"
    manifest_path = destination / "private/packet-manifest.json"
    require(file_hash(selection_path) == seal["selection_sha256"], "selection_changed_before_join")
    require(
        file_hash(manifest_path) == seal["manifest_file_sha256"], "manifest_changed_before_join"
    )
    require(digest(read_json(manifest_path)) == seal["packet_sha256"], "packet_changed_before_join")
    public_path = destination / "qa/index.html"
    html_sha = file_hash(public_path)
    selection = read_json(selection_path)
    learners = {r["example_id"]: r for r in read_rows(LEARNER / "primary.jsonl")}
    controls = {r["example_id"]: r["original"] for r in read_rows(NATIVE / "manifest.jsonl")}
    # The first semantic access to saved model results occurs ONLY after both seals
    # above have been checked. No result is returned to the packet builder.
    results_seal = read_json(RESULTS / "results-seal.json")
    predictions_path = RESULTS / "predictions.jsonl"
    require(
        file_hash(predictions_path) == results_seal["files"]["predictions.jsonl"],
        "saved_predictions_changed",
    )
    predictions = {r["example_id"]: r for r in read_rows(predictions_path)}
    require(set(predictions) == set(learners), "saved_result_population_changed")
    items = []
    for presentation in selection["presentation_order"]:
        ident = presentation["unit_id"]
        is_learner = presentation["base_role"] == "learner"
        row = learners[ident] if is_learner else controls[ident]
        saved = predictions.get(ident)
        unit = next(u for u in selection["units"] if u["unit_id"] == ident)
        items.append(
            {
                **presentation,
                "source_id": unit["source_id"],
                "speaker_id": unit["speaker_id"],
                "learner_take": [s["path"] for s in row["original_sources"]]
                if is_learner
                else None,
                "native_control_gold_tone": unit["gold"],
                "native_gold_basis": None if is_learner else "trusted AISHELL-3 corpus read label",
                "lexical_tone": row.get("intended_lexical_tone")
                if is_learner
                else row.get("lexical_tone"),
                "expected_surface_tone": row.get("expected_surface_tone"),
                "surface_alternatives": row.get("surface_alternatives"),
                "expanded_model_result": saved["expanded"] if saved else None,
                "pilot_model_result": saved["pilot"] if saved else None,
                "deterministic_result": saved["deterministic"] if saved else None,
                "result_availability": "existing_frozen_primary_results"
                if saved
                else "not_joined_for_controls_no_new_inference",
                "realized_learner_tone": None,
            }
        )
    key = {
        "schema": "benma-realized-tone-private-key-v1",
        "packet_version": read_json(manifest_path)["packet_version"],
        "packet_sha256": seal["packet_sha256"],
        "selection_sha256": seal["selection_sha256"],
        "saved_predictions_sha256": file_hash(predictions_path),
        "join_stage": "AFTER_SELECTION_ORDER_AUDIO_AND_PUBLIC_PAGE_FROZEN",
        "model_results_used_for_selection": False,
        "analysis_performed": False,
        "items": items,
    }
    write_json(destination / "private/answer-key.json", key)
    require(file_hash(public_path) == html_sha, "public_page_changed_by_key_join")
    return {
        "items": len(items),
        "packet_sha256": seal["packet_sha256"],
        "private_key_sha256": file_hash(destination / "private/answer-key.json"),
    }
