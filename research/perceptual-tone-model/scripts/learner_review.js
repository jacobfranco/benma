/* Alignment-only human review. No guesses, automatic passes or tone-family questions. */
'use strict';
const packet = JSON.parse(document.querySelector('#packet').textContent);
const storageKey = `learner-alignment:${packet.packet_sha256}`;
const status = document.querySelector('#status');
const reviewer = document.querySelector('#reviewer');
const sections = [...document.querySelectorAll('section[data-id]')];
const heard = new Map();
for (const section of sections) {
  heard.set(section.dataset.id, new Set());
  for (const button of section.querySelectorAll('[data-play]')) button.onclick = async () => {
    document.querySelectorAll('audio').forEach(a => {a.pause(); a.currentTime=0;});
    const view = button.dataset.play;
    const audio = section.querySelector(`audio[data-view="${view}"]`);
    try { await audio.play(); } catch (e) { status.textContent = `Playback failed: ${e.message}`; }
  };
  for(const audio of section.querySelectorAll('audio')) audio.onended = () => {
    heard.get(section.dataset.id).add(audio.dataset.view);
  };
}
function collect() {
  return {packet_sha256: packet.packet_sha256, reviewer: reviewer.value.trim(), reviews: sections.map(s => ({
    item_id: s.dataset.id, whole: s.querySelector('[data-decision=whole]').value,
    tone: s.querySelector('[data-decision=tone]').value, notes: s.querySelector('textarea').value,
    heard_all: s.querySelector('[data-heard]').checked && heard.get(s.dataset.id).size === 3,
    listened_views: [...heard.get(s.dataset.id)], reviewed_at: new Date().toISOString()
  }))};
}
function valid(data, complete) {
  if(data.packet_sha256 !== packet.packet_sha256 || !Array.isArray(data.reviews) || data.reviews.length !== sections.length ||
    new Set(data.reviews.map(r=>r.item_id)).size !== sections.length || data.reviews.some(r=>!sections.some(s=>s.dataset.id===r.item_id)))
    throw Error('Wrong packet or incomplete/duplicate item IDs.');
  if(complete && !data.reviewer) throw Error('Enter reviewer name.');
  for(const r of data.reviews) {
    if((r.whole && !packet.whole_choices.includes(r.whole)) || (r.tone && !packet.tone_choices.includes(r.tone))) throw Error('Invalid decision.');
    if(complete && (!r.whole || !r.tone || !r.heard_all)) throw Error(`Complete both decisions and listen to all three clips: ${r.item_id}`);
    if(complete && (r.whole !== 'PASS' || r.tone !== 'PASS') && !r.notes.trim()) throw Error(`Add boundary/ownership notes: ${r.item_id}`);
  }
}
function restore(data) {
  valid(data, false);
  reviewer.value = data.reviewer || '';
  for(const s of sections) {
    const r = data.reviews.find(r=>r.item_id === s.dataset.id);
    s.querySelector('[data-decision=whole]').value = r.whole;
    s.querySelector('[data-decision=tone]').value = r.tone;
    s.querySelector('textarea').value = r.notes;
    heard.set(s.dataset.id, new Set((r.listened_views || []).filter(v=>['context','whole','tone'].includes(v))));
    s.querySelector('[data-heard]').checked = r.heard_all;
  }
}
function save() { try {localStorage.setItem(storageKey, JSON.stringify(collect()));} catch {} }
document.addEventListener('change', save);
document.addEventListener('input', save);
function download(complete) {
  try {
    const data = collect(); valid(data, complete); save();
    const url = URL.createObjectURL(new Blob([JSON.stringify(data, null, 2)], {type:'application/json'}));
    const a = document.createElement('a'); a.href=url; a.download=complete?'learner-alignment-QA.json':'learner-alignment-draft.json'; a.click();
    setTimeout(()=>URL.revokeObjectURL(url), 1000);
    status.textContent = complete ? 'QA exported. Send the JSON for validation; no benchmark has been frozen.' : 'Draft saved.';
  } catch(e) {status.textContent=e.message;}
}
document.querySelector('#export').onclick=()=>download(true);
document.querySelector('#draft').onclick=()=>download(false);
document.querySelector('#import').onchange=async e=>{try {restore(JSON.parse(await e.target.files[0].text()));save();status.textContent='Review imported.';}catch(err){status.textContent=err.message;}};
try {const saved=localStorage.getItem(storageKey); if(saved) restore(JSON.parse(saved));} catch {}
