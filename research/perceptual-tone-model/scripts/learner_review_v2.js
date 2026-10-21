/* Alignment integrity only. Metadata is packet-bound; repeated exports are byte-stable. */
'use strict';
const packet = JSON.parse(document.querySelector('#packet').textContent);
const storageKey = `learner-alignment:${packet.packet_sha256}`;
const status = document.querySelector('#status');
const reviewer = document.querySelector('#reviewer');
const sections = [...document.querySelectorAll('section[data-id]')];
const items = new Map(packet.items.map(i=>[i.item_id,i]));
const heard = new Map(sections.map(s=>[s.dataset.id,new Set()]));
const revisions = new Map();
for(const section of sections) {
  for(const button of section.querySelectorAll('[data-play]')) button.onclick=async()=>{
    document.querySelectorAll('audio').forEach(a=>{a.pause();a.currentTime=0;});
    try {await section.querySelector(`audio[data-view="${button.dataset.play}"]`).play();}
    catch(e){status.textContent=`Playback failed: ${e.message}`;}
  };
  for(const audio of section.querySelectorAll('audio')) audio.onended=()=>{
    heard.get(section.dataset.id).add(audio.dataset.view);save();
  };
}
function collect() {
  const name=reviewer.value.trim();
  const reviews=sections.map(s=>{
    const item=items.get(s.dataset.id), listened=heard.get(s.dataset.id);
    const content={whole:s.querySelector('[data-decision=whole]').value,
      tone:s.querySelector('[data-decision=tone]').value,notes:s.querySelector('textarea').value,
      heard:{context:listened.has('context'),whole:listened.has('whole'),tone:listened.has('tone')},
      heard_all:s.querySelector('[data-heard]').checked && listened.size===3,reviewer:name};
    const fingerprint=JSON.stringify(content), previous=revisions.get(item.item_id);
    const reviewed_at=previous?.fingerprint===fingerprint?previous.reviewed_at:new Date().toISOString();
    revisions.set(item.item_id,{fingerprint,reviewed_at});
    return {item_id:item.item_id,unit_id:item.unit_id,source_id:item.source_id,
      item_sha256:item.item_sha256,alignment_flags:item.alignment_flags,
      ...content,reviewed_at};
  });
  return {schema:packet.schema,packet_sha256:packet.packet_sha256,reviewer:name,reviews};
}
function valid(data,complete) {
  if(data.schema!==packet.schema)throw Error('Wrong review schema.');
  if(data.packet_sha256!==packet.packet_sha256 || !Array.isArray(data.reviews) ||
     data.reviews.length!==sections.length || new Set(data.reviews.map(r=>r.item_id)).size!==sections.length)
    throw Error('Wrong packet or incomplete/duplicate item IDs.');
  if(complete && !data.reviewer?.trim())throw Error('Enter reviewer name.');
  for(const r of data.reviews) {
    const item=items.get(r.item_id);
    if(!item || ['unit_id','source_id','item_sha256'].some(k=>r[k]!==item[k]) ||
       JSON.stringify(r.alignment_flags)!==JSON.stringify(item.alignment_flags))
      throw Error('Wrong item identity, hash, or metadata.');
    if((r.whole && !packet.whole_choices.includes(r.whole)) || (r.tone && !packet.tone_choices.includes(r.tone)))
      throw Error('Invalid decision.');
    if(!r.heard || ['context','whole','tone'].some(v=>typeof r.heard[v]!=='boolean'))throw Error('Invalid heard flags.');
    if(r.reviewer!==data.reviewer || typeof r.notes!=='string' || !Number.isFinite(Date.parse(r.reviewed_at)))
      throw Error('Invalid reviewer, notes, or timestamp.');
    if(complete && !r.whole)throw Error(`Missing whole-target decision: ${r.item_id}`);
    if(complete && !r.tone)throw Error(`Missing tone-bearing decision: ${r.item_id}`);
    if(complete && (r.whole!=='PASS' || r.tone!=='PASS') && !r.notes.trim())throw Error(`Add boundary/ownership notes: ${r.item_id}`);
  }
}
function restore(data) {
  valid(data,false);reviewer.value=data.reviewer;
  for(const s of sections) {
    const r=data.reviews.find(r=>r.item_id===s.dataset.id);
    s.querySelector('[data-decision=whole]').value=r.whole;s.querySelector('[data-decision=tone]').value=r.tone;
    s.querySelector('textarea').value=r.notes;s.querySelector('[data-heard]').checked=r.heard_all;
    heard.set(r.item_id,new Set(['context','whole','tone'].filter(v=>r.heard[v])));
    const content={whole:r.whole,tone:r.tone,notes:r.notes,heard:r.heard,heard_all:r.heard_all,reviewer:r.reviewer};
    revisions.set(r.item_id,{fingerprint:JSON.stringify(content),reviewed_at:r.reviewed_at});
  }
  progress();
}
function progress() {
  const done=reviewer.value.trim()?sections.filter(s=>{
    const whole=s.querySelector('[data-decision=whole]').value;
    const tone=s.querySelector('[data-decision=tone]').value;
    return whole && tone && ((whole==='PASS' && tone==='PASS') || s.querySelector('textarea').value.trim());
  }).length:0;
  document.querySelector('#progress').textContent=`${done} / ${sections.length} items reviewed`;
}
function save(){try{localStorage.setItem(storageKey,JSON.stringify(collect()));}catch{}progress();}
document.addEventListener('change',save);document.addEventListener('input',save);
function download(complete) {
  try {
    const data=collect();valid(data,complete);save();
    const url=URL.createObjectURL(new Blob([JSON.stringify(data,null,2)+'\n'],{type:'application/json'}));
    const a=document.createElement('a');a.href=url;
    a.download=complete?packet.export_filename:'benma-learner-alignment-draft.json';a.click();
    setTimeout(()=>URL.revokeObjectURL(url),1000);
    status.textContent=complete?'QA exported. No benchmark release has been created.':'Draft saved.';
  }catch(e){status.textContent=e.message;}
}
document.querySelector('#export').onclick=()=>download(true);
document.querySelector('#draft').onclick=()=>download(false);
document.querySelector('#import').onchange=async e=>{try{restore(JSON.parse(await e.target.files[0].text()));save();status.textContent='Review imported.';}catch(err){status.textContent=err.message;}};
try {const saved=localStorage.getItem(storageKey);if(saved)restore(JSON.parse(saved));}catch{}
progress();
