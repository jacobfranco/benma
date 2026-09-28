import { ScrollView, StyleSheet, Text, View } from 'react-native';

import type { PerceivedSyllable } from '@/api/types';
import { ContourLines, PitchPlot } from '@/components/PitchPlot';
import { learnerVerdict, toneGesture } from '@/speech/learnerVerdict';
import { normalizedDisplayContour } from '@/speech/normalizedDisplayContour';
import { learnerGestureContour } from '@/speech/learnerGestureContour';
import { colors } from '@/theme';

export const lexicalShapes: Record<number, number[]> = { 1: [1, 1], 2: [.5, 1], 3: [.25, 0, .75], 4: [1, 0] };
type SyllableFields = Pick<PerceivedSyllable, 'index' | 'characters' | 'pinyin' | 'lexical_tone' |
  'expected_tone' | 'display_contour' | 'observed_contour' | 'start_seconds' | 'end_seconds'>;
export type ComparisonSyllable = Omit<SyllableFields, 'display_contour' | 'observed_contour'> & {
  expected_surface_tone?: number | null | undefined;
  expected_surface_shape?: PerceivedSyllable['expected_tone'] | undefined;
  display_contour?: SyllableFields['display_contour'] | undefined;
  observed_contour?: SyllableFields['observed_contour'] | undefined;
};

// Use only the classifier's selected evidence, never infer a nucleus from spelling.
// The complete display contour and original timestamps remain available in More detail.
export function primaryMineContour(syllable: Pick<ComparisonSyllable, 'display_contour' | 'observed_contour'>) {
  const display = syllable.display_contour;
  const observed = syllable.observed_contour;
  const gesture = learnerGestureContour(display, observed);
  if (gesture !== display) return gesture;
  const selected = observed?.features?.evidence_region_selected === 1;
  if (!display || (!selected && (observed?.reason !== 'sustained_level_after_onset' || observed.classification !== '1-like'))) return display;
  const start = selected ? observed?.features?.evidence_start_seconds : observed?.features?.first_reliable_core_seconds;
  const end = selected ? observed?.features?.evidence_end_seconds : observed?.features?.last_reliable_core_seconds;
  if (!Number.isFinite(start) || !Number.isFinite(end) || start! > end!) return display;
  // Features are rounded to four decimals; include the exact measured boundary.
  const segments = (display.segments ?? []).map(region => region.filter(p =>
    p.timestamp_seconds >= start! - .000051 && (selected ? p.timestamp_seconds < end! - .000051 : p.timestamp_seconds <= end! + .000051))).filter(region => region.length);
  if (!segments.length) return display;
  const values = segments.flat().map(p => p.normalized_semitones);
  return { ...display, segments, minimum_semitones: Math.min(-3, ...values.map(v => v - 1)),
    maximum_semitones: Math.max(3, ...values.map(v => v + 1)) };
}

export function unclearContourLabel(reason?: string): string {
  switch (reason) {
    case 'insufficient_voicing':
    case 'fragmented_voicing': return 'Not enough clear voice';
    case 'tracker_instability': return 'Pitch tracking was unstable';
    case 'noisy_contour': return 'Pitch was uneven';
    case 'low_frequency_contamination': return 'Background sound interfered';
    case 'ambiguous_shape': return 'Shape was ambiguous';
    case 'synthetic_timing': return 'Timing unavailable';
    default: return 'Could not read the pitch';
  }
}

function ExpectedShape({ syllable, normalized = false, extent = 4 }: { syllable: ComparisonSyllable; normalized?: boolean; extent?: number }) {
  const surface = syllable.expected_surface_shape !== undefined;
  const shape = surface ? syllable.expected_surface_shape! : syllable.expected_tone;
  const tone = surface ? syllable.expected_surface_tone : syllable.lexical_tone;
  const heights = shape.map(p => p.height).sort((a,b) => a-b);
  const center = heights.length ? (heights[Math.floor((heights.length-1)/2)]! + heights[Math.floor(heights.length/2)]!)/2 : .5;
  return <View style={[styles.shape, normalized && styles.expectedPlot]} accessibilityLabel={`Expected ${surface ? 'surface' : 'lexical'} tone ${tone ?? 'unresolved'}`}>
    {tone !== 0 && shape.length ? <ContourLines color={colors.reference}
      segments={[shape.map(p => ({ x: p.position*52+4, y: normalized ? 23-(p.height-center)*6/extent*19 : (1-p.height)*32+7, confidence: 1 }))]} /> :
      <Text style={styles.unavailable}>{tone === 0 ? 'Context-dependent' : '?'}</Text>}
  </View>;
}

