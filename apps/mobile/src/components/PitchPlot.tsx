import { useMemo, useState } from 'react';
import { StyleSheet, Text, View } from 'react-native';

import { colors } from '@/theme';

export interface PitchPoint {
  timestamp_seconds?: number;
  normalized_semitones?: number | null;
  voicing_probability?: number | null;
}

interface Region {
  label: string;
  start_seconds: number;
  end_seconds: number;
}

interface Dot {
  x: number;
  y: number;
  confidence: number;
}

export function pitchDots(points: PitchPoint[], width: number, height: number): Dot[] {
  const voiced = points.filter(
    (point): point is PitchPoint & {
      timestamp_seconds: number;
      normalized_semitones: number;
    } =>
      typeof point.timestamp_seconds === 'number' &&
      typeof point.normalized_semitones === 'number',
  );
  if (!voiced.length || width <= 0 || height <= 0) return [];
  const maximumTime = Math.max(...voiced.map((point) => point.timestamp_seconds), 0.001);
  const values = voiced.map((point) => point.normalized_semitones);
  const minimumPitch = Math.min(...values) - 1;
  const maximumPitch = Math.max(...values) + 1;
  const range = Math.max(2, maximumPitch - minimumPitch);
  return voiced.map((point) => ({
    x: (point.timestamp_seconds / maximumTime) * width,
    y: height - ((point.normalized_semitones - minimumPitch) / range) * height,
    confidence: point.voicing_probability ?? 1,
  }));
}

export function PitchPlot({
  user,
  reference = [],
  regions = [],
  compact = false,
}: {
  user: PitchPoint[];
  reference?: PitchPoint[];
  regions?: Region[];
  compact?: boolean;
}) {
  const [width, setWidth] = useState(0);
  const height = compact ? 92 : 160;
  const combined = useMemo(() => [...user, ...reference], [reference, user]);
  const scale = useMemo(() => pitchDots(combined, width, height), [combined, height, width]);
  const userCount = user.filter((point) => typeof point.normalized_semitones === 'number').length;
  const referenceCount = reference.filter(
    (point) => typeof point.normalized_semitones === 'number',
  ).length;
  const userDots = scale.slice(0, userCount);
  const referenceDots = scale.slice(userCount, userCount + referenceCount);
  const duration = Math.max(...regions.map((region) => region.end_seconds), 0);

  if (!userCount && !referenceCount) {
    return <Text style={styles.empty}>No reliable voiced pitch samples.</Text>;
  }

  return (
    <View>
      {!compact && (
        <View style={styles.legend}>
          <Text style={styles.userLegend}>● Mine</Text>
          <Text style={styles.referenceLegend}>● Reference</Text>
          <Text style={styles.axisLabel}>relative pitch ↑</Text>
        </View>
      )}
      <View
        accessibilityLabel="Relative pitch contour"
        onLayout={(event) => setWidth(event.nativeEvent.layout.width)}
        style={[styles.plot, { height }]}
      >
        {[0.25, 0.5, 0.75].map((fraction) => (
          <View key={fraction} style={[styles.gridLine, { top: height * fraction }]} />
        ))}
        {duration > 0 &&
          regions.map((region, index) => (
            <View
              key={`${region.label}-${index}`}
              style={[
                styles.region,
                {
                  left: `${(region.start_seconds / duration) * 100}%`,
                  width: `${((region.end_seconds - region.start_seconds) / duration) * 100}%`,
                },
              ]}
            >
              {!compact && <Text style={styles.regionLabel}>{region.label}</Text>}
            </View>
          ))}
        {referenceDots.map((dot, index) => (
          <View
            key={`reference-${index}`}
            style={[
              styles.dot,
              styles.referenceDot,
              { left: dot.x - 2, top: dot.y - 2, opacity: Math.max(0.25, dot.confidence) },
            ]}
          />
        ))}
        {userDots.map((dot, index) => (
          <View
            key={`user-${index}`}
            style={[
              styles.dot,
              styles.userDot,
              { left: dot.x - 2, top: dot.y - 2, opacity: Math.max(0.25, dot.confidence) },
            ]}
          />
        ))}
      </View>
      {!compact && <Text style={styles.timeLabel}>time →</Text>}
    </View>
  );
}

const styles = StyleSheet.create({
  legend: { flexDirection: 'row', gap: 14, alignItems: 'center', marginBottom: 8 },
  userLegend: { color: colors.primary, fontSize: 12, fontWeight: '700' },
  referenceLegend: { color: colors.reference, fontSize: 12, fontWeight: '700' },
  axisLabel: { marginLeft: 'auto', color: colors.secondary, fontSize: 11 },
  plot: {
    backgroundColor: colors.plotBackground,
    borderColor: colors.border,
    borderWidth: StyleSheet.hairlineWidth,
    borderRadius: 10,
    overflow: 'hidden',
    position: 'relative',
  },
  gridLine: {
    position: 'absolute',
    left: 0,
    right: 0,
    height: StyleSheet.hairlineWidth,
    backgroundColor: colors.plotGrid,
  },
  region: {
    position: 'absolute',
    top: 0,
    bottom: 0,
    borderRightColor: colors.plotGrid,
    borderRightWidth: StyleSheet.hairlineWidth,
  },
  regionLabel: { color: colors.secondary, fontSize: 10, padding: 4 },
  dot: { position: 'absolute', width: 4, height: 4, borderRadius: 2 },
  userDot: { backgroundColor: colors.primary },
  referenceDot: { backgroundColor: colors.reference },
  timeLabel: { color: colors.secondary, fontSize: 11, textAlign: 'right', marginTop: 4 },
  empty: { color: colors.secondary, fontSize: 13, fontStyle: 'italic' },
});
