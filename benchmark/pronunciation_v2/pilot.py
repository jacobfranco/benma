"""Conservative metadata selection, bounded downloads, and waveform diagnostics.

Run with the existing services/api/.venv Python (pypinyin 0.55.0, MIT).
This is an exploratory lexical-label manifest, never observed-tone gold.
"""

from __future__ import annotations

import argparse
import array
import collections
import hashlib
import html
import json
import math
import re
import subprocess
import sys
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from acquire import USER_AGENT, Client, pause, retry_seconds

MAX_FILES = 500
MAX_BYTES = 1024**3
ACCESS_DATE = "2026-09-28"
MARKS = {"\u0304": 1, "\u0301": 2, "\u030c": 3, "\u0300": 4}
HAN = re.compile(r"[\u3400-\u9fff]")
REQUIRED = [
    "source",
    "source_asset_id",
    "source_url",
    "local_path",
    "audio_sha256",
    "speaker_id",
    "speaker_native_status",
    "text",
    "pinyin",
    "tone",
    "syllable_count",
    "duration_seconds",
    "sample_rate_hz",
    "channels",
    "license",
    "license_url",
    "attribution",
    "commercial_use_status",
    "provenance_confidence",
    "label_source",
    "label_confidence",
    "notes",
]


def plain(value):
    return html.unescape(re.sub("<[^>]+>", "", value)).strip()


def normalize_text(value):
    return " ".join(unicodedata.normalize("NFC", value).split())


def parse_pinyin(value):
    """Parse ONE explicitly toned syllable; never interpret unmarked as T1."""
    value = normalize_text(value).lower().replace("u:", "ü").replace("v", "ü")
    if re.fullmatch(r"[a-zü]+[0-5]", value):
        tone = int(value[-1])
        return value[:-1] + str(tone), tone
    decomposed = unicodedata.normalize("NFD", value)
    marks = [MARKS[ch] for ch in decomposed if ch in MARKS]
    if len(marks) != 1:
        return None
    base = unicodedata.normalize("NFC", "".join(ch for ch in decomposed if ch not in MARKS))
    if not re.fullmatch(r"[a-zü]+", base):
        return None
    # One tone mark alone is insufficient for a phrase; callers require one Han character.
    return base + str(marks[0]), marks[0]


def dictionary_reading(text):
    from pypinyin import Style, pinyin

    if not HAN.fullmatch(text):
        return None, "multi_syllable"
    choices = sorted(
        set(
            pinyin(
                text,
                style=Style.TONE3,
                heteronym=True,
                neutral_tone_with_five=True,
                errors="default",
            )[0]
        )
    )
    if len(choices) != 1:
        return None, "ambiguous_reading"
    parsed = parse_pinyin(choices[0])
    if not parsed:
        return None, "unknown_pronunciation"
    if parsed[1] not in (1, 2, 3, 4):
        return None, "neutral_tone"
    return parsed, None


def wikitext(page):
    return page.get("revisions", [{}])[0].get("slots", {}).get("main", {}).get("*", "")


def field(wiki, name):
    match = re.search(r"^[ \t]*\|[ \t]*" + re.escape(name) + r"[ \t]*=[ \t]*([^\n]*)", wiki, re.M)
    return match.group(1).strip() if match else None


def license_policy(meta, wiki=""):
    """No category-level grants. Explicit optional CC0 requires the file's license block."""
    name = meta.get("LicenseShortName", {}).get("value", "")
    url = meta.get("LicenseUrl", {}).get("value", "")
    restrictions = plain(meta.get("Restrictions", {}).get("value", ""))
    if restrictions:
        return None, None, "license_restrictions"
    block = re.split(r"==\s*\{\{int:license-header\}\}\s*==", wiki, flags=re.I)
    if (
        len(block) == 2
        and re.search(r"\{\{cc-(?:0|zero)\s*\}\}", block[1], re.I)
        and ("{{Multi-license}}" in block[1] or not re.search(r"\{\{cc-by", block[1], re.I))
    ):
        return "CC0-1.0", "https://creativecommons.org/publicdomain/zero/1.0/", None
    if re.fullmatch(r"CC BY (?:2\.0|2\.5|3\.0|4\.0)(?: fr| uk)?", name):
        expected = "https://creativecommons.org/licenses/by/" + name[6:].replace(" ", "/")
        if url.rstrip("/").removesuffix("/deed.en").replace("http:", "https:") == expected:
            return name, url, None
        return None, None, "license_url_mismatch"
    if name in ("CC0", "CC0 1.0") and (
        url.rstrip("/").removesuffix("/deed.en").replace("http:", "https:")
        == "https://creativecommons.org/publicdomain/zero/1.0"
    ):
        return "CC0-1.0", url, None
    if "NC" in name:
        return None, None, "noncommercial"
    if "ND" in name:
        return None, None, "no_derivatives"
    if "SA" in name or "GFDL" in name:
        return None, None, "sharealike_deferred"
    return None, None, "unknown_license_or_pd_basis"


