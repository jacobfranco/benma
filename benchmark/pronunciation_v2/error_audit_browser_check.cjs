/* Offline functional check. Test annotations and embedded audio exist only in /tmp. */
const fs = require('node:fs');
const path = require('node:path');
const os = require('node:os');
const assert = require('node:assert/strict');
const {spawn} = require('node:child_process');
const {setTimeout: delay} = require('node:timers/promises');
const root = path.resolve(__dirname, '../..');
const output = path.join(root, 'docs/research/pronunciation-v2/2026-09-30-experiment-2-error-audit');
const original = fs.readFileSync(path.join(output, 'human-audit/index.html'), 'utf8');
const items = JSON.parse(original.match(/<script id="items" type="application\/json">(.*?)<\/script>/s)[1]);
const provenance = JSON.parse(fs.readFileSync(path.join(output, 'provenance.json'), 'utf8'));
const source = provenance.audio.find(row => row.source_asset_id === items[0].source_asset_id);
const audio = fs.readFileSync(path.resolve(root, source.local_path)).toString('base64');
const script = `
<script>
(async () => {
  const check = (ok, message) => {if (!ok) throw Error(message);};
  const marker = document.createElement('pre'); marker.id = 'browser-check';
  document.body.append(marker);
  try {
    check(items.length === 118, 'coverage');
    check($('target').textContent.includes(items[0].text), 'initial rendering');
    $('realized').value = 'unclear'; $('realized').dispatchEvent(new Event('input'));
    $('certainty').value = 'low'; $('certainty').dispatchEvent(new Event('input'));
    $('note').value = 'TEST ONLY: comma, quote " and newline\\nsecond line';
    $('note').dispatchEvent(new Event('input'));
    $('next').click(); $('prev').click();
    check($('realized').value === 'unclear' && $('note').value.includes('second line'), 'navigation persistence');
    const saved = JSON.parse(localStorage.getItem(key));
    check(saved[items[0].source_asset_id].realized_tone === 'unclear', 'browser persistence');
    let exported;
    download = (name, text, type) => {exported = {name, text, type};};
    $('csv').click();
    check(exported.name.endsWith('.csv'), 'CSV download');
    check(items.every(item => exported.text.split(item.source_asset_id).length === 2), 'unique CSV joins');
    check(exported.text.includes('quote "" and newline\\nsecond line'), 'CSV escaping');
    $('save').click(); const backup = exported.text;
    check(JSON.parse(backup).annotations[items[0].source_asset_id].confidence === 'low', 'JSON export');
    marker.textContent = 'WAIT: restore'; annotations = {}; render();
    const restore = new DataTransfer();
    restore.items.add(new File([backup], 'annotations.json', {type:'application/json'}));
    $('restore').files = restore.files; await $('restore').onchange({target:$('restore')});
    check($('realized').value === 'unclear', 'JSON restore');
    const invalid = new DataTransfer();
    invalid.items.add(new File(['{"schema":"wrong","annotations":{}}'], 'bad.json'));
    $('restore').files = invalid.files; await $('restore').onchange({target:$('restore')});
    check($('status').textContent.includes('Restore failed'), 'invalid import rejected');
    marker.textContent = 'WAIT: audio'; const selected = new DataTransfer();
    const bytes = Uint8Array.from(atob('${audio}'), character => character.charCodeAt(0));
    selected.items.add(new File([bytes], items[0].audio_filename, {type:'audio/wav'}));
    $('audio').preload = 'auto';
    $('files').files = selected.files; $('files').dispatchEvent(new Event('change'));
    check($('audio').src.startsWith('blob:'), 'local audio selection');
    await new Promise((resolve, reject) => {
      $('audio').onloadedmetadata = resolve; $('audio').onerror = () => reject(Error('audio decode'));
      if ($('audio').readyState >= 1) resolve();
    });
    check($('audio').duration > 0, 'decoded audio duration');
    marker.textContent = 'WAIT: playback'; await $('audio').play(); check(!$('audio').paused, 'playback started'); $('audio').pause();
    $('goto').value = '118'; $('goto').dispatchEvent(new Event('change'));
    check($('next').disabled && $('target').textContent.includes(items[117].text), 'last item');
    check(!Object.keys(items[0]).some(key => key.startsWith('A_') || key.startsWith('B_')), 'blind data');
    marker.textContent = 'PASS: 118 identities, navigation, persistence, CSV/JSON export, restore, validation, local audio decoding and playback';
  } catch (error) {marker.textContent = 'FAIL: ' + error.stack;}
})();
</script>`;
(async () => {
 const temp = fs.mkdtempSync(path.join(os.tmpdir(), 'benma-audit-browser-check-'));
 let browser;
 try {
  const file = path.join(temp, 'test.html');
  fs.writeFileSync(file, original.replace('</html>', script + '</html>'));
  browser = spawn(process.env.CHROMIUM || '/usr/bin/chromium', [
    '--headless', '--no-sandbox', '--disable-gpu', '--disable-dev-shm-usage',
    '--autoplay-policy=no-user-gesture-required', '--disable-background-networking',
    '--no-first-run', '--user-data-dir=' + path.join(temp, 'profile'),
    '--remote-debugging-pipe', 'about:blank'
  ], {stdio:['ignore', 'ignore', 'pipe', 'pipe', 'pipe']});
  let sequence = 0, buffer = '', stderr = '';
  const pending = new Map();
  browser.stderr.on('data', chunk => {stderr += chunk;});
  browser.stdio[4].on('data', chunk => {
    buffer += chunk;
    while (buffer.includes('\0')) {
      const end = buffer.indexOf('\0'), message = JSON.parse(buffer.slice(0, end));
      buffer = buffer.slice(end + 1);
      if (pending.has(message.id)) {
        pending.get(message.id)(message); pending.delete(message.id);
      }
    }
  });
  async function command(method, params = {}, sessionId) {
    const id = ++sequence;
    const response = new Promise(resolve => pending.set(id, resolve));
    browser.stdio[3].write(JSON.stringify({id, method, params, sessionId}) + '\0');
    let timeout;
    const result = await Promise.race([response, new Promise((_, reject) => {
      timeout = setTimeout(() => reject(Error('CDP timeout: ' + method + '\n' + stderr)), 15000);
    })]).finally(() => clearTimeout(timeout));
    if (result.error) throw Error(JSON.stringify(result.error));
    return result.result;
  }
  const {targetId} = await command('Target.createTarget', {url:'about:blank'});
  const {sessionId} = await command('Target.attachToTarget', {targetId, flatten:true});
  await command('Page.enable', {}, sessionId);
  await command('Page.navigate', {url:'file://' + file}, sessionId);
  let marker;
  for (let attempt = 0; attempt < 100; attempt++) {
    const response = await command('Runtime.evaluate', {
      expression:"document.getElementById('browser-check')?.textContent", returnByValue:true
    }, sessionId);
    marker = response.result.value;
    if (marker?.startsWith('PASS:') || marker?.startsWith('FAIL:')) break;
    await delay(100);
  }
  assert(marker?.startsWith('PASS:'), marker || 'Browser did not finish functional check');
  console.log(marker);
  // Inspect the real unmodified blank form; temporary test annotations are cleared.
  await command('Runtime.evaluate', {expression:'localStorage.clear()'}, sessionId);
  await command('Page.navigate', {url:'file://' + path.join(output, 'human-audit/index.html')}, sessionId);
  await command('Emulation.setDeviceMetricsOverride', {
    width:1000, height:1400, deviceScaleFactor:1, mobile:false
  }, sessionId);
  await delay(300);
  const screenshot = await command('Page.captureScreenshot', {format:'png'}, sessionId);
  fs.writeFileSync('/tmp/benma-error-audit-page.png', Buffer.from(screenshot.data, 'base64'));
  await command('Browser.close');
 } finally {
  if (browser && browser.exitCode === null) {
    browser.kill(); await new Promise(resolve => browser.once('exit', resolve));
  }
  fs.rmSync(temp, {recursive:true, force:true});
 }
})().catch(error => {console.error(error); process.exitCode = 1;});
