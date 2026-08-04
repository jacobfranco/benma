import {
  initialWorkflowState,
  workflowReducer,
  type WorkflowState,
} from '@/audio/workflowMachine';

interface Result {
  transcript: string;
}

function reduce(state: WorkflowState<Result>, action: Parameters<typeof workflowReducer<Result>>[1]) {
  return workflowReducer(state, action);
}

describe('recording workflow state machine', () => {
  it('models record, upload, and analysis explicitly', () => {
    let state = initialWorkflowState<Result>();
    state = reduce(state, { type: 'START_RECORDING' });
    expect(state.phase).toBe('recording');
    state = reduce(state, { type: 'RECORDED', uri: 'file:///speech.m4a', durationMillis: 1200 });
    expect(state).toMatchObject({ phase: 'recorded', recordingUri: 'file:///speech.m4a' });
    state = reduce(state, { type: 'UPLOAD' });
    expect(state.phase).toBe('uploading');
    state = reduce(state, { type: 'UPLOADED', utteranceId: 'utterance-1' });
    expect(state.phase).toBe('uploaded');
    state = reduce(state, { type: 'ANALYZE' });
    expect(state.phase).toBe('analyzing');
    state = reduce(state, { type: 'SUCCEEDED', result: { transcript: '你好' } });
    expect(state).toMatchObject({ phase: 'success', result: { transcript: '你好' } });
  });

  it('retries provider analysis without losing the uploaded utterance', () => {
    let state: WorkflowState<Result> = {
      ...initialWorkflowState<Result>(),
      phase: 'uploaded',
      recordingUri: 'file:///speech.m4a',
      utteranceId: 'utterance-1',
    };
    state = reduce(state, { type: 'FAILED', message: 'provider offline' });
    expect(state.utteranceId).toBe('utterance-1');
    state = reduce(state, { type: 'RETRY_ANALYSIS' });
    expect(state).toMatchObject({ phase: 'analyzing', utteranceId: 'utterance-1' });
  });

  it('does not analyze before an upload exists', () => {
    const state = reduce(initialWorkflowState<Result>(), { type: 'ANALYZE' });
    expect(state).toMatchObject({ phase: 'failure', error: 'No upload to analyze' });
  });
});
