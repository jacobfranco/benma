import './developmentAuth.test';
jest.mock('react-native-safe-area-context', () => ({ SafeAreaView: jest.requireActual('react-native-web').View }));
globalThis.fetch = jest.fn();
