"""Post-freeze exploratory physical-recording probe, with explicit span mismatch."""

import json
import subprocess
import sys
from pathlib import Path

import joblib

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from aishell3_train import DEFAULT_RUN, now, probabilities
from perceptual_tone.aishell3_embeddings import LAYERS, Encoder
from perceptual_tone.aishell3_learning import CLASSES
from perceptual_tone.audio import read_audio
from perceptual_tone.common import PACKAGE, ROOT, file_hash, read_json, read_rows, write_json
from perceptual_tone.manifest import verify_baseline


def run():
    folder = DEFAULT_RUN
    seal = read_json(folder / "test-seal.json")
    for name, sha in seal["files"].items():
        if file_hash(folder / name) != sha:
            raise ValueError("test_result_not_frozen")
    verify_baseline()
    selected = read_json(folder / "selected.json")
    best = selected["best_family_by_validation"]
    item = selected["models"][best]
    config = item["config"]
    if config["features"] != "embedding":
        raise ValueError("this_probe_requires_selected_audio_only_model")
    destination = folder / "external-probe.json"
    if destination.exists():
        saved = read_json(folder / "external-probe-seal.json")
        if saved["sha256"] != file_hash(destination):
            raise ValueError("probe_changed")
        return read_json(destination)
    model = joblib.load(folder / item["file"])
    encoder = Encoder(config["encoder"], folder / "external-embedding-cache", folder / "canonical")
    inventory = []
    excluded = []
    sources = {}
    stage = PACKAGE / "stage0.baseline.jsonl"
    sources[str(stage.relative_to(ROOT))] = file_hash(stage)
    for row in read_rows(stage):
        t = row["target"]
        d = row["deterministic"]
        if t["unit_kind"] != "syllable":
            excluded.append(
                {
                    "example_id": row["example_id"],
                    "reason": "grouped_timing_no_independent_syllable_span",
                }
            )
            continue
        inventory.append(
            {
                "example_id": row["example_id"],
                "recording": row["recording_id"],
                "transcript": row["utterance"],
                "syllable": t["syllable"],
                "index": t["syllable_index"],
                "audio": str(ROOT / row["audio"]["reference"]),
                "audio_sha256": row["audio"]["sha256"],
                "start": t["start_seconds"],
                "end": t["end_seconds"],
                "baseline_prediction": d["observed_family"].replace("TONE_", "T")
                if d["family_decision"] == "NUMBERED"
                else None,
                "baseline_decision": d["family_decision"],
                "baseline_support": d["family_scores"],
                "source": str(stage.relative_to(ROOT)),
                "recording_kind": (
                    "archived physical recording; identity not independently adjudicated"
                ),
                "neutral_expected_analysis_only": row["expected"]["neutral_context"],
            }
        )
    fixture_root = ROOT / "apps/mobile/src/__tests__/fixtures"
    fixtures = [
        fixture_root / "toneFeedbackPhysical.json",
        fixture_root / "toneClassificationPhysical.json",
    ]
    provenance_path = (
        ROOT
        / "docs/research/pronunciation-v2/2026-10-12-learner-classification"
        / "physical-provenance.json"
    )
    provenance = {r["id"]: r for r in read_json(provenance_path)}
    sources[str(provenance_path.relative_to(ROOT))] = file_hash(provenance_path)
    known = {r["example_id"] for r in inventory}
    for fixture in fixtures:
        values = read_json(fixture)
        values = values if isinstance(values, list) else [values]
        sources[str(fixture.relative_to(ROOT))] = file_hash(fixture)
        replay = json.loads(
            subprocess.run(
                ["node", str(ROOT / "benchmark/pronunciation_v2/tone_feedback.cjs")],
                input=json.dumps({"analyses": values}),
                text=True,
                capture_output=True,
                check=True,
            ).stdout
        )
        for analysis, out in zip(values, replay["analyses"], strict=True):
            if analysis["id"] in provenance:
                info = provenance[analysis["id"]]
                audio = ROOT / "services/api/var/audio" / info["storage_key"]
                sha = info["audio_sha256"]
                kind = info["label"]
            else:
                info = analysis["provenance"]
                sha = info["audio_sha256"]
                kind = info["kind"]
                paths = list(
                    (ROOT / "services/api/var/audio").glob(
                        "*/canonical/" + info["recording"] + ".wav"
                    )
                )
                if len(paths) != 1:
                    raise ValueError("ambiguous_physical_recording")
                audio = paths[0]
            recording = audio.stem
            for chunk in out["chunks"]:
                for unit in chunk["constituents"]:
                    u = unit["unit"]
                    o = unit["observed"]
                    example = recording + ":" + str(u["members"][0]["index"])
                    if example in known:
                        continue
                    if u["grouped"]:
                        excluded.append(
                            {
                                "example_id": example,
                                "reason": "grouped_timing_no_independent_syllable_span",
                            }
                        )
                        continue
                    known.add(example)
                    inventory.append(
                        {
                            "example_id": example,
                            "recording": recording,
                            "transcript": analysis["alignment_reference_text"],
                            "syllable": u["text"],
                            "index": u["members"][0]["index"],
                            "audio": str(audio),
                            "audio_sha256": sha,
                            "start": u["start"],
                            "end": u["end"],
                            "baseline_prediction": o["tone"].replace("TONE_", "T")
                            if o["decision"] == "NUMBERED"
                            else None,
                            "baseline_decision": o["decision"],
                            "baseline_support": o["fits"],
                            "source": str(fixture.relative_to(ROOT)),
                            "recording_kind": kind,
                            "neutral_expected_analysis_only": u["members"][0].get("lexical_tone")
                            == 0,
                        }
                    )
    protocol = {
        "started_at": now(),
        "test_seal_sha256": file_hash(folder / "test-seal.json"),
        "best_family": best,
        "model_sha256": item["sha256"],
        "config": config,
        "sources": sources,
        "inventory_scope": (
            "All suitable single-syllable units in Stage-0 plus toneFeedbackPhysical and "
            "toneClassificationPhysical; synthetic fixtures excluded. "
            "Six distinct archived 我想买这个 takes."
        ),
        "pooling_limitation": (
            "Physical archives have whole-syllable timings, not reviewed nucleus/coda phone spans. "
            "Uniformly pool the existing whole syllable as a proxy. "
            "Same frozen weights/layer/context; "
            "this is an exploratory representation mismatch, not matched-span evaluation."
        ),
        "context_policy": (
            "existing whole-syllable +/-250ms clipped to recording; "
            "same uniform 200-sample edge padding"
        ),
        "no_tuning": True,
        "no_accuracy_ground_truth": True,
        "neutral_caution": (
            "Four-way probabilities exclude T5; do not grade neutral 个 from these outputs."
        ),
    }
    write_json(folder / "external-probe-protocol.json", protocol)
    predicted = []
    for row in inventory:
        _, rate, frames = read_audio(row["audio"], row["audio_sha256"])
        a, b = row["start"], row["end"]
        contract = {
            "audio_reference": row["audio"],
            "audio_sha256": row["audio_sha256"],
            "read_unit": [a, b],
            "pooling": [a, b],
            "context": [max(0, a - 0.25), min(frames / rate, b + 0.25)],
        }
        vectors, record = encoder.extract(contract, config["view"])
        matrix = vectors[LAYERS.index(config["layer"])][None, :]
        prob = probabilities(model, matrix)[0]
        predicted.append(
            {
                **row,
                "probabilities": prob.tolist(),
                "prediction": CLASSES[prob.argmax()],
                "pooling_contract": contract,
                "embedding_cache_key": record["key"],
            }
        )
    results = {
        "protocol": protocol,
        "predictions": predicted,
        "excluded": excluded,
        "finished_at": now(),
    }
    write_json(destination, results)
    write_json(
        folder / "external-probe-seal.json",
        {
            "sha256": file_hash(destination),
            "protocol_sha256": file_hash(folder / "external-probe-protocol.json"),
            "frozen_at": now(),
        },
    )
    verify_baseline()
    return results


if __name__ == "__main__":
    results = run()
    print(
        json.dumps(
            {
                "units": len(results["predictions"]),
                "excluded": len(results["excluded"]),
                "phrase_takes": sorted(
                    {
                        r["recording"]
                        for r in results["predictions"]
                        if "我想买这个" in r["transcript"]
                    }
                ),
            },
            indent=2,
        )
    )
