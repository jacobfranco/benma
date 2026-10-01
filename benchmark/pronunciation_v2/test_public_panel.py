"""Metadata/byte fixtures only; no model imports, inference, or candidate listening."""

import ast
import copy
import hashlib
import io
import json
import tempfile
import unittest
import zipfile
from collections import Counter
from pathlib import Path
from unittest.mock import patch

import public_panel as panel

TOKENS = (
    "妈花天山书飞星秋冬风",
    "茶鱼牛门云河田龙羊梨",
    "马米水狗五你我奶口手",
    "爸四字电树菜瘦快问唱",
)


def fixtures(speakers=3):
    rows = []
    for speaker in range(speakers):
        for tone, tokens in enumerate(TOKENS, 1):
            for text in tokens:
                reading, reason = panel.dictionary_reading(text)
                assert not reason and reading[1] == tone
                asset = f"fixture:{speaker}:{text}"
                row = dict.fromkeys(panel.REQUIRED, "fixture")
                row.update(
                    source_asset_id=asset,
                    speaker_id=f"test:{speaker}",
                    speaker_name=f"Participant {speaker}",
                    text=text,
                    pinyin=reading[0],
                    tone=str(tone),
                    metadata_status="eligible",
                    exclusions="",
                    license="CC BY 4.0",
                    license_url=panel.LICENSE,
                    local_path="fixture.wav",
                )
                for key in (
                    "audio_sha256",
                    "source_sha256",
                    "source_sha1",
                    "decoded_pcm_sha256",
                    "evaluation_pcm_sha256",
                ):
                    row[key] = hashlib.sha256((asset + key).encode()).hexdigest()
                rows.append(row)
    return rows


class SelectionTests(unittest.TestCase):
    def test_deterministic_enumeration_and_selection(self):
        rows = fixtures(4)
        self.assertEqual(panel.choose(rows), panel.choose(list(reversed(rows))))
        self.assertEqual(len(panel.choose(rows)), 160)
        self.assertEqual(len({r["speaker_id"] for r in panel.choose(rows)}), 4)

    def test_exact_hash_rank(self):
        rows = fixtures()
        chosen = panel.choose(rows)
        first = [r for r in rows if r["speaker_id"] == "test:0" and r["tone"] == "1"]
        expected = sorted(
            first,
            key=lambda r: (
                hashlib.sha256(r["source_asset_id"].encode()).hexdigest(),
                r["source_asset_id"],
            ),
        )
        self.assertEqual(chosen[:10], expected)

    def test_only_t1_t4(self):
        for tone in ("0", "5", "6", ""):
            rows = fixtures()
            rows[0]["tone"] = tone
            with self.assertRaises(ValueError):
                panel.choose(rows)

    def test_conservative_readings(self):
        for text in ("车", "灯", "雨", "的", "ma", "妈妈", "\u3007"):
            rows = fixtures()
            rows[0]["text"] = text
            with self.assertRaises(ValueError):
                panel.choose(rows)

    def test_previous_names_and_ids(self):
        for name in (
            "Wei Gao",
            "CanonNi",
            "Levi Highway",
            "Luilui6666",
            "Jouketou",
            "雲角",
            "Fake estate",
            "Xudong Yang",
            "wyverald",
            "Wang Cheng",
            "Jun Da",
            "Yue Tan",
        ):
            row = fixtures()[0]
            row["speaker_name"] = name
            self.assertTrue(panel.blocked(row))
        for speaker in panel.PRIOR_IDS:
            row["speaker_name"], row["speaker_id"] = "unrelated display name", speaker
            self.assertTrue(panel.blocked(row))

    def test_history_disjointness(self):
        rows = fixtures()
        self.assertEqual(panel.choose(rows, [{"speaker_id": "test:0"}]), [])
        with self.assertRaises(ValueError):
            panel.validate_final(rows, [{"speaker_name": "Participant 0"}])

    def test_minimum_per_tone_and_speakers(self):
        rows = fixtures()
        for remove in (2, 3):
            reduced = rows[remove:]
            self.assertEqual(bool(panel.choose(reduced)), remove == 2)
        self.assertEqual(panel.choose(fixtures(2)), [])

    def test_prediction_fields_are_ignored(self):
        rows = fixtures()
        expected = panel.choose(rows)
        changed = copy.deepcopy(rows)
        for row in changed:
            row.update(prediction=object(), confidence=object(), f0=object(), correct=object())
        self.assertEqual(
            [r["source_asset_id"] for r in expected],
            [r["source_asset_id"] for r in panel.choose(changed)],
        )

    def test_duplicate_source_id(self):
        rows = fixtures()
        with self.assertRaises(ValueError):
            panel.choose([*rows, rows[0]])

    def test_duplicate_audio_and_pcm(self):
        for key in ("audio_sha256", "source_sha1", "decoded_pcm_sha256", "evaluation_pcm_sha256"):
            rows = fixtures()
            rows[1][key] = rows[0][key]
            with self.assertRaises(ValueError):
                panel.validate_final(rows, [])
            with self.assertRaises(ValueError):
                panel.validate_final(fixtures(), [{key: fixtures()[0][key]}])

    def test_required_provenance_license(self):
        for key in panel.REQUIRED:
            rows = fixtures()
            rows[0][key] = ""
            with self.assertRaises(ValueError, msg=key):
                panel.pool(rows)
        rows = fixtures()
        rows[0]["license"] = "CC BY-NC 4.0"
        with self.assertRaises(ValueError):
            panel.validate_final(rows, [])

    def test_no_seal_overwrite(self):
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp) / "panel"
            panel.exclusive_seal(out, {"sealed-test-manifest.csv": b"original"}, {"n": 1})
            with self.assertRaises(FileExistsError):
                panel.exclusive_seal(out, {"sealed-test-manifest.csv": b"changed"}, {"n": 2})
            self.assertEqual((out / "sealed-test-manifest.csv").read_bytes(), b"original")

    def test_no_raw_audio_staged(self):
        with (
            patch("evaluation_preflight.subprocess.check_output", return_value=b"file.wav\0"),
            self.assertRaises(ValueError),
        ):
            panel.check_no_staged_audio()
        panel.check_no_staged_audio()

    def test_no_model_dependencies(self):
        tree = ast.parse(Path(panel.__file__).read_text())
        forbidden = {"torch", "transformers", "features", "nonlinear_head", "model_probe"}
        imported = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name.split(".")[0] for alias in node.names)
            if isinstance(node, ast.ImportFrom):
                imported.add(node.module.split(".")[0])
        self.assertFalse(imported & forbidden)


