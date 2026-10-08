# Validation

Scope: standalone research prototype only. Production mobile/backend files were
not changed. Existing pronunciation/Tone Graph V2 work was not reset, reverted,
stashed, discarded, committed, pushed or deployed.

## Exact Mine + With context continuation results

| Check | Result |
| --- | --- |
| Frozen input integrity | All six canonical file SHA-256 values match saved captures; mono 16 kHz WAV duration agrees within one sample |
| Prototype model/player tests | 11 tests passed using `node benchmark/pronunciation_v2/test_audio_first.cjs` |
| Actual browser UI | Chromium passed six takes at both 320 and 390 px; no document horizontal overflow |
| Layout | Existing compact list retained; two 44 px actions fit on one row at both widths; horizontal alternative still passes |
| Real browser decoding | All six embedded original canonical files decoded |
| Exact sample-window playback | 30 accepted units × 0/40/80 ms = 90 offline browser audio renders; maximum PCM error 0; output stops at scheduled duration |
| Live playback path | 180 card clicks (30 units × 40/80 candidate settings × exact/context/exact) preserve exact Mine and replace each other; whole replay on d47274bc works |
| End/stop/cancellation | Real audio-clock end, rapid mixed taps across cards/takes, stale decode/end listeners, explicit stop, candidate/take changes, decode retry, visibility and page-exit cleanup covered; back/forward cached page stays reusable |
| Grouping/accessibility | One 雨伞 card with one exact and one context button; no 雨/伞 clips; explicit labels and explanations; action-specific focus/pressed state; visible status text |
| Target isolation | Explicit 广州/贵州 model regression; browser target edits leave frozen cards unchanged |
| Surfaces | Mock Practice/Free Practice expanded; Conversation collapsed with whole replay visible |
| Details | All 1,184 saved selected points across 63 segments rendered; timestamps and values unchanged; nested Raw equals original stored frame JSON |
| Source preservation | Continuation baseline: 1,016 existing tracked/untracked files; only the nine listed prototype/documentation files changed; no deletions or production changes (see context-preservation.json) |
| Research code checks | JavaScript syntax checks; Python Ruff check and format check passed |
| Working-tree whitespace | `git diff --check` passed |

Eleven focused tests cover character/group/no-timing cards, fail-closed synthetic and
invalid timing, timing independently usable without pitch/reading, status wording,
gesture suppression, target independence, padding/clamping, playback lifecycle,
rapid asynchronous races and decode failure/retry. Added action-specific tests cover
all 30 units at both candidates and stale asynchronous work across cards/takes. `incomplete` is tested with an
explicit mutated presentation fixture: none of the physical six has that state.

The browser compares exact stored selected arrays before/after interactions.
Detailed point counts are 253 / 189 / 214 / 224 / 164 / 140 in requested take order.
These are the complete More Detail counts, not the old timing-owned Mine counts;
out-of-unit selected measurements remain available, including all no-timing data.

## Reproduce

```sh
python benchmark/pronunciation_v2/audio_first_report.py
node benchmark/pronunciation_v2/test_audio_first.cjs
node benchmark/pronunciation_v2/audio_first_browser_check.cjs
node --check benchmark/pronunciation_v2/audio_first_model.cjs
node --check benchmark/pronunciation_v2/audio_first_browser_check.cjs
.venv/bin/ruff check benchmark/pronunciation_v2/audio_first_report.py
.venv/bin/ruff format --check benchmark/pronunciation_v2/audio_first_report.py
git diff --check
```

No dependency/model downloads are part of these commands. In this continuation,
sandboxed Chromium again could not start (ECONNRESET); approved escalation ran the
offline test. The first expanded browser run exposed an incorrect test assumption
that closed details have zero child rectangles. The assertion now uses actual
visibility (`checkVisibility`), and the complete browser suite passed.

