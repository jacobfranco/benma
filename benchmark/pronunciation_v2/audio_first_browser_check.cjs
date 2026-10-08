// Offline research-card, audio scheduling and mobile viewport validation.
// Chromium uses a pipe; no server, provider, remote asset or dependency download.
const fs = require('node:fs');
const path = require('node:path');
const os = require('node:os');
const {spawn} = require('node:child_process');
const assert = require('node:assert/strict');
const {setTimeout:delay} = require('node:timers/promises');
const root = path.resolve(process.argv[2] || 'services/api/var/audio-first-feedback');
(async () => {
  const browser = spawn('/usr/bin/chromium', [
    '--headless', '--no-sandbox', '--disable-gpu', '--disable-dev-shm-usage',
    '--disable-background-networking', '--no-first-run', '--disable-component-update',
    '--host-resolver-rules=MAP * ~NOTFOUND',
    '--user-data-dir=' + fs.mkdtempSync(path.join(os.tmpdir(), 'benma-audio-first-browser-')),
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
      const r = await command('Runtime.evaluate', {expression, returnByValue:true,awaitPromise:true,userGesture:true}, sessionId);
      if (r.exceptionDetails) throw Error(JSON.stringify(r.exceptionDetails));
      return r.result.value;
    }
    fs.mkdirSync(path.join(root,'figures'),{recursive:true});
    const results=[];
    assert.equal(await evaluate('evidence.recordings.length'),6);
    const frozen=await evaluate('JSON.stringify(evidence.recordings.map(r=>r.data))');
    for(const width of [390,320]) {
      await command('Emulation.setDeviceMetricsOverride',{width,height:844,deviceScaleFactor:1,mobile:true},sessionId);
      for(let i=0;i<6;i++) {
        const state=await evaluate(`review(${i})`);
        assert.equal(state.cards,[6,6,0,6,6,6][i]);
        assert.equal(state.points,[253,189,214,224,164,140][i]);
        assert(await evaluate('document.documentElement.scrollWidth <= innerWidth'));
        assert.equal(await evaluate(`$('pitch-details').open`),false);
        assert.equal(await evaluate(`document.querySelectorAll('.unit .status').length`),state.cards);
        assert.equal(await evaluate(`document.querySelectorAll('[data-action="exact"]').length`),state.cards);
        assert.equal(await evaluate(`document.querySelectorAll('[data-action="context"]').length`),state.cards);
        assert(await evaluate(`Array.from(document.querySelectorAll('.unit .actions')).every(actions=>{
          const [mine,context]=actions.children;
          return mine.getBoundingClientRect().height>=44 && context.getBoundingClientRect().height>=44 &&
            mine.getBoundingClientRect().top===context.getBoundingClientRect().top &&
            mine.getAttribute('aria-label').startsWith('Play exact recording for ') &&
            context.getAttribute('aria-label').startsWith('Play recording with context for ');
        })`));
        assert(!await evaluate(`$('cards').textContent.match(/correct|incorrect|detected Tone|wrong pronunciation/)`));
        if(i===0){
          assert.equal(await evaluate(`document.querySelectorAll('[data-focus="5:7"]').length`),1);
          assert.equal(await evaluate(`document.querySelectorAll('[aria-label="Play exact recording for 雨伞"]').length`),1);
          assert.equal(await evaluate(`document.querySelectorAll('[aria-label="Play recording with context for 雨伞"]').length`),1);
          assert.equal(await evaluate(`document.querySelectorAll('[aria-label="Play exact recording for 雨"], [aria-label="Play exact recording for 伞"], [aria-label="Play recording with context for 雨"], [aria-label="Play recording with context for 伞"]').length`),0);
          assert.equal(await evaluate(`document.querySelector('[data-play="5:7"]').getBoundingClientRect().height>=44`),true);
          await evaluate(`document.querySelector('[data-focus="5:7"]').click()`);
          assert.equal(await evaluate(`document.activeElement.dataset.play`),'5:7');
          assert.equal(await evaluate(`document.querySelector('.unit[data-selected="true"] .han').textContent`),'雨伞');
        }
        if(i===2){
          assert(await evaluate(`$('untimed').textContent.includes('Timing-specific feedback unavailable')`));
          assert.equal(await evaluate(`document.querySelectorAll('[data-focus]').length`),0);
        }
        await evaluate('window.scrollTo(0,0)');
        const shot=await command('Page.captureScreenshot',{format:'png'},sessionId);
        fs.writeFileSync(path.join(root,'figures',`${state.id.slice(0,8)}-${width}-list.png`),Buffer.from(shot.data,'base64'));
        if(width===390){
          const metrics=await command('Page.getLayoutMetrics',{},sessionId);
          const full=await command('Page.captureScreenshot',{format:'png',captureBeyondViewport:true,clip:{x:0,y:0,width,height:metrics.cssContentSize.height,scale:1}},sessionId);
          fs.writeFileSync(path.join(root,'figures',`${state.id.slice(0,8)}-full-list.png`),Buffer.from(full.data,'base64'));
        }
        await evaluate(`$('pitch-details').open=true`);
        assert.equal(await evaluate(`document.querySelectorAll('#plot .point').length`),state.points);
        assert.equal(await evaluate(`document.querySelectorAll('#plot .selected-segment').length`),await evaluate(`evidence.recordings[${i}].data.tone_graph.filtered.segments.filter(s=>s.length>1).length`));
        await evaluate(`$('raw').open=true`);await delay(30);
        assert.equal(await evaluate(`$('raw-data').textContent`),await evaluate(`JSON.stringify(evidence.recordings[${i}].data.tone_graph.raw,null,2)`));
      }
    }
    await command('Emulation.setDeviceMetricsOverride',{width:390,height:844,deviceScaleFactor:1,mobile:true},sessionId);
    for(const mode of ['Practice','Free Practice','Conversation']) {
      await evaluate(`$('mode').value=${JSON.stringify(mode)};review(0)`);
      assert.equal(await evaluate(`$('pronunciation').open`),mode!=='Conversation');
      assert.equal(await evaluate(`$('target-panel').hidden`),mode!=='Practice');
      const cardsBefore=await evaluate(`JSON.stringify(units)`);
      await evaluate(`$('target').value='贵州';renderTarget()`);
      assert.equal(await evaluate(`JSON.stringify(units)`),cardsBefore);
      if(mode==='Conversation'){
        assert(await evaluate(`Array.from(document.querySelectorAll('[data-play]')).every(b=>!b.checkVisibility())`));
        assert(await evaluate(`$('whole').getBoundingClientRect().height>=44`));
        const shot=await command('Page.captureScreenshot',{format:'png'},sessionId);
        fs.writeFileSync(path.join(root,'figures','conversation-collapsed.png'),Buffer.from(shot.data,'base64'));
        await evaluate(`$('pronunciation').open=true`);
      }
      assert.equal(await evaluate(`document.querySelectorAll('[data-action="exact"]').length`),6);
      assert.equal(await evaluate(`document.querySelectorAll('[data-action="context"]').length`),6);
    }
    await evaluate(`$('mode').value='Free Practice';$('layout').value='horizontal';review(0)`);
    assert(await evaluate(`$('cards').scrollWidth>$('cards').clientWidth`));
    assert(await evaluate(`document.documentElement.scrollWidth<=innerWidth`));
    const horizontal=await command('Page.captureScreenshot',{format:'png'},sessionId);
    fs.writeFileSync(path.join(root,'figures','40357072-horizontal.png'),Buffer.from(horizontal.data,'base64'));
    await evaluate(`$('layout').value='vertical';render()`);
    // Actual browser decode and PCM scheduling of all 30 units × 3 context settings.
    // This validates source/time/sample identity, not a human listening judgment.
    const audio=await evaluate(`(async()=>{
      const results=[];
      for(const r of evidence.recordings){
        const decoder=new OfflineAudioContext(1,1,16000);
        const bytes=Uint8Array.from(atob(r.audio_base64),c=>c.charCodeAt(0));
        const buffer=await decoder.decodeAudioData(bytes.buffer);
        let count=0,maxSampleError=0;
        for(const u of AudioFirst.cards(r.data))for(const pad of [0,40,80]){
          const b=AudioFirst.playbackBounds(u.start_seconds,u.end_seconds,buffer.duration,pad);
          const frames=Math.round((b.end_seconds-b.start_seconds)*16000);
          const ctx=new OfflineAudioContext(1,frames+160,16000),source=ctx.createBufferSource();
          source.buffer=buffer;source.connect(ctx.destination);source.start(0,b.start_seconds,b.end_seconds-b.start_seconds);
          const rendered=(await ctx.startRendering()).getChannelData(0),original=buffer.getChannelData(0);
          const offset=Math.round(b.start_seconds*16000);
          for(let i=0;i<frames;i++)maxSampleError=Math.max(maxSampleError,Math.abs(rendered[i]-original[offset+i]));
          if(rendered.slice(frames+1).some(v=>v!==0))throw Error('Playback overran bound');
          count++;
        }
        results.push({id:r.id,duration:buffer.duration,segments:count,max_sample_error:maxSampleError});
      }
      return results;
    })()`);
    assert.equal(audio.reduce((n,r)=>n+r.segments,0),90);
    assert(audio.every(r=>r.max_sample_error<0.000001));
    // Exercise BOTH real card buttons for every accepted unit at each candidate.
    // A running audio context is scheduling evidence, never a listening judgment.
    const actions=await evaluate(`(async()=>{
      const results=[];
      const check=(condition,message)=>{if(!condition)throw Error(message);};
      const wait=()=>new Promise(resolve=>setTimeout(resolve,5));
      for(let i=0;i<6;i++)for(const pad of [40,80]){
        $('padding').value=String(pad);review(i);
        for(const unit of units)for(const action of ['exact','context','exact']){
          const previous=player.source;
          const button=document.querySelector('[data-play="'+unit.key+'"][data-action="'+action+'"]');
          button.click();
          for(let n=0;n<200 && playbackState.state==='loading';n++)await wait();
          check(playbackState.state==='playing','Action did not play');
          check(playbackState.action===action,'Wrong active action');
          check(player.source!==previous,'Source reused');
          if(previous)check(previous.onended===null,'Stale end listener');
          check(document.activeElement===button,'Focus moved to wrong action');
          check(document.querySelectorAll('[data-play][aria-pressed="true"]').length===1,'Ambiguous active action');
          const b=playbackState.bounds,ms=action==='exact'?0:pad;
          check(b.padding_ms===ms,'Mine inherited context selector');
          check(b.start_seconds===Math.max(0,unit.start_seconds-ms/1000),'Wrong start');
          check(b.end_seconds===Math.min(evidence.recordings[i].duration_seconds,unit.end_seconds+ms/1000),'Wrong end');
          results.push({id:evidence.recordings[i].id,key:unit.key,action,padding_ms:ms});
        }
      }
      player.stop();return results;
    })()`);
    assert.equal(actions.length,180);
    for(let i=0;i<6;i++) {
      await evaluate(`review(${i});${i===2?"$('whole').click()":"document.querySelector('[data-play]').click()"}`);
      await delay(120);
      const playback=await evaluate('({state:playbackState.state,context:player.context.state,bounds:playbackState.bounds})');
      assert.equal(playback.state,'playing');assert.equal(playback.context,'running');results.push(playback);
      await evaluate(`$('stop').click()`);
      assert.equal(await evaluate('player.source'),null);
    }
    // Real audio-clock end event; no UI timer involved.
    await evaluate(`review(5);document.querySelector('[data-play="3:4"]').click()`);
    await delay(500);assert.equal(await evaluate('playbackState.state'),'idle');
    await evaluate(`review(0);document.querySelector('[data-play="0:1"]').click();document.querySelector('[data-play="5:7"]').click()`);
    await delay(50);assert.equal(await evaluate('playbackState.key'),'5:7');
    await evaluate('review(2)');assert.equal(await evaluate('player.source'),null);
    // Candidate changes stop playback. Mine stays exact even after selecting 80 ms.
    await evaluate(`review(0);document.querySelector('[data-action="context"]').click()`);
    await delay(50);
    await evaluate(`$('padding').value='40';$('padding').dispatchEvent(new Event('change'))`);
    assert.equal(await evaluate('player.source'),null);
    await evaluate(`document.querySelector('[data-action="exact"]').click();document.querySelector('[data-action="context"]').click();document.querySelector('[data-play="5:7"][data-action="context"]').click()`);
    await delay(50);
    assert.equal(await evaluate('playbackState.action'),'context');
    assert.equal(await evaluate('playbackState.key'),'5:7');
    // Browser back/forward cache suspends this page without permanently disabling replay.
    await evaluate(`window.dispatchEvent(new PageTransitionEvent('pagehide',{persisted:true}))`);
    assert.equal(await evaluate('player.source'),null);
    assert.equal(await evaluate('player.closed'),false);
    await evaluate(`document.querySelector('[data-action="context"]').click()`);
    await delay(50);assert.equal(await evaluate('playbackState.state'),'playing');
    await evaluate(`Object.defineProperty(document,'hidden',{configurable:true,value:true});document.dispatchEvent(new Event('visibilitychange'));delete document.hidden`);
    assert.equal(await evaluate('player.source'),null);
    assert.equal(await evaluate('JSON.stringify(evidence.recordings.map(r=>r.data))'),frozen);
    await evaluate(`document.querySelector('[data-action="context"]').click()`);
    await delay(50);
    await evaluate(`window.dispatchEvent(new PageTransitionEvent('pagehide',{persisted:false}))`);
    await delay(30);
    assert.equal(await evaluate('player.source'),null);
    assert.equal(await evaluate('player.context.state'),'closed');
    assert.equal(await evaluate('player.cache.size'),0);
    fs.writeFileSync(path.join(root,'browser-results.json'),JSON.stringify({audio,button_playback:results,card_actions:actions,widths:[320,390],layouts:2,physical_listening:false,pass:true},null,2)+'\n');
    console.log('PASS: six takes; 320/390 px; two actions/card; grouped focus; collapsed Conversation; target independence; unchanged selected/Raw evidence; 90 PCM spans; 180 exact/context actions; end/cancellation; rapid mixed taps; visibility/page cleanup; back/forward cache. Physical listening NOT performed.');
    await command('Browser.close');
  } finally {if(browser.exitCode===null)browser.kill();}
})().catch(error=>{console.error(error);process.exitCode=1;});
