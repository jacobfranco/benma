"""Local physical-test orchestration; artifacts never enter a frozen research release."""

import csv
import hashlib
import json
import os
import re
import shutil
import subprocess
import time
import uuid
import wave
from pathlib import Path

from .aishell3 import alignment_token
from .aishell3_alignment import reconstruct, textgrid
from .common import PACKAGE, ROOT, file_hash, read_json, write_json
from .dev_inference import (
    LearnedRecognizer,
    abstention,
    compare,
    project_spans,
    require_dev,
    span_contract,
)
from .learner_benchmark import tokens
from .learner_transfer import deterministic

SERVICE_PYTHON = ROOT / "services/api/.venv/bin/python"
DEFAULT_RUNS = PACKAGE / "data/generated/dev-learned-takes-v1"


def service(request):
    result = subprocess.run(
        [str(SERVICE_PYTHON), str(PACKAGE / "scripts/dev_service_bridge.py")],
        input=json.dumps(request),
        text=True,
        capture_output=True,
        timeout=100,
        check=True,
    )
    return json.loads(result.stdout)


def align(audio, syllables, folder):
    """Frozen phone inventory, automatic alignment, unchanged reconstruction checks."""
    folder.mkdir()
    dictionary = read_json(PACKAGE / "data/generated/learner-alignment-v1/lexicon.json")
    # Reuse native pronunciations in addition to the learner alignment inventory.
    for part in ("pilot", "expansion"):
        audit = read_json(
            PACKAGE / f"data/generated/aishell3-multispeaker-v2/{part}/lexicon-audit.json"
        )
        dictionary.update(audit["pronunciations"])
    units, lexicon = [], {}
    readings = tokens(
        {
            "alignment_transcript": "".join(s["characters"] for s in syllables),
            "intended_phrase": None,
            "actual_reading_hypothesis": None,
        }
    )
    for s, reading in zip(syllables, readings, strict=True):
        # Reuse research lexical MFA pronunciation, including ge4. Contextual
        # neutral expectation stays in the service result and never enters inference.
        pinyin = reading["alignment_pinyin"]
        if not s["pinyin_numeric"] or pinyin[:-1] != s["pinyin_numeric"][:-1]:
            raise ValueError("alignment_reading_disagreement")
        if not pinyin or not re.fullmatch(r"[a-zvü]+[1-5]", pinyin):
            raise ValueError("alignment_reading_unresolved")
        unit = {"index": s["index"], "hanzi": s["characters"], "corpus_pinyin": pinyin}
        token = alignment_token(unit)
        if token not in dictionary:
            raise ValueError("missing_pinned_pronunciation:" + pinyin)
        units.append(unit)
        lexicon[token] = dictionary[token]
    corpus = folder / "corpus/speaker"
    corpus.mkdir(parents=True)
    shutil.copyfile(audio, corpus / "take.wav")
    (corpus / "take.lab").write_text(" ".join(alignment_token(u) for u in units) + "\n")
    dictionary_path = folder / "read-units.dict"
    dictionary_path.write_text(
        "".join(
            token + "\t" + " ".join(phones) + "\n"
            for token, pronunciations in sorted(lexicon.items())
            for phones in pronunciations
        )
    )
    env = dict(os.environ)
    env["MFA_ROOT_DIR"] = str(folder / "work")
    env["PATH"] = str(PACKAGE / ".cache/mfa-env/bin") + os.pathsep + env.get("PATH", "")
    command = [
        str(PACKAGE / ".cache/mfa-env/bin/mfa"),
        "align",
        str(folder / "corpus"),
        str(dictionary_path),
        str(PACKAGE / ".cache/mfa-work/pretrained_models/acoustic/mandarin_mfa.zip"),
        str(folder / "aligned"),
        "--single_speaker",
        "--no_tokenization",
        "--num_jobs",
        "1",
        "--no_use_mp",
        "--no_use_postgres",
        "--textgrid_cleanup",
        "--output_format",
        "long_textgrid",
    ]
    write_json(folder / "command.json", {"argv": command, "speaker_adaptation": False})
    with (folder / "alignment.log").open("x") as log:
        subprocess.run(
            command, env=env, stdout=log, stderr=subprocess.STDOUT, check=True, timeout=180
        )
    diagnostics_file = folder / "aligned/alignment_analysis.csv"
    with diagnostics_file.open() as stream:
        diagnostics = list(csv.DictReader(stream))
    if len(diagnostics) != 1:
        raise ValueError("missing_alignment_diagnostics")
    grid = folder / "aligned/speaker/take.TextGrid"
    with wave.open(str(audio)) as stream:
        rate, frames = stream.getframerate(), stream.getnframes()
        pcm = stream.readframes(frames)
    utterance = {
        "utterance_id": folder.parent.name,
        "corpus": "Benma-dev-only",
        "speaker_id": "unidentified-live-speaker",
        "partition": "dev_only",
        "source_partition": "physical_smoke",
        "audio": {"reference": str(audio), "sha256": file_hash(audio)},
        "pcm_sha256": hashlib.sha256(pcm).hexdigest(),
        "duration": frames / rate,
        "transcript": "".join(s["characters"] for s in syllables),
        "transcript_provenance": "prompt_alignment_hypothesis",
        "prosody_status": "unknown",
        "units": units,
    }
    result = reconstruct(
        utterance,
        textgrid(grid.read_text()),
        lexicon,
        {
            "alignment_log_likelihood": float(diagnostics[0]["overall_log_likelihood"]),
            "textgrid_sha256": file_hash(grid),
        },
        read_json(PACKAGE / "configs/aishell3.json"),
    )
    write_json(folder / "units.json", result)
    return result


