import { useCallback, useEffect, useState } from 'react';

import { api } from '../api/client';
import { errorMessage } from '../api/errors';
import type { Utterance } from '../api/types';
import { PlaybackButton } from '../audio/PlaybackButton';
import {
  Body,
  Button,
  Card,
  ErrorMessage,
  EvidencePanel,
  EvidenceRow,
  Heading,
  Screen,
} from '../components/Ui';

export default function HistoryScreen() {
  const [utterances, setUtterances] = useState<Utterance[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setUtterances(await api.listUtterances());
    } catch (caught) {
      setError(errorMessage(caught));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    let active = true;
    void api
      .listUtterances()
      .then((items) => {
        if (active) setUtterances(items);
      })
      .catch((caught: unknown) => {
        if (active) setError(errorMessage(caught));
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, []);

  return (
    <Screen>
      <Heading>History / Development</Heading>
      <Body>Recent immutable utterances owned by this development account.</Body>
      <Button secondary label="Refresh" loading={loading} onPress={() => void load()} />
      <ErrorMessage message={error} />
      {!loading && utterances.length === 0 && <Body>No recordings yet.</Body>}
      {utterances.map((utterance, index) => (
        <Card key={utterance.id}>
          <Body>Recording {utterances.length - index}</Body>
          <PlaybackButton
            label="Play saved recording"
            uri={api.audioUrl(utterance)}
          />
          <EvidencePanel title="Audio evidence">
            <EvidenceRow label="Utterance ID" value={utterance.id} />
            <EvidenceRow label="Created" value={utterance.created_at} />
            <EvidenceRow label="Duration" value={utterance.original_audio.duration_seconds} />
            <EvidenceRow label="Original SHA-256" value={utterance.original_audio.sha256} />
            <EvidenceRow label="Canonical sample rate" value={utterance.canonical_audio.sample_rate_hz} />
          </EvidencePanel>
        </Card>
      ))}
    </Screen>
  );
}
