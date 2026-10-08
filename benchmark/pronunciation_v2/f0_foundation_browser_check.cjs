// Offline six-tracker browser regression; no server or remote assets.
const path=require('node:path'); const os=require('node:os');
const root=path.resolve(process.argv[2] || 'services/api/var/f0-foundation');
const fs=require('node:fs'); const {spawn}=require('node:child_process'); const assert=require('node:assert/strict'); const {setTimeout:delay}=require('node:timers/promises');
(async()=>{
 const browser=spawn('/usr/bin/chromium',['--headless','--no-sandbox','--disable-gpu','--disable-dev-shm-usage','--autoplay-policy=no-user-gesture-required','--disable-background-networking','--no-first-run','--user-data-dir='+fs.mkdtempSync(path.join(os.tmpdir(),'benma-rmvpe-browser-')),'--remote-debugging-pipe','about:blank'],{stdio:['ignore','ignore','pipe','pipe','pipe']});
 try {
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

 const {targetId}=await command('Target.createTarget',{url:'about:blank'});
 const {sessionId}=await command('Target.attachToTarget',{targetId,flatten:true});
 await command('Page.enable',{},sessionId);
 await command('Page.navigate',{url:'file://'+root+'/viewer.html'},sessionId);
 await delay(1200);
 const result=await command('Runtime.evaluate',{awaitPromise:true,returnByValue:true,expression:`(async()=>{
 const check=(v,m)=>{if(!v)throw Error(m)};
 const cards=document.querySelectorAll('details[id]');check(cards.length===49,'49 recordings');
 for(const c of cards){for(const label of 'ABCDEF'){check(c.querySelector('.track-'+label+'-raw')&&c.querySelector('.track-'+label+'-minimal')&&c.querySelector('.confidence-'+label),'six complete track groups')}}
 const card=document.getElementById('native_24k');check(card.open,'native expanded');
 for(const label of 'ABCDEF'){const box=card.querySelector('[data-track="'+label+'"]');const line=card.querySelector('.track-'+label+'-raw');box.click();check(getComputedStyle(line).display==='none','each tracker toggle');box.click();}
 const raw=card.querySelector('.track-A-raw');const clean=card.querySelector('.track-A-minimal');check(raw&&clean,'both views');
 check(getComputedStyle(raw).display!=='none','raw initially visible');
 const box=card.querySelector('[data-track="A"]');box.click();check(getComputedStyle(raw).display==='none','tracker toggle');box.click();
 const mode=card.querySelector('.mode');mode.value='minimal';mode.dispatchEvent(new Event('change'));check(getComputedStyle(clean).display!=='none'&&getComputedStyle(raw).display==='none','cleanup mode');
 card.querySelector('.production-toggle').click();check(getComputedStyle(card.querySelector('.production')).display!=='none','production overlay');
 const audio=card.querySelector('audio');audio.preload='auto';audio.load();await new Promise((resolve,reject)=>{audio.onloadedmetadata=resolve;audio.onerror=()=>reject(Error('audio failed'));if(audio.readyState>=1)resolve()});check(Math.abs(audio.duration-1.05)<.001,'audio duration');await audio.play();check(!audio.paused,'local playback');audio.pause();
 mode.value='raw';mode.dispatchEvent(new Event('change'));card.querySelector('.production-toggle').click();
 return 'PASS: 49 recordings, six complete raw/minimal/confidence groups each, all six toggles, native display, raw/minimal switch, production overlay, audio decode and playback';
 })()`},sessionId);
 if(result.exceptionDetails)throw Error(JSON.stringify(result.exceptionDetails));
 assert(result.result.value?.startsWith('PASS:'),JSON.stringify(result));console.log(result.result.value);
 await command('Emulation.setDeviceMetricsOverride',{width:1500,height:1050,deviceScaleFactor:1,mobile:false},sessionId);
 const screenshot=await command('Page.captureScreenshot',{format:'png'},sessionId);fs.writeFileSync(path.join(root,'rmvpe/viewer-browser.png'),Buffer.from(screenshot.data,'base64'));
 await command('Browser.close');
 } finally {if(browser.exitCode===null)browser.kill();}
})().catch(e=>{console.error(e);process.exitCode=1});
