import './toneFeedbackWorkspace.test';
jest.mock('react-native-web/dist/exports/Modal', () => ({
  __esModule: true, default: ({ children }: { children: unknown }) => children,
}));
