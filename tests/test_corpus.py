from __future__ import annotations

from pathlib import Path

from benchmark.corpus.seed import seed_manifest
from benchmark.models import CorpusManifest

ROOT = Path(__file__).resolve().parents[1]


def test_checked_manifest_matches_seed() -> None:
    checked = CorpusManifest.model_validate_json(
        (ROOT / "benchmark/corpus/manifests/benma-v0.1.0.json").read_text(encoding="utf-8")
    )
    assert checked == seed_manifest()


def test_corpus_has_all_sixteen_tone_pairs() -> None:
    tags = {
        tag for sample in seed_manifest().samples for tag in sample.tags if tag.startswith("pair_")
    }
    assert tags == {f"pair_{left}{right}" for left in range(1, 5) for right in range(1, 5)}


def test_corpus_contains_required_lexical_examples() -> None:
    texts = {sample.intended_text for sample in seed_manifest().samples}
    assert {"买", "卖", "水", "睡", "生活", "后面", "睡觉"} <= texts


def test_corpus_has_full_pilot_and_eventual_target() -> None:
    manifest = seed_manifest()
    assert len(manifest.samples) == 114
    assert manifest.desired_sample_count == 384
    assert all(sample.status == "planned" and sample.audio is None for sample in manifest.samples)


def test_corpus_has_adversarial_and_negative_strata() -> None:
    all_tags = {tag for sample in seed_manifest().samples for tag in sample.tags}
    assert {"adversarial_context", "nonsense", "silence", "sentence_corruption"} <= all_tags
