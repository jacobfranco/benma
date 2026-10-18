/* Browser engineering checks only. Synthetic answers never become human QA. */
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const assert = require('node:assert/strict');
const {spawn} = require('node:child_process');
const {pathToFileURL} = require('node:url');
const packageDir = path.resolve(__dirname, '..');
const root = path.join(packageDir, 'data/generated/aishell3-multispeaker-v2');
const originalMode = false;
const folder = path.join(root, 'spot-check');
const packet = JSON.parse(fs.readFileSync(path.join(folder,'packet.json'),'utf8'));
const expectedCount = packet.items.length;
const expectedMedia = packet.items.reduce((n,item)=>n+Object.keys(item.playback).length,0);
const profile = fs.mkdtempSync(path.join(os.tmpdir(), 'aishell3-browser-test-'));
const browser = spawn('/usr/bin/chromium', [
  '--headless', '--no-sandbox', '--disable-gpu', '--disable-background-networking',
  '--disable-extensions', '--no-first-run', '--no-default-browser-check',
  '--autoplay-policy=no-user-gesture-required', '--remote-debugging-port=0',
  `--user-data-dir=${profile}`, pathToFileURL(path.join(folder, 'index.html')).href,
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
  const media = await evaluate(`Promise.all([...document.querySelectorAll('audio')].map(audio => new Promise((resolve,reject) => {
    audio.addEventListener('loadedmetadata',()=>resolve({duration:audio.duration,error:audio.error?.code||null}),{once:true});
    audio.addEventListener('error',()=>reject(new Error(audio.src+' failed')),{once:true});
    audio.load();
  })))`);
  assert.equal(media.length,expectedMedia); assert.ok(media.every(m=>m.duration>0 && !m.error));
  assert.equal(await evaluate('document.querySelectorAll("section[data-id]").length'),expectedCount);
  // Decode at the source rate, compare every browser float to exact PCM16.
  // This tests browser decoding, not a human listener's audio device.
  let decodedCount=0, maximumRawNormalizationError=0;
  for(const item of packet.items) for(const clip of Object.values(item.playback)) {
    const bytes=fs.readFileSync(path.join(folder,clip.reference));
    const encoded=bytes.toString('base64');
    const decoded=await evaluate(`(async()=>{
      const bytes=Uint8Array.from(atob(${JSON.stringify(encoded)}),c=>c.charCodeAt(0));
      const view=new DataView(bytes.buffer);
      let offset=12, pcmStart, pcmLength, rate;
      while(offset+8<=bytes.length) {
        const tag=String.fromCharCode(...bytes.subarray(offset,offset+4));
        const size=view.getUint32(offset+4,true);
        if(tag==='fmt ') rate=view.getUint32(offset+12,true);
        if(tag==='data') {pcmStart=offset+8;pcmLength=size;}
        offset+=8+size+(size%2);
      }
      const context=new OfflineAudioContext(1,pcmLength/2,rate);
      const buffer=await context.decodeAudioData(bytes.buffer.slice(0));
      const actual=buffer.getChannelData(0);
      let maxError=0, maxErrorAsymmetric=0;
      for(let i=0;i<actual.length;i++) {maxError=Math.max(maxError,Math.abs(actual[i]-view.getInt16(pcmStart+i*2,true)/32768));const sample=view.getInt16(pcmStart+i*2,true);maxErrorAsymmetric=Math.max(maxErrorAsymmetric,Math.abs(actual[i]-sample/(sample<0 ? 32768 : 32767)));}
      return {frames:buffer.length,expected:pcmLength/2,maxError,maxErrorAsymmetric,rate:buffer.sampleRate};
    })()`);
    assert.equal(decoded.frames,decoded.expected);assert.ok(Math.min(decoded.maxError,decoded.maxErrorAsymmetric)<1e-7, JSON.stringify(decoded));assert.equal(decoded.rate,44100);
    maximumRawNormalizationError=Math.max(maximumRawNormalizationError,decoded.maxError);decodedCount++;
  }

  await evaluate(`document.querySelector('[data-view="context"]').click()`);
  await pause(150);
  assert.equal(await evaluate('document.querySelector("audio[data-view=context]").paused'),false);
  await evaluate(`document.querySelector('[data-view="target"]').click()`);
  await pause(30);
  assert.equal(await evaluate('document.querySelector("audio[data-view=target]").paused'),false);
  assert.equal(await evaluate('document.querySelector("audio[data-view=context]").paused'),true);
  await evaluate('document.querySelectorAll("audio").forEach(a=>a.pause())');
  if(!originalMode) {
    assert.equal(await evaluate(`new Promise((resolve,reject)=>{
      const audio=document.querySelector('audio[data-view=final]');
      const timer=setTimeout(()=>reject(new Error('final did not play')),5000);
      audio.addEventListener('playing',()=>{clearTimeout(timer);audio.pause();resolve(true)},{once:true});
      document.querySelector('button[data-view=final]').click();
    })`),true);
  }

  // Intercept downloads in memory: do not create QA answer files.
  await evaluate(`window.testExports=[]; URL.createObjectURL=blob=>{window.testExports.push(blob);return 'blob:synthetic-test'}; HTMLAnchorElement.prototype.click=function(){}; document.getElementById('export').click()`);
  assert.equal(await evaluate('window.testExports.length'),0);
  const original = await evaluate(`JSON.parse(document.getElementById('packet').textContent).packet_sha256`);
  await evaluate(`document.getElementById('reviewer').value='SYNTHETIC BROWSER TEST — NOT HUMAN QA';
    for(const section of document.querySelectorAll('section[data-id]')) {
      for(const select of section.querySelectorAll('select')) {select.value='PASS';select.dispatchEvent(new Event('change'));}
      const heard=section.querySelector('input[type=checkbox]');heard.checked=true;heard.dispatchEvent(new Event('change'));
    }
    document.getElementById('export').click()`);
  const exported = JSON.parse(await evaluate('window.testExports[0].text()'));
  assert.equal(exported.packet_sha256,original); assert.equal(exported.reviews.length,expectedCount);
  assert.ok(exported.reviews.every(r=>r.decision==='PASS' && r.heard_context_and_target && r.reviewed_at));
  if(!originalMode) {
    assert.ok(exported.reviews.every(r=>r.final_decision==='PASS' && r.heard_final));
    await evaluate(`const final=document.querySelector('[data-field=final_decision]');
      final.value='CLIPPED';final.dispatchEvent(new Event('change'));document.getElementById('export').click()`);
    assert.equal(await evaluate('window.testExports.length'),1);
    await evaluate(`const finalReset=document.querySelector('[data-field=final_decision]');
      finalReset.value='PASS';finalReset.dispatchEvent(new Event('change'))`);
  }

  await evaluate(`const first=document.querySelector('section select');first.value='WRONG UNIT';first.dispatchEvent(new Event('change'));document.getElementById('export').click()`);
  assert.equal(await evaluate('window.testExports.length'),1);
  await evaluate(`const notes=document.querySelector('section textarea');notes.value='SYNTHETIC issue';notes.dispatchEvent(new Event('input'));document.getElementById('export').click()`);
  assert.equal(await evaluate('window.testExports.length'),2);
  assert.equal(JSON.parse(await evaluate('window.testExports[1].text()')).reviews[0].decision,'WRONG UNIT');
  await evaluate(`(async()=>{
    const data=await window.testExports[1].text();
    const transfer=new DataTransfer();
    transfer.items.add(new File([data],'synthetic-import.json',{type:'application/json'}));
    const input=document.getElementById('import');input.files=transfer.files;
    input.dispatchEvent(new Event('change'));
  })()`);
  await pause(100);
  assert.equal(await evaluate('document.getElementById("message").textContent'),'Imported. Review and export when complete.');
  await evaluate(`document.getElementById('reviewer').value='SYNTHETIC RENAMED REVIEWER';document.getElementById('export').click()`);
  assert.equal(JSON.parse(await evaluate('window.testExports[2].text()')).reviews[0].reviewer,'SYNTHETIC RENAMED REVIEWER');
  await evaluate(`localStorage.clear(); location.reload()`);
  await pause(300);
  assert.equal(await evaluate('document.querySelectorAll("section select")[0].value'),'');
  await command('Emulation.setDeviceMetricsOverride',{width:1200,height:1000,deviceScaleFactor:1,mobile:false});
  const shot=await command('Page.captureScreenshot',{format:'png'});
  fs.writeFileSync(path.join(root,`spot-check/${originalMode ? 'original' : 'round2'}-browser.png`),Buffer.from(shot.data,'base64'));
  const result={browser:'Chromium',targets:expectedCount,media_loaded:expectedMedia,decoded_pcm_frames_and_normalized_samples_verified:decodedCount,maximum_raw_normalization_error:maximumRawNormalizationError,normalization:'signed PCM16: negative /32768, positive /32767; float tolerance 1e-7',context_and_target_buttons:'pass',
    export_complete_and_incomplete:'pass',import_and_reviewer_identity:'pass',nonpass_notes_required:'pass',synthetic_only:true,
    human_playback_qa:'not_assessed_by_engineering_test',human_answers_written:0};
  fs.writeFileSync(path.join(root,`spot-check/${originalMode ? 'original' : 'round2'}-browser-qa.json`),JSON.stringify(result,null,2)+'\n');
  console.log(JSON.stringify(result));
})().catch(error=>{console.error(error);process.exitCode=1;}).finally(async()=>{
  socket?.close(); browser.kill('SIGTERM'); await pause(300); fs.rmSync(profile,{recursive:true,force:true});
});
