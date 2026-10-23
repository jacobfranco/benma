"""Seal acoustic choices, then evaluate frozen heads; reuse exact persisted contracts."""

import argparse
import copy
import csv

import numpy as np

from .azure_timing_replay import audio_contract, geometric_frames
from .common import PACKAGE, ROOT, file_hash, read_json, write_json
from .f0_independent_replay import CLASSES, distance, sources
from .f0_independent_replay import OUT as PRIOR
from .ownership_diagnostics import OUT, audio
from .ownership_selector import CANDIDATES, FEATURE_KEYS, select_region

POLICY = "GAP_AWARE_AZURE"
PRIMARY = {("google", 2), ("take-2", 2), ("take-2", 1), ("google", 3)}


def acoustic_inputs():
    """Project metadata away before selection, including all saved pitch fields."""
    result = []
    for source in sources():
        values, rate = audio(source["audio"])
        with (OUT / f"diagnostics/{source['name']}-features.csv").open() as stream:
            spectral = [{k: float(r[k]) for k in FEATURE_KEYS} for r in csv.DictReader(stream)]
        units = source["units"]
        for i, unit in enumerate(units):
            result.append(
                {
                    "recording": source["name"],
                    "index": unit["index"],
                    "inputs": {
                        "whole": unit["whole"],
                        "previous": units[i - 1]["whole"] if i else None,
                        "following": units[i + 1]["whole"] if i + 1 < len(units) else None,
                        "duration": len(values) / rate,
                        "energy": [
                            [p["timestamp_seconds"], p["energy_rms"]] for p in source["raw"]["f0"]
                        ],
                        "threshold": source["raw"]["energy_gate"]["threshold_rms"],
                        "spectral": spectral,
                    },
                }
            )
    return result


def derive():
    rows = []
    for r in acoustic_inputs():
        names = CANDIDATES if (r["recording"], r["index"]) in PRIMARY else (POLICY,)
        for name in names:
            rows.append(
                {
                    "recording": r["recording"],
                    "index": r["index"],
                    "candidate": name,
                    "selection": select_region(**r["inputs"], candidate=name),
                }
            )
    return rows


def seal():
    rows = derive()
    write_json(
        OUT / "policy-before-inference.json",
        {
            "selected_policy": POLICY,
            "choice_basis": (
                "Acoustic evidence only: preserve full speech including fricative onset; "
                "reject deep splits between substantial islands. No output ranking or "
                "threshold sweep."
            ),
            "hypothesis_limits": (
                "Exploratory constants and only four recordings. A fricative onset exception "
                "is not phonetic proof; model sensitivity may block readiness."
            ),
            "constants": {
                "minimum_seconds": 0.060,
                "gap_seconds": 0.020,
                "depression_db": -20,
                "frication_zcr": 0.25,
                "frication_high_band_fraction": 0.25,
                "frication_majority": 0.5,
                "following_duration_ratio": 3,
            },
            "candidate_definitions": {
                "AZURE_SAFE_BASELINE": (
                    "Full neighbor-valid Azure, >=60ms broadband support; no internal ownership "
                    "guard. Deliberately permissive control."
                ),
                "CONTIGUOUS_SPEECH_SUPPORT": (
                    "Longest above-gate island; abstain if another island >=60ms, never silently "
                    "resolve two substantial islands."
                ),
                "GAP_AWARE_AZURE": (
                    "Full Azure; reject >=20ms, >=20dB deep gaps with >=60ms islands on both "
                    "sides except short majority-fricative left-edge onset followed by >=3x body "
                    "with >=60ms nonfricative support."
                ),
            },
            "no_expansion": (
                "No padding selected. Analyze hypothetical one-encoder-stride onset "
                "extension geometrically, clamped to unassigned neighbor-gap midpoint."
            ),
            "source_hashes": {
                str(p.relative_to(ROOT)): file_hash(p)
                for p in sorted((PACKAGE / "perceptual_tone").glob("ownership_*.py"))
            },
            "diagnostic_hashes": {
                str(p.relative_to(ROOT)): file_hash(p)
                for p in sorted((OUT / "diagnostics").glob("*"))
            },
            "freeze_sha256": file_hash(OUT / "freeze-before.json"),
            "rows": rows,
        },
    )


