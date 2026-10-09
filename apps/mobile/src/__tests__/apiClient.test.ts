import { fetch as expoFetch } from 'expo/fetch';
import { File } from 'expo-file-system';

import { ApiError, BenmaApiClient } from '@/api/client';
import { errorMessage } from '@/api/errors';

jest.mock('expo/fetch', () => ({ fetch: jest.fn() }));
jest.mock('expo-file-system', () => ({
  File: class MockExpoFile extends Blob {
    readonly uri: string;

    constructor(uri: string) {
      super(['device file'], { type: 'audio/mp4' });
      this.uri = uri;
    }
  },
}));

const multipartFetchMock = expoFetch as jest.Mock;

function jsonResponse(payload: unknown, status = 200): Response {
  return {
    ok: status >= 200 && status < 300,
    status,
    json: async () => payload,
  } as Response;
}

describe('API client', () => {
  afterEach(() => {
    multipartFetchMock.mockReset();
    jest.restoreAllMocks();
  });

  it('uploads an Expo File with auth and a pronunciation practice session', async () => {
    multipartFetchMock.mockResolvedValue(jsonResponse({ id: 'utterance-1' }));
    const globalFetchMock = jest.spyOn(globalThis, 'fetch');
    const appendMock = jest.spyOn(FormData.prototype, 'append');
    const client = new BenmaApiClient('http://api.test');
    client.setToken('opaque-token');

    await client.uploadUtterance('file:///recordings/speech.m4a', 'audio/mp4', 'practice-1');

    expect(globalFetchMock).not.toHaveBeenCalled();
    expect(multipartFetchMock).toHaveBeenCalledTimes(1);
    const [url, init] = multipartFetchMock.mock.calls[0]!;
    expect(url).toBe('http://api.test/v1/utterances');
    expect(init?.method).toBe('POST');
    expect(init?.body).toBeInstanceOf(FormData);
    const headers = new Headers(init?.headers);
    expect(headers.get('Authorization')).toBe('Bearer opaque-token');
    expect(headers.get('Content-Type')).toBeNull();

    const filePart = appendMock.mock.calls.find(([name]) => name === 'file');
    expect(filePart?.[1]).toBeInstanceOf(File);
    expect(filePart?.[1]).toMatchObject({ uri: 'file:///recordings/speech.m4a' });
    expect(filePart).toHaveLength(2);
    expect(appendMock).toHaveBeenCalledWith('practice_session_id', 'practice-1');
  });

  it('omits the optional practice session for a Free Talk upload', async () => {
    multipartFetchMock.mockResolvedValue(jsonResponse({ id: 'utterance-1' }));
    const appendMock = jest.spyOn(FormData.prototype, 'append');
    const client = new BenmaApiClient('http://api.test');

    await client.uploadUtterance('file:///recordings/speech.m4a', 'audio/mp4');

    expect(appendMock).toHaveBeenCalledWith('file', expect.any(File));
    expect(appendMock.mock.calls.some(([name]) => name === 'practice_session_id')).toBe(false);
  });

  it('normalizes failed multipart uploads through ApiError', async () => {
    multipartFetchMock.mockResolvedValue(
      jsonResponse(
        {
          error: {
            code: 'upload_rejected',
            message: 'recording rejected',
            retryable: false,
            request_id: 'request-upload-1',
          },
        },
        422,
      ),
    );
    const client = new BenmaApiClient('http://api.test');

    await expect(
      client.uploadUtterance('file:///recordings/speech.m4a', 'audio/mp4'),
    ).rejects.toMatchObject({
      code: 'upload_rejected',
      message: 'recording rejected',
      retryable: false,
      requestId: 'request-upload-1',
    });
  });

  it('surfaces multipart transport failures to the existing workflow handler', async () => {
    const failure = new TypeError('native multipart transport failed');
    multipartFetchMock.mockRejectedValue(failure);
    const client = new BenmaApiClient('http://api.test');

    await expect(
      client.uploadUtterance('file:///recordings/speech.m4a', 'audio/mp4'),
    ).rejects.toBe(failure);
  });

  it('sends the opaque bearer token and no semantic perception hints', async () => {
    const fetchMock = jest.spyOn(globalThis, 'fetch').mockResolvedValue(
      jsonResponse({
        id: 'run-1',
        transcript: '你好',
      }),
    );
    const client = new BenmaApiClient('http://api.test/');
    client.setToken('opaque-token');
    await client.createPerception('utterance-1');

    const [url, init] = fetchMock.mock.calls[0]!;
    expect(url).toBe('http://api.test/v1/utterances/utterance-1/perceptions');
    const headers = new Headers(init?.headers);
    expect(headers.get('Authorization')).toBe('Bearer opaque-token');
    expect(JSON.parse(String(init?.body))).toEqual({});
    expect(String(init?.body)).not.toMatch(/target|prompt|context|pinyin/);
  });

  it('maps the stable server error without exposing response internals', async () => {
    jest.spyOn(globalThis, 'fetch').mockResolvedValue(
      jsonResponse(
        {
          error: {
            code: 'provider_timeout',
            message: 'provider timed out',
            retryable: true,
            request_id: 'request-1',
          },
        },
        504,
      ),
    );
    const client = new BenmaApiClient('http://api.test');
    await expect(client.createPerception('utterance-1')).rejects.toMatchObject({
      code: 'provider_timeout',
      retryable: true,
      requestId: 'request-1',
    });
  });

  it('distinguishes reuse from an explicit pronunciation rerun', async () => {
    const fetchMock = jest.spyOn(globalThis, 'fetch').mockResolvedValue(jsonResponse({}));
    const client = new BenmaApiClient('http://api.test');
    await client.analyzePronunciation('attempt-1');
    await client.analyzePronunciation('attempt-1', true);
    expect(JSON.parse(String(fetchMock.mock.calls[0]?.[1]?.body))).toEqual({
      reuse_existing: true,
      rerun_provider: false,
      rerun_acoustics: false,
      rerun_alignment: false,
    });
    expect(JSON.parse(String(fetchMock.mock.calls[1]?.[1]?.body))).toEqual({
      reuse_existing: false,
      rerun_provider: true,
      rerun_acoustics: true,
      rerun_alignment: true,
    });
  });

  it('keeps reference playback authenticated', () => {
    const client = new BenmaApiClient('http://api.test/');
    expect(client.authenticatedHeaders()).toBeUndefined();
    client.setToken('opaque-token');
    expect(client.authenticatedHeaders()).toEqual({ Authorization: 'Bearer opaque-token' });
    expect(client.absoluteUrl('/v1/reference-speech/asset/audio')).toBe(
      'http://api.test/v1/reference-speech/asset/audio',
    );
  });

  it('uses the public persisted-conversation contracts for Free Talk', async () => {
    const fetchMock = jest.spyOn(globalThis, 'fetch').mockResolvedValue(jsonResponse({}));
    const client = new BenmaApiClient('http://api.test');

    await client.createConversation();
    await client.listConversationTurns('conversation-1');
    await client.addConversationUserTurn('conversation-1', 'utterance-1', 'perception-1');

    expect(fetchMock.mock.calls[0]?.[0]).toBe('http://api.test/v1/conversations');
    expect(JSON.parse(String(fetchMock.mock.calls[0]?.[1]?.body))).toEqual({});
    expect(fetchMock.mock.calls[1]?.[0]).toBe(
      'http://api.test/v1/conversations/conversation-1/turns',
    );
    expect(fetchMock.mock.calls[2]?.[0]).toBe(
      'http://api.test/v1/conversations/conversation-1/user-turns',
    );
    expect(JSON.parse(String(fetchMock.mock.calls[2]?.[1]?.body))).toEqual({
      utterance_id: 'utterance-1',
      perception_run_id: 'perception-1',
    });
  });

  it('downloads assistant speech bytes through authenticated Expo fetch', async () => {
    const bytes = new Uint8Array([0x52, 0x49, 0x46, 0x46]);
    multipartFetchMock.mockResolvedValue({
      ...jsonResponse({}),
      bytes: async () => bytes,
    });
    const globalFetchMock = jest.spyOn(globalThis, 'fetch');
    const client = new BenmaApiClient('http://api.test');
    client.setToken('opaque-token');

    await expect(
      client.downloadAssistantSpeech('/v1/assistant-speeches/speech-1/audio'),
    ).resolves.toEqual(bytes);

    expect(globalFetchMock).not.toHaveBeenCalled();
    const [url, init] = multipartFetchMock.mock.calls[0]!;
    expect(url).toBe('http://api.test/v1/assistant-speeches/speech-1/audio');
    expect(new Headers(init?.headers).get('Authorization')).toBe('Bearer opaque-token');
  });

  it('normalizes a failed authenticated speech download without exposing its response body', async () => {
    multipartFetchMock.mockResolvedValue(
      jsonResponse(
        {
          error: {
            code: 'assistant_speech_unavailable',
            message: 'speech unavailable',
            retryable: true,
            request_id: 'request-speech-1',
          },
        },
        503,
      ),
    );
    const client = new BenmaApiClient('http://api.test');
    client.setToken('opaque-token');

    await expect(
      client.downloadAssistantSpeech('/v1/assistant-speeches/speech-1/audio'),
    ).rejects.toMatchObject({
      code: 'assistant_speech_unavailable',
      message: 'speech unavailable',
      retryable: true,
      requestId: 'request-speech-1',
    });
  });
});