def crop(audio, interval, output):
    with wave.open(str(audio)) as stream:
        params = stream.getparams()
        stream.setpos(interval["start_sample"])
        pcm = stream.readframes(interval["end_sample"] - interval["start_sample"])
    with wave.open(str(output), "wb") as stream:
        stream.setparams(params)
        stream.writeframes(pcm)


class DevRuntime:
    def __init__(self, folder=DEFAULT_RUNS, *, enabled=False, asr=False):
        require_dev(enabled)
        self.folder = Path(folder).resolve()
        # Never permit an output root inside a historical research directory.
        if self.folder != DEFAULT_RUNS.resolve() and PACKAGE.resolve() in self.folder.parents:
            raise ValueError("use_default_dev_directory_or_output_outside_research_package")
        self.folder.mkdir(parents=True, exist_ok=True)
        self.recognizer = LearnedRecognizer(self.folder / "cache", enabled=enabled)
        self.asr = asr

    def take(self, recording, text="我想买这个", *, source_kind="physical_microphone"):
        if not re.fullmatch(r"[\u3400-\u4dbf\u4e00-\u9fff]{1,40}", text):
            raise ValueError("use_one_short_Hanzi_phrase")
        started = time.perf_counter()
        folder = self.folder / uuid.uuid4().hex
        folder.mkdir()
        source, audio = folder / "original.audio", folder / "canonical.wav"
        source.write_bytes(recording)
        prepared = service(
            {
                "action": "prepare",
                "source": str(source),
                "destination": str(audio),
                "text": text,
                "asr": self.asr,
            }
        )
        write_json(folder / "linguistic-and-asr.json", prepared)
        return self.analyze(
            audio, prepared, folder, text, started, source_kind, time.perf_counter() - started
        )

    def analyze(self, audio, prepared, folder, text, started, source_kind, prepare_seconds=0):
        syllables = prepared["syllables"]
        alignment_error = None
        phase = time.perf_counter()
        try:
            aligned = align(audio, syllables, folder / "alignment")
        except (ValueError, OSError, subprocess.SubprocessError, KeyError) as error:
            aligned = []
            alignment_error = "alignment_failure:" + (
                str(error) if isinstance(error, ValueError) else type(error).__name__
            )
        alignment_seconds = time.perf_counter() - phase
        return self.report(
            audio,
            prepared,
            aligned,
            folder,
            text,
            started,
            source_kind,
            alignment_error,
            alignment_seconds,
            prepare_seconds,
        )

    def report(
        self,
        audio,
        prepared,
        aligned,
        folder,
        text,
        started,
        source_kind,
        alignment_error=None,
        alignment_seconds=0,
        prepare_seconds=0,
    ):
        """Join text only after inference; this also supports saved-evidence regression tests."""
        report_started = time.perf_counter()
        encoder_reused = self.recognizer.encoder is not None
        learned_seconds = 0
        by_index = {r["index"]: r for r in aligned}
        usable = [
            r | {"source_id": folder.name}
            for r in aligned
            if r.get("start") is not None and not r.get("exclusion_reasons")
        ]
        phase = time.perf_counter()
        try:
            baseline = deterministic(usable, folder / "deterministic") if usable else {}
            acoustic_error = None
        except (OSError, subprocess.SubprocessError, ValueError) as error:
            baseline, acoustic_error = {}, "acoustic_failure:" + type(error).__name__
        acoustic_seconds = time.perf_counter() - phase
        asr = prepared["asr"]
        asr_mismatch = (
            asr.get("status") == "available"
            and re.sub(r"[^\u3400-\u4dbf\u4e00-\u9fff]", "", asr.get("transcript", "")) != text
        )
        rows = []
        for target in prepared["syllables"]:
            index = target["index"]
            alignment = by_index.get(index)
            base = baseline.get(alignment["example_id"], {}) if alignment else {}
            spans, contract, clips = None, None, {}
            reason = alignment_error or acoustic_error
            try:
                spans = project_spans(audio, alignment)
                contract, _ = span_contract(audio, alignment)
            except (ValueError, OSError, KeyError, wave.Error) as error:
                reason = reason or str(error)
            # Diagnostic playback survives an inference abstention on a short pool.
            if spans:
                for kind, key in (
                    ("whole", "playback_read_unit"),
                    ("tone", "tone_bearing_pooling_span"),
                    ("context", "context"),
                ):
                    name = f"unit-{index}-{kind}.wav"
                    if spans.get(key):
                        crop(audio, spans[key], folder / name)
                        clips[kind] = name
            if not reason and asr_mismatch:
                reason = "asr_prompt_mismatch_review_alignment"
            if not reason and target["expected_surface_tone"] == 0:
                reason = "neutral_outside_four_tone_model"
            if not reason:
                # Require retained voiced support within the pool, not just its neighbors.
                a, b = contract["pooling"]
                if not any(
                    a <= p["timestamp_seconds"] < b
                    for segment in base.get("segments", [])
                    for p in segment
                ):
                    reason = "no_voiced_support_in_tone_bearing_span"
            inference_started = time.perf_counter()
            predictions = (
                {"expanded": abstention(reason), "pilot": abstention(reason)}
                if reason
                else self.recognizer.infer(contract)
            )
            learned_seconds += time.perf_counter() - inference_started
            comparison = compare(
                target["expected_surface_tone"], predictions["expanded"], predictions["pilot"], base
            )
            heard = predictions["expanded"].get("prediction")
            numeric = target["pinyin_numeric"]
            rows.append(
                {
                    "index": index,
                    "target": target,
                    "heard": {
                        "learned_family": heard,
                        "confidence": predictions["expanded"].get("confidence"),
                    },
                    "expanded": predictions["expanded"],
                    "pilot": predictions["pilot"],
                    "deterministic": base or {"prediction": None, "reason": reason},
                    "alignment": alignment,
                    "spans": spans,
                    "clips": clips,
                    "comparison": comparison,
                    "tone_realization_numeric": numeric[:-1] + heard[-1]
                    if heard and numeric
                    else None,
                    "inference_seconds": predictions.get("inference_seconds"),
                }
            )
        rendered = service(
            {"action": "render", "pinyin": [r["tone_realization_numeric"] for r in rows]}
        )
        for row, marked in zip(rows, rendered, strict=True):
            row["tone_realization_rendering"] = marked
        chunks = []
        for chunk in prepared["chunks"]:
            members = [rows[i] for i in chunk["syllable_indices"]]
            bearing = [r for r in members if r["target"]["expected_surface_tone"] != 0]
            chunks.append(
                chunk
                | {
                    "constituent_states": [r["comparison"]["state"] for r in members],
                    "neutral_nonveto": True,
                    "grade": "unavailable"
                    if not bearing
                    or any(r["comparison"]["grade"] == "unavailable" for r in bearing)
                    else "experimental_mismatch"
                    if any(r["comparison"]["grade"] == "experimental_mismatch" for r in bearing)
                    else "experimental_match",
                }
            )
        report = {
            "version": "dev-learned-tone-v1",
            "take_id": folder.name,
            "source_kind": source_kind,
            "intended_phrase": text,
            "intended_pinyin": " ".join(s["pinyin"] or "?" for s in prepared["syllables"]),
            "tone_realization_rendering": " ".join(rendered),
            "rendering_label": "Tone-realization rendering — not ASR lexical transcription",
            "asr": asr,
            "asr_prompt_mismatch": asr_mismatch,
            "units": rows,
            "chunks": chunks,
            "alignment_error": alignment_error,
            "acoustic_error": acoustic_error,
            "audio_sha256": file_hash(audio),
            "production_grading_changed": False,
            "performance": self.recognizer.performance()
            | {
                "alignment_seconds": alignment_seconds,
                "prepare_seconds": prepare_seconds,
                "acoustic_seconds": acoustic_seconds,
                "encoder_reused": encoder_reused,
                "encoder_load_this_take_seconds": 0
                if encoder_reused
                else self.recognizer.encoder_load_seconds,
                "learned_seconds": learned_seconds,
                "report_generation_seconds": time.perf_counter()
                - report_started
                - acoustic_seconds
                - learned_seconds,
                "inference_and_reporting_seconds": time.perf_counter()
                - report_started
                - acoustic_seconds,
                "utterance_total_seconds": time.perf_counter() - started,
            },
            "verification": self.recognizer.verification,
            "caveats": [
                "Learner transfer remains unresolved; agreement is not ground truth.",
                "Confidence is raw argmax probability, not calibrated correctness.",
                "Automatic phone alignment is provisional; inspect crop playback.",
                "No confidence threshold or confident-error classification is established.",
                "A surprising take is diagnostic evidence, not a tuning target.",
            ],
        }
        write_json(folder / "report.json", report)
        return report
