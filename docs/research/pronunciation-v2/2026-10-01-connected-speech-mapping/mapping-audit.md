# Mapping audit

The diagnosis is confirmed, with an important qualification: v1 already accepted **single-character word timing without a reading**, so timing and reading coverage were not identical. The four original saved records contain **36 Han units, 30 accepted timings and 27 resolved readings**. All 36 have explicit Azure `Syllables[].Grapheme/Offset/Duration` entries. No capture is synthetic.

## Code path and every relevant reading gate

1. Production `azure_alignment.timing_payload()` whitelists Word, word timing, miscue status and **Phonemes**. It discards the entire **Syllables/Grapheme** tier, even when a character boundary is explicit. The research v1 harness retained the complete raw response separately, so replay can recover it.
2. `azure_syllable_units(payload, reference, readings)` requires the reading-list length to match the Han count. It maps provider words against the complete reference's alphanumeric sequence in order. For a single-character word it starts with the word interval; for a multi-character word it starts with **no span**.
3. Its only multi-character path requires phone count == character count, a full SAPI syllable-shaped label, and the phone's base pinyin == resolved reading base. Tone digits are ignored for that comparison. Only then is the phone span accepted and `reference_phone_label` attached. Containment allows 1 ms relative to the word. Thus one decision conflates character timing, reading and phone attachment. An empty unresolved reading cannot match any full phone base.
4. Research `alignment_evidence()` calls `perceived_syllables()` and passes `[s.pinyin or "" ...]` to this mapper. It then checks complete lexical text, interval validity, order, overlap, maximum 3-second unit duration and audio containment. These latter checks are independent of reading; they do not cause the six missing spans in this study.
5. `build_record()` receives no accepted timing for those six units, emits `syllable_timing_unresolved`, cannot time-slice F0, and attaches no phone. Reading ambiguity becomes an apparent timing gap. Markdown faithfully renders that mistaken absence; it is not a reporting-only defect.
6. Outside the research path, production `PerceivedSpeechAnalysisService.run().validated()` accepts an exact character label **or** a normalized pinyin match. Its Azure request also passes empty strings for unresolved readings. Exact-character labels need no resolved pinyin, but the Azure mapper has already lost these spans. Native exact-offset ASR timing does not have the pinyin gate.
7. Production `alignment.syllable_labels_match()` likewise accepts exact character **or** matching pinyin, with equal list lengths. `timing.resolve_target_timing()` uses it for target-layer evidence only. Neither function is invoked by the new research grapheme mapper. Production `ReplayAligner` is a separately labeled synthetic equal-duration partitioner; it is **not** the saved-real-evidence replay implemented here and is never invoked by it.
8. `compare_text()` resolves intended readings only after perceived units are built. Its edit/expectation layer never supplies readings or boundaries to perception. No target-relative provider assessment is invoked.

Production files remain unchanged. Research v2 replaces the Azure mapping call with `connected_mapping.grapheme_candidates(raw, text)`, whose signature has **no readings or target**. Phone-only multi-character fallback is deliberately absent in v2. Historical v1 records keep their original version and semantics.

## Reading audit

`perceived_syllables()` iterates contiguous Han runs with exact character offsets. `readings.resolve_run()` already tries longest exact matches in its reviewed supplement and `pypinyin.phrases_dict` before per-character heteronym expansion and restricted grammar/default rules. It is not blindly querying every character first. It does not consult intended text. Exact perception pronunciation tokens may override dictionary readings, but ordinary ASR tokens and scores cannot do that.

The installed and research-pinned **pypinyin 0.55.0** phrase dictionary contains 47,111 entries. Direct inspection found **no exact entries** for 天气, 晚上, 吃饭, 水果, 我要, 哪种, 说说 or 贵州, nor supplements for these phrases. Calling pypinyin on these full phrases with `heteronym=True` also falls back to the same character alternatives. Merely passing Azure's word segmentation therefore cannot safely fix the gaps. In S03 Azure even segments 哪 and 种 separately; full perceived-clause context remains necessary.

| Perceived phrase | Existing resolution | Why remaining ambiguity is retained |
| --- | --- | --- |
| 天气 | tiān + unresolved 气 | qi4 / qi3; no phrase entry |
| 晚上 | wǎn + unresolved 上 | shang4 / shang3; no lexical-neutral phrase entry |
| 吃饭 | unresolved 吃 + fàn | chi1 / qi1; no phrase entry |
| 水果 | shuǐ + unresolved 果 | guo3 / luo3 / guan4; no phrase entry |
| 我要 | wǒ + unresolved 要 | yao4 / yao1 / yao3; no supported grammatical rule |
| 哪种 | both unresolved | character alternatives; no supported classifier-context rule |
| 说说 | both unresolved | shuo1 / shui4 / yue4; no supported reduplication reading/neutral rule |
| 贵州 | guì zhōu | both character readings uniquely resolved; exact perceived word context retained |

The research context pass preserves full-clause decisions and may fill an unresolved character only when an exact perceived word yields an existing **phrase** resolution. It never treats an isolated word as a new grammatical clause, selects the first heteronym, learns readings from Azure phone labels, or introduces a list of these study strings. Existing phrases such as 银行 continue to resolve 行 → háng independently of an intended 行走. In these four captures **zero additional readings resolve**; existing 今天/不错/我们 phrase resolutions remain; 进去 retains dictionary readings. 贵州 is correctly resolved from perceived characters, labeled dictionary with context 贵州, not falsely labeled as a newly discovered phrase-dictionary entry.

The dictionary gap is a documented limitation, not a reason to discard timing. Adding a reviewed phrase lexicon could be a separate change with provenance and held-out phrase tests. No new neutral-tone or reduplication policy is invented in this pass.

## Actual recovered boundaries

S01: 气 (3210–3460 ms), first 说 (5810–5900), second 说 (5910–6000). S02: 上 (2200–2550), 吃 (4430–4810). S03: 果 (3130–3590). S13: none were missing. These are copied provider spans, not splits or estimates. All five requested word regions—天气, 晚上, 吃饭, 水果 and 说说—now retain every provider character interval despite unresolved readings.
