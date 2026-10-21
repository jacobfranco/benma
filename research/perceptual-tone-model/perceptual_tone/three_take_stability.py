"""Inference-only diagnostics. No production imports, fitting, or span replacement."""

import hashlib
import json
import re
import time
import wave
from collections import Counter
from datetime import datetime
from pathlib import Path

import numpy as np

from .aishell3_boundaries import sample_index
from .aishell3_embeddings import PAD, Encoder, input_audio
from .common import PACKAGE, ROOT, file_hash, read_json
from .dev_inference import verify_frozen
from .embeddings import frame_centers
from .learner_release import RELEASE
from .learner_transfer import CLASSES, load_models, probabilities

RUN = PACKAGE / "data/generated/three-take-stability-v1"


def write_generated(path, value):
    """Only replace derived diagnostic outputs, never a freeze/original artifact."""
    path = Path(path)
    if path.parent.resolve() != RUN.resolve() or path.name not in {
        "diagnostics.json",
        "annotated-diagnostics.json",
        "component-hashes.json",
        "report-verification.json",
    }:
        raise ValueError("not_a_generated_diagnostic_output")
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n")


def verify_snapshot(folder=RUN):
    manifest = read_json(folder / "freeze-manifest.json")
    for name, record in manifest["files"].items():
        for path in (ROOT / name, ROOT / record["snapshot"]):
            if file_hash(path) != record["sha256"]:
                raise ValueError("take_mutated:" + str(path))
    for name, expected in manifest["starting_source_files"].items():
        if file_hash(ROOT / name) != expected:
            raise ValueError("preexisting_source_mutated:" + name)
    return {
        "original_files_verified": len(manifest["files"]),
        "snapshot_files_verified": len(manifest["files"]),
        "starting_source_files_verified": len(manifest["starting_source_files"]),
    }


def compact_grid(pool, region, rate=16000):
    """33 requests: axes plus translation/expansion diagonals; deduplicate after clamp."""
    offsets = range(-40, 41, 10)
    requests = {(d, 0) for d in offsets} | {(0, d) for d in offsets}
    requests |= {(d, d) for d in offsets} | {(d, -d) for d in offsets}
    lo, hi = [sample_index(x, rate) for x in region]
    p, q = [sample_index(x, rate) for x in pool]
    variants = {}
    for ds, de in sorted(requests):
        a, b = max(lo, p + round(ds * rate / 1000)), min(hi, q + round(de * rate / 1000))
        # Both edges clamp to both region endpoints, including collapsed spans.
        a, b = min(hi, a), max(lo, b)
        key = (a, b)
        variants.setdefault(
            key,
            {
                "start": a / rate,
                "end": b / rate,
                "duration_ms": (b - a) * 1000 / rate,
                "actual_delta_ms": [(a - p) * 1000 / rate, (b - q) * 1000 / rate],
                "requested_offsets_ms": [],
            },
        )["requested_offsets_ms"].append([ds, de])
    return list(variants.values())


def selected_points(graph, interval):
    return [
        p
        for segment in graph["filtered"]["segments"]
        for p in segment
        if interval[0] <= p["timestamp_seconds"] < interval[1]
    ]


def acoustic_summary(graph, interval):
    points = selected_points(graph, interval)
    t = [p["timestamp_seconds"] for p in points]
    y = np.array([p["normalized_semitones"] for p in points])
    # Count 10ms analysis cells, clipped to the requested region; do not bridge gaps.
    support = sum(max(0, min(interval[1], x + 0.005) - max(interval[0], x - 0.005)) for x in t)
    islands = []
    for p in points:
        if not islands or p["timestamp_seconds"] - islands[-1][-1]["timestamp_seconds"] > 0.015:
            islands.append([])
        islands[-1].append(p)
    result = {
        "usable_frames": len(t),
        "voiced_support_ms": support * 1000,
        "voiced_frame_cell_ms_unclipped": len(t) * 10,
        "islands": len(islands),
        "first": t[0] if t else None,
        "last": t[-1] if t else None,
        "range_st": float(np.ptp(y)) if len(y) else None,
        "net_st": float(y[-1] - y[0]) if len(y) > 1 else None,
        "fall_st": None,
        "recovery_st": None,
        "shape_basis": "largest_contiguous_retained_island; no interpolation",
    }
    if islands:
        largest = max(islands, key=len)
        z = np.array([p["normalized_semitones"] for p in largest])
        bottom = int(z.argmin())
        result.update(
            largest_island_frames=len(z),
            fall_st=float(z[0] - z[bottom]),
            recovery_st=float(z[-1] - z[bottom]),
            largest_island_net_st=float(z[-1] - z[0]),
        )
    return result


