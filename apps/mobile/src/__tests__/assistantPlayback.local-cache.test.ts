import React, { useEffect } from 'react';
import { act, create, type ReactTestRenderer } from 'react-test-renderer';

import { useAssistantPlayback } from '@/audio/useAssistantPlayback';
import type { AudioDownload } from '@/audio/useCachedAudio';
import { resetAudioSession, stopAllPlayback } from '@/audio/session';

const mockFileContents = new Map<string, Uint8Array>();
const mockDeletedUris: string[] = [];
let mockCorruptWrite = false;
const renderers: ReactTestRenderer[] = [];
beforeEach(() => {
  mockCorruptWrite = false;
  mockPlayer.replace.mockImplementation((source: unknown) => {
    // Match the installed iOS bridge, which rejects null AudioSource records.
    if (source === null) throw new Error('Cannot convert null to AudioSource record');
    mockStatus = { ...mockStatus, isLoaded: false, error: null };
  });
});
afterEach(async () => {
  for (const renderer of renderers.splice(0)) await act(async () => renderer.unmount());
});

jest.mock('expo-file-system', () => {
  const uriFor = (first: unknown, rest: string[]) => {
    const base = typeof first === 'string' ? first : (first as { uri: string }).uri;
    return [base.replace(/\/$/, ''), ...rest].join('/');
  };

  class MockFile {
    readonly uri: string;

    constructor(first: unknown, ...rest: string[]) {
      this.uri = uriFor(first, rest);
    }

    get exists() {
      return mockFileContents.has(this.uri);
    }

    get size() {
      return mockFileContents.get(this.uri)?.byteLength ?? null;
    }

    async bytes() {
      return mockFileContents.get(this.uri) ?? new Uint8Array();
    }

    write(bytes: Uint8Array) {
      const written = new Uint8Array(bytes);
      if (mockCorruptWrite) written[written.length - 1] = written[written.length - 1]! ^ 1;
      mockFileContents.set(this.uri, written);
    }

    delete() {
      mockDeletedUris.push(this.uri);
      mockFileContents.delete(this.uri);
    }
  }

  class MockDirectory {
    readonly uri: string;
    exists = true;

    constructor(first: unknown, ...rest: string[]) {
      this.uri = uriFor(first, rest);
    }

    create() {
      this.exists = true;
    }

    list() {
      return [...mockFileContents.keys()]
        .filter((uri) => uri.startsWith(`${this.uri}/`))
        .map((uri) => new MockFile(uri));
    }
  }

  return {
    Directory: MockDirectory,
    File: MockFile,
    Paths: { cache: { uri: 'file:///cache/' } },
  };
});

let mockListener: ((status: typeof mockStatus) => void) | null = null;
const mockPlayer = {
  get isLoaded() { return mockStatus.isLoaded; },
  addListener: jest.fn((_event: string, listener: typeof mockListener) => { mockListener = listener; return { remove: jest.fn() }; }),
  pause: jest.fn(),
  play: jest.fn(),
  replace: jest.fn(),
  seekTo: jest.fn<Promise<void>, [number]>(),
};
const mockUseAudioPlayer = jest.fn((_source?: unknown, _options?: unknown) => mockPlayer);
let mockStatus = {
  didJustFinish: false,
  error: null as string | null,
  isLoaded: false,
  playing: false,
};

jest.mock('expo-audio', () => ({
  useAudioPlayer: (source: unknown, options: unknown) => mockUseAudioPlayer(source, options),
  useAudioPlayerStatus: () => mockStatus,
}));

const mockFetchAudio = jest.fn<Promise<Uint8Array | AudioDownload>, [string]>();
let latestPlayback!: ReturnType<typeof useAssistantPlayback>;

const source = (id: string) => ({
  id,
  url: `/v1/assistant-speeches/${id}/audio`,
});

function waveBytes(): Uint8Array {
  const bytes = new Uint8Array(64);
  bytes.set([0x52, 0x49, 0x46, 0x46], 0);
  bytes.set([0x57, 0x41, 0x56, 0x45], 8);
  const view = new DataView(bytes.buffer);
  view.setUint32(4, bytes.length - 8, true);
  bytes.set([0x66, 0x6d, 0x74, 0x20], 12);
  view.setUint32(16, 16, true);
  view.setUint16(20, 1, true); // PCM
  view.setUint16(22, 1, true); // mono
  view.setUint32(24, 16000, true);
  view.setUint32(28, 32000, true);
  view.setUint16(32, 2, true);
  view.setUint16(34, 16, true);
  bytes.set([0x64, 0x61, 0x74, 0x61], 36);
  view.setUint32(40, bytes.length - 44, true);
  return bytes;
}

