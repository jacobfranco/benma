from __future__ import annotations

from pathlib import Path

import pytest
from conftest import write_wav

from benchmark.audio import import_recording, inspect_wav, normalize_to_canonical, sha256_file


def test_normalization_converts_rate_channels_and_width(tmp_path: Path) -> None:
    source = write_wav(tmp_path / "stereo.wav", rate=44100, channels=2, duration=0.25)
    destination = tmp_path / "canonical.wav"
    info = normalize_to_canonical(source, destination)
    assert info.sample_rate_hz == 16000
    assert info.channels == 1
    assert info.sample_width_bits == 16
    assert info.duration_seconds == pytest.approx(0.25, abs=0.02)


def test_import_preserves_original_bytes(tmp_path: Path) -> None:
    source = write_wav(tmp_path / "source.wav", rate=22050, channels=2)
    original_hash = sha256_file(source)
    asset = import_recording(source, sample_id="sample_1", recordings_root=tmp_path / "recordings")
    assert asset.original_asset_path
    assert sha256_file(asset.original_asset_path) == original_hash
    assert asset.original_asset_path != asset.asset_path
    assert asset.sha256 == sha256_file(asset.asset_path)
    assert inspect_wav(asset.asset_path).sample_rate_hz == 16000


def test_import_refuses_to_overwrite_original(tmp_path: Path) -> None:
    source = write_wav(tmp_path / "source.wav")
    root = tmp_path / "recordings"
    import_recording(source, sample_id="sample_1", recordings_root=root)
    with pytest.raises(FileExistsError):
        import_recording(source, sample_id="sample_1", recordings_root=root)


def test_normalization_rejects_empty_file(tmp_path: Path) -> None:
    source = tmp_path / "empty.wav"
    source.touch()
    with pytest.raises(ValueError, match="empty"):
        normalize_to_canonical(source, tmp_path / "out.wav")
