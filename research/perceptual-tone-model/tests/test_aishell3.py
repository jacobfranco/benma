"""Real corpus parsing fixtures plus deliberately damaged alignment contracts."""

import copy
import io
import tempfile
import unittest
import wave
from pathlib import Path

import numpy as np
from perceptual_tone.aishell3 import (
    alignment_token,
    attach_prosody,
    audio_only_request,
    checked_wav,
    custom_lexicon,
    g2p_spelling,
    parse_content,
    parse_dictionary,
    parse_prosody,
    parse_speakers,
    pinyin_token,
    quality_gate,
    resolve_speaker,
    speaker_split,
    strip_tone,
    t3_contexts,
    verify_split,
)
from perceptual_tone.aishell3_alignment import reconstruct, textgrid
from perceptual_tone.audio import read_audio
from perceptual_tone.common import PACKAGE, digest, file_hash, read_json

FIXTURES = Path(__file__).parent / "fixtures/aishell3"


class CorpusTests(unittest.TestCase):
    def setUp(self):
        self.real = [
            parse_content(x["line"]) for x in read_json(FIXTURES / "content.json")["examples"]
        ]
        self.registry = parse_speakers((FIXTURES / "speakers.txt").read_text(), {"fixture": True})

    def test_real_examples_round_trip_without_character_splitting(self):
        for utterance in self.real:
            reconstructed = (
                utterance["filename"]
                + "\t"
                + " ".join(f"{u['hanzi']} {u['corpus_pinyin']}" for u in utterance["units"])
            )
            self.assertEqual(parse_content(reconstructed), utterance)
        dian = next(u for r in self.real for u in r["units"] if u["corpus_pinyin"] == "dianr3")
        self.assertEqual(dian["hanzi"], "点儿")
        self.assertTrue(dian["erhua"])
        self.assertEqual(strip_tone("dianr3"), "dianr")

    def test_actual_readings_not_lexical_rules(self):
        u = next(r for r in self.real if r["utterance_id"] == "SSB00090030")
        self.assertEqual([x["corpus_pinyin"] for x in u["units"]], ["wan2", "wan3", "xiang1"])
        self.assertIsNone(u["units"][0]["lexical_tone"])

    def test_neutral_and_zero_initial(self):
        self.assertEqual(pinyin_token("de5")["label"], "T5")
        self.assertFalse(pinyin_token("er2")["erhua"])
        self.assertEqual(strip_tone("an1"), "an")
        self.assertEqual(strip_tone("nv3"), "nv")

    def test_preserve_atypical_multi_hanzi(self):
        u = parse_content("SSB07360405.wav 哪儿 lang3")["units"][0]
        self.assertEqual(u["hanzi"], "哪儿")
        self.assertTrue(u["unusual_multi_hanzi"])

    def test_malformed_pairs_and_punctuation_rejected(self):
        for line in (
            "SSB00090030.wav 碗",
            "../SSB00090030.wav 碗 wan3",
            "SSB00090030.wav 碗 wan0",
            "SSB00090030.wav 碗 wan3 %",
        ):
            with self.subTest(line=line), self.assertRaises(ValueError):
                parse_content(line)
        for value in ("wo", "wo0", "wo6", "wo3x", "wǒ", "wo3ma5"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                pinyin_token(value)

    def test_verified_speaker_and_audio_mapping(self):
        u = next(r for r in self.real if r["speaker_id"] == "SSB0009")
        member = "test/wav/SSB0009/" + u["filename"]
        self.assertEqual(resolve_speaker(u, member, self.registry)["accent"], "south")
        for wrong in (
            member.replace("SSB0009/", "SSB0011/"),
            "../" + member,
            member.replace(u["filename"], "SSB00099999.wav"),
        ):
            with self.assertRaises(ValueError):
                resolve_speaker(u, wrong, self.registry)
        with self.assertRaises(ValueError):
            resolve_speaker(u, member, {})

    def test_metadata_duplicates_rejected(self):
        with self.assertRaises(ValueError):
            parse_speakers("SSB0009 B female south\nSSB0009 B female south", {})

    def test_real_prosody_markers_not_syllables(self):
        rows = [
            parse_prosody(line)
            for line in (FIXTURES / "prosody.txt").read_text().splitlines()
            if line and not line.startswith("#")
        ]
        self.assertEqual(rows[0]["units"][-1]["prosody_after"], "$")
        self.assertTrue(any(u["prosody_after"] == "%" for r in rows for u in r["units"]))
        example = parse_content(
            "SSB00430444.wav 持 chi2 起 qi3 红 hong2 缨 ying1 枪 qiang1 "
            "追 zhui1 赶 gan3 对 dui4 方 fang1 半 ban4 公 gong1 里 li3"
        )
        attached = attach_prosody(example, rows[0])
        self.assertEqual(len(attached["units"]), 12)
        broken = copy.deepcopy(rows[0])
        broken["units"][0]["corpus_pinyin"] = "chi3"
        with self.assertRaises(ValueError):
            attach_prosody(example, broken)

    def test_g2p_orthography_and_unique_alignment_tokens(self):
        self.assertEqual(g2p_spelling("wo3"), "wǒ")
        self.assertEqual(g2p_spelling("de5"), "de")
        self.assertEqual(g2p_spelling("dianr3"), "diǎnr")
        tokens = [alignment_token(pinyin_token("wo" + str(i))) for i in range(1, 6)]
        self.assertEqual(len(set(tokens)), 5)
        self.assertTrue(all(t.isalpha() for t in tokens))

    def test_oov_and_phone_inventory_fail_closed(self):
        u = parse_content("SSB00090030.wav 碗 wan2")
        entries, mapping, oov = custom_lexicon([u], {}, {"w", "a˧˥", "n"})
        self.assertEqual(oov, ["wan2"])
        self.assertFalse(entries or mapping)
        with self.assertRaises(ValueError):
            custom_lexicon([u], {"wan2": [("not_a_model_phone",)]}, {"w"})
        self.assertEqual(
            parse_dictionary("wán\t0.9\t0.1\t1.0\t1.0\tw a˧˥ n")["wán"], [("w", "a˧˥", "n")]
        )
        with self.assertRaisesRegex(ValueError, "g2p_tone"):
            custom_lexicon([u], {"wan2": [("w", "a˨˩˦", "n")]}, {"w", "a˨˩˦", "n"})

    def test_wav_complete_data_and_stale_outer_header(self):
        b = io.BytesIO()
        with wave.open(b, "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(44100)
            w.writeframes(b"\x01\x00" * 4410)
        raw = b.getvalue()
        stale = raw[:4] + (len(raw) + 50).to_bytes(4, "little") + raw[8:]
        self.assertEqual(checked_wav(raw)["pcm_sha256"], checked_wav(stale)["pcm_sha256"])
        self.assertIsNotNone(checked_wav(stale)["container_warning"])
        with self.assertRaises(ValueError):
            checked_wav(raw[:-2])


class AlignmentTests(unittest.TestCase):
    def setUp(self):
        self.config = read_json(PACKAGE / "configs/aishell3.json")
        self.u = {
            **parse_content("SSB06930026.wav 点儿 dianr3 爱 ai4 的 de5"),
            "corpus": "AISHELL-3",
            "partition": "pilot_qa",
            "source_partition": "test",
            "audio": {},
            "pcm_sha256": "abc",
            "duration": 1.1,
            "transcript_provenance": {},
            "prosody_status": "not_available",
        }
        self.lexicon = {
            "aisdianrtonec": [["t", "j", "a˨˩˦", "ɻ"]],
            "aisa itoned".replace(" ", ""): [["aj˥˩"]],
            "aisdetonee": [["t", "ə"]],
        }
        self.tiers = {
            "words": [
                (0, 0.1, ""),
                (0.1, 0.5, "aisdianrtonec"),
                (0.5, 0.8, "aisaitoned"),
                (0.8, 1.0, "aisdetonee"),
                (1.0, 1.1, ""),
            ],
            "phones": [
                (0, 0.1, "sil"),
                (0.1, 0.2, "t"),
                (0.2, 0.25, "j"),
                (0.25, 0.4, "a˨˩˦"),
                (0.4, 0.5, "ɻ"),
                (0.5, 0.8, "aj˥˩"),
                (0.8, 0.85, "t"),
                (0.85, 1.0, "ə"),
                (1.0, 1.1, "sil"),
            ],
        }

    def run_reconstruct(self, tiers=None, diagnostics=None):
        return reconstruct(
            self.u,
            tiers or self.tiers,
            self.lexicon,
            {"alignment_log_likelihood": -20} if diagnostics is None else diagnostics,
            self.config,
        )

    def test_phone_owned_multi_hanzi_zero_initial_neutral(self):
        rows = self.run_reconstruct()
        self.assertEqual([r["reconstruction_status"] for r in rows], ["candidate"] * 3)
        self.assertEqual(rows[0]["hanzi"], "点儿")
        self.assertEqual(rows[0]["end"], 0.5)
        self.assertEqual(rows[2]["label"], "T5")

    def test_token_drop_and_reorder_reject_whole_utterance(self):
        broken = copy.deepcopy(self.tiers)
        broken["words"].pop(2)
        self.assertTrue(
            all(
                "alignment_token_sequence_mismatch" in r["exclusion_reasons"]
                for r in self.run_reconstruct(broken)
            )
        )
        broken = copy.deepcopy(self.tiers)
        a, b, _ = broken["words"][1]
        broken["words"][1] = (a, b, "aisdetonee")
        self.assertTrue(all(r["exclusion_reasons"] for r in self.run_reconstruct(broken)))

    def test_wrong_missing_and_crossing_phones(self):
        broken = copy.deepcopy(self.tiers)
        broken["phones"][3] = (0.25, 0.4, "a˥˩")
        self.assertIn(
            "phone_pronunciation_mismatch", self.run_reconstruct(broken)[0]["exclusion_reasons"]
        )
        broken = copy.deepcopy(self.tiers)
        broken["phones"][4] = (0.4, 0.6, "ɻ")
        self.assertIn(
            "orphan_or_crossing_phone", self.run_reconstruct(broken)[0]["exclusion_reasons"]
        )
        broken = copy.deepcopy(self.tiers)
        broken["phones"] = [p for p in broken["phones"] if p[2] != "aj˥˩"]
        self.assertIn(
            "required_phones_missing", self.run_reconstruct(broken)[1]["exclusion_reasons"]
        )

    def test_bounds_diagnostics_and_durations(self):
        self.u["duration"] = 0.9
        self.assertIn("alignment_outside_audio", self.run_reconstruct()[0]["exclusion_reasons"])
        self.u["duration"] = 1.1
        self.assertIn(
            "missing_alignment_diagnostics",
            self.run_reconstruct(diagnostics={})[0]["exclusion_reasons"],
        )
        self.assertIn(
            "extreme_alignment_log_likelihood",
            self.run_reconstruct(diagnostics={"alignment_log_likelihood": -101})[0][
                "exclusion_reasons"
            ],
        )
        self.config["duration_max_seconds"] = 0.3
        self.assertIn(
            "implausible_read_unit_duration", self.run_reconstruct()[0]["exclusion_reasons"]
        )

    def test_long_textgrid_parser_and_corruption(self):
        text = 'File type = "ooTextFile"\nObject class = "TextGrid"\n'
        for index, (name, intervals) in enumerate(self.tiers.items(), 1):
            text += (
                f'item [{index}]:\nclass = "IntervalTier"\nname = "{name}"\n'
                f"intervals: size = {len(intervals)}\n"
            )
            for j, (a, b, label) in enumerate(intervals, 1):
                text += f'intervals [{j}]:\nxmin = {a}\nxmax = {b}\ntext = "{label}"\n'
        self.assertEqual(textgrid(text), self.tiers)
        with self.assertRaises(ValueError):
            textgrid(text.replace("xmin = 0.1", "xmin = -0.1"))
        with self.assertRaises(ValueError):
            textgrid(text.replace("intervals: size = 5", "intervals: size = 6"))

    def test_real_mfa_outputs_and_reproducible_read_units(self):
        fixture = read_json(FIXTURES / "alignment.json")
        for record in fixture["records"]:
            u = record["utterance"]
            path = FIXTURES / (u["utterance_id"] + ".TextGrid")
            self.assertEqual(file_hash(path), record["textgrid_sha256"])
            tiers = textgrid(path.read_text())
            args = (u, tiers, fixture["lexicon"], {"alignment_log_likelihood": -40}, self.config)
            rows = reconstruct(*args)
            self.assertEqual(digest(rows), digest(reconstruct(*copy.deepcopy(args))))
            self.assertEqual(len(rows), len(u["units"]))
            self.assertTrue(all(r["reconstruction_status"] == "candidate" for r in rows))
            self.assertEqual(
                [r["corpus_pinyin"] for r in rows], [r["corpus_pinyin"] for r in u["units"]]
            )

    def test_internal_silence_and_collapsed_phones_quarantined(self):
        broken = copy.deepcopy(self.tiers)
        broken["phones"][3] = (0.25, 0.4, "sil")
        self.assertIn(
            "silence_inside_read_unit", self.run_reconstruct(broken)[0]["exclusion_reasons"]
        )
        self.config["phone_floor_seconds"] = 0.2
        self.assertIn("collapsed_phone_durations", self.run_reconstruct()[0]["exclusion_reasons"])

    def test_t3_context_does_not_invent_internal_phrase_boundaries(self):
        result = t3_contexts(self.run_reconstruct())
        self.assertEqual(result["before_T4"], 1)
        self.assertEqual(result["phrase_position_unknown"], 1)
        self.assertEqual(result["phrase_medial"], 0)


class IsolationTests(unittest.TestCase):
    def test_speaker_split_reproducible_and_disjoint(self):
        speakers = [f"SSB{i:04d}" for i in range(16)]
        a = speaker_split(speakers)
        self.assertEqual(a, speaker_split(list(reversed(speakers)) + speakers))
        self.assertEqual(sorted(a.values()).count("test"), 3)
        rows = [
            {
                "example_id": str(i),
                "speaker_id": s,
                "utterance_id": str(i),
                "pcm_sha256": str(i),
                "partition": a[s],
            }
            for i, s in enumerate(speakers)
        ]
        verify_split(rows)
        bad = copy.deepcopy(rows)
        other = next(r for r in bad if r["partition"] != bad[0]["partition"])
        other["pcm_sha256"] = bad[0]["pcm_sha256"]
        with self.assertRaises(ValueError):
            verify_split(bad)

    def test_label_mutation_cannot_change_audio_features(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "test.wav"
            with wave.open(str(path), "wb") as w:
                w.setnchannels(1)
                w.setsampwidth(2)
                w.setframerate(16000)
                w.writeframes(np.arange(1600, dtype="<i2").tobytes())
            row = {
                "audio": {
                    "reference": str(path),
                    "sha256": file_hash(path),
                    "sample_rate_hz": 16000,
                },
                "start": 0.02,
                "end": 0.08,
                "label": "T3",
                "corpus_tone": 3,
                "corpus_pinyin": "wo3",
                "hanzi": "我",
                "lexical_tone": 3,
            }
            poisoned = {
                **row,
                "label": "T4",
                "corpus_tone": 4,
                "corpus_pinyin": "ma4",
                "hanzi": "骂",
                "lexical_tone": 4,
                "expected_tone": 4,
            }
            self.assertEqual(audio_only_request(row), audio_only_request(poisoned))

            def features(value):
                req = audio_only_request(value)
                pcm, rate, _ = read_audio(req["audio"]["reference"], req["audio"]["sha256"])
                return np.frombuffer(pcm, dtype="<i2")[
                    int(req["start_seconds"] * rate) : int(req["end_seconds"] * rate)
                ]

            np.testing.assert_array_equal(features(row), features(poisoned))

    def test_quality_gate_does_not_infer_review_from_artifacts(self):
        rows = [
            {
                "example_id": str(i),
                "speaker_id": f"SSB{i:04d}",
                "label": "T1",
                "reconstruction_status": "candidate",
            }
            for i in range(4)
        ]
        registry = {r["speaker_id"]: {} for r in rows}
        result = quality_gate(rows, registry, [], stage="pilot")
        self.assertFalse(result["passed"])
        self.assertIn("developer_audio_qa_incomplete", result["blockers"])
        review = {"example_id": "0", "item_sha256": "stale"}
        with self.assertRaises(ValueError):
            quality_gate(rows, registry, [review], stage="pilot")


if __name__ == "__main__":
    unittest.main()
