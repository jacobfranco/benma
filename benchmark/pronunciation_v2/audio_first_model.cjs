/* Research presentation only. No classifier, target comparison, or F0 selection. */
(function (root) {
  const contextCandidatesMs = Object.freeze([40, 80]);
  const statusLabels = {
    sufficient: 'Pitch evidence available', incomplete: 'Pitch evidence incomplete',
    unstable: 'Pitch evidence unstable', insufficient: 'Not enough pitch evidence',
  };
  const gestures = {level: 'Level-like', rising: 'Rising', dipping: 'Dipping / valley-like', falling: 'Falling'};
  const trustedReading = s => s.reading_source !== 'unresolved' && s.resolution_confidence === 'high' && !!s.pinyin;
  function reference(s) {
    if (!trustedReading(s) || s.lexical_tone == null) return `${s.characters}: Reading unresolved`;
    const tone = t => t === 0 ? 'Neutral' : `T${t}`;
    return `${s.characters} · ${s.pinyin} · ${s.expected_surface_tone == null
      ? `Lexical ${tone(s.lexical_tone)}; contextual reference unresolved`
      : `Reference tone: ${tone(s.expected_surface_tone)}`}`;
  }
  function cards(data) {
    if (!['aligned', 'partial'].includes(data.alignment_status) || data.evidence_status === 'synthetic_replay') return [];
    const valid = s => {
      return Number.isFinite(s.start_seconds) && Number.isFinite(s.end_seconds) &&
        0 <= s.start_seconds && s.start_seconds < s.end_seconds && s.end_seconds <= data.duration_seconds &&
        ['azure_provider_grapheme', 'azure_word'].includes(s.timing_source ?? s.source) &&
        !!s.timing_evidence_id && s.timing_evidence_id === data.timing_evidence_id;
    };
    const units = data.syllables.filter(valid).map(s => ({source:s, members:[s], grouped:false}));
    for (const g of data.timing_groups ?? []) {
      const members = data.syllables.filter(s => s.character_start >= g.character_start && s.character_end <= g.character_end);
      if (!valid(g) || members.length < 2 || members.some(s => s.start_seconds != null || s.end_seconds != null) ||
          members[0].character_start !== g.character_start || members.at(-1).character_end !== g.character_end ||
          members.some((s, i) => i && members[i-1].character_end !== s.character_start) ||
          members.map(s => s.characters).join('') !== g.text) continue;
      units.push({source:g, members, grouped:true});
    }
    // Reject conflicting identities rather than duplicate a group or invent ownership.
    return units.filter(u => !units.some(v => v !== u &&
      u.source.character_start < v.source.character_end && v.source.character_start < u.source.character_end))
      .sort((a,b) => a.source.character_start - b.source.character_start).map(({source:s,members,grouped}) => {
        // Timing can support listening even when pitch evidence is entirely absent.
        // Only acoustic labels depend on the projection's identity and bounds.
        const p=s.pitch_projection;
        const bound=!!p && !!data.pitch_track_evidence_id && p.track_evidence_id===data.pitch_track_evidence_id &&
          p.start_seconds===s.start_seconds && p.end_seconds===s.end_seconds && p.timing_evidence_id===s.timing_evidence_id;
        const state = bound ? s.pitch_eligibility?.state ?? 'unavailable' : 'unavailable';
        const observed = !grouped && state === 'sufficient'
          ? s.observed_confidence === 'moderate' && gestures[s.observed_gesture]
            ? `${gestures[s.observed_gesture]} (tentative)` : 'Unclear'
          : null;
        return {
          key: `${s.character_start}:${s.character_end}`, text: grouped ? s.text : s.characters,
          character_start:s.character_start, character_end:s.character_end, grouped,
          reading: members.every(trustedReading) ? members.map(s => s.pinyin).join(' ') : null,
          start_seconds:s.start_seconds, end_seconds:s.end_seconds,
          state, status:statusLabels[state] ?? 'Pitch evidence unavailable', observed,
          references:members.map(reference), timing_source:s.timing_source ?? s.source,
          playback_label:`Play exact recording for ${grouped ? s.text : s.characters}`,
          context_playback_label:`Play recording with context for ${grouped ? s.text : s.characters}`,
        };
      });
  }
  function playbackBounds(start, end, duration, paddingMs = 0) {
    if (![start,end,duration,paddingMs].every(Number.isFinite) || start < 0 || end <= start || duration <= 0 ||
        !(paddingMs === 0 || contextCandidatesMs.includes(paddingMs))) throw Error('Playback timing unavailable');
    const playbackStart = Math.max(0, Math.min(duration, start - paddingMs / 1000));
    const playbackEnd = Math.max(0, Math.min(duration, end + paddingMs / 1000));
    if (playbackStart >= playbackEnd || start >= duration) throw Error('Playback timing outside recording');
    return {accepted_start_seconds:start, accepted_end_seconds:end, start_seconds:playbackStart, end_seconds:playbackEnd, padding_ms:paddingMs};
  }
  // A fresh source per tap, one decoded full recording per take. Audio-clock duration
  // avoids a timeupdate/setTimeout stop, which can overrun on backgrounded tabs.
  class SegmentPlayer {
    constructor(contextFactory, decode, onState = () => {}) {
      this.contextFactory=contextFactory; this.decode=decode; this.onState=onState;
      this.context=null; this.source=null; this.cache=new Map(); this.operation=0; this.closed=false;
    }
    stop() {
      this.operation++;
      if (this.source) { this.source.onended=null; this.source.stop(); this.source.disconnect(); this.source=null; }
      this.onState({state:'idle'});
    }
    playExact(recording, unit) { return this.play(recording, unit, 0); }
    playWithContext(recording, unit, paddingMs) {
      if (!unit || !contextCandidatesMs.includes(paddingMs)) throw Error('Choose a context listening candidate');
      return this.play(recording, unit, paddingMs);
    }
    async play(recording, unit, paddingMs=0) {
      if (this.closed) return null;
      this.stop();
      const operation=this.operation;
      const action=unit ? paddingMs ? 'context' : 'exact' : 'whole';
      this.onState({state:'loading', key:unit?.key ?? 'whole', action});
      try {
        this.context ??= this.contextFactory();
        // Resume in the explicit tap handler before any decoding await.
        const resume=this.context.resume();
        let pending=this.cache.get(recording.id);
        if (!pending) {
          pending=Promise.resolve().then(() => this.decode(this.context,recording));
          this.cache.set(recording.id,pending);
          pending.catch(() => { if(this.cache.get(recording.id)===pending)this.cache.delete(recording.id); });
        }
        const [,buffer]=await Promise.all([resume,pending]);
        if (this.closed || operation !== this.operation) return null;
        const bounds=playbackBounds(unit?.start_seconds ?? 0,unit?.end_seconds ?? buffer.duration,buffer.duration,unit ? paddingMs : 0);
        const source=this.context.createBufferSource(); this.source=source;
        source.buffer=buffer; source.connect(this.context.destination);
        source.onended=() => {
          source.disconnect();
          if (this.source===source) {this.source=null; this.onState({state:'idle'});}
        };
        source.start(0,bounds.start_seconds,bounds.end_seconds-bounds.start_seconds);
        this.onState({state:'playing',key:unit?.key ?? 'whole',action,bounds});
        return bounds;
      } catch (error) {
        if (operation===this.operation && !this.closed) {this.stop();this.onState({state:'error',message:'Recording audio unavailable. Try again.'});}
        return null;
      }
    }
    async dispose() {if(this.closed)return;this.closed=true;this.stop();this.cache.clear();if(this.context)await this.context.close();}
  }
  const api={cards,playbackBounds,SegmentPlayer,statusLabels};
  if(typeof module !== 'undefined')module.exports=api;
  else root.AudioFirst=api;
})(globalThis);
