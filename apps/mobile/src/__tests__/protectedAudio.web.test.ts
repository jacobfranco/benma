import React, { useEffect } from 'react';
import { act, create, type ReactTestRenderer } from 'react-test-renderer';

import { useCachedAudio } from '@/audio/useCachedAudio.web';
import { beginRecording, registerPlayback, resetAudioSession } from '@/audio/session';
import { BenmaApiClient } from '@/api/client';

jest.mock('expo-file-system', () => { throw new Error('Filesystem evaluated on web'); });
jest.mock('expo/fetch', () => { throw new Error('Expo fetch evaluated on web'); });
function wave() {
  const bytes = new Uint8Array(48), view = new DataView(bytes.buffer);
  bytes.set([82, 73, 70, 70]); view.setUint32(4, 40, true);
  bytes.set([87, 65, 86, 69, 102, 109, 116, 32], 8); view.setUint32(16, 16, true);
  bytes.set([100, 97, 116, 97], 36); view.setUint32(40, 4, true);
  return bytes;
}
class BrowserAudio {
  src = ''; ended = false; currentTime = 0;
  onplaying: (() => void) | null = null;
  onpause: (() => void) | null = null;
  onended: (() => void) | null = null;
  onerror: (() => void) | null = null;
  play = jest.fn(async () => { this.onplaying?.(); });
  pause = jest.fn(() => { this.onpause?.(); });
  removeAttribute() { this.src = ''; }
  load = jest.fn();
}
let players: BrowserAudio[];
let controllers: ReturnType<typeof useCachedAudio>[];
const download = jest.fn(), revoke = jest.fn(), createUrl = jest.fn();
const renderers: ReactTestRenderer[] = [];
const source = (id: string, kind = 'assistant-speeches') => ({ id, url: `/v1/${kind}/${id}/audio` });
function Harness({ index = 0 }) { const value = useCachedAudio(download); useEffect(() => { controllers[index] = value; }); return null; }
async function mount(index = 0) {
  await act(async () => { renderers.push(create(React.createElement(Harness, { index }))); });
}
beforeAll(() => { Object.assign(globalThis, { IS_REACT_ACT_ENVIRONMENT: true }); });
beforeEach(() => {
  players = []; controllers = []; jest.clearAllMocks();
  download.mockResolvedValue({ bytes: wave(), contentType: 'audio/wav' });
  Object.defineProperty(globalThis, 'Audio', { configurable: true, value: jest.fn(() => { const p = new BrowserAudio(); players.push(p); return p; }) });
  Object.defineProperty(URL, 'createObjectURL', { configurable: true, value: createUrl.mockImplementation(() => `blob:cache-${createUrl.mock.calls.length}`) });
  Object.defineProperty(URL, 'revokeObjectURL', { configurable: true, value: revoke });
});
afterEach(async () => { await act(async () => { for (const r of renderers.splice(0)) r.unmount(); resetAudioSession(); }); });
it.each(['assistant-speeches', 'reference-speech', 'utterances'])('caches %s, replays, replaces and revokes on logout', async (kind) => {
  await mount();
  await act(async () => { await controllers[0]!.play(source('one', kind)); });
  await act(async () => { await controllers[0]!.play(source('one', kind)); });
  expect(download).toHaveBeenCalledTimes(1); expect(createUrl).toHaveBeenCalledTimes(1); expect(revoke).not.toHaveBeenCalled();
  await act(async () => { await controllers[0]!.play(source('two', kind)); });
  expect(revoke).toHaveBeenCalledWith('blob:cache-1');
  await act(async () => resetAudioSession());
  expect(players[0]!.src).toBe(''); expect(revoke).toHaveBeenCalledWith('blob:cache-2');
});
it('accepts learner WebM/Opus and rejects MIME/container mismatch', async () => {
  await mount();
  download.mockResolvedValueOnce({ bytes: new Uint8Array([26, 69, 223, 163, ...Array(20).fill(0)]), contentType: 'audio/webm;codecs=opus' });
  await act(async () => { await controllers[0]!.play(source('learner', 'utterances')); });
  expect(createUrl).toHaveBeenCalledTimes(1);
  download.mockResolvedValueOnce({ bytes: wave(), contentType: 'audio/webm' });
  await act(async () => { await controllers[0]!.play(source('bad')); });
  expect(controllers[0]!.error).toContain('Audio unavailable'); expect(createUrl).toHaveBeenCalledTimes(1);
});
it('retains media on autoplay denial and permits a manual retry', async () => {
  await mount(); await act(async () => { await controllers[0]!.play(source('one')); });
  players[0]!.play.mockRejectedValueOnce(new DOMException('blocked', 'NotAllowedError'));
  await act(async () => { await controllers[0]!.play(source('one')); });
  expect(controllers[0]!.error).toBeNull(); expect(controllers[0]!.needsInteraction).toBe(true);
  await act(async () => { await controllers[0]!.play(source('one')); });
  expect(controllers[0]!.needsInteraction).toBe(false); expect(download).toHaveBeenCalledTimes(1);
});
it('cancels late downloads on recording and auth reset', async () => {
  await mount(); let finish!: (value: Uint8Array) => void;
  download.mockImplementationOnce(() => new Promise((resolve) => { finish = resolve; }));
  let task!: Promise<void>;
  await act(async () => { task = controllers[0]!.play(source('one')); });
  await act(async () => { beginRecording({}); resetAudioSession(); finish(wave()); await task; });
  expect(createUrl).not.toHaveBeenCalled(); expect(players).toHaveLength(0);
});
it('bounds retained media even while old conversation rows stay mounted', async () => {
  for (let i = 0; i < 30; i++) { await mount(i); await act(async () => { await controllers[i]!.play(source(String(i))); }); }
  expect(createUrl.mock.calls.length - revoke.mock.calls.length).toBe(12);
  expect(players[0]!.src).toBe(''); expect(players[29]!.src).toBe('blob:cache-30');
});
it('installs auth and completes cleanup even if one player throws', () => {
  const cleanup = jest.fn();
  const bad = registerPlayback(() => {}, () => { throw new Error('disposed'); });
  const good = registerPlayback(() => {}, cleanup);
  const client = new BenmaApiClient();
  expect(() => client.setToken('test-session')).not.toThrow();
  expect(client.authenticatedHeaders()).toEqual({ Authorization: 'Bearer test-session' });
  expect(cleanup).toHaveBeenCalledTimes(1); bad(); good();
});

it('downloads protected audio with browser auth and Blob transport', async () => {
  const blob = { type: 'audio/wav', arrayBuffer: async () => wave().buffer };
  const fetch = jest.fn().mockResolvedValue({ ok: true, status: 200, blob: async () => blob });
  globalThis.fetch = fetch;
  const client = new BenmaApiClient('http://localhost:8000');
  client.setToken('fixture-token');
  const result = await client.downloadAudioFile('/v1/reference-speech/ref/audio');
  expect(result.blob).toBe(blob);
  expect(result.bytes).toEqual(wave());
  const [url, init] = fetch.mock.calls[0]!;
  expect(url).toBe('http://localhost:8000/v1/reference-speech/ref/audio');
  expect(init.headers.get('Authorization')).toBe('Bearer fixture-token');
});
