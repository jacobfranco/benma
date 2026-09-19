import type { BenmaApiClient } from '@/api/client';
import type { ConversationTurn } from '@/api/types';
import { measureSpeech } from '@/speech/workflow';

// Speech follows a durable assistant turn. Client-supplied text is never accepted.
export function requestTurnSpeech(
  client: Pick<BenmaApiClient, 'createAssistantSpeech'>,
  assistant: ConversationTurn,
) {
  const generationId = assistant.assistant_generation_run_id;
  if (assistant.role !== 'assistant' || !generationId) {
    throw new Error('Audio unavailable for this turn');
  }
  return measureSpeech('assistant TTS', () => client.createAssistantSpeech(generationId));
}
