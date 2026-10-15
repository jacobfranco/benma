import { useMemo } from 'react';

import type { DisplayContour } from '@/api/types';
import { PitchPlot } from '@/components/PitchPlot';
import { shapeDisplay } from '@/speech/pitchShapeDisplay';

// Learner view has its own explicit display projection. Technical PitchPlot
// callers continue to use real timestamps and the recording's semitone scale.
export function PitchShapePlot({ display, start, end, height = 96, regions = [] }: {
  display: DisplayContour; start: number; end: number; height?: number;
  regions?: { label: string; start: number; end: number }[];
}) {
  const { domain, layout } = useMemo(() => shapeDisplay(display.segments ?? [], start, end, regions), [display, start, end, regions]);
  return <PitchPlot user={[]} display={{ ...display, minimum_semitones: domain[0], maximum_semitones: domain[1] }}
    startSeconds={start} durationSeconds={end} xLayout={layout} fixedDisplayDomain
    showPoints showAxes={false} showMineLabel={false} showRegionLabels={false} plotHeight={height}
    accessibilityLabel="Pitch shape across the selected spoken span; gaps mean missing pitch" />;
}
