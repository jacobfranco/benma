import { ApiError, BenmaApiClient } from '@/api/client';
import { errorMessage } from '@/api/errors';

function jsonResponse(payload: unknown, status = 200): Response {
  return {
    ok: status >= 200 && status < 300,
    status,
    json: async () => payload,
  } as Response;
}

describe('API client', () => {
  afterEach(() => jest.restoreAllMocks());

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
