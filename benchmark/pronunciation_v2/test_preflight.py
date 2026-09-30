"""Regression tests for the pre-model provenance stop gate; no ML dependency."""

import hashlib
import unittest

from preflight import GROUPS, audit_sample, embedded_conflicts, verify_bytes


def row(**changes):
    return {
        "speaker_id": "shtooka:wei-gao",
        "text": "为",
        "pinyin": "wei2",
        "tone": 2,
        "license": "CC BY 2.0 fr",
        "source_asset_id": "commons:1",
        "duration_seconds": 1.0,
        **changes,
    }


class PreflightTests(unittest.TestCase):
    def test_replacement_file_stops_on_three_independent_conflicts(self):
        tags = {
            "SWAC_SPEAK_NAME": "Tan",
            "SWAC_TEXT": "围",
            "SWAC_PRON_PHON": "wéi",
            "LICENSE": "Creative Commons BY-SA 3.0 U.S",
        }
        self.assertEqual(
            embedded_conflicts(row(), tags),
            [
                "embedded_speaker_conflicts_with_wei_gao_group",
                "embedded_text_differs_from_manifest",
                "embedded_sharealike_vs_selected_license_unresolved",
            ],
        )

    def test_normal_wei_gao_carriage_return_tags(self):
        tags = {
            "SWAC_SPEAK_NAME": "Wei Gao\r",
            "SWAC_TEXT": "为\r",
            "SWAC_PRON_PHON": "wéi\r",
            "LICENSE": "Creative Commons BY\r",
        }
        self.assertEqual(embedded_conflicts(row(), tags), [])

    def test_collection_license_alone_is_checked(self):
        self.assertIn(
            "embedded_sharealike_vs_selected_license_unresolved",
            embedded_conflicts(row(), {"SWAC_COLL_LICENSE": "Creative Commons BY-SA"}),
        )

    def test_tone_conflict_does_not_relabel(self):
        original = row()
        self.assertEqual(
            embedded_conflicts(original, {"SWAC_PRON_PHON": "wèi"}),
            ["embedded_pinyin_differs_from_manifest"],
        )
        self.assertEqual(original["tone"], 2)

    def test_unmarked_tag_does_not_assert_conflicting_tone(self):
        self.assertEqual(
            embedded_conflicts(row(), {"SWAC_PRON_PHON": "wei"}),
            ["embedded_pinyin_unmarked_or_unparseable"],
        )

    def test_byte_verification_detects_change(self):
        data = b"unchanged original"
        original = {
            "source_bytes": len(data),
            "source_sha1": hashlib.sha1(data).hexdigest(),
            "audio_sha256": hashlib.sha256(data).hexdigest(),
        }
        self.assertEqual(verify_bytes(original, data), [])
        self.assertEqual(len(verify_bytes(original, data + b"x")), 3)

    def test_audit_covers_every_group_and_tone_deterministically(self):
        rows = [
            row(speaker_id=g, tone=t, source_asset_id=f"{g}:{t}:{d}", duration_seconds=d)
            for g in GROUPS
            for t in range(1, 5)
            for d in (0.6, 1.0, 1.65)
        ]
        issues = {r["source_asset_id"]: [] for r in rows}
        sample = audit_sample(rows, issues)
        self.assertEqual(len(sample), 32)
        self.assertEqual(sample, audit_sample(list(reversed(rows)), issues))

    def test_singletons_are_auxiliary_and_anomalies_always_audited(self):
        rows = [row(source_asset_id=f"commons:{i}", duration_seconds=i) for i in (1, 2, 3)]
        rows.append(row(speaker_id="shtooka:yue-tan", source_asset_id="singleton"))
        issues = {r["source_asset_id"]: [] for r in rows}
        issues["commons:2"] = ["conflict"]
        sample = audit_sample(rows, issues)
        self.assertEqual(sample["commons:2"], {"metadata_or_integrity_issue"})
        self.assertEqual(sample["singleton"], {"singleton"})
        self.assertNotIn("shtooka:yue-tan", GROUPS)


if __name__ == "__main__":
    unittest.main()
