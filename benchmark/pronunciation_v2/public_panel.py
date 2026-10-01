"""Experiment 3 public-data audit/acquisition. No model or feature imports.

SAIT-EMA 17506802 only; run with services/api/.venv/bin/python.
Network stages use bounded HTTP Range requests, never whole speaker archives.
"""

import argparse
import csv
import hashlib
import importlib.metadata
import io
import json
import re
import struct
import subprocess
import urllib.request
import zipfile
import zlib
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from pathlib import Path

from evaluation_preflight import check_no_staged_audio, digest, immutable_write, name_key
from nonlinear_sources import PRIOR_IDS, PRIOR_NAMES
from pilot import diagnostics, dictionary_reading, parse_pinyin

ROOT = Path(__file__).resolve().parents[2]
AUDIT = ROOT / "docs/research/pronunciation-v2/2026-10-01-experiment-3-discovery"
CACHE = ROOT / "benchmark/corpus/recordings/original/experiment-3-discovery"
EVIDENCE = CACHE / "evidence"
FROZEN = ROOT / "docs/research/pronunciation-v2/2026-10-01-experiment-3-preflight"
OUT = ROOT / "docs/research/pronunciation-v2/2026-10-01-experiment-3-data"
RECORD = "https://zenodo.org/records/17506802"
PAPER = "https://www.nature.com/articles/s41597-026-07237-9"
LICENSE = "https://creativecommons.org/licenses/by/4.0/"
EXPECTED_SPEAKERS = frozenset(
    ["A_F001", "A_M001"]
    + [f"{gender}{n:03}" for gender in ("F", "M") for n in range(1, 6)]
    + [f"L_{gender}{n:03}" for gender in ("F", "M") for n in range(1, 4)]
)
SELECTION = (
    "deduplicate source bytes globally and text within speaker; all speakers with >=8 "
    "unique targets in every T1-T4 cell; rank by SHA256(source_asset_id UTF-8), then ID; "
    "take at most 10 per cell; >=3 speakers; no predictions"
)
REQUIRED = (
    "source_asset_id",
    "speaker_id",
    "speaker_name",
    "speaker_identity_evidence",
    "source_url",
    "audio_url",
    "revision_id",
    "text",
    "pinyin",
    "tone",
    "label_source",
    "license",
    "license_url",
    "license_evidence_url",
    "attribution",
    "archive_member",
    "archive_md5",
    "speaker_native_status",
    "native_status_evidence",
)


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode()


def csv_data(rows, fields=None):
    rows = list(rows)
    fields = fields or sorted(set().union(*(r.keys() for r in rows)))
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode()


def csv_rows(path):
    with path.open(newline="") as handle:
        return list(csv.DictReader(handle))


def manifest_bytes(rows):
    return csv_data(
        sorted(
            rows,
            key=lambda r: (
                r["speaker_id"],
                int(r["tone"]),
                hashlib.sha256(r["source_asset_id"].encode()).hexdigest(),
                r["source_asset_id"],
            ),
        )
    )


def mono16_pcm(path):
    pcm = subprocess.check_output(
        [
            "ffmpeg",
            "-v",
            "error",
            "-i",
            str(path),
            "-map",
            "0:a:0",
            "-ac",
            "1",
            "-ar",
            "16000",
            "-f",
            "f32le",
            "-acodec",
            "pcm_f32le",
            "-",
        ],
        timeout=30,
    )
    if len(pcm) < 400 * 4 or len(pcm) % 4:
        raise ValueError("Invalid or too short evaluation PCM")
    return pcm


def frozen_check():
    expected = {
        "head-linear.npz": "d3f1cbe4a6ac7ea7c76b4538805d57cf99a36dd7d14909432725d4bc5cf696c2",
        "head-nonlinear.npz": "eb2c29fb7473faac715b93cdb1671134d7c408dc87065166b77e50d630efd28d",
        "protocol.lock.json": "f795f15d970043d65592ac9ef7cd3ee4af9b36bf2310de23a840bcf12db08721",
    }
    for filename, sha in expected.items():
        if digest(FROZEN / filename) != sha:
            raise ValueError(f"Frozen bytes changed: {filename}")
    lock = json.loads((FROZEN / "heads.lock.json").read_text())
    if lock["evaluation_predictions_opened"] is not False:
        raise ValueError("Predictions already opened")
    if lock["nonlinear_arrays_sha256"] != (
        "d3961629af0f7f91005c60911ea408a3fe1d149db2cc986df231765f35170659"
    ):
        raise ValueError("Array receipt changed")
    if importlib.metadata.version("pypinyin") != "0.55.0":
        raise ValueError("Requires pypinyin 0.55.0")
    return expected


