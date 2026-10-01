"""Experiment 3 bounded metadata audit. No audio/model/prediction access or downloads."""

import argparse
import csv
import hashlib
import html
import json
import re
from collections import Counter, defaultdict

from evaluation_preflight import (
    BLOCKED_IDS,
    BLOCKED_NAMES,
    CACHE,
    OLD,
    ROOT,
    commons_row,
    csv_bytes,
    digest,
    immutable_write,
    jsonl,
    name_key,
    ompal_rows,
)

OUT = ROOT / "docs/research/pronunciation-v2/2026-10-01-experiment-3-preflight"
PRIOR_IDS = frozenset(
    BLOCKED_IDS | {"lingualibre:Q1332695", "lingualibre:Q19614", "lingualibre:Q812770"}
)
PRIOR_NAMES = frozenset(BLOCKED_NAMES | {"jouketou", "雲角", "fakeestate"})
REQUIRED = (
    "source_asset_id",
    "speaker_id",
    "speaker_name",
    "source_url",
    "audio_url",
    "revision_id",
    "license",
    "license_url",
    "license_evidence_url",
    "attribution",
    "source_sha1",
    "speaker_native_status",
    "label_source",
    "text",
    "pinyin",
    "tone",
)


def previously_used(row):
    return row["speaker_id"] in PRIOR_IDS or name_key(row["speaker_name"]) in PRIOR_NAMES


def choose(rows):
    """At least 3 new speakers, >=8 distinct targets/tone each, at most 10/tone.

    Selection reads only metadata allowlist fields, never model scores. Repeated
    source bytes and same-speaker text are deduplicated before checking coverage.
    """
    cells = defaultdict(list)
    seen_ids, seen_bytes, seen_texts = set(), set(), set()
    for row in sorted(rows, key=lambda r: r["source_asset_id"]):
        if row["metadata_status"] != "eligible" or previously_used(row):
            continue
        if any(not row.get(k) for k in REQUIRED):
            raise ValueError("Missing required provenance")
        if str(row["tone"]) not in {"1", "2", "3", "4"}:
            raise ValueError("Only T1-T4")
        asset, source_hash = row["source_asset_id"], row["source_sha1"]
        target = (row["speaker_id"], row["text"])
        if asset in seen_ids:
            raise ValueError("Duplicate source asset")
        seen_ids.add(asset)
        if source_hash in seen_bytes or target in seen_texts:
            continue
        seen_bytes.add(source_hash)
        seen_texts.add(target)
        cells[row["speaker_id"], str(row["tone"])].append(row)
    speakers = sorted(
        {s for s, _ in cells if all(len(cells.get((s, str(t)), [])) >= 8 for t in range(1, 5))}
    )
    if len(speakers) < 3:
        return []
    selected = []
    for speaker in speakers:
        for tone in range(1, 5):
            selected.extend(
                sorted(
                    cells[speaker, str(tone)],
                    key=lambda r: (
                        hashlib.sha256(r["source_asset_id"].encode()).hexdigest(),
                        r["source_asset_id"],
                    ),
                )[:10]
            )
    return selected