def preliminary(page):
    """Find single-character candidates before spending requests on revisions."""
    info = page.get("imageinfo", [{}])[0]
    meta = info.get("extmetadata", {})
    desc = plain(meta.get("ImageDescription", {}).get("value", ""))
    if page["title"].startswith("File:LL-"):
        match = re.match(
            r"^File:LL-(?:Q9192|Q727694) \(cmn\)-.+-([^\-]+)\.(?:wav|ogg|flac)$", page["title"]
        )
        return bool(match and HAN.fullmatch(match.group(1)))
    match = re.search(r'Pronunciation of "([^"]+)" \(([^)]+)\) in Chinese\.', desc)
    return bool(match and HAN.fullmatch(match.group(2)))


def normalize(page):
    info = page.get("imageinfo", [{}])[0]
    meta = info.get("extmetadata", {})
    wiki = wikitext(page)
    lic, lic_url, license_reject = license_policy(meta, wiki)
    desc = plain(meta.get("ImageDescription", {}).get("value", ""))
    artist = plain(meta.get("Artist", {}).get("value", ""))
    credit = plain(meta.get("Credit", {}).get("value", ""))
    ll = page["title"].startswith("File:LL-")
    record = dict.fromkeys(REQUIRED)
    record.update(
        source="lingua_libre_commons" if ll else "wikimedia_commons",
        source_asset_id="commons:" + str(page["pageid"]),
        source_url=info.get("descriptionurl"),
        title=page["title"],
        source_collection="Lingua Libre"
        if ll
        else ("Shtooka" if "Shtooka" in credit else "Commons"),
        audio_url=info.get("url", "").split("?")[0],
        source_sha1=info.get("sha1"),
        source_bytes=info.get("size"),
        uploader=info.get("user"),
        uploader_id="commons-user:" + info["user"] if info.get("user") else None,
        recorder_id=None,
        author=artist or None,
        recorder=None,
        speaker_native_status="UNKNOWN",
        speaker_identity_confidence="unknown",
        license=lic,
        license_url=lic_url,
        api_license=meta.get("LicenseShortName", {}).get("value"),
        license_evidence_url="https://commons.wikimedia.org/w/index.php?oldid="
        + str(page["revisions"][0]["revid"])
        if page.get("revisions")
        else info.get("descriptionurl"),
        license_templates=re.findall(r"\{\{(?:[Mm]ulti-license|cc-[^{}]+)\}\}", wiki),
        attribution=f"{page['title']}; {artist}; {info.get('descriptionurl')}; {lic_url}",
        attribution_required=lic != "CC0-1.0" if lic else None,
        commercial_use_status="permitted" if lic else "unresolved_or_excluded",
        derivative_use_status="permitted" if lic else "unresolved_or_excluded",
        share_alike_required=False if lic else None,
        public_domain_basis=None,
        access_date=ACCESS_DATE,
        provenance_confidence="medium" if lic else "low",
        license_status="GREEN" if lic else "YELLOW",
        label_confidence=None,
        label_source=None,
        observed_surface_tone=None,
        native_status_evidence=None,
        revision_id=page.get("revisions", [{}])[0].get("revid"),
        metadata_description=desc,
        source_credit=credit,
        notes="Exploratory lexical label; realized tone and native status not listening-certified.",
    )
    reasons = []
    if license_reject:
        reasons.append(license_reject)
    if not page["title"].lower().endswith((".ogg", ".oga", ".wav", ".flac", ".mp3", ".opus")):
        reasons.append("not_audio")
    parsed = None
    if ll:
        speaker = field(wiki, "speakerId") or field(wiki, "locutorId")
        record["speaker_id"] = "lingualibre:" + speaker if speaker else None
        record["recorder"] = field(wiki, "author")
        record["speaker_name"] = field(wiki, "speaker") or field(wiki, "locutor")
        record["speaker_identity_confidence"] = "explicit_profile_id" if speaker else "unknown"
        record["text"] = field(wiki, "transcription")
        if field(wiki, "languageId") not in ("Q9192", "Q727694"):
            reasons.append("wrong_language_or_unverified")
        if field(wiki, "qualifier"):
            reasons.append("qualifier_requires_audit")
        if record["text"]:
            parsed, reason = dictionary_reading(record["text"])
            if reason:
                reasons.append(reason)
            record["label_source"] = "pypinyin 0.55.0 heteronym=True; singleton reading only"
        else:
            reasons.append("metadata_insufficient")
    else:
        match = re.search(r'Pronunciation of "([^"]+)" \(([^)]+)\) in Chinese\.', desc)
        if match:
            pinyin, text = match.groups()
            record["text"] = text
            if HAN.fullmatch(text):
                parsed = parse_pinyin(pinyin)
                if parsed:
                    # Check supplied reading membership; never choose the first reading.
                    from pypinyin import Style
                    from pypinyin import pinyin as readings

                    options = readings(
                        text, style=Style.TONE3, heteronym=True, neutral_tone_with_five=True
                    )[0]
                    if parsed[0].replace("ü", "v") not in [p.replace("ü", "v") for p in options]:
                        reasons.append("metadata_dictionary_conflict")
                else:
                    reasons.append("unknown_pronunciation")
                record["label_source"] = (
                    "explicit file description pinyin; dictionary membership cross-check"
                )
            else:
                reasons.append("multi_syllable")
        else:
            reasons.append("metadata_insufficient")
        # Authors are NOT generally speakers. Only reviewed source-specific mappings qualify.
        speakers = {
            "Wei Gao, Vion Nicolas": ("shtooka:wei-gao", "Wei Gao", "Nicolas Vion"),
            "Yue Tan": ("shtooka:yue-tan", "Yue Tan", None),
            "Xudong Yang": ("commons:wyverald", "Xudong Yang", "Xudong Yang"),
        }
        if artist in speakers and match:
            sid, name, recorder = speakers[artist]
            record.update(
                speaker_id=sid,
                speaker_name=name,
                recorder=recorder,
                speaker_identity_confidence="source_specific_mapping_pending_embedded_tag_check",
            )
    if record["recorder"]:
        recorder_match = re.search(r"User:([^]|]+)", record["recorder"])
        record["recorder_id"] = (
            "commons-user:" + recorder_match.group(1)
            if recorder_match
            else "named-recorder:" + record["recorder"]
        )
    if record["text"]:
        record["text"] = normalize_text(record["text"])
    if not record["speaker_id"]:
        reasons.append("speaker_unknown")
    if parsed:
        record.update(
            pinyin=parsed[0], tone=parsed[1], syllable_count=1, label_confidence="high_lexical"
        )
        if parsed[1] not in (1, 2, 3, 4):
            reasons.append("neutral_tone")
    if not parsed and not any(
        x in reasons for x in ("multi_syllable", "ambiguous_reading", "neutral_tone")
    ):
        reasons.append("label_unresolved")
    return record, list(dict.fromkeys(reasons))