def range_get(url, start, end, total):
    """Refuse ignored/mismatched ranges before reading a potentially huge body."""
    if not 0 <= start <= end < total or end - start >= 2_000_000:
        raise ValueError("Range bound exceeded")
    request = urllib.request.Request(url, headers={"Range": f"bytes={start}-{end}"})
    with urllib.request.urlopen(request, timeout=40) as response:
        if response.status != 206 or response.headers.get("Content-Range") != (
            f"bytes {start}-{end}/{total}"
        ):
            raise ValueError("Server ignored or changed range; no body read")
        data = response.read(end - start + 2)
        if len(data) != end - start + 1:
            raise ValueError(
                f"Incomplete or oversized range: {url} {start}-{end}; "
                f"expected {end - start + 1}, received {len(data)}"
            )
        receipt = dict(
            url=url,
            start=start,
            end=end,
            total=total,
            bytes=len(data),
            sha256=hashlib.sha256(data).hexdigest(),
            status=response.status,
            etag=response.headers.get("ETag", ""),
            retrieved_at=datetime.now(UTC).isoformat(),
        )
    return data, receipt


def central_location(tail, total):
    offset = tail.rfind(b"PK\x05\x06")
    if offset < 0:
        raise ValueError("Missing ZIP end record")
    end = tail[offset:]
    _sig, disk, cd_disk, n_disk, n, size, start, comment = struct.unpack("<4s4H2LH", end[:22])
    if disk or cd_disk or n_disk != n or n == 65535 or len(end) != 22 + comment:
        raise ValueError("Unsupported split/ZIP64/comment structure")
    if start + size != total - len(end) or size > 2_000_000:
        raise ValueError("Unexpected central directory bounds")
    return start, size, end


def parse_central(central, end):
    # Virtual archive consisting only of its directory. Local header offsets stay
    # absolute, while the directory itself starts at zero in this small object.
    patched = bytearray(end)
    struct.pack_into("<L", patched, 16, 0)
    with zipfile.ZipFile(io.BytesIO(central + patched)) as archive:
        entries = []
        for info in archive.infolist():
            if info.flag_bits & 1 or info.compress_type not in (0, 8):
                raise ValueError("Encrypted/unsupported ZIP entry")
            entries.append(
                dict(
                    name=info.filename,
                    size=info.file_size,
                    compressed_size=info.compress_size,
                    offset=info.header_offset,
                    crc32=info.CRC,
                    method=info.compress_type,
                )
            )
    if len({e["name"] for e in entries}) != len(entries):
        raise ValueError("Duplicate ZIP member name")
    return sorted(entries, key=lambda e: e["name"])


def speaker_archives():
    record = json.loads((EVIDENCE / "sait-zenodo").read_text())
    if record["metadata"]["license"]["id"] != "cc-by-4.0":
        raise ValueError("Dataset license changed")
    return sorted(
        (f for f in record["files"] if re.fullmatch(r"(?:A_|L_)?[FM]\d{3}\.zip", f["key"])),
        key=lambda f: f["key"],
    )


def index_archives():
    frozen_check()
    directory = CACHE / "indexes"
    directory.mkdir(exist_ok=True)
    for source in speaker_archives():
        name = source["key"].removesuffix(".zip")
        path = directory / f"{name}.json"
        if path.exists():
            continue
        url, total = source["links"]["self"], source["size"]
        tail, receipt1 = range_get(url, total - 65557, total - 1, total)
        start, length, end = central_location(tail, total)
        central, receipt2 = range_get(url, start, start + length - 1, total)
        entries = parse_central(central, end)
        immutable_write(
            path,
            encoded(
                dict(
                    archive=source,
                    entries=entries,
                    receipts=[receipt1, receipt2],
                )
            ),
        )
        print(name, len(entries), "index entries", flush=True)


def prompts():
    with zipfile.ZipFile(EVIDENCE / "sait-materials") as archive:
        lines = archive.read("speech_materials.txt").decode("utf-16").splitlines()
    result = []
    for line in lines:
        index, content = line.split("\t", 1)
        parts = content.split()
        text = parts[0] if len(parts) >= 2 else ""
        source_pinyin = parts[1] if len(parts) == 2 else ""
        reading, reason = dictionary_reading(text)
        if not reason and parse_pinyin(source_pinyin) != reading:
            reason = "source_dictionary_conflict"
        result.append(
            dict(
                file_id=index,
                exact_prompt=content,
                text=text,
                source_pinyin=source_pinyin,
                pinyin=reading[0] if reading and not reason else "",
                tone=str(reading[1]) if reading and not reason else "",
                exclusions=reason or "",
            )
        )
    if len(result) != 962 or len({r["file_id"] for r in result}) != 962:
        raise ValueError("Unexpected prompt enumeration")
    return result


