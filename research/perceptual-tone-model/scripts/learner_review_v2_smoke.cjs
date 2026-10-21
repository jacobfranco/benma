/* Browser engineering checks only. Synthetic answers never become human QA. */
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const assert = require('node:assert/strict');
const {spawn} = require('node:child_process');
const {pathToFileURL} = require('node:url');
const packageDir = path.resolve(__dirname, '..');
const root = path.join(packageDir, 'data/generated/learner-transfer-v1-20261019/review-with-optional-telemetry');
const profile = fs.mkdtempSync(path.join(os.tmpdir(), 'learner-browser-test-'));
const browser = spawn('/usr/bin/chromium', [
  '--headless', '--no-sandbox', '--disable-gpu', '--disable-background-networking',
  '--disable-extensions', '--no-first-run', '--no-default-browser-check',
  '--autoplay-policy=no-user-gesture-required', '--remote-debugging-port=0',
  `--user-data-dir=${profile}`, pathToFileURL(path.join(root, 'qa/index.html')).href,
], {stdio: ['ignore', 'ignore', 'pipe']});
let errors = ''; browser.stderr.on('data', data => { errors += data; });
const pause = ms => new Promise(resolve => setTimeout(resolve, ms));
let socket;
(async () => {
  let port;
  for (let i=0; i<100; i++) {
    try { port = fs.readFileSync(path.join(profile, 'DevToolsActivePort'), 'utf8').split('\n')[0]; break; } catch {}
    if (browser.exitCode !== null) throw new Error(errors);
    await pause(100);
  }
  if (!port) throw new Error(`Browser did not start: ${errors}`);
  const pages = await (await fetch(`http://127.0.0.1:${port}/json/list`)).json();
  socket = new WebSocket(pages.find(p => p.type === 'page').webSocketDebuggerUrl);
  await new Promise((resolve, reject) => {socket.onopen=resolve; socket.onerror=reject;});
  let sequence=0; const pending=new Map();
  socket.onmessage = event => {const data=JSON.parse(event.data); if (pending.has(data.id)) {
    const {resolve,reject}=pending.get(data.id); pending.delete(data.id);
    data.error ? reject(new Error(JSON.stringify(data.error))) : resolve(data.result);
  }};
  const command = (method,params={}) => new Promise((resolve,reject) => {
    const id=++sequence; pending.set(id,{resolve,reject}); socket.send(JSON.stringify({id,method,params}));
  });
  const evaluate = async expression => {
    const result = await command('Runtime.evaluate',{expression,awaitPromise:true,returnByValue:true});
    if (result.exceptionDetails) throw new Error(JSON.stringify(result.exceptionDetails));
    return result.result.value;
  };
  await command('Runtime.enable');
  for(let i=0;i<50;i++) {if(await evaluate('document.readyState === "complete"'))break;await pause(100);}


  const count=await evaluate('packet.items.length');assert.equal(count,123);
  const media=await evaluate(`Promise.all([...document.querySelectorAll('audio')].map(a=>new Promise((resolve,reject)=>{
    a.onloadedmetadata=()=>resolve(a.duration);a.onerror=()=>reject(Error(a.src));a.load();
  })))`);assert.equal(media.length,369);assert.ok(media.every(d=>d>0));
  assert.equal(await evaluate('document.body.innerText.includes("experimental_final_under_60ms")'),false);
  assert.equal(await evaluate('document.querySelectorAll(".identity").length'),123);
  await evaluate(`window.playCard=[...document.querySelectorAll('section')].find(s=>s.querySelector('audio[data-view=whole]').duration>.3);playCard.querySelector('[data-play=context]').click()`);await pause(60);
  assert.equal(await evaluate('playCard.querySelector("audio[data-view=context]").paused'),false);
  await evaluate('playCard.querySelector("[data-play=whole]").click()');await pause(40);
  assert.equal(await evaluate('playCard.querySelector("audio[data-view=context]").paused'),true);
  assert.equal(await evaluate('playCard.querySelector("audio[data-view=whole]").paused'),false);
  await evaluate(`document.querySelectorAll('audio').forEach(a=>a.pause());window.testExports=[];window.testDownloads=[];
    URL.createObjectURL=blob=>{testExports.push(blob);return 'blob:synthetic'};
    HTMLAnchorElement.prototype.click=function(){testDownloads.push(this.download)};
    document.querySelector('#export').click()`);assert.equal(await evaluate('testExports.length'),0);
  await evaluate(`reviewer.value='SYNTHETIC BROWSER TEST';document.querySelector('#export').click()`);
  assert.match(await evaluate('status.textContent'),/Missing whole-target decision: Q001/);
  await evaluate(`sections[0].querySelector('[data-decision=whole]').value='PASS';document.querySelector('#export').click()`);
  assert.match(await evaluate('status.textContent'),/Missing tone-bearing decision: Q001/);
  await evaluate(`for(const s of sections){for(const x of s.querySelectorAll('select'))x.value='PASS';s.querySelector('[data-heard]').checked=false;heard.set(s.dataset.id,new Set());}document.querySelector('#export').click()`);
  assert.equal(await evaluate('testExports.length'),1);
  const first=await evaluate('testExports[0].text()');const data=JSON.parse(first);
  assert.equal(data.reviews.length,123);assert.ok(data.reviews.every(r=>r.unit_id&&r.source_id&&r.item_sha256&&r.reviewed_at&&!r.heard_all&&Object.values(r.heard).every(v=>v===false)));
  assert.equal(await evaluate('document.querySelector("#progress").textContent'),'123 / 123 items reviewed');
  assert.equal(data.reviews.filter(r=>r.alignment_flags.length).length,37);
  assert.equal(await evaluate('testDownloads[0]'),'benma-learner-alignment-qa.json');
  await evaluate('document.querySelector("#export").click()');assert.equal(await evaluate('testExports[1].text()'),first,'repeated export must be byte-identical');
  await evaluate(`document.querySelector('select').value='WRONG UNIT';document.querySelector('#export').click()`);assert.equal(await evaluate('testExports.length'),2);
  await evaluate(`document.querySelector('textarea').value='Synthetic boundary note';document.querySelector('#export').click()`);assert.equal(await evaluate('testExports.length'),3);
  await evaluate(`(async()=>{const d=JSON.parse(await testExports[2].text());d.reviews[0].item_sha256='wrong';
    const dt=new DataTransfer();dt.items.add(new File([JSON.stringify(d)],'synthetic.json',{type:'application/json'}));
    const input=document.querySelector('#import');input.files=dt.files;input.dispatchEvent(new Event('change'));})()`);await pause(60);
  assert.match(await evaluate('status.textContent'),/Wrong item/);
  await evaluate(`(async()=>{const d=await testExports[2].text();const dt=new DataTransfer();dt.items.add(new File([d],'synthetic.json',{type:'application/json'}));
    const input=document.querySelector('#import');input.files=dt.files;input.dispatchEvent(new Event('change'));})()`);await pause(60);
  assert.equal(await evaluate('status.textContent'),'Review imported.');
  await evaluate('document.querySelector("#export").click()');assert.equal(await evaluate('testExports[3].text()'),await evaluate('testExports[2].text()'),'import/export must preserve timestamps');
  for(const width of [390,1280]){await command('Emulation.setDeviceMetricsOverride',{width,height:900,deviceScaleFactor:1,mobile:false});assert.ok(await evaluate('document.documentElement.scrollWidth<=innerWidth'));}
  await evaluate('localStorage.clear();location.reload()');await pause(200);
  assert.equal(await evaluate('[...document.querySelectorAll("select")].filter(s=>s.value).length'),0);
  const screen=await command('Page.captureScreenshot',{format:'png'});fs.writeFileSync(path.join(root,'qa/browser-preview.png'),Buffer.from(screen.data,'base64'));
  console.log(JSON.stringify({qa_items:123,audio_files_loaded:369,exclusive_playback:true,alignment_flags_not_displayed:true,
    take_identity_visible:true,playback_telemetry_optional:true,exact_missing_field_errors:true,issue_notes_required:true,all_item_hashes_exported:true,
    flags_preserved_in_export:37,repeat_export_byte_identical:true,import_export_byte_identical:true,
    corrupted_item_hash_rejected:true,viewport_widths:[390,1280],synthetic_answers_written:false}));
})().catch(e=>{console.error(e);process.exitCode=1;}).finally(()=>{socket?.close();browser.kill();});
