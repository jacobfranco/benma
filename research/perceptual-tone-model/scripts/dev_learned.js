/* Local research presentation only; production never imports this file. */
'use strict';
const $ = id => document.getElementById(id);
let token, recorder, stream, chunks = [], takeId;
function node(tag, text, cls) {
  const el = document.createElement(tag);
  if (text !== undefined) el.textContent = text;
  if (cls) el.className = cls;
  return el;
}
function tone(value) { return value == null ? 'unresolved' : value === 0 ? 'neutral' : `T${value}`; }
function span(value) { return value ? `${value.start_seconds.toFixed(3)}–${value.end_seconds.toFixed(3)} s` : 'unavailable'; }
function probability(value) { return value == null ? '—' : value.toFixed(4); }
async function request(url, options = {}) {
  const response = await fetch(url, options);
  const body = await response.json();
  if (!response.ok) throw new Error(body.message || body.error);
  return body;
}
function audioLink(parent, id, name, label) {
  const button = node('button', label);
  button.onclick = () => {
    document.querySelectorAll('audio').forEach(a => a.pause());
    let player = parent.querySelector('audio');
    if (!player) { player = document.createElement('audio'); player.controls = true; parent.append(player); }
    player.src = `/takes/${id}/${name}`;
    player.play().catch(error => { $('status').textContent = error.message; });
  };
  parent.append(button);
}
function chart(unit) {
  const ns = 'http://www.w3.org/2000/svg';
  const svg = document.createElementNS(ns, 'svg');
  svg.setAttribute('viewBox', '0 0 800 210');
  svg.setAttribute('role', 'img');
  svg.setAttribute('aria-label', `${unit.target.characters} retained F0 contour with tone-bearing crop shaded`);
  const segments = unit.deterministic.segments || [];
  const points = segments.flat().filter(p => Number.isFinite(p.normalized_semitones));
  if (!points.length || !unit.alignment) return node('p', 'F0 contour unavailable; no shape diagnosis.', 'muted');
  const lo = Math.min(...points.map(p => p.normalized_semitones)) - 1;
  const hi = Math.max(...points.map(p => p.normalized_semitones)) + 1;
  const a = unit.alignment.start, b = unit.alignment.end;
  const x = t => 55 + 725 * (t - a) / (b - a);
  const y = v => 175 - 140 * (v - lo) / (hi - lo);
  const add = (tag, attrs, text) => {
    const element = document.createElementNS(ns, tag);
    Object.entries(attrs).forEach(([k, v]) => element.setAttribute(k, v));
    if (text !== undefined) element.textContent = text;
    svg.append(element);
  };
  const pool = unit.spans?.tone_bearing_pooling_span;
  if (pool) add('rect', {x:x(pool.start_seconds), y:25, width:x(pool.end_seconds)-x(pool.start_seconds), height:155, fill:'#deeee8'});
  [lo, (lo+hi)/2, hi].forEach(v => {
    add('line', {x1:55, x2:780, y1:y(v), y2:y(v), stroke:'#dbe0e6'});
    add('text', {x:4, y:y(v)+4, 'font-size':12}, `${v.toFixed(1)}`);
  });
  // Separate retained islands remain separate; never draw across missing F0.
  segments.forEach(s => add('polyline', {points:s.map(p => `${x(p.timestamp_seconds)},${y(p.normalized_semitones)}`).join(' '), fill:'none', stroke:'#325bb0', 'stroke-width':2.5}));
  add('text', {x:55, y:16, 'font-size':12}, 'F0 · semitones relative to utterance baseline; shaded = nucleus/coda');
  add('text', {x:55, y:201, 'font-size':12}, `${a.toFixed(3)} s`);
  add('text', {x:710, y:201, 'font-size':12}, `${b.toFixed(3)} s`);
  return svg;
}
function render(report) {
  takeId = report.take_id;
  $('results').replaceChildren();
  const overview = node('section');
  overview.append(node('h2', report.intended_phrase), node('p', `Intended: ${report.intended_pinyin}`),
    node('p', `${report.rendering_label}: ${report.tone_realization_rendering}`),
    node('p', `Lexical ASR: ${report.asr.transcript || 'unavailable'} · ${report.asr.status}`),
    node('p', `Take ${report.take_id} · ${report.source_kind}`, 'muted'));
  if (report.asr_prompt_mismatch) overview.append(node('p', 'ASR differs from the prompt. Learned inference abstained pending alignment review.'));
  audioLink(overview, takeId, 'canonical.wav', 'Play whole sentence');
  const download = node('a', 'Download report');
  download.href = `/takes/${takeId}/report.json`; download.download = `benma-${takeId}.json`;
  overview.append(document.createTextNode(' '), download);
  const performance = report.performance;
  overview.append(node('p', `Elapsed ${performance.utterance_total_seconds.toFixed(2)} s · alignment ${performance.alignment_seconds.toFixed(2)} s · acoustic ${performance.acoustic_seconds.toFixed(2)} s · inference/report ${performance.inference_and_reporting_seconds.toFixed(2)} s · peak RSS ${performance.process_peak_rss_mib.toFixed(0)} MiB`, 'muted'));
  $('results').append(overview);
  for (const unit of report.units) {
    const target = unit.target, result = unit.comparison;
    const article = node('article', undefined, result.grade === 'unavailable' ? 'unavailable' : result.grade === 'experimental_match' ? 'match' : 'concern');
    article.append(node('h2', `${target.characters} · ${target.pinyin || '?'} · ${result.state}`),
      node('p', `Lexical ${tone(target.lexical_tone)} · expected surface ${tone(target.expected_surface_tone)} · ${target.surface_rule}`),
      node('p', result.interpretation), node('p', `Reason: ${result.reason}`, 'muted'));
    const columns = node('div', undefined, 'grid');
    const learned = node('div');
    learned.append(node('h3', `Expanded: ${unit.expanded.prediction || 'ABSTAIN'}`),
      node('p', `Raw confidence ${probability(unit.expanded.confidence)}`));
    const table = node('table');
    const head = node('tr'); head.append(node('th', 'Family'), node('th', 'Probability')); table.append(head);
    for (const t of ['T1','T2','T3','T4']) { const row = node('tr'); row.append(node('td',t),node('td',probability(unit.expanded.probabilities?.[t]))); table.append(row); }
    learned.append(table);
    if (unit.expanded.reason) learned.append(node('p', unit.expanded.reason));
    const secondary = node('div');
    secondary.append(node('h3', 'Independent diagnostic signals'),
      node('p', `Pilot: ${unit.pilot.prediction || 'ABSTAIN'} · confidence ${probability(unit.pilot.confidence)}`),
      node('p', `Deterministic: ${unit.deterministic.prediction || 'ABSTAIN'} · ${unit.deterministic.observed?.reason || unit.deterministic.reason || ''}`),
      node('p', `Voicing quality: ${unit.deterministic.eligibility?.state || 'unavailable'}`),
      node('p', `Whole unit: ${span(unit.spans?.playback_read_unit)}`),
      node('p', `Nucleus/coda: ${span(unit.spans?.tone_bearing_pooling_span)}`),
      node('p', `Context: ${span(unit.spans?.context)}`));
    columns.append(learned, secondary); article.append(columns, chart(unit));
    const playback = node('div');
    for (const [kind,name] of Object.entries(unit.clips)) audioLink(playback,takeId,name,`Play ${kind}`);
    article.append(playback);
    if (result.explanation) article.append(node('p',result.explanation));
    const details = node('details'); details.append(node('summary','Alignment, F0 features, provenance and model metadata'),node('pre',JSON.stringify(unit,null,2)));
    article.append(details); $('results').append(article);
  }
  for (const chunk of report.chunks) {
    const section = node('section');
    section.append(node('h2', `Linguistic chunk: ${chunk.text}`), node('p', `${chunk.grade} · ${chunk.constituent_states.join(' / ')}`),node('p','Neutral constituents do not receive a numbered-tone correction or veto the chunk.'));
    $('results').append(section);
  }
  $('observation').hidden = false; $('saved').textContent = ''; $('notes').value = '';
}
async function history() {
  const reports = await request('/takes');
  $('history').replaceChildren(node('option','Choose a take'));
  $('history').firstChild.value = '';
  for (const r of reports) { const option=node('option',`${r.intended_phrase} · ${r.take_id.slice(0,8)} · ${r.source_kind}`); option.value=r.take_id; $('history').append(option); }
}
$('history').onchange = async () => {
  if (!$('history').value) return;
  try { render(await request(`/takes/${$('history').value}/report.json`)); }
  catch(error) { $('status').textContent=error.message; }
};
$('record').onclick = async () => {
  try {
    document.querySelectorAll('audio').forEach(a => a.pause());
    stream = await navigator.mediaDevices.getUserMedia({audio:true});
    chunks=[]; recorder = new MediaRecorder(stream);
    recorder.ondataavailable = e => { if(e.data.size) chunks.push(e.data); };
    recorder.onstop = async () => {
      stream.getTracks().forEach(t=>t.stop());
      $('status').textContent='Aligning phones, measuring F0, and running frozen models…';
      $('history').disabled=true;
      try {
        const report=await request('/take',{method:'POST',headers:{'X-Benma-Dev':token,'X-Phrase':encodeURIComponent($('phrase').value)},body:new Blob(chunks,{type:recorder.mimeType})});
        render(report); await history();
        $('status').textContent='Take saved. Inspect the crops first; repeat naturally before considering any change.';
      } catch(error) { $('status').textContent=error.message; }
      finally { $('record').disabled=false; $('history').disabled=false; $('phrase').disabled=false; }
    };
    recorder.start(); $('record').disabled=true; $('stop').disabled=false; $('phrase').disabled=true;
    $('status').textContent='Recording — speak naturally, then stop.';
  } catch(error) { stream?.getTracks().forEach(t=>t.stop()); $('status').textContent=error.message; }
};
$('stop').onclick = () => { $('stop').disabled=true; recorder.stop(); };
$('save').onclick = async () => {
  try { await request('/observation',{method:'POST',headers:{'X-Benma-Dev':token,'Content-Type':'application/json'},body:JSON.stringify({take_id:takeId,category:$('category').value,notes:$('notes').value})}); $('saved').textContent='Saved as an observation, not ground truth.'; }
  catch(error) { $('saved').textContent=error.message; }
};
request('/config').then(async config=>{
  token=config.token; $('record').disabled=false;
  $('status').textContent=`Ready · ${config.verification.baseline.verified_files} baseline files verified.`;
  $('asr-status').textContent=config.asr_requested ? 'Configured live ASR requested. Unavailable providers are reported explicitly.' : 'ASR is off. Alignment uses the displayed prompt as a hypothesis. Start the server with --asr to use configured live ASR.';
  await history();
}).catch(error=>{ $('status').textContent=error.message; });