def word_transcript(data):
    """Read corpus word-tier text only; never use or crop by alignment boundaries."""
    text = data.decode("utf-16" if data.startswith((b"\xff\xfe", b"\xfe\xff")) else "utf-8-sig")
    parts = re.split(r"\n\s*item \[\d+\]:", text)
    tiers = [p for p in parts if re.search(r'name = "(?:word|words)"', p)]
    if len(tiers) != 1:
        raise ValueError("Missing/ambiguous word tier")
    tokens = re.findall(r'text = "((?:[^"]|"")*)"', tiers[0])
    return [t.replace('""', '"') for t in tokens if t.strip()]


def enumerate_candidates():
    rows = []
    with zipfile.ZipFile(EVIDENCE / "sait-textgrids") as grids:
        grid_names = set(grids.namelist())
        for source in speaker_archives():
            speaker = source["key"].removesuffix(".zip")
            index = json.loads((CACHE / "indexes" / f"{speaker}.json").read_text())
            entries = {e["name"]: e for e in index["entries"]}
            wav_by_id = defaultdict(list)
            for name in entries:
                match = re.search(r"/wav/(\d{4})\.wav$", name)
                if match:
                    wav_by_id[match[1]].append(name)
            for prompt in prompts():
                file_id = prompt["file_id"]
                matches = wav_by_id[file_id]
                grid_name = f"TextGrids/{speaker}/{file_id}.TextGrid"
                grid_matches = [grid_name] if grid_name in grid_names else []
                reason = prompt["exclusions"]
                if len(matches) != 1:
                    reason = reason or "missing_or_ambiguous_audio_member"
                if not reason:
                    if len(grid_matches) != 1:
                        reason = "missing_or_ambiguous_transcript"
                    elif word_transcript(grids.read(grid_matches[0])) not in (
                        [prompt["text"]],
                        [prompt["pinyin"]],
                    ):
                        reason = "corpus_transcript_conflict"
                member = matches[0] if len(matches) == 1 else ""
                row = dict(
                    **prompt,
                    source="SAIT-EMA",
                    speaker_id=f"sait-ema:{speaker}",
                    speaker_name=speaker,
                    speaker_identity_evidence=RECORD + "/files/README.txt",
                    speaker_native_status="LEARNER" if speaker.startswith("L_") else "NATIVE",
                    native_status_evidence=PAPER,
                    source_asset_id=f"zenodo:17506802:{member or speaker + '/' + file_id}",
                    source_url=RECORD,
                    audio_url=source["links"]["self"],
                    revision_id="17506802",
                    archive_member=member,
                    archive_md5=source["checksum"],
                    archive_size=source["size"],
                    archive_key=source["key"],
                    archive_crc32=entries[member]["crc32"] if member else "",
                    source_bytes=entries[member]["size"] if member else "",
                    license="CC BY 4.0",
                    license_url=LICENSE,
                    license_evidence_url=RECORD + "/files/README.txt",
                    attribution=f"Jia, Xie, Fang and Sun; SAIT-EMA; {RECORD}; {LICENSE}; "
                    "distributed WAV unchanged; evaluation decode only",
                    label_source="pypinyin 0.55.0 heteronym=True singleton TONE3 neutral=5; "
                    "source prompt and corpus word-tier cross-check",
                    transcript_member=grid_matches[0] if len(grid_matches) == 1 else "",
                    metadata_status="excluded" if reason else "eligible",
                )
                row["exclusions"] = reason
                rows.append(row)
    return sorted(rows, key=lambda r: r["source_asset_id"])


def blocked(row, previous=()):
    ids = PRIOR_IDS | {r.get("speaker_id", "") for r in previous}
    names = PRIOR_NAMES | {name_key(r.get("speaker_name", "")) for r in previous}
    return row["speaker_id"] in ids or name_key(row["speaker_name"]) in names


def pool(rows, previous=()):
    cells = defaultdict(list)
    ids, texts, hashes = set(), set(), set()
    for row in sorted(rows, key=lambda r: r["source_asset_id"]):
        if row["source_asset_id"] in ids:
            raise ValueError("Duplicate source ID")
        ids.add(row["source_asset_id"])
        if row["metadata_status"] != "eligible" or blocked(row, previous):
            continue
        if any(not row.get(k) for k in REQUIRED):
            raise ValueError("Missing required provenance/license")
        if str(row["tone"]) not in {"1", "2", "3", "4"}:
            raise ValueError("Only T1-T4")
        reading, reason = dictionary_reading(row["text"])
        if reason or reading != (row["pinyin"], int(row["tone"])):
            raise ValueError("Not a singleton lexical reading")
        key = row["speaker_id"], row["text"]
        sha = row.get("audio_sha256")
        if key in texts or (sha and sha in hashes):
            continue
        texts.add(key)
        if sha:
            hashes.add(sha)
        cells[row["speaker_id"], str(row["tone"])].append(row)
    return cells


