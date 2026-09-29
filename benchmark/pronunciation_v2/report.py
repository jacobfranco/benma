"""Rebuild compact inventory/audit artifacts from the existing local snapshots."""

import argparse
import collections
import csv
import hashlib
import json
import statistics
from pathlib import Path

from pilot import license_policy, normalize, wikitext, write_jsonl


def rows(path):
    return [json.loads(line) for line in path.read_text().splitlines()]


def counts(records, field):
    return dict(sorted(collections.Counter(str(r.get(field)) for r in records).items()))


MEANINGFUL_SPEAKERS = (
    "shtooka:wei-gao",
    "lingualibre:Q1431140",
    "lingualibre:Q1573006",
    "lingualibre:Q301531",
)


def readiness(manifest):
    tones = collections.Counter(r["tone"] for r in manifest)
    substantial = [r for r in manifest if r["speaker_id"] in MEANINGFUL_SPEAKERS]
    substantial_tones = collections.Counter(r["tone"] for r in substantial)
    by_speaker = {
        sid: [r for r in substantial if r["speaker_id"] == sid] for sid in MEANINGFUL_SPEAKERS
    }
    cells_ok = all(
        len(group) >= 40 and all(sum(r["tone"] == tone for r in group) >= 5 for tone in range(1, 5))
        for group in by_speaker.values()
    )
    return {
        "pipeline_smoke_ready": len(manifest) >= 8
        and all(tones[t] >= 2 for t in range(1, 5))
        and len({r["speaker_id"] for r in manifest}) >= 2,
        "exploratory_experiment_ready": len(substantial) >= 300
        and all(substantial_tones[t] >= 50 for t in range(1, 5))
        and cells_ok,
        "stronger_generalization_ready": False,
        "threshold_scope": (
            "Proposed data readiness gates, not statistical power or production guarantees"
        ),
    }