class ArchiveTests(unittest.TestCase):
    def test_metadata_and_exact_member(self):
        stream = io.BytesIO()
        with zipfile.ZipFile(stream, "w", zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("S/wav/0001.wav", b"fixture bytes" * 10)
            archive.writestr("S/pos/0001.pos", b"unused")
        raw = stream.getvalue()
        start, size, end = panel.central_location(raw, len(raw))
        entries = panel.parse_central(raw[start : start + size], end)
        entry = next(e for e in entries if e["name"].endswith(".wav"))
        self.assertEqual(panel.extract_member(raw[entry["offset"] :], entry), b"fixture bytes" * 10)
        with self.assertRaises(ValueError):
            panel.extract_member(raw[:15], entry)
        entry["crc32"] += 1
        with self.assertRaises(ValueError):
            panel.extract_member(raw, entry)

    def test_refuse_ignored_range_without_body_read(self):
        class Response:
            status = 200
            headers = None

            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def read(self, size):
                raise AssertionError("Must not read large body")

        with (
            patch("public_panel.urllib.request.urlopen", return_value=Response()),
            self.assertRaises(ValueError),
        ):
            panel.range_get("https://example.test/data.zip", 0, 10, 100)

    def test_transcript_is_not_segmentation(self):
        text = b'item []:\n item [1]:\n name = "words"\n text = ""\n text = "bu3"\n'
        self.assertEqual(panel.word_transcript(text), ["bu3"])

    def test_recorded_metadata_replays_deterministically(self):
        if not (panel.AUDIT / "candidate-items.csv").exists():
            self.skipTest("Metadata stage not yet complete")
        first = panel.enumerate_candidates()
        self.assertEqual(panel.csv_data(first), (panel.AUDIT / "candidate-items.csv").read_bytes())
        self.assertEqual(
            len(panel.choose(first)),
            len(json.loads((panel.AUDIT / "selection.json").read_text())["selected_ids"]),
        )


class CompletedPanelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = []
        for row in panel.selected_rows():
            path = panel.CACHE / "audio" / row["speaker_name"] / (row["file_id"] + ".json")
            receipt = json.loads(path.read_text())
            cls.rows.append(
                {**row, **{k: v for k, v in receipt.items() if k not in {"network", "zip_entry"}}}
            )

    def test_exact_18_speakers_720_rows_balanced(self):
        panel.validate_composition(self.rows)
        self.assertEqual(Counter(r["tone"] for r in self.rows), dict.fromkeys("1234", 180))
        self.assertEqual(
            Counter(r["speaker_native_status"] for r in self.rows), {"NATIVE": 480, "LEARNER": 240}
        )
        self.assertEqual(
            len({r["speaker_name"] for r in self.rows if r["speaker_native_status"] == "NATIVE"}),
            12,
        )
        self.assertEqual(
            len({r["speaker_name"] for r in self.rows if r["speaker_native_status"] == "LEARNER"}),
            6,
        )

    def test_manifest_bytes_independent_of_acquisition_order(self):
        self.assertEqual(panel.manifest_bytes(self.rows), panel.manifest_bytes(self.rows[::-1]))
        data = panel.manifest_bytes(self.rows)
        self.assertEqual(
            panel.manifest_bytes(list(panel.csv.DictReader(io.StringIO(data.decode())))), data
        )

    def test_real_hashes_no_internal_or_historical_overlap(self):
        historical, _ = panel.historical_metadata()
        historical.extend(
            json.loads((panel.AUDIT / "historical-mono16k-index.json").read_text())["audio"]
        )
        panel.validate_final(self.rows, historical)
        for row in self.rows:
            self.assertEqual(panel.digest(panel.ROOT / row["local_path"]), row["audio_sha256"])

    def test_actual_raw_audio_ignored(self):
        paths = [r["local_path"] for r in self.rows]
        ignored = panel.subprocess.check_output(
            ["git", "check-ignore", "--stdin"],
            input="\n".join(paths),
            text=True,
            cwd=panel.ROOT,
        ).splitlines()
        self.assertEqual(set(ignored), set(paths))

    def test_completed_acquisition_resume_uses_no_network(self):
        with patch("public_panel.range_get", side_effect=AssertionError("Unexpected redownload")):
            for row in panel.selected_rows():
                receipt = panel.acquire_one(row)
                self.assertEqual(receipt["source_asset_id"], row["source_asset_id"])


if __name__ == "__main__":
    unittest.main()
