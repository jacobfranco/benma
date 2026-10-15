// Replay the production TS models on frozen numbers. No providers or audio I/O.
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const root = path.resolve(__dirname, '../..');
const ts = require(path.join(root, 'apps/mobile/node_modules/typescript'));
const cache = new Map();
function load(name) {
  if (cache.has(name)) return cache.get(name);
  // UI is never rendered; only the real exported projection functions execute.
  if (name === 'react-native') return { StyleSheet: { create: x => x } };
  if (name === 'react' || name === 'react/jsx-runtime') return {};
  if (!name.startsWith('@/')) throw Error(`Unexpected import ${name}`);
  const base = path.join(root, name.replace('@/', 'apps/mobile/src/'));
  const filename = fs.existsSync(base + '.ts') ? base + '.ts' : base + '.tsx';
  const module = { exports: {} };
  const code = ts.transpileModule(fs.readFileSync(filename, 'utf8'), {
    compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022, jsx: ts.JsxEmit.ReactJSX }, fileName: filename,
  }).outputText;
  vm.runInNewContext(code, { module, exports: module.exports, require: load }, { filename });
  cache.set(name, module.exports);
  return module.exports;
}
function replay(input) {
  const { classifyPitchShape } = load('@/speech/pitchShape');
  const { classifyToneLikeness } = load('@/speech/toneLikeness');
  const { gradeLearnerPitch, pitchExpectation, pitchGradePresentation } = load('@/speech/learnerPitchGrade');
  const rows = (input.rows ?? []).map(row => {
    const segments = row.segments.map(s => s.map(p => ({ timestamp_seconds: p.t, normalized_semitones: p.st })));
    const flags = row.segments.flat().filter(p => row.flagged_indices?.includes(p.index)).map(p => p.t);
    // Raw branch flags survive even when the flagged frames were excluded from
    // the retained projection. They must not disappear in this offline adapter.
    const shape = row.grouped ? { shape: 'UNCLEAR', reason: 'grouped_timing', features: {}, perturbations: {} }
      : classifyPitchShape(segments, flags, !!row.flagged_indices?.length);
    const observed = classifyToneLikeness(shape, segments);
    const expected = pitchExpectation(input.context[row.id], Object.entries(input.context)
      .filter(([id]) => id.split(':')[0] === row.id.split(':')[0]).map(([, syllable]) => syllable));
    const grade = gradeLearnerPitch(observed, expected, segments.some(s => s.length));
    return { id: row.id, shape, observed, expected, grade, color: pitchGradePresentation[grade.agreement].color };
  });
  const analyses = (input.analyses ?? []).map(analysis => {
    const { pronunciationChunks } = load('@/speech/pronunciationChunks');
    const { gradeChunkPitch } = load('@/speech/chunkPitchGrade');
    return { id: analysis.id, chunks: pronunciationChunks(analysis.data).map(chunk => {
      const result = gradeChunkPitch(analysis, chunk);
      return { text: chunk.text, ...result, color: pitchGradePresentation[result.grade.agreement].color };
    }) };
  });
  return { rows, analyses };
}
module.exports = { load, replay };
if (require.main === module) process.stdout.write(JSON.stringify(replay(JSON.parse(fs.readFileSync(0, 'utf8')))));