def stability(variants, baseline, *, usable, margin_sensitive=False):
    """Human descriptive margin annotation, not a confidence cutoff."""
    valid = [v for v in variants if v.get("expanded")]
    if not usable or not valid:
        return "UNUSABLE"
    if any(v["expanded"]["prediction"] != baseline for v in valid):
        return "BOUNDARY-SENSITIVE"
    return "MARGIN-SENSITIVE" if margin_sensitive else "STABLE"


def prediction(p):
    p = np.asarray(p)
    ranked = np.sort(p)
    return {
        "prediction": CLASSES[int(p.argmax())],
        "confidence": float(p.max()),
        "margin": float(ranked[-1] - ranked[-2]),
        "probabilities": dict(zip(CLASSES, p.tolist(), strict=True)),
    }


def latency(report, log):
    p = report["performance"]
    patterns = {
        "mfa_internal_seconds": r"Everything took ([\d.]+) seconds",
        "corpus_setup_seconds": r"Setting up corpus took ([\d.]+) seconds",
        "alignment_setup_seconds": r"Setup for alignment in ([\d.]+) seconds",
        "features_seconds_nested_in_setup": r"Generated features in ([\d.]+) seconds",
        "compile_graph_seconds": r"Compiling training graphs took ([\d.]+) seconds",
        "alignment_round_seconds": r"Alignment round took ([\d.]+) seconds",
        "collect_alignment_seconds": r"Collecting alignments took ([\d.]+) seconds",
        "quality_seconds": r"Analyzed alignment quality in ([\d.]+) seconds",
        "textgrid_export_seconds": r"Exported TextGrids in a total of ([\d.]+) seconds",
    }
    result = {
        k: float(m.group(1)) if (m := re.search(v, log)) else None for k, v in patterns.items()
    }
    result["saved"] = p
    result["mfa_fraction_of_server_total"] = p["alignment_seconds"] / p["utterance_total_seconds"]
    result["outside_mfa_internal_seconds"] = (
        p["alignment_seconds"] - result["mfa_internal_seconds"]
        if result["mfa_internal_seconds"] is not None
        else None
    )
    result["learned_excluding_encoder_load_seconds"] = p["learned_seconds"] - (
        p["encoder_load_this_take_seconds"] or 0
    )
    result["unmeasured"] = [
        "browser recording finalization/upload/network/browser paint",
        "span derivation separately (included in report_generation_seconds)",
        "pure MFA startup separately (outside-internal residual also contains wrapper/exit work)",
    ]
    return result


def worker_timing(log):
    """Timestamp bounds, not a profiler: only the logged processing window."""
    lines = [line for line in log.splitlines() if " - " in line]
    selected = [line for line in lines if "Processing 1-1" in line or "Done 1, errors on 0" in line]

    def timestamp(line):
        return datetime.strptime(line.split(" - ")[0], "%Y-%m-%d %H:%M:%S,%f")

    return {
        "logged_processing_seconds": (
            (timestamp(selected[-1]) - timestamp(selected[0])).total_seconds()
            if len(selected) == 2
            else None
        ),
        "worker_log_span_seconds": (
            (timestamp(lines[-1]) - timestamp(lines[0])).total_seconds() if lines else None
        ),
        "qualification": (
            "logged timestamp window, excludes earlier/later work; not isolated kernel profiling"
        ),
    }