def report(cache, output):
    pages = rows(cache / "commons-metadata.jsonl")
    candidates = rows(cache / "candidate-evidence.jsonl")
    selected = rows(cache / "selected.jsonl")
    rejected = rows(cache / "rejected.jsonl")
    manifest = (
        rows(output / "pilot-manifest.jsonl") if (output / "pilot-manifest.jsonl").exists() else []
    )
    output.mkdir(parents=True, exist_ok=True)
    eligible_fields = [
        "source_asset_id",
        "source",
        "source_collection",
        "title",
        "source_url",
        "audio_url",
        "source_sha1",
        "source_bytes",
        "speaker_id",
        "speaker_name",
        "speaker_native_status",
        "recorder_id",
        "uploader_id",
        "text",
        "pinyin",
        "tone",
        "syllable_count",
        "license",
        "license_url",
        "license_evidence_url",
        "revision_id",
        "attribution",
        "label_source",
        "label_confidence",
        "provenance_confidence",
        "access_date",
    ]
    eligible_path = output / "eligible-metadata.csv"
    temporary = eligible_path.with_suffix(".csv.tmp")
    with temporary.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=[*eligible_fields, "acquisition_status"], lineterminator="\n")
        writer.writeheader()
        for row in selected:
            writer.writerow(
                {
                    **{key: row.get(key) for key in eligible_fields},
                    "acquisition_status": "metadata_eligible_not_a_local_audio_claim",
                }
            )
    temporary.replace(eligible_path)
    candidate_lookup = {p["pageid"]: p for p in candidates}
    selected_ids = {r["source_asset_id"] for r in selected}
    pilot_ids = {r["source_asset_id"] for r in manifest}
    candidate_rows = []
    for page in candidates:
        record, reasons = normalize(page)
        candidate_rows.append(
            {
                "source_asset_id": record["source_asset_id"],
                "source_url": record["source_url"],
                "revision_id": record["revision_id"],
                "source": record["source"],
                "api_license": record["api_license"],
                "selected_license": record["license"],
                "speaker_id": record["speaker_id"],
                "text": record["text"],
                "pinyin": record["pinyin"],
                "tone": record["tone"],
                "reasons": "|".join(reasons),
                "metadata_eligible": record["source_asset_id"] in selected_ids,
                "in_pilot": record["source_asset_id"] in pilot_ids,
            }
        )
    with (output / "candidate-audit.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(candidate_rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(candidate_rows)
    source_stats = {}
    for name, subset in [
        ("lingua_libre_commons", [p for p in pages if p["title"].startswith("File:LL-")]),
        ("other_commons", [p for p in pages if not p["title"].startswith("File:LL-")]),
    ]:
        licenses = collections.Counter()
        chosen_licenses = collections.Counter()
        uploaders = set()
        sha1s = collections.Counter()
        for page in subset:
            info = page["imageinfo"][0]
            meta = info["extmetadata"]
            licenses[meta.get("LicenseShortName", {}).get("value", "unknown")] += 1
            chosen, _, _ = license_policy(meta, wikitext(candidate_lookup.get(page["pageid"], {})))
            if chosen:
                chosen_licenses[chosen] += 1
            uploaders.add(info.get("user"))
            sha1s[info["sha1"]] += 1
        source_stats[name] = {
            "file_pages": len(subset),
            "api_license_distribution": dict(licenses),
            "license_policy_passes_in_inventory": dict(chosen_licenses),
            "uploader_accounts": len(uploaders),
            "duplicate_sha1_extra_files": sum(n - 1 for n in sha1s.values()),
            "single_character_candidates": sum(p["pageid"] in candidate_lookup for p in subset),
        }
    speakers = []
    for sid in sorted({r["speaker_id"] for r in manifest}):
        subset = [r for r in manifest if r["speaker_id"] == sid]
        speakers.append(
            {
                "speaker_id": sid,
                "speaker_name": subset[0].get("speaker_name"),
                "clips": len(subset),
                "tone_counts": counts(subset, "tone"),
                "native_status": counts(subset, "speaker_native_status"),
                "recorder_ids": sorted(
                    {r.get("recorder_id") for r in subset if r.get("recorder_id")}
                ),
            }
        )
    sha1s = collections.Counter(p["imageinfo"][0]["sha1"] for p in pages)
    sizes = [
        p.stat().st_size for p in (cache / "audio").glob("*") if p.is_file() and p.suffix != ".part"
    ]
    summary = {
        "access_date": "2026-09-28",
        "unique_inventory_pages": len(pages),
        "single_character_candidates": len(candidates),
        "green_single_character_candidates": sum(
            r["selected_license"] is not None for r in candidate_rows
        ),
        "metadata_eligible": len(selected),
        "metadata_rejected": len(rejected),
        "eligible_tones": counts(selected, "tone"),
        "eligible_speakers": counts(selected, "speaker_id"),
        "inventory_sources": source_stats,
        "inventory_sha1_duplicate_groups": sum(n > 1 for n in sha1s.values()),
        "inventory_sha1_duplicate_extra_files": sum(n - 1 for n in sha1s.values()),
        "accepted": len(manifest),
        "readiness": readiness(manifest),
        "downloaded_files_on_disk": len(sizes),
        "audio_bytes_on_disk": sum(sizes),
        "pilot_tones": counts(manifest, "tone"),
        "pilot_licenses": counts(manifest, "license"),
        "pilot_sources": counts(manifest, "source"),
        "pilot_native_status": counts(manifest, "speaker_native_status"),
        "speakers": speakers,
        "largest_speaker_share": max((s["clips"] for s in speakers), default=0) / len(manifest)
        if manifest
        else None,
        "median_clips_per_speaker": statistics.median(s["clips"] for s in speakers)
        if speakers
        else None,
        "rejection_primary_counts": dict(collections.Counter(r["reasons"][0] for r in rejected)),
        "rejection_all_reason_counts": dict(
            collections.Counter(x for r in rejected for x in r["reasons"])
        ),
        "snapshot_sha256": {
            name: hashlib.sha256((cache / name).read_bytes()).hexdigest()
            for name in [
                "commons-metadata.jsonl",
                "categories.json",
                "candidate-evidence.jsonl",
                "selected.jsonl",
                "rejected.jsonl",
            ]
        },
    }
    (output / "inventory-summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n"
    )
    # Compact source-hash duplicate evidence; these are distinct page IDs, not extra unique sounds.
    duplicated = {h for h, n in sha1s.items() if n > 1}
    write_jsonl(
        output / "inventory-duplicates.jsonl",
        [
            {
                "source_asset_id": "commons:" + str(p["pageid"]),
                "source_url": p["imageinfo"][0]["descriptionurl"],
                "source_sha1": p["imageinfo"][0]["sha1"],
            }
            for p in pages
            if p["imageinfo"][0]["sha1"] in duplicated
        ],
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache", type=Path, default=Path("/tmp/benma-pronunciation-v2-pilot"))
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("docs/research/pronunciation-v2/2026-09-28-data-feasibility"),
    )
    args = parser.parse_args()
    report(args.cache, args.output)
