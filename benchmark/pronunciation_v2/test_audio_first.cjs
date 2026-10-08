const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const {cards,playbackBounds,SegmentPlayer}=require('./audio_first_model.cjs');
const rows=JSON.parse(fs.readFileSync('services/api/var/audio-first-feedback/viewer-data.json')).recordings;
const clone=x=>JSON.parse(JSON.stringify(x));

test('six frozen takes: individual, whole group, no fabricated timing, source immutable',()=>{
  const before=JSON.stringify(rows);
  assert.deepEqual(rows.map(r=>cards(r.data).length),[6,6,0,6,6,6]);
  const primary=cards(rows[0].data);
  assert.deepEqual(primary.map(c=>c.text),['我','想','买','五','把','雨伞']);
  assert.deepEqual(primary.filter(c=>c.grouped).map(c=>[c.text,c.start_seconds,c.end_seconds]),[['雨伞',3.56,4.87]]);
  assert.equal(primary[5].playback_label,'Play exact recording for 雨伞');
  assert.equal(primary[5].context_playback_label,'Play recording with context for 雨伞');
  assert.equal(primary[5].reading,'yǔ sǎn');
  assert.equal(primary[4].reading,null);
  assert.equal(JSON.stringify(rows),before);
});
test('synthetic, wrong evidence identity, invalid duration and conflicting groups fail closed',()=>{
  for(const key of ['alignment_status','evidence_status']) {
    const d=clone(rows[0].data);d[key]=key==='alignment_status'?'synthetic':'synthetic_replay';assert.equal(cards(d).length,0);
  }
  const d=clone(rows[0].data);d.syllables[0].timing_evidence_id='other';
  d.syllables[1].end_seconds=d.duration_seconds+1;
  d.timing_groups.push(clone(d.timing_groups[0]));
  assert.deepEqual(cards(d).map(c=>c.text),['买','五','把']);
});
test('timing and listening remain available without pitch or resolved reading',()=>{
  const d=clone(rows[0].data);d.pitch_track_evidence_id=null;d.tone_graph=null;
  const result=cards(d);assert.equal(result.length,6);
  assert(result.every(c=>c.status==='Pitch evidence unavailable' && c.observed===null));
  assert.equal(result[4].text,'把');assert.equal(result[4].reading,null);
});
test('states are evidence language; low confidence and ineligible gestures are conservative',()=>{
  for(const [state,wording] of Object.entries({sufficient:'Pitch evidence available',incomplete:'Pitch evidence incomplete',unstable:'Pitch evidence unstable',insufficient:'Not enough pitch evidence'})) {
    const d=clone(rows[1].data),s=d.syllables[0];s.pitch_eligibility.state=state;s.observed_gesture='rising';s.observed_confidence='moderate';
    const c=cards(d)[0];assert.equal(c.status,wording);assert.equal(c.observed,state==='sufficient'?'Rising (tentative)':null);
  }
  assert.equal(cards(rows[0].data)[0].observed,'Unclear');
  assert.equal(cards(rows[0].data)[5].observed,null);
  assert(!JSON.stringify(rows.flatMap(r=>cards(r.data))).match(/correct|incorrect|good tone|bad tone|detected Tone|wrong pronunciation/));
});
test('广州 target versus 贵州 perceived identity, timing, measurements and gestures',()=>{
  // Explicit synthetic presentation regression, separate from the six physical takes.
  const d=clone(rows[4].data);d.syllables=d.syllables.slice(0,2);d.syllables[0].characters='贵';d.syllables[1].characters='州';
  const before=JSON.stringify(d),base=cards(d);
  for(const target of ['广州','贵州','上海']) {
    const result=cards({...d,intended_text:target,target:{text:target}});
    assert.deepEqual(result,base);assert.deepEqual(result.map(c=>c.text),['贵','州']);
  }
  assert.equal(JSON.stringify(d),before);
});
test('padding only affects playback bounds, clamped to decoded duration',()=>{
  for(const r of rows)for(const c of cards(r.data))for(const pad of [0,40,80]) {
    const before=JSON.stringify(c),b=playbackBounds(c.start_seconds,c.end_seconds,r.duration_seconds,pad);
    assert.equal(b.accepted_start_seconds,c.start_seconds);assert.equal(b.accepted_end_seconds,c.end_seconds);
    assert.equal(b.start_seconds,Math.max(0,c.start_seconds-pad/1000));
    assert.equal(b.end_seconds,Math.min(r.duration_seconds,c.end_seconds+pad/1000));
    assert.equal(JSON.stringify(c),before);
  }
  assert.equal(playbackBounds(0.01,1.5,1.4,80).end_seconds,1.4);
  assert.equal(playbackBounds(0.01,0.1,1,80).start_seconds,0);
  for(const args of [[0,0,1],[1,2,0.9],[0,1,NaN],[NaN,1,1],[0,1,1,100]])assert.throws(()=>playbackBounds(...args));
});
function harness(decode) {
  const sources=[],states=[];
  const ctx={destination:{},resume:async()=>{},close:async()=>{ctx.closed=true;},createBufferSource:()=>{
    const s={connect(){},disconnect(){s.disconnected=true;},start(...args){s.args=args;},stop(){s.stopped=true;}};sources.push(s);return s;
  }};
  const player=new SegmentPlayer(()=>ctx,decode??(async()=>({duration:1})),s=>states.push(s));
  return {player,ctx,sources,states};
}
test('one full-buffer cache; repeat taps stop/disconnect prior source; exact offset/duration',async()=>{
  let decodes=0;const h=harness(async()=>{decodes++;return {duration:1};});
  const unit={key:'unit',start_seconds:0.2,end_seconds:0.6};
  const bound=await h.player.play({id:'a'},unit,40);assert.equal(bound.start_seconds,0.16);
  assert.deepEqual(h.sources[0].args,[0,0.16,0.48]);
  await h.player.play({id:'a'},unit);assert.equal(decodes,1);assert(h.sources[0].stopped&&h.sources[0].disconnected);
  h.sources[1].onended();assert.equal(h.player.source,null);assert(h.sources[1].disconnected);
  await h.player.dispose();assert(h.ctx.closed);assert.equal(h.player.cache.size,0);
});
test('rapid taps, stopping and disposal invalidate asynchronous loads',async()=>{
  let resolve;const h=harness(()=>new Promise(r=>{resolve=r;}));
  const unit={key:'u',start_seconds:0.2,end_seconds:0.5};
  const first=h.player.play({id:'a'},unit);const second=h.player.play({id:'a'},unit);
  await Promise.resolve();resolve({duration:1});assert.equal(await first,null);assert(await second);assert.equal(h.sources.length,1);
  h.player.stop();assert(h.sources[0].stopped);
  let finish;const pendingHarness=harness(()=>new Promise(r=>{finish=r;}));
  const pending=pendingHarness.player.play({id:'b'},unit);await Promise.resolve();await pendingHarness.player.dispose();finish({duration:1});
  assert.equal(await pending,null);assert.equal(pendingHarness.sources.length,0);
});
test('decode failure is retryable; whole playback uses actual decoded duration',async()=>{
  let n=0;const h=harness(async()=>{if(!n++)throw Error('bad decode');return {duration:1.25};});
  assert.equal(await h.player.play({id:'a'},null),null);assert.equal(h.states.at(-1).state,'error');
  assert.equal((await h.player.play({id:'a'},null)).end_seconds,1.25);assert.deepEqual(h.sources[0].args,[0,0,1.25]);
  await h.player.dispose();
});

