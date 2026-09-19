export interface RecordingUploadSource {
  body: FormData;
  fetch: (input: string, init?: RequestInit) => Promise<Response>;
  release: () => void;
}
