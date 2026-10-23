'use strict';
const $ = id => document.getElementById(id);
const storageKey = 'listening-' + PACKET.listener_id + '-' + PACKET.packet_sha256;
let result = null, index = 0, plays = 0, heard = false, busy = false;
let player = new Audio();
$('identity').textContent = 'Participant ' + PACKET.listener_id;
function persist() {
  try { localStorage.setItem(storageKey, JSON.stringify(result)); }
  catch { $('status').textContent = 'Browser saving unavailable. Download a JSON backup before closing.'; }
}
function validSaved(value) {
  return value && value.version === PACKET.version && value.listener_id === PACKET.listener_id &&
    value.packet_sha256 === PACKET.packet_sha256 && Array.isArray(value.responses) &&
    value.responses.length <= PACKET.trials.length && value.responses.every((r,i) =>
      r.trial_id === PACKET.trials[i].trial_id && r.position === i+1 &&
      ['T1','T2','T3','T4','NEUTRAL','UNCLEAR'].includes(r.answer) && r.play_count >= 1);
}
function refresh() {
  $('welcome').hidden = true; $('export').hidden = false; $('csv').hidden = false;
  index = result.responses.length;
  $('study').hidden = index === PACKET.trials.length;
  $('done').hidden = index !== PACKET.trials.length;
  if (index === PACKET.trials.length) return;
  const t = PACKET.trials[index];
  plays = 0; heard = false; busy = false;
  document.querySelectorAll('[name=answer]').forEach(r => {r.checked = false;});
  $('next').disabled = true; $('play').disabled = false;
  $('progress').textContent = `Trial ${index+1} of ${PACKET.trials.length}`;
  $('instruction').textContent = t.view === 'crop' ? 'Listen to the target syllable.' :
    'Listen to the passage, then the target syllable. Give one judgment for that target.';
  $('timing').hidden = t.view === 'crop'; $('cursor').style.left = '0%';
  $('playing').textContent = '';
}
$('start').onclick = () => {
  const eligibility = Object.fromEntries(['adult','native','primary_childhood','independent'].map(k => [k,$(k).checked]));
  if (!Object.values(eligibility).every(Boolean)) {
    $('status').textContent = 'Please confirm all four participation statements to begin.'; return;
  }
  result = {version:PACKET.version, listener_id:PACKET.listener_id, packet_sha256:PACKET.packet_sha256,
    eligibility, background:Object.fromEntries(['region','other_variety','current_language'].map(k => [k,$(k).value.trim()])),
    started_at:new Date().toISOString(), completed_at:null, responses:[]};
  $('status').textContent = ''; persist(); refresh();
};
function playAudio(src, passage, t) {
  return new Promise((resolve,reject) => {
    player = new Audio(src);
    player.onloadedmetadata = () => {
      if (passage) {
        $('zone').style.left = (100*t.target_start/player.duration)+'%';
        $('zone').style.width = (100*(t.target_end-t.target_start)/player.duration)+'%';
      }
    };
    player.ontimeupdate = () => { if(passage) $('cursor').style.left = (100*player.currentTime/player.duration)+'%'; };
    player.onended = resolve;
    player.onerror = () => reject(new Error('Audio could not be played.'));
    player.play().catch(reject);
  });
}
$('play').onclick = async () => {
  if (busy || !result || index >= PACKET.trials.length) return;
  busy = true; $('play').disabled = true; $('next').disabled = true;
  const t = PACKET.trials[index];
  try {
    if (t.view === 'context') {
      $('playing').textContent = ' Passage'; await playAudio(t.context, true, t);
      await new Promise(resolve => setTimeout(resolve, 350));
    }
    $('playing').textContent = ' Target syllable'; await playAudio(t.target, false, t);
    plays++; heard = true; $('playing').textContent = ' Playback complete'; $('status').textContent = '';
  } catch (error) { $('status').textContent = 'Playback failed. Try again before answering. ' + error.message; }
  finally {busy = false; $('play').disabled = false; enableNext();}
};
function enableNext() {
  $('next').disabled = busy || !heard || !document.querySelector('[name=answer]:checked');
}
document.querySelectorAll('[name=answer]').forEach(r => r.onchange = enableNext);
$('next').onclick = () => {
  const answer = document.querySelector('[name=answer]:checked');
  if (!result || busy || !heard || !answer || index >= PACKET.trials.length) return;
  const t = PACKET.trials[index];
  result.responses.push({trial_id:t.trial_id, position:t.position, answer:answer.value,
    answered_at:new Date().toISOString(), play_count:plays});
  if (result.responses.length === PACKET.trials.length) result.completed_at = new Date().toISOString();
  persist(); refresh();
};
function download(content, ext, mime) {
  const url = URL.createObjectURL(new Blob([content], {type:mime}));
  const a = document.createElement('a'); a.href = url;
  a.download = PACKET.listener_id + '-responses.' + ext; a.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
$('export').onclick = () => {if(result) download(JSON.stringify(result,null,2), 'json', 'application/json');};
$('csv').onclick = () => {
  if (!result) return;
  const fields = ['listener_id','packet_sha256','trial_id','position','answer','answered_at','play_count'];
  const rows = result.responses.map(r => fields.map(k => JSON.stringify(String(r[k] ?? result[k]))).join(','));
  download(fields.join(',')+'\n'+rows.join('\n')+'\n','csv','text/csv');
};
try {
  const saved = JSON.parse(localStorage.getItem(storageKey));
  if (validSaved(saved)) {result = saved; refresh();}
  else if(saved) $('status').textContent = 'Saved data could not be restored. Contact the coordinator.';
} catch { $('status').textContent = 'Browser saving unavailable. Download a backup before closing.'; }
