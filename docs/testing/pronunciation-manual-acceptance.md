# Pronunciation manual acceptance

## Checkpoint acceptance — 2026-09-18

Real-human Chromium microphone acceptance was performed, as reported by the user:

- **你好** was perceived correctly. Surface expectations showed **你 → Tone 2** and
  **好 → Tone 3**; real learner mini-contours rendered. Mine conservatively showed **Unclear**
  where the acoustic quality gate lacked enough clear pitch.
- **你在干什么?** was perceived correctly in Simplified Chinese, segmented into syllable cards,
  and displayed learner contours per syllable. Mine remained **Unclear** when evidence did not
  meet the quality threshold.

This behavior is accepted for the checkpoint. Mine deliberately reports acoustic tone-like
evidence; it does not establish intended-target correctness in free Conversation. Known-target
Practice retains stronger target-relative semantics. The quality gate has not been weakened
to produce labels and still needs calibration over a larger real-user corpus.

Mini-contour and Expected-vs-Mine UX polish, classifier calibration, final physical **Stop → chart**
latency measurement, and **physical iPhone final acceptance** remain follow-ups. They do not
block this checkpoint. This status supersedes earlier milestone reports that treated human or
physical-device acceptance as a commit gate. Historical fixture and saved-clip measurements
remain separate from these user-reported observations.

## Follow-up checklist

Run `benma-api` and `benma-mobile` in separate terminals. Open Chromium with a real microphone
and sign in. Use live configured providers. This is human acceptance, not a benchmark.

- Say **你好**. Check Chinese script, **nǐ / hǎo**, dictionary **3 + 3** under More detail,
  Expected here **2 + 3**, and Mine where the signal passes the quality gate. An unclear syllable
  must have a debuggable reason. Check the contour, Play mine, assistant text and assistant audio.
- Say **你好，今天我们聊聊周末吧。** Confirm heard text appears with the Pronunciation skeleton
  already present. Assistant and analysis arrivals keep the pronunciation/reply positions stable.
- Check **nǐ hǎo jīn tiān wǒ men liáo liáo zhōu mò ba**. Expected/Mine should be understandable
  without More detail. Mine gets a tone-like label only with real timing and adequate pitch;
  otherwise it must stay unclear. Open More detail and check the connected contour and gaps.
- Play mine; confirm assistant text arrives independently and assistant speech is audible.
- Deliberately change one tone. Check that perceived text remains authoritative, Mine reflects
  measured acoustics, and free speech makes no intended-target correctness claim.
- Say **你好，今天我……**. Pronunciation must remain visible even if meaning stays unresolved.
- In free Practice, repeat one clip and confirm the same feedback without an assistant reply.
- In known-target Practice, prepare **你好**. Check reference speech, Expected/Mine, target-relative
  assessment and the shared chart/details. Lexical and surface-tone labels must stay distinct.
- On a physical iPhone, check recording, analysis UI, AssistantSpeech autoplay/replay,
  ReferenceSpeech playback and playback → recording interruption. Check narrow horizontal
  scrolling and larger text sizes.

The local live setup now uses Praat and explicitly enabled Azure timing against the exact
persisted perceived text. Real saved clips have 2/2, 11/11 and 5/5 syllable coverage. Restart the
API helper to load the updated configuration. The saved 你好 produces 你 2-like and 好 unclear
because of a 15.3104-semitone tracker jump; do not force that second label. New recordings may
differ. Do not treat fixture shapes or equal-duration replay partitions as real timing.

Record pass/fail, device/browser, whether real timing was available, and any screenshot/latency
observations. Physical Stop → useful feedback and audible speaker latency are still unknown.
See the [final implementation and evidence report](../development/perception-alignment-pitch-2026-09-18.md).
