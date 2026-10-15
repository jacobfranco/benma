// Learner presentation only: use existing projected availability, never strict
// eligibility or a new coverage/readability threshold. Diagnostics stay in details.
export const pitchFeedbackCopy = {
  limited: 'Pitch detail is limited.',
  unavailable: "Pitch couldn't be measured reliably.",
} as const;

export function learnerPitchMessage(evidence: readonly { hasPitch: boolean }[]): string | null {
  if (!evidence.some(e => e.hasPitch)) return pitchFeedbackCopy.unavailable;
  // A whole constituent has no retained pitch. Grouped timing is one constituent;
  // do not invent character-level availability within that accepted span.
  return evidence.some(e => !e.hasPitch) ? pitchFeedbackCopy.limited : null;
}
