"""Focused offline data-gate tests; no model, provider, or production code."""

import hashlib
import io
import json
import math
import struct
import tempfile
import unittest
import wave
from pathlib import Path
from unittest.mock import call, patch

import pilot
import report


def metadata(license="CC BY 2.0 fr", url="https://creativecommons.org/licenses/by/2.0/fr/deed.en"):
    return {"LicenseShortName": {"value": license}, "LicenseUrl": {"value": url}}


def page(text="八", reading="bā", license="CC BY 2.0 fr"):
    meta = metadata(license)
    meta.update(
        ImageDescription={"value": f'Pronunciation of "{reading}" ({text}) in Chinese.'},
        Artist={"value": "Wei Gao, Vion Nicolas"},
        Credit={"value": "The Shtooka Project"},
    )
    return {
        "pageid": 1,
        "title": "File:Zh-bā.ogg",
        "imageinfo": [
            {
                "extmetadata": meta,
                "sha1": "abc",
                "descriptionurl": "https://commons.wikimedia.org/wiki/File:Zh-bā.ogg",
            }
        ],
    }


class ToneTests(unittest.TestCase):
    def test_numbered_and_diacritic_tones(self):
        for value, expected in [
            ("mā", ("ma1", 1)),
            ("má", ("ma2", 2)),
            ("mǎ", ("ma3", 3)),
            ("mà", ("ma4", 4)),
            ("lü4", ("lü4", 4)),
            ("lv4", ("lü4", 4)),
            ("lǚ", ("lü3", 3)),
            ("ma5", ("ma5", 5)),
        ]:
            self.assertEqual(pilot.parse_pinyin(value), expected)

    def test_no_invented_tone(self):
        for value in ["ma", "ma6", "mā má", "ni3hao3", "你好", "mǎ̀"]:
            self.assertIsNone(pilot.parse_pinyin(value))

    def test_polyphone_not_first_reading(self):
        self.assertEqual(pilot.dictionary_reading("行")[1], "ambiguous_reading")

    def test_single_reading(self):
        self.assertEqual(pilot.dictionary_reading("妈"), (("ma1", 1), None))

    def test_phrase_deferred(self):
        self.assertEqual(pilot.dictionary_reading("你好")[1], "multi_syllable")

    def test_explicit_polyphone_resolved(self):
        row, reasons = pilot.normalize(page("行", "xíng"))
        self.assertEqual(reasons, [])
        self.assertEqual(row["tone"], 2)

    def test_conflicting_metadata_rejected(self):
        self.assertIn("metadata_dictionary_conflict", pilot.normalize(page("八", "bà"))[1])

    def test_neutral_excluded(self):
        self.assertIn("neutral_tone", pilot.normalize(page("们", "men5"))[1])

    def test_uploader_not_speaker(self):
        p = page()
        p["imageinfo"][0]["user"] = "UploadBot"
        p["imageinfo"][0]["extmetadata"]["Artist"] = {"value": "unknown"}
        row, reasons = pilot.normalize(p)
        self.assertIsNone(row["speaker_id"])
        self.assertIn("speaker_unknown", reasons)

    def test_location_is_not_native_status(self):
        p = page()
        p["imageinfo"][0]["extmetadata"]["ImageDescription"]["value"] += (
            " Speaker from Pekin, China."
        )
        self.assertEqual(pilot.normalize(p)[0]["speaker_native_status"], "UNKNOWN")


class FieldTests(unittest.TestCase):
    def test_empty_qualifier_does_not_consume_date(self):
        wiki = " | qualifier     = \n | date = 2025-11-20\n"
        self.assertEqual(pilot.field(wiki, "qualifier"), "")
        self.assertEqual(pilot.field(wiki, "date"), "2025-11-20")


class LicenseTests(unittest.TestCase):
    def test_by_accepted(self):
        self.assertEqual(pilot.license_policy(metadata())[0], "CC BY 2.0 fr")

    def test_wrong_license_link_rejected(self):
        self.assertIsNone(pilot.license_policy(metadata(url="https://example.org"))[0])

    def test_sharealike_not_nc_but_deferred(self):
        self.assertEqual(pilot.license_policy(metadata("CC BY-SA 4.0"))[2], "sharealike_deferred")

    def test_explicit_optional_cc0(self):
        wiki = "== {{int:license-header}} ==\n{{Multi-license}}\n{{cc-by-sa-4.0}}\n{{cc-0}}"
        self.assertEqual(pilot.license_policy(metadata("CC BY-SA 4.0"), wiki)[0], "CC0-1.0")

    def test_category_does_not_grant_cc0(self):
        m = metadata("CC BY-SA 4.0")
        m["Categories"] = {"value": "CC-Zero"}
        self.assertIsNone(pilot.license_policy(m)[0])

    def test_nc_nd_unknown_rejected(self):
        for value in ["CC BY-NC 4.0", "CC BY-ND 4.0", "Public domain", "unknown", "FAL"]:
            self.assertIsNone(pilot.license_policy(metadata(value))[0])