def choose(rows, previous=()):
    cells = pool(rows, previous)
    speakers = sorted({s for s, _ in cells if all(len(cells[s, str(t)]) >= 8 for t in range(1, 5))})
    if len(speakers) < 3:
        return []
    return [
        r
        for s in speakers
        for t in range(1, 5)
        for r in sorted(
            cells[s, str(t)],
            key=lambda r: (
                hashlib.sha256(r["source_asset_id"].encode()).hexdigest(),
                r["source_asset_id"],
            ),
        )[:10]
    ]


def prepare():
    frozen_check()
    rows = enumerate_candidates()
    # Unequal CRC32/size pairs prove unequal bytes. Equal pairs are NOT proof of
    # duplication: fail closed for a separate byte-level audit before selection.
    byte_keys = [
        (r["archive_crc32"], r["source_bytes"]) for r in rows if r["metadata_status"] == "eligible"
    ]
    if len(set(byte_keys)) != len(byte_keys):
        raise ValueError("CRC/size collisions require byte-level dedup before selection")
    selected = choose(rows)
    cells = pool(rows)
    summaries = []
    for source in speaker_archives():
        speaker = "sait-ema:" + source["key"].removesuffix(".zip")
        summaries.append(
            dict(
                speaker_id=speaker,
                **{f"t{t}": len(cells[speaker, str(t)]) for t in range(1, 5)},
                count_basis="unique lexical targets with existing WAV and matching word-tier; "
                "distinct CRC32/size pairs exclude identical source bytes",
                selected=sum(r["speaker_id"] == speaker for r in selected),
            )
        )
    immutable_write(AUDIT / "candidate-items.csv", csv_data(rows))
    immutable_write(AUDIT / "candidate-speakers.csv", csv_data(summaries))
    immutable_write(
        AUDIT / "exclusions.csv",
        csv_data(
            [r for r in rows if r["exclusions"]],
            sorted(rows[0]),
        ),
    )
    immutable_write(
        AUDIT / "selection.json",
        encoded(
            dict(
                created_at=datetime.now(UTC).isoformat(),
                rule=SELECTION,
                candidate_items_sha256=digest(AUDIT / "candidate-items.csv"),
                source_bytes_distinct_by_zip_crc32_and_size=True,
                selected_ids=[r["source_asset_id"] for r in selected],
                metadata_inputs_sha256={
                    str(p.relative_to(ROOT)): digest(p)
                    for p in (
                        EVIDENCE / "sait-materials",
                        EVIDENCE / "sait-textgrids",
                        EVIDENCE / "sait-zenodo",
                        EVIDENCE / "sait-documentation",
                        *sorted((CACHE / "indexes").glob("*.json")),
                    )
                },
            )
        ),
    )
    print(json.dumps(summaries, indent=2))
    print("Selected before audio acquisition:", len(selected))


def selected_rows():
    lock = json.loads((AUDIT / "selection.json").read_text())
    if digest(AUDIT / "candidate-items.csv") != lock["candidate_items_sha256"]:
        raise ValueError("Candidate metadata changed after selection")
    for path, sha in lock["metadata_inputs_sha256"].items():
        if digest(ROOT / path) != sha:
            raise ValueError("Source metadata changed after selection")
    rows = choose(csv_rows(AUDIT / "candidate-items.csv"))
    if [r["source_asset_id"] for r in rows] != lock["selected_ids"] or not rows:
        raise ValueError("Selection changed or insufficient coverage")
    return rows


def extract_member(block, entry):
    if block[:4] != b"PK\x03\x04" or len(block) < 30:
        raise ValueError("Missing local ZIP header")
    values = struct.unpack("<4s5H3L2H", block[:30])
    flags, method, name_len, extra_len = values[2], values[3], values[-2], values[-1]
    name = block[30 : 30 + name_len].decode("utf-8" if flags & 2048 else "cp437")
    if name != entry["name"] or method != entry["method"] or flags & 1:
        raise ValueError("Local ZIP header mismatch")
    start = 30 + name_len + extra_len
    compressed = block[start : start + entry["compressed_size"]]
    if len(compressed) != entry["compressed_size"] or entry["size"] > 2_000_000:
        raise ValueError("ZIP size bound or truncated member")
    if method == 8:
        decoder = zlib.decompressobj(-15)
        data = decoder.decompress(compressed, entry["size"] + 1)
        if not decoder.eof or decoder.unused_data or decoder.unconsumed_tail:
            raise ValueError("Invalid/bomb compressed member")
    else:
        data = compressed
    if len(data) != entry["size"] or zlib.crc32(data) != entry["crc32"]:
        raise ValueError("ZIP member size/CRC verification failed")
    return data


