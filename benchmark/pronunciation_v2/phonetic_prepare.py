"""Preparation only. Labels can select cases here but never cross the acoustic manifest boundary."""

import argparse
import hashlib
import json
from dataclasses import fields
from pathlib import Path

from benchmark.pronunciation_v2.phonetic_evidence import SavedFrame, dump, sha

STUDIES = ("S01", "S02", "S03", "S13")
FOCAL = {
    ("S01", "u3"): "recovered_timing",
    ("S01", "u10"): "recovered_timing",
    ("S01", "u11"): "recovered_timing",
    ("S02", "u4"): "recovered_timing",
    ("S02", "u9"): "recovered_timing",
    ("S03", "u6"): "recovered_timing",
    ("S02", "u10"): "user_reported_possible_issue_not_gold",
    ("S13", "u3"): "lexical_substitution_control_not_phonetic_gold",
    ("S13", "u4"): "lexical_substitution_control_not_phonetic_gold",
}


def control_candidates(records):
    candidates = []
    for study in ("S02", "S03"):
        record = records[study]
        if record["alignment"]["issues"]:
            continue
        for unit in record["units"]:
            if (study, unit["unit_id"]) in FOCAL or not unit["timing"]:
                continue
            pitch = unit["pitch"]
            if pitch["usable_frame_count"] < 5:
                continue
            if any(not p.get("quality_usable", True) for p in pitch["frames"]):
                continue
            if not any(p.get("energy_rms", 0) > 0 for p in pitch["frames"]):
                continue
            candidates.append(
                (
                    study,
                    unit["unit_id"],
                    pitch["usable_frame_count"] / pitch["frame_count"],
                    pitch["usable_frame_count"],
                )
            )
    return sorted(candidates, key=lambda row: (-row[2], -row[3], row[0], int(row[1][1:])))


def prepare(source_root, reviewed_root, output):
    records, provenance = {}, {}
    for study in STUDIES:
        path = source_root / f"benma-study-{study}" / "record.json"
        original = json.loads(path.read_text())  # Missing captures/audio stop the pass.
        reviewed_path = reviewed_root / study / "record.json"
        reviewed = json.loads(reviewed_path.read_text())
        if reviewed["schema_version"] != "connected-speech-v2":
            raise ValueError("Expected the completed mapping-pass record")
        for field in ("recording_id", "audio", "perception", "acoustics"):
            if original[field] != reviewed[field]:
                raise ValueError(f"Reviewed record changed saved evidence: {field}")
        if original["alignment"]["raw_response"] != reviewed["alignment"]["raw_response"]:
            raise ValueError("Provider capture changed")
        if reviewed["alignment"]["issues"] or any(u["timing"] is None for u in reviewed["units"]):
            raise ValueError("Mapping pass not complete or conflicting")
        if sha(original["audio"]["path"]) != original["audio"]["sha256"]:
            raise ValueError("Source audio changed")
        if reviewed["replay"]["source_record_sha256"] != sha(path):
            raise ValueError("Reviewed mapping does not derive from source capture")
        records[study] = reviewed
        provenance[study] = {
            "source_record_sha256": sha(path),
            "reviewed_record_sha256": sha(reviewed_path),
            "audio": original["audio"],
        }
    candidates = control_candidates(records)
    if len(candidates) < 3:
        raise ValueError("Insufficient eligible controls")
    selected = dict(FOCAL)
    selected.update({(s, u): "acoustic_evidence_control_not_gold" for s, u, _, _ in candidates[:3]})
    order = sorted(
        selected, key=lambda k: hashlib.sha256(f"phonetic-v1:{k[0]}:{k[1]}".encode()).hexdigest()
    )
    manifest, key = [], []
    names = {f.name for f in fields(SavedFrame)}
    for i, (study, uid) in enumerate(order, 1):
        record = records[study]
        unit = next(u for u in record["units"] if u["unit_id"] == uid)
        span = {k: unit["timing"][k] for k in ("start_ms", "end_ms")}
        frames = [
            {k: p.get(k, True if k == "quality_usable" else None) for k in names}
            for p in record["acoustics"]["f0"]
            if span["start_ms"] <= p["timestamp_seconds"] * 1000 < span["end_ms"]
        ]
        rid = f"R{i:02d}"
        manifest.append(
            {
                "id": rid,
                "audio_path": record["audio"]["path"],
                "audio_sha256": record["audio"]["sha256"],
                "span": span,
                "saved_frames": frames,
            }
        )
        key.append(
            {
                "id": rid,
                "study": study,
                "unit": uid,
                "character": unit["perceived_text"],
                "selection": selected[(study, uid)],
                "span": span,
            }
        )
    output.mkdir(parents=True, exist_ok=False)
    dump(output / "acoustic-manifest.json", {"version": 1, "regions": manifest})
    dump(
        output / "unblinding-key.json",
        {"regions": key, "control_ranking": candidates, "provenance": provenance},
    )
    print(f"Prepared {len(manifest)} regions. Key is separate; do not open before packet sealing.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, default=Path("/tmp"))
    parser.add_argument(
        "--reviewed-root",
        type=Path,
        default=Path("services/api/var/connected-study/mapping-v2-reviewed"),
    )
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    prepare(args.source_root, args.reviewed_root, args.output)


if __name__ == "__main__":
    main()
