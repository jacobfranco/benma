# Bounded public discovery log

Study directory date: 2026-10-01. Actual UTC times are in retrieval receipts.
Started on branch pronunciation-v2-research with a clean working tree. No commits
or pushes. No production code changes. No external messages or data requests sent.

Search scope: GitHub, Hugging Face, Zenodo, Figshare, OpenSLR, institutional speech
corpora and original phonetics/pronunciation publications. Stop after 21 plausible
source entries plus the directly linked documentation needed to resolve the
qualifying lead. This is a bounded search, not proof that all public data has been
exhausted. Sources were investigated for rights, identities and asset structure;
model difficulty and reported classifier accuracy were not selection criteria.

Queries included Mandarin isolated syllable corpus; Mandarin tone production
dataset; Mandarin monosyllabic corpus download speakers; Chinese isolated word
OpenSLR; site:huggingface.co/datasets Mandarin tone speaker;
site:zenodo.org Mandarin tone audio dataset; site:figshare.com Mandarin tone
recordings; CN_Mono corpus download; Tone Perfect license; MCAE-Monosyllable
license; EMA-MAE license; SAIT-EMA data availability.

The search followed GitHub tone-classification repositories to the original MSU
Tone Perfect source, and pronunciation-recognition publications to CN_Mono.
Isolated-word literature led to ManDi, CASS-AGING, MCAE and EMA-MAE. The latter
search exposed SAIT-EMA; its original publication linked the Zenodo data deposit.
The HF check included apparently promising “segment” and “syllable” names, which
proved to be full sentences, measurement-only datasets or synthetic voices.
Figshare and Zenodo complete release file lists distinguished recordings from
supplemental result documents. Source details and evidence URLs are in the CSV.

Documentation downloads were individually capped at 3 MB, later 6 MB for the
4.98 MB MCAE spreadsheet. The qualifying SAIT transcript archive had its exact
9,392,380-byte size verified; its prompt archive is only 11,426 bytes. No large
speaker archive was acquired whole. All 18 speaker central directories were
inspected, followed by one preselected set, with source and decoded-byte checks.
There was no forced alignment, ASR, pitch analysis, audio listening or model use.

Access failures were preserved rather than bypassed: tone.lib.msu.edu returned
403; the owner article also returned 403 through the shell while the ordinary
web research tool rendered its published text. Some direct CC legalcode pages
returned 403; their public deeds were read through web research, and MCAE's full
NC legal text was supplied directly by the OSF license API. One guessed CN_Mono
paper URL (W12-5807) proved to be unrelated; it was discarded as evidence and
replaced with the correct W12-5805 linked by the search. One M001 ZIP-directory
range was truncated and failed closed; the same metadata request was manually
resumed and completed, retaining all previously successful indexes. No denied
request was rerouted to circumvent an access control.

Historical overlap scan: read all prior research corpus/selection/candidate
manifests plus the v0.1.0 corpus manifest, and recursively enumerate local audio
under benchmark/corpus/recordings and ~/.cache/benma, excluding the new cache.
Also include every extant local path named by those historical manifests. The
result is 7,983 metadata rows and 700 distinct local file paths, all redecoded.
Raw/PCM hashes and input-file hashes are retained in historical-overlap-index.json.
No historical model predictions or model behavior reports were consulted.
