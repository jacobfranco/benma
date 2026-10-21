"""Offline, sealed timing diagnosis. No provider, MFA, or production execution."""

import copy
import time

import numpy as np

from .azure_timing_replay import (
    CLASSES, OUT as SAVED, REFERENCE, audio_contract, compare, infer_region,
    summarize, voiced_envelope,
)
from .common import ROOT, file_hash, read_json, write_json
from .dev_inference import LearnedRecognizer, abstention
from .three_take_stability import selected_points

OUT = SAVED.parent / "fast-timing-ownership-v1"


def verify_freeze():
    files = read_json(OUT / "freeze-manifest.json")["files"]
    for name, expected in files.items():
        if file_hash(ROOT / name) != expected:
            raise ValueError("preexisting_file_changed:" + name)
    return {"verified_files": len(files)}


def discontinuities(graph, raw, pool):
    """Evidence-only guard: a retained-F0 gap contains below-noise-gate energy.

    Reuse the saved analyzer's RMS threshold and 10 ms frame lattice. No new
    amplitude/duration cutoff; a pitch dropout alone is not a silent interruption.
    This marks uncertain ownership, never an error or a syllable boundary.
    """
    points = selected_points(graph, pool)
    threshold = raw["energy_gate"]["threshold_rms"]
    found = []
    for left, right in zip(points, points[1:]):
        start, end = left["timestamp_seconds"], right["timestamp_seconds"]
        if end - start <= 0.015:  # existing retained-island adjacency convention
            continue
        low = [
            p["timestamp_seconds"] for p in raw["f0"]
            if start < p["timestamp_seconds"] < end and p["energy_rms"] < threshold
        ]
        if low:
            found.append({
                "between_retained_centers": [start, end],
                "below_existing_energy_gate_centers": low,
                "threshold_rms": threshold,
            })
    return found


def ownership_alternatives(graph, raw, left, right):
    """Small fixed set, numeric timing/energy only; never selects by model output."""
    center_left, center_right = np.mean(left), np.mean(right)
    provider_boundary = (left[1] + right[0]) / 2
    window = [
        p for p in raw["f0"]
        if center_left <= p["timestamp_seconds"] <= center_right
    ]
    minima = [
        p for before, p, after in zip(window, window[1:], window[2:])
        if p["energy_rms"] < before["energy_rms"]
        and p["energy_rms"] <= after["energy_rms"]
    ]
    nearest = min(
        minima,
        key=lambda p: (abs(p["timestamp_seconds"] - provider_boundary),
                       p["timestamp_seconds"]),
    ) if minima else None
    midpoint = float((center_left + center_right) / 2)
    variants = {
        "provider_envelope": [list(left), list(right)],
        "center_midpoint": [[left[0], midpoint], [midpoint, right[1]]],
    }
    if nearest:
        boundary = nearest["timestamp_seconds"]
        variants["nearest_energy_minimum"] = [
            [left[0], boundary], [boundary, right[1]],
        ]
    # Diagnostic adaptation of the existing evidence selector's 0.6 RMS ratio.
    # It is not a final boundary rule: a low-energy sonorant can remain voiced.
    retained = {p["timestamp_seconds"] for p in selected_points(graph, [left[0], right[1]])}
    energy = [p["energy_rms"] for p in raw["f0"] if p["timestamp_seconds"] in retained]
    cutoff = float(np.median(energy) * 0.6) if energy else 0
    if window:
        anchor = min(range(len(window)), key=lambda i: abs(
            window[i]["timestamp_seconds"] - provider_boundary
        ))
        if window[anchor]["energy_rms"] <= cutoff:
            lo = hi = anchor
            while lo and window[lo - 1]["energy_rms"] <= cutoff:
                lo -= 1
            while hi + 1 < len(window) and window[hi + 1]["energy_rms"] <= cutoff:
                hi += 1
            variants["withhold_energy_trough"] = [
                [left[0], window[lo]["timestamp_seconds"] - 0.005],
                [window[hi]["timestamp_seconds"] + 0.005, right[1]],
            ]
    return {"whole_spans": variants, "diagnostic_low_energy_cutoff": cutoff}


