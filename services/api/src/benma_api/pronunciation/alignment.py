"""Optional forced-alignment boundary with normalized, sanity-checked evidence."""

from __future__ import annotations

import re
import shutil
import subprocess
import tempfile
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from sqlalchemy import select
from sqlalchemy.orm import Session

from benma_api.config import Settings
from benma_api.db.models import (
    AlignmentRun,
    AudioAsset,
    PronunciationAttempt,
    PronunciationTarget,
    Utterance,
)
from benma_api.errors import AnalysisUnsupportedError, AuthorizationError
from benma_api.pronunciation.service import target_snapshot
from benma_api.storage.audio_store import AudioObjectStore


@dataclass(frozen=True, slots=True)
class AlignmentRequest:
    audio_path: Path
    target_text: str
    pinyin_syllables: list[str]
    duration_seconds: float
    timeout_seconds: float


@dataclass(frozen=True, slots=True)
class AlignmentResponse:
    units: list[dict[str, Any]]
    raw_result: dict[str, Any] | None
    evidence_status: str


class AlignmentPort(Protocol):
    algorithm_name: str
    algorithm_version: str

    def align(self, request: AlignmentRequest) -> AlignmentResponse: ...


class DisabledAligner:
    algorithm_name = "disabled"
    algorithm_version = "1.0.0"

    def align(self, request: AlignmentRequest) -> AlignmentResponse:
        del request
        raise AnalysisUnsupportedError("syllable alignment is not configured")


class ReplayAligner:
    algorithm_name = "replay_duration_partition"
    algorithm_version = "1.0.0"

    def align(self, request: AlignmentRequest) -> AlignmentResponse:
        count = len(request.pinyin_syllables)
        width = request.duration_seconds / count if count else 0
        units = [
            {
                "label": label,
                "syllable_index": index,
                "start_seconds": round(index * width, 4),
                "end_seconds": round((index + 1) * width, 4),
                "confidence": None,
            }
            for index, label in enumerate(request.pinyin_syllables)
        ]
        return AlignmentResponse(
            units=units,
            raw_result={"synthetic": True, "method": "equal duration partition"},
            evidence_status="synthetic_replay",
        )


def parse_textgrid(text: str) -> list[dict[str, Any]]:
    pattern = re.compile(
        r"intervals \[\d+\]:\s*xmin = ([0-9.eE+-]+)\s*"
        r'xmax = ([0-9.eE+-]+)\s*text = "(.*?)"',
        re.DOTALL,
    )
    return [
        {
            "label": label.replace('\\"', '"'),
            "start_seconds": float(start),
            "end_seconds": float(end),
            "confidence": None,
        }
        for start, end, label in pattern.findall(text)
        if label.strip()
    ]


class MontrealForcedAligner:
    algorithm_name = "montreal_forced_aligner_align_one_legacy"

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        executable = shutil.which(settings.mfa_binary)
        self.executable = executable or settings.mfa_binary
        self.algorithm_version = self._version() if executable else "unavailable"

    def _version(self) -> str:
        try:
            completed = subprocess.run(
                [self.executable, "version"],
                check=True,
                capture_output=True,
                text=True,
                timeout=10,
            )
            return completed.stdout.strip().splitlines()[-1][:64] or "unknown"
        except (OSError, subprocess.SubprocessError, IndexError):
            return "unknown"

    def align(self, request: AlignmentRequest) -> AlignmentResponse:
        if shutil.which(self.settings.mfa_binary) is None:
            raise AnalysisUnsupportedError("MFA is not installed")
        with tempfile.TemporaryDirectory(prefix="benma-mfa-") as temporary:
            root = Path(temporary)
            transcript = root / "target.txt"
            transcript.write_text(request.target_text, encoding="utf-8")
            output = root / "alignment.TextGrid"
            try:
                completed = subprocess.run(
                    [
                        self.executable,
                        "align_one",
                        str(request.audio_path),
                        str(transcript),
                        self.settings.mfa_dictionary,
                        self.settings.mfa_acoustic_model,
                        str(output),
                        "--clean",
                    ],
                    check=False,
                    capture_output=True,
                    text=True,
                    timeout=min(request.timeout_seconds, self.settings.mfa_timeout_seconds),
                )
            except subprocess.TimeoutExpired as exc:
                raise AnalysisUnsupportedError("MFA alignment timed out") from exc
            except OSError as exc:
                raise AnalysisUnsupportedError("MFA could not be started") from exc
            if completed.returncode != 0 or not output.exists():
                raise AnalysisUnsupportedError(
                    f"MFA alignment failed with code {completed.returncode}"
                )
            text = output.read_text(encoding="utf-8")
            units = parse_textgrid(text)
        return AlignmentResponse(
            units=units,
            raw_result={"textgrid": text, "stderr_tail": completed.stderr[-800:]},
            evidence_status="live_tool",
        )