def verify_freeze():
    before = read_json(OUT / "freeze-before.json")
    changed = [
        p
        for p, sha in before["files"].items()
        if not (ROOT / p).is_file() or file_hash(ROOT / p) != sha
    ]
    if changed:
        raise ValueError(f"frozen_files_changed: {changed}")
    return {
        "verified_files": len(before["files"]),
        "changed": changed,
        "freeze_sha256": file_hash(OUT / "freeze-before.json"),
    }


def run():
    from benma_api.pronunciation.learned_runtime import validate_contract

    from .aishell3_embeddings import Encoder
    from .dev_inference import abstention
    from .learner_transfer import load_models, probabilities

    plan = read_json(OUT / "policy-before-inference.json")
    assert plan["rows"] == derive()
    assert plan["freeze_sha256"] == file_hash(OUT / "freeze-before.json")
    for path, sha in {**plan["source_hashes"], **plan["diagnostic_hashes"]}.items():
        assert file_hash(ROOT / path) == sha, path
    verify_freeze()
    lock = read_json(PACKAGE / "configs/dev-learned-lock.json")
    for path, sha in lock["files"].items():
        assert file_hash(ROOT / path) == sha, path
    prior = {(r["recording"], r["index"]): r for r in read_json(PRIOR / "results.json")["rows"]}
    inputs = {(r["recording"], r["index"]): r["inputs"] for r in acoustic_inputs()}
    # Selection and the complete acoustic plan are sealed before any head is loaded.
    encoder = Encoder("chinese_hubert_base", OUT / "cache/embeddings", OUT / "cache/canonical")
    assert encoder.base.weights == lock["encoder_weights"]
    models = load_models(lock["model_method"])
    rows, evaluated = [], []
    for planned in plan["rows"]:
        row = copy.deepcopy(planned)
        key = (row["recording"], row["index"])
        old, inp, sel = prior[key], inputs[key], row["selection"]
        row.update(
            character=old["character"],
            take_id=old["take_id"],
            pitch_evidence=old["pitch_evidence"],
            neutral=old["neutral"],
        )
        template = old["representations"]["AZURE_WHOLE"]["contract"]
        contract = (
            audio_contract(
                template["audio_reference"],
                template["audio_sha256"],
                inp["whole"],
                sel["span"],
                inp["duration"],
            )
            if sel["span"]
            else None
        )
        if contract:
            contract["context"] = template["context"]
        row.update(contract=contract, pooled_frames=0, outputs=None)
        reason = sel["reason"] if sel["representation"] != "usable" else None
        reason = reason or ("neutral_outside_four_tone_model" if old["neutral"] else None)
        row["gate_reason"] = reason
        row["learned_representation"] = "abstain" if reason else "usable"
        if reason:
            row["outputs"] = {m: abstention(reason) for m in models}
            row["inference_source"] = "abstained_before_encoder"
        else:
            validate_contract(contract)
            matches = [
                (name, r)
                for name, r in old["representations"].items()
                if r["contract"] == contract and r.get("pooled_frames", 0) > 0
            ]
            matches += [
                (f"new:{r['candidate']}", r) for r in evaluated if r["contract"] == contract
            ]
            if matches:
                name, match = matches[0]
                row.update(
                    outputs=match["outputs"],
                    pooled_frames=match["pooled_frames"],
                    inference_source=f"exact_contract_reuse:{name}",
                )
            else:
                vector, record = encoder.extract(contract, "context")
                row["outputs"] = {}
                row["pooled_frames"] = record["owned_frames"]
                row["embedding"] = record
                row["inference_source"] = "fresh_frozen_inference"
                for model, matrix in probabilities(models, vector[1][None]).items():
                    p = matrix[0]
                    row["outputs"][model] = {
                        "status": "ok",
                        "reason": None,
                        "prediction": CLASSES[int(p.argmax())],
                        "probabilities": dict(zip(CLASSES, p.tolist(), strict=True)),
                    }
            assert row["pooled_frames"] == geometric_frames(contract)
            evaluated.append(row)
        ref = old["representations"]["CURRENT_REFERENCE"]
        row["current_reference"] = ref
        row["stability"] = {
            m: distance(ref["outputs"][m], row["outputs"][m])
            for m in models
            if ref["outputs"][m]["status"] == "ok" and row["outputs"][m]["status"] == "ok"
        }
        row["representation_changed"] = ref["contract"] != contract
        if contract:
            onset = copy.deepcopy(contract)
            limit = (inp["previous"][1] + inp["whole"][0]) / 2 if inp["previous"] else 0
            onset["pooling"][0] = max(0, inp["whole"][0] - 0.020, limit)
            onset["read_unit"][0] = onset["pooling"][0]
            row["onset_geometry_only"] = {
                "added_ms": 1000 * (inp["whole"][0] - onset["pooling"][0]),
                "span": onset["pooling"],
                "added_frame_centers": geometric_frames(onset) - geometric_frames(contract),
            }
        rows.append(row)
        print(
            row["recording"],
            row["index"],
            row["candidate"],
            row["inference_source"],
            row["outputs"]["expanded"]["prediction"],
            row["outputs"]["pilot"]["prediction"],
            flush=True,
        )
    final = [r for r in rows if r["candidate"] == POLICY]
    aggregate = {
        "units": len(final),
        "current_usable": sum(r["current_reference"]["pooled_frames"] > 0 for r in final),
        "new_usable": sum(r["pooled_frames"] > 0 for r in final),
        "restored": [],
        "lost": [],
        "representation_changed": sum(r["representation_changed"] for r in final),
        "heads": {},
        "disagreements": [],
    }
    for r in final:
        identity = f"{r['recording']}:{r['index']}"
        if r["pooled_frames"] and not r["current_reference"]["pooled_frames"]:
            aggregate["restored"].append(identity)
        if r["current_reference"]["pooled_frames"] and not r["pooled_frames"]:
            aggregate["lost"].append(identity)
        if (
            r["pooled_frames"]
            and r["outputs"]["expanded"]["prediction"] != r["outputs"]["pilot"]["prediction"]
        ):
            aggregate["disagreements"].append(identity)
    for model in models:
        pairs = [(r, r["stability"][model]) for r in final if model in r["stability"]]
        aggregate["heads"][model] = {
            "mutually_usable": len(pairs),
            "argmax_changes": [
                f"{r['recording']}:{r['index']}" for r, d in pairs if not d["same_argmax"]
            ],
            "mean_tv": float(np.mean([d["total_variation"] for _, d in pairs])),
            "max_tv": max(d["total_variation"] for _, d in pairs),
        }
    write_json(
        OUT / "results.json",
        {
            "rows": rows,
            "aggregate": aggregate,
            "policy_sha256": file_hash(OUT / "policy-before-inference.json"),
            "prior_results_sha256": file_hash(PRIOR / "results.json"),
            "encoder_weights": encoder.base.weights,
            "encoder_cache_misses": encoder.misses,
            "encoder_cache_hits": encoder.hits,
        },
    )
    write_json(OUT / "freeze-verification.json", verify_freeze())
    fields = [
        "recording",
        "index",
        "character",
        "candidate",
        "ownership",
        "learned_representation",
        "pitch",
        "span",
        "frames",
        "expanded",
        "pilot",
        "current_expanded",
        "current_pilot",
        "expanded_tv",
        "pilot_tv",
        "reason",
        "inference_source",
    ]
    with (OUT / "all-candidates.csv").open("x") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for r in rows:
            writer.writerow(
                dict(
                    recording=r["recording"],
                    index=r["index"],
                    character=r["character"],
                    candidate=r["candidate"],
                    ownership=r["selection"]["ownership"],
                    learned_representation=r["learned_representation"],
                    pitch=r["pitch_evidence"]["status"],
                    span=r["selection"]["span"],
                    frames=r["pooled_frames"],
                    expanded=r["outputs"]["expanded"]["prediction"],
                    pilot=r["outputs"]["pilot"]["prediction"],
                    current_expanded=r["current_reference"]["outputs"]["expanded"]["prediction"],
                    current_pilot=r["current_reference"]["outputs"]["pilot"]["prediction"],
                    expanded_tv=r["stability"].get("expanded", {}).get("total_variation"),
                    pilot_tv=r["stability"].get("pilot", {}).get("total_variation"),
                    reason=r["gate_reason"],
                    inference_source=r["inference_source"],
                )
            )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("seal", "run"))
    args = parser.parse_args()
    {"seal": seal, "run": run}[args.action]()
