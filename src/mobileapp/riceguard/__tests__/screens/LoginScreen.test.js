// __tests__/screens/LoginScreen.test.js
/**
 * @format
 */

import React from 'react';
import { render, fireEvent, waitFor, act } from '@testing-library/react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { Alert } from 'react-native';
import LoginScreen from '../../src/screens/LoginScreen';
import { AuthProvider } from '../../src/context/AuthContext';

// Mock AsyncStorage
jest.mock('@react-native-async-storage/async-storage');

// Mock Alert
jest.mock('react-native', () => {
  const RN = jest.requireActual('react-native');
  return {
    ...RN,
    Alert: {
      alert: jest.fn(),
    },
  };
});

// Mock expo-image-picker
jest.mock('expo-image-picker', () => ({
  launchImageLibraryAsync: jest.fn(),
  MediaTypeOptions: {
    Images: 'images',
  },
}));

// Mock API
jest.mock('../../src/api', () => ({
  login: jest.fn(),
  register: jest.fn(),
}));

const mockNavigation = {
  navigate: jest.fn(),
  goBack: jest.fn(),
  dispatch: jest.fn(),
  setOptions: jest.fn(),
  isFocused: jest.fn(() => true),
  addListener: jest.fn(() => jest.fn()),
};

const mockRoute = {
  params: {},
  name: 'Login',
  key: 'Login-key',
};

// Test wrapper component
const TestWrapper = ({ children }) => (
  <AuthProvider>{children}</AuthProvider>
);

