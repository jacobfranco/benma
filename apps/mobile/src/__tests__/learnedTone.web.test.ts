import './learnedTone.test';
// Test renderer cannot mount DOM portals; keep the established web-test convention.
jest.mock('react-native-web/dist/exports/Modal', () => ({
  __esModule: true, default: ({ children }: { children: unknown }) => children,
}));