def write_jsonl(path, rows):
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
    temporary.replace(path)


def select(cache, offline=False):
    client = Client(cache / "api", offline)
    pages = [
        json.loads(line) for line in (cache / "commons-metadata.jsonl").read_text().splitlines()
    ]
    candidates = sorted(
        [p for p in pages if preliminary(p)],
        key=lambda p: p["title"].startswith("File:LL-Q727694"),
    )
    print(f"Single-character metadata candidates: {len(candidates)}", flush=True)
    for start in range(0, len(candidates), 50):
        batch = candidates[start : start + 50]
        result = client.query(
            prop="revisions",
            pageids="|".join(str(p["pageid"]) for p in batch),
            rvprop="content|ids",
            rvslots="main",
        )
        for page in batch:
            page.update(result["query"]["pages"][str(page["pageid"])])
    accepted, rejected = [], []
    seen = set()
    for page in pages:
        record, reasons = normalize(page)
        # Preselection is conservative; LL phrase metadata needn't be fetched to reject.
        if page["title"].startswith("File:LL-") and not preliminary(page):
            reasons = ["not_single_character_candidate"]
        sha = record["source_sha1"]
        if not reasons and sha in seen:
            reasons.append("duplicate_source_sha1")
        if reasons:
            rejected.append(
                {
                    "source_asset_id": record["source_asset_id"],
                    "title": page["title"],
                    "source_url": record["source_url"],
                    "reasons": reasons,
                    "api_license": record["api_license"],
                }
            )
        else:
            seen.add(sha)
            accepted.append(record)
    # Round robin speaker x tone cells: scarce speakers aren't lost to the cap.
    groups = collections.defaultdict(list)
    for row in accepted:
        groups[(row["speaker_id"], row["tone"])].append(row)
    selected = []
    while groups:
        for key in sorted(list(groups)):
            selected.append(groups[key].pop(0))
            if not groups[key]:
                del groups[key]
    write_jsonl(cache / "selected.jsonl", selected)
    write_jsonl(cache / "rejected.jsonl", rejected)
    write_jsonl(cache / "candidate-evidence.jsonl", candidates)
    print(
        "Eligible",
        len(selected),
        "Rejected",
        len(rejected),
        "speakers",
        dict(collections.Counter(r["speaker_id"] for r in selected)),
        "tones",
        dict(collections.Counter(r["tone"] for r in selected)),
        flush=True,
    )


