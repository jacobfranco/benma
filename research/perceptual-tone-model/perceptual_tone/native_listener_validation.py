"""Write-once blinded listening study. Stdlib only; no inference or fitting imports."""

import argparse
import base64
import hashlib
import io
import json
import random
import shutil
import subprocess
import wave
import zipfile
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

from .common import PACKAGE, ROOT, digest, file_hash, read_json, read_rows, write_json

OUT = PACKAGE / "data/generated/native-listener-validation-v1"
AUDIT = PACKAGE / "data/generated/pooling-blocker-audit-v1"
PRIOR = PACKAGE / "data/generated/pooling-confirmatory-v1"
LEARNER = PACKAGE / "data/generated/releases/benma-learner-natural-v1-20261019"
NATIVE = PACKAGE / (
    "data/generated/aishell3-multispeaker-v2/releases/aishell3-multispeaker-context-v2-20261017"
)
SELECTION_SHA = "5c4ac1ad525691648044362cecba32495acace05165b9536819ffdef23aabe6e"
VERSION = "native-listener-validation-v1"
SEED = 20261022
CHOICES = ["T1", "T2", "T3", "T4", "NEUTRAL", "UNCLEAR"]
RULES = {
    "target_listeners": 5,
    "minimum_qualified": 3,
    "maximum_enrolled": 5,
    "native_correct_min": 10,
    "native_denominator": 12,
    "native_per_tone_min": 2,
    "native_per_tone_denominator": 3,
    "repeat_consistent_min": 6,
    "repeat_denominator": 8,
    "strong_n_min": 5,
    "strong_joint_fraction": 0.8,
    "moderate_n_min": 3,
    "moderate_joint_fraction": 2 / 3,
    "strong_unclear_max": 0.2,
    "moderate_unclear_max": 1 / 3,
    "minimum_same_item_distance": 8,
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def frozen_selection():
    require(file_hash(AUDIT / "selection.json") == SELECTION_SHA, "audit selection changed")
    s = read_json(AUDIT / "selection.json")
    require(len(s["learner_disagreements"]) == len(s["learner_controls"]) == 7, "case count")
    return s


def select_native(rows, split, quarantine):
    """Deterministic structural clarity proxies; never accepts predictions as inputs."""
    pool = []
    for c in rows:
        r, s = c["original"], c["spans"]
        if (
            r["partition"] != "test"
            or split[r["speaker_id"]] != "test"
            or r["example_id"] in quarantine
            or r["exclusion_reasons"]
            or s["flags"]
            or not s["available"]
            or r["erhua"]
            or r["unusual_multi_hanzi"]
            or r["corpus_tone"] not in (1, 2, 3, 4)
        ):
            continue
        # Avoid third-tone chains in qualification controls; use corpus reading, not lexicon.
        if r["corpus_tone"] == 3 and any(
            neighbor and neighbor["corpus_tone"] == 3
            for neighbor in (r["preceding"], r["following"])
        ):
            continue
        d = (
            s["tone_bearing_pooling_span"]["end_seconds"]
            - s["tone_bearing_pooling_span"]["start_seconds"]
        )
        pool.append((r, s, d))
    chosen, speakers, utterances = [], Counter(), set()
    for difficulty, count, low, high in [("positive", 3, 0.18, 0.45), ("challenge", 1, 0.06, 0.12)]:
        for _ in range(count):
            for tone in (1, 2, 3, 4):
                candidates = [
                    (r, s, d)
                    for r, s, d in pool
                    if r["corpus_tone"] == tone
                    and low <= d <= high
                    and r["utterance_id"] not in utterances
                ]
                require(candidates, "insufficient native controls")
                r, s, _ = min(
                    candidates,
                    key=lambda v: (
                        speakers[v[0]["speaker_id"]],
                        digest([SEED, v[0]["example_id"]]),
                    ),
                )
                chosen.append((r, s, difficulty))
                speakers[r["speaker_id"]] += 1
                utterances.add(r["utterance_id"])
    return chosen


def wav_clip(path, span):
    with wave.open(str(path)) as w:
        require(w.getnchannels() == 1 and w.getsampwidth() == 2, "PCM16 mono required")
        rate = w.getframerate()
        a, b = span["start_sample"], span["end_sample"]
        require(rate == span["sample_rate_hz"] and 0 <= a < b <= w.getnframes(), "invalid span")
        w.setpos(a)
        pcm = w.readframes(b - a)
    require(any(pcm), "silent clip")
    result = io.BytesIO()
    with wave.open(result, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(pcm)
    return result.getvalue()


def make_trials(items, listener_id, seed):
    trials = [
        dict(item_id=i["id"], kind=i["kind"], view=v, repeat=False)
        for i in items
        for v in ("crop", "context")
    ]
    repeat_ids = []
    for kind, count in [("disagreement", 3), ("agreement", 3), ("native_positive", 2)]:
        candidates = sorted(
            (i["id"] for i in items if i["kind"] == kind), key=lambda i: digest([SEED, "repeat", i])
        )
        repeat_ids.extend(candidates[:count])
    trials += [
        dict(
            item_id=i,
            kind=next(x["kind"] for x in items if x["id"] == i),
            view="context",
            repeat=True,
        )
        for i in repeat_ids
    ]
    rng = random.Random(seed)
    for _attempt in range(100000):
        rng.shuffle(trials)
        positions = {}
        valid = True
        for pos, t in enumerate(trials):
            if (
                t["item_id"] in positions
                and pos - positions[t["item_id"]] < RULES["minimum_same_item_distance"]
            ):
                valid = False
                break
            positions[t["item_id"]] = pos
        if valid and all(
            len({t["kind"].split("_")[0] for t in trials[k : k + 12]}) == 3
            for k in range(0, len(trials) - 11, 12)
        ):
            break
    else:
        raise ValueError("randomization constraints unsatisfied")
    for pos, t in enumerate(trials):
        t["trial_id"] = digest([VERSION, listener_id, seed, pos])[:24]
        t["position"] = pos + 1
    return trials, _attempt + 1


def response_schema():
    string = {"type": "string"}
    eligibility = {
        "type": "object",
        "additionalProperties": False,
        "required": ["adult", "native", "primary_childhood", "independent"],
        "properties": {
            k: {"const": True} for k in ("adult", "native", "primary_childhood", "independent")
        },
    }
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "additionalProperties": False,
        "required": [
            "version",
            "listener_id",
            "packet_sha256",
            "eligibility",
            "background",
            "started_at",
            "completed_at",
            "responses",
        ],
        "properties": {
            "version": {"const": VERSION},
            "listener_id": {"enum": [f"L{i:02}" for i in range(1, 6)]},
            "packet_sha256": {"type": "string", "pattern": "^[a-f0-9]{64}$"},
            "eligibility": eligibility,
            "background": {
                "type": "object",
                "additionalProperties": False,
                "required": ["region", "other_variety", "current_language"],
                "properties": {
                    k: {"type": "string", "maxLength": 200}
                    for k in ("region", "other_variety", "current_language")
                },
            },
            "started_at": string,
            "completed_at": string,
            "responses": {
                "type": "array",
                "minItems": 68,
                "maxItems": 68,
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["trial_id", "position", "answer", "answered_at", "play_count"],
                    "properties": {
                        "trial_id": {"type": "string", "pattern": "^[a-f0-9]{24}$"},
                        "position": {"type": "integer", "minimum": 1, "maximum": 68},
                        "answer": {"enum": CHOICES},
                        "answered_at": string,
                        "play_count": {"type": "integer", "minimum": 1},
                    },
                },
            },
        },
    }