def acquire_one(row):
    speaker = row["speaker_name"]
    destination = CACHE / "audio" / speaker / (row["file_id"] + ".wav")
    receipt_path = destination.with_suffix(".json")
    if receipt_path.exists():
        receipt = json.loads(receipt_path.read_text())
        if digest(destination) != receipt["audio_sha256"]:
            raise ValueError("Cached audio changed")
        return receipt
    index = json.loads((CACHE / "indexes" / f"{speaker}.json").read_text())
    entry = next(e for e in index["entries"] if e["name"] == row["archive_member"])
    # At most 1024 adjacent archive bytes permit one request for local header and
    # payload. Only the exact selected WAV is extracted; no sentence cropping.
    block, network = range_get(
        row["audio_url"],
        entry["offset"],
        min(entry["offset"] + entry["compressed_size"] + 1023, int(row["archive_size"]) - 1),
        int(row["archive_size"]),
    )
    data = extract_member(block, entry)
    destination.parent.mkdir(parents=True, exist_ok=True)
    immutable_write(destination, data)
    info = diagnostics(destination)
    # Established encoder preprocessing without importing/using the encoder.
    pcm = subprocess.check_output(
        [
            "ffmpeg",
            "-v",
            "error",
            "-i",
            str(destination),
            "-ac",
            "1",
            "-ar",
            "16000",
            "-f",
            "f32le",
            "-acodec",
            "pcm_f32le",
            "-",
        ],
        timeout=30,
    )
    if not pcm:
        raise ValueError("Empty evaluation PCM")
    receipt = dict(
        source_asset_id=row["source_asset_id"],
        local_path=str(destination.relative_to(ROOT)),
        source_sha256=hashlib.sha256(data).hexdigest(),
        audio_sha256=hashlib.sha256(data).hexdigest(),
        source_sha1=hashlib.sha1(data).hexdigest(),
        decoded_pcm_sha256=info["decoded_pcm_sha256"],
        evaluation_pcm_sha256=hashlib.sha256(pcm).hexdigest(),
        duration_seconds=info["duration_seconds"],
        sample_rate_hz=info["sample_rate_hz"],
        channels=info["channels"],
        decode_success=info["decode_success"],
        network=network,
        zip_entry=entry,
    )
    immutable_write(receipt_path, encoded(receipt))
    return receipt


def acquire():
    frozen_check()
    if (OUT / "seal.json").exists():
        raise FileExistsError("Already sealed")
    rows = selected_rows()
    # Sequential requests respect the source; receipts permit exact resume but no
    # substitute items or automatic retry of a rejected/throttled request.
    for number, row in enumerate(rows, 1):
        acquire_one(row)
        if number % 10 == 0:
            print(f"Verified {number}/{len(rows)} selected WAVs", flush=True)


def historical_metadata():
    research = ROOT / "docs/research/pronunciation-v2"
    names = {
        "clean-corpus-manifest.csv",
        "split-manifest.csv",
        "sealed-test-manifest.csv",
        "candidate-items.csv",
        "candidate-audit.csv",
        "eligible-metadata.csv",
        "pilot-manifest.jsonl",
        "training-manifest.csv",
        "inventory-duplicates.jsonl",
    }
    paths = sorted(
        p
        for p in research.rglob("*")
        if p.name in names and AUDIT not in p.parents and OUT not in p.parents
    )
    rows = []
    for path in paths:
        if path.suffix == ".csv":
            rows.extend(csv_rows(path))
        else:
            rows.extend(json.loads(line) for line in path.read_text().splitlines())
    corpus = ROOT / "benchmark/corpus/manifests/benma-v0.1.0.json"
    rows.extend(json.loads(corpus.read_text())["samples"])
    paths.append(corpus)
    return rows, paths


