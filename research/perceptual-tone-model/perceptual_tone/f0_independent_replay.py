"""Write-once four-recording experiment; run seal before run. No provider calls."""

import argparse
import itertools
import wave
from pathlib import Path

import numpy as np

from .azure_timing_replay import audio_contract, geometric_frames
from .common import PACKAGE, ROOT, file_hash, read_json, write_json
from .f0_independent import CANDIDATES, select_region
from .three_take_stability import acoustic_summary

OUT = PACKAGE / "data/generated/f0-independent-v1"
GOOGLE = ROOT / "services/api/var/google-mai-autopsy"
SAVED = PACKAGE / "data/generated/azure-timing-replay-v1"
FAST = PACKAGE / "data/generated/fast-timing-ownership-v1"
CLASSES = ("T1", "T2", "T3", "T4")


def sources():
    grouped = {}
    for row in read_json(FAST / "final-results.json")["rows"]:
        grouped.setdefault(row["take_id"], []).append(row)
    result = []
    for tid, rows in grouped.items():
        data = read_json(SAVED / tid / "acoustics.json")
        result.append({
            "name": f"take-{rows[0]['take']}", "take_id": tid, **data,
            "audio": rows[0]["representations"]["final"]["contract"]["audio_reference"],
            "units": [{
                "index": r["index"], "character": r["character"],
                "whole": r["azure_whole"], "neutral": r["outside_numbered_scope"],
                "saved": r["representations"]["final"]["model_outputs"],
                "saved_pool": r["representations"]["final"]["contract"]["pooling"],
            } for r in rows],
        })
    analysis = read_json(GOOGLE / "google-analysis.json")["result"]
    identity = read_json(GOOGLE / "google-identity.json")
    units = analysis["dev_learned_tone"]["units"]
    result.append({
        "name": "google", "take_id": identity["attempts"][0]["id"],
        "audio": identity["audio_path"],
        "raw": read_json(GOOGLE / "google-acoustic.json")["normalized_result"],
        "graph": analysis["tone_graph"],
        "units": [{
            "index": u["index"], "character": u["characters"],
            "whole": u["realization"]["azure_span"], "neutral": u["expected_neutral"],
            "saved": {"expanded": u["realization"]},
            "saved_pool": u["realization"]["pooling_span"],
        } for u in units],
    })
    return result


