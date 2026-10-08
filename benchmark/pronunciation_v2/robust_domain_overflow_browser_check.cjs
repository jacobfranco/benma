// Local-file diagnostic viewer validation and saved before/after plots.
// Chromium uses a pipe; no server, provider, remote asset or dependency download.
const fs = require('node:fs');
const path = require('node:path');
const os = require('node:os');
const {spawn} = require('node:child_process');
const assert = require('node:assert/strict');
const {setTimeout:delay} = require('node:timers/promises');
const root = path.resolve(process.argv[2] || 'services/api/var/relative-pitch-gesture/overflow');
(async () => {
  const browser = spawn('/usr/bin/chromium', [
    '--headless', '--no-sandbox', '--disable-gpu', '--disable-dev-shm-usage',
    '--disable-background-networking', '--no-first-run', '--disable-component-update',
    '--host-resolver-rules=MAP * ~NOTFOUND',
    '--user-data-dir=' + fs.mkdtempSync(path.join(os.tmpdir(), 'benma-overflow-browser-')),
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
    fs.mkdirSync(path.join(root,'figures'),{recursive:true});
    assert.equal(await evaluate('evidence.recordings.length'),6);
    for (const policy of ['q90','q95','q97.5','mad3']) {
      await evaluate(`document.getElementById('policy').value='${policy}';render()`);
      for (let i=0;i<6;i++) {
        const state=await evaluate(`review(${i})`);
        assert.equal(state.points,[252,188,0,224,161,136][i]);
        assert.equal(await evaluate(`document.querySelectorAll('#robust .overflow-event').length`),state.events);
        assert.equal(await evaluate(`document.querySelectorAll('#robust .point').length`),await evaluate(`evidence.recordings[${i}].policies['${policy}'].inside_points`));
        if(i===2)assert.equal(await evaluate(`document.querySelectorAll('#robust .contour').length`),0);
        if(policy==='mad3'||i===0){
          const metrics=await command('Page.getLayoutMetrics',{},sessionId);
          const shot=await command('Page.captureScreenshot',{format:'png',captureBeyondViewport:true,clip:{x:0,y:0,width:1500,height:metrics.cssContentSize.height,scale:1}},sessionId);
          fs.writeFileSync(path.join(root,'figures',state.id.slice(0,8)+'-'+policy+'.png'),Buffer.from(shot.data,'base64'));
        }
      }
    }
    await evaluate(`review(0)`);
    assert.equal(await evaluate(`document.querySelectorAll('#zoom .overflow-event').length`),2);
    assert.equal(await evaluate(`document.querySelectorAll('#zoom .crossing').length`),1);
    const box=await evaluate(`const b=document.getElementById('zoom-section').getBoundingClientRect();({x:b.x,y:b.y,width:b.width,height:b.height,scale:1})`);
    const shot=await command('Page.captureScreenshot',{format:'png',captureBeyondViewport:true,clip:box},sessionId);
    fs.writeFileSync(path.join(root,'figures','40357072-zoom.png'),Buffer.from(shot.data,'base64'));
    await evaluate(`review(1)`);
    const sustained=await evaluate(`evidence.recordings[1].policies.mad3.events.filter(e=>e.unit_key==='5').map(e=>e.duration_seconds)`);
    assert(Math.abs(sustained[0]-.03)<1e-9&&Math.abs(sustained[1]-.21)<1e-9);
    const hover=await evaluate(`document.querySelector('#robust .overflow-event').dispatchEvent(new Event('pointerenter'));document.getElementById('inspect').textContent`);
    assert(hover.includes('source_indices')&&hover.includes('duration_seconds'));
    await command('Emulation.setDeviceMetricsOverride',{width:390,height:844,deviceScaleFactor:1,mobile:true},sessionId);
    await evaluate(`review(0)`);
    assert.equal(await evaluate(`document.querySelectorAll('#robust svg').length`),1);
    assert(await evaluate(`const host=document.getElementById('robust');host.scrollWidth>host.clientWidth`));
    const mobileShot=await command('Page.captureScreenshot',{format:'png'},sessionId);
    fs.writeFileSync(path.join(root,'figures','40357072-narrow.png'),Buffer.from(mobileShot.data,'base64'));
    console.log('PASS: all six takes × four policies; exact inside counts and event counts; empty no-timing Mine; grouped zoom with exact crossing; 30/210 ms sustained high overflow; provenance hover; narrow viewport; nine full screenshots + group zoom.');
    await command('Browser.close');
  } finally {if(browser.exitCode===null)browser.kill();}
})().catch(error=>{console.error(error);process.exitCode=1;});