def history():
    """Inventory all local historical audio, including OMPAL and the opened 118."""
    frozen_check()
    rows, paths = historical_metadata()
    roots = [ROOT / "benchmark/corpus/recordings", Path.home() / ".cache/benma"]
    extensions = {".wav", ".flac", ".ogg", ".opus", ".mp3", ".m4a"}
    files = {
        p.resolve()
        for root in roots
        for p in root.rglob("*")
        if p.suffix.lower() in extensions and CACHE not in p.parents
    }
    for row in rows:
        path = row.get("local_path")
        if path:
            path = Path(path) if Path(path).is_absolute() else ROOT / path
            if path.exists() and path.is_file():
                files.add(path.resolve())

    def inspect(path):
        data = path.read_bytes()
        return dict(
            local_path=str(path),
            audio_sha256=hashlib.sha256(data).hexdigest(),
            source_sha1=hashlib.sha1(data).hexdigest(),
            decoded_pcm_sha256=diagnostics(path)["decoded_pcm_sha256"],
        )

    with ThreadPoolExecutor(max_workers=4) as executor:
        audio = list(executor.map(inspect, sorted(files)))
    immutable_write(
        AUDIT / "historical-overlap-index.json",
        encoded(
            dict(
                metadata_inputs_sha256={str(p.relative_to(ROOT)): digest(p) for p in paths},
                audio=audio,
                roots=[str(p) for p in roots],
                metadata_rows=len(rows),
                audio_files=len(audio),
                note="All local historical audio decoded; "
                "metadata retains remote source IDs/hashes. "
                "Exact hashes cannot prove absence of transformed copies or biological aliases.",
            )
        ),
    )
    print("Historical metadata rows:", len(rows), "redecoded historical files:", len(audio))


def validate_final(rows, previous):
    cells = Counter()
    seen = defaultdict(set)
    keys = (
        "source_asset_id",
        "audio_sha256",
        "source_sha1",
        "decoded_pcm_sha256",
        "evaluation_pcm_sha256",
    )
    old = {k: {r[k] for r in previous if r.get(k)} for k in keys}
    for row in rows:
        if blocked(row, previous):
            raise ValueError("Historical speaker overlap")
        if any(not row.get(k) for k in (*REQUIRED, *keys, "source_sha256", "local_path")):
            raise ValueError("Missing required provenance/license/hash")
        if row["license"] != "CC BY 4.0" or row["license_url"] != LICENSE:
            raise ValueError("Unaudited audio license")
        reading, reason = dictionary_reading(row["text"])
        if reason or reading != (row["pinyin"], int(row["tone"])):
            raise ValueError("Only singleton lexical T1-T4")
        if row["metadata_status"] != "eligible" or row["exclusions"]:
            raise ValueError("Excluded candidate")
        for key in keys:
            if row[key] in old[key] or row[key] in seen[key]:
                raise ValueError(f"Duplicate/overlap {key}")
            seen[key].add(row[key])
        target = row["speaker_id"], row["text"]
        if target in seen["target"]:
            raise ValueError("Duplicate speaker target")
        seen["target"].add(target)
        cells[row["speaker_id"], str(row["tone"])] += 1
    speakers = {s for s, _ in cells}
    if len(speakers) < 3 or any(
        not 8 <= cells[s, str(t)] <= 10 for s in speakers for t in range(1, 5)
    ):
        raise ValueError("Minimum three speakers and 8-10 per tone")


def normalized_history():
    """Extend the verified 700-file audit; preserve the existing native-PCM index."""
    frozen_check()
    prior = AUDIT / "historical-overlap-index.json"
    historical = json.loads(prior.read_text())

    def inspect(row):
        path = Path(row["local_path"])
        if digest(path) != row["audio_sha256"]:
            raise ValueError("Historical source bytes changed")
        return {**row, "evaluation_pcm_sha256": hashlib.sha256(mono16_pcm(path)).hexdigest()}

    with ThreadPoolExecutor(max_workers=4) as executor:
        rows = list(executor.map(inspect, historical["audio"]))
    immutable_write(
        AUDIT / "historical-mono16k-index.json",
        encoded(
            dict(
                parent_index_sha256=digest(prior),
                audio=rows,
                audio_files=len(rows),
                decoded_format="whole mono 16000 Hz f32le, "
                "matching features.py load_waveform; no model",
            )
        ),
    )
    print("Historical mono-16k PCM hashes:", len(rows))


def validate_composition(rows):
    if len(rows) != 720 or {r["speaker_name"] for r in rows} != EXPECTED_SPEAKERS:
        raise ValueError("Expected exact 720 rows and 18 preselected speakers")
    counts = Counter((r["speaker_name"], str(r["tone"])) for r in rows)
    if any(counts[s, str(t)] != 10 for s in EXPECTED_SPEAKERS for t in range(1, 5)):
        raise ValueError("Expected exactly 10 per tone per speaker")
    for row in rows:
        status = "LEARNER" if row["speaker_name"].startswith("L_") else "NATIVE"
        if row["speaker_native_status"] != status:
            raise ValueError("Source-declared status changed")