function Harness({ tick }: { tick: number }) {
  void tick;
  const playback = useAssistantPlayback(mockFetchAudio);
  useEffect(() => {
    latestPlayback = playback;
  }, [playback]);
  return null;
}

async function renderHarness(): Promise<ReactTestRenderer> {
  let renderer!: ReactTestRenderer;
  await act(async () => {
    renderer = create(React.createElement(Harness, { tick: 0 }));
  });
  renderers.push(renderer);
  return renderer;
}

async function updateStatus(renderer: ReactTestRenderer, tick: number): Promise<void> {
  await act(async () => {
    mockListener?.(mockStatus);
    renderer.update(React.createElement(Harness, { tick }));
  });
}

describe('assistant playback local cache', () => {
  beforeEach(() => {
    jest.restoreAllMocks();
    jest.clearAllMocks();
    mockListener = null;
    mockFileContents.clear();
    mockDeletedUris.length = 0;
    mockStatus = {
      didJustFinish: false,
      error: null,
      isLoaded: false,
      playing: false,
    };
    mockPlayer.seekTo.mockResolvedValue();
    mockFetchAudio.mockResolvedValue(waveBytes());
    jest.spyOn(console, 'info').mockImplementation(() => {});
  });

  it('fetches speech bytes, writes them to cache, and loads only the local file URI', async () => {
    const renderer = await renderHarness();

    await act(async () => {
      await latestPlayback.play(source('speech-1'));
    });

    expect(mockUseAudioPlayer).toHaveBeenCalledWith(null, { keepAudioSessionActive: true });
    expect(mockFetchAudio).toHaveBeenCalledWith('/v1/assistant-speeches/speech-1/audio');
    expect([...mockFileContents.values()][0]).toEqual(
      waveBytes(),
    );
    expect(mockPlayer.replace).toHaveBeenCalledWith(
      expect.stringMatching(/file:\/\/\/cache\/protected-audio\/\d+\/assistant-speeches-speech-1.wav/),
    );
    expect(JSON.stringify(mockPlayer.replace.mock.calls)).not.toContain('http');
    expect(mockPlayer.play).not.toHaveBeenCalled();

    mockStatus = { ...mockStatus, isLoaded: true };
    await updateStatus(renderer, 1);
    expect(mockPlayer.play).toHaveBeenCalledTimes(1);
  });

  it('replays the loaded local file without downloading it again', async () => {
    const renderer = await renderHarness();
    await act(async () => {
      await latestPlayback.play(source('speech-1'));
    });
    mockStatus = { ...mockStatus, didJustFinish: true, isLoaded: true };
    await updateStatus(renderer, 1);
    mockFetchAudio.mockClear();
    mockPlayer.play.mockClear();

    await act(async () => {
      await latestPlayback.play(source('speech-1'));
    });

    expect(mockFetchAudio).not.toHaveBeenCalled();
    expect(mockPlayer.seekTo).toHaveBeenCalledWith(0);
    expect(mockPlayer.play).toHaveBeenCalledTimes(1);
  });

  it('stops the prior item, replaces it after the new local file loads, and removes old cache', async () => {
    const renderer = await renderHarness();
    await act(async () => {
      await latestPlayback.play(source('speech-1'));
    });
    mockStatus = { ...mockStatus, isLoaded: true };
    await updateStatus(renderer, 1);

    await act(async () => {
      await latestPlayback.play(source('speech-2'));
    });

    expect(mockPlayer.pause).toHaveBeenCalled();
    expect(mockPlayer.replace).toHaveBeenLastCalledWith(
      expect.stringMatching(/file:\/\/\/cache\/protected-audio\/\d+\/assistant-speeches-speech-2.wav/),
    );
    expect(mockDeletedUris).toContainEqual(
      expect.stringMatching(/file:\/\/\/cache\/protected-audio\/\d+\/assistant-speeches-speech-1.wav/),
    );
    expect(mockFileContents.size).toBe(1);

    mockStatus = { ...mockStatus, isLoaded: false };
    await updateStatus(renderer, 2);
    mockStatus = { ...mockStatus, isLoaded: true };
    await updateStatus(renderer, 3);
    expect(mockPlayer.play).toHaveBeenCalledTimes(2);
  });

  it('surfaces authenticated download failures without persisting secrets', async () => {
    const consoleError = jest.spyOn(console, 'error').mockImplementation(() => {});
    mockFetchAudio.mockRejectedValue(new Error('secret-token https://private.test?token=secret-token'));
    await renderHarness();

    await act(async () => {
      await latestPlayback.play(source('speech-1'));
    });

    expect(latestPlayback.error).toContain('could not be played');
    expect(JSON.stringify(consoleError.mock.calls)).not.toContain('secret-token');
    expect(mockPlayer.replace).not.toHaveBeenCalled();
    expect(JSON.stringify([...mockFileContents.keys()])).not.toContain('Authorization');
    expect(JSON.stringify(consoleError.mock.calls)).not.toContain('Authorization');
    expect(JSON.stringify(latestPlayback)).not.toContain('Authorization');
  });

  it('surfaces a native local-player error without logging source data', async () => {
    const consoleError = jest.spyOn(console, 'error').mockImplementation(() => {});
    const renderer = await renderHarness();

    mockStatus = { ...mockStatus, error: 'The operation could not be completed' };
    await updateStatus(renderer, 1);

    expect(latestPlayback.error).toContain('could not be played');
    expect(consoleError).toHaveBeenCalledWith(
      '[audio playback] failed', expect.objectContaining({ operation: 'native-load' }),
    );
    expect(JSON.stringify(consoleError.mock.calls)).not.toContain('/v1/assistant-speeches');
  });

  it('does not start delayed autoplay after recording stops pending playback', async () => {
    let finishDownload!: (bytes: Uint8Array) => void;
    mockFetchAudio.mockReturnValue(
      new Promise((resolve) => {
        finishDownload = resolve;
      }),
    );
    await renderHarness();

    let pending!: Promise<void>;
    await act(async () => {
      pending = latestPlayback.play(source('speech-1'));
      latestPlayback.stop();
      finishDownload(waveBytes());
      await pending;
    });

    expect(mockPlayer.replace).not.toHaveBeenCalled();
    expect(mockPlayer.play).not.toHaveBeenCalled();
  });
});


