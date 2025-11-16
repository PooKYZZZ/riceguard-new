import '@testing-library/jest-dom';

// Silence/spy alerts for assertions
beforeAll(() => {
  jest.spyOn(window, 'alert').mockImplementation(() => {});
});

// Clean mocks between tests
afterEach(() => {
  jest.clearAllMocks();
});