def derive_rows():
    from benma_api.pronunciation.learned import refine_span
    from benma_api.pronunciation.pitch_evidence import (
        build_pitch_track, interpretation_eligibility, project_pitch,
    )

    rows = []
    for source in sources():
        raw, graph, units = source["raw"], source["graph"], source["units"]
        audio = source["audio"]
        sha = file_hash(audio)
        with wave.open(audio) as stream:
            duration = stream.getnframes() / stream.getframerate()
        retained = [p["timestamp_seconds"] for s in graph["filtered"]["segments"] for p in s]
        track = build_pitch_track(raw, audio_sha256=sha, tracker_source="saved_praat",
                                  tracker_version="frozen", parameters={})
        assert [f.timestamp_seconds for f in track.frames if f.selected_f0_hz is not None] == retained
        energy = [(p["timestamp_seconds"], p["energy_rms"]) for p in raw["f0"]]
        for i, unit in enumerate(units):
            whole = unit["whole"]
            reference = refine_span(whole, retained, raw, duration).model_dump()
            # Historical no-F0 rows recorded whole bounds as an audit placeholder.
            if reference["pooling_span"] is not None:
                assert reference["pooling_span"] == unit["saved_pool"]
            eligibility = interpretation_eligibility(track, project_pitch(
                track, *whole, timing_source="azure_provider_grapheme"
            )).model_dump(mode="json")
            pitch = {
                "status": "usable" if eligibility["state"] == "sufficient" else "unavailable",
                "eligibility": eligibility,
                "measurements": acoustic_summary(graph, whole),
                "coaching_capability": "measurements_only_pending_family_corroboration"
                if eligibility["state"] == "sufficient" else "no_specific_pitch_coaching",
            }
            reps = {}
            for candidate in ("CURRENT_REFERENCE", *CANDIDATES):
                if candidate == "CURRENT_REFERENCE":
                    reason = reference["reason"]
                    span = reference["pooling_span"]
                    representation = {
                        "status": "valid" if not reason else "invalid", "reason": reason,
                        "span": span, "ownership_status": "ambiguous"
                        if reason == "ambiguous_interrupted_voiced_envelope" else "safe",
                        "onset_added_ms": 0.0, "continuity": reference["continuity"],
                    }
                else:
                    representation = select_region(
                        whole, units[i - 1]["whole"] if i else None,
                        units[i + 1]["whole"] if i + 1 < len(units) else None,
                        duration, energy, raw["energy_gate"]["threshold_rms"], candidate,
                    )
                    span = representation["span"]
                    reason = None if representation["status"] == "valid" else representation["reason"]
                reason = reason or ("neutral_outside_four_tone_model" if unit["neutral"] else None)
                contract = None
                if span:
                    owner = [min(span[0], whole[0]), whole[1]]
                    contract = audio_contract(audio, sha, owner, span, duration)
                    # Isolate pooling: every variant has the same original Azure context.
                    contract["context"] = reference["context_span"]
                frames = [p for p in raw["f0"] if span and span[0] <= p["timestamp_seconds"] < span[1]]
                reps[candidate] = {
                    "representation": representation, "contract": contract,
                    "duration_ms": 1000 * (span[1] - span[0]) if span else None,
                    "geometric_frames": geometric_frames(contract) if contract else 0,
                    "gate_reason": reason,
                    "energy": {
                        "threshold_rms": raw["energy_gate"]["threshold_rms"],
                        "above_gate_frames": sum(p["energy_rms"] >= raw["energy_gate"]["threshold_rms"] for p in frames),
                        "total_frames": len(frames),
                    },
                    "f0": acoustic_summary(graph, span) if span else None,
                }
            rows.append({
                "recording": source["name"], "take_id": source["take_id"], **unit,
                "pitch_evidence": pitch, "representations": reps,
            })
    return rows


def seal():
    write_json(OUT / "policy-before-inference.json", {
        "policy": {
            "candidates": ["CURRENT_REFERENCE", *CANDIDATES],
            "minimum_seconds": 0.06, "onset_max_seconds": 0.005,
            "onset_basis": "existing 10 ms acoustic-cell half-width; unassigned gap midpoint clamp",
            "guard": "any internal below-existing-gate energy between supported centers; missing lattice fails closed",
            "selection": "No output-based ranking. Assess ownership, support, coverage costs and descriptive stability.",
            "known_pre_inference_cost": "Energy guard flags take-2 想 as well as take-2 买; no island rescue.",
            "ground_truth": "User listening confirms complete Google Azure 买, not its tone label.",
        },
        "source_hashes": {str(p.relative_to(ROOT)): file_hash(p) for p in (
            Path(__file__), Path(__file__).with_name("f0_independent.py"))},
        "freeze_sha256": file_hash(OUT / "freeze-before.json"),
        "rows": derive_rows(),
    })


def distance(a, b):
    p, q = [np.array([v["probabilities"][c] for c in CLASSES]) for v in (a, b)]
    return {"same_argmax": a["prediction"] == b["prediction"],
            "total_variation": float(abs(p - q).sum() / 2),
            "max_probability_delta": float(abs(p - q).max())}


