/* Browser checks with synthetic in-memory answers only; no participant exports retained. */
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const assert = require('node:assert/strict');
const {spawn} = require('node:child_process');
const {pathToFileURL} = require('node:url');
const root = process.env.NATIVE_LISTENER_TEST_PACKAGE || path.resolve(__dirname, '../data/generated/native-listener-validation-v1');
const profile = fs.mkdtempSync(path.join(os.tmpdir(), 'SYNTHETIC-native-listener-browser-'));
const browser = spawn('/usr/bin/chromium', [
  '--headless', '--no-sandbox', '--disable-gpu', '--disable-background-networking',
  '--disable-extensions', '--no-first-run', '--no-default-browser-check',
  '--autoplay-policy=no-user-gesture-required', '--remote-debugging-port=0',
  `--user-data-dir=${profile}`, pathToFileURL(path.join(root, 'listener-packages/L01/index.html')).href,
], {stdio:['ignore','ignore','pipe']});
let errors = '', socket;
browser.stderr.on('data', data => {errors += data;});
const pause = ms => new Promise(resolve => setTimeout(resolve, ms));
const timeout = setTimeout(() => {browser.kill(); throw Error('Browser test timed out');}, 90000);
(async () => {
  let port;
  for(let i=0;i<100;i++) {
    try {port = fs.readFileSync(path.join(profile,'DevToolsActivePort'),'utf8').split('\n')[0];break;} catch {}
    if(browser.exitCode !== null) throw Error(errors);
    await pause(100);
  }
  assert.ok(port, errors);
  const pages = await (await fetch(`http://127.0.0.1:${port}/json/list`)).json();
  socket = new WebSocket(pages.find(p=>p.type==='page').webSocketDebuggerUrl);
  await new Promise((resolve,reject)=>{socket.onopen=resolve;socket.onerror=reject;});
  const pending = new Map(); let sequence = 0;
  socket.onmessage = event => {const d=JSON.parse(event.data);if(pending.has(d.id)) {
    const p=pending.get(d.id);pending.delete(d.id);d.error?p.reject(Error(JSON.stringify(d.error))):p.resolve(d.result);
  }};
  const command=(method,params={})=>new Promise((resolve,reject)=>{const id=++sequence;pending.set(id,{resolve,reject});socket.send(JSON.stringify({id,method,params}));});
  const evaluate=async expression=>{const r=await command('Runtime.evaluate',{expression,awaitPromise:true,returnByValue:true});
    if(r.exceptionDetails)throw Error(JSON.stringify(r.exceptionDetails));return r.result.value;};
  await command('Runtime.enable');
  for(let i=0;i<50;i++){if(await evaluate('document.readyState === "complete"'))break;await pause(100);}
  assert.equal(await evaluate('PACKET.trials.length'),68);
  assert.equal(await evaluate('document.body.innerText.includes("expanded")'),false);
  await evaluate(`$('start').click()`);
  assert.equal(await evaluate('result === null'),true);
  await evaluate(`['adult','native','primary_childhood','independent'].forEach(k=>$(k).checked=true);$('start').click()`);
  assert.equal(await evaluate('$ ("next").disabled'),true);
  await evaluate(`document.querySelector('[value="UNCLEAR"]').checked=true;enableNext();$('next').click()`);
  assert.equal(await evaluate('result.responses.length'),0);
  // Decode every embedded WAV through the actual browser media stack.
  const media = await evaluate(`Promise.all(PACKET.trials.flatMap(t=>[t.target,t.context]).map(src=>new Promise((resolve,reject)=>{
    const a=new Audio(src);a.onloadedmetadata=()=>resolve(a.duration);a.onerror=()=>reject(Error('audio decode'));a.load();
  })))`);
  assert.equal(media.length,136);assert.ok(media.every(d=>d>0));
  // Exercise actual playback promise, context sequence (when applicable), response gating and saving.
  await evaluate(`$('play').onclick()`);
  assert.equal(await evaluate('heard'),true);
  assert.equal(await evaluate('$ ("next").disabled'),false);
  await evaluate(`$('next').click()`);
  assert.equal(await evaluate('result.responses.length'),1);
  await command('Page.reload');await pause(500);
  assert.equal(await evaluate('result.responses.length'),1);
  // Exercise the context-then-target playback branch with real audio as well.
  await evaluate(`(async()=>{index=PACKET.trials.findIndex(t=>t.view==='context');heard=false;
    await $('play').onclick();})()`);
  assert.equal(await evaluate('heard'),true);
  assert.ok(await evaluate('parseFloat($("zone").style.width)>0'));
  await evaluate('refresh()');
  // Complete synthetic UI responses in memory, including both abstention choices.
  await evaluate(`while(result.responses.length<PACKET.trials.length){heard=true;plays=1;
    const code=result.responses.length%2?'NEUTRAL':'UNCLEAR';
    document.querySelector('[value="'+code+'"]').checked=true;enableNext();$('next').click();}`);
  assert.equal(await evaluate('result.responses.length'),68);
  assert.equal(await evaluate('$ ("done").hidden'),false);
  assert.equal(await evaluate('$ ("study").hidden'),true);
  await evaluate(`window.testExports=[];URL.createObjectURL=blob=>{testExports.push(blob);return 'blob:synthetic';};
    HTMLAnchorElement.prototype.click=function(){};$('export').click();$('csv').click();`);
  const exported = await evaluate(`(async()=>JSON.parse(await testExports[0].text()))()`);
  assert.equal(exported.responses.length,68);assert.ok(exported.completed_at);
  assert.equal(exported.listener_id,'L01');assert.equal(exported.eligibility.adult,true);
  const csv=await evaluate(`testExports[1].text()`);assert.equal(csv.trim().split('\n').length,69);
  assert.ok(exported.responses.some(r=>r.answer==='NEUTRAL'));
  assert.ok(exported.responses.some(r=>r.answer==='UNCLEAR'));
  // Narrow viewport remains usable.
  await command('Emulation.setDeviceMetricsOverride',{width:390,height:844,deviceScaleFactor:1,mobile:false});
  assert.ok(await evaluate('document.documentElement.scrollWidth <= 390'));
  console.log(JSON.stringify({passed:true,trials:68,decoded_audio_views:136,actual_playback:true,context_sequence:true,
    omission_guard:true,eligibility_guard:true,resume:true,json_export:true,csv_export:true,narrow_view:true,
    synthetic_only:true},null,2));
})().catch(error=>{console.error(error);process.exitCode=1;}).finally(async()=>{
  clearTimeout(timeout);if(socket)socket.close();browser.kill();await pause(300);
  fs.rmSync(profile,{recursive:true,force:true});
});
