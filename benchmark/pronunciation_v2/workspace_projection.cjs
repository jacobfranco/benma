// Offline audit: execute production projection and PCM cropping, without a player.
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const root = path.resolve(__dirname, '../..');
const ts = require(path.join(root, 'apps/mobile/node_modules/typescript'));
const cache = new Map();
function load(name) {
  if (cache.has(name)) return cache.get(name);
  if (name === 'react-native') return { StyleSheet: { create: x => x } };
  if (name === '@/theme') return { colors: {} };
  if (name === 'react' || name === 'react/jsx-runtime') return {};
  const relative = name.replace('@/', 'apps/mobile/src/');
  const filename = ['.ts', '.tsx'].map(ext => path.join(root, relative + ext)).find(fs.existsSync);
  if (!filename) throw Error(`Unexpected import ${name}`);
  const module = { exports: {} };
  const code = ts.transpileModule(fs.readFileSync(filename, 'utf8'), {
    compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022,
      jsx: ts.JsxEmit.ReactJSX }, fileName: filename,
  }).outputText;
  vm.runInNewContext(code, { module, exports: module.exports, require: load,
    Uint8Array, DataView }, { filename });
  cache.set(name, module.exports);
  return module.exports;
}
const { pronunciationUnits, unitPitch } = load('@/speech/pronunciationWorkspace');
const { exactRecording } = load('@/audio/exactRecording');
const input = JSON.parse(fs.readFileSync(0, 'utf8'));
process.stdout.write(JSON.stringify(input.map(({ data, audioPath, audit = false }) => {
  const before = JSON.stringify(data), units = pronunciationUnits(data);
  const bytes = audioPath ? new Uint8Array(fs.readFileSync(audioPath)) : null;
  let dataStart = 0;
  if (bytes) {
    const view = new DataView(bytes.buffer, bytes.byteOffset, bytes.byteLength);
    for (let at = 12; at + 8 <= bytes.length;) {
      const size = view.getUint32(at + 4, true);
      if (String.fromCharCode(...bytes.slice(at, at + 4)) === 'data') dataStart = at + 8;
      at += 8 + size + size % 2;
    }
    if (!dataStart) throw Error('Missing canonical PCM');
  }
  const project = value => pronunciationUnits(value).map(u => unitPitch(value, u).segments);
  const changedTarget = { ...data, target: '广州', expected_surface_tones: [4, 1] };
  if (JSON.stringify(project(data)) !== JSON.stringify(project(changedTarget)))
    throw Error('Target affected ownership');
  const output = units.map(unit => {
    const cropped = bytes && exactRecording(bytes, unit.start, unit.end);
    if (cropped && !cropped.subarray(44).every((value, i) =>
      value === bytes[dataStart + Math.round(unit.start * 16000) * 2 + i]))
      throw Error('Playback PCM differs from accepted canonical interval');
    return { id: unit.id, text: unit.text, start: unit.start, end: unit.end,
      grouped: unit.grouped, members: unit.members.map(s => s.index),
      contour: unitPitch(data, unit, units),
      playback: { start: unit.start, end: unit.end,
        first_sample: Math.round(unit.start * 16000), last_sample: Math.round(unit.end * 16000),
        samples: cropped ? (cropped.length - 44) / 2 : null } };
  });
  if (JSON.stringify(data) !== before) throw Error('Projection mutated evidence');
  return audit ? { units: output, measurement: require('./measurement_audit.cjs').audit({ data }) } : output;
})));
