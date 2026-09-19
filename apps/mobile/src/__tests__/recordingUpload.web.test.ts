import { BenmaApiClient } from '@/api/client';
import { retainRecordingUri } from '@/audio/recordingUri';
import { submitSpeech, type SpeechCheckpoint, type SpeechMode } from '@/speech/workflow';

// Importing the client/upload graph on web must not evaluate native file APIs.
jest.mock('expo-file-system', () => { throw new Error('Native filesystem imported on web'); });
jest.mock('expo/fetch', () => ({ fetch: () => { throw new Error('Native upload fetch used on web'); } }));

const uri = 'blob:http://localhost:8081/recording-test';
let client: BenmaApiClient;
let fetchMock: jest.Mock;
let releaseCapture: () => void;
const revoke = jest.fn();

function readBlob(blob: Blob): Promise<ArrayBuffer> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result as ArrayBuffer);
    reader.onerror = reject;
    reader.readAsArrayBuffer(blob);
  });
}

beforeAll(() => {
  // jsdom has browser Blob/FormData validation but not these newer browser methods.
  Object.defineProperty(Blob.prototype, 'arrayBuffer', { configurable: true,
    value(this: Blob) { return readBlob(this); } });
  Object.defineProperty(URL, 'revokeObjectURL', { configurable: true, value: revoke });
});

beforeEach(() => {
  jest.clearAllMocks();
  jest.spyOn(console, 'info').mockImplementation(() => {});
  client = new BenmaApiClient('http://api.test');
  client.setToken('opaque-token');
  releaseCapture = retainRecordingUri(uri);
  fetchMock = jest.fn();
  globalThis.fetch = fetchMock;
});

afterEach(() => { releaseCapture(); jest.restoreAllMocks(); });

function recordingResponse(blob: Blob) {
  return { ok: true, blob: async () => blob };
}
function uploadResponse() {
  return { ok: true, status: 201, headers: new Headers(), json: async () => ({ id: 'utterance-1' }) };
}

it.each([
  ['audio/webm', 'webm', undefined],
  ['audio/webm;codecs=opus', 'webm', 'practice-1'],
  ['audio/mp4;codecs=mp4a.40.2', 'm4a', undefined],
  ['audio/ogg;codecs=opus', 'ogg', undefined],
])('uploads real browser %s bytes as %s with bearer auth', async (mime, extension, practiceId) => {
  const blob = new Blob([new Uint8Array([1, 2, 3, 4])], { type: mime });
  fetchMock.mockResolvedValueOnce(recordingResponse(blob)).mockResolvedValueOnce(uploadResponse());

  await client.uploadUtterance(uri, 'audio/webm', practiceId);

  expect(fetchMock).toHaveBeenCalledTimes(2);
  expect(fetchMock).toHaveBeenNthCalledWith(1, uri); // Conversion has no bearer header.
  const [url, init] = fetchMock.mock.calls[1]!;
  expect(url).toBe('http://api.test/v1/utterances');
  expect(init.method).toBe('POST');
  expect(init.headers.get('Authorization')).toBe('Bearer opaque-token');
  expect(init.headers.has('Content-Type')).toBe(false); // Browser owns the multipart boundary.
  expect(init.body).toBeInstanceOf(FormData);
  const file = init.body.get('file') as File;
  expect(file).toBeInstanceOf(Blob);
  expect(file).toBeInstanceOf(File);
  expect(file.name).toBe(`recording.${extension}`);
  expect(file.type).toBe(mime);
  expect(new Uint8Array(await readBlob(file))).toEqual(new Uint8Array([1, 2, 3, 4]));
  expect(init.body.get('practice_session_id')).toBe(practiceId ?? null);
  expect(revoke).not.toHaveBeenCalled(); // Still owned by capture for retry/local replay.
});

it('detects the container when the browser omits MIME instead of guessing from the caller', async () => {
  fetchMock.mockResolvedValueOnce(recordingResponse(new Blob(['\x00\x00\x00\x18ftypM4A '])))
    .mockResolvedValueOnce(uploadResponse());
  await client.uploadUtterance(uri, 'audio/webm');
  const file = fetchMock.mock.calls[1]![1].body.get('file') as File;
  expect(file.type).toBe('audio/mp4');
  expect(file.name).toBe('recording.m4a');
});

