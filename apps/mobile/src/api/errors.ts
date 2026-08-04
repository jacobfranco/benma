import { ApiError } from '@/api/client';

const MESSAGES: Record<string, string> = {
  authentication_error: 'Your development session has expired. Sign in again.',
  authorization_error: 'That recording or result is no longer available.',
  invalid_audio: 'The recording could not be read. Please record it again.',
  provider_unavailable: 'Speech analysis is temporarily unavailable. Your recording is safe.',
  provider_timeout: 'Speech analysis took too long. Your recording is safe; retry analysis.',
  provider_rejected_request: 'The speech provider could not analyze this recording.',
  provider_malformed_response: 'The provider returned evidence Benma could not interpret.',
  analysis_unsupported: 'This analysis mode is not configured on the backend.',
  validation_error: 'Please check the information and try again.',
};

export function errorMessage(error: unknown): string {
  if (error instanceof ApiError) return MESSAGES[error.code] ?? error.message;
  if (error instanceof TypeError) return 'Network connection failed. Your local recording is safe.';
  if (error instanceof Error) return error.message;
  return 'Something went wrong. Please try again.';
}
