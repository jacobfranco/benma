import { useMemo, useState } from 'react';
import { StyleSheet, Text, View } from 'react-native';

import type { DisplayContour } from '@/api/types';
import { pitchFeedbackCopy } from '@/speech/pitchFeedback';
import { colors } from '@/theme';

export interface PitchPoint {
  timestamp_seconds?: number;
  normalized_semitones?: number | null;
  voicing_probability?: number | null;
}
interface Region { label: string; start_seconds: number; end_seconds: number }
interface Dot { x: number; y: number; confidence: number }
// A separate display coordinate leaves source timestamps untouched.
export interface PitchXLayout {
  segments: (PitchPoint & { position: number })[][];
  regions: { index: number; label: string; start: number; end: number }[];
  evidenceRegions?: { index: number; label: string; start: number; end: number }[];
  pauses: number[];
  extent: number;
}
export function normalizedGeometry(layout: PitchXLayout, width: number, height: number, domain: [number, number]): Dot[][] {
  if (width <= 0 || height <= 0 || layout.extent <= 0) return [];
  return layout.segments.map(segment => segment.map(p => ({ x: p.position / layout.extent * width,
    y: height - (p.normalized_semitones! - domain[0]) / Math.max(2, domain[1] - domain[0]) * height, confidence: 1 })));
}

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

// Display coordinates only: preserve measured timestamps and every segment boundary.
export function contourGeometry(segments: PitchPoint[][], width: number, height: number,
  domain: [number, number], start: number, end: number, fitVoiced = false): Dot[][] {
  const points = segments.flat().filter(p => Number.isFinite(p.timestamp_seconds) && Number.isFinite(p.normalized_semitones));
  const first = fitVoiced && points.length ? Math.min(...points.map(p => p.timestamp_seconds!)) : start;
  const last = fitVoiced && points.length ? Math.max(...points.map(p => p.timestamp_seconds!)) : end;
  return segments.map(segment => pitchDots(segment, width, height, last, domain, first));
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
  durationSeconds = 0, startSeconds = 0, fitVoiced = false, fixedDisplayDomain = false,
  showPoints = false, pointsOnly = false, rejected = [], xLayout, showRegionLabels = true, showMineLabel = true,
  showAxes = true, showEmptyLabel = true, transparent = false, plotHeight,
  accessibilityLabel = 'Relative pitch contour' }: {
  accessibilityLabel?: string;
  plotHeight?: number;
  transparent?: boolean;
  showAxes?: boolean; showEmptyLabel?: boolean;
  xLayout?: PitchXLayout | undefined; showRegionLabels?: boolean; showMineLabel?: boolean;
  showPoints?: boolean; pointsOnly?: boolean; rejected?: PitchPoint[];
  user: PitchPoint[]; reference?: PitchPoint[]; display?: DisplayContour | null | undefined; referenceDisplay?: DisplayContour | null | undefined;
  fixedDisplayDomain?: boolean; regions?: Region[]; compact?: boolean; durationSeconds?: number; startSeconds?: number; fitVoiced?: boolean;
}) {
  const [width, setWidth] = useState(0);
  const height = compact ? 46 : plotHeight ?? 136;
  const segments = useMemo(() => display?.segments ?? pitchSegments(user), [display, user]);
  const referenceSegments = useMemo(() => referenceDisplay?.segments ?? pitchSegments(reference), [referenceDisplay, reference]);
  const all = [...segments.flat(), ...referenceSegments.flat(), ...rejected].filter(p => Number.isFinite(p.normalized_semitones));
  const duration = Math.max(durationSeconds, ...regions.map(r => r.end_seconds),
    ...all.map(p => p.timestamp_seconds ?? 0), startSeconds + .001);
  const domain: [number, number] = fixedDisplayDomain ? [display?.minimum_semitones ?? -4, display?.maximum_semitones ?? 4] : [Math.min(display?.minimum_semitones ?? -3,
    ...all.map(p => (p.normalized_semitones ?? 0)-1)),
  Math.max(display?.maximum_semitones ?? 3, ...all.map(p => (p.normalized_semitones ?? 0)+1))];
  const geometry = (items: PitchPoint[][]) => contourGeometry(items, width-8, height-8, domain, startSeconds, duration, fitVoiced)
    .map(segment => segment.map(p => ({ ...p, x: p.x+4, y: p.y+4 })));
  const mineGeometry = xLayout ? normalizedGeometry(xLayout, width-8, height-8, domain)
    .map(segment => segment.map(p => ({ ...p, x: p.x+4, y: p.y+4 }))) : geometry(segments);
  const plotRegions = xLayout ? (xLayout.evidenceRegions ?? xLayout.regions).map(r => ({ label: r.label,
    left: r.start / xLayout.extent, width: (r.end-r.start) / xLayout.extent })) : regions.map(r => ({ label: r.label,
    left: (r.start_seconds-startSeconds) / (duration-startSeconds), width: (r.end_seconds-r.start_seconds) / (duration-startSeconds) }));
  return <View>
    {!compact && (showMineLabel || reference.length > 0 || showAxes) && <View style={styles.legend}>
      {showMineLabel && <Text style={styles.userLegend}>Mine</Text>}
      {reference.length > 0 && <Text style={styles.referenceLegend}>Reference</Text>}
      {showAxes && <Text style={styles.axisLabel}>relative pitch (st) ↑</Text>}
    </View>}
    <View accessibilityLabel={accessibilityLabel} onLayout={e => setWidth(e.nativeEvent.layout.width)}
      style={[styles.plot, { height }, transparent && { backgroundColor: 'transparent' }]}>
      {!compact && [.25, .5, .75].map(f => <View key={f} style={[styles.gridLine, { top: height*f }]} />)}
      {!compact && plotRegions.map((r, i) => <View key={i} style={[styles.region, {
        left: 4 + r.left * (width-8), width: r.width * (width-8),
      }]}>{showRegionLabels && <Text style={styles.regionLabel}>{r.label}</Text>}</View>)}
      {xLayout?.pauses.map(position => <Text key={position} testID="pitch-pause" accessibilityLabel="Pause"
        style={[styles.pause, { left: 4 + position / xLayout.extent * (width-8) - 5 }]}>‖</Text>)}
      {showEmptyLabel && !(xLayout ? xLayout.segments.flat().length : all.length) && <Text style={styles.empty}>{xLayout && !xLayout.regions.length ? 'Timing unavailable · see More detail for pitch' : pitchFeedbackCopy.unavailable}</Text>}
      {!pointsOnly && <ContourLines segments={geometry(referenceSegments)} color={colors.reference} />}
      {!pointsOnly && <ContourLines segments={mineGeometry} />}
      {(showPoints || pointsOnly) && <ContourLines segments={mineGeometry.flat().map(p => [p])} />}
      {rejected.length > 0 && <ContourLines segments={geometry([rejected]).flat().map(p => [p])} color={colors.secondary} />}
    </View>
    {!compact && showAxes && <Text style={styles.timeLabel}>{xLayout ? 'syllables →' : 'time →'}</Text>}
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
  pause: { position: 'absolute', bottom: 4, color: colors.secondary, fontSize: 14 },
  line: { position: 'absolute', height: 2, borderRadius: 1 },
  dot: { position: 'absolute', width: 3, height: 3, borderRadius: 2 },
  timeLabel: { color: colors.secondary, fontSize: 11, textAlign: 'right', marginTop: 4 },
  empty: { color: colors.secondary, fontSize: 12, textAlign: 'center', marginTop: 12 },
});
