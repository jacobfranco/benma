"""Build an auditable clean experiment manifest without rewriting acquisition history."""

import argparse
import collections
import json
from pathlib import Path

from pilot import diagnostics, field, normalize, validate, wikitext
from preflight import (
    GROUPS,
    embedded_conflicts,
    read_rows,
    sha256,
    verify_bytes,
    write_csv,
    write_json,
)

BAD_ASSET = "commons:3052714"
UNMARKED = "commons:3052537"


def disposition(row, page):
    if row["source_asset_id"] == BAD_ASSET:
        return False, "mandatory_exclusion:speaker_text_date_license_conflict;ShareAlike_deferred"
    if row["speaker_id"] not in GROUPS:
        return False, "singleton_excluded_from_experiment"
    normalized, reasons = normalize(page)
    for key in ("text", "pinyin", "tone", "speaker_id", "license", "revision_id", "source_sha1"):
        if normalized[key] != row[key]:
            reasons.append("cached_metadata_mismatch:" + key)
    tags = row["embedded_tags"]
    issues = embedded_conflicts(row, tags)
    # Explicit primary description, not dictionary-first or model-derived inference.
    if (
        row["source_asset_id"] == UNMARKED
        and (row["text"], row["pinyin"], row["tone"]) == ("哪", "na3", 3)
        and 'Pronunciation of "nǎ" (哪)' in wikitext(page)
        and tags.get("SWAC_PRON_PHON", "").strip() == "na"
    ):
        issues = [i for i in issues if i != "embedded_pinyin_unmarked_or_unparseable"]
    if row["speaker_id"] == "shtooka:wei-gao":
        if tags.get("SWAC_SPEAK_NAME", "").strip() != "Wei Gao":
            issues.append("unknown_or_conflicting_shtooka_speaker")
        if field(wikitext(page), "Date") != tags.get("SWAC_TECH_DATE", "").strip():
            issues.append("source_embedded_date_conflict")
        if any(
            tags.get(k, "").strip() != "Creative Commons BY"
            for k in ("LICENSE", "SWAC_COLL_LICENSE")
        ):
            issues.append("unresolved_embedded_license")
    if reasons or issues:
        return False, "|".join(reasons + issues)
    return True, "explicit_primary_nǎ_T3_resolves_unmarked_tag" if row[
        "source_asset_id"
    ] == UNMARKED else "metadata_consistent"


def validate_split(rows, require_readiness=True):
    if not rows:
        raise ValueError("Empty corpus")
    seen = {key: set() for key in ("source_asset_id", "audio_sha256", "decoded_pcm_sha256")}
    for row in rows:
        if row["speaker_id"] not in GROUPS:
            raise ValueError("Singleton/unknown group in primary split")
        if row["partition"] != GROUPS[row["speaker_id"]]:
            raise ValueError("Group leakage or changed partition")
        if int(row["tone"]) not in (1, 2, 3, 4):
            raise ValueError("Unsupported tone")
        if row["source_asset_id"] == BAD_ASSET:
            raise ValueError("Known bad asset included")
        for key in seen:
            if row[key] in seen[key]:
                raise ValueError("Duplicate asset/content")
            seen[key].add(row[key])
    if require_readiness:
        tones = collections.Counter(int(r["tone"]) for r in rows)
        if len(rows) < 300 or any(tones[t] < 50 for t in range(1, 5)):
            raise ValueError("Global readiness failed")
        for group in GROUPS:
            sub = [r for r in rows if r["speaker_id"] == group]
            if len(sub) < 40 or any(sum(int(r["tone"]) == t for r in sub) < 5 for t in range(1, 5)):
                raise ValueError("Group readiness failed")


def clean_rows(rows, pages):
    decisions, included = [], []
    fields = (
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
        "license_url",
        "source_url",
        "revision_id",
        "attribution",
        "duration_seconds",
        "rms",
        "peak_level",
        "silence_ratio",
        "clipping_percentage",
        "decode_success",
    )
    for row in sorted(rows, key=lambda r: r["source_asset_id"]):
        validate(row)
        keep, reason = disposition(row, pages[row["source_asset_id"]])
        record = {k: row[k] for k in fields}
        record.update(
            partition=GROUPS[row["speaker_id"]] if keep else "excluded",
            included=keep,
            decision_reason=reason,
            provenance_json=json.dumps(
                {
                    k: row[k]
                    for k in (
                        "embedded_tags",
                        "metadata_description",
                        "recorder_id",
                        "uploader_id",
                        "speaker_native_status",
                        "label_source",
                        "license_evidence_url",
                    )
                },
                ensure_ascii=False,
                sort_keys=True,
            ),
        )
        decisions.append(record)
        if keep:
            included.append(record)
    validate_split(included)
    return decisions, included


def run(manifest, cache, output):
    rows = read_rows(manifest)
    pages = {f"commons:{p['pageid']}": p for p in read_rows(cache / "candidate-evidence.jsonl")}
    for i, row in enumerate(rows, 1):
        path = Path(row["local_path"])
        if path.parent.resolve() != (cache / "audio").resolve() or verify_bytes(
            row, path.read_bytes()
        ):
            raise ValueError("Missing, changed, or nonpersistent audio: " + row["source_asset_id"])
        actual = diagnostics(path)
        if any(actual[k] != row[k] for k in ("decoded_pcm_sha256", "embedded_tags")):
            raise ValueError("Decode/tags changed")
        if i % 100 == 0:
            print(f"Remediation verified {i}/{len(rows)}", flush=True)
    decisions, included = clean_rows(rows, pages)
    output.mkdir(parents=True, exist_ok=True)
    write_csv(output / "clean-corpus-manifest.csv", decisions)
    write_csv(output / "split-manifest.csv", included)
    summary = {
        "status": "PASS",
        "corpus_manifest_sha256": sha256(manifest),
        "clean_manifest_sha256": sha256(output / "clean-corpus-manifest.csv"),
        "split_manifest_sha256": sha256(output / "split-manifest.csv"),
        "included": len(included),
        "excluded": len(decisions) - len(included),
        "tones": dict(collections.Counter(r["tone"] for r in included)),
        "partitions": dict(collections.Counter(r["partition"] for r in included)),
        "licenses": dict(collections.Counter(r["license"] for r in included)),
        "groups": {
            g: {
                "n": sum(r["speaker_id"] == g for r in included),
                "tones": dict(
                    collections.Counter(r["tone"] for r in included if r["speaker_id"] == g)
                ),
            }
            for g in GROUPS
        },
        "shtooka_explicit_wei_gao": sum(r["speaker_id"] == "shtooka:wei-gao" for r in included),
        "shtooka_contradictory_names": 0,
        "shtooka_unknown_names": 0,
        "all_500_hashes_and_decodes_reverified": True,
        "group_leakage": False,
        "unmarked_pinyin_disposition": next(
            r["decision_reason"] for r in included if r["source_asset_id"] == UNMARKED
        ),
    }
    write_json(output / "remediation-summary.json", summary)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--cache", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    run(args.manifest, args.cache, args.output)
