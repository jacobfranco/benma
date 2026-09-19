import React, { useEffect } from 'react';
import { act, create } from 'react-test-renderer';

import { registerPlayback, playbackAllowed } from '@/audio/session';
import { useAudioCapture } from '@/audio/useAudioCapture';

const mockRecorder = {
  getStatus: jest.fn(),
  prepareToRecordAsync: jest.fn<Promise<void>, []>(),
  record: jest.fn(),
  stop: jest.fn<Promise<void>, []>(),
  uri: 'file:///recording.m4a',
};
let mockRecordingStatusListener: ((status: {
  hasError: boolean;
  isFinished: boolean;
  error: string | null;
}) => void) | null = null;

jest.mock('expo-audio', () => ({
  AudioModule: {
    getRecordingPermissionsAsync: jest.fn().mockResolvedValue({ granted: true }),
    requestRecordingPermissionsAsync: jest.fn().mockResolvedValue({ granted: true }),
  },
  RecordingPresets: { HIGH_QUALITY: { extension: '.m4a' } },
  setAudioModeAsync: jest.fn().mockResolvedValue(undefined),
  useAudioRecorder: (
    _options: unknown,
    listener: typeof mockRecordingStatusListener,
  ) => {
    mockRecordingStatusListener = listener;
    return mockRecorder;
  },
  useAudioRecorderState: () => ({
    durationMillis: 0,
    isRecording: false,
    mediaServicesDidReset: false,
  }),
}));

let latestCapture!: ReturnType<typeof useAudioCapture>;
const captureHook = (capture: ReturnType<typeof useAudioCapture>) => {
  latestCapture = capture;
};

function Harness({
  onCapture,
}: {
  onCapture: (capture: ReturnType<typeof useAudioCapture>) => void;
}) {
  const capture = useAudioCapture({ directory: 'cache' });
  useEffect(() => onCapture(capture), [capture, onCapture]);
  return null;
}

describe('audio capture lifecycle', () => {
  beforeEach(() => {
    jest.restoreAllMocks();
    jest.clearAllMocks();
    mockRecorder.prepareToRecordAsync.mockResolvedValue();
    mockRecorder.stop.mockResolvedValue();
    mockRecorder.getStatus.mockReturnValue({ isRecording: true, durationMillis: 2345 });
  });

  it('uses the final native status captured before recorder finalization', async () => {
    await act(async () => {
      create(React.createElement(Harness, { onCapture: captureHook }));
    });
    await act(async () => {
      await latestCapture.start();
    });

    const recording = await latestCapture.stop();

    expect(recording).toEqual({ uri: 'file:///recording.m4a', durationMillis: 2345 });
    expect(mockRecorder.prepareToRecordAsync).toHaveBeenCalledTimes(1);
    expect(mockRecorder.record).toHaveBeenCalledTimes(1);
    expect(mockRecorder.stop).toHaveBeenCalledTimes(1);
  });

  it('rejects a recording that the native session ended before the user stopped it', async () => {
    await act(async () => {
      create(React.createElement(Harness, { onCapture: captureHook }));
    });
    await act(async () => {
      await latestCapture.start();
      mockRecordingStatusListener?.({ hasError: false, isFinished: true, error: null });
    });
    mockRecorder.getStatus.mockReturnValue({ isRecording: false, durationMillis: 0 });

    let thrown: unknown;
    await act(async () => {
      try {
        await latestCapture.stop();
      } catch (error) {
        thrown = error;
      }
    });
    expect(thrown).toEqual(expect.objectContaining({ message: 'Recording stopped unexpectedly. Please record again.' }));
    expect(mockRecorder.stop).not.toHaveBeenCalled();
  });
});

it('stops all playback before preparing the native recorder', async () => {
  const stopPlayback = jest.fn();
  const unregister = registerPlayback(stopPlayback);
  mockRecorder.getStatus.mockReturnValue({ isRecording: true, durationMillis: 1000 });
  let renderer!: ReturnType<typeof create>;
  await act(async () => { renderer = create(React.createElement(Harness, { onCapture: captureHook })); });
  mockRecorder.prepareToRecordAsync.mockClear();
  await act(async () => { await latestCapture.start(); });
  expect(stopPlayback).toHaveBeenCalled();
  expect(stopPlayback.mock.invocationCallOrder[0]).toBeLessThan(mockRecorder.prepareToRecordAsync.mock.invocationCallOrder[0]!);
  expect(playbackAllowed()).toBe(false);
  await act(async () => { await latestCapture.stop(); });
  expect(playbackAllowed()).toBe(true);
  unregister();
  await act(async () => renderer.unmount());
});