def seal_plan():
    """Run before any new model calls; preserve exact policy and numeric alternatives."""
    rows = read_json(SAVED / "voiced_envelope-results.json")["rows"]
    alternatives, interruptions, takes = {}, [], {}
    for row in rows:
        take, tid = row["take"], row["take_id"]
        if take not in takes:
            takes[take] = read_json(SAVED / tid / "acoustics.json")
        data = takes[take]
        pool = voiced_envelope(data["graph"], row["azure_whole"])
        issues = discontinuities(data["graph"], data["raw"], pool) if pool else []
        if issues:
            interruptions.append({"take": take, "index": row["index"], "evidence": issues})
    for take, indices in [(2, (1, 2)), (3, (3, 4))]:
        pair = [next(r for r in rows if r["take"] == take and r["index"] == i) for i in indices]
        data = takes[take]
        alternatives[str(take)] = ownership_alternatives(
            data["graph"], data["raw"], *[r["azure_whole"] for r in pair]
        )
    write_json(OUT / "policy-before-inference.json", {
        "policy": "Existing Azure-clamped retained-F0 envelope; abstain on a retained-F0 "
        "gap with intervening RMS below the already-saved analyzer energy gate. "
        "Do not assign either voiced portion or fill the gap. Keep existing duration, "
        "no-support and external neutral gates. No boundary snap adopted.",
        "reason": "Continuous sonorant transition near take-2 provider edge has no unique "
        "acoustic split; a later deep energy interruption makes single-unit ownership "
        "uncertain. Take-3 final has no supported internal split; energy-only neutral "
        "tail cannot supply a retained contour. Abstention is evidence uncertainty, "
        "not a learner error. No probabilities select spans.",
        "limitations": "Conservative guard can abstain on legitimate glottalization or "
        "a pause within one syllable. Three takes cannot establish general accuracy.",
        "alternatives": alternatives, "interruptions": interruptions,
        "source_sha256": file_hash(__file__),
        "saved_refinement_sha256": file_hash(SAVED / "voiced_envelope-results.json"),
        "freeze": verify_freeze(),
    })


