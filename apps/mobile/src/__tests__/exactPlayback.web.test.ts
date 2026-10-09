import React from 'react';
import { act, create, type ReactTestRenderer } from 'react-test-renderer';

import { canonicalWave } from './canonicalWave';

import { api } from '@/api/client';
import { ExactPlaybackButton, useCanonicalRecording } from '@/audio/ExactPlaybackButton';
import { resetAudioSession, stopAllPlayback } from '@/audio/session';

class BrowserAudio {
  src = ''; ended = false; currentTime = 0;
  onplaying: (() => void) | null = null;
  onpause: (() => void) | null = null;
  onended: (() => void) | null = null;
  onerror: (() => void) | null = null;
  play = jest.fn(async () => this.onplaying?.());
  pause = jest.fn(() => this.onpause?.());
  removeAttribute() { this.src = ''; }
  load = jest.fn();
}
let renderer: ReactTestRenderer, players: BrowserAudio[];
const createUrl = jest.fn(), revoke = jest.fn();
function Harness({ start = .1, end = .2 }) {
  const fetchRecording = useCanonicalRecording('u');
  return React.createElement(ExactPlaybackButton, { key: `${start}:${end}`, utteranceId: 'u', text: '想', start, end, fetchRecording });
}
async function press() {
  await act(async () => renderer.root.findByProps({ accessibilityLabel: 'Play my recording for 想' }).props.onPress());
}
beforeEach(async () => {
  players = []; jest.clearAllMocks();
  jest.spyOn(api, 'downloadCanonicalRecording').mockResolvedValue(canonicalWave());
  Object.defineProperty(globalThis, 'Audio', { configurable: true, value: jest.fn(() => { const p = new BrowserAudio(); players.push(p); return p; }) });
  Object.defineProperty(URL, 'createObjectURL', { configurable: true, value: createUrl.mockImplementation(() => `blob:exact-${createUrl.mock.calls.length}`) });
  Object.defineProperty(URL, 'revokeObjectURL', { configurable: true, value: revoke });
  await act(async () => { renderer = create(React.createElement(Harness)); });
});
afterEach(async () => {
  await act(async () => { renderer.unmount(); resetAudioSession(); });
  jest.restoreAllMocks();
});
it('downloads canonical once, replaces one exact segment, and cleans playback on unmount', async () => {
  expect(api.downloadCanonicalRecording).not.toHaveBeenCalled(); // No autoplay/preload.
  await press();
  expect(api.downloadCanonicalRecording).toHaveBeenCalledWith('u');
  expect(createUrl.mock.calls[0]![0].size).toBe(44 + .1 * 32000);
  await act(async () => renderer.update(React.createElement(Harness, { start: .3, end: .5 })));
  expect(players[0]!.src).toBe('');
  expect(revoke).toHaveBeenCalledWith('blob:exact-1');
  await press();
  expect(api.downloadCanonicalRecording).toHaveBeenCalledTimes(1);
  expect(createUrl.mock.calls[1]![0].size).toBe(44 + .2 * 32000);
  await act(async () => renderer.unmount());
  expect(players[1]!.src).toBe('');
  expect(revoke).toHaveBeenCalledWith('blob:exact-2');
});
it('rapid taps share the pending canonical download; only the latest selection starts', async () => {
  let finish!: (value: Uint8Array) => void;
  jest.mocked(api.downloadCanonicalRecording).mockReturnValueOnce(new Promise(resolve => { finish = resolve; }));
  await press(); await press();
  await act(async () => renderer.update(React.createElement(Harness, { start: .4, end: .6 })));
  await press();
  await act(async () => finish(canonicalWave()));
  expect(api.downloadCanonicalRecording).toHaveBeenCalledTimes(1);
  expect(createUrl).toHaveBeenCalledTimes(1);
  expect(players).toHaveLength(1);
  expect(players[0]!.play).toHaveBeenCalledTimes(1);
});
it('stop/navigation/background invalidates a pending download without later playback', async () => {
  let finish!: (value: Uint8Array) => void;
  jest.mocked(api.downloadCanonicalRecording).mockReturnValueOnce(new Promise(resolve => { finish = resolve; }));
  await press();
  await act(async () => { stopAllPlayback(); finish(canonicalWave()); });
  expect(createUrl).not.toHaveBeenCalled();
  expect(players).toHaveLength(0);
});
it('a canonical failure never falls back to original audio, and retry can succeed', async () => {
  jest.mocked(api.downloadCanonicalRecording).mockRejectedValueOnce(new Error('Unavailable'));
  await press();
  expect(JSON.stringify(renderer.toJSON())).toContain('Audio unavailable');
  expect(players).toHaveLength(0);
  await press();
  expect(players[0]!.play).toHaveBeenCalledTimes(1);
});