def verify_blinding(folder, packet, items):
    require(
        set(p.name for p in folder.iterdir()) == {"index.html", "app.js", "packet.js"},
        "unexpected file in shareable folder",
    )
    require(set(packet) == {"version", "listener_id", "packet_sha256", "trials"}, "packet fields")
    for t in packet["trials"]:
        require(
            set(t)
            == {"trial_id", "position", "view", "target", "context", "target_start", "target_end"},
            "trial contains hidden fields",
        )
        for field in ("target", "context"):
            raw = base64.b64decode(t[field].removeprefix("data:audio/wav;base64,"))
            require(raw[:4] == b"RIFF" and raw[8:12] == b"WAVE", "invalid WAV")
            # Minimal WAV only: no text, filenames, tags, INFO or metadata chunks.
            chunks, offset = [], 12
            while offset < len(raw):
                name = raw[offset : offset + 4]
                size = int.from_bytes(raw[offset + 4 : offset + 8], "little")
                chunks.append(name)
                offset += 8 + size + size % 2
            require(chunks == [b"fmt ", b"data"], "audio metadata leakage")
    text = "\n".join((folder / f).read_text() for f in ("index.html", "app.js"))
    metadata = json.dumps(
        [{k: v for k, v in t.items() if k not in ("target", "context")} for t in packet["trials"]]
    )
    forbidden = [
        "expanded",
        "pilot",
        "prediction",
        "probabilities",
        "expected_tone",
        "lexical",
        "sandhi",
        "grade",
        "hanzi",
        "pinyin",
        "gold",
        "disagreement",
        "native_positive",
        "benma",
        "private",
    ]
    require(not any(word in (text + metadata).lower() for word in forbidden), "text leakage")
    require(not any(i["id"] in text + metadata for i in items), "source ID leakage")
    return {
        "passed": True,
        "trials": len(packet["trials"]),
        "audio_metadata": "fmt/data only",
        "schema_allowlist": True,
        "source_ids_absent": True,
        "private_files_absent": True,
    }


