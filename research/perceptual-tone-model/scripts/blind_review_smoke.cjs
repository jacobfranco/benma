/* Disposable browser + synthetic answers only. Never writes a human review. */
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const assert = require('node:assert/strict');
const {spawn, spawnSync} = require('node:child_process');
const {pathToFileURL} = require('node:url');
const packageDir = path.resolve(__dirname, '..');
const root = path.join(packageDir, 'data/generated/realized-tone-blind-v1-20261019');
const temporary = fs.mkdtempSync(path.join(os.tmpdir(), 'blind-review-test-'));
const profile = path.join(temporary, 'profile'); fs.mkdirSync(profile);
const browser = spawn('/usr/bin/chromium', [
  '--headless', '--no-sandbox', '--disable-gpu', '--disable-background-networking',
  '--disable-extensions', '--no-first-run', '--no-default-browser-check',
  '--autoplay-policy=no-user-gesture-required', '--remote-debugging-port=0',
  `--user-data-dir=${profile}`, pathToFileURL(path.join(root, 'qa/index.html')).href,
], {stdio:['ignore','ignore','pipe']});
let errors = ''; browser.stderr.on('data', data => {errors += data;});
const pause = ms => new Promise(resolve => setTimeout(resolve, ms));
let socket;
const timeout = setTimeout(() => {console.error('Browser test timeout'); browser.kill(); process.exit(1);}, 90000);
(async () => {
  let port;
  for (let i=0;i<100;i++) {
    try {port = fs.readFileSync(path.join(profile,'DevToolsActivePort'),'utf8').split('\n')[0];break;} catch {}
    if (browser.exitCode !== null) throw Error(errors);
    await pause(100);
  }
  if (!port) throw Error(errors || 'Browser failed to start');
  const pages = await (await fetch(`http://127.0.0.1:${port}/json/list`)).json();
  socket = new WebSocket(pages.find(p => p.type === 'page').webSocketDebuggerUrl);
  await new Promise((resolve,reject) => {socket.onopen=resolve;socket.onerror=reject;});
  let sequence=0; const pending=new Map();
  socket.onmessage = event => {const data=JSON.parse(event.data);if(pending.has(data.id)) {
    const {resolve,reject}=pending.get(data.id);pending.delete(data.id);
    data.error ? reject(Error(JSON.stringify(data.error))) : resolve(data.result);
  }};
  const command = (method,params={}) => new Promise((resolve,reject) => {
    const id=++sequence;pending.set(id,{resolve,reject});socket.send(JSON.stringify({id,method,params}));
  });
  const evaluate = async expression => {
    const result = await command('Runtime.evaluate',{expression,awaitPromise:true,returnByValue:true});
    if(result.exceptionDetails)throw Error(JSON.stringify(result.exceptionDetails));
    return result.result.value;
  };
  await command('Runtime.enable');
  for(let i=0;i<50;i++){if(await evaluate('document.readyState === "complete"'))break;await pause(100);}
  assert.equal(await evaluate('packet.items.length'),52);
  const durations = await evaluate(`Promise.all(packet.items.flatMap(item=>Object.values(item.audio)).map(src=>
    new Promise((resolve,reject)=>{const a=new Audio();a.onloadedmetadata=()=>resolve(a.duration);
      a.onerror=()=>reject(Error('Cannot decode audio'));a.src=src;a.load();})))`);
  assert.equal(durations.length,104);assert.ok(durations.every(n=>n>0));
  assert.equal(await evaluate('document.querySelector("[data-play=whole]").disabled'),true);
  await evaluate('document.querySelector("[data-play=tone]").click()');
  for(let i=0;i<30;i++){if(await evaluate('rows[0].tone_bearing_heard'))break;await pause(50);}
  assert.equal(await evaluate('rows[0].tone_bearing_heard'),true);
  assert.equal(await evaluate('document.querySelector("[data-play=whole]").disabled'),false);
  await evaluate('document.querySelector("[data-play=whole]").click()');
  for(let i=0;i<30;i++){if(await evaluate('rows[0].whole_target_heard'))break;await pause(50);}
  assert.equal(await evaluate('rows[0].whole_target_heard'),true);
  await evaluate('document.querySelector("[data-play=tone]").click();document.querySelector("[data-play=whole]").click()');
  assert.equal(await evaluate('document.querySelector("audio[data-view=tone]").paused'),true);
  await evaluate('document.querySelectorAll("audio").forEach(a=>a.pause())');
  assert.match(await evaluate(`try{exportText(true);'unexpected'}catch(e){e.message}`),/reviewer name/);
  await evaluate(`reviewer.value='SYNTHETIC BROWSER TEST';reviewer.dispatchEvent(new Event('input'))`);
  assert.match(await evaluate(`try{exportText(true);'unexpected'}catch(e){e.message}`),/tone family at item 1/);
  await evaluate(`document.querySelector('input[value=NEUTRAL]').click()`);
  assert.match(await evaluate(`try{exportText(true);'unexpected'}catch(e){e.message}`),/confidence at item 1/);
  await evaluate(`const select=document.querySelector('[data-field=confidence]');select.value='4';select.dispatchEvent(new Event('change'))`);
  assert.equal(await evaluate('rows[0].perceived_tone'),'NEUTRAL');
  assert.equal(await evaluate('rows[0].confidence'),4);
  assert.match(await evaluate('document.querySelector("#progress").textContent'),/^1 \/ 52/);
  // A completed export also requires tone-bearing playback on every item.
  await evaluate(`window.draftBytes=exportText(false);rows.forEach((r,i)=>{r.perceived_tone=choices[i%6][0];r.confidence=3;r.timestamp='2026-10-19T20:00:00.000Z';})`);
  assert.match(await evaluate(`try{exportText(true);'unexpected'}catch(e){e.message}`),/Finish tone-bearing playback/);
  await evaluate(`rows.forEach(r=>{r.tone_bearing_heard=true;r.whole_target_heard=false;r.usability=null;});persist();render();window.completeBytes=exportText(true)`);
  assert.equal(await evaluate('exportText(true) === completeBytes'),true);
  await evaluate('importText(completeBytes)');
  assert.equal(await evaluate('exportText(true) === completeBytes'),true);
  for(const field of ['packet_sha256','annotation_id','perceived_tone','confidence','timestamp','source_id']) {
    const rejected = await evaluate(`(()=>{const bad=JSON.parse(completeBytes);
      ${field === 'packet_sha256' ? "bad.packet_sha256='wrong';" :
        `bad.reviews[0][${JSON.stringify(field)}]=${field === 'confidence' ? '6' : "'invalid'"};`}
      try{importText(JSON.stringify(bad));return false;}catch{return true;}})()`);
    assert.equal(rejected,true,field);
    assert.equal(await evaluate('exportText(true) === completeBytes'),true,'rejected import must not modify answers');
  }
  const exported = await evaluate('completeBytes');
  const value = JSON.parse(exported);
  assert.ok(value.reviews.some(r=>r.perceived_tone==='NEUTRAL'));
  assert.ok(value.reviews.some(r=>r.perceived_tone==='UNCLEAR'));
  assert.ok(value.reviews.every(r=>r.usability===null&&!r.whole_target_heard));
  const syntheticFile=path.join(temporary,'synthetic-only.json');fs.writeFileSync(syntheticFile,exported);
  const python=path.resolve(packageDir,'../../benchmark/pronunciation_v2/.venv/bin/python');
  const roundTrip=spawnSync(python,['-c',
    'import sys;from perceptual_tone.blind_packet import validate_review;from perceptual_tone.common import read_json,digest;p=read_json(sys.argv[1]);p["packet_sha256"]=digest(p);print(validate_review(p,read_json(sys.argv[2])))',
    path.join(root,'private/packet-manifest.json'),syntheticFile],
    {encoding:'utf8',env:{...process.env,PYTHONPATH:packageDir}});
  assert.equal(roundTrip.status,0,roundTrip.stderr);
  // Exercise actual export button without creating a developer answer file.
  await evaluate(`window.testDownloads=[];window.testBlobs=[];
    URL.createObjectURL=blob=>{testBlobs.push(blob);return 'blob:synthetic'};
    HTMLAnchorElement.prototype.click=function(){testDownloads.push(this.download)};
    document.querySelector('#export').click()`);
  assert.equal(await evaluate('testDownloads[0]'),'benma-realized-tone-blind-review.json');
  assert.equal(await evaluate('testBlobs[0].text()'),exported);
  await evaluate('document.querySelector("#export").click()');
  assert.equal(await evaluate('testBlobs[1].text()'),exported);
  const draft = await evaluate('draftBytes');
  await command('Page.reload');
  await pause(350);
  assert.equal(await evaluate('exportText(true)'),exported,'browser resume is lossless');
  const visible = await evaluate('document.body.innerText');
  for(const word of ['learner','native','pilot','expanded','source_id','SSB','answer-key','pinyin','hanzi','duplicate'])
    assert.ok(!visible.toLowerCase().includes(word.toLowerCase()),word);
  assert.equal(await evaluate('document.querySelectorAll("a[href],script[src],link[href],iframe,form").length'),0);
  assert.equal(await evaluate('performance.getEntriesByType("resource").filter(r=>/^https?:/.test(r.name)).length'),0);
  // Return to an empty synthetic draft for a representative screenshot.
  await evaluate('importText(' + JSON.stringify(draft) + ')');
  for(const width of [390,1280]) {
    await command('Emulation.setDeviceMetricsOverride',{width,height:1000,deviceScaleFactor:1,mobile:width===390});
    assert.equal(await evaluate('document.documentElement.scrollWidth<=window.innerWidth'),true);
  }
  const shot=await command('Page.captureScreenshot',{format:'png',captureBeyondViewport:true});
  fs.writeFileSync(path.join(root,'private/browser-preview.png'),Buffer.from(shot.data,'base64'));
  console.log(JSON.stringify({status:'PASS',presentations:52,audio_decodes:104,
    tone_first_gate:true,real_playback_heard_flags:true,exclusive_playback:true,
    complete_export_gates:true,optional_whole_and_usability:true,neutral_and_unclear_preserved:true,
    deterministic_export:true,import_export_round_trip:true,python_export_validation:true,
    invalid_imports_rejected:6,browser_resume:true,visible_leakage_audit:true,external_requests:0,
    responsive_widths:[390,1280],synthetic_profile_only:true,human_review_files_created:0},null,2));
})().catch(error=>{console.error(error.stack||error);process.exitCode=1;}).finally(async()=>{
  clearTimeout(timeout);if(socket)socket.close();browser.kill();await pause(300);
  fs.rmSync(temporary,{recursive:true,force:true});
});
