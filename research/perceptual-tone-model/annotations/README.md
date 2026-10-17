# Blinded annotation and import

Read [LISTENER_GUIDE.md](LISTENER_GUIDE.md) with native Mandarin listeners before
collection. The primary judgment concerns contextual acceptability, not contour
matching. Perceived family is a separate optional response.

`preflight` creates `PACKET/public/items.jsonl`, local audio files, the bilingual
guide and `responses.template.jsonl`. Give listeners **only `PACKET/public/`**.
The public allowlist contains the phrase, target Hanzi/index, opaque item ID and
audio timings. It never includes Benma family/grade/support, expected families,
diagnostic collection intent, speaker ID, researcher paths or another answer.
Items are shuffled with the config seed. Stable item IDs depend on recording
content and target identity, never predicted or human labels. All public audio
names are opaque. Wide and full-utterance playback preserve connected speech.

Each listener fills a separate copy of the JSONL response template. Combine the
completed files by concatenating their JSONL lines, then import with the private
map. The command validates the whole batch before writing a new manifest.
Identifiers must be globally unique; repeating the exact same judgment is
idempotent. Altering an existing ID fails. A revision has a new ID, incremented
version and `supersedes` pointing to that listener's current answer for this item.
All previous raw answers remain in the dataset; only the current revision votes.

Example completed response (replace the item ID with one from your packet):

```json
{"item_id":"item-OPAQUE_ID","judgment_id":"round1-listener03-item01","annotator_id":"listener03","acceptability":"borderline","perceived_tone":null,"confidence":null,"notes":"连读里有些不自然，但不能确定有错。","timestamp":"2026-10-15T15:30:00Z","rubric_version":"1.0","version":1,"supersedes":null,"origin":"human"}
```

Default aggregation requires 3 listeners, a unique ≥2/3 majority, normalized
four-label entropy ≤0.6, and no mixed gradable/ungradable votes. The configurable
`unanimous` mode requires all active listeners to agree. Ties, insufficient
judgments and high disagreement keep `aggregate.label: null`; unanimous ungradable
remains `ungradable`. Both are excluded from classifier fitting and kept in
coverage reports. Confidence is preserved but not used to weight votes.

The importer requires explicit human provenance. Only the dedicated Stage-0
Python workflow permits mock judgments, and only on rows marked Stage 0. Software
can reject mislabeled formats and known synthetic provenance; it cannot establish
that a person actually listened. Independent listener recruitment and collection
audit remain part of real data collection. An adjudication UI and concealed-repeat
scheduling are future collection improvements, not implemented here.
