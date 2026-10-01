# Manual sentence study: 14 attempts

No recordings were fabricated or collected for this packet. Record each numbered item as a separate file; ordinary comfortable speech, not a tone drill. A quiet setting is helpful. Keep each under 30 seconds for the existing Azure short-audio path. Do not repeatedly record until the system agrees. Optional notes may describe hesitation, noise or a consciously altered sound.

Pinyin below is a **reading guide**, not acoustic gold. Spaces roughly group words. It uses dictionary/citation tone marks (including yī/bù and third tones); ordinary surface changes are described in the phenomenon column. Unmarked syllables are neutral. Tone marks do not prescribe a measured contour in running speech.

| ID | Intended Chinese | Pinyin guide | Rough meaning | Phenomenon / instruction |
| --- | --- | --- | --- | --- |
| S01 | 今天天气不错，我们出去走走吧。 | Jīntiān tiānqì bùcuò, wǒmen chūqù zǒuzou ba. | The weather is nice today; let's go for a walk. | Fully natural/correct-intent baseline; several tone combinations, 不 before T4, neutral 们/吧 and reduplication. Speak naturally; “correct-intent” is not a gold pronunciation label. |
| S02 | 我昨天晚上跟朋友去吃饭了。 | Wǒ zuótiān wǎnshang gēn péngyou qù chīfàn le. | I went to eat with friends last night. | 13 written syllable candidates; useful 8–15-syllable sentence, lexical neutral syllables and multi-character words. Natural pace. |
| S03 | 你想买哪种水果？ | Nǐ xiǎng mǎi nǎ zhǒng shuǐguǒ? | What kind of fruit do you want to buy? | Long consecutive T3 chain with prosodic grouping. Natural phrasing; do not force full dipping T3 on every character. |
| S04 | 我觉得这个办法很好。 | Wǒ juéde zhège bànfǎ hěn hǎo. | I think this method is good. | Reviewed 很好 T3 pair plus connected/half-third possibilities. Natural speech. |
| S05 | 我想买一个新的杯子。 | Wǒ xiǎng mǎi yī ge xīn de bēizi. | I'd like to buy a new cup. | 一 in a quantity phrase, neutral 个/的/子; ordinary 一个 commonly yí ge, but neutral classifier handling may be unresolved by current rules. Do not exaggerate. |
| S06 | 请给我一杯热茶。 | Qǐng gěi wǒ yī bēi rè chá. | Please give me a cup of hot tea. | 一 before T1 normally yì; short T3 sequence; consonants and multi-character grouping. Natural speech. |
| S07 | 这不是我的手机。 | Zhè bù shì wǒ de shǒujī. | This isn't my phone. | 不 before T4 normally bú; neutral 的; multicharacter noun. Natural speech. |
| S08 | 我今天不想喝咖啡。 | Wǒ jīntiān bù xiǎng hē kāfēi. | I don't want coffee today. | 不 before T3 ordinarily stays bù; connected third tone. Natural speech. |
| S09 | 妈妈在家等着我们呢。 | Māma zài jiā děngzhe wǒmen ne. | Mom is waiting for us at home. | Reviewed lexical neutral 妈妈 plus 着/们/呢; inspect duration and missing F0 without demanding fixed neutral pitch. Natural speech. |
| S10 | 等我下班以后，我们再一起去吃饭。 | Děng wǒ xiàbān yǐhòu, wǒmen zài yīqǐ qù chīfàn. | After I finish work, let's go eat together. | Complex clause, 一起 (normally yìqǐ; current restricted 一 rules may abstain), several multi-character words. Speak at your normal faster conversational pace, not an artificial speed challenge. |
| S11 | 我想买一杯咖啡。 | Wǒ xiǎng mǎi yī bēi kāfēi. | I'd like to buy a cup of coffee. | Deliberate lexical-tone manipulation: say 买 as mài (T4), keeping its consonant/vowel and everything else as natural as possible. Intended text stays 买. Declared manipulation is known; actual realization still needs evidence. |
| S12 | 这附近有四家咖啡店。 | Zhè fùjìn yǒu sì jiā kāfēidiàn. | There are four cafés nearby. | Deliberate consonant manipulation: say 四 sì as shì, retaining T4 and the rest of the sentence. Do not change other words. Inspect lexical substitution separately from physical cause. |
| S13 | 我要去广州。 | Wǒ yào qù Guǎngzhōu. | I'm going to Guangzhou. | Deliberate **word substitution**: actually say 我要去贵州 (Wǒ yào qù Guìzhōu). Keep intended field 广州. This is a word substitution, not a controlled single-tone error. Preserve whatever ASR returns, including 贵州 if recognized. |
| S14 | 我昨天晚上跟朋友去吃饭了。 | Wǒ zuótiān wǎnshang gēn péngyou qù chīfàn le. | I went to eat with friends last night. | Optional repeat of S02 at a comfortable natural pace. Do not imitate the earlier pitch contour. Tests stability across natural attempts. |

## Recording log

Use local filenames `S01.wav` etc. (other containers accepted through production ffmpeg canonicalization). Save audio outside tracked source/docs, for example a private directory or ignored `services/api/var/connected-study/`. Do not commit recordings. Preserve the original even if converted for analysis.

For each file, record: ID, original path/hash, session/device, exact intended sentence, natural/manipulated/repeat, declared manipulation if any, approximate pace and optional noise/hesitation notes. Leave actual perceived text for the recognizer. Keep S13's stated target as 广州 even though the spoken instruction is 贵州.

Run with and without target using separate output directories if testing the truth boundary. A saved-evidence replay, rather than two live ASR calls, is needed for exact equality comparison: provider nondeterminism across calls must not be mistaken for target contamination. Current `--fixture` mode labels all replayed material synthetic; do not relabel a real capture as synthetic for an empirical study. Use `build_record` on the saved real record's perception/alignment/acoustics to compare target layers, preserving provenance.

## Annotation policy

You are not expected to be a native gold annotator. For S11–S13, the intended manipulation is known, but whether you physically realized it as planned is not automatically known. For other attempts, record observations and obvious failures; do not label every tone right/wrong by impression. ASR agreement is not gold and dictionary tones are not measured surface tones. Later native/phonetic review, if required, is a separately scoped annotation step with uncertain/disputed labels retained.
