// Native recording files remain managed by Expo/the existing cache policy.
export function retainRecordingUri(_uri: string): () => void {
  return () => {};
}
