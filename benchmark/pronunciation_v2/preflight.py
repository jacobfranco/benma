"""Read-only corpus revalidation; stop before modeling on provenance conflicts.

Uses the existing pilot environment and decoder. Never downloads, edits the
input manifest, corrects labels, reassigns groups, or fits a model.
"""

import argparse
import collections
import csv
import hashlib
import json
import subprocess
from pathlib import Path

from pilot import diagnostics, normalize, normalize_text, parse_pinyin, validate

GROUPS = {
    "shtooka:wei-gao": "train",
    "lingualibre:Q1431140": "train",
    "lingualibre:Q1573006": "validation",
    "lingualibre:Q301531": "test",
}


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_rows(path):
    return [json.loads(line) for line in path.read_text().splitlines()]


def write_json(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n")


def write_csv(path, rows):
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def embedded_conflicts(row, tags):
    """Flag contradictory evidence; absence of tags is not identity verification."""
    tags = {key: str(value).strip() for key, value in tags.items()}
    issues = []
    speaker = tags.get("SWAC_SPEAK_NAME")
    if row["speaker_id"] == "shtooka:wei-gao" and speaker and speaker != "Wei Gao":
        issues.append("embedded_speaker_conflicts_with_wei_gao_group")
    if tags.get("SWAC_TEXT") and normalize_text(tags["SWAC_TEXT"]) != row["text"]:
        issues.append("embedded_text_differs_from_manifest")
    reading = tags.get("SWAC_PRON_PHON")
    if reading:
        parsed = parse_pinyin(reading)
        if parsed is None:
            issues.append("embedded_pinyin_unmarked_or_unparseable")
        elif parsed != (row["pinyin"], row["tone"]):
            issues.append("embedded_pinyin_differs_from_manifest")
    licenses = [tags.get(key, "").upper() for key in ("LICENSE", "SWAC_COLL_LICENSE")]
    if any("BY-SA" in value for value in licenses) and "BY-SA" not in row["license"]:
        issues.append("embedded_sharealike_vs_selected_license_unresolved")
    return issues


def verify_bytes(row, data):
    checks = {
        "source_bytes": len(data) == row["source_bytes"],
        "source_sha1": hashlib.sha1(data).hexdigest() == row["source_sha1"],
        "local_sha256": hashlib.sha256(data).hexdigest() == row["audio_sha256"],
    }
    return [name + "_mismatch" for name, passed in checks.items() if not passed]


def audit_sample(rows, issues):
    """Shortest/longest per group-tone cell, all singletons and every anomaly."""
    selected = {}
    for group in GROUPS:
        for tone in range(1, 5):
            cell = sorted(
                (r for r in rows if r["speaker_id"] == group and r["tone"] == tone),
                key=lambda r: (r["duration_seconds"], r["source_asset_id"]),
            )
            for row, reason in (
                [(cell[0], "cell_shortest"), (cell[-1], "cell_longest")] if cell else []
            ):
                selected.setdefault(row["source_asset_id"], set()).add(reason)
    for row in rows:
        asset = row["source_asset_id"]
        if row["speaker_id"] not in GROUPS:
            selected.setdefault(asset, set()).add("singleton")
        if issues[asset]:
            selected.setdefault(asset, set()).add("metadata_or_integrity_issue")
    return selected


def run(manifest, cache, output):
    rows = sorted(read_rows(manifest), key=lambda r: r["source_asset_id"])
    pages = {f"commons:{p['pageid']}": p for p in read_rows(cache / "candidate-evidence.jsonl")}
    output.mkdir(parents=True, exist_ok=True)
    issues, decoded, conflicts, records = {}, {}, [], []
    for index, row in enumerate(rows, 1):
        asset = row["source_asset_id"]
        problems = []
        try:
            validate(row)
        except ValueError as exc:
            problems.append("manifest_schema: " + str(exc))
        if parse_pinyin(row["pinyin"]) != (row["pinyin"], row["tone"]):
            problems.append("pinyin_tone_mismatch")
        normalized, reasons = normalize(pages[asset])
        if reasons:
            problems.append("cached_metadata_rejection: " + "|".join(reasons))
        for key in (
            "text",
            "pinyin",
            "tone",
            "speaker_id",
            "license",
            "source_sha1",
            "revision_id",
        ):
            if row[key] != normalized[key]:
                problems.append("cached_metadata_mismatch: " + key)
        path = Path(row["local_path"])
        if path.parent.resolve() != (cache / "audio").resolve():
            problems.append("path_outside_persistent_audio_cache")
        try:
            problems.extend(verify_bytes(row, path.read_bytes()))
            audio = diagnostics(path)
            decoded[asset] = audio
            if audio["decoded_pcm_sha256"] != row["decoded_pcm_sha256"]:
                problems.append("decoded_pcm_hash_mismatch")
            if audio["embedded_tags"] != row["embedded_tags"]:
                problems.append("cached_embedded_tags_mismatch")
            if audio["rms"] < 0.00001 or audio["peak_level"] < 0.0001:
                problems.append("near_silent_signal")
            if audio["clipping_percentage"] > 10:
                problems.append("excessive_clipping")
            problems.extend(embedded_conflicts(row, audio["embedded_tags"]))
        except (OSError, ValueError, subprocess.SubprocessError) as exc:
            problems.append("audio_integrity_failure: " + str(exc))
            audio = {}
        issues[asset] = problems
        if problems:
            conflicts.append({"manifest_row": row, "redecoded_audio": audio, "issues": problems})
        records.append(
            {
                **{
                    key: row[key]
                    for key in (
                        "source_asset_id",
                        "local_path",
                        "audio_sha256",
                        "source_sha1",
                        "decoded_pcm_sha256",
                        "speaker_id",
                        "speaker_name",
                        "text",
                        "pinyin",
                        "tone",
                        "license",
                        "source_url",
                        "revision_id",
                    )
                },
                "proposed_partition_only": GROUPS.get(row["speaker_id"], "auxiliary"),
                **{
                    key: audio.get(key)
                    for key in (
                        "duration_seconds",
                        "sample_rate_hz",
                        "channels",
                        "peak_level",
                        "rms",
                        "silence_ratio",
                        "clipping_percentage",
                        "decode_success",
                    )
                },
                "embedded_speaker": audio.get("embedded_tags", {})
                .get("SWAC_SPEAK_NAME", "")
                .strip(),
                "issues": "|".join(problems),
            }
        )
        if index % 100 == 0:
            print(f"Reverified {index}/{len(rows)}", flush=True)

    duplicates = {}
    for key in (
        "source_asset_id",
        "local_path",
        "source_sha1",
        "audio_sha256",
        "decoded_pcm_sha256",
    ):
        groups = collections.defaultdict(list)
        for row in rows:
            value = decoded.get(row["source_asset_id"], {}).get(key, row[key])
            groups[value].append(row["source_asset_id"])
        duplicates[key] = [assets for assets in groups.values() if len(assets) > 1]

    def counts(items):
        return dict(sorted(collections.Counter(items).items()))

    selected = audit_sample(rows, issues)
    audit = [
        {
            **record,
            "audit_selection": "|".join(sorted(selected[record["source_asset_id"]])),
            "listening_status": "NOT_LISTENED",
        }
        for record in records
        if record["source_asset_id"] in selected
    ]
    group_summary = {}
    for group in sorted({r["speaker_id"] for r in rows}):
        group_rows = [r for r in rows if r["speaker_id"] == group]
        group_summary[group] = {
            "clips": len(group_rows),
            "tones": counts(r["tone"] for r in group_rows),
            "embedded_speakers": counts(
                decoded.get(r["source_asset_id"], {})
                .get("embedded_tags", {})
                .get("SWAC_SPEAK_NAME", "ABSENT")
                .strip()
                for r in group_rows
            ),
        }
    blocked = bool(conflicts) or any(duplicates.values())
    summary = {
        "status": "STOP_BEFORE_TRAINING" if blocked else "PREFLIGHT_DIAGNOSTICS_PASSED",
        "corpus_manifest_sha256": sha256(manifest),
        "cached_evidence_sha256": sha256(cache / "candidate-evidence.jsonl"),
        "manifest_rows": len(rows),
        "decoded_files": len(decoded),
        "local_files_in_audio_directory": sum(p.is_file() for p in (cache / "audio").iterdir()),
        "tones": counts(r["tone"] for r in rows),
        "groups": group_summary,
        "duplicates": duplicates,
        "issue_counts": counts(p for ps in issues.values() for p in ps),
        "flagged_assets": sorted(r["manifest_row"]["source_asset_id"] for r in conflicts),
        "proposed_partition_counts_only": counts(
            GROUPS.get(r["speaker_id"], "auxiliary") for r in rows
        ),
        "split_frozen": False,
        "model_work_started": False,
        "test_metrics_opened": False,
        "listening_performed": False,
        "audit_sample_count": len(audit),
        "all_native_statuses": counts(r["speaker_native_status"] for r in rows),
        "duration_range_seconds": [
            min(a["duration_seconds"] for a in decoded.values()),
            max(a["duration_seconds"] for a in decoded.values()),
        ]
        if decoded
        else None,
        "label_contract": "Lexical labels; not listening-audited surface-tone gold",
    }
    write_csv(output / "corpus-diagnostics.csv", records)
    write_csv(output / "human-listening-audit.csv", audit)
    write_json(output / "provenance-conflicts.json", conflicts)
    write_json(output / "preflight-summary.json", summary)
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 2 if blocked else 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--cache", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    raise SystemExit(run(args.manifest, args.cache, args.output))
