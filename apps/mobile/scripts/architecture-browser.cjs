/* Offline acceptance of actual persisted phone evidence. All /v1 calls intercepted.
 * PLAYWRIGHT_MODULE=/path/to/playwright BENMA_WEB_URL=http://localhost:8083 node scripts/architecture-browser.cjs
 */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const { chromium, devices } = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
let debugPage;
const results = require('../src/__tests__/fixtures/architectureAcceptance.json');
const output = process.env.BENMA_BROWSER_OUTPUT || '/tmp/benma-architecture-browser';
fs.mkdirSync(output, { recursive: true });
function wav() {
  const b=Buffer.alloc(3244); b.write('RIFF'); b.writeUInt32LE(3236,4); b.write('WAVEfmt ',8);
  b.writeUInt32LE(16,16); b.writeUInt16LE(1,20); b.writeUInt16LE(1,22); b.writeUInt32LE(16000,24);
  b.writeUInt32LE(32000,28); b.writeUInt16LE(2,32); b.writeUInt16LE(16,34); b.write('data',36); b.writeUInt32LE(3200,40); return b;
}
(async()=>{
 const browser=await chromium.launch({executablePath:'/usr/bin/chromium',args:['--no-sandbox','--use-fake-device-for-media-stream','--use-fake-ui-for-media-stream']});
 try {
  for(const mobile of [false,true]){
   const context=await browser.newContext(mobile?devices['Pixel 7']:{});
   const page=await context.newPage();debugPage=page;const errors=[];const submissions=[];const playback=[];
   page.on('pageerror',e=>errors.push(String(e)));
   await page.addInitScript(()=>localStorage.setItem('benma.auth.session-token','offline-browser-fixture'));
   let chosen;
   await page.route('**/v1/**',async route=>{
    const req=route.request(), path=new URL(req.url()).pathname;
    const json=data=>route.fulfill({json:data});
    if(path==='/v1/pronunciation-targets'){
     chosen=results.find(r=>r.target.text===req.postDataJSON().text);assert(chosen);return json(chosen.target);
    }
    if(path.endsWith('/reference-speech'))return json({id:'ref',status:'succeeded',audio_url:'/v1/reference-speech/ref/audio',generation_config:{evidence_status:'synthetic_replay'}});
    if(path.endsWith('/audio')){playback.push(path);return route.fulfill({contentType:'audio/wav',body:wav()});}
    if(path==='/v1/utterances')return json({id:chosen.attempt.utterance_id});
    if(path.endsWith('/perceptions'))return json({id:'perception',utterance_id:chosen.attempt.utterance_id,status:'succeeded',transcript:'嘛。',normalized_result:{evidence_status:'live_provider'}});
    if(path==='/v1/pronunciation-attempts'){
     const body=req.postDataJSON();assert.equal(body.target_id,chosen.target.id);submissions.push(body);return json(chosen.attempt);
    }
    if(path.endsWith('/analyze'))return json(chosen);
    if(path.endsWith('/speech-analysis'))return route.fulfill({status:503,json:{detail:'offline fixture'}});
    return route.fulfill({status:404,json:{detail:'unhandled offline route'}});
   });
   const click=async name=>{const b=page.getByRole('button',{name,exact:true}).last();if(mobile)await b.tap();else await b.click();};
   await page.goto(process.env.BENMA_WEB_URL||'http://localhost:8083');await click('Open Practice');await click('Add a target phrase');
   const input=page.getByRole('textbox',{name:'Target phrase',exact:true});
   for(const [index,text] of ['妈','马','骂','嘛'].entries()){
    if(index)await click('Change target');
    await input.fill(text);await click('Prepare target');
    await page.getByRole('button',{name:'▶ Native reference',exact:true}).waitFor();
    await click('Tap to speak');await page.waitForTimeout(300);await click('Stop recording');
    await page.getByText('Experimental pronunciation analysis',{exact:true}).last().waitFor();
    await page.getByLabel(`Expected surface tone ${chosen.syllables[0].expected_surface_tone}`,{exact:true}).last().waitFor();
    await page.waitForTimeout(150);
    if(text==='妈')await page.getByText('Tone 1 ✓',{exact:true}).waitFor();
    if(text==='马'||text==='骂')await page.getByText('Couldn’t judge this one clearly. Try a steady recording.',{exact:true}).last().waitFor();
    if(text==='嘛')await page.getByText('Context-dependent',{exact:true}).last().waitFor();
    await page.getByText('Provider assessment is a development fixture. Tone feedback uses local recording evidence.',{exact:true}).last().waitFor();
    assert.equal(await page.getByText(/Pronunciation accuracy vs target: 79/).count(),0);
    await page.getByLabel('Expected and mine by syllable',{exact:true}).last().scrollIntoViewIfNeeded();
    const plot=page.getByLabel('Relative pitch contour',{exact:true}).last();
    const primaryLines=await plot.getByTestId('contour-line').count();assert(primaryLines>0);
    await page.screenshot({path:`${output}/${mobile?'touch':'mouse'}-${index+1}.png`});
    await click('More detail');await page.getByText('Raw measured pitch',{exact:true}).last().waitFor();
    assert.equal(await page.getByText(/Pronunciation accuracy vs target: 79/).count(),0);
    if(text==='妈'){
     await page.getByText('Boundary evidence excluded: 3 onset / 5 terminal frames',{exact:true}).waitFor();
     const plots=page.getByLabel('Relative pitch contour',{exact:true});
     await plots.nth(1).getByTestId('contour-line').nth(primaryLines).waitFor();
     assert(await plots.nth(1).getByTestId('contour-line').count()>primaryLines);
    }
    assert.equal(await page.getByText(/Measured pitch moved/).count(),0);
    await page.getByText('Raw measured pitch',{exact:true}).last().scrollIntoViewIfNeeded();
    await page.screenshot({path:`${output}/${mobile?'touch':'mouse'}-${index+1}-detail.png`});
    await click('▶ Mine');await page.waitForTimeout(250);await click('Less detail');
    assert(await page.getByText(`Recording for target: ${text} ${chosen.target.display_pinyin}`,{exact:true}).count());
   }
   // Repeated recording retains the neutral target and its actual persisted ID.
   await click('Tap to speak');await page.waitForTimeout(300);
   await Promise.all([page.waitForResponse(r=>r.url().endsWith('/analyze')),click('Stop recording')]);
   await page.getByText('Experimental pronunciation analysis',{exact:true}).last().waitFor();
   assert.equal(submissions.length,5);assert.equal(submissions[4].target_id,submissions[3].target_id);
   assert(playback.length>=4);assert.deepEqual(errors,[]);
   await click('Clear target · use free practice');
   await page.getByText('Free practice: speak without a target phrase.',{exact:true}).waitFor();
   console.log(`${mobile?'touch':'mouse'}: four real persisted results, fixture boundary, raw/details, playback, target persistence PASS`);
   await context.close();
  }
 }catch(e){ if(debugPage) { console.log(await debugPage.locator('body').innerText());await debugPage.screenshot({path:output+'/failure.png'}); }throw e;}finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
