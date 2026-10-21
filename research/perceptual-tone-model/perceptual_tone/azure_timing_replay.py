"""Frozen-head timing compatibility experiment; no production entry point."""

import argparse
import copy
import time

import numpy as np

from .aishell3_boundaries import sample_index
from .aishell3_embeddings import PAD
from .common import PACKAGE, ROOT, file_hash, read_json, write_json
from .dev_inference import LearnedRecognizer, abstention, validate_runtime_contract
from .three_take_stability import acoustic_summary, selected_points

OUT = PACKAGE / "data/generated/azure-timing-replay-v1"
REFERENCE = PACKAGE / "data/generated/three-take-stability-v1"
CLASSES = ("T1", "T2", "T3", "T4")


def verify_freeze():
    manifest = read_json(OUT / "freeze-manifest.json")
    for name, expected in manifest["files"].items():
        if file_hash(ROOT / name) != expected:
            raise ValueError("preexisting_file_changed:" + name)
    return {"verified_files": len(manifest["files"]), "manifest_sha256": file_hash(
        OUT / "freeze-manifest.json"
    )}


def audio_contract(audio, sha256, whole, pool, duration):
    """Only audio identity and numeric spans cross the frozen inference boundary."""
    return {
        "audio_reference": str(audio),
        "audio_sha256": sha256,
        "read_unit": list(whole),
        "pooling": list(pool),
        "context": [max(0, whole[0] - 0.25), min(duration, whole[1] + 0.25)],
    }


def voiced_envelope(graph, whole):
    """Optional generic support envelope; no pitch values, lexical inputs or gap filling.

    Outer edges of retained 10ms F0 cells, clamped inside the provider owner.
    Interior dropouts remain in the pool. No largest-island or shape selection.
    """
    points = selected_points(graph, whole)
    if not points:
        return None
    return [
        max(whole[0], points[0]["timestamp_seconds"] - 0.005),
        min(whole[1], points[-1]["timestamp_seconds"] + 0.005),
    ]


