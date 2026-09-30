"""Focused model-free acquisition and seal invariants, using synthetic fixtures."""

import hashlib
import json
import random
from unittest.mock import patch

import evaluation_preflight as preflight
import pytest
from evaluation_preflight import (
    BLOCKED_IDS,
    FIELDS,
    blocked,
    choose,
    commons_row,
    csv_bytes,
    immutable_write,
    temporal_bin_boundaries,
    validate_final,
    verify_source,
)


def item(index=1, **changes):
    return {
        **dict.fromkeys(FIELDS, "fixture"),
        "source": "lingua_libre_commons",
        "source_asset_id": f"commons:{index}",
        "speaker_id": "lingualibre:new",
        "speaker_name": "New speaker",
        "tone": 1,
        "pinyin": "ma1",
        "text": f"target{index}",
        "metadata_status": "eligible",
        "exclusions": "",
        "native_status_evidence": "",
        "audio_sha256": f"audio{index}",
        "source_sha1": f"source{index}",
        "decoded_pcm_sha256": f"pcm{index}",
        **changes,
    }


def pool():
    return [item(t * 100 + n, tone=t) for t in range(1, 5) for n in range(12)]


def test_order_independent_selection_and_serialization():
    rows = pool()
    expected = choose(rows)
    assert len(expected) == 40
    random.Random(42).shuffle(rows)
    assert choose(rows) == expected
    assert csv_bytes(rows) == csv_bytes(reversed(rows))
    assert b"\r\n" not in csv_bytes(rows)


def test_sparse_cell_retained_without_replacement():
    rows = [r for r in pool() if not (r["tone"] == 2 and int(r["source_asset_id"][-2:]) > 8)]
    assert len(choose(rows)) == 39
    rows = [r for r in rows if not (r["tone"] == 2 and int(r["source_asset_id"][-2:]) > 6)]
    assert choose(rows) == set()


@pytest.mark.parametrize("speaker", sorted(BLOCKED_IDS))
def test_all_prior_speakers_cannot_enter_final_manifest(speaker):
    row = item(speaker_id=speaker)
    assert blocked(row)
    assert choose([dict(r, speaker_id=speaker) for r in pool()]) == set()
    with pytest.raises(ValueError, match="Speaker overlaps"):
        validate_final([row], [])


@pytest.mark.parametrize("alias", ["Wei Gao", "CanonNi", "Levi_Highway", "Luilui6666"])
def test_names_block_alias_with_different_profile_id(alias):
    assert blocked(item(speaker_name=alias))


def test_prior_corpus_extra_speaker_blocked_dynamically():
    with pytest.raises(ValueError, match="Speaker overlaps"):
        validate_final([item()], [{"speaker_id": "lingualibre:new"}])


@pytest.mark.parametrize(
    "key", ["source_asset_id", "audio_sha256", "source_sha1", "decoded_pcm_sha256"]
)
def test_duplicate_keys_within_panel_and_across_previous(key):
    row = item()
    with patch("evaluation_preflight.digest", return_value=row["audio_sha256"]):
        with pytest.raises(ValueError, match="Duplicate"):
            validate_final([row, item(2, **{key: row[key]})], [])
        with pytest.raises(ValueError, match="Duplicate"):
            validate_final([row], [{"speaker_id": "other", key: row[key]}])


def test_duplicate_speaker_target_metadata():
    row = item()
    with (
        patch("evaluation_preflight.digest", return_value=row["audio_sha256"]),
        pytest.raises(ValueError, match="Duplicate speaker-target"),
    ):
        validate_final([row, item(2, text=row["text"])], [])


@pytest.mark.parametrize("tone", [0, 5, "", "1.0", "T3"])
def test_only_tones_one_through_four(tone):
    with pytest.raises(ValueError):
        validate_final([item(tone=tone)], [])


@pytest.mark.parametrize(
    "key",
    [
        "source_url",
        "speaker_id",
        "license_evidence_url",
        "label_source",
        "audio_sha256",
        "duration_seconds",
        "attribution",
    ],
)
def test_required_provenance(key):
    with pytest.raises(ValueError, match="Missing required provenance"):
        validate_final([item(**{key: ""})], [])