def build(out=OUT):
    require(not out.exists(), "write-once: output already exists")
    s = frozen_selection()
    source_paths = set(AUDIT.glob("*.json")) | set(NATIVE.glob("*.*")) | set(LEARNER.glob("*.*"))
    source_paths |= {
        PRIOR / "representation-manifest.json",
        PRIOR / "representation-manifest-seal.json",
        PRIOR / "predictions.json",
    }
    inherited = read_json(AUDIT / "freeze-verification.json")["checked_files"]
    for p, sha in inherited.items():
        require(file_hash(ROOT / p) == sha, "protected source changed: " + p)
        source_paths.add(ROOT / p)
    for root, manifest in [(LEARNER, "release-manifest.json"), (NATIVE, "release.json")]:
        for p, sha in read_json(root / manifest)["files"].items():
            require(file_hash(root / p) == sha, "frozen release mismatch: " + p)
            source_paths.add(root / p)
    require(
        read_json(NATIVE / "release.json")["qa_gate"] == "SATISFIED_WITH_EXPLICIT_QUARANTINES",
        "native release QA gate",
    )
    registry = {r["speaker_id"]: r for r in read_rows(NATIVE / "speaker-registry.jsonl")}
    rep = read_json(PRIOR / "representation-manifest.json")
    owners = {
        r["id"]: r["ownership_span"]
        for r in rep["records"]
        if r["arm"] == "ACOUSTIC_WEIGHTED" and r["perturbation"] == "BASE"
    }
    learner_rows = {r["example_id"]: r for r in read_rows(LEARNER / "primary.jsonl")}
    selected = [
        (learner_rows[i], learner_rows[i]["spans"], "disagreement")
        for i in s["learner_disagreements"]
    ]
    selected += [
        (learner_rows[m["control"]], learner_rows[m["control"]]["spans"], "agreement")
        for m in s["learner_controls"]
    ]
    native = select_native(
        read_rows(NATIVE / "manifest.jsonl"),
        read_json(NATIVE / "split.json")["assignments"],
        {r["record"]["example_id"] for r in read_rows(NATIVE / "quarantined.jsonl")},
    )
    selected += [(r, sp, "native_" + difficulty) for r, sp, difficulty in native]
    items, audio = [], {}
    for r, sp, kind in selected:
        p = Path(r["audio"]["reference"])
        require(file_hash(p) == r["audio"]["sha256"], "audio changed")
        source_paths.add(p)
        with wave.open(str(p)) as source:
            require(
                hashlib.sha256(source.readframes(source.getnframes())).hexdigest()
                == r["pcm_sha256"],
                "source PCM changed",
            )
        crop, context = sp["playback_read_unit"], sp["context"]
        if kind in ("disagreement", "agreement"):
            require(
                [crop["start_seconds"], crop["end_seconds"]] == owners[r["example_id"]],
                "frozen ownership mismatch",
            )
        label = None
        if kind.startswith("native"):
            require(
                registry[r["speaker_id"]]["metadata_provenance"]["official_metadata_exact_match"],
                "native speaker metadata not verified",
            )
            provenance = r["transcript_provenance"]
            transcript = p.parents[3] / provenance["member"]
            require(file_hash(transcript) == provenance["sha256"], "pronunciation source changed")
            source_paths.add(transcript)
            fields = transcript.read_text().splitlines()[provenance["line"] - 1].split()
            require(
                fields[0] == r["utterance_id"] + ".wav"
                and fields[2 + 2 * r["index"]] == r["corpus_pinyin"],
                "read-label mismatch",
            )
            label = "T" + str(r["corpus_tone"])
        item = {
            "id": r["example_id"],
            "recording_id": r["utterance_id"],
            "unit_id": r["index"],
            "speaker_id": r["speaker_id"],
            "kind": kind,
            "native_label": label,
            "source_audio": str(p),
            "canonical_audio_sha256": file_hash(p),
            "source_pcm_sha256": r["pcm_sha256"],
            "owner_crop": crop,
            "context": context,
            "label_basis": r["transcript_provenance"] if label else None,
            "original_recordings": r.get("original_sources", []),
        }
        blobs = {view: wav_clip(p, span) for view, span in [("crop", crop), ("context", context)]}
        item["clip_sha256"] = {k: hashlib.sha256(v).hexdigest() for k, v in blobs.items()}
        audio[item["id"]] = blobs
        items.append(item)
    freeze = {str(p.relative_to(ROOT)): file_hash(p) for p in sorted(source_paths) if p.is_file()}
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    out.mkdir(parents=True)
    write_json(out / "freeze-before.json", {"files": freeze, "git_head": head})
    plan = {
        "version": VERSION,
        "registered_at": datetime.now(UTC).isoformat(),
        "seed": SEED,
        "rules": RULES,
        "choices": CHOICES,
        "selection_sha256": SELECTION_SHA,
        "learner_disagreements": s["learner_disagreements"],
        "learner_controls": s["learner_controls"],
        "native_control_ids": [i["id"] for i in items if i["kind"].startswith("native")],
        "native_selection": "test speakers; clean frozen flags; unique utterances; 3/tone .18-.45s "
        "positive nucleus and 1/tone .06-.12s challenge; speaker balance "
        "then SHA256(seed, ID); exclude adjacent T3 chains; no predictions",
        "presentation": (
            "all 30 items in crop-only and context-then-identical-crop; 8 context repeats"
        ),
        "repeat_selection": (
            "lowest SHA256(seed, repeat, ID): 3 disagreements, 3 agreements, 2 positives"
        ),
        "stopping": "enroll assigned L01-L05 once, no replacements selected by results; freeze all "
        "available complete and incomplete submissions before scoring; >=3 qualified "
        "required, otherwise unresolved; additional cohort needs new preregistration",
        "protocol_sha256": file_hash(PACKAGE / "native-listener-validation-protocol.md"),
        "implementation_sha256": file_hash(Path(__file__)),
        "analysis_sha256": file_hash(PACKAGE / "perceptual_tone/native_listener_analysis.py"),
        "schema_sha256": digest(response_schema()),
        "human_responses_exist": False,
    }
    write_json(out / "preregistration.json", plan)
    write_json(out / "response-schema.json", response_schema())
    mapping = {"version": VERSION, "items": items, "listeners": {}}
    leaks = {}
    for n in range(1, 6):
        lid = f"L{n:02}"
        seed = int(digest([SEED, lid])[:16], 16)
        trials, attempts = make_trials(items, lid, seed)
        public = []
        for t in trials:
            item = next(i for i in items if i["id"] == t["item_id"])
            blobs = audio[item["id"]]
            public.append(
                {
                    "trial_id": t["trial_id"],
                    "position": t["position"],
                    "view": t["view"],
                    "target": "data:audio/wav;base64," + base64.b64encode(blobs["crop"]).decode(),
                    "context": "data:audio/wav;base64,"
                    + base64.b64encode(blobs["context"]).decode(),
                    "target_start": item["owner_crop"]["start_seconds"]
                    - item["context"]["start_seconds"],
                    "target_end": item["owner_crop"]["end_seconds"]
                    - item["context"]["start_seconds"],
                }
            )
        packet = {"version": VERSION, "listener_id": lid, "trials": public}
        packet["packet_sha256"] = digest(packet)
        folder = out / "listener-packages" / lid
        folder.mkdir(parents=True)
        for name in ("index.html", "app.js"):
            shutil.copyfile(PACKAGE / "scripts/native_listener" / name, folder / name)
        (folder / "packet.js").write_text(
            "const PACKET = " + json.dumps(packet, separators=(",", ":")) + ";\n"
        )
        mapping["listeners"][lid] = {
            "seed": seed,
            "shuffle_attempts": attempts,
            "packet_sha256": packet["packet_sha256"],
            "trials": trials,
        }
        leaks[lid] = verify_blinding(folder, packet, items)
        archive = out / "share" / (lid + ".zip")
        archive.parent.mkdir(exist_ok=True)
        with zipfile.ZipFile(archive, "x", compression=zipfile.ZIP_DEFLATED) as zipped:
            for name in ("index.html", "app.js", "packet.js"):
                info = zipfile.ZipInfo(lid + "/" + name, date_time=(1980, 1, 1, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                zipped.writestr(info, (folder / name).read_bytes())
        with zipfile.ZipFile(archive) as zipped:
            require(
                set(zipped.namelist())
                == {lid + "/" + name for name in ("index.html", "app.js", "packet.js")},
                "share archive leakage",
            )
    write_json(out / "PRIVATE/trial-key.json", mapping)
    write_json(
        out / "PRIVATE/prediction-reference.json",
        {
            "path": str(PRIOR / "predictions.json"),
            "sha256": file_hash(PRIOR / "predictions.json"),
            "note": "opened ONLY after raw-response seal AND verified consensus seal",
        },
    )
    write_json(out / "leak-checks.json", leaks)
    write_json(
        out / "preregistration-seal.json",
        {
            "sha256": file_hash(out / "preregistration.json"),
            "files": {
                str(p.relative_to(out)): file_hash(p) for p in sorted(out.rglob("*")) if p.is_file()
            },
        },
    )
    verify_freeze(out, write=True)
    return {"output": str(out), "items": len(items), "trials_per_listener": 68}


def verify_freeze(out=OUT, write=False):
    before = read_json(out / "freeze-before.json")
    changed = [p for p, sha in before["files"].items() if file_hash(ROOT / p) != sha]
    require(not changed, "frozen inputs mutated: " + str(changed))
    require(
        subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
        == before["git_head"],
        "git HEAD changed",
    )
    result = {
        "changed_files": changed,
        "checked_files": len(before["files"]),
        "git_head_unchanged": True,
    }
    if write:
        write_json(out / "freeze-verification.json", result)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["build", "verify"])
    args = parser.parse_args()
    print(json.dumps(build() if args.command == "build" else verify_freeze(), indent=2))