it('uses the same cache for reference speech and cancels loading before recording', async () => {
  mockFetchAudio.mockResolvedValue(waveBytes());
  mockStatus = { didJustFinish: false, error: null, isLoaded: false, playing: false };
  const renderer = await renderHarness();
  await act(async () => { await latestPlayback.play({ id: 'reference-1', url: '/v1/reference-speech/reference-1/audio' }); });
  expect(mockPlayer.replace).toHaveBeenLastCalledWith(expect.stringMatching(/reference-speech-reference-1.wav$/));
  const playCount = mockPlayer.play.mock.calls.length;
  await act(async () => { stopAllPlayback(); });
  mockStatus = { ...mockStatus, isLoaded: true };
  await updateStatus(renderer, 1);
  expect(mockPlayer.play).toHaveBeenCalledTimes(playCount);
  await act(async () => renderer.unmount());
});

it('separates reference and assistant identities and removes cached audio on sign-out', async () => {
  mockFetchAudio.mockResolvedValue(waveBytes());
  const renderer = await renderHarness();
  await act(async () => { await latestPlayback.play({ id: 'same', url: '/v1/reference-speech/same/audio' }); });
  await act(async () => { await latestPlayback.play({ id: 'same', url: '/v1/assistant-speeches/same/audio' }); });
  expect(mockPlayer.replace).toHaveBeenLastCalledWith(expect.stringMatching(/assistant-speeches-same.wav$/));
  await act(async () => { resetAudioSession(); });
  expect(mockFileContents.size).toBe(0);
  expect(latestPlayback.activeId).toBeNull();
  await act(async () => renderer.unmount());
});

it('keeps saved learner M4A recordings playable through the same protected cache', async () => {
  const bytes = new Uint8Array(64);
  bytes.set([0x66, 0x74, 0x79, 0x70], 4);
  mockFetchAudio.mockResolvedValue(bytes);
  const renderer = await renderHarness();
  await act(async () => { await latestPlayback.play({ id: 'learner', url: '/v1/utterances/learner/audio' }); });
  expect(mockPlayer.replace).toHaveBeenLastCalledWith(expect.stringMatching(/utterances-learner.m4a$/));
  await act(async () => renderer.unmount());
});

