# AISHELL-3 real fixtures

`content.json` contains exact transcript lines from the official OpenSLR93
AISHELL-3 v1.0 `test/content.txt`. It records original line numbers, the member
SHA-256 and the [official archive URL](https://www.openslr.org/resources/93/data_aishell3.tgz).
`speakers.txt` contains excerpts of that archive's `spk-info.txt`.
The [publisher declares Apache-2.0](https://www.openslr.org/93/).
Corpus: Beijing Shell Shell Technology Co., Ltd.; Shi, Bu, Xu, Zhang and Li,
*AISHELL-3: A Multi-speaker Mandarin TTS Corpus and the Baselines*.

`prosody.txt` is an excerpt of `train/label_train-set.txt` from
[AISHELL/AISHELL-3](https://huggingface.co/datasets/AISHELL/AISHELL-3), revision
`f20d5db4a31fe779ef07bb1af4ea92da5c786622`. It is a format fixture; none of this
pass's acquired test utterances has an entry in that train prosody file.

The two `.TextGrid` files are actual outputs of the local 32-utterance MFA pilot,
not invented timing fixtures. `alignment.json` supplies their corpus read units,
hashes and the research dictionary needed to validate phone ownership.
Its absolute audio paths document provenance; these tests require no audio,
network, pretrained model or generated dataset.

Alignment resources: Michael McAuliffe and Morgan Sonderegger, Mandarin MFA
acoustic model v3.0.0, Mandarin (China) MFA dictionary v3.0.0, and Mandarin
(China Pinyin) MFA G2P model v3.0.0; [Montreal Corpus Tools](https://mfa-models.readthedocs.io/),
CC-BY-4.0. The custom tokens and nine pronunciation corrections are research
adaptations, documented in `configs/aishell3-pronunciations.json` and the recovery
report. They do not modify the upstream resources or AISHELL tone labels.

Other test intervals and damaged inputs are explicitly synthetic failure cases.
