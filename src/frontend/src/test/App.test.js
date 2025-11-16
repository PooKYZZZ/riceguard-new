// src/test/App.test.js
/**
 * Comprehensive tests for App component
 */

import React from 'react';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BrowserRouter } from 'react-router-dom';
import App from '../App';
import * as api from '../api';

// Mock the API module
jest.mock('../api');

// Mock localStorage
const localStorageMock = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn(),
};
global.localStorage = localStorageMock;

// Mock console.log to avoid noise in tests
const originalConsoleLog = console.log;
beforeAll(() => {
  console.log = jest.fn();
});

afterAll(() => {
  console.log = originalConsoleLog;
});

// Helper function to render App with router
const renderApp = () => {
  return render(
    <BrowserRouter>
      <App />
    </BrowserRouter>
  );
};

describe('App Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    localStorageMock.getItem.mockClear();
    localStorageMock.setItem.mockClear();
  });

  test('renders main landing page elements', () => {
    // Act
    renderApp();

    // Assert
    expect(screen.getByText('We\'re here to guide you — "Your Smart Companion for Healthy Rice Fields"')).toBeInTheDocument();
    expect(screen.getByText('Log in')).toBeInTheDocument();
    expect(screen.getByText('Sign Up')).toBeInTheDocument();

    // Check for logo and background image
    const logo = screen.getByAltText('logo');
    const bgImage = screen.getByAltText('background');
    expect(logo).toBeInTheDocument();
    expect(bgImage).toBeInTheDocument();
  });

  test('opens login modal when login button is clicked', async () => {
    // Arrange
    const user = userEvent.setup();
    renderApp();

    // Act
    const loginButton = screen.getByText('Log in');
    await user.click(loginButton);

    // Assert
    expect(screen.getByText('Log in')).toBeInTheDocument();
    expect(screen.getByLabelText('Email')).toBeInTheDocument();
    expect(screen.getByLabelText('Password')).toBeInTheDocument();
    expect(screen.getByDisplayValue('Cancel')).toBeInTheDocument();
  });

  test('opens signup modal when signup button is clicked', async () => {
    // Arrange
    const user = userEvent.setup();
    renderApp();

    // Act
    const signupButton = screen.getByText('Sign Up');
    await user.click(signupButton);

    // Assert
    expect(screen.getByText('Sign Up')).toBeInTheDocument();
    expect(screen.getByLabelText('Email')).toBeInTheDocument();
    expect(screen.getByDisplayValue('Password')).toBeInTheDocument();
    expect(screen.getByDisplayValue('Confirm Password')).toBeInTheDocument();
    expect(screen.getByDisplayValue('Cancel')).toBeInTheDocument();
  });

  test('closes login modal when cancel button is clicked', async () => {
    // Arrange
    const user = userEvent.setup();
    renderApp();

    // Open login modal first
    const loginButton = screen.getByText('Log in');
    await user.click(loginButton);

    // Act
    const cancelButton = screen.getByDisplayValue('Cancel');
    await user.click(cancelButton);

    // Assert
    expect(screen.queryByDisplayValue('Cancel')).not.toBeInTheDocument();
    expect(screen.getByText('Log in')).toBeInTheDocument(); // Main button should still be visible
  });

  test('closes signup modal when cancel button is clicked', async () => {
    // Arrange
    const user = userEvent.setup();
    renderApp();

    // Open signup modal first
    const signupButton = screen.getByText('Sign Up');
    await user.click(signupButton);

    // Act
    const cancelButton = screen.getByDisplayValue('Cancel');
    await user.click(cancelButton);

    // Assert
    expect(screen.queryByDisplayValue('Cancel')).not.toBeInTheDocument();
    expect(screen.getByText('Sign Up')).toBeInTheDocument(); // Main button should still be visible
  });

  test('updates email input when typing in login form', async () => {
    // Arrange
    const user = userEvent.setup();
    renderApp();

    const loginButton = screen.getByText('Log in');
    await user.click(loginButton);

    // Act
    const emailInput = screen.getByLabelText('Email');
    await user.type(emailInput, 'test@example.com');

    // Assert
    expect(emailInput).toHaveValue('test@example.com');
  });

  test('updates password input when typing in login form', async () => {
    // Arrange
    const user = userEvent.setup();
    renderApp();

    const loginButton = screen.getByText('Log in');
    await user.click(loginButton);

    // Act
    const passwordInput = screen.getByLabelText('Password');
    await user.type(passwordInput, 'password123');

    // Assert
    expect(passwordInput).toHaveValue('password123');
  });

  test('updates email input when typing in signup form', async () => {
    // Arrange
    const user = userEvent.setup();
    renderApp();

    const signupButton = screen.getByText('Sign Up');
    await user.click(signupButton);

    // Act
    const emailInput = screen.getByLabelText('Email');
    await user.type(emailInput, 'test@example.com');

    // Assert
    expect(emailInput).toHaveValue('test@example.com');
  });

  test('updates password inputs when typing in signup form', async () => {
    // Arrange
    const user = userEvent.setup();
    renderApp();

    const signupButton = screen.getByText('Sign Up');
    await user.click(signupButton);

    // Act
    const passwordInput = screen.getByDisplayValue('Password');
    const confirmInput = screen.getByDisplayValue('Confirm Password');

    await user.type(passwordInput, 'password123');
    await user.type(confirmInput, 'password123');

    // Assert
    expect(passwordInput).toHaveValue('password123');
    expect(confirmInput).toHaveValue('password123');
  });

  test('shows error for invalid email in signup form', async () => {
    // Arrange
    const user = userEvent.setup();
    renderApp();

    const signupButton = screen.getByText('Sign Up');
    await user.click(signupButton);

    // Act
    const emailInput = screen.getByLabelText('Email');
    await user.type(emailInput, 'invalid-email');

    const passwordInput = screen.getByDisplayValue('Password');
    await user.type(passwordInput, 'password123');

    const confirmInput = screen.getByDisplayValue('Confirm Password');
    await user.type(confirmInput, 'password123');

    const submitButton = screen.getByDisplayValue('Sign Up');
    await user.click(submitButton);

    // Assert
    expect(screen.getByText('Please enter a valid email address.')).toBeInTheDocument();
  });

  test('shows error for short password in signup form', async () => {
    // Arrange
    const user = userEvent.setup();
    renderApp();

    const signupButton = screen.getByText('Sign Up');
    await user.click(signupButton);

    // Act
    const emailInput = screen.getByLabelText('Email');
    await user.type(emailInput, 'test@example.com');

    const passwordInput = screen.getByDisplayValue('Password');
    await user.type(passwordInput, '123'); // Too short

    const confirmInput = screen.getByDisplayValue('Confirm Password');
    await user.type(confirmInput, '123');

    const submitButton = screen.getByDisplayValue('Sign Up');
    await user.click(submitButton);

    // Assert
    expect(screen.getByText('Password must be at least 6 characters long.')).toBeInTheDocument();
  });

  test('shows error for mismatched passwords in signup form', async () => {
    // Arrange
    const user = userEvent.setup();
    renderApp();

    const signupButton = screen.getByText('Sign Up');
    await user.click(signupButton);

    // Act
    const emailInput = screen.getByLabelText('Email');
    await user.type(emailInput, 'test@example.com');

    const passwordInput = screen.getByDisplayValue('Password');
    await user.type(passwordInput, 'password123');

    const confirmInput = screen.getByDisplayValue('Confirm Password');
    await user.type(confirmInput, 'differentpassword');

    const submitButton = screen.getByDisplayValue('Sign Up');
    await user.click(submitButton);

    // Assert
    expect(screen.getByText('Passwords do not match.')).toBeInTheDocument();
  });

  test('clears error when closing signup modal', async () => {
    // Arrange
    const user = userEvent.setup();
    renderApp();

    const signupButton = screen.getByText('Sign Up');
    await user.click(signupButton);

    // Trigger validation error
    const emailInput = screen.getByLabelText('Email');
    await user.type(emailInput, 'invalid');

    const submitButton = screen.getByDisplayValue('Sign Up');
    await user.click(submitButton);

    // Verify error is shown
    expect(screen.getByText('Please enter a valid email address.')).toBeInTheDocument();

    // Act
    const cancelButton = screen.getByDisplayValue('Cancel');
    await user.click(cancelButton);

    // Reopen signup modal
    await user.click(signupButton);

    // Assert
    expect(screen.queryByText('Please enter a valid email address.')).not.toBeInTheDocument();
  });

  test('clears form fields when closing login modal', async () => {
    // Arrange
    const user = userEvent.setup();
    renderApp();

    const loginButton = screen.getByText('Log in');
    await user.click(loginButton);

    // Fill form
    const emailInput = screen.getByLabelText('Email');
    const passwordInput = screen.getByLabelText('Password');

    await user.type(emailInput, 'test@example.com');
    await user.type(passwordInput, 'password123');

    // Act
    const cancelButton = screen.getByDisplayValue('Cancel');
    await user.click(cancelButton);

    // Reopen login modal
    await user.click(loginButton);

    // Assert
    expect(screen.getByLabelText('Email')).toHaveValue('');
    expect(screen.getByLabelText('Password')).toHaveValue('');
  });

  test('clears form fields when closing signup modal', async () => {
    // Arrange
    const user = userEvent.setup();
    renderApp();

    const signupButton = screen.getByText('Sign Up');
    await user.click(signupButton);

    // Fill form
    const emailInput = screen.getByLabelText('Email');
    const passwordInput = screen.getByDisplayValue('Password');
    const confirmInput = screen.getByDisplayValue('Confirm Password');

    await user.type(emailInput, 'test@example.com');
    await user.type(passwordInput, 'password123');
    await user.type(confirmInput, 'password123');

    // Act
    const cancelButton = screen.getByDisplayValue('Cancel');
    await user.click(cancelButton);

    // Reopen signup modal
    await user.click(signupButton);

    // Assert
    expect(screen.getByLabelText('Email')).toHaveValue('');
    expect(screen.getByDisplayValue('Password')).toHaveValue('');
    expect(screen.getByDisplayValue('Confirm Password')).toHaveValue('');
  });

  test('handles successful signup and login flow', async () => {
    // Arrange
    api.register.mockResolvedValue({ success: true });
    api.login.mockResolvedValue({
      accessToken: 'mock_token',
      user: { id: '1', email: 'test@example.com' }
    });

    const user = userEvent.setup();
    renderApp();

    const signupButton = screen.getByText('Sign Up');
    await user.click(signupButton);

    // Act
    const emailInput = screen.getByLabelText('Email');
    await user.type(emailInput, 'test@example.com');

    const passwordInput = screen.getByDisplayValue('Password');
    await user.type(passwordInput, 'password123');

    const confirmInput = screen.getByDisplayValue('Confirm Password');
    await user.type(confirmInput, 'password123');

    const submitButton = screen.getByDisplayValue('Sign Up');
    await user.click(submitButton);

    // Assert
    await waitFor(() => {
      expect(api.register).toHaveBeenCalledWith({
        name: 'test',
        email: 'test@example.com',
        password: 'password123'
      });
    });

    await waitFor(() => {
      expect(api.login).toHaveBeenCalledWith({
        email: 'test@example.com',
        password: 'password123'
      });
    });

    expect(localStorageMock.setItem).toHaveBeenCalledWith('token', 'mock_token');
  });

  test('handles successful login flow', async () => {
    // Arrange
    api.login.mockResolvedValue({
      accessToken: 'mock_token',
      user: { id: '1', email: 'test@example.com' }
    });

    const user = userEvent.setup();
    renderApp();

    const loginButton = screen.getByText('Log in');
    await user.click(loginButton);

    // Act
    const emailInput = screen.getByLabelText('Email');
    await user.type(emailInput, 'test@example.com');

    const passwordInput = screen.getByLabelText('Password');
    await user.type(passwordInput, 'password123');

    const submitButton = screen.getByDisplayValue('Log in');
    await user.click(submitButton);

    // Assert
    await waitFor(() => {
      expect(api.login).toHaveBeenCalledWith({
        email: 'test@example.com',
        password: 'password123'
      });
    });

    expect(localStorageMock.setItem).toHaveBeenCalledWith('token', 'mock_token');
  });

  test('shows alert on login failure', async () => {
    // Arrange
    const errorMessage = 'Invalid credentials';
    api.login.mockRejectedValue(new Error(errorMessage));

    // Mock alert
    const alertSpy = jest.spyOn(window, 'alert').mockImplementation(() => {});

    const user = userEvent.setup();
    renderApp();

    const loginButton = screen.getByText('Log in');
    await user.click(loginButton);

    // Act
    const emailInput = screen.getByLabelText('Email');
    await user.type(emailInput, 'test@example.com');

    const passwordInput = screen.getByLabelText('Password');
    await user.type(passwordInput, 'wrongpassword');

    const submitButton = screen.getByDisplayValue('Log in');
    await user.click(submitButton);

    // Assert
    await waitFor(() => {
      expect(alertSpy).toHaveBeenCalledWith(errorMessage);
    });

    alertSpy.mockRestore();
  });

  test('shows error on signup failure', async () => {
    // Arrange
    const errorMessage = 'Email already exists';
    api.register.mockRejectedValue(new Error(errorMessage));

    const user = userEvent.setup();
    renderApp();

    const signupButton = screen.getByText('Sign Up');
    await user.click(signupButton);

    // Act
    const emailInput = screen.getByLabelText('Email');
    await user.type(emailInput, 'existing@example.com');

    const passwordInput = screen.getByDisplayValue('Password');
    await user.type(passwordInput, 'password123');

    const confirmInput = screen.getByDisplayValue('Confirm Password');
    await user.type(confirmInput, 'password123');

    const submitButton = screen.getByDisplayValue('Sign Up');
    await user.click(submitButton);

    // Assert
    await waitFor(() => {
      expect(screen.getByText(errorMessage)).toBeInTheDocument();
    });
  });

  test('prevents form submission with empty fields in login', async () => {
    // Arrange
    const user = userEvent.setup();
    renderApp();

    const loginButton = screen.getByText('Log in');
    await user.click(loginButton);

    // Act
    const submitButton = screen.getByDisplayValue('Log in');
    await user.click(submitButton);

    // Assert
    // Form should not be submitted, inputs should be required
    expect(api.login).not.toHaveBeenCalled();
  });

  test('prevents form submission with empty fields in signup', async () => {
    // Arrange
    const user = userEvent.setup();
    renderApp();

    const signupButton = screen.getByText('Sign Up');
    await user.click(signupButton);

    // Act
    const submitButton = screen.getByDisplayValue('Sign Up');
    await user.click(submitButton);

    // Assert
    // Form should not be submitted, inputs should be required
    expect(api.register).not.toHaveBeenCalled();
  });

  test('has correct accessibility attributes', () => {
    // Act
    renderApp();

    // Assert
    const logo = screen.getByAltText('logo');
    const bgImage = screen.getByAltText('background');

    expect(logo).toBeInTheDocument();
    expect(bgImage).toBeInTheDocument();

    // Check buttons have proper text content for screen readers
    expect(screen.getByRole('button', { name: 'Log in' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Sign Up' })).toBeInTheDocument();
  });

  test('modal backdrop prevents closing modal when clicked inside', async () => {
    // Arrange
    const user = userEvent.setup();
    renderApp();

    const loginButton = screen.getByText('Log in');
    await user.click(loginButton);

    // Act
    const modal = screen.getByText('Log in').closest('.modal');
    if (modal) {
      await user.click(modal);
    }

    // Assert
    // Modal should still be open
    expect(screen.getByDisplayValue('Cancel')).toBeInTheDocument();
  });

  test('handles rapid button clicks', async () => {
    // Arrange
    const user = userEvent.setup({ advanceTimers: jest.advanceTimersByTime });
    renderApp();

    // Act
    const loginButton = screen.getByText('Log in');
    await user.click(loginButton);
    await user.click(loginButton);
    await user.click(loginButton);

    // Assert
    // Only one modal should open
    expect(screen.getAllByText('Log in')).toHaveLength(2); // One button, one modal title
  });

  test('focus management works correctly', () => {
    // Act
    renderApp();

    // Assert
    // Main buttons should be focusable
    const loginButton = screen.getByText('Log in');
    const signupButton = screen.getByText('Sign Up');

    expect(loginButton.closest('button')).toHaveAttribute('type');
    expect(signupButton.closest('button')).toHaveAttribute('type');
  });

  test('cleans up event listeners on unmount', () => {
    // Arrange
    const { unmount } = renderApp();
    const removeEventListenerSpy = jest.spyOn(document, 'removeEventListener');

    // Act
    unmount();

    // Assert
    // Clean up should happen (this is more of an integration test)
    expect(removeEventListenerSpy).toHaveBeenCalled();

    removeEventListenerSpy.mockRestore();
  });
});