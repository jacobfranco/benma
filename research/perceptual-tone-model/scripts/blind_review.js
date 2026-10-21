'use strict';
const packet = JSON.parse(document.querySelector('#packet').textContent);
const choices = [
  ['T1', 'T1 — high / level'], ['T2', 'T2 — rising'],
  ['T3', 'T3 — low / dipping / low-rising'], ['T4', 'T4 — falling'],
  ['NEUTRAL', 'NEUTRAL / WEAK'], ['UNCLEAR', 'UNCLEAR / CANNOT TELL'],
];
const reviewer = document.querySelector('#reviewer');
const card = document.querySelector('#card');
const status = document.querySelector('#status');
const jump = document.querySelector('#jump');
const storageKey = 'listening-review:' + packet.packet_sha256;
let current = 0;
let rows = packet.items.map(item => ({
  annotation_id: item.annotation_id, perceived_tone: null, confidence: null, usability: null,
  tone_bearing_heard: false, whole_target_heard: false, timestamp: null,
}));
const completed = row => row.perceived_tone !== null && row.confidence !== null && row.tone_bearing_heard;
const exactKeys = (value, keys) => value && typeof value === 'object' && !Array.isArray(value) &&
  Object.keys(value).sort().join('|') === [...keys].sort().join('|');
function checkReview(value, complete) {
  if (!exactKeys(value, ['schema','packet_version','packet_sha256','reviewer','reviews']) ||
      value.schema !== 'benma-realized-tone-review-v1' || value.packet_version !== packet.packet_version ||
      value.packet_sha256 !== packet.packet_sha256) throw Error('This file does not match this review packet.');
  if (typeof value.reviewer !== 'string' || (complete && !value.reviewer.trim())) throw Error('Enter your reviewer name.');
  if (!Array.isArray(value.reviews) || value.reviews.length !== packet.items.length) throw Error('Wrong item count.');
  for (let i=0; i<value.reviews.length; i++) {
    const r = value.reviews[i];
    if (!exactKeys(r, ['annotation_id','perceived_tone','confidence','usability',
      'tone_bearing_heard','whole_target_heard','timestamp']) || r.annotation_id !== packet.items[i].annotation_id)
      throw Error('Invalid item identity or fields at item ' + (i+1));
    if (!(choices.some(([key]) => key === r.perceived_tone) || (!complete && r.perceived_tone === null)))
      throw Error('Choose a tone family at item ' + (i+1));
    if (!((Number.isInteger(r.confidence) && r.confidence >= 1 && r.confidence <= 5) || (!complete && r.confidence === null)))
      throw Error('Choose confidence at item ' + (i+1));
    if (![null,'CLEAR','BORDERLINE','UNUSABLE'].includes(r.usability)) throw Error('Invalid acoustic usability.');
    if (typeof r.tone_bearing_heard !== 'boolean' || typeof r.whole_target_heard !== 'boolean') throw Error('Invalid listening fields.');
    if (complete && !r.tone_bearing_heard) throw Error('Finish tone-bearing playback at item ' + (i+1));
    if (r.whole_target_heard && !r.tone_bearing_heard) throw Error('Listen to tone-bearing target first.');
    if (!(r.timestamp === null && !complete) && (typeof r.timestamp !== 'string' ||
      !/^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d\.\d{3}Z$/.test(r.timestamp) || !Number.isFinite(Date.parse(r.timestamp))))
      throw Error('Invalid timestamp at item ' + (i+1));
  }
  return value;
}
function reviewValue() {
  return {schema: 'benma-realized-tone-review-v1', packet_version: packet.packet_version,
    packet_sha256: packet.packet_sha256, reviewer: reviewer.value.trim(),
    reviews: rows.map(r => ({annotation_id:r.annotation_id, perceived_tone:r.perceived_tone,
      confidence:r.confidence, usability:r.usability, tone_bearing_heard:r.tone_bearing_heard,
      whole_target_heard:r.whole_target_heard, timestamp:r.timestamp}))};
}
function persist() {
  try { localStorage.setItem(storageKey, JSON.stringify(reviewValue())); }
  catch { status.textContent = 'Browser storage unavailable. Use Save draft to preserve your progress.'; }
  document.querySelector('#progress').textContent = rows.filter(completed).length + ' / ' + rows.length + ' items complete';
}
function change(field, value, index=current) {
  if (rows[index][field] !== value) {
    rows[index][field] = value;
    rows[index].timestamp = new Date().toISOString();
    persist();
  }
}
function render() {
  document.querySelectorAll('audio').forEach(a => a.pause());
  const row = rows[current], item = packet.items[current], index = current;
  card.replaceChildren();
  const id = document.createElement('p'); id.className = 'id'; id.textContent = item.annotation_id; card.append(id);
  const playback = document.createElement('div'); playback.className = 'row'; card.append(playback);
  const buttons = {};
  for (const [view,label,field] of [['tone','TONE-BEARING TARGET','tone_bearing_heard'],['whole','WHOLE TARGET','whole_target_heard']]) {
    const audio = document.createElement('audio'); audio.src = item.audio[view]; audio.preload = 'metadata'; audio.dataset.view = view;
    const button = document.createElement('button'); button.type = 'button'; button.dataset.play = view;
    button.textContent = 'Play ' + label; button.className = view === 'tone' ? 'primary' : '';
    button.disabled = view === 'whole' && !row.tone_bearing_heard;
    buttons[view] = button;
    button.onclick = async () => {
      document.querySelectorAll('audio').forEach(a => {if (a !== audio) a.pause();});
      audio.currentTime = 0;
      try { await audio.play(); } catch { status.textContent = 'Playback failed. Please reopen this page in a browser with audio playback enabled.'; }
    };
    audio.onended = () => {
      change(field, true, index);
      if (index === current) { buttons.whole.disabled = false; updateHeard(); }
    };
    audio.onerror = () => { status.textContent = 'Audio could not be loaded for this item.'; };
    playback.append(button, audio);
  }
  const heard = document.createElement('p'); heard.className = 'heard'; heard.id = 'heard'; card.append(heard);
  function updateHeard() { heard.textContent = 'Tone-bearing heard: ' + (row.tone_bearing_heard ? 'yes' : 'no') +
    ' · Whole target heard: ' + (row.whole_target_heard ? 'yes' : 'no'); }
  updateHeard();
  const fieldset = document.createElement('fieldset');
  const legend = document.createElement('legend'); legend.textContent = 'WHAT TONE FAMILY DOES THIS AUDIO MOST SOUND LIKE?'; fieldset.append(legend);
  const options = document.createElement('div'); options.className = 'choices'; fieldset.append(options);
  for (const [value,label] of choices) {
    const wrapper = document.createElement('label'), input = document.createElement('input');
    input.type = 'radio'; input.name = 'perceived-tone'; input.value = value; input.checked = row.perceived_tone === value;
    input.onchange = () => change('perceived_tone', value); wrapper.append(input, document.createTextNode(label)); options.append(wrapper);
  }
  card.append(fieldset);
  for (const [field,label,values] of [
    ['confidence','Confidence (1 = very unsure; 5 = very sure)',[['','Choose confidence'],...[1,2,3,4,5].map(n => [String(n),String(n)])]],
    ['usability','Acoustic usability (optional)',[['','Not specified'],['CLEAR','CLEAR'],['BORDERLINE','BORDERLINE'],['UNUSABLE','UNUSABLE']]],
  ]) {
    const wrapper = document.createElement('label'); wrapper.textContent = label;
    const select = document.createElement('select'); select.dataset.field = field;
    for (const [value,text] of values) { const option = document.createElement('option'); option.value = value; option.textContent = text; select.append(option); }
    select.value = row[field] === null ? '' : String(row[field]);
    select.onchange = () => change(field, select.value === '' ? null : field === 'confidence' ? Number(select.value) : select.value);
    wrapper.append(select); card.append(wrapper);
  }
  jump.value = String(current);
  document.querySelector('#position').textContent = 'Item ' + (current+1) + ' of ' + rows.length;
  document.querySelector('#previous').disabled = current === 0;
  document.querySelector('#next').disabled = current === rows.length-1;
  persist();
}
function importText(text) {
  const value = checkReview(JSON.parse(text), false);
  reviewer.value = value.reviewer;
  rows = value.reviews.map(r => ({...r}));
  current = Math.max(0, rows.findIndex(r => !completed(r)));
  render(); status.textContent = 'Saved review resumed.';
}
function exportText(complete) {
  const value = reviewValue(); checkReview(value, complete);
  return JSON.stringify(value, null, 2) + '\n';
}
function download(complete) {
  try {
    const text = exportText(complete);
    const url = URL.createObjectURL(new Blob([text], {type:'application/json'}));
    const link = document.createElement('a'); link.href = url;
    link.download = complete ? 'benma-realized-tone-blind-review.json' : 'benma-realized-tone-blind-draft.json';
    link.click(); setTimeout(() => URL.revokeObjectURL(url), 1000);
    status.textContent = complete ? 'Completed review exported. Save it in Downloads.' : 'Draft exported.';
  } catch (error) { status.textContent = error.message; }
}
for (let i=0; i<rows.length; i++) { const option = document.createElement('option'); option.value = String(i); option.textContent = String(i+1); jump.append(option); }
jump.onchange = () => {current = Number(jump.value); render();};
document.querySelector('#previous').onclick = () => {current--; render();};
document.querySelector('#next').onclick = () => {current++; render();};
document.querySelector('#export').onclick = () => download(true);
document.querySelector('#draft').onclick = () => download(false);
document.querySelector('#resume').onclick = () => document.querySelector('#import').click();
document.querySelector('#import').onchange = async event => {
  const file = event.target.files[0]; if (!file) return;
  try {importText(await file.text());} catch (error) {status.textContent = error.message;}
  event.target.value = '';
};
reviewer.oninput = persist;
try { const saved = localStorage.getItem(storageKey); if (saved) importText(saved); else render(); }
catch { render(); status.textContent = 'No usable browser draft loaded. Resume a saved JSON file if needed.'; }