describe('learner error messages', () => {
  it('states that preserved audio can be retried after provider failure', () => {
    const message = errorMessage(new ApiError('provider_unavailable', 'internal', true));
    expect(message).toContain('recording is safe');
  });

  it('maps network failures separately', () => {
    expect(errorMessage(new TypeError('fetch failed'))).toContain('Network connection failed');
  });
});

it('requests TTS using only a persisted generation identity', async () => {
  const fetchMock = jest.spyOn(globalThis, 'fetch').mockResolvedValue(jsonResponse({}));
  const client = new BenmaApiClient('http://api.test');
  await client.createAssistantSpeech('generation-1');
  expect(fetchMock).toHaveBeenCalledWith('http://api.test/v1/assistant-generations/generation-1/speech',
    expect.objectContaining({ method: 'POST', body: '{}' }));
  jest.restoreAllMocks();
});

it('uses the authenticated bytes transport for reference speech too', async () => {
  multipartFetchMock.mockResolvedValue({ ...jsonResponse({}), bytes: async () => new Uint8Array([1, 2]) });
  const client = new BenmaApiClient('http://api.test');
  client.setToken('reference-test-token');
  await client.downloadAudio('/v1/reference-speech/reference-1/audio');
  const [url, init] = multipartFetchMock.mock.calls.at(-1)!;
  expect(url).toBe('http://api.test/v1/reference-speech/reference-1/audio');
  expect(new Headers(init.headers).get('Authorization')).toBe('Bearer reference-test-token');
  for (const invalid of ['https://elsewhere.test/audio', '/v1/reference-speech/ref/audio?token=secret', '//elsewhere.test/audio']) {
    await expect(client.downloadAudio(invalid)).rejects.toThrow('Invalid protected audio path');
  }
});