def run():
    plan = read_json(OUT / "policy-before-inference.json")
    assert plan["source_sha256"] == file_hash(__file__)
    verify_freeze()
    recognizer = LearnedRecognizer(OUT / "cache", enabled=True)
    # Resident encoder and heads, initialized once for the whole replay.
    from .aishell3_embeddings import Encoder
    from .dev_inference import LOCK
    from .learner_transfer import load_models

    start = time.perf_counter()
    recognizer.encoder = Encoder(
        "chinese_hubert_base", recognizer.folder / "embeddings", recognizer.folder / "canonical"
    )
    assert recognizer.encoder.base.weights == read_json(LOCK)["encoder_weights"]
    recognizer.encoder.base._load()
    recognizer.encoder_load_seconds = time.perf_counter() - start
    start = time.perf_counter()
    recognizer.models = load_models(recognizer.config)
    recognizer.classifier_load_seconds = time.perf_counter() - start
    resident_ids = (id(recognizer.encoder), id(recognizer.models))
    source = read_json(SAVED / "voiced_envelope-results.json")["rows"]
    rows, timings, reproduction = [], {}, []
    for original in source:
        row = copy.deepcopy(original)
        tid = row["take_id"]
        data = read_json(SAVED / tid / "acoustics.json")
        capture = read_json(SAVED / tid / "capture.json")
        start = time.perf_counter()
        pool = voiced_envelope(data["graph"], row["azure_whole"]) or row["azure_whole"]
        issues = discontinuities(data["graph"], data["raw"], pool)
        old = row["representations"]["voiced_envelope"]
        contract = audio_contract(
            old["contract"]["audio_reference"], old["contract"]["audio_sha256"],
            row["azure_whole"], pool, capture["duration_seconds"],
        )
        assert contract == old["contract"]
        derivation = time.perf_counter() - start
        if issues:
            # Build diagnostics/gating metadata without executing the classifier.
            result = infer_region(recognizer, contract, data["graph"], outside_numbered_scope=True)
            result["model_outputs"] = {
                m: {**abstention("ambiguous_interrupted_voiced_envelope"), "margin": None}
                for m in ("expanded", "pilot")
            }
        else:
            result = infer_region(
                recognizer, contract, data["graph"],
                outside_numbered_scope=row["outside_numbered_scope"],
            )
        result["interruptions"] = issues
        result["comparison"] = compare(row["reference"], result, row["mfa_frames"])
        row["representations"] = {"final": result}
        rows.append(row)
        timings.setdefault(tid, {"refinement_and_guard_seconds": 0, "inference_seconds": 0})
        timings[tid]["refinement_and_guard_seconds"] += derivation
        timings[tid]["inference_seconds"] += result["wall_seconds"]
        for model in ("expanded", "pilot"):
            actual, previous = result["model_outputs"][model], old["model_outputs"][model]
            if actual["probabilities"]:
                delta = max(abs(actual["probabilities"][c] - previous["probabilities"][c])
                            for c in CLASSES)
                assert delta <= 1e-6
                reproduction.append({"take": row["take"], "index": row["index"],
                                     "model": model, "max_probability_delta": delta})
        print("final", row["take"], row["character"],
              result["model_outputs"]["expanded"]["prediction"],
              result["model_outputs"]["expanded"]["reason"], flush=True)
    final_performance = recognizer.performance()
    write_json(OUT / "final-results.json", {
        "rows": rows, "summary": summarize(rows), "timings": timings,
        "performance": final_performance, "saved_refinement_reproduction": reproduction,
        "policy_sha256": file_hash(OUT / "policy-before-inference.json"),
    })
    # Alternatives are diagnostics only and are executed after final output is sealed.
    alternatives = []
    for take, indices in [(2, (1, 2)), (3, (3, 4))]:
        pair = [next(r for r in source if r["take"] == take and r["index"] == i) for i in indices]
        tid = pair[0]["take_id"]
        data = read_json(SAVED / tid / "acoustics.json")
        duration = read_json(SAVED / tid / "capture.json")["duration_seconds"]
        for name, spans in plan["alternatives"][str(take)]["whole_spans"].items():
            for row, whole in zip(pair, spans, strict=True):
                old = row["representations"]["voiced_envelope"]
                pool = voiced_envelope(data["graph"], whole) or whole
                # Fixed original context isolates ownership/pooling from context changes.
                contract = {**old["contract"], "read_unit": whole, "pooling": pool}
                result = infer_region(
                    recognizer, contract, data["graph"],
                    outside_numbered_scope=row["outside_numbered_scope"],
                )
                alternatives.append({
                    "take": take, "index": row["index"], "character": row["character"],
                    "alternative": name, "result": result,
                    "comparison_to_provider_envelope": compare(
                        old["model_outputs"], result, old["geometric_frames"]
                    ),
                })
        # Both separate islands, never select the preferred prediction.
        if take == 2:
            row = pair[1]
            old = row["representations"]["voiced_envelope"]
            points = selected_points(data["graph"], old["contract"]["pooling"])
            islands = []
            for point in points:
                if not islands or point["timestamp_seconds"] - islands[-1][-1] > 0.015:
                    islands.append([])
                islands[-1].append(point["timestamp_seconds"])
            for i, island in enumerate(islands):
                whole = row["azure_whole"]
                pool = [max(whole[0], island[0] - 0.005), min(whole[1], island[-1] + 0.005)]
                result = infer_region(
                    recognizer, {**old["contract"], "pooling": pool}, data["graph"]
                )
                alternatives.append({
                    "take": take, "index": row["index"], "character": row["character"],
                    "alternative": f"separate_island_{i + 1}_diagnostic_only",
                    "result": result,
                    "comparison_to_provider_envelope": compare(
                        old["model_outputs"], result, old["geometric_frames"]
                    ),
                })
    write_json(OUT / "alternatives.json", alternatives)
    reference_reproduction = []
    for row in source:
        if row["reference"]["expanded"]["status"] != "ok":
            continue
        contract = copy.deepcopy(row["reference"]["expanded"]["span_metadata"])
        contract["audio_reference"] = str(REFERENCE / "frozen" / row["take_id"] / "canonical.wav")
        actual = recognizer.infer(contract)
        deltas = {
            model: max(abs(actual[model]["probabilities"][c]
                           - row["reference"][model]["probabilities"][c]) for c in CLASSES)
            for model in ("expanded", "pilot")
        }
        assert max(deltas.values()) <= 1e-6
        reference_reproduction.append({"take": row["take"], "index": row["index"], **deltas})
    assert resident_ids == (id(recognizer.encoder), id(recognizer.models))
    write_json(OUT / "verification.json", {
        "freeze": verify_freeze(), "reference_reproduction": reference_reproduction,
        "resident_encoder_and_heads_reused": True, "performance_after_diagnostics": recognizer.performance(),
        "no_provider_or_mfa_calls": True,
    })


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("stage", choices=["seal", "run"])
    args = parser.parse_args()
    seal_plan() if args.stage == "seal" else run()