class RateLimitTests(unittest.TestCase):
    def test_long_retry_after_is_not_shortened(self):
        self.assertEqual(pilot.retry_seconds("600"), 600)

    def test_transient_429_honors_backoff(self):
        import urllib.error

        error = urllib.error.HTTPError(
            "https://upload.wikimedia.org/a", 429, "rate limit", {"Retry-After": "600"}, None
        )
        with tempfile.TemporaryDirectory() as tmp:
            response = io.BytesIO(b"abcd")
            response.headers = {"Content-Length": "4"}
            with (
                patch("pilot.urllib.request.urlopen", side_effect=[error, response]),
                patch("pilot.pause") as pause,
                patch("pilot.time.time", return_value=0),
            ):
                pilot.fetch_audio(
                    "https://upload.wikimedia.org/a", Path(tmp) / "a.wav", 4, pilot.Budget(1, 4)
                )
            pause.assert_has_calls([call(60), call(600)])

    def test_global_throttle_limit_and_persistent_cooldown(self):
        import urllib.error

        error = urllib.error.HTTPError(
            "https://upload.wikimedia.org/a", 429, "rate limit", {"Retry-After": "600"}, None
        )
        with tempfile.TemporaryDirectory() as tmp, patch("pilot.time.time", return_value=1000):
            state = Path(tmp) / "network-cooldown.json"
            pacing = pilot.DownloadPacing(state, delay=60, max_throttles=2)
            self.assertTrue(pacing.throttled(error))
            self.assertFalse(pacing.throttled(error))
            resumed = pilot.DownloadPacing(state, delay=60, max_throttles=2)
            with patch("pilot.pause") as pause:
                resumed.before_request()
            pause.assert_called_once_with(600)

    def test_pacing_parameter_bounds(self):
        for delay, limit in [(0, 2), (60, 0), (60, 4)]:
            with self.assertRaises(ValueError):
                pilot.DownloadPacing(delay=delay, max_throttles=limit)

    def test_http_date_retry(self):
        with patch("acquire.time.time", return_value=0):
            self.assertEqual(pilot.retry_seconds("Thu, 01 Jan 1970 00:10:00 GMT"), 601)


class ReadinessTests(unittest.TestCase):
    def test_small_balanced_pilot_is_only_smoke_ready(self):
        rows = [{"speaker_id": str(sid), "tone": tone} for sid in range(2) for tone in range(1, 5)]
        self.assertTrue(report.readiness(rows)["pipeline_smoke_ready"])
        self.assertFalse(report.readiness(rows)["exploratory_experiment_ready"])

    def test_total_count_cannot_replace_speaker_coverage(self):
        rows = [
            {"speaker_id": report.MEANINGFUL_SPEAKERS[0], "tone": i % 4 + 1} for i in range(400)
        ]
        self.assertFalse(report.readiness(rows)["exploratory_experiment_ready"])
        rows = [
            {"speaker_id": sid, "tone": i % 4 + 1}
            for sid in report.MEANINGFUL_SPEAKERS
            for i in range(80)
        ]
        self.assertTrue(report.readiness(rows)["exploratory_experiment_ready"])