def test_ambiguous_items_cannot_be_selected_or_sealed():
    rows = [dict(r, metadata_status="excluded", exclusions="ambiguous_reading") for r in pool()]
    assert choose(rows) == set()
    with pytest.raises(ValueError, match="Ambiguous/excluded"):
        validate_final([rows[0]], [])


def test_prediction_values_are_never_read():
    class Poison(dict):
        def __getitem__(self, key):
            if key in {"prediction", "v1_prediction", "probabilities", "correct"}:
                raise AssertionError("Prediction accessed")
            return super().__getitem__(key)

        def get(self, key, default=None):
            return self[key] if key in self else default  # noqa: SIM401

    rows = [
        Poison(
            r, prediction=object(), probabilities=object(), v1_prediction=object(), correct=object()
        )
        for r in pool()
    ]
    assert choose(rows) == choose(pool())
    assert csv_bytes(rows) == csv_bytes(pool())


def test_source_integrity_supports_git_blob_and_raw_sha1():
    data = b"original wave fixture"
    verify_source(
        {
            "source": "commons",
            "source_bytes": len(data),
            "source_sha1": hashlib.sha1(data).hexdigest(),
        },
        data,
    )
    blob = b"blob " + str(len(data)).encode() + b"\0" + data
    row = {
        "source": "OMPAL",
        "source_bytes": len(data),
        "source_sha1": hashlib.sha1(blob).hexdigest(),
    }
    verify_source(row, data)
    with pytest.raises(ValueError, match="Source size/hash"):
        verify_source(row, data + b"changed")


def test_seal_cannot_be_replaced(tmp_path):
    path = tmp_path / "sealed.csv"
    immutable_write(path, b"original\n")
    immutable_write(path, b"original\n")
    with pytest.raises(FileExistsError):
        immutable_write(path, b"changed\n")
    assert path.read_bytes() == b"original\n"


def test_valid_panel_checks_local_audio_hash():
    with patch("evaluation_preflight.digest", return_value="audio1"):
        validate_final([item()], [])
    with (
        patch("evaluation_preflight.digest", return_value="changed"),
        pytest.raises(ValueError, match="Local audio changed"),
    ):
        validate_final([item()], [])


def page(text="你", name="New speaker", license_name="CC BY-SA 4.0"):
    wiki = (
        "{{Lingua Libre record\n | speaker = " + name + "\n | speakerId = QNEW\n"
        " | languageId = Q9192\n | transcription = " + text + "\n | qualifier = \n}}\n"
        "== {{int:license-header}} ==\n{{cc-by-sa-4.0}}"
    )
    return {
        "pageid": 1,
        "title": f"File:LL-Q9192 (cmn)-{name}-{text}.wav",
        "revisions": [{"revid": 123, "slots": {"main": {"*": wiki}}}],
        "imageinfo": [
            {
                "url": "https://example.org/a.wav",
                "size": 100,
                "sha1": "hash",
                "descriptionurl": "https://example.org/a",
                "extmetadata": {
                    "Artist": {"value": f"Speaker: {name}"},
                    "LicenseShortName": {"value": license_name},
                    "LicenseUrl": {"value": "https://creativecommons.org/licenses/by-sa/4.0"},
                },
            }
        ],
    }


def test_real_normalizer_excludes_polyphones_and_preserves_unknown_native():
    row = commons_row(page(), True)
    assert row["metadata_status"] == "eligible"
    assert row["pinyin"] == "ni3" and row["tone"] == 3
    assert row["speaker_native_status"] == "UNKNOWN"
    assert "ambiguous_reading" in commons_row(page("行"), True)["exclusions"]
    assert "sharealike_deferred" in commons_row(page(), False)["exclusions"]


def test_contradictory_filename_rejected():
    value = page()
    value["title"] = "File:LL-Q9192 (cmn)-Different-你.wav"
    assert "filename_template_conflict" in commons_row(value, True)["exclusions"]


