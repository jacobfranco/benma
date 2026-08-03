"""Montreal Forced Aligner command adapter and TextGrid extraction."""

from __future__ import annotations

import re
import shutil
import subprocess
import tempfile
from pathlib import Path

from benchmark.models import AlignmentResult, AlignmentUnit, TimeSpan
from benchmark.providers.base import ForcedAligner, UnsupportedConfigurationError


def parse_textgrid(path: Path) -> tuple[AlignmentUnit, ...]:
    text = path.read_text(encoding="utf-8")
    pattern = re.compile(
        r"intervals \[\d+\]:\s*xmin = ([0-9.eE+-]+)\s*"
        r"xmax = ([0-9.eE+-]+)\s*text = \"(.*?)\"",
        re.DOTALL,
    )
    return tuple(
        AlignmentUnit(
            label=label.replace('\\"', '"'),
            span=TimeSpan(start_seconds=float(start), end_seconds=float(end)),
        )
        for start, end, label in pattern.findall(text)
        if label
    )


class MontrealForcedAligner(ForcedAligner):
    algorithm_name = "montreal_forced_aligner"
    algorithm_version = "runtime"

    def __init__(
        self,
        *,
        dictionary: str = "mandarin_mfa",
        acoustic_model: str = "mandarin_mfa",
    ) -> None:
        self.dictionary = dictionary
        self.acoustic_model = acoustic_model

    def align(self, audio_path: str, transcript: str) -> AlignmentResult:
        executable = shutil.which("mfa")
        if executable is None:
            raise UnsupportedConfigurationError(
                "MFA is not installed; see docs/benchmark/running.md for the isolated setup"
            )
        with tempfile.TemporaryDirectory(prefix="benma-mfa-") as temporary:
            root = Path(temporary)
            transcript_path = root / "target.txt"
            transcript_path.write_text(transcript, encoding="utf-8")
            output = root / "alignment.TextGrid"
            completed = subprocess.run(
                [
                    executable,
                    "align_one",
                    audio_path,
                    str(transcript_path),
                    self.dictionary,
                    self.acoustic_model,
                    str(output),
                    "--clean",
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            if completed.returncode != 0:
                raise UnsupportedConfigurationError(
                    f"MFA align_one failed: {completed.stderr[-800:]}",
                    code=str(completed.returncode),
                )
            units = parse_textgrid(output)
        warnings = () if units else ("MFA produced no non-empty intervals",)
        return AlignmentResult(
            algorithm=self.algorithm_name,
            algorithm_version=self.algorithm_version,
            words=units,
            confidence_proxy=None,
            warnings=warnings,
        )


class ReplayForcedAligner(ForcedAligner):
    algorithm_name = "replay_alignment"
    algorithm_version = "1.0.0"

    def __init__(self, result: AlignmentResult) -> None:
        self.result = result

    def align(self, audio_path: str, transcript: str) -> AlignmentResult:
        del audio_path, transcript
        return self.result
