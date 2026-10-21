"""Inspectable tables for the isolated Azure replay, built from sealed JSON outputs."""
# ruff: noqa: RUF001

import csv
import json
import time

from .azure_timing_replay import CLASSES, OUT, REFERENCE
from .common import read_json, write_json
from .three_take_stability import selected_points


def table(headers, rows):
    return "\n".join([
        "| " + " | ".join(headers) + " |",
        "|" + "|".join("---" for _ in headers) + "|",
        *["| " + " | ".join(str(x) for x in row) + " |" for row in rows],
    ])


def interval(span):
    return f"{span[0]:.4f}–{span[1]:.4f}"


def vector(output):
    if not output.get("probabilities"):
        return "—"
    return " / ".join(f"{output['probabilities'][c]:.6f}" for c in CLASSES)


def margin(output):
    p = output.get("probabilities")
    return sorted(p.values())[-1] - sorted(p.values())[-2] if p else None


def optional(value, digits=6):
    return "—" if value is None else f"{value:.{digits}f}"


def build():
    started = time.perf_counter()
    raw = read_json(OUT / "raw-results.json")
    refined = read_json(OUT / "voiced_envelope-results.json")
    prior = read_json(REFERENCE / "diagnostics.json")
    prior_by_key = {(r["take"], r["index"]): r for r in prior["rows"]}
    timings, boundaries, probabilities, deltas, ownership, csv_rows = [], [], [], [], [], []
    provider = []
    excursions = {"raw": [], "voiced_envelope": []}
    for a, b in zip(raw["rows"], refined["rows"], strict=True):
        key = (a["take"], a["index"])
        assert key == (b["take"], b["index"])
        take, character = a["take"], a["character"]
        ar, br = a["representations"]["raw"], b["representations"]["voiced_envelope"]
        boundaries.append([
            take, character, interval(a["mfa_whole"]), interval(a["mfa_pool"]),
            interval(a["azure_whole"]), interval(br["contract"]["pooling"]),
            " / ".join(f"{v:+.1f}" for v in a["boundary_delta_vs_mfa_whole_ms"]),
            " / ".join(f"{v:+.1f}" for v in a["pool_delta_vs_mfa_pool_ms"]),
            " / ".join(f"{v:+.1f}" for v in b["pool_delta_vs_mfa_pool_ms"]),
            f"{a['duration_delta_vs_mfa_pool_ms']:+.1f}",
            f"{b['duration_delta_vs_mfa_pool_ms']:+.1f}",
            f"{a['mfa_frames']} / {ar['geometric_frames']} / {br['geometric_frames']}",
        ])
        for mode, result in [("MFA", None), ("raw", ar), ("voiced_envelope", br)]:
            outputs = a["reference"] if result is None else result["model_outputs"]
            frames = a["mfa_frames"] if result is None else result["geometric_frames"]
            pooling = a["mfa_pool"] if result is None else result["contract"]["pooling"]
            inference = None if result is None else result["wall_seconds"]
            probabilities.append([
                take, character, mode,
                outputs["expanded"]["prediction"] or "abstain", vector(outputs["expanded"]),
                optional(outputs["expanded"]["confidence"]), optional(margin(outputs["expanded"])),
                outputs["pilot"]["prediction"] or "abstain", vector(outputs["pilot"]),
                optional(outputs["pilot"]["confidence"]), optional(margin(outputs["pilot"])),
                frames, f"{(pooling[1] - pooling[0]) * 1000:.1f}", optional(inference),
                outputs["expanded"].get("reason") or "—",
            ])
            for model in ("expanded", "pilot"):
                output = outputs[model]
                csv_rows.append({
                    "take": take, "take_id": a["take_id"], "character": character,
                    "representation": mode, "model": model,
                    "pool_start": pooling[0], "pool_end": pooling[1],
                    "span_duration_ms": (pooling[1] - pooling[0]) * 1000,
                    "geometric_frames": frames,
                    "actual_pooled_frames": output.get("embedding", {}).get("owned_frames"),
                    "prediction": output["prediction"], "confidence": output["confidence"],
                    "margin": margin(output), "status": output["status"],
                    "reason": output.get("reason"),
                    **{c: (output["probabilities"] or {}).get(c) for c in CLASSES},
                    "both_heads_inference_seconds": inference,
                })
            if result:
                for model in ("expanded", "pilot"):
                    comparison = result["comparison"][model]
                    deltas.append([
                        take, character, mode, model,
                        comparison.get("same_argmax", "not comparable"),
                        optional(comparison.get("total_variation")),
                        optional(comparison.get("max_probability_delta")),
                        optional(comparison.get("margin_delta")),
                        optional(comparison.get("confidence_delta")),
                        result["comparison"]["pooled_frames_delta"],
                    ])
                variants = [v["expanded"]["probabilities"]
                            for v in prior_by_key[key]["variants"] if "expanded" in v]
                if variants and outputs["expanded"]["probabilities"]:
                    outside = [
                        c for c in CLASSES
                        if not min(v[c] for v in variants) - 1e-6
                        <= outputs["expanded"]["probabilities"][c]
                        <= max(v[c] for v in variants) + 1e-6
                    ]
                    if outside:
                        excursions[mode].append({
                            "take": take, "index": a["index"], "character": character,
                            "classes_outside_prior_perturbation_range": outside,
                        })
        graph = read_json(OUT / a["take_id"] / "acoustics.json")["graph"]
        same_take = [r for r in raw["rows"] if r["take"] == take]
        groups = {}
        for p in selected_points(graph, a["azure_whole"]):
            owners = [r["character"] for r in same_take
                      if r["mfa_whole"][0] <= p["timestamp_seconds"] < r["mfa_whole"][1]]
            owner = "+".join(owners) or "unowned"
            groups.setdefault(owner, []).append(p["timestamp_seconds"])
        ownership.append({
            "take": take, "character": character,
            "azure_region_retained_f0_by_mfa_owner": groups,
            "qualification": "Competing timing hypotheses, not independently verified ownership",
        })

    for take, tid in enumerate(read_json(OUT / "freeze-manifest.json")["take_order"], 1):
        response = read_json(OUT / tid / "azure-raw.json")
        best = response["NBest"][0]
        provider.append({
            "take": take, "take_id": tid, "status": response["RecognitionStatus"],
            "display": response["DisplayText"], "lexical": best["Lexical"],
            "utterance_confidence": best.get("Confidence"),
            "words": [{
                "text": w["Word"], "start": w["Offset"] / 1e7,
                "end": (w["Offset"] + w["Duration"]) / 1e7,
                "confidence": w.get("Confidence"),
            } for w in best["Words"]],
        })
        previous_end = None
        for word in best["Words"]:
            for g in word.get("Syllables", []):
                start, end = g["Offset"] / 1e7, (g["Offset"] + g["Duration"]) / 1e7
                timings.append([
                    take, word["Word"], g["Grapheme"], g["Offset"], g["Duration"],
                    f"{start:.3f}", f"{end:.3f}", f"{(end-start)*1000:.0f}",
                    "unavailable" if g.get("Confidence") is None else g["Confidence"],
                    word.get("Confidence"), optional(
                        None if previous_end is None else (start-previous_end)*1000, 1
                    ),
                ])
                previous_end = end

    text = [
        "# Azure replay: full evidence tables",
        "MFA is the **frozen diagnostic reference**, not ground truth. Times are seconds; "
        "deltas are candidate minus MFA. Probabilities are raw preferences, not correctness. "
        "The sealed JSON files preserve full floating-point precision.",
        "## Raw provider character timing",
        "All 15 graphemes are present, ordered and non-overlapping. No merged character timing. "
        "`这个` is one word with two explicit character spans. Missing confidence is not repaired; "
        "word Confidence=0 is preserved and is not treated as boundary confidence. "
        "AccuracyScore is assessment, not timing confidence, and is not used.",
        table(["Take", "Word", "Grapheme", "Offset ticks", "Duration ticks", "Start", "End",
               "ms", "Grapheme confidence", "Word confidence", "Gap before ms"], timings),
        "## Boundary and frame comparison",
        "Frame triplets are MFA actual / Azure whole geometric / refined geometric. "
        "Geometric frames on abstained rows were not pooled by inference. "
        "Context remains Azure whole ±250ms for both Azure representations.",
        table(["Take", "Char", "MFA whole", "MFA pool", "Azure whole", "Refined pool",
               "Azure−MFA whole edges ms", "Raw−MFA pool edges ms",
               "Refined−MFA pool edges ms", "Raw duration Δ ms", "Refined duration Δ ms",
               "Frames M/A/R"], boundaries),
        "## Full frozen expanded and pilot outputs",
        "Vectors are T1 / T2 / T3 / T4. Existing conservative B is exactly raw A on all "
        "15 inputs, so its identical vectors are recorded in raw-results.json, not duplicated "
        "here. Refined B is the generic F0-cell envelope. Inference time includes both heads "
        "and gating, with an already loaded encoder and no embedding-cache hits. "
        "MFA timing is available in the frozen original reports.",
        table(["Take", "Char", "Representation", "Expanded", "Expanded probabilities",
               "Raw confidence", "Margin", "Pilot", "Pilot probabilities", "Pilot confidence",
               "Pilot margin", "Frames", "Duration ms", "Inference seconds", "Reason"],
              probabilities),
        "## Probability, margin and actual pooled-frame differences",
        "TV = half the L1 probability distance. Non-comparable cases retain explicit "
        "abstentions; no synthetic probability vector is substituted.",
        table(["Take", "Char", "Representation", "Model", "Same argmax", "TV", "Max |Δp|",
               "Δ margin", "Δ confidence", "Actual frames Δ"], deltas),
    ]
    (OUT / "comparison.md").write_text("\n\n".join(text) + "\n")
    with (OUT / "full-outputs.csv").open("w") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(csv_rows[0]))
        writer.writeheader()
        writer.writerows(csv_rows)
    write_json(OUT / "provider-summary.json", provider)
    write_json(OUT / "competing-ownership.json", ownership)
    write_json(OUT / "probability-range-excursions.json", {
        "definition": "Any class outside its previously saved +/-40ms admissible pooling "
        "range, tolerance 1e-6 for reproduction. Descriptive only, no new pass threshold. "
        "Context also changes, so this is not proof of a timing error.",
        "results": excursions,
    })
    report_seconds = time.perf_counter() - started
    latency = {}
    for tid, values in refined["latency"].items():
        core = sum(values[k] for k in (
            "azure_request_seconds_including_transport_json_decode",
            "timestamp_parsing_seconds", "f0_seconds", "numeric_region_derivation_seconds",
            "warm_frozen_inference_and_gating_seconds",
        ))
        latency[tid] = {
            **values,
            "warm_sequential_core_seconds": core,
            "measured_stage_wall_sum_with_evidence_io_seconds": (
                values["capture_total_seconds"] + values["local_analysis_wall_seconds"]
            ),
            "conservative_warm_estimate_including_entire_batch_report_seconds": (
                values["capture_total_seconds"] + values["local_analysis_wall_seconds"]
                + report_seconds
            ),
        }
    write_json(OUT / "latency-summary.json", {
        "full_three_take_evidence_report_seconds": report_seconds,
        "takes": latency, "cold_setup": refined["performance"],
        "qualification": "Stage sums from separate capture and inference processes, not a "
        "single end-to-end server request. Same fresh Azure calls reused for each representation. "
        "Full report cost charged to each take conservatively. Excludes interpreter/library "
        "imports, initial experiment freeze hashing, browser stop/finalization, client upload "
        "to Benma and paint. Provider upload/network/response decode is included. "
        "No full deterministic family classification invoked; measured F0 supports "
        "the existing gate.",
    })
    print(json.dumps({"report_seconds": report_seconds, "latency": latency,
                      "excursion_counts": {k: len(v) for k, v in excursions.items()}}, indent=2))


if __name__ == "__main__":
    build()
