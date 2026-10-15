// Execute the actual mobile geometry/display functions on the frozen numeric corpus.
// No audio, provider calls, database writes or screenshot classification.
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const root = path.resolve(__dirname, '../..');
const ts = require(path.join(root, 'apps/mobile/node_modules/typescript'));
const cache = new Map();
function load(name) {
  if (cache.has(name)) return cache.get(name);
  const filename = path.join(root, name.replace('@/', 'apps/mobile/src/') + '.ts');
  const module = { exports: {} };
  const code = ts.transpileModule(fs.readFileSync(filename, 'utf8'), {
    compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 }, fileName: filename,
  }).outputText;
  vm.runInNewContext(code, { module, exports: module.exports, require: load }, { filename });
  cache.set(name, module.exports);
  return module.exports;
}
const { classifyPitchShape } = load('@/speech/pitchShape');
const { shapeDisplay } = load('@/speech/pitchShapeDisplay');
const input = JSON.parse(fs.readFileSync(0, 'utf8'));
process.stdout.write(JSON.stringify(input.map(row => {
  const segments = row.segments.map(s => s.map(p => ({ timestamp_seconds: p.t, normalized_semitones: p.st })));
  const before = JSON.stringify(segments);
  const flags = row.segments.flat().filter(p => row.flagged_indices?.includes(p.index)).map(p => p.t);
  const result = classifyPitchShape(segments, flags);
  const display = shapeDisplay(segments, row.start, row.end);
  if (JSON.stringify(segments) !== before) throw Error('Mutated selected evidence');
  return { id: row.id, result, display };
})));