test('exact and context actions preserve all 30 units, use only 40/80 ms, and cancel each other',async()=>{
  const before=JSON.stringify(rows);
  for(const r of rows)for(const unit of cards(r.data)) {
    const h=harness(async()=>({duration:r.duration_seconds}));
    for(const pad of [40,80]) {
      const exact=await h.player.playExact(r,unit);
      assert.equal(exact.start_seconds,unit.start_seconds);
      assert.equal(exact.end_seconds,unit.end_seconds);
      assert.equal(exact.padding_ms,0);
      assert.equal(h.states.at(-1).action,'exact');
      const old=h.player.source;
      const context=await h.player.playWithContext(r,unit,pad);
      assert(old.stopped && old.disconnected);assert.equal(old.onended,null);
      assert.equal(context.padding_ms,pad);
      assert.equal(context.start_seconds,Math.max(0,unit.start_seconds-pad/1000));
      assert.equal(context.end_seconds,Math.min(r.duration_seconds,unit.end_seconds+pad/1000));
      assert.equal(h.states.at(-1).action,'context');
      const previous=h.player.source;
      await h.player.playExact(r,unit);
      assert(previous.stopped && previous.disconnected);assert.equal(previous.onended,null);
    }
    for(const pad of [0,120,NaN,undefined])assert.throws(()=>h.player.playWithContext(r,unit,pad));
    assert.throws(()=>h.player.playWithContext(r,null,40));
    await h.player.dispose();
  }
  assert.equal(JSON.stringify(rows),before);
});
test('rapid mixed actions across cards/takes cannot revive stale loads or end listeners',async()=>{
  const pending={};
  const h=harness((ctx,r)=>new Promise(resolve=>{pending[r.id]=resolve;}));
  const first=cards(rows[0].data)[0],group=cards(rows[0].data).at(-1);
  const a=h.player.playExact(rows[0],first);
  const b=h.player.playWithContext(rows[0],group,40);
  const c=h.player.playExact(rows[1],cards(rows[1].data)[0]);
  await Promise.resolve();
  pending[rows[1].id]({duration:rows[1].duration_seconds});
  assert(await c);
  pending[rows[0].id]({duration:rows[0].duration_seconds});
  assert.equal(await a,null);assert.equal(await b,null);
  assert.equal(h.sources.length,1);assert.equal(h.states.at(-1).action,'exact');
  const staleEnd=h.sources[0].onended;
  await h.player.playWithContext(rows[0],group,80);
  const active=h.player.source;staleEnd();
  assert.equal(h.player.source,active);assert.equal(h.states.at(-1).action,'context');
  await h.player.dispose();
  assert(active.stopped && active.disconnected);assert.equal(active.onended,null);
  const count=h.states.length;
  assert.equal(await h.player.playExact(rows[0],first),null);
  assert.equal(h.states.length,count);
});