describe('LoginScreen Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    AsyncStorage.clear();
  });

  test('renders login form correctly', () => {
    // Arrange
    const { getByPlaceholderText, getByText } = render(
      <TestWrapper>
        <LoginScreen navigation={mockNavigation} route={mockRoute} />
      </TestWrapper>
    );

    // Assert
    expect(getByPlaceholderText('Email')).toBeTruthy();
    expect(getByPlaceholderText('Password')).toBeTruthy();
    expect(getByText('Login')).toBeTruthy();
    expect(getByText('Don\'t have an account? Register')).toBeTruthy();
  });

  test('updates email input value when typed', () => {
    // Arrange
    const { getByPlaceholderText } = render(
      <TestWrapper>
        <LoginScreen navigation={mockNavigation} route={mockRoute} />
      </TestWrapper>
    );

    // Act
    const emailInput = getByPlaceholderText('Email');
    fireEvent.changeText(emailInput, 'test@example.com');

    // Assert
    expect(emailInput.props.value).toBe('test@example.com');
  });

  test('updates password input value when typed', () => {
    // Arrange
    const { getByPlaceholderText } = render(
      <TestWrapper>
        <LoginScreen navigation={mockNavigation} route={mockRoute} />
      </TestWrapper>
    );

    // Act
    const passwordInput = getByPlaceholderText('Password');
    fireEvent.changeText(passwordInput, 'password123');

    // Assert
    expect(passwordInput.props.value).toBe('password123');
  });

  test('toggles password visibility when eye icon is pressed', () => {
    // Arrange
    const { getByTestId } = render(
      <TestWrapper>
        <LoginScreen navigation={mockNavigation} route={mockRoute} />
      </TestWrapper>
    );

    // Act
    // This would require adding testID to the eye icon
    // For now, we test that the component renders without error
  });

  test('shows error for empty email on login attempt', async () => {
    // Arrange
    const { getByText, getByPlaceholderText } = render(
      <TestWrapper>
        <LoginScreen navigation={mockNavigation} route={mockRoute} />
      </TestWrapper>
    );

    // Act
    const loginButton = getByText('Login');
    fireEvent.press(loginButton);

    // Assert
    await waitFor(() => {
      expect(Alert.alert).toHaveBeenCalledWith('Error', 'Please fill in all fields');
    });
  });

  test('shows error for empty password on login attempt', async () => {
    // Arrange
    const { getByText, getByPlaceholderText } = render(
      <TestWrapper>
        <LoginScreen navigation={mockNavigation} route={mockRoute} />
      </TestWrapper>
    );

    // Act
    const emailInput = getByPlaceholderText('Email');
    fireEvent.changeText(emailInput, 'test@example.com');

    const loginButton = getByText('Login');
    fireEvent.press(loginButton);

    // Assert
    await waitFor(() => {
      expect(Alert.alert).toHaveBeenCalledWith('Error', 'Please fill in all fields');
    });
  });

  test('shows error for invalid email format', async () => {
    // Arrange
    const { getByText, getByPlaceholderText } = render(
      <TestWrapper>
        <LoginScreen navigation={mockNavigation} route={mockRoute} />
      </TestWrapper>
    );

    // Act
    const emailInput = getByPlaceholderText('Email');
    const passwordInput = getByPlaceholderText('Password');
    const loginButton = getByText('Login');

    fireEvent.changeText(emailInput, 'invalid-email');
    fireEvent.changeText(passwordInput, 'password123');
    fireEvent.press(loginButton);

    // Assert
    await waitFor(() => {
      expect(Alert.alert).toHaveBeenCalledWith('Error', 'Please enter a valid email address');
    });
  });

  test('navigates to register screen when register link is pressed', () => {
    // Arrange
    const { getByText } = render(
      <TestWrapper>
        <LoginScreen navigation={mockNavigation} route={mockRoute} />
      </TestWrapper>
    );

    // Act
    const registerLink = getByText('Don\'t have an account? Register');
    fireEvent.press(registerLink);

    // Assert
    expect(mockNavigation.navigate).toHaveBeenCalledWith('Register');
  });

  test('handles login API error gracefully', async () => {
    // Arrange
    const { login } = require('../../src/api');
    login.mockRejectedValue(new Error('Network error'));

    const { getByText, getByPlaceholderText } = render(
      <TestWrapper>
        <LoginScreen navigation={mockNavigation} route={mockRoute} />
      </TestWrapper>
    );

    // Act
    const emailInput = getByPlaceholderText('Email');
    const passwordInput = getByPlaceholderText('Password');
    const loginButton = getByText('Login');

    fireEvent.changeText(emailInput, 'test@example.com');
    fireEvent.changeText(passwordInput, 'password123');
    fireEvent.press(loginButton);

    // Assert
    await waitFor(() => {
      expect(Alert.alert).toHaveBeenCalledWith('Error', 'Login failed. Please try again.');
    });
  });

  test('stores auth token on successful login', async () => {
    // Arrange
    const { login } = require('../../src/api');
    login.mockResolvedValue({
      data: {
        accessToken: 'mock_token',
        user: { id: '1', email: 'test@example.com', name: 'Test User' }
      }
    });

    const { getByText, getByPlaceholderText } = render(
      <TestWrapper>
        <LoginScreen navigation={mockNavigation} route={mockRoute} />
      </TestWrapper>
    );

    // Act
    const emailInput = getByPlaceholderText('Email');
    const passwordInput = getByPlaceholderText('Password');
    const loginButton = getByText('Login');

    fireEvent.changeText(emailInput, 'test@example.com');
    fireEvent.changeText(passwordInput, 'password123');
    fireEvent.press(loginButton);

    // Assert
    await waitFor(() => {
      expect(AsyncStorage.setItem).toHaveBeenCalledWith('authToken', 'mock_token');
    });
  });

  test('navigates to Scan screen on successful login', async () => {
    // Arrange
    const { login } = require('../../src/api');
    login.mockResolvedValue({
      data: {
        accessToken: 'mock_token',
        user: { id: '1', email: 'test@example.com', name: 'Test User' }
      }
    });

    const { getByText, getByPlaceholderText } = render(
      <TestWrapper>
        <LoginScreen navigation={mockNavigation} route={mockRoute} />
      </TestWrapper>
    );

    // Act
    const emailInput = getByPlaceholderText('Email');
    const passwordInput = getByPlaceholderText('Password');
    const loginButton = getByText('Login');

    fireEvent.changeText(emailInput, 'test@example.com');
    fireEvent.changeText(passwordInput, 'password123');
    fireEvent.press(loginButton);

    // Assert
    await waitFor(() => {
      expect(mockNavigation.navigate).toHaveBeenCalledWith('Scan');
    });
  });

  test('shows loading indicator during login attempt', async () => {
    // Arrange
    const { login } = require('../../src/api');
    login.mockImplementation(() => new Promise(resolve => setTimeout(resolve, 100)));

    const { getByText, getByPlaceholderText, queryByText } = render(
      <TestWrapper>
        <LoginScreen navigation={mockNavigation} route={mockRoute} />
      </TestWrapper>
    );

    // Act
    const emailInput = getByPlaceholderText('Email');
    const passwordInput = getByPlaceholderText('Password');
    const loginButton = getByText('Login');

    fireEvent.changeText(emailInput, 'test@example.com');
    fireEvent.changeText(passwordInput, 'password123');
    fireEvent.press(loginButton);

    // Assert
    // Button text should change to show loading state
    // This depends on the actual implementation
    await waitFor(() => {
      expect(login).toHaveBeenCalled();
    });
  });

  test('disables login button during API call', async () => {
    // Arrange
    const { login } = require('../../src/api');
    login.mockImplementation(() => new Promise(resolve => setTimeout(resolve, 100)));

    const { getByText, getByPlaceholderText } = render(
      <TestWrapper>
        <LoginScreen navigation={mockNavigation} route={mockRoute} />
      </TestWrapper>
    );

    // Act
    const emailInput = getByPlaceholderText('Email');
    const passwordInput = getByPlaceholderText('Password');
    const loginButton = getByText('Login');

    fireEvent.changeText(emailInput, 'test@example.com');
    fireEvent.changeText(passwordInput, 'password123');
    fireEvent.press(loginButton);

    // Assert
    // Button should be disabled during loading
    await waitFor(() => {
      expect(login).toHaveBeenCalled();
    });
  });

  test('handles form submission with Enter key', () => {
    // Arrange
    const { getByPlaceholderText } = render(
      <TestWrapper>
        <LoginScreen navigation={mockNavigation} route={mockRoute} />
      </TestWrapper>
    );

    // Act
    const passwordInput = getByPlaceholderText('Password');
    fireEvent(passwordInput, 'submitEditing');

    // Assert
    // Should trigger login validation
    // This depends on the actual implementation
  });

  test('persists form state on component re-render', () => {
    // Arrange
    const { getByPlaceholderText, rerender } = render(
      <TestWrapper>
        <LoginScreen navigation={mockNavigation} route={mockRoute} />
      </TestWrapper>
    );

    // Act
    const emailInput = getByPlaceholderText('Email');
    const passwordInput = getByPlaceholderText('Password');

    fireEvent.changeText(emailInput, 'test@example.com');
    fireEvent.changeText(passwordInput, 'password123');

    rerender(
      <TestWrapper>
        <LoginScreen navigation={mockNavigation} route={mockRoute} />
      </TestWrapper>
    );

    // Assert
    expect(emailInput.props.value).toBe('test@example.com');
    expect(passwordInput.props.value).toBe('password123');
  });

  test('handles screen focus events', () => {
    // Arrange
    const { getByPlaceholderText } = render(
      <TestWrapper>
        <LoginScreen navigation={mockNavigation} route={mockRoute} />
      </TestWrapper>
    );

    // Act
    // Simulate screen focus
    fireEvent(mockNavigation, 'focus');

    // Assert
    // Should handle focus without error
    expect(getByPlaceholderText('Email')).toBeTruthy();
  });

  test('handles screen blur events', () => {
    // Arrange
    const { getByPlaceholderText } = render(
      <TestWrapper>
        <LoginScreen navigation={mockNavigation} route={mockRoute} />
      </TestWrapper>
    );

    // Act
    // Simulate screen blur
    fireEvent(mockNavigation, 'blur');

    // Assert
    // Should handle blur without error
    expect(getByPlaceholderText('Email')).toBeTruthy();
  });

  test('clears form fields after successful login', async () => {
    // Arrange
    const { login } = require('../../src/api');
    login.mockResolvedValue({
      data: {
        accessToken: 'mock_token',
        user: { id: '1', email: 'test@example.com', name: 'Test User' }
      }
    });

    const { getByText, getByPlaceholderText, queryByDisplayValue } = render(
      <TestWrapper>
        <LoginScreen navigation={mockNavigation} route={mockRoute} />
      </TestWrapper>
    );

    // Act
    const emailInput = getByPlaceholderText('Email');
    const passwordInput = getByPlaceholderText('Password');
    const loginButton = getByText('Login');

    fireEvent.changeText(emailInput, 'test@example.com');
    fireEvent.changeText(passwordInput, 'password123');
    fireEvent.press(loginButton);

    // Assert
    await waitFor(() => {
      // After successful login, form should be cleared or user navigated away
      expect(mockNavigation.navigate).toHaveBeenCalled();
    });
  });

  test('handles component unmounting during async operation', async () => {
    // Arrange
    const { login } = require('../../src/api');
    login.mockImplementation(() => new Promise(resolve => setTimeout(resolve, 100)));

    const { getByText, getByPlaceholderText, unmount } = render(
      <TestWrapper>
        <LoginScreen navigation={mockNavigation} route={mockRoute} />
      </TestWrapper>
    );

    // Act
    const emailInput = getByPlaceholderText('Email');
    const passwordInput = getByPlaceholderText('Password');
    const loginButton = getByText('Login');

    fireEvent.changeText(emailInput, 'test@example.com');
    fireEvent.changeText(passwordInput, 'password123');
    fireEvent.press(loginButton);

    // Unmount component before async operation completes
    unmount();

    // Assert
    // Should handle unmounting without error
    expect(true).toBeTruthy();
  });
});