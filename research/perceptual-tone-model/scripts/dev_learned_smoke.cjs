/* Disposable Chromium microphone replay, explicitly marked automated_browser_replay. */
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const assert = require('node:assert/strict');
const {spawn} = require('node:child_process');
const root = path.resolve(__dirname, '..');
const base = process.argv[2] || 'http://127.0.0.1:8767';
const output = path.join(root, 'data/generated/dev-learned-integration-v1');
const temporary = fs.mkdtempSync(path.join(os.tmpdir(), 'benma-dev-browser-'));
const profile = path.join(temporary, 'profile'); fs.mkdirSync(profile);
const source = path.join(root, 'data/generated/learner-alignment-v1/corpus/jacob/4966e43af7d8a3fb1e682966.wav');
const browser = spawn('/usr/bin/chromium', [
  '--headless', '--no-sandbox', '--disable-gpu', '--disable-background-networking',
  '--disable-extensions', '--no-first-run', '--no-default-browser-check',
  '--autoplay-policy=no-user-gesture-required', '--remote-debugging-port=0',
  '--use-fake-ui-for-media-stream', '--use-fake-device-for-media-stream',
  `--use-file-for-fake-audio-capture=${source}`, `--user-data-dir=${profile}`, base,
], {stdio:['ignore','ignore','pipe']});
let errors = ''; browser.stderr.on('data', data => {errors += data;});
const pause = ms => new Promise(resolve => setTimeout(resolve, ms));
let socket;
const timeout = setTimeout(() => {browser.kill(); console.error('Browser test timeout'); process.exit(1);}, 120000);
(async () => {
  let port;
  for (let i=0;i<100;i++) {
    try {port=fs.readFileSync(path.join(profile,'DevToolsActivePort'),'utf8').split('\n')[0];break;} catch {}
    if(browser.exitCode!==null)throw Error(errors);
    await pause(100);
  }
  if(!port)throw Error(errors || 'Browser did not start');
  const pages=await (await fetch(`http://127.0.0.1:${port}/json/list`)).json();
  socket=new WebSocket(pages.find(p=>p.type==='page').webSocketDebuggerUrl);
  await new Promise((resolve,reject)=>{socket.onopen=resolve;socket.onerror=reject;});
  let sequence=0;const pending=new Map();
  socket.onmessage=event=>{const data=JSON.parse(event.data);if(pending.has(data.id)){
    const {resolve,reject}=pending.get(data.id);pending.delete(data.id);
    data.error?reject(Error(JSON.stringify(data.error))):resolve(data.result);
  }};
  const command=(method,params={})=>new Promise((resolve,reject)=>{
    const id=++sequence;pending.set(id,{resolve,reject});socket.send(JSON.stringify({id,method,params}));
  });
  const evaluate=async expression=>{
    const result=await command('Runtime.evaluate',{expression,awaitPromise:true,returnByValue:true});
    if(result.exceptionDetails)throw Error(JSON.stringify(result.exceptionDetails));
    return result.result.value;
  };
  await command('Runtime.enable');
  for(let i=0;i<100;i++){if(await evaluate('!!document.getElementById("record") && !document.getElementById("record").disabled'))break;await pause(100);}
  assert.match(await evaluate('document.getElementById("status").textContent'),/413/);
  const blocked=await fetch(base+'/take',{method:'POST',body:'unsigned'});
  assert.equal(blocked.status,403);
  const config=await (await fetch(base+'/config')).json();
  const foreign=await fetch(base+'/take',{method:'POST',headers:{Origin:'https://example.com','X-Benma-Dev':config.token},body:'foreign'});
  assert.equal(foreign.status,403);
  const captureStarted=Date.now();
  await evaluate('document.getElementById("record").click()');
  for(let i=0;i<50;i++){if(await evaluate('!document.getElementById("stop").disabled'))break;await pause(100);}
  assert.equal(await evaluate('document.getElementById("stop").disabled'),false);
  await pause(3300);
  await evaluate('document.getElementById("stop").click()');
  for(let i=0;i<500;i++){
    if(await evaluate('!document.getElementById("record").disabled'))break;
    await pause(100);
  }
  assert.equal(await evaluate('document.querySelectorAll("#results article").length'),5,
    await evaluate('document.getElementById("status").textContent'));
  const ident=await evaluate('takeId');
  const report=await (await fetch(`${base}/takes/${ident}/report.json`)).json();
  assert.equal(report.source_kind,'automated_browser_replay');
  assert.deepEqual(report.units.map(u=>u.target.characters),['我','想','买','这','个']);
  assert.equal(report.chunks[0].text,'这个');
  assert.equal(report.production_grading_changed,false);
  assert.ok(report.units.some(u=>u.expanded.status==='ok'));
  assert.match(await evaluate('document.getElementById("results").textContent'),/not ASR lexical transcription/);
  assert.ok(await evaluate('document.querySelectorAll("#results svg").length')>0);
  const durations=await evaluate(`Promise.all(${JSON.stringify(['canonical.wav',...report.units.flatMap(u=>Object.values(u.clips))])}.map(name=>new Promise((resolve,reject)=>{
    const a=new Audio();a.onloadedmetadata=()=>resolve(a.duration);a.onerror=()=>reject(Error(name));
    a.src='/takes/${ident}/'+name;a.load();})))`);
  assert.ok(durations.every(v=>v>0));
  await evaluate(`document.getElementById('category').value='insufficient evidence';
    document.getElementById('notes').value='AUTOMATED UI TEST ONLY. Not a human perceptual judgment.';
    document.getElementById('save').click();`);
  for(let i=0;i<50;i++){if(await evaluate('document.getElementById("saved").textContent.includes("Saved")'))break;await pause(100);}
  assert.match(await evaluate('document.getElementById("saved").textContent'),/not ground truth/);
  // Reload persistent report, then inspect both desktop and narrow-screen overflow.
  await command('Page.reload');await pause(600);
  await evaluate(`document.getElementById('history').value='${ident}';document.getElementById('history').dispatchEvent(new Event('change'));`);
  await pause(300);
  assert.equal(await evaluate('document.querySelectorAll("#results article").length'),5);
  await command('Emulation.setDeviceMetricsOverride',{width:390,height:844,deviceScaleFactor:1,mobile:false});
  assert.ok(await evaluate('document.documentElement.scrollWidth <= innerWidth + 1'));
  const screenshot=await command('Page.captureScreenshot',{format:'png',captureBeyondViewport:false});
  fs.writeFileSync(path.join(output,'browser-mobile.png'),Buffer.from(screenshot.data,'base64'));
  const result={status:'PASS',take_id:ident,record_upload_alignment_inference_render:true,
    unsigned_and_foreign_requests_rejected:true,units:5,chunk:'这个',decodable_clips:durations.length,
    persisted_reload:true,observation_not_ground_truth:true,narrow_screen_no_overflow:true,
    elapsed_seconds:(Date.now()-captureStarted)/1000,performance:report.performance};
  fs.writeFileSync(path.join(output,'browser-tests.json'),JSON.stringify(result,null,2)+'\n');
  console.log(JSON.stringify(result,null,2));
})().catch(error=>{console.error(error);process.exitCode=1;}).finally(()=>{
  clearTimeout(timeout);socket?.close();browser.kill();
});