it('uses native readiness even when React never renders an unloaded replacement state', async () => {
  mockFetchAudio.mockResolvedValue(waveBytes());
  const renderer = await renderHarness();
  await act(async () => { await latestPlayback.play(source('first')); });
  mockStatus = { ...mockStatus, isLoaded: true };
  await updateStatus(renderer, 1);
  const previousPlays = mockPlayer.play.mock.calls.length;
  await act(async () => { await latestPlayback.play(source('second')); });
  // No intermediate isLoaded=false React update is needed.
  mockStatus = { ...mockStatus, isLoaded: true };
  await updateStatus(renderer, 2);
  expect(mockPlayer.play).toHaveBeenCalledTimes(previousPlays + 1);
  await act(async () => renderer.unmount());
});

it('never sends null to native replace and verifies exact WAV bytes before loading', async () => {
  mockStatus = { didJustFinish: false, error: null, isLoaded: false, playing: false };
  mockFetchAudio.mockResolvedValue(waveBytes());
  await renderHarness();
  await act(async () => { await latestPlayback.play(source('verified')); });
  const uri = mockPlayer.replace.mock.calls.at(-1)![0] as string;
  expect(uri).toMatch(/\.wav$/);
  expect(mockFileContents.get(uri)).toEqual(waveBytes());
  expect(mockPlayer.replace.mock.calls.every(([value]) => value !== null)).toBe(true);
  expect(latestPlayback.error).toBeNull();
});

it('rejects a write that preserves the header and size but corrupts the audio bytes', async () => {
  jest.spyOn(console, 'error').mockImplementation(() => {});
  mockCorruptWrite = true;
  mockFetchAudio.mockResolvedValue(waveBytes());
  await renderHarness();
  const replacements = mockPlayer.replace.mock.calls.length;
  await act(async () => { await latestPlayback.play(source('corrupt')); });
  expect(latestPlayback.error).toContain('could not be played');
  expect(mockPlayer.replace).toHaveBeenCalledTimes(replacements);
  expect([...mockFileContents.keys()].some((key) => key.includes('corrupt'))).toBe(false);
});

it('supports learner WebM container detection without claiming iOS decoder support', async () => {
  const bytes = new Uint8Array(64);
  bytes.set([0x1a, 0x45, 0xdf, 0xa3]);
  mockFetchAudio.mockResolvedValue(bytes);
  await renderHarness();
  await act(async () => { await latestPlayback.play({ id: 'webm', url: '/v1/utterances/webm/audio' }); });
  expect(mockPlayer.replace).toHaveBeenLastCalledWith(expect.stringMatching(/\.webm$/));
});

it('replays loaded local WAV without another network request', async () => {
  mockFetchAudio.mockResolvedValue(waveBytes());
  const renderer = await renderHarness();
  await act(async () => { await latestPlayback.play(source('replay')); });
  mockStatus = { ...mockStatus, isLoaded: true };
  await updateStatus(renderer, 1);
  const downloads = mockFetchAudio.mock.calls.length;
  mockStatus = { ...mockStatus, didJustFinish: true };
  await updateStatus(renderer, 2);
  await act(async () => { await latestPlayback.play(source('replay')); });
  expect(mockFetchAudio).toHaveBeenCalledTimes(downloads);
  expect(mockPlayer.seekTo).toHaveBeenCalledWith(0);
});

it('sanitizes native error diagnostics but retains the failing operation and OS error code', async () => {
  const errors = jest.spyOn(console, 'error').mockImplementation(() => {});
  mockFetchAudio.mockResolvedValue(waveBytes());
  mockPlayer.replace.mockImplementationOnce(() => { throw new Error('AVFoundationErrorDomain Code=-11800 https://private/audio?token=secret Authorization: Bearer secret'); });
  await renderHarness();
  await act(async () => { await latestPlayback.play(source('native-error')); });
  expect(errors).toHaveBeenCalledWith('[audio playback] failed', expect.objectContaining({
    operation: 'replace-local-source', domain: 'AVFoundationErrorDomain', code: -11800,
  }));
  expect(JSON.stringify(errors.mock.calls)).not.toMatch(/secret|private|Authorization|Bearer/);
});

it('deduplicates concurrent downloads and ignores completion after unmount', async () => {
  let finish!: (bytes: Uint8Array) => void;
  mockFetchAudio.mockReturnValue(new Promise((resolve) => { finish = resolve; }));
  const renderer = await renderHarness();
  const downloads = mockFetchAudio.mock.calls.length, replaces = mockPlayer.replace.mock.calls.length;
  let one!: Promise<void>, two!: Promise<void>;
  await act(async () => {
    one = latestPlayback.play(source('concurrent'));
    two = latestPlayback.play(source('concurrent'));
    renderer.unmount();
  });
  await act(async () => { finish(waveBytes()); await Promise.all([one, two]); });
  expect(mockFetchAudio).toHaveBeenCalledTimes(downloads + 1);
  expect(mockPlayer.replace).toHaveBeenCalledTimes(replaces);
});

