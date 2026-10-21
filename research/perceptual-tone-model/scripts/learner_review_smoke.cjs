/* Browser engineering checks only. Synthetic answers never become human QA. */
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const assert = require('node:assert/strict');
const {spawn} = require('node:child_process');
const {pathToFileURL} = require('node:url');
const packageDir = path.resolve(__dirname, '..');
const root = path.join(packageDir, 'data/generated/learner-alignment-v1');
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

  const count = await evaluate('JSON.parse(document.querySelector("#packet").textContent).items.length');
  assert.equal(count,123);
  assert.equal(await evaluate('document.querySelectorAll("section[data-id]").length'), count);
  const media = await evaluate(`Promise.all([...document.querySelectorAll('audio')].map(audio=>new Promise((resolve,reject)=>{
    audio.onloadedmetadata=()=>resolve(audio.duration); audio.onerror=()=>reject(Error(audio.src)); audio.load();
  })))`);
  assert.equal(media.length, count*3);assert.ok(media.every(d=>d>0));
  await evaluate(`document.querySelector('[data-play=context]').click()`);await pause(80);
  assert.equal(await evaluate('document.querySelector("audio[data-view=context]").paused'),false);
  await evaluate(`document.querySelector('[data-play=whole]').click()`);await pause(50);
  assert.equal(await evaluate('document.querySelector("audio[data-view=context]").paused'),true);
  assert.equal(await evaluate('document.querySelector("audio[data-view=whole]").paused'),false);
  await evaluate(`document.querySelectorAll('audio').forEach(a=>a.pause()); window.testExports=[];
    URL.createObjectURL=blob=>{window.testExports.push(blob);return 'blob:synthetic-test'};
    HTMLAnchorElement.prototype.click=function(){};document.querySelector('#export').click()`);
  assert.equal(await evaluate('window.testExports.length'),0);
  await evaluate(`document.querySelector('#reviewer').value='SYNTHETIC BROWSER TEST — NOT HUMAN QA';
    for(const s of document.querySelectorAll('section[data-id]')) {
      for(const select of s.querySelectorAll('select')) select.value='PASS';
      s.querySelector('[data-heard]').checked=true;
    }
    document.querySelector('#export').click()`);
  assert.equal(await evaluate('window.testExports.length'),0,'checking heard without playback must fail');
  // Synthetic events exercise UI only inside a disposable profile; no answers reach disk.
  await evaluate(`for(const a of document.querySelectorAll('audio')) a.dispatchEvent(new Event('ended'));
    document.querySelector('#export').click()`);
  assert.equal(await evaluate('window.testExports.length'),1);
  let result=JSON.parse(await evaluate('window.testExports[0].text()'));
  assert.equal(result.reviews.length,count);assert.ok(result.reviews.every(r=>r.whole==='PASS'&&r.tone==='PASS'&&r.heard_all));
  await evaluate(`document.querySelector('select').value='WRONG UNIT';document.querySelector('#export').click()`);
  assert.equal(await evaluate('window.testExports.length'),1,'issue without notes blocked');
  await evaluate(`document.querySelector('textarea').value='Synthetic boundary note';document.querySelector('#export').click()`);
  assert.equal(await evaluate('window.testExports.length'),2);
  await evaluate(`(async()=>{ const d=JSON.parse(await window.testExports[1].text());d.packet_sha256='wrong';
    const dt=new DataTransfer();dt.items.add(new File([JSON.stringify(d)],'synthetic.json',{type:'application/json'}));
    const input=document.querySelector('#import');input.files=dt.files;input.dispatchEvent(new Event('change'));})()`);
  await pause(80);
  assert.match(await evaluate('document.querySelector("#status").textContent'),/Wrong packet/);
  for(const width of [390,1280]) {
    await command('Emulation.setDeviceMetricsOverride',{width,height:900,deviceScaleFactor:1,mobile:false});
    assert.ok(await evaluate('document.documentElement.scrollWidth<=innerWidth'), `overflow at ${width}`);
  }
  await evaluate('localStorage.clear(); location.reload()');await pause(200);
  assert.equal(await evaluate('[...document.querySelectorAll("select")].filter(s=>s.value).length'),0);
  const screen=await command('Page.captureScreenshot',{format:'png'});
  fs.writeFileSync(path.join(root,'qa/browser-preview.png'),Buffer.from(screen.data,'base64'));
  console.log(JSON.stringify({qa_items:count,audio_files_loaded:media.length,playback:true,exclusive_playback:true,
    incomplete_review_blocked:true,playback_acknowledgments_required:true,issue_notes_required:true,
    wrong_packet_blocked:true,viewport_widths:[390,1280],synthetic_answers_written:false}));
})().catch(e=>{console.error(e);process.exitCode=1;}).finally(()=>{socket?.close();browser.kill();});
