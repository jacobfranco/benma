import './pronunciationChunks.test';
// Real portal/keyboard/focus behavior is covered by the offline browser review.
jest.mock('react-native-web/dist/exports/Modal', () => ({
  __esModule: true, default: ({ children }: { children: unknown }) => children,
}));
