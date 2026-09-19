import './freeTalkScreen.test';
jest.mock('react-native-safe-area-context', () => ({ SafeAreaView: jest.requireActual('react-native-web').View }));