it('streams authoritative meaning before the reply across split UTF-8 chunks', async () => {
  const { TextEncoder, TextDecoder } = jest.requireActual('util');
  const originalDecoder = globalThis.TextDecoder;
  globalThis.TextDecoder = TextDecoder;
  const heardId = 'perception-1';
  const encoder = new TextEncoder();
  const meaning = encoder.encode(JSON.stringify({ type: 'interpretation', interpretation: {
    perception_run_id: heardId, decision: 'infer', inferred_text: '你好，今天我去北京。',
  } }) + '\n');
  const reply = encoder.encode(JSON.stringify({ type: 'complete', result: {
    perception_run_id: heardId, assistant_turn: { assistant_text: '你好！' },
  } }) + '\n');
  let finish!: (value: { value: Uint8Array; done: boolean }) => void;
  const read = jest.fn()
    .mockResolvedValueOnce({ value: meaning.slice(0, meaning.length - 5), done: false })
    .mockResolvedValueOnce({ value: meaning.slice(meaning.length - 5), done: false })
    .mockImplementationOnce(() => new Promise((resolve) => { finish = resolve; }));
  const cancel = jest.fn().mockResolvedValue(undefined);
  multipartFetchMock.mockResolvedValue({ ok: true, status: 200, body: { getReader: () => ({ read, cancel }) } });
  const interpretation = jest.fn();
  try {
    const client = new BenmaApiClient('http://api.test');
    const pending = client.addConversationUserTurn('c', 'u', heardId, interpretation);
    for (let i = 0; i < 15; i++) await Promise.resolve();
    expect(interpretation).toHaveBeenCalledWith(expect.objectContaining({ inferred_text: '你好，今天我去北京。' }));
    finish({ value: reply, done: false });
    expect(await pending).toMatchObject({ assistant_turn: { assistant_text: '你好！' } });
    expect(cancel).toHaveBeenCalledTimes(1);
    expect(multipartFetchMock.mock.calls.at(-1)![0]).toBe('http://api.test/v1/conversations/c/user-turns/stream');
  } finally { globalThis.TextDecoder = originalDecoder; multipartFetchMock.mockReset(); }
});

