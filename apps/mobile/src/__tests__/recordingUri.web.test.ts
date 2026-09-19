import React, { useEffect } from 'react';
import { act, create, type ReactTestRenderer } from 'react-test-renderer';

import { retainRecordingUri } from '@/audio/recordingUri';
import { useAudioCapture } from '@/audio/useAudioCapture';

const mockRecorder = {
  uri: 'blob:http://localhost/one',
  prepareToRecordAsync: jest.fn(), record: jest.fn(), stop: jest.fn(),
  getStatus: () => ({ isRecording: true, durationMillis: 2000 }),
};
jest.mock('expo-audio', () => ({
  AudioModule: {
    getRecordingPermissionsAsync: async () => ({ granted: true }),
    requestRecordingPermissionsAsync: async () => ({ granted: true }),
  },
  RecordingPresets: { HIGH_QUALITY: {} },
  setAudioModeAsync: async () => {},
  useAudioRecorder: () => mockRecorder,
  useAudioRecorderState: () => ({ isRecording: false }),
}));

let capture: ReturnType<typeof useAudioCapture>;
function Harness() {
  const value = useAudioCapture();
  useEffect(() => { capture = value; });
  return null;
}

let renderer: ReactTestRenderer;
const revoke = jest.fn();
beforeAll(() => {
  Object.assign(globalThis, { IS_REACT_ACT_ENVIRONMENT: true, IS_REACT_NATIVE_TEST_ENVIRONMENT: true });
});
beforeEach(async () => {
  jest.clearAllMocks();
  Object.defineProperty(URL, 'revokeObjectURL', { configurable: true, value: revoke });
  mockRecorder.uri = 'blob:http://localhost/one';
  mockRecorder.stop.mockResolvedValue(undefined);
  await act(async () => { renderer = create(React.createElement(Harness)); });
});
afterEach(async () => { await act(async () => renderer.unmount()); });

it('releases replaced recordings while retaining one current recording for retry', async () => {
  for (let i = 0; i < 30; i++) {
    mockRecorder.uri = `blob:http://localhost/${i}`;
    await act(async () => { await capture.start(); await capture.stop(); });
    expect(revoke).toHaveBeenCalledTimes(i);
    expect(revoke).not.toHaveBeenCalledWith(mockRecorder.uri);
  }
  await act(async () => renderer.unmount());
  expect(revoke).toHaveBeenCalledTimes(30);
});

it('keeps a local replay lease alive after the capture screen unmounts', async () => {
  await act(async () => { await capture.start(); await capture.stop(); });
  const releaseReplay = retainRecordingUri(mockRecorder.uri);
  await act(async () => renderer.unmount());
  expect(revoke).not.toHaveBeenCalled();
  releaseReplay(); releaseReplay();
  expect(revoke).toHaveBeenCalledTimes(1);
});

it('cleans up a recording URL produced after its owner unmounted', async () => {
  let finish!: () => void;
  mockRecorder.stop.mockImplementationOnce(() => new Promise<void>((resolve) => { finish = resolve; }));
  await act(async () => { await capture.start(); });
  const pending = capture.stop();
  await act(async () => renderer.unmount());
  expect(revoke).not.toHaveBeenCalled();
  finish();
  await pending;
  expect(revoke).toHaveBeenCalledWith(mockRecorder.uri);
});

it('never revokes native file URIs', () => {
  retainRecordingUri('file:///native/recording.m4a')();
  expect(revoke).not.toHaveBeenCalled();
});

it('stops the microphone and releases its discarded URL on unmount during recording', async () => {
  await act(async () => { await capture.start(); });
  await act(async () => renderer.unmount());
  expect(mockRecorder.stop).toHaveBeenCalledTimes(1);
  expect(revoke).toHaveBeenCalledWith(mockRecorder.uri);
});