export function SyllableComparison({ syllables = [], loading = false, heard = '', gradeTarget = false }: {
  gradeTarget?: boolean; syllables?: ComparisonSyllable[]; loading?: boolean; heard?: string;
}) {
  return <ScrollView horizontal showsHorizontalScrollIndicator accessibilityLabel="Expected and mine by syllable"
    style={[styles.scroll, gradeTarget && { height: 214 }]} contentContainerStyle={styles.row}>
    {loading ? Array.from(heard.match(/[\u3400-\u4dbf\u4e00-\u9fff]/g) ?? ['·', '·', '·']).map((character, index) =>
      <View key={index} style={styles.cell} testID="syllable-skeleton">
        <Text style={styles.character}>{character}</Text>
        <View style={styles.skeletonText} />
        <View style={styles.pair}>{['Expected', 'Mine'].map(label => <View key={label} style={styles.half}>
          <Text style={styles.caption}>{label}</Text><View style={styles.skeletonShape} />
          <View style={styles.skeletonText} />
        </View>)}</View>
      </View>) : syllables.map(syllable => {
        const observed = syllable.observed_contour?.classification ?? 'unclear';
        const surface = syllable.expected_surface_shape !== undefined;
        const tone = surface ? syllable.expected_surface_tone : syllable.lexical_tone;
        const verdict = learnerVerdict(tone, syllable.observed_contour);
        const neutral = tone === 0;
        const mine = gradeTarget ? normalizedDisplayContour(primaryMineContour(syllable), syllable.observed_contour) : primaryMineContour(syllable);
        return <View key={syllable.index} style={[styles.cell, gradeTarget && { height: 204 }]} testID={`syllable-${syllable.index}`}>
          <View style={styles.heading}><Text style={styles.character}>{syllable.characters}</Text>
            <Text style={styles.pinyin}>{syllable.pinyin ?? '?'}</Text></View>
          <View style={styles.pair}>
            <View style={styles.half}><Text style={styles.caption}>{tone === 0 ? 'Expected pitch' : surface ? 'Expected here' : 'Dictionary'}</Text>
              <ExpectedShape syllable={syllable} normalized={gradeTarget} extent={mine?.maximum_semitones ?? 4} />
              <Text style={styles.expected}>{tone === 0 ? 'Neutral tone' : `Tone ${tone ?? '?'}`}</Text>
            </View>
            <View style={styles.half}><Text style={styles.caption}>Mine · broad pitch</Text>
              {syllable.display_contour?.segments?.length ? <PitchPlot compact fitVoiced user={[]} fixedDisplayDomain={gradeTarget} display={mine}
                startSeconds={syllable.start_seconds ?? 0} durationSeconds={syllable.end_seconds ?? 0} /> :
                <View style={styles.shape}><Text style={styles.unavailable}>—</Text></View>}
              <Text style={styles.mine}>{gradeTarget && !neutral ? verdict === 'matches' ? `Tone ${tone} ✓` : verdict === 'close' ? 'Close' : verdict === 'different' ? `Tone ${observed.replace('-like', '')}` : 'Unclear' : observed === 'unclear' ? 'Unclear' : observed === 'neutral-like' ? 'Neutral-like' : `Tone ${observed}`}</Text>
            </View>
          </View>
          <Text numberOfLines={gradeTarget ? 3 : 2} style={styles.note}>{gradeTarget ? neutral ? 'Context-dependent pitch' : verdict === 'matches' ? `Good · ${toneGesture[tone!]}` : verdict === 'close' ? 'Compatible shape; limited evidence' : verdict === 'different' ? `Expected Tone ${tone}. Yours sounded more like Tone ${observed.replace('-like', '')}` : `${unclearContourLabel(syllable.observed_contour?.reason)}. No confident tone judgment.` : syllable.pinyin === null ? 'Reading unresolved' :
            !syllable.display_contour ? 'Timing unavailable' : observed === 'unclear' ? unclearContourLabel(syllable.observed_contour?.reason) : syllable.observed_contour?.confidence === 'low' ? 'Tentative shape · low confidence' : 'Approximate shape'}</Text>
        </View>;
      })}
  </ScrollView>;
}
const styles = StyleSheet.create({
  scroll: { flexGrow: 0, height: 198 },
  row: { gap: 8, paddingBottom: 8 },
  cell: { width: 154, height: 188, padding: 10, borderRadius: 12, borderWidth: StyleSheet.hairlineWidth,
    borderColor: colors.border, backgroundColor: colors.plotBackground, gap: 8 },
  heading: { flexDirection: 'row', gap: 8, alignItems: 'baseline', height: 32 },
  character: { fontSize: 24, lineHeight: 32, color: colors.text },
  pinyin: { fontSize: 16, color: colors.text },
  pair: { flexDirection: 'row', gap: 10 },
  half: { width: 60, gap: 3 },
  caption: { color: colors.secondary, fontSize: 11, height: 28 },
  expected: { color: colors.reference, fontSize: 11, fontWeight: '600' },
  mine: { color: colors.primary, fontSize: 11, fontWeight: '600' },
  shape: { width: 60, height: 46, position: 'relative', justifyContent: 'center', alignItems: 'center' },
  expectedPlot: { borderWidth: StyleSheet.hairlineWidth, borderColor: colors.border, borderRadius: 8, overflow: 'hidden' },
  unavailable: { color: colors.secondary, fontSize: 11, textAlign: 'center' },
  note: { color: colors.secondary, fontSize: 10, lineHeight: 14 },
  skeletonText: { width: 42, height: 10, borderRadius: 4, backgroundColor: colors.plotGrid },
  skeletonShape: { width: 60, height: 42, marginVertical: 4, borderRadius: 6, backgroundColor: colors.plotGrid },
});