def exclusive_seal(directory, artifacts, seal):
    """Refuse every pre-existing finalization; failed partial writes need review."""
    if directory.exists():
        raise FileExistsError("Refusing to overwrite a panel directory")
    directory.mkdir()
    for name, data in artifacts.items():
        with (directory / name).open("xb") as handle:
            handle.write(data)
    with (directory / "seal.json").open("xb") as handle:
        handle.write(encoded(seal))


def seal():
    frozen = frozen_check()
    if OUT.exists():
        raise FileExistsError("Panel directory already exists")
    selected = selected_rows()
    previous, history_paths = historical_metadata()
    historical = json.loads((AUDIT / "historical-overlap-index.json").read_text())
    normalized = json.loads((AUDIT / "historical-mono16k-index.json").read_text())
    if normalized["parent_index_sha256"] != digest(AUDIT / "historical-overlap-index.json"):
        raise ValueError("Historical parent index changed")
    for path in history_paths:
        if historical["metadata_inputs_sha256"][str(path.relative_to(ROOT))] != digest(path):
            raise ValueError("Historical metadata changed after overlap indexing")
    for row in historical["audio"]:
        if digest(row["local_path"]) != row["audio_sha256"]:
            raise ValueError("Historical audio changed after decode")
    previous.extend(normalized["audio"])
    final, evidence = [], []
    for row in selected:
        path = CACHE / "audio" / row["speaker_name"] / (row["file_id"] + ".json")
        receipt = json.loads(path.read_text())
        if receipt["source_asset_id"] != row["source_asset_id"]:
            raise ValueError("Acquisition identity differs")
        audio = ROOT / receipt["local_path"]
        if digest(audio) != receipt["audio_sha256"] or receipt["source_sha256"] != digest(audio):
            raise ValueError("Source audio bytes changed")
        if zlib.crc32(audio.read_bytes()) != int(row["archive_crc32"]):
            raise ValueError("Source CRC changed")
        info = diagnostics(audio)
        for key in ("decoded_pcm_sha256", "sample_rate_hz", "channels", "duration_seconds"):
            if info[key] != receipt[key]:
                raise ValueError(f"Re-decoded {key} changed")
        pcm = mono16_pcm(audio)
        if hashlib.sha256(pcm).hexdigest() != receipt["evaluation_pcm_sha256"]:
            raise ValueError("Evaluation preprocessing changed")
        final.append(
            {**row, **{k: v for k, v in receipt.items() if k not in {"network", "zip_entry"}}}
        )
        evidence.append(
            dict(candidate=row, acquisition=receipt, acquisition_receipt_sha256=digest(path))
        )
    validate_final(final, previous)
    validate_composition(final)
    check_no_staged_audio()
    manifest = manifest_bytes(final)
    acquired_evidence = b"".join(
        (json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n").encode() for r in evidence
    )
    # Finish review, source audit, environment and validation before this command.
    copied = (
        "review.md",
        "sources.md",
        "candidate-sources.csv",
        "candidate-speakers.csv",
        "candidate-items.csv",
        "exclusions.csv",
        "selection.json",
        "environment.md",
        "retrieval-receipts.jsonl",
        "historical-overlap-index.json",
        "historical-mono16k-index.json",
        "validation.json",
        "search-log.md",
        "promising-source-counts.csv",
        "web-evidence.jsonl",
    )
    artifacts = {name: (AUDIT / name).read_bytes() for name in copied}
    artifacts.update(
        {
            "sealed-test-manifest.csv": manifest,
            "selected-source-evidence.jsonl": acquired_evidence,
        }
    )
    code_paths = [Path(__file__), Path(__file__).with_name("test_public_panel.py")]
    provenance = dict(
        created_at=datetime.now(UTC).isoformat(),
        git_head=subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        branch="pronunciation-v2-research",
        selection_rule=SELECTION,
        artifacts_sha256={k: hashlib.sha256(v).hexdigest() for k, v in artifacts.items()},
        code_sha256={str(p.relative_to(ROOT)): digest(p) for p in code_paths},
        frozen_sha256=frozen,
        heads_lock_sha256=digest(FROZEN / "heads.lock.json"),
        nonlinear_arrays_sha256_from_frozen_receipt=(
            "d3961629af0f7f91005c60911ea408a3fe1d149db2cc986df231765f35170659"
        ),
        source_inputs_sha256=json.loads((AUDIT / "selection.json").read_text())[
            "metadata_inputs_sha256"
        ],
        all_retrieved_evidence_sha256={
            str(p.relative_to(ROOT)): digest(p) for p in sorted(EVIDENCE.iterdir()) if p.is_file()
        },
        no_model_or_encoder_access=True,
        evaluation_predictions_opened=False,
        no_audio_listening_or_f0_labeling=True,
        no_production_changes=True,
        source_bytes_sha256_scope="exact distributed WAV member bytes; full ZIP MD5 not verified",
        decoded_pcm_sha256_scope="SHA256(rate:channels:f32le: prefix + native decoded PCM)",
        evaluation_pcm_sha256_scope="SHA256(whole mono 16kHz f32le PCM); no encoder normalization",
        historical_metadata_rows=historical["metadata_rows"],
        historical_audio_files=historical["audio_files"],
        limitations=[
            "Stable corpus speaker IDs establish no known overlap, not biological uniqueness.",
            "Exact hashes cannot detect every transformed duplicate.",
            "Source transcript labels are lexical truth, not a certification of realized tone.",
            "Twelve source-declared native controls and six source-declared learners are included.",
            "Archive CRC/size inequality proves distinct candidate bytes; "
            "selected WAVs also SHA-256 verified.",
            "Metadata discovery used no expected model difficulty, predictions, F0 or listening.",
        ],
    )
    artifacts["provenance.json"] = encoded(provenance)
    counts = {
        s: {
            str(t): sum(r["speaker_id"] == s and r["tone"] == str(t) for r in final)
            for t in range(1, 5)
        }
        for s in sorted({r["speaker_id"] for r in final})
    }
    receipt = dict(
        status="SEALED_UNOPENED",
        sealed_at=datetime.now(UTC).isoformat(),
        rows=len(final),
        speaker_count=len(counts),
        tone_counts={str(t): sum(r["tone"] == str(t) for r in final) for t in range(1, 5)},
        speaker_status_counts={
            "source_declared_native_controls": 12,
            "source_declared_learners": 6,
        },
        speaker_status_clip_counts={
            "source_declared_native_controls": 480,
            "source_declared_learners": 240,
        },
        manifest_sha256=hashlib.sha256(manifest).hexdigest(),
        speakers=counts,
        artifacts_sha256={k: hashlib.sha256(v).hexdigest() for k, v in artifacts.items()},
        selection_rule=SELECTION,
        selection_rule_sha256=hashlib.sha256(SELECTION.encode()).hexdigest(),
        selection_lock_sha256=digest(AUDIT / "selection.json"),
        frozen_sha256=frozen,
        heads_lock_sha256=digest(FROZEN / "heads.lock.json"),
        model_access=False,
        embeddings_computed=False,
        evaluation_predictions_opened=False,
        raw_audio_staged=False,
    )
    exclusive_seal(OUT, artifacts, receipt)
    print(json.dumps(dict(rows=len(final), manifest_sha256=receipt["manifest_sha256"])))


def verify_seal():
    frozen_check()
    receipt = json.loads((OUT / "seal.json").read_text())
    for name, sha in receipt["artifacts_sha256"].items():
        if digest(OUT / name) != sha:
            raise ValueError(f"Sealed artifact changed: {name}")
    provenance = json.loads((OUT / "provenance.json").read_text())
    for path, sha in provenance["code_sha256"].items():
        if digest(ROOT / path) != sha:
            raise ValueError(f"Sealing code changed: {path}")
    rows = csv_rows(OUT / "sealed-test-manifest.csv")
    if manifest_bytes(rows) != (OUT / "sealed-test-manifest.csv").read_bytes():
        raise ValueError("Manifest canonical bytes differ")
    validate_composition(rows)
    for row in rows:
        if digest(ROOT / row["local_path"]) != row["audio_sha256"]:
            raise ValueError("Sealed local audio changed")
    if receipt["model_access"] or receipt["evaluation_predictions_opened"]:
        raise ValueError("Panel is no longer unopened")
    check_no_staged_audio()
    print(
        json.dumps(
            dict(
                status="VERIFIED_SEALED_UNOPENED",
                rows=len(rows),
                manifest_sha256=receipt["manifest_sha256"],
            )
        )
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "stage",
        choices=("index", "prepare", "acquire", "history", "history-mono16k", "seal", "verify"),
    )
    args = parser.parse_args()
    {
        "index": index_archives,
        "prepare": prepare,
        "acquire": acquire,
        "history": history,
        "history-mono16k": normalized_history,
        "seal": seal,
        "verify": verify_seal,
    }[args.stage]()


if __name__ == "__main__":
    main()
