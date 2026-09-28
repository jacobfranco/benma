// Offline developer evidence. No app network or providers. Read-only snapshots.
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),ts=require('typescript');
const {performance}=require('node:perf_hooks');
const base=path.resolve(__dirname,'../src'), cache={};
function moduleFrom(source,imports={}){
 const context={exports:{},require:n=>{if(n in imports)return imports[n];throw Error(n);}};
 vm.runInNewContext(ts.transpileModule(source,{compilerOptions:{module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2022}}).outputText,context);
 return context.exports;
}
function load(name){if(cache[name])return cache[name]; const source=fs.readFileSync(`${base}/speech/${name}.ts`,'utf8');return cache[name]=moduleFrom(source,{'@/speech/learnerGestureContour':name==='learnerGestureContour'?{}:load('learnerGestureContour')});}
const gesture=load('learnerGestureContour'), normalize=load('normalizedDisplayContour'), verdict=load('learnerVerdict');
function primary(source,imports={}){return moduleFrom(source.slice(source.indexOf('export function primaryMineContour'),source.indexOf('export function unclearContourLabel')),imports).primaryMineContour;}
const oldPrimary=primary(fs.readFileSync('/tmp/benma-consistency-before/SyllableComparison.tsx','utf8'));
// The extracted helper refers to a module-scope import; supply its lexical binding.
const nowPrimary=moduleFrom('const {learnerGestureContour}=require("gesture");\n'+fs.readFileSync(`${base}/speech/SyllableComparison.tsx`,'utf8').split('export function primaryMineContour')[1].split('export function unclearContourLabel')[0].replace(/^/, 'export function primaryMineContour'),{gesture}).primaryMineContour;
const oldNormalize=moduleFrom(fs.readFileSync('/tmp/benma-consistency-before/normalizedDisplayContour.ts','utf8')).normalizedDisplayContour;
const output=path.resolve(__dirname,'../../../docs/calibration/2026-09-25-consistency');
const fresh=JSON.parse(fs.readFileSync(`${output}/fresh-diagnostics.json`));
const results=JSON.parse(fs.readFileSync('/tmp/benma-consistency-corpus/results-after.json'));
const range=d=>{const v=d.segments.flat().map(p=>p.normalized_semitones);return Math.max(...v)-Math.min(...v);};
const rows=fresh.map(r=>{
 const s=results.find(x=>x.attempt.id===r.attempt_id).syllables[0], old=r.result.syllables[0];
 const before=oldNormalize(oldPrimary(old),old.observed_contour),after=normalize.normalizedDisplayContour(nowPrimary(s),s.observed_contour);
 return {target:r.target,attempt_id:r.attempt_id,before,after,verdict:verdict.learnerVerdict(s.expected_surface_tone,s.observed_contour),before_range_st:range(before),after_range_st:range(after),before_pixel_range:range(before)/(before.maximum_semitones-before.minimum_semitones)*38,after_pixel_range:range(after)/(after.maximum_semitones-after.minimum_semitones)*38};
});
const s=results.find(r=>r.attempt.id===fresh[0].attempt_id).syllables[0];
for(let i=0;i<1000;i++)normalize.normalizedDisplayContour(nowPrimary(s),s.observed_contour);
const times=[];for(let run=0;run<31;run++){const start=performance.now();for(let i=0;i<1000;i++)normalize.normalizedDisplayContour(nowPrimary(s),s.observed_contour);times.push((performance.now()-start)/1000);}times.sort((a,b)=>a-b);
fs.writeFileSync(`${output}/display-traces.json`,JSON.stringify({rows,primary_transform_ms:{median:times[15],p95:times[29]},semantics:'Bin timestamps are representative centers, not measured F0 frames. Linear connections are display-only.'},null,2)+'\n');
const acoustic=JSON.parse(fs.readFileSync(`${output}/acoustic-traces.json`))[0];
const primaryContour=rows[0].after,filtered=acoustic.full_filtered;
const rawSegments=[];let seg=[];for(const p of acoustic.raw_window){if(p.normalized_semitones==null){if(seg.length)rawSegments.push(seg);seg=[];}else seg.push(p);}if(seg.length)rawSegments.push(seg);
function plot(segments,title,caption,fit){
 const points=segments.flat(),min=fit?Math.min(...points.map(p=>p.timestamp_seconds)):.37,max=fit?Math.max(...points.map(p=>p.timestamp_seconds)):1.21;
 const sorted=points.map(p=>p.normalized_semitones).sort((a,b)=>a-b),center=fit?0:(sorted[Math.floor((sorted.length-1)/2)]+sorted[Math.floor(sorted.length/2)])/2;
 return `<section><h2>${title}</h2><svg viewBox="0 0 340 240"><rect x="20" y="20" width="300" height="180" fill="#f6f9fc" stroke="#cad2dc"/>${[-4,-2,0,2,4].map(v=>`<path d="M20 ${110-v*22.5} H320" stroke="#dde4ee"/><text x="0" y="${114-v*22.5}" font-size="10">${v}</text>`).join('')}${segments.map(s=>`<polyline fill="none" stroke="#176b86" stroke-width="2" points="${s.map(p=>`${20+(p.timestamp_seconds-min)/(max-min)*300},${110-(p.normalized_semitones-center)*22.5}`).join(' ')}"/>`).join('')}<text x="20" y="222" font-size="12">${fit?'Representative bin positions':`${min}–${max} seconds; measured time`}</text></svg><p>${caption}</p></section>`;
}
const html=`<!doctype html><meta charset="utf-8"><style>body{font:17px system-ui;margin:30px;color:#183241;background:#fff}main{display:flex;gap:24px}section{width:340px}h2{font-size:19px}p{font-size:14px;line-height:1.5}svg{width:340px}</style><h1>Fresh 妈: one recording, three evidence views</h1><p>Attempt ${fresh[0].attempt_id} · 2026-09-25 14:55:14 EDT · 1-like / moderate / Matches</p><main>${plot(primaryContour.segments,'PRIMARY · judged broad gesture','Exact five medians. 1.4544 st broad range. No flattening or target template.',true)}${plot(filtered.segments,'MORE DETAIL · filtered F0','All 58 retained frames. 5.2764 st range; onset and offset remain visible.',false)}${plot(rawSegments,'RAW · measured F0','All raw F0 observations in the aligned interval. 5.3585 st voiced range; null gaps retained.',false)}</main><p>Shared ±4-semitone scale, median-centered per representation. Full detail uses measured time; the compact primary fits the representative bin centers. These views answer different questions.</p>`;
fs.writeFileSync(`${output}/tone1-evidence.html`,html);
console.log(rows.map(r=>({target:r.target,verdict:r.verdict,before_px:r.before_pixel_range,after_px:r.after_pixel_range})));console.log('primary transform ms',times[15],times[29]);