class DownloadTests(unittest.TestCase):
    def test_hard_caps(self):
        for count, size in [(501, 1), (1, 1024**3 + 1), (-1, 1)]:
            with self.assertRaises(ValueError):
                pilot.Budget(count, size)

    def test_byte_and_count_caps(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "one.wav"
            budget = pilot.Budget(1, 4)
            pilot.bounded_copy(io.BytesIO(b"abcd"), target, 4, budget)
            self.assertEqual(target.read_bytes(), b"abcd")
            self.assertFalse(budget.allows(0))
            self.assertEqual((budget.files, budget.bytes), (1, 4))
            with self.assertRaises(ValueError):
                pilot.bounded_copy(io.BytesIO(b"a"), Path(tmp) / "two", 1, budget)

    def test_short_read_charged_and_partial_removed(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "one.wav"
            budget = pilot.Budget(1, 4)
            with self.assertRaises(ValueError):
                pilot.bounded_copy(io.BytesIO(b"ab"), target, 4, budget)
            self.assertFalse(target.exists())
            self.assertFalse(list(Path(tmp).glob("*.part")))
            self.assertEqual((budget.files, budget.bytes), (1, 2))

    def test_resume_budget(self):
        budget = pilot.Budget(500, 1024**3, used_files=500, used_bytes=5)
        self.assertFalse(budget.allows(1))

    def test_diagnostics_and_pcm_dedupe(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "a.wav"
            samples = [round(10000 * math.sin(2 * math.pi * 200 * i / 16000)) for i in range(1600)]
            with wave.open(str(path), "wb") as out:
                out.setparams((1, 2, 16000, 0, "NONE", "not compressed"))
                out.writeframes(struct.pack("<" + "h" * len(samples), *samples))
            d = pilot.diagnostics(path)
            self.assertEqual(d["sample_rate_hz"], 16000)
            self.assertAlmostEqual(d["duration_seconds"], 0.1)
            self.assertEqual(d["channels"], 1)
            self.assertEqual(d["clipping_percentage"], 0)
            self.assertGreater(d["rms"], 0.2)
            copy = Path(tmp) / "b.wav"
            copy.write_bytes(path.read_bytes())
            self.assertEqual(d["decoded_pcm_sha256"], pilot.diagnostics(copy)["decoded_pcm_sha256"])

    def test_manifest_and_duplicate_rejection_offline(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache = Path(tmp)
            (cache / "audio").mkdir()
            rows = []
            for ident in [1, 2]:
                row, _ = pilot.normalize(page())
                row.update(
                    source_asset_id=f"commons:{ident}",
                    source_bytes=4,
                    source_sha1=hashlib.sha1(b"abcd").hexdigest(),
                    title="File:sample.wav",
                )
                (cache / "audio" / f"commons-{ident}.wav").write_bytes(b"abcd")
                rows.append(row)
            pilot.write_jsonl(cache / "selected.jsonl", rows)
            diagnostic = {
                "duration_seconds": 1.0,
                "sample_rate_hz": 16000,
                "channels": 1,
                "rms": 0.1,
                "peak_level": 0.4,
                "clipping_percentage": 0,
                "silence_ratio": 0,
                "decode_success": True,
                "decoded_pcm_sha256": "a" * 64,
                "embedded_tags": {},
            }
            with patch.object(pilot, "diagnostics", return_value=diagnostic):
                pilot.download(cache, cache / "out", offline=True)
            manifest = [
                json.loads(x) for x in (cache / "out/pilot-manifest.jsonl").read_text().splitlines()
            ]
            self.assertEqual(len(manifest), 1)
            pilot.validate(manifest[0])
            self.assertIn("duplicate_audio", (cache / "download-rejected.jsonl").read_text())
            del manifest[0]["tone"]
            with self.assertRaises(ValueError):
                pilot.validate(manifest[0])

    def test_network_stop_preserves_later_cached_files(self):
        import urllib.error

        with tempfile.TemporaryDirectory() as tmp:
            cache = Path(tmp)
            (cache / "audio").mkdir()
            rows = []
            for ident in [1, 2, 3]:
                row, _ = pilot.normalize(page())
                row.update(
                    source_asset_id=f"commons:{ident}",
                    source_bytes=4,
                    source_sha1=hashlib.sha1(b"abcd").hexdigest(),
                    title="File:sample.wav",
                    audio_url="https://upload.wikimedia.org/sample.wav",
                )
                rows.append(row)
            (cache / "audio/commons-2.wav").write_bytes(b"abcd")
            pilot.write_jsonl(cache / "selected.jsonl", rows)
            diagnostic = {
                "duration_seconds": 1.0,
                "sample_rate_hz": 16000,
                "channels": 1,
                "rms": 0.1,
                "peak_level": 0.4,
                "clipping_percentage": 0,
                "silence_ratio": 0,
                "decode_success": True,
                "decoded_pcm_sha256": "a" * 64,
                "embedded_tags": {},
            }
            with (
                patch.object(pilot, "diagnostics", return_value=diagnostic),
                patch.object(
                    pilot, "fetch_audio", side_effect=urllib.error.URLError("rate limited")
                ) as fetch,
            ):
                pilot.download(cache, cache / "out")
            fetch.assert_called_once()
            manifest = report.rows(cache / "out/pilot-manifest.jsonl")
            self.assertEqual([r["source_asset_id"] for r in manifest], ["commons:2"])
            summary = json.loads((cache / "out/pilot-summary.json").read_text())
            self.assertIsNotNone(summary["acquisition_stopped_reason"])


if __name__ == "__main__":
    unittest.main()
