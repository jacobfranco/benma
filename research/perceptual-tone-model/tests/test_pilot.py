"""Research contracts and adversarial checks; no production tests are changed."""

import copy
import tempfile
import unittest
import wave
from pathlib import Path
from types import SimpleNamespace

import numpy as np
from perceptual_tone.annotations import active_judgments, aggregate, import_annotations, item_id
from perceptual_tone.audio import bounds, packet, prepare_windows, read_audio, verify_window_config
from perceptual_tone.common import PACKAGE, file_hash, read_json, read_rows, write_json
from perceptual_tone.embeddings import FrozenEncoder, cache_key, frame_centers, pool
from perceptual_tone.experiment import experiment_identity, validate_config
from perceptual_tone.features import baseline_prediction, matrix, vector
from perceptual_tone.manifest import replay, upgrade, validate, verify_baseline
from perceptual_tone.metrics import metrics
from perceptual_tone.splits import apply_split, leakage_checks, split_speakers
from sklearn.impute import SimpleImputer


def judgment(label="acceptable", annotator="listener", jid="j1", **changes):
    return {
        "judgment_id": jid,
        "annotator_id": annotator,
        "acceptability": label,
        "perceived_tone": None,
        "confidence": None,
        "notes": None,
        "timestamp": "2026-10-15T00:00:00Z",
        "rubric_version": "1.0",
        "version": 1,
        "supersedes": None,
        "origin": "human",
        **changes,
    }


class PilotTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix="benma-pilot-tests-")
        cls.root = Path(cls.temp.name)
        cls.config = read_json(PACKAGE / "configs/pilot.json")
        cls.aggregation = cls.config["aggregation"]
        selected = {}
        for row in read_rows(PACKAGE / "stage0.baseline.jsonl"):
            if row["target"]["unit_kind"] == "syllable":
                selected.setdefault(row["recording_id"], row)
        cls.originals = list(selected.values())[:6]
        speakers = {r["recording_id"]: f"speaker-{i}" for i, r in enumerate(cls.originals)}
        cls.rows = upgrade(cls.originals, "unit-test-v1", speakers)
        cls.rows = prepare_windows(cls.rows, cls.config["windows"], cls.root / "audio")

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def test_manifest_accepts_supported_fields_and_rejects_unknown(self):
        validate(self.rows)
        for change in (
            lambda r: r.update(surprise=1),
            lambda r: r["target"].update(syllable_index=-1),
            lambda r: r["target"].update(start_seconds=r["target"]["end_seconds"]),
            lambda r: r["target"].update(syllable_indices=[99]),
        ):
            row = copy.deepcopy(self.rows[0])
            change(row)
            with self.assertRaises(ValueError):
                validate([row])
        with self.assertRaises(ValueError):
            validate([self.rows[0], self.rows[0]])

    def test_annotation_import_preserves_raw_revisions_and_reimport(self):
        rows = copy.deepcopy(self.rows[:1])
        mapping = self.root / "annotation-map.json"
        write_json(mapping, {"items": {item_id(rows[0]): rows[0]["example_id"]}})
        first = {"item_id": item_id(rows[0]), **judgment()}
        second = {
            "item_id": item_id(rows[0]),
            **judgment("incorrect", jid="j2", version=2, supersedes="j1"),
        }
        result = import_annotations(rows, [first, second], mapping, self.aggregation)
        self.assertEqual(len(result[0]["annotations"]), 2)
        self.assertEqual(result[0]["annotations"][0]["acceptability"], "acceptable")
        self.assertEqual(
            active_judgments(result[0]["annotations"])[0]["acceptability"], "incorrect"
        )
        self.assertEqual(result, import_annotations(result, [second], mapping, self.aggregation))
        with self.assertRaisesRegex(ValueError, "overwrite"):
            import_annotations(
                result, [{**second, "acceptability": "borderline"}], mapping, self.aggregation
            )
        with self.assertRaises(ValueError):
            import_annotations(
                rows, [{**first, "origin": "deterministic"}], mapping, self.aggregation
            )
        with self.assertRaises(ValueError):
            import_annotations(
                rows, [{**first, "acceptability": "STRONG_MATCH"}], mapping, self.aggregation
            )

    def test_annotation_revisions_require_explicit_chain(self):
        with self.assertRaisesRegex(ValueError, "supersede"):
            active_judgments([judgment(), judgment("incorrect", jid="j2")])
        with self.assertRaises(ValueError):
            active_judgments([judgment(timestamp="2026-10-15T00:00:00")])

    def test_global_judgment_identity(self):
        rows = copy.deepcopy(self.rows[:2])
        for row in rows:
            row["annotations"] = [judgment()]
            row["provenance"]["annotation_kind"] = "human"
        with self.assertRaisesRegex(ValueError, "globally unique"):
            validate(rows)

    def test_aggregation_disagreement_unanimity_and_ungradable(self):
        def votes(labels):
            return [judgment(label, f"a{i}", f"j{i}") for i, label in enumerate(labels)]

        raw = votes(["acceptable", "acceptable", "incorrect"])
        before = copy.deepcopy(raw)
        derived = aggregate(raw, self.aggregation)
        self.assertEqual(derived["label"], "acceptable")
        self.assertEqual(derived["disagreement_count"], 1)
        self.assertAlmostEqual(derived["entropy_normalized"], 0.459147917, places=6)
        self.assertEqual(raw, before)
        self.assertIsNone(aggregate(raw, {**self.aggregation, "method": "unanimous"})["label"])
        self.assertIsNone(aggregate(raw, {**self.aggregation, "max_entropy": 0.1})["label"])
        self.assertIsNone(
            aggregate(votes(["acceptable", "incorrect", "borderline"]), self.aggregation)["label"]
        )
        self.assertIsNone(
            aggregate(votes(["acceptable", "acceptable", "ungradable"]), self.aggregation)["label"]
        )
        self.assertEqual(
            aggregate(votes(["ungradable"] * 3), self.aggregation)["label"], "ungradable"
        )
        self.assertEqual(aggregate([], self.aggregation)["reason"], "unlabeled")

    def test_packet_is_blinded_stable_and_has_context(self):
        path = self.root / "packet"
        packet(self.rows[:2], path)
        items = read_rows(path / "public/items.jsonl")
        for item in items:
            self.assertEqual(
                set(item),
                {
                    "item_id",
                    "utterance",
                    "target_hanzi",
                    "syllable_index",
                    "audio",
                    "full_utterance_audio",
                },
            )
            self.assertEqual(set(item["audio"]), {"target", "local", "wide"})
            self.assertTrue((path / "public" / item["full_utterance_audio"]).is_file())
        changed = copy.deepcopy(self.rows[0])
        changed["deterministic"]["color"] = "red"
        changed["example_id"] = "incorrect-label-in-filename"
        self.assertEqual(item_id(changed), item_id(self.rows[0]))
        self.assertFalse((path / "public/private-map.json").exists())

    def test_speaker_split_is_reproducible_and_input_order_independent(self):
        assigned, split = split_speakers(self.rows, self.config["split"])
        reversed_rows, reversed_split = split_speakers(
            list(reversed(self.rows)), self.config["split"]
        )
        self.assertEqual(split, reversed_split)
        self.assertEqual(
            {r["speaker_id"]: r["partition"] for r in assigned},
            {r["speaker_id"]: r["partition"] for r in reversed_rows},
        )
        self.assertEqual(set(split["speakers"].values()), {"train", "validation", "test"})
        altered = copy.deepcopy(split)
        altered["speakers"][self.rows[0]["speaker_id"]] = "wrong"
        with self.assertRaises(ValueError):
            apply_split(self.rows, altered)

    def test_ten_speaker_split_target(self):
        selected = {}
        for row in read_rows(PACKAGE / "stage0.baseline.jsonl"):
            if row["target"]["unit_kind"] == "syllable":
                selected.setdefault(row["recording_id"], row)
        originals = list(selected.values())[:10]
        rows = upgrade(
            originals,
            "ten-speaker-test",
            {r["recording_id"]: f"speaker-{i}" for i, r in enumerate(originals)},
        )
        rows = prepare_windows(rows, self.config["windows"], self.root / "audio")
        _, split = split_speakers(rows, self.config["split"])
        self.assertEqual(
            [list(split["speakers"].values()).count(p) for p in ("train", "validation", "test")],
            [6, 2, 2],
        )
        rows[0]["speaker_id"] = None
        with self.assertRaisesRegex(ValueError, "every speaker"):
            split_speakers(rows, self.config["split"])

    def test_speaker_and_recording_leakage_rejected(self):
        rows, _ = split_speakers(self.rows, self.config["split"])
        duplicate = copy.deepcopy(rows[0])
        duplicate["example_id"] = "a-different-example"
        duplicate["partition"] = "test" if duplicate["partition"] != "test" else "train"
        with self.assertRaisesRegex(ValueError, "speaker leakage"):
            leakage_checks([*rows, duplicate])
        duplicate["speaker_id"] = "a-different-speaker"
        with self.assertRaisesRegex(ValueError, "recording leakage"):
            leakage_checks([*rows, duplicate])
        duplicate["recording_id"] = "renamed-recording"
        with self.assertRaisesRegex(ValueError, "recording_sha leakage"):
            leakage_checks([*rows, duplicate])

    def test_duplicate_audio_windows_with_different_recordings_rejected(self):
        a = copy.deepcopy(self.rows[0])
        b = copy.deepcopy(a)
        pcm, rate, _ = read_audio(a["audio"]["reference"])
        path = self.root / "different-container-and-tail.wav"
        with wave.open(str(path), "wb") as stream:
            stream.setnchannels(1)
            stream.setsampwidth(2)
            stream.setframerate(rate)
            stream.writeframes(pcm + b"\x01\x00" * rate)
        b.update(
            example_id="duplicate-crop", recording_id="other-recording", speaker_id="other-speaker"
        )
        b["audio"].update(reference=str(path), sha256=file_hash(path))
        a["partition"], b["partition"] = "train", "test"
        rows = prepare_windows([a, b], self.config["windows"], self.root / "duplicates")
        with self.assertRaisesRegex(ValueError, "audio_window_pcm leakage"):
            leakage_checks(rows)

    def test_scientific_mode_rejects_fixture_provenance(self):
        rows, _ = split_speakers(self.rows, self.config["split"])
        rows[0]["provenance"]["speaker_identity"] = "temporary_fixture"
        with self.assertRaisesRegex(ValueError, "scientific"):
            leakage_checks(rows, scientific=True)

    def test_window_bounds_clipping_and_config_mismatch(self):
        self.assertEqual(bounds(0.1, 0.4, 16000, 16000, 0.35, 1.2), (0, 16000))
        for args in (
            (-0.1, 0.4, 16000, 16000, 0.2, 0.2),
            (0.1, 2, 16000, 16000, 0.2, 0.2),
            (0.4, 0.1, 16000, 16000, 0.2, 0.2),
            (0.1, 0.4, 16000, 16000, -1, 0.2),
        ):
            with self.assertRaises(ValueError):
                bounds(*args)
        verify_window_config(self.rows, self.config["windows"])
        with self.assertRaises(ValueError):
            verify_window_config(
                self.rows,
                {**self.config["windows"], "local": {"before_seconds": 0, "after_seconds": 0}},
            )

    def test_audio_checksums_and_source_window_provenance(self):
        with self.assertRaisesRegex(ValueError, "checksum"):
            read_audio(self.rows[0]["audio"]["reference"], "0" * 64)
        rows, _ = split_speakers(self.rows, self.config["split"])
        rows[0]["windows"]["target"]["start_sample"] += 1
        with self.assertRaisesRegex(ValueError, "provenance"):
            leakage_checks(rows)

    def test_cache_key_stability_and_sensitivity(self):
        args = [
            "audiohash",
            {"model": "a", "revision": "b"},
            {"pooling": "target"},
            [10, 20],
            {"torch": "v"},
            {"weights": "sha"},
        ]
        self.assertEqual(cache_key(*args), cache_key(*copy.deepcopy(args)))
        for i in range(len(args)):
            changed = copy.deepcopy(args)
            changed[i] = "different"
            self.assertNotEqual(cache_key(*args), cache_key(*changed))

    def test_verified_embedding_cache_hit_and_corruption(self):
        encoder = FrozenEncoder.__new__(FrozenEncoder)
        encoder.encoder = {"sample_rate_hz": 16000, "hidden_size": 3}
        encoder.settings = {"view": "local", "pooling": "target_mean"}
        encoder.directory = self.root / "test-only-cache"
        encoder.directory.mkdir()
        encoder.weights, encoder.environment = {}, {}
        encoder.hits = encoder.misses = 0
        row = self.rows[0]
        window = row["windows"]["local"]
        target = [
            row["target"][k] * 16000 - window["start_sample"]
            for k in ("start_seconds", "end_seconds")
        ]
        key = cache_key(window["pcm_sha256"], encoder.encoder, encoder.settings, target, {}, {})
        path = encoder.directory / f"{key}.npy"
        np.save(
            path, np.array([1.0, 2.0, 3.0])
        )  # Explicit cache fixture, never a speech encoder substitute.
        write_json(
            encoder.directory / f"{key}.json", {"cache_key": key, "vector_sha256": file_hash(path)}
        )
        values, _ = encoder.extract(row)
        np.testing.assert_equal(values, [1, 2, 3])
        self.assertEqual(encoder.hits, 1)
        path.write_bytes(b"corrupt")
        with self.assertRaisesRegex(ValueError, "checksum"):
            encoder.extract(row)

    def test_receptive_field_alignment_and_pooling(self):
        centers = frame_centers(SimpleNamespace(conv_kernel=[10, 3], conv_stride=[5, 2]), 3)
        np.testing.assert_equal(centers, [9.5, 19.5, 29.5])
        hidden = np.array([[1.0, 2.0], [3.0, 4.0], [8.0, 9.0]])
        np.testing.assert_equal(pool(hidden, centers, [15, 25], "target_mean"), [3, 4])
        np.testing.assert_allclose(pool(hidden, centers, [15, 25], "context_mean"), hidden.mean(0))
        self.assertEqual(pool(hidden, centers, [15, 25], "target_context_concat").shape, (4,))
        with self.assertRaises(ValueError):
            pool(hidden, centers, [100, 120], "target_mean")

    def test_feature_schema_and_missing_values(self):
        names, original = vector(self.rows[0], "benma")
        changed = copy.deepcopy(self.rows[0])
        changed["deterministic"]["shape"]["features"] = {}
        second_names, missing = vector(changed, "benma")
        self.assertEqual(names, second_names)
        self.assertTrue(np.isnan(missing[names.index("shape.start_st")]))
        values, columns = matrix([changed, self.rows[1]], ["benma", "context"])
        self.assertEqual(values.shape[1], len(columns))
        self.assertEqual(values[0, columns.index("missing.benma.shape.start_st")], 1)
        self.assertEqual(len(original), len(missing))
        # Held-out extreme values cannot influence training-fitted median statistics.
        imputer = SimpleImputer(strategy="median", keep_empty_features=True).fit(
            [[1.0, np.nan], [3.0, np.nan]]
        )
        np.testing.assert_equal(imputer.transform([[np.nan, 999.0]])[0], [2.0, 999.0])

    def test_labels_ids_notes_filenames_and_consensus_never_enter_features(self):
        changed = copy.deepcopy(self.rows[0])
        changed.update(
            example_id="incorrect",
            speaker_id="acceptable",
            utterance="borderline",
            annotations=[judgment("incorrect")],
            aggregate={"label": "incorrect"},
        )
        changed["audio"]["reference"] = "incorrect.wav"
        changed["target"]["pinyin"] = "incorrect"
        changed["deterministic"]["learner_grade"]["agreement"] = "CLEAR_DIFFERENCE"
        changed["deterministic"]["coaching_message"] = "incorrect"
        for group in ("benma", "context"):
            before_names, before = vector(self.rows[0], group)
            after_names, after = vector(changed, group)
            self.assertEqual(before_names, after_names)
            np.testing.assert_equal(before, after)
        with self.assertRaises(ValueError):
            matrix(self.rows, ["annotations"])

    def test_metric_denominators_abstentions_and_calibration(self):
        truth = ["acceptable", "acceptable", "borderline", "incorrect", "incorrect"]
        predictions = ["incorrect", "abstain", "borderline", "incorrect", "abstain"]
        probabilities = [
            [0.05, 0.05, 0.9],
            [0.4, 0.3, 0.3],
            [0.1, 0.8, 0.1],
            [0.05, 0.05, 0.9],
            [0.34, 0.33, 0.33],
        ]
        report = metrics(truth, predictions, probabilities)
        self.assertEqual(report["warning_on_acceptable"]["rate"], 0.5)
        self.assertEqual(report["incorrect_on_acceptable"]["rate"], 0.5)
        self.assertEqual(report["confident_incorrect_precision"]["rate"], 0.5)
        self.assertEqual(report["incorrect_recall"]["rate"], 0.5)
        self.assertEqual(report["abstention"]["rate"], 0.4)
        self.assertAlmostEqual(report["macro_f1"], 0.5)
        self.assertEqual(
            report["confusion_matrix"]["counts"], [[0, 0, 1, 1], [0, 1, 0, 0], [0, 0, 1, 1]]
        )
        self.assertEqual(sum(b["count"] for b in report["calibration"]["reliability_bins"]), 5)
        perfect = metrics(
            ["acceptable", "borderline", "incorrect"],
            ["acceptable", "borderline", "incorrect"],
            np.eye(3),
        )
        self.assertEqual(perfect["calibration"]["multiclass_brier"], 0)
        self.assertEqual(perfect["calibration"]["ece"], 0)
        no_acceptable = metrics(["incorrect"], ["abstain"])
        self.assertIsNone(no_acceptable["warning_on_acceptable"]["rate"])
        self.assertEqual(no_acceptable["incorrect_recall"]["rate"], 0)

    def test_baseline_adapter_and_immutable_replay(self):
        self.assertEqual(verify_baseline()["verified_files"], 413)
        rows, _ = replay(self.rows)
        for before, after in zip(self.rows, rows, strict=True):
            self.assertEqual(before["deterministic"], after["deterministic"])
        row = copy.deepcopy(self.rows[0])
        for grade, expected in (
            ("STRONG_MATCH", "acceptable"),
            ("PARTIAL_OR_WEAK", "borderline"),
            ("CLEAR_DIFFERENCE", "incorrect"),
            ("UNAVAILABLE", "abstain"),
        ):
            row["deterministic"]["learner_grade"]["agreement"] = grade
            self.assertEqual(baseline_prediction(row), expected)

    def test_experiment_config_and_identity_reproducibility(self):
        validate_config(self.config)
        rows, split = split_speakers(self.rows, self.config["split"])
        first = experiment_identity(rows, split, self.config, {})
        second = experiment_identity(list(reversed(rows)), split, copy.deepcopy(self.config), {})
        self.assertEqual(first, second)
        changed = copy.deepcopy(self.config)
        changed["seed"] += 1
        self.assertNotEqual(
            first["config_sha256"], experiment_identity(rows, split, changed, {})["config_sha256"]
        )
        with self.assertRaises(ValueError):
            validate_config({**self.config, "target": "deterministic.color"})


if __name__ == "__main__":
    unittest.main()