it('cross-checks MIME against container bytes and preserves legitimate WAV ancillary chunks', async () => {
  jest.spyOn(console, 'error').mockImplementation(() => {});
  const original = waveBytes(), withJunk = new Uint8Array(original.length + 10);
  withJunk.set(original.slice(0, 12));
  withJunk.set([0x4a, 0x55, 0x4e, 0x4b, 1, 0, 0, 0, 7, 0], 12); // odd JUNK chunk and pad
  withJunk.set(original.slice(12), 22);
  new DataView(withJunk.buffer).setUint32(4, withJunk.length - 8, true);
  mockFetchAudio.mockResolvedValue({ bytes: withJunk, contentType: 'audio/wav; charset=binary' });
  await renderHarness();
  await act(async () => { await latestPlayback.play(source('chunks')); });
  expect(latestPlayback.error).toBeNull();
  expect(mockPlayer.replace).toHaveBeenLastCalledWith(expect.stringMatching(/chunks\.wav$/));
  mockFetchAudio.mockResolvedValue({ bytes: original, contentType: 'audio/mp4' });
  const replaces = mockPlayer.replace.mock.calls.length;
  await act(async () => { await latestPlayback.play(source('mismatch')); });
  expect(mockPlayer.replace).toHaveBeenCalledTimes(replaces);
  expect(latestPlayback.error).toContain('could not be played');
});

it('rejects a truncated WAV data chunk before handing it to native playback', async () => {
  jest.spyOn(console, 'error').mockImplementation(() => {});
  const bytes = waveBytes();
  new DataView(bytes.buffer).setUint32(40, bytes.length, true);
  mockFetchAudio.mockResolvedValue(bytes);
  await renderHarness();
  const replaces = mockPlayer.replace.mock.calls.length;
  await act(async () => { await latestPlayback.play(source('truncated')); });
  expect(mockPlayer.replace).toHaveBeenCalledTimes(replaces);
  expect(latestPlayback.error).toContain('could not be played');
});

it('an older download cannot replace or delete a newer playing source', async () => {
  let finishOld!: (bytes: Uint8Array) => void;
  mockFetchAudio.mockImplementationOnce(() => new Promise((resolve) => { finishOld = resolve; }));
  mockFetchAudio.mockResolvedValueOnce(waveBytes());
  await renderHarness();
  let old!: Promise<void>;
  await act(async () => { old = latestPlayback.play(source('old')); });
  await act(async () => { await latestPlayback.play(source('new')); });
  const currentUri = mockPlayer.replace.mock.calls.at(-1)![0] as string;
  await act(async () => { finishOld(waveBytes()); await old; });
  expect(mockPlayer.replace).toHaveBeenLastCalledWith(currentUri);
  expect(mockFileContents.has(currentUri)).toBe(true);
  expect([...mockFileContents.keys()].some((uri) => uri.endsWith('old.wav'))).toBe(false);
});

it('a sign-out during download cannot reload or retain the old account audio', async () => {
  let finish!: (bytes: Uint8Array) => void;
  mockFetchAudio.mockImplementationOnce(() => new Promise((resolve) => { finish = resolve; }));
  await renderHarness();
  let pending!: Promise<void>;
  await act(async () => { pending = latestPlayback.play(source('signed-out')); resetAudioSession(); });
  const replaces = mockPlayer.replace.mock.calls.length;
  await act(async () => { finish(waveBytes()); await pending; });
  expect(mockPlayer.replace).toHaveBeenCalledTimes(replaces);
  expect([...mockFileContents.keys()].some((uri) => uri.includes('signed-out'))).toBe(false);
  expect(latestPlayback.activeId).toBeNull();
});

it('ignores a stale loaded event until the current native item is loaded', async () => {
  mockFetchAudio.mockResolvedValue(waveBytes());
  const renderer = await renderHarness();
  await act(async () => { await latestPlayback.play(source('wait-native')); });
  const plays = mockPlayer.play.mock.calls.length;
  await act(async () => { mockListener?.({ ...mockStatus, isLoaded: true }); });
  expect(mockPlayer.play).toHaveBeenCalledTimes(plays);
  mockStatus = { ...mockStatus, isLoaded: true };
  await updateStatus(renderer, 1);
  expect(mockPlayer.play).toHaveBeenCalledTimes(plays + 1);
});