def stage_fixture(tmp_path):
    output, cache = tmp_path / "out", tmp_path / "cache"
    output.mkdir()
    cache.mkdir()
    rows = [item(audio_sha256="", selection_status="selected_before_acquisition")]
    data = csv_bytes(rows)
    (output / "candidate-items.csv").write_bytes(data)
    (output / "protocol.md").write_text("fixed protocol\n")
    (output / "selection.json").write_text(
        json.dumps(
            {
                "candidate_items_sha256_before_acquisition": hashlib.sha256(data).hexdigest(),
                "selected_ids": [rows[0]["source_asset_id"]],
            }
        )
    )
    return output, cache


def test_incomplete_downloads_leave_unsealed_without_fake_manifest(tmp_path):
    output, cache = stage_fixture(tmp_path)
    with (
        patch.object(preflight, "OUT", output),
        patch.object(preflight, "CACHE", cache),
        patch.object(preflight, "summaries"),
    ):
        preflight.seal()
        record = json.loads((output / "preflight-status.json").read_text())
        assert record["status"] == "BLOCKED_NO_TRUSTWORTHY_COMPLETE_SET"
        assert record["n"] == 0
        assert record["manifest_sha256"] is None
        assert not (output / "sealed-test-manifest.csv").exists()
        assert not (output / "seal.json").exists()
        with pytest.raises(RuntimeError, match="No sealed evaluation manifest"):
            preflight.verify()


def test_editing_selection_metadata_before_seal_is_rejected(tmp_path):
    output, cache = stage_fixture(tmp_path)
    with (output / "candidate-items.csv").open("a") as handle:
        handle.write("changed\n")
    with (
        patch.object(preflight, "OUT", output),
        patch.object(preflight, "CACHE", cache),
        pytest.raises(ValueError, match="metadata changed"),
    ):
        preflight.seal()
    assert not (output / "sealed-test-manifest.csv").exists()


def test_corrupt_download_is_never_saved(tmp_path):
    row = item(
        source_bytes=3,
        source_sha1=hashlib.sha1(b"wav").hexdigest(),
        audio_url="https://upload.wikimedia.org/wikipedia/commons/a.wav",
    )
    from unittest.mock import MagicMock

    response = MagicMock()
    response.__enter__.return_value.read.return_value = b"BAD"
    destination = tmp_path / "bad.wav"
    with (
        patch("evaluation_preflight.urllib.request.urlopen", return_value=response),
        pytest.raises(ValueError, match="Source size/hash"),
    ):
        preflight.download(row, destination)
    assert not destination.exists()


@pytest.mark.parametrize(
    "n,expected",
    [
        (3, (0, 1, 2, 3)),
        (4, (0, 1, 2, 4)),
        (5, (0, 1, 3, 5)),
        (7, (0, 2, 4, 7)),
    ],
)
def test_temporal_floor_boundaries_match_frozen_protocol(n, expected):
    assert temporal_bin_boundaries(n) == expected


@pytest.mark.parametrize("n", [-1, 0, 1, 2, 3.0, True])
def test_temporal_short_or_invalid_sequences_stop_both_arms(n):
    with pytest.raises(ValueError, match="three valid frames"):
        temporal_bin_boundaries(n)


def test_temporal_bins_cover_valid_frames_once_and_preserve_chronology():
    for n in range(3, 1000):
        boundaries = temporal_bin_boundaries(n)
        bins = [list(range(boundaries[j], boundaries[j + 1])) for j in range(3)]
        assert all(bins)
        assert [i for part in bins for i in part] == list(range(n))
        assert max(map(len, bins)) - min(map(len, bins)) <= 1


def test_synthetic_masked_frames_are_gathered_before_binning():
    # No actual audio, encoder or model. Padding values cannot affect the thirds.
    hidden = [1, 999, 3, 5, 999, 7, 9]
    mask = [True, False, True, True, False, True, True]
    valid = [value for value, keep in zip(hidden, mask, strict=True) if keep]
    bounds = temporal_bin_boundaries(len(valid))
    means = [sum(valid[bounds[j] : bounds[j + 1]]) / (bounds[j + 1] - bounds[j]) for j in range(3)]
    assert means == [1, 4, 8]
