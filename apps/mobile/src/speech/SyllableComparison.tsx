import { ScrollView, StyleSheet, Text, View } from 'react-native';

import type { PerceivedSyllable } from '@/api/types';
import { ContourLines, PitchPlot } from '@/components/PitchPlot';
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

function ExpectedShape({ syllable }: { syllable: ComparisonSyllable }) {
  const surface = syllable.expected_surface_shape !== undefined;
  const shape = surface ? syllable.expected_surface_shape! : syllable.expected_tone;
  const tone = surface ? syllable.expected_surface_tone : syllable.lexical_tone;
  return <View style={styles.shape} accessibilityLabel={`Expected ${surface ? 'surface' : 'lexical'} tone ${tone ?? 'unresolved'}`}>
    {shape.length ? <ContourLines color={colors.reference}
      segments={[shape.map(p => ({ x: p.position*48+5, y: (1-p.height)*32+7, confidence: 1 }))]} /> :
      <Text style={styles.unavailable}>{tone === 0 ? 'varies' : '?'}</Text>}
  </View>;
}

export function SyllableComparison({ syllables = [], loading = false, heard = '' }: {
  syllables?: ComparisonSyllable[]; loading?: boolean; heard?: string;
}) {
  return <ScrollView horizontal showsHorizontalScrollIndicator accessibilityLabel="Expected and mine by syllable"
    style={styles.scroll} contentContainerStyle={styles.row}>
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
        return <View key={syllable.index} style={styles.cell} testID={`syllable-${syllable.index}`}>
          <View style={styles.heading}><Text style={styles.character}>{syllable.characters}</Text>
            <Text style={styles.pinyin}>{syllable.pinyin ?? '?'}</Text></View>
          <View style={styles.pair}>
            <View style={styles.half}><Text style={styles.caption}>{surface ? 'Expected here' : 'Dictionary'}</Text>
              <ExpectedShape syllable={syllable} />
              <Text style={styles.expected}>{tone === 0 ? 'Neutral · 0' : `Tone ${tone ?? '?'}`}</Text>
            </View>
            <View style={styles.half}><Text style={styles.caption}>Mine</Text>
              {syllable.display_contour?.segments?.length ? <PitchPlot compact user={[]} display={syllable.display_contour}
                startSeconds={syllable.start_seconds ?? 0} durationSeconds={syllable.end_seconds ?? 0} /> :
                <View style={styles.shape}><Text style={styles.unavailable}>—</Text></View>}
              <Text style={styles.mine}>{observed === 'unclear' ? 'Unclear' : observed === 'neutral-like' ? 'Neutral-like' : `Tone ${observed}`}</Text>
            </View>
          </View>
          <Text numberOfLines={1} style={styles.note}>{syllable.pinyin === null ? 'Reading unresolved' :
            !syllable.display_contour ? 'Timing unavailable' : observed === 'unclear' ? 'Not enough clear pitch' : 'Approximate shape'}</Text>
        </View>;
      })}
  </ScrollView>;
}
const styles = StyleSheet.create({
  scroll: { flexGrow: 0, height: 184 },
  row: { gap: 8, paddingBottom: 8 },
  cell: { width: 154, height: 174, padding: 10, borderRadius: 12, borderWidth: StyleSheet.hairlineWidth,
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
  unavailable: { color: colors.secondary, fontSize: 13 },
  note: { color: colors.secondary, fontSize: 10, lineHeight: 14 },
  skeletonText: { width: 42, height: 10, borderRadius: 4, backgroundColor: colors.plotGrid },
  skeletonShape: { width: 60, height: 42, marginVertical: 4, borderRadius: 6, backgroundColor: colors.plotGrid },
});