def run(folder=RUN):
    import torch

    initial = verify_snapshot(folder)
    frozen = verify_frozen()
    manifest = read_json(folder / "freeze-manifest.json")
    acoustic = read_json(folder / "full-acoustics.json")
    config = read_json(RELEASE / "inference-config.json")
    start = time.perf_counter()
    encoder = Encoder("chinese_hubert_base", folder / "embedding-cache", folder / "canonical-cache")
    if (
        encoder.base.weights
        != read_json(PACKAGE / "configs/dev-learned-lock.json")["encoder_weights"]
    ):
        raise ValueError("encoder_weights_changed")
    encoder.base._load()
    models = load_models(config)
    load_seconds = time.perf_counter() - start
    rows, timing = [], {}
    frames_dir = folder / "hidden-states"
    frames_dir.mkdir(exist_ok=True)
    for take_number, tid in enumerate(manifest["take_order"], 1):
        take = folder / "frozen" / tid
        report = read_json(take / "report.json")
        graph = acoustic[tid]["graph"]
        timing[tid] = latency(report, (take / "alignment/work/corpus/corpus.log").read_text())
        timing[tid]["worker"] = worker_timing(
            (take / "alignment/work/corpus/alignment/log/align.1.log").read_text()
        )
        saved_raw = read_json(take / "deterministic/raw.json")
        for unit in report["units"]:
            i = unit["index"]
            spans = unit["spans"]
            whole, pool, context = [
                [spans[k][t] for t in ("start_seconds", "end_seconds")]
                for k in ("playback_read_unit", "tone_bearing_pooling_span", "context")
            ]
            contract = {
                "audio_reference": str(take / "canonical.wav"),
                "audio_sha256": report["audio_sha256"],
                "read_unit": whole,
                "pooling": pool,
                "context": context,
            }
            audio, target, _ = input_audio(contract, "context", folder / "canonical-cache")
            inputs = encoder.base.processor(audio, sampling_rate=16000, return_tensors="pt")
            with torch.inference_mode():
                hidden = encoder.base.model(**inputs, output_hidden_states=True).hidden_states[9][0]
            centers = frame_centers(encoder.base.model.config, hidden.shape[0])
            hpath = frames_dir / f"{tid}-{i}.npy"
            np.save(hpath, hidden.cpu().numpy(), allow_pickle=False)
            hidden_hash = file_hash(hpath)
            # Every variant reuses these exact hidden states; only its mean-pooling mask changes.
            original_mask = (centers >= target[0]) & (centers < target[1])
            reproduce = {}
            baseline = {}
            if unit["expanded"]["status"] == "ok":
                base_vector = hidden[original_mask].mean(0).cpu().numpy()
                base_probs = probabilities(models, base_vector[None])
                baseline = {name: prediction(v[0]) for name, v in base_probs.items()}
                for name in ("expanded", "pilot"):
                    expected = [unit[name]["probabilities"][c] for c in CLASSES]
                    reproduce[name] = float(np.max(np.abs(base_probs[name][0] - expected)))
                    if reproduce[name] > 1e-6:
                        raise ValueError("baseline_probabilities_not_reproduced")
                # Compare against the untouched existing pooled-vector cache as well.
                record = unit["expanded"]["embedding"]
                cached = (
                    PACKAGE
                    / "data/generated/dev-learned-takes-v1/cache/embeddings"
                    / (record["key"] + ".npy")
                )
                if file_hash(cached) != record["sha256"]:
                    raise ValueError("original_embedding_corrupted")
                delta = float(np.max(np.abs(np.load(cached, allow_pickle=False)[1] - base_vector)))
                reproduce["original_vector_max_abs_delta"] = delta
                if delta > 1e-6:
                    raise ValueError("baseline_vector_not_reproduced")
            # Preserve and verify crop PCM identity; WAV container headers can differ.
            with wave.open(str(take / "canonical.wav")) as stream:
                rate = stream.getframerate()
                source = stream.readframes(stream.getnframes())
            clip_checks = {}
            for kind, interval in zip(
                ("whole", "tone", "context"), (whole, pool, context), strict=True
            ):
                with wave.open(str(take / unit["clips"][kind])) as stream:
                    actual = stream.readframes(stream.getnframes())
                a, b = [sample_index(t, rate) * 2 for t in interval]
                clip_checks[kind] = actual == source[a:b]
            if not all(clip_checks.values()):
                raise ValueError("crop_pcm_mismatch")
            original_points = saved_raw[i]["segments"]
            new_points = [
                [p for p in seg if whole[0] <= p["timestamp_seconds"] < whole[1]]
                for seg in graph["filtered"]["segments"]
            ]
            if original_points != [s for s in new_points if s]:
                raise ValueError("full_pitch_does_not_reproduce_saved_pitch")
            whole_evidence = acoustic_summary(graph, whole)
            pool_evidence = acoustic_summary(graph, pool)
            usable = unit["expanded"]["status"] == "ok"
            variants = compact_grid(pool, whole)
            for v in variants:
                v["hidden_sha256"] = hidden_hash
                v["f0"] = acoustic_summary(graph, [v["start"], v["end"]])
                a, b = [
                    sample_index(t, 16000) - sample_index(context[0], 16000) + PAD
                    for t in (v["start"], v["end"])
                ]
                mask = (centers >= a) & (centers < b)
                v["pooled_frames"] = int(mask.sum())
                v["frame_indices"] = np.flatnonzero(mask).tolist()
                reason = (
                    "original_unusable_no_forced_classification"
                    if not usable
                    else "too_little_material"
                    if v["duration_ms"] < 60 - 1e-6
                    else "no_voiced_support"
                    if not v["f0"]["usable_frames"]
                    else "no_frame_centers"
                    if not mask.any()
                    else None
                )
                v["reason"] = reason
                if reason:
                    continue
                vector = hidden[mask].mean(0).cpu().numpy()
                for name, values in probabilities(models, vector[None]).items():
                    v[name] = prediction(values[0])
                    v[name]["family_changed"] = (
                        v[name]["prediction"] != baseline[name]["prediction"]
                    )
                    v[name]["confidence_delta"] = (
                        v[name]["confidence"] - baseline[name]["confidence"]
                    )
                    v[name]["max_probability_delta"] = max(
                        abs(v[name]["probabilities"][c] - baseline[name]["probabilities"][c])
                        for c in CLASSES
                    )
            valid = [v for v in variants if "expanded" in v]
            summary = {
                "valid_variants": len(valid),
                "distinct_clamped_variants": len(variants),
                "unique_pool_masks": len({tuple(v["frame_indices"]) for v in valid}),
                "family_counts": dict(Counter(v["expanded"]["prediction"] for v in valid)),
                "confidence_range": [
                    min(v["expanded"]["confidence"] for v in valid),
                    max(v["expanded"]["confidence"] for v in valid),
                ]
                if valid
                else None,
                "margin_range": [
                    min(v["expanded"]["margin"] for v in valid),
                    max(v["expanded"]["margin"] for v in valid),
                ]
                if valid
                else None,
                "max_probability_delta": max(
                    (v["expanded"]["max_probability_delta"] for v in valid), default=None
                ),
                "flips": [v for v in valid if v["expanded"]["family_changed"]],
            }
            row = {
                "take": take_number,
                "take_id": tid,
                "index": i,
                "character": unit["target"]["characters"],
                "whole": whole,
                "pool": pool,
                "context": context,
                "pool_duration_ms": (pool[1] - pool[0]) * 1000,
                "phones": unit["alignment"]["aligned_phones"],
                "owned_phone_indices": spans["owned_phone_indices"],
                "original_pooled_frames": unit["expanded"].get("embedding", {}).get("owned_frames"),
                "geometric_pooled_frames": int(original_mask.sum()),
                "whole_acoustics": whole_evidence,
                "pool_acoustics": pool_evidence,
                "voiced_outside_pool_within_whole_frames": whole_evidence["usable_frames"]
                - pool_evidence["usable_frames"],
                "expanded": unit["expanded"],
                "pilot": unit["pilot"],
                "deterministic": unit["deterministic"],
                "comparison": unit["comparison"],
                "alignment_log_likelihood": unit["alignment"]["alignment_diagnostics"][
                    "alignment_log_likelihood"
                ],
                "clip_pcm_checks": clip_checks,
                "reproduction": reproduce,
                "hidden_sha256": hidden_hash,
                "context_pcm_sha256": hashlib.sha256(audio.tobytes()).hexdigest(),
                "variants": variants,
                "perturbation_summary": summary,
                "stability": stability(
                    variants, baseline.get("expanded", {}).get("prediction"), usable=usable
                ),
            }
            # Baseline probabilities for gated units are deliberately not emitted.
            rows.append(row)
            print(
                take_number,
                row["character"],
                row["stability"],
                summary["family_counts"],
                summary["confidence_range"],
                flush=True,
            )
    result = {
        "method": {
            "pooling_only": True,
            "context_fixed": True,
            "clamp": "original whole read unit",
            "grid": "33 requested offsets: axes and both diagonals, +/-40ms in 10ms steps",
            "margin_label": "human descriptive assessment; no new production threshold",
            "unusable": "original abstentions remain unclassified, even if variants gain evidence",
            "endpoint": "nearest sample, half open; >=start and <end frame-center selection",
            "support": "sum of 10ms retained F0 cells clipped to interval, no gap bridging",
            "scope_limit": (
                "does not rule out larger alignment errors or context-window sensitivity"
            ),
        },
        "frozen_verification": frozen,
        "initial_snapshot": initial,
        "encoder_and_models_load_seconds": load_seconds,
        "rows": rows,
        "latency": timing,
        "final_snapshot": verify_snapshot(folder),
    }
    write_generated(folder / "diagnostics.json", result)
    return result


if __name__ == "__main__":
    run()
