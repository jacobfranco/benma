import { useMemo, useState } from 'react';
import { StyleSheet, Text, View } from 'react-native';

import type { DisplayContour } from '@/api/types';
import { colors } from '@/theme';

export interface PitchPoint {
  timestamp_seconds?: number;
  normalized_semitones?: number | null;
  voicing_probability?: number | null;
}
interface Region { label: string; start_seconds: number; end_seconds: number }
interface Dot { x: number; y: number; confidence: number }

export function pitchDots(points: PitchPoint[], width: number, height: number, durationSeconds = 0,
  domain?: [number, number], startSeconds = 0): Dot[] {
  const voiced = points.filter((p) => Number.isFinite(p.timestamp_seconds) && Number.isFinite(p.normalized_semitones));
  if (!voiced.length || width <= 0 || height <= 0) return [];
  const end = Math.max(durationSeconds, ...points.map(p => Number.isFinite(p.timestamp_seconds) ? p.timestamp_seconds! : 0), startSeconds + .001);
  const low = domain?.[0] ?? Math.min(-3, ...voiced.map(p => p.normalized_semitones! - 1));
  const high = domain?.[1] ?? Math.max(3, ...voiced.map(p => p.normalized_semitones! + 1));
  return voiced.map(p => ({ x: (p.timestamp_seconds! - startSeconds) / (end - startSeconds) * width,
    y: height - (p.normalized_semitones! - low) / Math.max(2, high - low) * height,
    confidence: p.voicing_probability ?? 1 }));
}

// Legacy evidence keeps explicit gaps. New analyses supply server-filtered segments.
export function pitchSegments(points: PitchPoint[]): PitchPoint[][] {
  const segments: PitchPoint[][] = [];
  let current: PitchPoint[] = [];
  for (const point of points) {
    if (!Number.isFinite(point.timestamp_seconds) || !Number.isFinite(point.normalized_semitones)) {
      if (current.length) segments.push(current);
      current = []; continue;
    }
    const last = current.at(-1);
    if (last && (point.timestamp_seconds! - last.timestamp_seconds! > .045 || point.timestamp_seconds! <= last.timestamp_seconds!)) {
      segments.push(current); current = [];
    }
    current.push(point);
  }
  if (current.length) segments.push(current);
  return segments;
}

// Native Views keep this shared with iOS/Android without adding an SVG dependency.
export function ContourLines({ segments, color = colors.primary }: { segments: Dot[][]; color?: string }) {
  return <>{segments.flatMap((segment, i) => segment.length === 1 ? [
    <View key={`${i}-single`} style={[styles.dot, { left: segment[0]!.x - 1.5, top: segment[0]!.y - 1.5, backgroundColor: color }]} />,
  ] : segment.slice(1).map((end, j) => {
    const start = segment[j]!, dx = end.x - start.x, dy = end.y - start.y;
    const length = Math.hypot(dx, dy);
    return <View key={`${i}-${j}`} testID="contour-line" style={[styles.line, {
      left: (start.x + end.x) / 2 - length / 2, top: (start.y + end.y) / 2 - 1,
      width: length, backgroundColor: color, transform: [{ rotate: `${Math.atan2(dy, dx)}rad` }],
    }]} />;
  }))}</>;
}

export function PitchPlot({ user, reference = [], display, referenceDisplay, regions = [], compact = false,
  durationSeconds = 0, startSeconds = 0 }: {
  user: PitchPoint[]; reference?: PitchPoint[]; display?: DisplayContour | null | undefined; referenceDisplay?: DisplayContour | null | undefined;
  regions?: Region[]; compact?: boolean; durationSeconds?: number; startSeconds?: number;
}) {
  const [width, setWidth] = useState(0);
  const height = compact ? 46 : 136;
  const segments = useMemo(() => display?.segments ?? pitchSegments(user), [display, user]);
  const referenceSegments = useMemo(() => referenceDisplay?.segments ?? pitchSegments(reference), [referenceDisplay, reference]);
  const all = [...segments.flat(), ...referenceSegments.flat()];
  const duration = Math.max(durationSeconds, ...regions.map(r => r.end_seconds),
    ...all.map(p => p.timestamp_seconds ?? 0), startSeconds + .001);
  const domain: [number, number] = [Math.min(display?.minimum_semitones ?? -3,
    ...all.map(p => (p.normalized_semitones ?? 0)-1)),
  Math.max(display?.maximum_semitones ?? 3, ...all.map(p => (p.normalized_semitones ?? 0)+1))];
  const geometry = (items: PitchPoint[][]) => items.map(s => pitchDots(s, width-8, height-8, duration, domain, startSeconds)
    .map(p => ({ ...p, x: p.x+4, y: p.y+4 })));
  if (!all.length) return <View style={{ height }}><Text style={styles.empty}>No clear pitch</Text></View>;
  return <View>
    {!compact && <View style={styles.legend}>
      <Text style={styles.userLegend}>Mine</Text>
      {reference.length > 0 && <Text style={styles.referenceLegend}>Reference</Text>}
      <Text style={styles.axisLabel}>relative pitch (st) ↑</Text>
    </View>}
    <View accessibilityLabel="Relative pitch contour" onLayout={e => setWidth(e.nativeEvent.layout.width)}
      style={[styles.plot, { height }]}>
      {!compact && [.25, .5, .75].map(f => <View key={f} style={[styles.gridLine, { top: height*f }]} />)}
      {!compact && regions.map((r, i) => <View key={i} style={[styles.region, {
        left: `${r.start_seconds / duration * 100}%`, width: `${(r.end_seconds-r.start_seconds) / duration * 100}%`,
      }]}><Text style={styles.regionLabel}>{r.label}</Text></View>)}
      <ContourLines segments={geometry(referenceSegments)} color={colors.reference} />
      <ContourLines segments={geometry(segments)} />
    </View>
    {!compact && <Text style={styles.timeLabel}>time →</Text>}
  </View>;
}
const styles = StyleSheet.create({
  legend: { flexDirection: 'row', flexWrap: 'wrap', gap: 14, marginBottom: 8 },
  userLegend: { color: colors.primary, fontSize: 12, fontWeight: '700' },
  referenceLegend: { color: colors.reference, fontSize: 12, fontWeight: '700' },
  axisLabel: { marginLeft: 'auto', color: colors.secondary, fontSize: 11 },
  plot: { backgroundColor: colors.plotBackground, borderColor: colors.border, borderWidth: StyleSheet.hairlineWidth,
    borderRadius: 8, overflow: 'hidden', position: 'relative' },
  gridLine: { position: 'absolute', left: 0, right: 0, height: StyleSheet.hairlineWidth, backgroundColor: colors.plotGrid },
  region: { position: 'absolute', top: 0, bottom: 0, borderRightColor: colors.plotGrid, borderRightWidth: StyleSheet.hairlineWidth },
  regionLabel: { color: colors.secondary, fontSize: 10, padding: 4 },
  line: { position: 'absolute', height: 2, borderRadius: 1 },
  dot: { position: 'absolute', width: 3, height: 3, borderRadius: 2 },
  timeLabel: { color: colors.secondary, fontSize: 11, textAlign: 'right', marginTop: 4 },
  empty: { color: colors.secondary, fontSize: 12, textAlign: 'center', marginTop: 12 },
});