Prior-pass execution notes: Run the Python source
directly with stdlib Python; `python -m benchmark...` on the system interpreter
initially failed because the unrelated benchmark package imports Pydantic. The
direct command avoids that dependency. The first sandboxed Chromium attempt could
not start; the offline check succeeded after approved sandbox escalation. Chromium
blocks HTTP/HTTPS and uses a remote-debugging pipe. Initial Python formatting/line
length findings were fixed, then the relevant checks passed.

## Artifacts and inspection

- [Local viewer](../../../../services/api/var/audio-first-feedback/viewer.html)
- [Browser results](../../../../services/api/var/audio-first-feedback/browser-results.json)
- [Continuation preservation check](../../../../services/api/var/audio-first-feedback/context-preservation.json)
- [Primary list at 390 px](../../../../services/api/var/audio-first-feedback/figures/40357072-390-list.png)
- [Primary horizontal alternative](../../../../services/api/var/audio-first-feedback/figures/40357072-horizontal.png)
- [a5acd04c full list](../../../../services/api/var/audio-first-feedback/figures/a5acd04c-full-list.png)
- [No-timing control at 320 px](../../../../services/api/var/audio-first-feedback/figures/d47274bc-320-list.png)
- [Collapsed Conversation](../../../../services/api/var/audio-first-feedback/figures/conversation-collapsed.png)
- [Continuation final git state](../../../../services/api/var/audio-first-feedback/context-final-git-state.txt)
- [Current context playback report](context-playback.md)
- [Physical listening sheet — pending](listening-review.md)

The continuation primary 390 px, short-take 320 px, and collapsed Conversation
screenshots were visually inspected; remaining screenshots are available for review. The browser also captures each
take at both widths and a full-page list capture for every take. Files containing
audio/data/screenshots stay under the pre-existing ignored `services/api/var/` path;
the source template and compact review artifact are reviewable repository additions.

No physical phone playback/listening session was performed. Browser audio scheduling
and zero PCM error do not establish acoustic naturalness, segment intelligibility,
mobile speaker behavior, assistive-technology usability, or learner preference.
No native/web production test suites, exports or backend suites were rerun because
their code did not change. No acoustic/model research was rerun.

## Original prototype files (prior pass)

- `benchmark/pronunciation_v2/audio_first_model.cjs`
- `benchmark/pronunciation_v2/audio_first_report.py`
- `benchmark/pronunciation_v2/audio_first_viewer.html`
- `benchmark/pronunciation_v2/audio_first_browser_check.cjs`
- `benchmark/pronunciation_v2/test_audio_first.cjs`
- This documentation directory: `README.md`, `product-model.md`,
  `six-take-review.md`, `playback.md`, `validation.md`, `replay.json`.

No production files changed. `docs/development/tone-graph-v2.md` is intentionally
unchanged because cards were not integrated. The final ordinary `git diff --stat`
includes the large pre-existing tracked diff and omits all untracked additions;
it must not be attributed to this pass.

## Files changed by this continuation

- `audio_first_model.cjs`: explicit exact/context methods, distinct action state and
  labels; accepted evidence construction unchanged apart from playback labels.
- `audio_first_viewer.html`: two card buttons; context-only 40/80 selector; semantics,
  focus/pressed state, and back/forward-cache-safe page lifecycle.
- `test_audio_first.cjs`, `audio_first_browser_check.cjs`: focused action, timing,
  cancellation, accessibility, surface and lifecycle coverage.
- This directory: `README.md`, `product-model.md`, `playback.md`, `validation.md`;
  `replay.json` regenerated for the new playback labels only.
- Added `context-playback.md` and `listening-review.md`.

Production gate A/B/C and perceptual decisions 1–4 remain pending. The user agreed
to review the prepared viewer; no listening judgments have been supplied yet.
The single remaining product issue is the missing exact/40/80 listening comparison
needed to establish context usefulness and a global window. No production constant
was chosen. Model/browser checks cannot fill in those listening results.