def run():
    from benma_api.pronunciation.learned_runtime import validate_contract

    from .aishell3_embeddings import Encoder
    from .dev_inference import abstention
    from .learner_transfer import load_models, probabilities

    plan = read_json(OUT / "policy-before-inference.json")
    assert plan["freeze_sha256"] == file_hash(OUT / "freeze-before.json")
    for p, sha in plan["source_hashes"].items():
        assert file_hash(ROOT / p) == sha
    assert derive_rows() == plan["rows"]
    lock = read_json(PACKAGE / "configs/dev-learned-lock.json")
    for p, sha in lock["files"].items():
        assert file_hash(ROOT / p) == sha, p
    encoder = Encoder("chinese_hubert_base", OUT / "cache/embeddings", OUT / "cache/canonical")
    assert encoder.base.weights == lock["encoder_weights"]
    encoder.base._load()
    models = load_models(lock["model_method"])
    rows, reproduction, stability = plan["rows"], [], []
    vectors = {}
    for row in rows:
        for name, rep in row["representations"].items():
            reason = rep["gate_reason"]
            rep["pooled_frames"] = 0
            if reason:
                rep["outputs"] = {model: abstention(reason) for model in models}
                continue
            validate_contract(rep["contract"])
            vector, record = encoder.extract(rep["contract"], "context")
            vectors[(row["recording"], row["index"], name)] = vector[1]
            rep["embedding"] = record
            rep["pooled_frames"] = record["owned_frames"]
            assert rep["pooled_frames"] == rep["geometric_frames"]
            rep["outputs"] = {}
            for model, matrix in probabilities(models, vector[1][None]).items():
                p = matrix[0]
                rep["outputs"][model] = {
                    "status": "ok", "reason": None, "prediction": CLASSES[int(p.argmax())],
                    "probabilities": dict(zip(CLASSES, p.tolist(), strict=True)),
                }
                saved = row["saved"].get(model)
                if name == "CURRENT_REFERENCE" and saved and saved["probabilities"]:
                    delta = distance(saved, rep["outputs"][model])["max_probability_delta"]
                    assert delta <= 1e-6
                    reproduction.append({"recording": row["recording"], "index": row["index"],
                                         "model": model, "max_probability_delta": delta})
            print(row["recording"], row["character"], name,
                  rep["outputs"]["expanded"]["prediction"], rep["pooled_frames"], flush=True)
        for a, b in itertools.combinations(row["representations"], 2):
            left, right = (row["representations"][n] for n in (a, b))
            if not left["pooled_frames"] or not right["pooled_frames"]:
                continue
            va, vb = [vectors[(row["recording"], row["index"], n)] for n in (a, b)]
            stability.append({
                "recording": row["recording"], "index": row["index"], "pair": [a, b],
                "expanded": distance(left["outputs"]["expanded"], right["outputs"]["expanded"]),
                "pilot": distance(left["outputs"]["pilot"], right["outputs"]["pilot"]),
                "embedding_l2": float(np.linalg.norm(va - vb)),
                "embedding_cosine_distance": float(1 - np.dot(va, vb) / (np.linalg.norm(va) * np.linalg.norm(vb))),
            })
    # Repeat one contract with an empty cache to prove fresh deterministic inference.
    encoder.cache = OUT / "repeat/embeddings"
    encoder.cache.mkdir(parents=True, exist_ok=False)
    google = next(r for r in rows if r["recording"] == "google" and r["index"] == 2)
    rep = google["representations"]["AZURE_WHOLE"]
    repeated, record = encoder.extract(rep["contract"], "context")
    original = vectors[("google", 2, "AZURE_WHOLE")]
    assert np.array_equal(repeated[1], original)
    counterfactual_checks = []
    for old, candidate in zip(read_json(GOOGLE / "counterfactual.json")["cases"],
                              ("AZURE_WHOLE", "AZURE_ENERGY_SUPPORTED"), strict=True):
        new = google["representations"][candidate]
        assert old["contract"] == new["contract"]
        delta = distance(old["output"], new["outputs"]["expanded"])["max_probability_delta"]
        assert delta <= 1e-6
        counterfactual_checks.append({"candidate": candidate, "max_probability_delta": delta})
    write_json(OUT / "results.json", {
        "rows": rows, "stability": stability, "reference_reproduction": reproduction,
        "google_counterfactual_reproduction": counterfactual_checks,
        "fresh_repeat_embedding_exact": True,
        "policy_sha256": file_hash(OUT / "policy-before-inference.json"),
        "frozen_lock_sha256": file_hash(PACKAGE / "configs/dev-learned-lock.json"),
        "verified_lock_files": len(lock["files"]), "encoder_weights": encoder.base.weights,
        "encoder_cache_hits": encoder.hits, "encoder_cache_misses": encoder.misses,
    })


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("seal", "run"))
    args = parser.parse_args()
    {"seal": seal, "run": run}[args.action]()
