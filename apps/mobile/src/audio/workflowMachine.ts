export type WorkflowPhase =
  | 'idle'
  | 'permission_required'
  | 'recording'
  | 'recorded'
  | 'uploading'
  | 'uploaded'
  | 'analyzing'
  | 'success'
  | 'failure';

export interface WorkflowState<Result> {
  phase: WorkflowPhase;
  recordingUri: string | null;
  durationMillis: number;
  utteranceId: string | null;
  result: Result | null;
  error: string | null;
}

export type WorkflowAction<Result> =
  | { type: 'PERMISSION_REQUIRED' }
  | { type: 'START_RECORDING' }
  | { type: 'RECORDED'; uri: string; durationMillis: number }
  | { type: 'UPLOAD' }
  | { type: 'UPLOADED'; utteranceId: string }
  | { type: 'ANALYZE' }
  | { type: 'SUCCEEDED'; result: Result }
  | { type: 'FAILED'; message: string }
  | { type: 'RETRY_ANALYSIS' }
  | { type: 'RESET' };

export function initialWorkflowState<Result>(): WorkflowState<Result> {
  return {
    phase: 'idle',
    recordingUri: null,
    durationMillis: 0,
    utteranceId: null,
    result: null,
    error: null,
  };
}

export function workflowReducer<Result>(
  state: WorkflowState<Result>,
  action: WorkflowAction<Result>,
): WorkflowState<Result> {
  switch (action.type) {
    case 'PERMISSION_REQUIRED':
      return { ...state, phase: 'permission_required', error: null };
    case 'START_RECORDING':
      return { ...initialWorkflowState<Result>(), phase: 'recording' };
    case 'RECORDED':
      return {
        ...state,
        phase: 'recorded',
        recordingUri: action.uri,
        durationMillis: action.durationMillis,
        error: null,
      };
    case 'UPLOAD':
      return { ...state, phase: 'uploading', error: null };
    case 'UPLOADED':
      return { ...state, phase: 'uploaded', utteranceId: action.utteranceId, error: null };
    case 'ANALYZE':
    case 'RETRY_ANALYSIS':
      if (!state.utteranceId) return { ...state, phase: 'failure', error: 'No upload to analyze' };
      return { ...state, phase: 'analyzing', error: null };
    case 'SUCCEEDED':
      return { ...state, phase: 'success', result: action.result, error: null };
    case 'FAILED':
      return { ...state, phase: 'failure', error: action.message };
    case 'RESET':
      return initialWorkflowState<Result>();
    default:
      return state;
  }
}
