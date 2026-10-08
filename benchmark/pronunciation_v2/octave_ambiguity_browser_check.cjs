// Local-file diagnostic viewer validation and saved before/after plots.
// Chromium uses a pipe; no server, provider, remote asset or dependency download.
const fs = require('node:fs');
const path = require('node:path');
const os = require('node:os');
const {spawn} = require('node:child_process');
const assert = require('node:assert/strict');
const {setTimeout:delay} = require('node:timers/promises');
const root = path.resolve(process.argv[2] || 'services/api/var/octave-ambiguity');
(async () => {
  const browser = spawn('/usr/bin/chromium', [
    '--headless', '--no-sandbox', '--disable-gpu', '--disable-dev-shm-usage',
    '--disable-background-networking', '--no-first-run', '--disable-component-update',
    '--host-resolver-rules=MAP * ~NOTFOUND',
    '--user-data-dir=' + fs.mkdtempSync(path.join(os.tmpdir(), 'benma-octave-browser-')),
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
    const recordings = await evaluate(`evidence.map(r=>({id:r.id,windows:r.windows.map(w=>w[0])}))`);
    assert.equal(recordings.length, 7);
    fs.mkdirSync(path.join(root, 'figures'), {recursive:true});
    let figures = 0;
    for (const r of recordings) {
      for (const event of ['all', ...r.windows]) {
        const state = await evaluate(`setReview(${JSON.stringify(r.id)},${JSON.stringify(event)}); window.__review`);
        assert.equal(state.recording, r.id);
        assert(state.after <= state.before);
        const image = await command('Page.captureScreenshot', {format:'png'}, sessionId);
        fs.writeFileSync(path.join(root, 'figures', r.id.slice(0,8)+'-'+event+'.png'), Buffer.from(image.data,'base64'));
        figures++;
      }
    }
    const low = await evaluate(`setReview('7787300e','protected-low'); const f=active.frames.find(f=>f.timestamp_seconds===2.5124); const a=trialFrames().find(f=>f.timestamp_seconds===2.5124); ({raw:f.raw_f0_hz,before:f.selected_f0_hz,after:a.selected_f0_hz})`);
    assert.deepEqual(low, {raw:54.61,before:54.61,after:null});
    const protectedStrict = await evaluate(`setReview('7787300e','protected-low','consensus'); trialFrames().find(f=>f.timestamp_seconds===2.5124).selected_f0_hz`);
    assert.equal(protectedStrict,54.61);
    const strict = await evaluate(`setReview(evidence[0].id,'A4','consensus'); window.__review`);
    assert.equal(strict.before-strict.after,4);
    await command('Input.dispatchMouseEvent', {type:'mouseMoved',x:730,y:690}, sessionId);
    const info = await evaluate(`document.getElementById('inspect').textContent`);
    assert(info.includes('candidates') && info.includes('raw_tracker_hz'));
    console.log(`PASS: seven recordings, 13 event zooms, ${figures} saved plots, exact frame counts, unsafe low-F0 counterexample, consensus switch, candidate hover. Local files only.`);
    await command('Browser.close');
  } finally { if (browser.exitCode === null) browser.kill(); }
})().catch(error => {console.error(error);process.exitCode=1;});
