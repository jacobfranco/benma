// Offline research bridge. Execute the existing mobile pure functions, without
// mounting React Native or copying their contour/label rules.
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const root = path.resolve(__dirname, '../..');
const ts = require(path.join(root, 'apps/mobile/node_modules/typescript'));
const cache = new Map();
const files = {
  '@/speech/learnerGestureContour': 'learnerGestureContour.ts',
  '@/speech/normalizedDisplayContour': 'normalizedDisplayContour.ts',
  '@/speech/learnerVerdict': 'learnerVerdict.ts',
  '@/speech/SyllableComparison': 'SyllableComparison.tsx',
};
function load(name) {
  if (cache.has(name)) return cache.get(name);
  if (!files[name]) {
    if (name === 'react-native') return { StyleSheet: { create: x => x } };
    if (name === '@/theme') return { colors: {} };
    if (['react/jsx-runtime', '@/components/PitchPlot'].includes(name)) return {};
    throw new Error(`Unexpected dependency: ${name}`);
  }
  const filename = path.join(root, 'apps/mobile/src/speech', files[name]);
  const code = ts.transpileModule(fs.readFileSync(filename, 'utf8'), {
    compilerOptions: { module: ts.ModuleKind.CommonJS, jsx: ts.JsxEmit.ReactJSX,
      target: ts.ScriptTarget.ES2022 }, fileName: filename,
  }).outputText;
  const module = { exports: {} };
  vm.runInNewContext(code, { module, exports: module.exports, require: load }, { filename });
  cache.set(name, module.exports);
  return module.exports;
}
const { primaryMineContour, unclearContourLabel, lexicalShapes } = load('@/speech/SyllableComparison');
const { normalizedDisplayContour } = load('@/speech/normalizedDisplayContour');
const { learnerVerdict } = load('@/speech/learnerVerdict');
const input = JSON.parse(fs.readFileSync(0, 'utf8'));
process.stdout.write(JSON.stringify(input.map(s => {
  const primary = primaryMineContour(s);
  return {
    primary_contour: primary,
    normalized_primary_contour: normalizedDisplayContour(primary, s.observed_contour),
    verdict: learnerVerdict(s.lexical_tone, s.observed_contour),
    unclear_label: unclearContourLabel(s.observed_contour?.reason),
    canonical_heights_reference_only: lexicalShapes[s.lexical_tone],
    interpolation_is_display_only: true,
  };
})));
