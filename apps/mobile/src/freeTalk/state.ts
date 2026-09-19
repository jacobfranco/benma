import type { ConversationTurn } from '@/api/types';

// Reconciliation stores authoritative server records, not a separate semantic history.
export function reconcileTurns(current: ConversationTurn[], incoming: ConversationTurn[]): ConversationTurn[] {
  const byId = new Map(current.map((turn) => [turn.id, turn]));
  for (const turn of incoming) byId.set(turn.id, turn);
  return [...byId.values()].sort((a, b) => a.sequence_number - b.sequence_number);
}