def diagnostics(path):
    probe = json.loads(
        subprocess.check_output(
            ["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(path)],
            timeout=30,
        )
    )
    streams = [s for s in probe["streams"] if s["codec_type"] == "audio"]
    if len(streams) != 1:
        raise ValueError("Expected exactly one audio stream")
    stream = streams[0]
    rate, channels = int(stream["sample_rate"]), int(stream["channels"])
    duration = float(probe["format"]["duration"])
    if not 0 < duration <= 30 or not 0 < rate <= 192000 or not 0 < channels <= 8:
        raise ValueError("Decode safety bounds exceeded")
    pcm = subprocess.check_output(
        [
            "ffmpeg",
            "-v",
            "error",
            "-i",
            str(path),
            "-map",
            "0:a:0",
            "-t",
            "30",
            "-f",
            "f32le",
            "-acodec",
            "pcm_f32le",
            "-",
        ],
        timeout=30,
    )
    samples = array.array("f", pcm)
    if sys.byteorder != "little":
        samples.byteswap()
    if not samples or any(not math.isfinite(x) for x in samples):
        raise ValueError("Empty or nonfinite decoded audio")
    rms = math.sqrt(sum(x * x for x in samples) / len(samples))
    peak = max(abs(x) for x in samples)
    # All-channel 10 ms windows; this is an amplitude proxy, not speech activity detection.
    width = max(1, round(rate * 0.01) * channels)
    frames = [samples[i : i + width] for i in range(0, len(samples), width)]
    silence = sum(math.sqrt(sum(x * x for x in f) / len(f)) < 0.001 for f in frames) / len(frames)
    return {
        "duration_seconds": len(samples) / rate / channels,
        "sample_rate_hz": rate,
        "channels": channels,
        "peak_level": peak,
        "rms": rms,
        "clipping_percentage": 100 * sum(abs(x) >= 0.999 for x in samples) / len(samples),
        "silence_ratio": silence,
        "decode_success": True,
        "decoded_pcm_sha256": hashlib.sha256(
            f"{rate}:{channels}:f32le:".encode() + pcm
        ).hexdigest(),
        "embedded_tags": {**probe.get("format", {}).get("tags", {}), **stream.get("tags", {})},
    }


def validate(row):
    missing = set(REQUIRED) - row.keys()
    if missing:
        raise ValueError(f"Missing fields: {sorted(missing)}")
    if row["tone"] not in (1, 2, 3, 4) or row["syllable_count"] != 1:
        raise ValueError("Not a supported isolated tone")
    if not row["speaker_id"] or row["license_status"] != "GREEN":
        raise ValueError("Missing identity or clean rights")
    if not re.fullmatch("[a-f0-9]{64}", row["audio_sha256"] or ""):
        raise ValueError("Invalid audio hash")
    if row["speaker_native_status"] not in ("NATIVE", "NON_NATIVE", "UNKNOWN"):
        raise ValueError("Invalid native status")
    if not row["decode_success"] or row["duration_seconds"] <= 0:
        raise ValueError("Invalid audio")


class Budget:
    def __init__(self, count=500, size=1024**3, used_files=0, used_bytes=0):
        if not 0 <= count <= MAX_FILES or not 0 <= size <= MAX_BYTES:
            raise ValueError("Requested cap exceeds 500 files / 1 GiB or is negative")
        self.count, self.size = count, size
        self.files, self.bytes = used_files, used_bytes

    def allows(self, size):
        return self.files < self.count and size >= 0 and self.bytes + size <= self.size


def bounded_copy(response, target, expected_size, budget):
    if not budget.allows(expected_size):
        raise ValueError("Download cap reached")
    partial = target.with_suffix(target.suffix + ".part")
    budget.files += 1
    received = 0
    try:
        with partial.open("wb") as handle:
            while received < expected_size:
                block = response.read(min(65536, expected_size - received))
                if not block:
                    break
                received += len(block)
                budget.bytes += len(block)
                handle.write(block)
        if received != expected_size:
            raise ValueError("Download size mismatch")
        partial.replace(target)
    finally:
        partial.unlink(missing_ok=True)


class DownloadPacing:
    """One request at a time, persisted cooldown, bounded throttles per invocation."""

    def __init__(self, state_path=None, delay=60, max_throttles=2):
        if delay < 2 or max_throttles < 1 or max_throttles > 3:
            raise ValueError("Delay must be >=2s; max-throttles must be 1..3")
        self.state_path = state_path
        self.delay = delay
        self.max_throttles = max_throttles
        self.throttles = 0
        self.state = (
            json.loads(state_path.read_text()) if state_path and state_path.exists() else {}
        )

    def before_request(self):
        wait = max(self.delay, self.state.get("not_before_epoch", 0) - time.time())
        if wait > self.delay:
            print(f"Honoring persisted cooldown: {math.ceil(wait)}s", flush=True)
        pause(wait)

    def throttled(self, exc):
        self.throttles += 1
        delay = retry_seconds(exc.headers.get("Retry-After"), 60 * 2 ** (self.throttles - 1))
        self.state = {
            "not_before_epoch": time.time() + delay,
            "last_status": exc.code,
            "retry_after_seconds": delay,
        }
        if self.state_path:
            temporary = self.state_path.with_suffix(".tmp")
            temporary.write_text(json.dumps(self.state, indent=2) + "\n")
            temporary.replace(self.state_path)
        print(
            f"HTTP {exc.code}; cooldown {delay}s; throttle {self.throttles}/{self.max_throttles}",
            flush=True,
        )
        return self.throttles < self.max_throttles


def fetch_audio(url, path, size, budget, pacing=None):
    """Stop cleanly on repeated throttles, including across different files."""
    pacing = pacing or DownloadPacing()
    while True:
        pacing.before_request()
        try:
            with urllib.request.urlopen(
                urllib.request.Request(url, headers={"User-Agent": USER_AGENT}), timeout=45
            ) as response:
                length = response.headers.get("Content-Length")
                if length and int(length) != size:
                    raise ValueError("HTTP size disagrees with inventory")
                bounded_copy(response, path, size, budget)
                return
        except urllib.error.HTTPError as exc:
            if exc.code not in (429, 503) or not pacing.throttled(exc):
                raise


def download(
    cache,
    output,
    max_files=500,
    max_bytes=1024**3,
    offline=False,
    request_delay=60,
    max_throttles=2,
):
    audio_dir = cache / "audio"
    audio_dir.mkdir(exist_ok=True)
    output.mkdir(parents=True, exist_ok=True)
    ledger_path = cache / "download-ledger.json"
    ledger = (
        json.loads(ledger_path.read_text()) if ledger_path.exists() else {"files": 0, "bytes": 0}
    )
    budget = Budget(max_files, max_bytes, ledger["files"], ledger["bytes"])
    selected = [json.loads(line) for line in (cache / "selected.jsonl").read_text().splitlines()]
    manifest, rejected = [], []
    stopped = None
    pacing = DownloadPacing(cache / "network-cooldown.json", request_delay, max_throttles)
    seen_hash, seen_pcm = set(), set()
    for row in selected:
        path = audio_dir / (row["source_asset_id"].replace(":", "-") + Path(row["title"]).suffix)
        if not path.exists():
            if offline or stopped or not budget.allows(row["source_bytes"]):
                rejected.append(
                    {
                        "source_asset_id": row["source_asset_id"],
                        "reasons": [
                            "acquisition_stopped" if stopped else "download_cap_or_offline"
                        ],
                    }
                )
                continue
            url = row["audio_url"]
            if urllib.parse.urlparse(url).hostname != "upload.wikimedia.org":
                raise ValueError("Unexpected audio host")
            try:
                fetch_audio(url, path, row["source_bytes"], budget, pacing)
            except (urllib.error.URLError, TimeoutError, KeyboardInterrupt) as exc:
                rejected.append(
                    {
                        "source_asset_id": row["source_asset_id"],
                        "reasons": ["network_stopped"],
                        "detail": str(exc),
                    }
                )
                stopped = str(exc) or "user_interrupt"
                print(f"Acquisition stopped: {stopped}", flush=True)
                # Still inspect later cached files so a throttle cannot shrink the local pilot.
                continue
            finally:
                ledger_path.write_text(
                    json.dumps({"files": budget.files, "bytes": budget.bytes}, indent=2) + "\n"
                )
        data = path.read_bytes()
        if len(data) != row["source_bytes"] or hashlib.sha1(data).hexdigest() != row["source_sha1"]:
            raise ValueError(f"Source changed or corrupt cache: {path}")
        row.update(
            local_path=str(path.resolve()),
            audio_sha256=hashlib.sha256(data).hexdigest(),
            acquisition_status="downloaded_hash_verified_decoded",
        )
        try:
            row.update(diagnostics(path))
        except (subprocess.SubprocessError, ValueError, KeyError) as exc:
            rejected.append(
                {
                    "source_asset_id": row["source_asset_id"],
                    "reasons": ["decode_error"],
                    "detail": str(exc),
                }
            )
            continue
        reasons = []
        if row["rms"] < 1e-5 or row["peak_level"] < 1e-4:
            reasons.append("near_zero_audio")
        if row["clipping_percentage"] > 10:
            reasons.append("extreme_clipping")
        if row["audio_sha256"] in seen_hash or row["decoded_pcm_sha256"] in seen_pcm:
            reasons.append("duplicate_audio")
        if reasons:
            rejected.append({"source_asset_id": row["source_asset_id"], "reasons": reasons})
            continue
        seen_hash.add(row["audio_sha256"])
        seen_pcm.add(row["decoded_pcm_sha256"])
        validate(row)
        manifest.append(row)
        if len(manifest) % 25 == 0:
            print(f"Accepted downloaded clips: {len(manifest)}", flush=True)
    write_jsonl(output / "pilot-manifest.jsonl", manifest)
    write_jsonl(cache / "download-rejected.jsonl", rejected)
    summary = {
        "acquisition_stopped_reason": stopped,
        "eligible_metadata_rows": len(selected),
        "eligible_not_in_local_pilot": len(selected) - len(manifest),
        "accepted": len(manifest),
        "download_ledger": {"files": budget.files, "bytes": budget.bytes},
        "tones": dict(collections.Counter(r["tone"] for r in manifest)),
        "speakers": dict(collections.Counter(r["speaker_id"] for r in manifest)),
        "licenses": dict(collections.Counter(r["license"] for r in manifest)),
        "native_status": dict(collections.Counter(r["speaker_native_status"] for r in manifest)),
        "download_rejections": dict(collections.Counter(x for r in rejected for x in r["reasons"])),
    }
    (output / "pilot-summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["select", "download"])
    parser.add_argument("--cache", type=Path, default=Path("/tmp/benma-pronunciation-v2-pilot"))
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("docs/research/pronunciation-v2/2026-09-28-data-feasibility"),
    )
    parser.add_argument("--max-files", type=int, default=500)
    parser.add_argument("--max-bytes", type=int, default=1024**3)
    parser.add_argument("--offline", action="store_true")
    parser.add_argument(
        "--request-delay",
        type=float,
        default=60,
        help="Seconds between serial requests; default 60",
    )
    parser.add_argument(
        "--max-throttles",
        type=int,
        default=2,
        help="Stop after this many 429/503 responses per run (1..3)",
    )
    args = parser.parse_args()
    if args.command == "select":
        select(args.cache, args.offline)
    else:
        download(
            args.cache,
            args.output,
            args.max_files,
            args.max_bytes,
            args.offline,
            args.request_delay,
            args.max_throttles,
        )


if __name__ == "__main__":
    main()