def write_csv(path, rows, fields):
    with path.open("x", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def audit():
    OUT.mkdir(parents=True, exist_ok=True)
    inventory = jsonl(OLD / "commons-metadata.jsonl")
    evidence = jsonl(OLD / "candidate-evidence.jsonl")
    # Check authoritative snapshot receipts before reusing exact revision metadata.
    previous = (
        ROOT / "docs/research/pronunciation-v2/2026-09-30-experiment-2-preflight/provenance.json"
    )
    receipts = json.loads(previous.read_text())["inputs_sha256"]
    inputs = [OLD / "commons-metadata.jsonl", OLD / "candidate-evidence.jsonl"]
    inputs += [
        CACHE / "ompal" / n for n in ("tree.json", "README.md", "LICENSE", "native_scores.json")
    ]
    for path in inputs:
        if digest(path) != receipts[str(path)]:
            raise ValueError(f"Cached source snapshot changed: {path}")
    rows = [commons_row(page, allow_sharealike=True) for page in evidence] + ompal_rows()
    for row in rows:
        if previously_used(row):
            row["metadata_status"] = "excluded"
            row["exclusions"] = "|".join(
                filter(None, (row["exclusions"], "previously_inspected_speaker"))
            )
        if row["speaker_name"] == "Assassas77":
            row["native_status_evidence"] = "https://commons.wikimedia.org/wiki/User:Assassas77"
            # French native / intermediate Chinese is supporting evidence only;
            # it does not expressly establish Mandarin acquisition history.
            row["speaker_native_status"] = "UNKNOWN"
    selected = choose(rows)
    if selected:
        raise RuntimeError(
            "New metadata coverage found: separate audio/provenance audit required before seal"
        )
    groups = defaultdict(list)
    for row in rows:
        groups[row["speaker_name"]].append(row)
    inventory_groups = defaultdict(list)
    for page in inventory:
        if not page["title"].startswith("File:LL-"):
            continue
        artist = page["imageinfo"][0]["extmetadata"].get("Artist", {}).get("value", "")
        plain = " ".join(html.unescape(re.sub(r"<[^>]+>", " ", artist)).split())
        match = re.search(r"Speaker: (.*?) Recorder:", plain)
        if match:
            inventory_groups[match[1]].append(page)
    summaries = []
    for name in sorted(set(groups) | set(inventory_groups)):
        items = groups[name]
        pages = inventory_groups[name]
        eligible = [r for r in items if r["metadata_status"] == "eligible"]
        counts = Counter(str(r["tone"]) for r in eligible)
        old = name_key(name) in PRIOR_NAMES or any(previously_used(r) for r in items)
        reasons = (
            "previously_inspected_speaker"
            if old
            else (
                "insufficient_per_tone_coverage"
                if eligible
                else "no_audited_eligible_isolated_target"
            )
        )
        if not items:
            reasons = "inventory_only_no_unqualified_single_character_candidate_in_cached_audit"
        ids = sorted({r["speaker_id"] for r in items if r["speaker_id"]})
        summaries.append(
            dict(
                speaker_name=name or "unresolved",
                speaker_id="|".join(ids),
                prior_inspected=old,
                inventory_items=len(pages) if pages else len(items),
                audited_items=len(items),
                native_status="NATIVE" if name.startswith("SPEAKER01") else "UNKNOWN",
                native_status_evidence="|".join(
                    sorted(
                        {r["native_status_evidence"] for r in items if r["native_status_evidence"]}
                    )
                ),
                accepted_item_licenses="|".join(
                    sorted({r["license"] for r in items if r["license"]})
                ),
                inventory_license_short_names="|".join(
                    sorted(
                        {
                            p["imageinfo"][0]["extmetadata"]
                            .get("LicenseShortName", {})
                            .get("value", "")
                            for p in pages
                        }
                    )
                ),
                source_url=items[0]["source_url"]
                if items
                else pages[0]["imageinfo"][0]["descriptionurl"],
                t1=counts["1"],
                t2=counts["2"],
                t3=counts["3"],
                t4=counts["4"],
                count_basis=(
                    "eligible audited isolated lexical targets; "
                    "zero does not describe unaudited speech"
                ),
                selected_items=0,
                exclusion=reasons,
            )
        )
    immutable_write(OUT / "candidate-items.csv", csv_bytes(rows))
    write_csv(OUT / "candidate-speakers.csv", summaries, list(summaries[0]))
    excluded = []
    for row in rows:
        excluded.append(
            dict(
                source_asset_id=row["source_asset_id"],
                speaker_name=row["speaker_name"],
                source_url=row["source_url"],
                revision_id=row["revision_id"],
                reason=row["exclusions"] or "insufficient_per_tone_coverage",
            )
        )
    write_csv(OUT / "exclusions.csv", excluded, list(excluded[0]))
    report = dict(
        inventory_pages=len(inventory),
        revision_audits=len(evidence),
        audited_items=len(rows),
        new_eligible_items=sum(r["metadata_status"] == "eligible" for r in rows),
        selected_items=0,
        sealed=False,
        reason="no three qualifying independent new speakers",
        selection_depends_on_predictions=False,
        audio_downloaded=0,
        source_snapshot="2026-09-28",
        inputs_sha256={str(p): digest(p) for p in inputs},
        artifacts_sha256={
            n: digest(OUT / n)
            for n in ("candidate-items.csv", "candidate-speakers.csv", "exclusions.csv")
        },
    )
    with (OUT / "source-audit.json").open("x") as handle:
        json.dump(report, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print(json.dumps({k: v for k, v in report.items() if not k.endswith("sha256")}, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    audit()