it('treats truncated and failed conversation streams as response failures without retrying provider work', async () => {
  const { TextEncoder, TextDecoder } = jest.requireActual('util');
  const originalDecoder = globalThis.TextDecoder;
  globalThis.TextDecoder = TextDecoder;
  try {
    for (const event of ['', JSON.stringify({ type: 'error', error_code: 'provider_timeout' }) + '\n']) {
      const cancel = jest.fn().mockResolvedValue(undefined);
      multipartFetchMock.mockResolvedValue({ ok: true, status: 200, body: { getReader: () => ({
        read: jest.fn().mockResolvedValue({ value: new TextEncoder().encode(event), done: true }), cancel,
      }) } });
      await expect(new BenmaApiClient('http://api.test').addConversationUserTurn('c', 'u', 'p', () => {})).rejects.toThrow(/Conversation/);
      expect(cancel).toHaveBeenCalledTimes(1);
    }
    expect(multipartFetchMock).toHaveBeenCalledTimes(2);
  } finally { globalThis.TextDecoder = originalDecoder; multipartFetchMock.mockReset(); }
});

it('requests transcript analysis using only an owned perception ID, then retrieves the immutable result', async () => {
  const fetchMock = jest.spyOn(globalThis, 'fetch').mockResolvedValue(jsonResponse({ id: 'analysis' }));
  try {
    const client = new BenmaApiClient('http://api.test');
    client.setToken('opaque-token');
    await client.analyzePerceivedSpeech('perception');
    expect(fetchMock.mock.calls[0]![0]).toBe('http://api.test/v1/perceptions/perception/speech-analysis');
    expect(fetchMock.mock.calls[0]![1]?.body).toBe('{}');
    expect(new Headers(fetchMock.mock.calls[0]![1]?.headers).get('Authorization')).toBe('Bearer opaque-token');
    await client.getPerceivedSpeechAnalysis('analysis');
    expect(fetchMock.mock.calls[1]![0]).toBe('http://api.test/v1/perceived-speech-analyses/analysis');
  } finally { fetchMock.mockRestore(); }
});

it('requests canonical audio only by authenticated utterance identity and rejects paths', async () => {
  multipartFetchMock.mockResolvedValue({ ...jsonResponse({}), bytes: async () => new Uint8Array([1, 2]) });
  const client = new BenmaApiClient('http://api.test');
  client.setToken('canonical-test-token');
  await client.downloadCanonicalRecording('utterance-1');
  const [url, init] = multipartFetchMock.mock.calls.at(-1)!;
  expect(url).toBe('http://api.test/v1/utterances/utterance-1/audio?canonical=true');
  expect(new Headers(init.headers).get('Authorization')).toBe('Bearer canonical-test-token');
  for (const invalid of ['../other', 'x/audio?path=secret', 'https://other.test']) {
    await expect(client.downloadCanonicalRecording(invalid)).rejects.toThrow('Invalid protected audio path');
  }
});
