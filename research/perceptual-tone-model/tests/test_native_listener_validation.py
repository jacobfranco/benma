"""Engineering fixtures only: synthetic answers live in temporary directories."""

import base64
import hashlib
import json
import os
import tempfile
import unittest
import zipfile
from collections import Counter
from pathlib import Path
from unittest.mock import patch

from perceptual_tone import native_listener_analysis as analysis
from perceptual_tone import native_listener_validation as study
from perceptual_tone.common import file_hash, read_json, read_rows

DISAGREEMENTS = [
    "learner:0b44eac1332ea0859ac54d67:4",
    "learner:39e33220c5dec271b192f561:2",
    "learner:39e33220c5dec271b192f561:3",
    "learner:4cf712ee935667d1ab00dd9f:1",
    "learner:4cf712ee935667d1ab00dd9f:10",
    "learner:4cf712ee935667d1ab00dd9f:4",
    "learner:4cf712ee935667d1ab00dd9f:5",
]
CONTROLS = [
    "learner:39e33220c5dec271b192f561:0",
    "learner:0b44eac1332ea0859ac54d67:5",
    "learner:39e33220c5dec271b192f561:5",
    "learner:4cf712ee935667d1ab00dd9f:2",
    "learner:39e33220c5dec271b192f561:8",
    "learner:0b44eac1332ea0859ac54d67:2",
    "learner:0b44eac1332ea0859ac54d67:1",
]


class ListeningStudyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.package = Path(os.environ.get("NATIVE_LISTENER_TEST_PACKAGE", str(study.OUT)))
        cls.key = read_json(cls.package / "PRIVATE/trial-key.json")
        cls.plan = read_json(cls.package / "preregistration.json")
        cls.items = cls.key["items"]

    def packet(self, lid):
        source = (self.package / "listener-packages" / lid / "packet.js").read_text()
        return json.loads(source.removeprefix("const PACKET = ").removesuffix(";\n"))

    def fixture(self, lid="L01"):
        listener = self.key["listeners"][lid]
        lookup = {i["id"]: i for i in self.items}
        return {
            "version": study.VERSION,
            "listener_id": lid,
            "packet_sha256": listener["packet_sha256"],
            "eligibility": dict.fromkeys(
                ["adult", "native", "primary_childhood", "independent"], True
            ),
            "background": dict.fromkeys(["region", "other_variety", "current_language"], ""),
            "started_at": "2026-10-22T00:00:00Z",
            "completed_at": "2026-10-22T01:00:00Z",
            "responses": [
                {
                    "trial_id": t["trial_id"],
                    "position": t["position"],
                    "answer": lookup[t["item_id"]]["native_label"] or "T2",
                    "answered_at": "2026-10-22T00:30:00Z",
                    "play_count": 1,
                }
                for t in listener["trials"]
            ],
        }

    def test_exact_disagreements(self):
        self.assertEqual(self.plan["learner_disagreements"], DISAGREEMENTS)
        self.assertEqual(
            [i["id"] for i in self.items if i["kind"] == "disagreement"], DISAGREEMENTS
        )

    def test_exact_controls_and_matching(self):
        self.assertEqual([m["control"] for m in self.plan["learner_controls"]], CONTROLS)
        self.assertEqual([m["case"] for m in self.plan["learner_controls"]], DISAGREEMENTS)
        self.assertEqual(
            self.plan["learner_controls"], study.frozen_selection()["learner_controls"]
        )

    def test_deterministic_native_selection_ignores_predictions(self):
        rows = read_rows(study.NATIVE / "manifest.jsonl")
        split = read_json(study.NATIVE / "split.json")["assignments"]
        quarantine = {
            r["record"]["example_id"] for r in read_rows(study.NATIVE / "quarantined.jsonl")
        }
        first = study.select_native(rows, split, quarantine)
        for r in rows:
            r["expanded_prediction"] = "POISON"
            r["original"]["pilot_prediction"] = "POISON"
        second = study.select_native(list(reversed(rows)), split, quarantine)
        expected = self.plan["native_control_ids"]
        self.assertEqual([r["example_id"] for r, _, _ in first], expected)
        self.assertEqual([r["example_id"] for r, _, _ in second], expected)
        self.assertTrue(all(split[r["speaker_id"]] == "test" for r, _, _ in first))
        self.assertEqual(
            Counter(r["corpus_tone"] for r, _, d in first if d == "positive"),
            {1: 3, 2: 3, 3: 3, 4: 3},
        )
        self.assertEqual(
            Counter(r["corpus_tone"] for r, _, d in first if d == "challenge"),
            {1: 1, 2: 1, 3: 1, 4: 1},
        )

    def test_repeat_audio_identity_ids_and_counts(self):
        for lid, listener in self.key["listeners"].items():
            public = {r["trial_id"]: r for r in self.packet(lid)["trials"]}
            originals = {
                (t["item_id"], t["view"]): t for t in listener["trials"] if not t["repeat"]
            }
            repeats = [t for t in listener["trials"] if t["repeat"]]
            self.assertEqual(
                Counter(t["kind"] for t in repeats),
                {"disagreement": 3, "agreement": 3, "native_positive": 2},
            )
            self.assertEqual(len(public), 68)
            for t in repeats:
                original = originals[t["item_id"], t["view"]]
                self.assertNotEqual(t["trial_id"], original["trial_id"])
                for view in ("target", "context"):
                    self.assertEqual(
                        public[t["trial_id"]][view], public[original["trial_id"]][view]
                    )

    def test_randomization_reproducible_different_and_separated(self):
        orders = []
        for lid, listener in self.key["listeners"].items():
            trials, attempts = study.make_trials(self.items, lid, listener["seed"])
            self.assertEqual(trials, listener["trials"])
            self.assertEqual(attempts, listener["shuffle_attempts"])
            positions = {}
            for t in trials:
                if t["item_id"] in positions:
                    self.assertGreaterEqual(t["position"] - positions[t["item_id"]], 8)
                positions[t["item_id"]] = t["position"]
            orders.append([t["item_id"] for t in trials])
        self.assertEqual(len({tuple(o) for o in orders}), 5)

    def test_no_hidden_fields_expected_tones_or_private_files(self):
        for lid in self.key["listeners"]:
            folder = self.package / "listener-packages" / lid
            self.assertTrue(study.verify_blinding(folder, self.packet(lid), self.items)["passed"])
            for key in (
                "expanded_prediction",
                "pilot_prediction",
                "expected_tone",
                "lexical_tone",
                "probabilities",
                "sandhi_target",
                "expected_grade",
                "native_label",
            ):
                poisoned = self.packet(lid)
                poisoned["trials"][0][key] = "T1"
                with self.assertRaises(ValueError):
                    study.verify_blinding(folder, poisoned, self.items)

    def test_source_pcm_crops_and_context_are_exact(self):
        packet = self.packet("L01")
        lookup = {t["trial_id"]: t for t in self.key["listeners"]["L01"]["trials"]}
        items = {i["id"]: i for i in self.items}
        for t in packet["trials"]:
            item = items[lookup[t["trial_id"]]["item_id"]]
            for name, field in [("crop", "target"), ("context", "context")]:
                raw = base64.b64decode(t[field].split(",")[1])
                span = item["owner_crop"] if name == "crop" else item["context"]
                self.assertEqual(raw, study.wav_clip(item["source_audio"], span))
                self.assertEqual(hashlib.sha256(raw).hexdigest(), item["clip_sha256"][name])

    def test_schema_neutral_unclear_and_fixed_rules(self):
        schema = read_json(self.package / "response-schema.json")
        self.assertEqual(schema, study.response_schema())
        self.assertEqual(
            schema["properties"]["responses"]["items"]["properties"]["answer"]["enum"],
            ["T1", "T2", "T3", "T4", "NEUTRAL", "UNCLEAR"],
        )
        self.assertEqual(self.plan["rules"], study.RULES)
        self.assertEqual(study.RULES["native_correct_min"], 10)
        self.assertEqual(study.RULES["repeat_consistent_min"], 6)
        self.assertEqual(study.RULES["native_per_tone_min"], 2)

    def test_qualify_and_reject_native_per_tone_failure(self):
        data = self.fixture()
        listener = self.key["listeners"]["L01"]
        self.assertTrue(analysis.score_listener(data, listener, self.items)[0]["qualified"])
        lookup = {i["id"]: i for i in self.items}
        wrong = 0
        for r, t in zip(data["responses"], listener["trials"], strict=True):
            if (
                lookup[t["item_id"]]["kind"] == "native_positive"
                and lookup[t["item_id"]]["native_label"] == "T1"
                and t["view"] == "context"
                and not t["repeat"]
                and wrong < 2
            ):
                r["answer"] = "UNCLEAR"
                wrong += 1
        score, _ = analysis.score_listener(data, listener, self.items)
        self.assertEqual(score["native_correct"], 10)
        self.assertFalse(score["qualified"])

    def test_repeat_boundary(self):
        listener = self.key["listeners"]["L01"]
        for errors in (2, 3):
            data = self.fixture()
            changed = 0
            for r, t in zip(data["responses"], listener["trials"], strict=True):
                if t["repeat"] and changed < errors:
                    r["answer"] = "UNCLEAR"
                    changed += 1
            score, _ = analysis.score_listener(data, listener, self.items)
            self.assertEqual(score["qualified"], errors == 2)
            self.assertEqual(score["repeat_consistent"], 8 - errors)

    def test_invalid_incomplete_and_duplicate_trials_rejected(self):
        for mutation in ("partial", "duplicate", "omission", "eligibility", "playback"):
            data = self.fixture()
            if mutation == "partial":
                data["responses"].pop()
            elif mutation == "duplicate":
                data["responses"][1] = data["responses"][0]
            elif mutation == "omission":
                data["responses"][0]["answer"] = ""
            elif mutation == "eligibility":
                data["eligibility"]["adult"] = False
            else:
                data["responses"][0]["play_count"] = 0
            self.assertFalse(
                analysis.score_listener(data, self.key["listeners"]["L01"], self.items)[0][
                    "qualified"
                ]
            )

    def test_case_states_views_unclear_neutral_and_repeats(self):
        def votes(crop, context=None, repeat=None):
            v = {("x", "crop", False): crop, ("x", "context", False): context or crop}
            if repeat:
                v["x", "context", True] = repeat
            return v

        scenarios = [
            ([votes("T2")] * 5, "STRONG", "T2"),
            ([votes("T2")] * 3, "MODERATE", "T2"),
            ([votes("T2")] * 2, "UNRESOLVED", None),
            ([votes("T2")] * 2 + [votes("UNCLEAR")], "MODERATE", "T2"),
            ([votes("T2")] * 3 + [votes("T1")] * 2, "AMBIGUOUS", None),
            ([votes("T2", "T1")] * 5, "AMBIGUOUS", None),
            ([votes("UNCLEAR")] * 5, "UNRESOLVED", None),
            ([votes("NEUTRAL")] * 5, "STRONG", "NEUTRAL"),
            ([votes("T2", repeat="T1")] * 5, "UNRESOLVED", None),
        ]
        for data, state, tone in scenarios:
            result = analysis.case_evidence("x", data)
            self.assertEqual((result["state"], result["consensus_tone"]), (state, tone))

    def test_inter_rater_degenerate_and_disagreement(self):
        items = [{"id": "a", "kind": "disagreement"}, {"id": "b", "kind": "disagreement"}]
        agree = {("a", v, False): "T1" for v in ("crop", "context")}
        agree.update({("b", v, False): "T2" for v in ("crop", "context")})
        report = analysis.inter_rater(items, [agree] * 3)
        self.assertEqual(report[0]["fleiss_kappa_six_categories"], 1)
        self.assertEqual(report[0]["pair_denominator"], 6)
        self.assertIsNone(analysis.inter_rater(items, [agree])[0]["fleiss_kappa_six_categories"])

    def test_unblind_requires_raw_and_consensus_seals(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with self.assertRaises(ValueError):
                analysis.unblind(self.package, root)
            incoming = root / "incoming"
            incoming.mkdir()
            (incoming / "L01.json").write_text(json.dumps(self.fixture()))
            responses = root / "responses"
            analysis.seal_responses(self.package, incoming, responses, True)
            with self.assertRaisesRegex(ValueError, "consensus"):
                analysis.unblind(self.package, responses)

    def test_full_pipeline_synthetic_only_and_tamper_gates(self):
        with tempfile.TemporaryDirectory(prefix="SYNTHETIC-native-listener-") as tmp:
            root = Path(tmp)
            incoming = root / "incoming"
            incoming.mkdir()
            for lid in self.key["listeners"]:
                (incoming / (lid + ".json")).write_text(json.dumps(self.fixture(lid)))
            responses = root / "responses"
            with self.assertRaises(ValueError):
                analysis.seal_responses(self.package, incoming, responses)
            analysis.seal_responses(self.package, incoming, responses, True)
            original_reader = analysis.read_json

            def no_predictions(path):
                if str(path).endswith("predictions.json"):
                    raise AssertionError("head predictions read before consensus seal")
                return original_reader(path)

            with patch.object(analysis, "read_json", side_effect=no_predictions):
                report = analysis.analyze(self.package, responses)
            self.assertEqual(report["qualified_n"], 5)
            synthetic_predictions = root / "synthetic-predictions.json"
            synthetic_predictions.write_text(
                json.dumps(
                    {
                        "rows": [
                            {
                                "id": item_id,
                                "head": head,
                                "prediction": "T2",
                                "arm": "ACOUSTIC_WEIGHTED",
                                "perturbation": "BASE",
                            }
                            for item_id in DISAGREEMENTS
                            for head in ("expanded", "pilot")
                        ]
                    }
                )
            )

            def synthetic_reference(path):
                if str(path).endswith("PRIVATE/prediction-reference.json"):
                    return {
                        "path": str(synthetic_predictions),
                        "sha256": file_hash(synthetic_predictions),
                    }
                if str(path) == str(study.PRIOR / "predictions.json"):
                    raise AssertionError(
                        "Real head outputs must not be compared to synthetic labels"
                    )
                return original_reader(path)

            with patch.object(analysis, "read_json", side_effect=synthetic_reference):
                result = analysis.unblind(self.package, responses)
            self.assertEqual(len(result), 7)
            self.assertTrue(all(r["state"] == "STRONG" for r in result))
            # Sealed raw byte changes invalidate even a previously derived consensus.
            with (responses / "raw/L01.json").open("a") as stream:
                stream.write(" ")
            with self.assertRaisesRegex(ValueError, "response changed"):
                analysis.unblind(self.package, responses)

    def test_frozen_inputs_unchanged(self):
        self.assertEqual(study.verify_freeze(self.package)["changed_files"], [])

    def test_share_archives_exclude_private_mapping(self):
        for lid in self.key["listeners"]:
            with zipfile.ZipFile(self.package / "share" / (lid + ".zip")) as archive:
                self.assertEqual(
                    set(archive.namelist()),
                    {lid + "/" + n for n in ("index.html", "app.js", "packet.js")},
                )
                for name in archive.namelist():
                    self.assertEqual(
                        archive.read(name), (self.package / "listener-packages" / name).read_bytes()
                    )

    def test_native_overall_accuracy_boundary(self):
        listener = self.key["listeners"]["L01"]
        positive = [i for i in self.items if i["kind"] == "native_positive"]
        for errors in (2, 3):
            wrong = {i["id"] for i in positive[:errors]}
            data = self.fixture()
            for r, t in zip(data["responses"], listener["trials"], strict=True):
                if t["item_id"] in wrong:
                    r["answer"] = "UNCLEAR"
            score, _ = analysis.score_listener(data, listener, self.items)
            self.assertEqual(score["native_correct"], 12 - errors)
            self.assertEqual(score["repeat_consistent"], 8)
            self.assertEqual(score["qualified"], errors == 2)

    def test_partial_submission_archived_then_disqualified(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            incoming = root / "incoming"
            incoming.mkdir()
            data = self.fixture()
            data["responses"].pop()
            data["completed_at"] = None
            raw = json.dumps(data)
            (incoming / "L01.json").write_text(raw)
            responses = root / "responses"
            analysis.seal_responses(self.package, incoming, responses, True)
            self.assertEqual((responses / "raw/L01.json").read_text(), raw)
            report = analysis.analyze(self.package, responses)
            self.assertEqual(report["qualified_n"], 0)
            self.assertTrue(all(c["state"] == "UNRESOLVED" for c in report["cases"]))

    def test_no_actual_human_results_created(self):
        self.assertFalse((self.package / "responses").exists())
        self.assertFalse((self.package / "incoming").exists())
        self.assertFalse(self.plan["human_responses_exist"])

    def test_package_integrity_seal(self):
        self.assertEqual(analysis.verify_package(self.package), self.key)


if __name__ == "__main__":
    unittest.main()