def validate_alignment(
    units: list[dict[str, Any]], *, target_count: int, duration_seconds: float
) -> dict[str, Any]:
    issues: list[str] = []
    if not units:
        issues.append("missing_target_units")
    if len(units) != target_count:
        issues.append("target_unit_count_mismatch")
    previous_end = 0.0
    for unit in units:
        start = float(unit["start_seconds"])
        end = float(unit["end_seconds"])
        if start < 0 or end < start:
            issues.append("impossible_duration")
        if start < previous_end - 0.001:
            issues.append("boundary_overlap")
        if end - start > 3.0:
            issues.append("extreme_duration")
        if end > duration_seconds + 0.05:
            issues.append("alignment_beyond_audio")
        previous_end = max(previous_end, end)
    covered = sum(
        max(0.0, float(item["end_seconds"]) - float(item["start_seconds"])) for item in units
    )
    if duration_seconds > 0 and covered / duration_seconds < 0.35:
        issues.append("excessive_unaligned_audio")
    issues = list(dict.fromkeys(issues))
    return {
        "quality": "invalid" if issues else "raw_evidence",
        "issues": issues,
        "usable_for_syllable_visualization": not issues,
        "capability_state": "raw_evidence",
    }


def build_aligner(settings: Settings) -> AlignmentPort:
    if settings.alignment_provider == "replay":
        return ReplayAligner()
    if settings.alignment_provider == "mfa":
        return MontrealForcedAligner(settings)
    return DisabledAligner()


class AlignmentService:
    def __init__(self, db: Session, store: AudioObjectStore, aligner: AlignmentPort) -> None:
        self.db = db
        self.store = store
        self.aligner = aligner

    def run(
        self, *, account_id: uuid.UUID, attempt_id: uuid.UUID, reuse: bool = True
    ) -> AlignmentRun:
        attempt = self.db.get(PronunciationAttempt, attempt_id)
        if attempt is None or attempt.account_id != account_id:
            raise AuthorizationError("pronunciation attempt was not found")
        if reuse:
            existing = self.db.scalar(
                select(AlignmentRun)
                .where(
                    AlignmentRun.account_id == account_id,
                    AlignmentRun.pronunciation_attempt_id == attempt_id,
                    AlignmentRun.algorithm == self.aligner.algorithm_name,
                    AlignmentRun.algorithm_version == self.aligner.algorithm_version,
                    AlignmentRun.status == "succeeded",
                )
                .order_by(AlignmentRun.created_at.desc())
            )
            if existing is not None:
                return existing
        target = self.db.get(PronunciationTarget, attempt.target_id)
        utterance = self.db.get(Utterance, attempt.utterance_id)
        if target is None or utterance is None:
            raise AuthorizationError("attempt evidence was not found")
        asset = self.db.get(AudioAsset, utterance.canonical_audio_asset_id)
        if asset is None or asset.duration_seconds is None:
            raise AuthorizationError("canonical audio was not found")
        snapshot = target_snapshot(target)
        started = time.perf_counter()
        try:
            response = self.aligner.align(
                AlignmentRequest(
                    audio_path=self.store.path_for_processing(asset.storage_key),
                    target_text=target.text,
                    pinyin_syllables=target.pinyin_syllables,
                    duration_seconds=asset.duration_seconds,
                    timeout_seconds=45.0,
                )
            )
            quality = validate_alignment(
                response.units,
                target_count=len(target.pinyin_syllables),
                duration_seconds=asset.duration_seconds,
            )
            normalized = {
                "units": response.units,
                "quality": quality,
                "evidence_status": response.evidence_status,
            }
            run = AlignmentRun(
                account_id=account_id,
                utterance_id=utterance.id,
                pronunciation_attempt_id=attempt_id,
                target_snapshot=snapshot,
                algorithm=self.aligner.algorithm_name,
                algorithm_version=self.aligner.algorithm_version,
                normalized_result=normalized,
                raw_result=response.raw_result,
                quality=quality["quality"],
                latency_ms=round((time.perf_counter() - started) * 1000),
                status="succeeded",
            )
        except AnalysisUnsupportedError as exc:
            run = AlignmentRun(
                account_id=account_id,
                utterance_id=utterance.id,
                pronunciation_attempt_id=attempt_id,
                target_snapshot=snapshot,
                algorithm=self.aligner.algorithm_name,
                algorithm_version=self.aligner.algorithm_version,
                quality="unavailable",
                latency_ms=round((time.perf_counter() - started) * 1000),
                status="failed",
                error_code=exc.code,
                error_message=exc.message,
            )
        self.db.add(run)
        self.db.commit()
        return run
