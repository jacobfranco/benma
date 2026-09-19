// The capture hook, upload, and local player each hold a lease while using the URL.
const owners = new Map<string, number>();

export function retainRecordingUri(uri: string): () => void {
  if (!uri.startsWith('blob:')) return () => {};
  owners.set(uri, (owners.get(uri) ?? 0) + 1);
  let released = false;
  return () => {
    if (released) return;
    released = true;
    const remaining = (owners.get(uri) ?? 1) - 1;
    if (remaining > 0) owners.set(uri, remaining);
    else {
      owners.delete(uri);
      URL.revokeObjectURL(uri);
    }
  };
}
