// Offline product verdicts from the actual pure learner model. No app/network starts.
// node scripts/review-verdicts.cjs <recomputation.json> <output.json>
// Optional reviewed labels: BENMA_REVIEWED_LABELS=<JSON {"utterance_id:syllable_index": 1..4}>
const fs = require('node:fs');
const path = require('node:path');
const ts = require('typescript');
const vm = require('node:vm');
const source = fs.readFileSync(path.resolve(__dirname, '../src/speech/learnerVerdict.ts'), 'utf8');
const compiled = ts.transpileModule(source, { compilerOptions: { module: ts.ModuleKind.CommonJS } }).outputText;
const context = { exports: {} };
vm.runInNewContext(compiled, context);
const rows = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
const labels = process.env.BENMA_REVIEWED_LABELS ? JSON.parse(fs.readFileSync(process.env.BENMA_REVIEWED_LABELS, 'utf8')) : {};
let labeled = 0, mismatches = 0, unclear = 0;
for (const row of rows) row.syllables.forEach((s, index) => {
  s.old_learner_verdict = context.exports.learnerVerdict(s.expected, s.old);
  s.new_learner_verdict = context.exports.learnerVerdict(s.expected, s.new);
  const label = labels[`${row.utterance_id}:${index}`];
  if ([1,2,3,4].includes(label)) {
    labeled++;
    if (s.new.classification === 'unclear') unclear++;
    else if (s.new.classification !== `${label}-like`) mismatches++;
  }
});
fs.writeFileSync(process.argv[3], JSON.stringify({ reviewed_labels: labeled,
  mismatch_rate_all_reviewed: labeled ? mismatches/labeled : null,
  unclear_rate_all_reviewed: labeled ? unclear/labeled : null,
  pilot_recordings_added: 0, rows }, null, 2)+'\n');
