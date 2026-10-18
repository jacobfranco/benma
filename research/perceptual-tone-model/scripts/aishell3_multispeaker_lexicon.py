"""Apply the pilot's dictionary correction procedure to observed new G2P failures."""

import json
import sys
import zipfile

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[1]))
from aishell3_continue import stable_json
from aishell3_multispeaker_acquire import ROOT
from aishell3_round2 import stable_bytes
from perceptual_tone.aishell3 import custom_lexicon, parse_dictionary
from perceptual_tone.aishell3_boundaries import NUCLEI, TONES
from perceptual_tone.common import PACKAGE, file_hash, read_json, read_rows


def build(root=ROOT):
    stage = root / "expansion"
    assets = PACKAGE / ".cache/mfa-work/pretrained_models"
    acoustic = assets / "acoustic/mandarin_mfa.zip"
    with zipfile.ZipFile(acoustic) as archive:
        meta = json.loads(archive.read("mandarin_mfa/meta.json"))
    generated = parse_dictionary((stage / "pinyin.dict").read_text())
    spellings = read_json(stage / "g2p-spelling.json")
    pronunciations = {p: generated[s] for p, s in spellings.items() if s in generated}
    reused = read_json(root / "pilot/lexicon-audit.json")
    for token, pinyin in reused["mapping"].items():
        if pinyin in spellings:
            pronunciations[pinyin] = reused["pronunciations"][token]
    stock_path = assets / "dictionary/mandarin_china_mfa.dict"
    stock = parse_dictionary(stock_path.read_text())
    applied = {}
    for config_name in (
        "aishell3-pronunciations.json",
        "aishell3-multispeaker-pronunciations.json",
    ):
        config = read_json(PACKAGE / "configs" / config_name)
        if config.get("source_sha256", file_hash(stock_path)) != file_hash(stock_path):
            raise ValueError("correction_source_dictionary_changed")
        for pinyin, spec in config["entries"].items():
            if pinyin not in spellings:
                continue
            if tuple(spec["source_phones"]) not in stock.get(spec["source_word"], []):
                raise ValueError("correction_source_phones_not_in_pinned_dictionary")
            if config_name.startswith("aishell3-multispeaker"):
                bases = [p.translate(TONES) for p in spec["source_phones"]]
                contour = {"1": "˥", "2": "˧˥", "3": "˨˩˦", "4": "˥˩", "5": ""}[pinyin[-1]]
                expected = [p + contour if p in NUCLEI else p for p in bases]
                if spec["phones"] != expected or sum(p in NUCLEI for p in bases) != 1:
                    raise ValueError("new_correction_must_preserve_verified_segmental_phones")
            applied[pinyin] = {
                **spec,
                "configuration": config_name,
                "configuration_sha256": file_hash(PACKAGE / "configs" / config_name),
                "rejected_g2p_phones": generated.get(spellings[pinyin]),
            }
            pronunciations[pinyin] = [tuple(spec["phones"])]
    entries, mapping, oovs = custom_lexicon(
        read_rows(stage / "utterances.jsonl"), pronunciations, meta["phones"]
    )
    if oovs:
        raise ValueError("unresolved_oovs:" + ",".join(oovs))
    audit = {
        "oovs": oovs,
        "mapping": mapping,
        "pronunciations": entries,
        "generated_pinyin_dictionary_sha256": file_hash(stage / "pinyin.dict"),
        "stock_dictionary_supported_overrides": applied,
        "acoustic_metadata": meta,
        "models": {
            str(p.relative_to(assets)): {"sha256": file_hash(p), "bytes": p.stat().st_size}
            for p in assets.rglob("*")
            if p.is_file() and p.suffix in {".zip", ".dict"}
        },
    }
    stable_json(stage / "lexicon-audit.json", audit)
    content = "".join(
        word + "\t" + " ".join(phones) + "\n"
        for word in sorted(entries)
        for phones in entries[word]
    )
    stable_bytes(stage / "read-units.dict", content.encode())
    return {
        "alignment_tokens": len(entries),
        "oovs": len(oovs),
        "corrections_applied": len(applied),
    }


if __name__ == "__main__":
    print(json.dumps(build(), indent=2))
