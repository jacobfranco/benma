// Replay the actual mobile layout/geometry functions, without rendering React.
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const root = path.resolve(__dirname, '../..');
const ts = require(path.join(root, 'apps/mobile/node_modules/typescript'));
function load(relative) {
  const filename = path.join(root, relative);
  const code = ts.transpileModule(fs.readFileSync(filename, 'utf8'), {
    compilerOptions: {module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022, jsx: ts.JsxEmit.ReactJSX},
    fileName: filename,
  }).outputText;
  const module = {exports: {}};
  vm.runInNewContext(code, {module, exports:module.exports, require(name) {
    if (name === 'react-native') return {StyleSheet:{create:x=>x}};
    if (name === '@/theme') return {colors:{}};
    if (name === 'react' || name === 'react/jsx-runtime') return {};
    throw Error('Unexpected runtime dependency: '+name);
  }}, {filename});
  return module.exports;
}
const {normalizedMine, rawPitch} = load('apps/mobile/src/speech/sentenceToneGraph.ts');
const {normalizedGeometry} = load('apps/mobile/src/components/PitchPlot.tsx');
const input = JSON.parse(fs.readFileSync(0,'utf8'));
const output = input.map(({data, relative}) => {
  const original = JSON.stringify(data);
  const current = normalizedMine(data);
  const graph = data.tone_graph;
  const vals = graph.mine.segments.flat().map(p=>p.normalized_semitones);
  const domain = [Math.min(graph.mine.minimum_semitones, ...vals.map(v=>v-1)),
                  Math.max(graph.mine.maximum_semitones, ...vals.map(v=>v+1))];
  const proposed = normalizedMine({...data,tone_graph:{...graph,mine:relative}});
  const relDomain = [relative.minimum_semitones,relative.maximum_semitones];
  const renamed = JSON.parse(JSON.stringify(data));
  // Change every textual/reference value while keeping the same accepted spans.
  renamed.target = 'unrelated target';
  renamed.syllables.forEach(s=>Object.assign(s, {characters:'字'.repeat(s.character_end-s.character_start),
    pinyin:'unrelated',lexical_tone:4,expected_surface_tone:1}));
  renamed.timing_groups.forEach(g=>g.text='字'.repeat(g.character_end-g.character_start));
  const renamedLayout = normalizedMine({...renamed,tone_graph:{...graph,mine:relative}});
  const geometry = normalizedGeometry(proposed,700,128,relDomain);
  if (JSON.stringify(geometry)!==JSON.stringify(normalizedGeometry(renamedLayout,700,128,relDomain)))
    throw Error('Reference/identity changed geometry');
  if (JSON.stringify(data)!==original) throw Error('Input mutated');
  return {current,proposed,current_domain:domain,relative_domain:relDomain,
    current_geometry:normalizedGeometry(current,700,128,domain),relative_geometry:geometry,
    raw:rawPitch(data),target_independence:true,input_unchanged:true};
});
process.stdout.write(JSON.stringify(output));
