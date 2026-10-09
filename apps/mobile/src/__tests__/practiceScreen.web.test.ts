import './practiceScreen.test';
// Test renderer cannot mount ReactDOM portals; browser smoke covers real modal behavior.
jest.mock('react-native-web/dist/exports/Modal', () => ({
  __esModule: true, default: ({ children }: { children: unknown }) => children,
}));
jest.mock('react-native-safe-area-context', () => ({ SafeAreaView: jest.requireActual('react-native-web').View }));
