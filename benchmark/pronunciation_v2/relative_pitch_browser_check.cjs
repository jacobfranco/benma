// Local-file diagnostic viewer validation and saved before/after plots.
// Chromium uses a pipe; no server, provider, remote asset or dependency download.
const fs = require('node:fs');
const path = require('node:path');
const os = require('node:os');
const {spawn} = require('node:child_process');
const assert = require('node:assert/strict');
const {setTimeout:delay} = require('node:timers/promises');
const root = path.resolve(process.argv[2] || 'services/api/var/relative-pitch-gesture');
(async () => {
  const browser = spawn('/usr/bin/chromium', [
    '--headless', '--no-sandbox', '--disable-gpu', '--disable-dev-shm-usage',
    '--disable-background-networking', '--no-first-run', '--disable-component-update',
    '--host-resolver-rules=MAP * ~NOTFOUND',
    '--user-data-dir=' + fs.mkdtempSync(path.join(os.tmpdir(), 'benma-relative-browser-')),
    '--remote-debugging-pipe', 'about:blank',
  ], {stdio: ['ignore', 'ignore', 'pipe', 'pipe', 'pipe']});
  try {
    let sequence = 0, buffer = '', stderr = '';
    const pending = new Map();
    browser.stderr.on('data', chunk => {stderr += chunk;});
    browser.stdio[4].on('data', chunk => {
      buffer += chunk;
      while (buffer.includes('\0')) {
        const end = buffer.indexOf('\0'), message = JSON.parse(buffer.slice(0, end));
        buffer = buffer.slice(end + 1);
        if (pending.has(message.id)) { pending.get(message.id)(message); pending.delete(message.id); }
      }
    });
    async function command(method, params = {}, sessionId) {
      const id = ++sequence, response = new Promise(resolve => pending.set(id, resolve));
      browser.stdio[3].write(JSON.stringify({id, method, params, sessionId}) + '\0');
      let timer;
      const result = await Promise.race([response, new Promise((_, reject) => {
        timer = setTimeout(() => reject(Error('CDP timeout: ' + method + '\n' + stderr)), 15000);
      })]).finally(() => clearTimeout(timer));
      if (result.error) throw Error(JSON.stringify(result.error));
      return result.result;
    }
    const {targetId} = await command('Target.createTarget', {url: 'about:blank'});
    const {sessionId} = await command('Target.attachToTarget', {targetId, flatten: true});
    await command('Page.enable', {}, sessionId);
    await command('Network.enable', {}, sessionId);
    await command('Network.setBlockedURLs', {urls: ['http://*', 'https://*']}, sessionId);
    await command('Emulation.setDeviceMetricsOverride', {width:1500, height:1220, deviceScaleFactor:1, mobile:false}, sessionId);
    await command('Page.navigate', {url:'file://' + root + '/viewer.html'}, sessionId);
    await delay(700);
    async function evaluate(expression) {
      const r = await command('Runtime.evaluate', {expression, returnByValue:true}, sessionId);
      if (r.exceptionDetails) throw Error(JSON.stringify(r.exceptionDetails));
      return r.result.value;
    }
    const recordings = await evaluate(`evidence.recordings.map(r=>({id:r.id,projected:r.projected_count}))`);
    assert.equal(recordings.length,6);
    fs.mkdirSync(path.join(root,'figures'),{recursive:true});
    for (let i=0;i<recordings.length;i++) {
      const state=await evaluate(`setReview(${i})`);
      assert.equal(state.id,recordings[i].id);
      assert.equal(state.relativePoints,recordings[i].projected);
      const paths=await evaluate(`document.querySelectorAll('#relative polyline').length`);
      if(i===2) {assert.equal(paths,0);assert.equal(state.relativePoints,0);}
      const text=await evaluate(`document.getElementById('status').textContent`);
      if(i===2)assert(text.includes('NO TRUSTWORTHY TIMING'));
      const metrics=await command('Page.getLayoutMetrics',{},sessionId);
      const image=await command('Page.captureScreenshot',{format:'png',captureBeyondViewport:true,
        clip:{x:0,y:0,width:1500,height:metrics.cssContentSize.height,scale:1}},sessionId);
      fs.writeFileSync(path.join(root,'figures',state.id.slice(0,8)+'.png'),Buffer.from(image.data,'base64'));
    }
    await evaluate(`setReview(1)`);
    const high=await evaluate(`({n:document.querySelectorAll('#high-control circle').length,
      segments:document.querySelectorAll('#high-control polyline').length})`);
    assert.deepEqual(high,{n:24,segments:2});
    const low=await evaluate(`evidence.low_control.explicit.selected_hz`);
    assert.equal(low,54.61);
    const hover=await evaluate(`const point=document.querySelector('#relative circle');
      point.dispatchEvent(new Event('pointerenter')); document.getElementById('inspect').textContent`);
    assert(hover.includes('source_frame_index')&&hover.includes('timestamp_seconds'));
    const grouped=await evaluate(`setReview(0); document.getElementById('units').textContent`);
    assert(grouped.includes('雨伞 (grouped)'));
    await command('Emulation.setDeviceMetricsOverride',{width:390,height:844,deviceScaleFactor:1,mobile:true},sessionId);
    await evaluate(`draw()`);
    assert.equal(await evaluate(`document.querySelectorAll('#relative svg').length`),1);
    console.log('PASS: six local recordings; exact projected counts; empty no-timing Mine; grouped span; 24 high points / 2 gap-separated paths; protected 54.610 Hz; provenance hover; narrow viewport; six full screenshots.');
    await command('Browser.close');
  } finally {if(browser.exitCode===null)browser.kill();}
})().catch(error=>{console.error(error);process.exitCode=1;});