it.each(['fetch', 'http', 'blob', 'empty', 'mime'])('keeps %s conversion failure at the upload layer and permits retry', async (stage) => {
  const failure = new Error(`Cannot read ${uri}`);
  if (stage === 'fetch') fetchMock.mockRejectedValueOnce(failure);
  else if (stage === 'http') fetchMock.mockResolvedValueOnce({ ok: false });
  else if (stage === 'blob') fetchMock.mockResolvedValueOnce({ ok: true, blob: async () => { throw failure; } });
  else fetchMock.mockResolvedValueOnce(recordingResponse(
    new Blob(stage === 'empty' ? [] : ['data'], { type: stage === 'mime' ? 'text/plain' : 'audio/webm' }),
  ));
  const perception = jest.spyOn(client, 'createPerception').mockResolvedValue({ id: 'p', transcript: '你好' } as never);
  jest.spyOn(client, 'getPerceivedReadings').mockRejectedValue(new Error('optional readings'));
  jest.spyOn(client, 'analyzePerceivedSpeech').mockRejectedValue(new Error('unused analysis'));
  const checkpoint: SpeechCheckpoint = { uri };
  await expect(submitSpeech(client, { responseMode: 'none' }, checkpoint, 'audio/webm', () => {}, () => {}))
    .rejects.toMatchObject({ stage: 'upload', message: 'Upload failed. Try sending the recording again.' });
  expect(checkpoint.utteranceId).toBeUndefined();
  expect(perception).not.toHaveBeenCalled();
  expect(fetchMock).toHaveBeenCalledTimes(1);
  expect(revoke).not.toHaveBeenCalled();
  expect(JSON.stringify(jest.mocked(console.info).mock.calls)).not.toContain(uri);
  fetchMock.mockResolvedValueOnce(recordingResponse(new Blob(['audio'], { type: 'audio/webm' })))
    .mockResolvedValueOnce(uploadResponse());
  await submitSpeech(client, { responseMode: 'none' }, checkpoint, 'audio/webm', () => {}, () => {});
  expect(checkpoint.utteranceId).toBe('utterance-1');
});

it('sanitizes conversion errors even outside the shared speech workflow', async () => {
  fetchMock.mockRejectedValue(new Error(`Failed to read ${uri}`));
  await expect(client.uploadUtterance(uri, 'audio/webm')).rejects.toThrow(
    'Recording could not be prepared for upload. Try sending it again.',
  );
});

it('keeps the object URL alive through an in-flight upload after capture and replay release it', async () => {
  const releaseReplay = retainRecordingUri(uri);
  let finish!: (value: ReturnType<typeof uploadResponse>) => void;
  fetchMock.mockResolvedValueOnce(recordingResponse(new Blob(['audio'], { type: 'audio/webm' })))
    .mockImplementationOnce(() => new Promise((resolve) => { finish = resolve; }));
  const pending = client.uploadUtterance(uri, 'audio/webm');
  for (let i = 0; i < 10; i++) await Promise.resolve();
  expect(fetchMock).toHaveBeenCalledTimes(2);
  releaseCapture(); releaseReplay();
  expect(revoke).not.toHaveBeenCalled();
  finish(uploadResponse());
  await pending;
  expect(revoke).toHaveBeenCalledTimes(1);
  expect(revoke).toHaveBeenCalledWith(uri);
});

it.each<SpeechMode>([
  { responseMode: 'conversation', conversationId: 'c' },
  { responseMode: 'none' },
  { responseMode: 'none', targetId: 'target' },
])('uses the browser upload once across retries for $responseMode / $targetId', async (mode) => {
  fetchMock.mockResolvedValueOnce(recordingResponse(new Blob(['audio'], { type: 'audio/webm' })))
    .mockResolvedValueOnce(uploadResponse());
  jest.spyOn(client, 'createPerception').mockRejectedValueOnce(new Error('retry perception'))
    .mockResolvedValue({ id: 'perception', transcript: '你好' } as never);
  jest.spyOn(client, 'getPerceivedReadings').mockRejectedValue(new Error('optional readings'));
  jest.spyOn(client, 'analyzePerceivedSpeech').mockRejectedValue(new Error('optional analysis'));
  jest.spyOn(client, 'createAttempt').mockResolvedValue({ id: 'attempt' } as never);
  jest.spyOn(client, 'analyzePronunciation').mockResolvedValue({} as never);
  jest.spyOn(client, 'addConversationUserTurn').mockResolvedValue({ id: 'turn' } as never);
  const checkpoint: SpeechCheckpoint = { uri };
  await expect(submitSpeech(client, mode, checkpoint, 'audio/webm', () => {}, () => {}))
    .rejects.toMatchObject({ stage: 'perception' });
  await submitSpeech(client, mode, checkpoint, 'audio/webm', () => {}, () => {});
  expect(fetchMock).toHaveBeenCalledTimes(2); // One blob conversion, one utterance POST.
  expect(client.createPerception).toHaveBeenCalledTimes(2);
});
