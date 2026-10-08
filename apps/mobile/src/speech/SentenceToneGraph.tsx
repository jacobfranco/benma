import { useEffect, useRef, useState } from 'react';
import { Pressable, ScrollView, StyleSheet, Text, useWindowDimensions, View } from 'react-native';

import type { PerceivedSpeechAnalysis } from '@/api/types';
import { PitchPlot } from '@/components/PitchPlot';
import { expectedLabel, graphWidth, hasTiming, normalizedMine, rawPitch, toneName, toneReference, timingGroups, timingGroupFor } from '@/speech/sentenceToneGraph';
import { colors } from '@/theme';
import { gestureLabel, toneGestureMatch } from '@/speech/toneGestureMatch';

export function SentenceToneGraph({ data }: { data: PerceivedSpeechAnalysis['data'] }) {
  const scroll = useRef<ScrollView>(null);
  useEffect(() => {
    scroll.current?.scrollTo({ x: 0, y: 0, animated: false });
  }, [data]);
  const [detail, setDetail] = useState(false);
  const [raw, setRaw] = useState(false);
  const [layoutWidth, setLayoutWidth] = useState(0);
  const [selectedUnit, setSelectedUnit] = useState<number | null>(null);
  const windowWidth = useWindowDimensions().width;
  const viewport = layoutWidth || Math.max(240, windowWidth - 100);
  // Synthetic equal partitions are never presented as perceived speech boundaries.
  const timed = data.alignment_status === 'synthetic' ? [] : data.syllables.filter(hasTiming);
  const groups = timingGroups(data);
  const spans = [...timed, ...groups];
  const untimed = data.syllables.filter(s => !timed.includes(s as typeof timed[number]) && !timingGroupFor(data, s));
  const graph = data.tone_graph;
  const contour = detail ? graph?.filtered ?? data.display_contour : graph?.mine ?? data.display_contour;
  const evidenceTimes = (graph?.filtered ?? data.display_contour)?.segments?.flat().map(p => p.timestamp_seconds) ?? [];
  // Trim only empty recording margins when timing exists; coordinates remain seconds.
  // Every selected measurement and every timed unit stays inside the shared domain.
  const start = spans.length ? Math.min(...spans.map(s => s.start_seconds), ...evidenceTimes) : 0;
  const end = spans.length ? Math.max(...spans.map(s => s.end_seconds), ...evidenceTimes) : data.duration_seconds;
  const duration = Math.max(end, start + .001);
  const shortest = timed.length ? Math.min(...timed.map(s => s.end_seconds - s.start_seconds)) : undefined;
  const normalized = normalizedMine(data);
  // Fit whole cells at the initial viewport edge. Long strips snap to a cell start.
  const cellWidth = (viewport - 8) / Math.max(1, Math.floor((viewport - 8) / 96));
  const width = detail ? graphWidth(viewport, duration - start, data.syllables.length, shortest) : Math.max(viewport, normalized.extent * cellWidth + 8);
  const snapOffsets = [...normalized.regions.map(r => r.start * cellWidth), width - viewport]
    .filter(offset => offset >= 0 && offset <= width - viewport).sort((a, b) => a - b);
  const tracker = rawPitch(data);
  const regions = [...timed.map(s => ({ label: s.characters, start_seconds: s.start_seconds, end_seconds: s.end_seconds })),
    ...groups.map(g => ({ label: g.text, start_seconds: g.start_seconds, end_seconds: g.end_seconds }))];
  const cells = detail ? timed : data.syllables;
  const selected = data.syllables.find(s => s.index === selectedUnit);
  const selectedGroup = selected && timingGroupFor(data, selected);
  const selectedFeedback = selected && toneGestureMatch(selected, data.alignment_status !== 'synthetic' && !selectedGroup);
  const box = (left: number, right: number) => ({ left: 4 + left / normalized.extent * (width - 8), width: (right - left) / normalized.extent * (width - 8) });
  return <View style={styles.container} onLayout={event => setLayoutWidth(event.nativeEvent.layout.width)}>
    <Text style={styles.title}>Your pitch</Text>
    {detail && <Text style={styles.caption}>Real recording time. Gaps mean missing pitch; height is relative to this recording.</Text>}
    <ScrollView key={detail ? 'detail' : 'mine'} ref={scroll} horizontal accessibilityLabel="Sentence pitch timeline" style={{ maxWidth: '100%' }}
      snapToOffsets={detail ? undefined : snapOffsets} decelerationRate="fast">
      <View style={{ width }}>
        {!detail && normalized.evidenceRegions?.map(region => {
          const syllable = data.syllables.find(s => s.index === region.index);
          const grouped = groups.some(g => g.character_start === syllable?.character_start);
          const state = syllable && !grouped ? toneGestureMatch(syllable, data.alignment_status !== 'synthetic').comparison : 'uncertain';
          return <View key={region.start} testID={`tone-cell-state-${syllable?.index}`} pointerEvents="none"
            accessibilityValue={{ text: grouped ? 'grouped_evidence' : state }}
            style={[styles.cellState, styles[state], box(region.start, region.end), grouped && styles.grouped]} />;
        })}
        <PitchPlot user={[]} display={contour ?? { segments: [] }} regions={regions}
          durationSeconds={duration} startSeconds={start} showPoints={detail} xLayout={detail ? undefined : normalized}
          transparent={!detail} showRegionLabels={false} showMineLabel={false} showAxes={detail} showEmptyLabel={detail} />
        {detail && <Text style={styles.caption}>{start.toFixed(2)}–{duration.toFixed(2)} s · real recording time</Text>}
        <View style={{ height: detail ? 110 : 92 }}>
          {cells.map((s, i) => <Pressable key={s.index} testID={`character-unit-${s.index}`} accessibilityRole="button" onPress={() => setSelectedUnit(s.index)}
            accessibilityLabel={`${s.characters}, tone gesture ${toneGestureMatch(s, data.alignment_status !== 'synthetic' && !timingGroupFor(data, s)).comparison}${timingGroupFor(data, s) ? ', grouped word pitch, no individual attribution' : ''}, pitch measurements and reference details`}
            style={[styles.unit, { left: 4 + (detail && hasTiming(s) ? (s.start_seconds - start) / (duration - start) : normalized.regions[i]!.start / normalized.extent) * (width - 8),
              width: (detail && hasTiming(s) ? (s.end_seconds - s.start_seconds) / (duration - start) : 1 / normalized.extent) * (width - 8) }]}>
            <Text style={styles.character}>{s.characters}</Text>
            {detail && hasTiming(s) && <Text style={styles.caption}>{s.start_seconds.toFixed(2)}–{s.end_seconds.toFixed(2)} s</Text>}
          </Pressable>)}
          {detail && groups.map(group => <Pressable key={group.character_start} testID={`timing-group-${group.character_start}`}
            accessibilityRole="button" accessibilityLabel={`${group.text}, grouped word pitch, tone gesture uncertain`}
            onPress={() => setSelectedUnit(data.syllables.find(s => s.character_start === group.character_start)!.index)}
            style={[styles.unit, { left: 4 + (group.start_seconds - start) / (duration - start) * (width - 8),
              width: (group.end_seconds - group.start_seconds) / (duration - start) * (width - 8) }]}>
            <Text style={styles.character}>{group.text}</Text>
            <Text style={styles.caption}>{group.start_seconds.toFixed(2)}–{group.end_seconds.toFixed(2)} s · grouped pitch</Text>
          </Pressable>)}
        </View>
      </View>
    </ScrollView>

    {selected && <View style={styles.untimed}>
      <Text style={styles.character}>{selected.characters} · {selected.pinyin ?? 'Reading unresolved'}</Text>
      <Text style={styles.caption}>{selected.pitch_eligibility?.state === 'unstable'
        ? 'Pitch tracking: Uncertain'
        : `Observed pitch: ${selected.pitch_eligibility?.state === 'incomplete' ? 'Incomplete evidence' : gestureLabel[selectedFeedback!.observed_gesture]}`}</Text>
      <Text style={styles.caption}>Observed confidence: {selectedFeedback!.observed_confidence}</Text>
      <Text style={styles.caption}>Tone gesture: {selectedFeedback!.comparison}</Text>
      <Text style={styles.expected}>Lexical tone: {selected.lexical_tone == null || selected.reading_source === 'unresolved' ? 'Unresolved' : toneName(selected.lexical_tone)}</Text>
      <Text style={styles.expected}>{toneReference(selected).lexicalFallback ? 'Reference tone: unresolved · Contextual realization: unresolved' : selectedFeedback!.reference_tone == null ? 'Reference tone: unresolved' : `${expectedLabel(selected)}${selectedFeedback!.reference_tone === 1 ? ' (level-like)' : selectedFeedback!.reference_tone === 2 ? ' (rising)' : selectedFeedback!.reference_tone === 4 ? ' (falling)' : ''}`}</Text>
      <Text style={styles.caption}>Reference pronunciation. Pitch gestures are experimental; tone comparison remains uncertain.</Text>
      {selectedFeedback!.reference_tone === 3 && <Text style={styles.caption}>Connected T3 can be low or dipping; its exact realization is unresolved.</Text>}
      {selectedFeedback!.reference_tone === 0 && <Text style={styles.caption}>Neutral tone has no fixed pitch shape.</Text>}
      {selectedGroup && <Text style={styles.caption}>{selectedGroup.text} · grouped word pitch · {selectedGroup.start_seconds.toFixed(2)}–{selectedGroup.end_seconds.toFixed(2)} s. Pitch is measured across this word; individual character timing is unavailable. No individual tone comparison.</Text>}
      <Text style={styles.caption}>{timed.includes(selected as typeof timed[number]) && hasTiming(selected) ? `${selected.start_seconds.toFixed(2)}–${selected.end_seconds.toFixed(2)} s · Pitch evidence: ${selected.pitch_eligibility?.state ?? 'unavailable'}` : selectedGroup ? 'Word timing available; character timing unavailable' : 'Timing unavailable'}</Text>
    </View>}
    {detail && untimed.length > 0 && <View style={styles.untimed}>
      <Text style={styles.caption}>Syllable timing is unavailable for:</Text>
      {untimed.map(s => <Text key={s.index} style={styles.caption}>{s.characters} · {s.pinyin ?? 'Reading unresolved'} · {expectedLabel(s)}</Text>)}
    </View>}
    {detail && <Text style={styles.caption}>Pitch evidence describes available measurements. Reference pronunciation is in character details. Mine uses equal character widths; ‖ marks a pause of at least 0.30 s.</Text>}
    <Pressable accessibilityRole="button" accessibilityLabel={detail ? 'Less detail' : 'More detail'}
      accessibilityState={{ expanded: detail }} onPress={() => { setDetail(!detail); setRaw(false); }}>
      <Text style={styles.link}>{detail ? 'Less detail' : 'More detail'}</Text>
    </Pressable>
    {detail && <View style={styles.container}>
      {(data.unresolved_spans ?? []).map((span, index) => <Text key={index} style={styles.caption}>{String(span.text)} · reading unresolved</Text>)}
      <Text style={styles.caption}>{graph ? 'Filtered F0 samples over real time. Dots are retained measurements; lines stop at missing evidence and syllable boundaries.' : 'This saved analysis has only a simplified contour. Record again for full pitch detail.'}</Text>
      <Pressable accessibilityRole="button" accessibilityLabel={raw ? 'Hide raw' : 'Raw'}
        accessibilityState={{ expanded: raw }} onPress={() => setRaw(!raw)}><Text style={styles.link}>{raw ? 'Hide raw' : 'Raw'}</Text></Pressable>
      {raw && <>
        <Text style={styles.caption}>Raw tracker evidence · developer detail</Text>
        {graph ? <>
          <Text style={styles.caption}>Teal: retained timestamps. Gray: excluded timestamps. Tracker Hz before energy gating where available; otherwise stored F0. No lines connect raw points.</Text>
          <ScrollView horizontal accessibilityLabel="Raw pitch timeline"><View style={{ width }}>
            <PitchPlot user={tracker.retained} rejected={tracker.rejected} pointsOnly regions={regions} durationSeconds={data.duration_seconds} />
          </View></ScrollView>
          <Text style={styles.caption}>Exclusion reasons: {[...new Set(graph.raw.flatMap(p => p.exclusion_reasons ?? []))].join(', ') || 'Unavailable in this saved analysis'}</Text>
          <Text style={styles.caption}>{graph.raw.filter(p => p.retained).length} retained / {graph.raw.length} frames · {graph.raw.filter(p => p.tracker_f0_hz == null && p.f0_hz == null).length} missing</Text>
        </> : <Text style={styles.caption}>Raw tracker evidence unavailable for this saved analysis.</Text>}
      </>}
    </View>}
  </View>;
}
const styles = StyleSheet.create({
  container: { gap: 8 }, title: { color: colors.primary, fontSize: 14, fontWeight: '600' },
  caption: { color: colors.secondary, fontSize: 11, lineHeight: 16 },
  expected: { color: colors.reference, fontSize: 11, lineHeight: 16 },
  character: { color: colors.text, fontSize: 34, lineHeight: 44, textAlign: 'center' },
  cellState: { position: 'absolute', top: 0, bottom: 0, borderRadius: 6 },
  consistent: { backgroundColor: 'rgba(18,100,92,0.10)' },
  different: { backgroundColor: colors.warningBackground },
  uncertain: { backgroundColor: colors.plotBackground },
  grouped: { borderColor: colors.border, borderWidth: 1 },
  unit: { alignItems: 'center', position: 'absolute', paddingHorizontal: 3, borderLeftWidth: StyleSheet.hairlineWidth, borderColor: colors.border },
  untimed: { gap: 3 }, link: { color: colors.primary, fontSize: 13, paddingVertical: 6 },
});