def geometric_frames(contract):
    # Exact frozen HuBERT configuration: 400-sample receptive field, 320 stride.
    count = (
        sample_index(contract["context"][1], 16000)
        - sample_index(contract["context"][0], 16000) + 2 * PAD
    )
    centers = 199.5 + np.arange(max(0, (count - 400) // 320 + 1)) * 320
    a, b = [
        sample_index(t, 16000) - sample_index(contract["context"][0], 16000) + PAD
        for t in contract["pooling"]
    ]
    return int(((centers >= a) & (centers < b)).sum())


def infer_region(recognizer, contract, graph, *, outside_numbered_scope=False):
    started = time.perf_counter()
    reason = None
    try:
        validate_runtime_contract(contract)
    except ValueError as error:
        reason = str(error)
    if not reason and outside_numbered_scope:
        reason = "neutral_outside_four_tone_model"
    if not reason and not selected_points(graph, contract["pooling"]):
        reason = "no_voiced_support_in_tone_bearing_span"
    result = (
        {"expanded": abstention(reason), "pilot": abstention(reason)}
        if reason else recognizer.infer(contract)
    )
    for model in ("expanded", "pilot"):
        p = result[model]["probabilities"]
        result[model]["margin"] = (
            sorted(p.values())[-1] - sorted(p.values())[-2] if p else None
        )
    return {
        "contract": contract,
        "geometric_frames": geometric_frames(contract),
        "duration_ms": 1000 * (contract["pooling"][1] - contract["pooling"][0]),
        "acoustics": acoustic_summary(graph, contract["pooling"]),
        "model_outputs": result,
        "wall_seconds": time.perf_counter() - started,
    }


def compare(reference, candidate, reference_frames):
    result = {}
    actual_frames = candidate["model_outputs"]["expanded"].get("embedding", {}).get(
        "owned_frames"
    )
    result["pooled_frames_delta"] = (
        actual_frames - reference_frames
        if actual_frames is not None and reference_frames is not None else None
    )
    for model in ("expanded", "pilot"):
        a, b = reference[model], candidate["model_outputs"][model]
        if not a["probabilities"] or not b["probabilities"]:
            result[model] = {"comparable": False}
            continue
        p, q = [np.array([x["probabilities"][c] for c in CLASSES]) for x in (a, b)]
        result[model] = {
            "comparable": True, "same_argmax": a["prediction"] == b["prediction"],
            "total_variation": float(abs(q - p).sum() / 2),
            "max_probability_delta": float(abs(q - p).max()),
            "class_probability_deltas": dict(zip(CLASSES, (q - p).tolist(), strict=True)),
            "margin_delta": float(
                (np.sort(q)[-1] - np.sort(q)[-2]) - (np.sort(p)[-1] - np.sort(p)[-2])
            ),
            "confidence_delta": b["confidence"] - a["confidence"],
        }
    return result


def summarize(rows):
    summary = {}
    for mode in rows[0]["representations"]:
        values = [r["representations"][mode] for r in rows]
        comparable = [v["comparison"]["expanded"] for v in values
                      if v["comparison"]["expanded"]["comparable"]]
        pilot = [v["comparison"]["pilot"] for v in values
                 if v["comparison"]["pilot"]["comparable"]]
        summary[mode] = {
            "expanded_same_argmax": sum(v["same_argmax"] for v in comparable),
            "expanded_comparable": len(comparable),
            "pilot_same_argmax": sum(v["same_argmax"] for v in pilot),
            "pilot_comparable": len(pilot),
            "abstentions_all_15": sum(
                v["model_outputs"]["expanded"]["status"] != "ok" for v in values
            ),
            "numbered_abstentions_of_12": sum(
                r["representations"][mode]["model_outputs"]["expanded"]["status"] != "ok"
                for r in rows if not r["outside_numbered_scope"]
            ),
            "lost_previously_usable": sum(
                r["reference"]["expanded"]["status"] == "ok"
                and r["representations"][mode]["model_outputs"]["expanded"]["status"] != "ok"
                for r in rows
            ),
            # Descriptive distribution, not a fitted meaningful-shift/pass threshold.
            "tv_distances": [v["total_variation"] for v in comparable],
            "margin_deltas": [v["margin_delta"] for v in comparable],
        }
    return summary


def run(*, refinement=False):
    verification = verify_freeze()
    manifest = read_json(OUT / "freeze-manifest.json")
    mode = "voiced_envelope" if refinement else "raw"
    destination = OUT / (mode + "-results.json")
    if destination.exists():
        raise ValueError("result_already_sealed")
    recognizer = LearnedRecognizer(OUT / ("cache-" + mode), enabled=True)
    # Warm all takes identically; cold setup is separately measured, never hidden.
    from .aishell3_embeddings import Encoder
    from .dev_inference import LOCK
    from .learner_transfer import load_models

    start = time.perf_counter()
    recognizer.encoder = Encoder(
        "chinese_hubert_base", recognizer.folder / "embeddings",
        recognizer.folder / "canonical",
    )
    assert recognizer.encoder.base.weights == read_json(LOCK)["encoder_weights"]
    recognizer.encoder.base._load()
    recognizer.encoder_load_seconds = time.perf_counter() - start
    start = time.perf_counter()
    recognizer.models = load_models(recognizer.config)
    recognizer.classifier_load_seconds = time.perf_counter() - start
    rows, latency = [], {}
    for take_number, tid in enumerate(manifest["take_order"], 1):
        started = time.perf_counter()
        capture = read_json(OUT / tid / "capture.json")
        graph = read_json(OUT / tid / "acoustics.json")["graph"]
        report = read_json(REFERENCE / "frozen" / tid / "report.json")
        audio = REFERENCE / "frozen" / tid / "canonical.wav"
        by_index = {u["syllable_index"]: u for u in capture["units"]}
        derivation_seconds = inference_seconds = 0
        for reference in report["units"]:
            index = reference["index"]
            u = by_index.get(index)
            if u is None:
                raise ValueError("missing_timing_no_invented_region")
            start = time.perf_counter()
            whole = [u["start_seconds"], u["end_seconds"]]
            pool = whole if not refinement else voiced_envelope(graph, whole)
            # No-support case keeps original bounds only to record its explicit abstention.
            pool = pool or whole
            contract = audio_contract(
                audio, report["audio_sha256"], whole, pool, capture["duration_seconds"]
            )
            derivation_seconds += time.perf_counter() - start
            # Scope gate is outside inference; no expected numbered tone is read or passed.
            outside_scope = reference["target"]["expected_surface_tone"] == 0
            result = infer_region(
                recognizer, contract, graph, outside_numbered_scope=outside_scope
            )
            inference_seconds += result["wall_seconds"]
            frames = reference["expanded"].get("embedding", {}).get("owned_frames")
            result["comparison"] = compare(reference, result, frames)
            spans = reference["spans"]
            mfa_whole, mfa_pool, mfa_context = [
                [spans[k][t] for t in ("start_seconds", "end_seconds")]
                for k in ("playback_read_unit", "tone_bearing_pooling_span", "context")
            ]
            reps = {mode: result}
            if not refinement:
                conservative = capture["conservative_regions"][str(index)]
                assert [conservative["start"], conservative["end"]] == whole
                # Exact same input: alias outputs explicitly, not a fake second measurement.
                reps["existing_conservative"] = copy.deepcopy(result)
                reps["existing_conservative"]["reused_identical_raw_input"] = True
                reps["existing_conservative"]["wall_seconds"] = 0
            row = {
                "take": take_number, "take_id": tid, "index": index,
                "character": u["label"], "outside_numbered_scope": outside_scope,
                "reference": {k: reference[k] for k in ("expanded", "pilot")},
                "mfa_whole": mfa_whole, "mfa_pool": mfa_pool, "mfa_context": mfa_context,
                "mfa_frames": frames, "azure_whole": whole,
                "boundary_delta_vs_mfa_whole_ms": [
                    1000 * (a - b) for a, b in zip(whole, mfa_whole, strict=True)
                ],
                "pool_delta_vs_mfa_pool_ms": [
                    1000 * (a - b) for a, b in zip(pool, mfa_pool, strict=True)
                ],
                "duration_delta_vs_mfa_pool_ms": 1000 * (
                    pool[1] - pool[0] - mfa_pool[1] + mfa_pool[0]
                ),
                "representations": reps,
            }
            rows.append(row)
            print(take_number, u["label"], mode,
                  reference["expanded"]["prediction"], "->",
                  result["model_outputs"]["expanded"]["prediction"],
                  result["model_outputs"]["expanded"]["confidence"],
                  "F0", result["acoustics"]["usable_frames"], flush=True)
        latency[tid] = {
            **capture["latency"],
            "numeric_region_derivation_seconds": derivation_seconds,
            "warm_frozen_inference_and_gating_seconds": inference_seconds,
            "local_analysis_wall_seconds": time.perf_counter() - started,
        }
    # One baseline reproduction per previously usable unit, no perturbation rerun.
    reproduction = []
    if not refinement:
        for row in rows:
            reference = row["reference"]
            if reference["expanded"]["status"] != "ok":
                continue
            contract = copy.deepcopy(reference["expanded"]["span_metadata"])
            contract["audio_reference"] = str(
                REFERENCE / "frozen" / row["take_id"] / "canonical.wav"
            )
            actual = recognizer.infer(contract)
            deltas = {
                model: max(abs(actual[model]["probabilities"][c]
                               - reference[model]["probabilities"][c]) for c in CLASSES)
                for model in ("expanded", "pilot")
            }
            if max(deltas.values()) > 1e-6:
                raise ValueError("frozen_inference_not_reproduced")
            reproduction.append({"take": row["take"], "index": row["index"], **deltas})
    result = {
        "mode": mode, "initial_freeze": verification,
        "performance": recognizer.performance(),
        "rows": rows, "summary": summarize(rows), "latency": latency,
        "baseline_reproduction": reproduction,
        "method": {
            "context": "Azure whole span +/-250ms, audio-clamped; frozen 200-sample edge pad",
            "layer": 9, "classes": CLASSES, "no_refitting": True,
            "context_changes_vs_mfa": True,
            "support_gate": "existing >=60ms and any retained F0; neutral outside model",
            "refinement": "outer retained 10ms F0-cell envelope inside Azure owner"
            if refinement else "none",
        },
    }
    write_json(destination, result)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--refinement", action="store_true")
    args = parser.parse_args()
    run(refinement=args.refinement)
