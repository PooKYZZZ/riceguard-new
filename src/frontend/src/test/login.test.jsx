// src/test/login.test.jsx
import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

// ---- mocks ----
const mockLogin = jest.fn();
jest.mock('../api', () => ({
  login: (...args) => mockLogin(...args),
  register: jest.fn(),
}));

const mockNavigate = jest.fn();
jest.mock('react-router-dom', () => {
  const actual = jest.requireActual('react-router-dom');
  return { ...actual, useNavigate: () => mockNavigate };
});

import App from '../App';

// ---- helpers ----
const openLoginModal = async (user, container) => {
  // Landing page “Log in” (only one before modal opens)
  const openBtn = screen.getByRole('button', { name: /^log in$/i });
  await user.click(openBtn);

  // Wait for modal inputs to appear
  await waitFor(() => {
    const email = container.querySelector('#loginEmail');
    const pass  = container.querySelector('#password');
    if (!email || !pass) throw new Error('Modal inputs not found yet');
  });

  // Use submit inside modal (avoid the landing button)
  const submitBtn = container.querySelector('.modal form button[type="submit"]');
  const emailInput = container.querySelector('#loginEmail');
  const passInput  = container.querySelector('#password');

  return { submitBtn, emailInput, passInput };
};

beforeEach(() => {
  jest.spyOn(window, 'alert').mockImplementation(() => {});
  jest.spyOn(Storage.prototype, 'setItem');
});
afterEach(() => {
  jest.restoreAllMocks();
  mockLogin.mockReset();
  mockNavigate.mockReset();
});

describe('Login flow (frontend)', () => {
  test('FC-LOGIN-001: empty fields → shows error and no redirect', async () => {
    const user = userEvent.setup();
    const { container } = render(<App />);

    const { submitBtn } = await openLoginModal(user, container);

    mockLogin.mockRejectedValueOnce(new Error('Email and password are required.'));

    await user.click(submitBtn);

    await waitFor(() =>
      expect(window.alert).toHaveBeenCalledWith('Email and password are required.')
    );
    expect(mockNavigate).not.toHaveBeenCalled();
    expect(localStorage.setItem).not.toHaveBeenCalled();
    // If UI prevents calling API when empty:
    // expect(mockLogin).not.toHaveBeenCalled();
  });

  test('FC-LOGIN-002: invalid email → alert, stay on page', async () => {
    const user = userEvent.setup();
    const { container } = render(<App />);

    const { submitBtn, emailInput, passInput } = await openLoginModal(user, container);

    mockLogin.mockRejectedValueOnce(new Error('Enter a valid email address.'));

    await user.type(emailInput, 'abc@');
    await user.type(passInput, 'secret');
    await user.click(submitBtn);

    await waitFor(() =>
      expect(window.alert).toHaveBeenCalledWith('Enter a valid email address.')
    );
    expect(mockNavigate).not.toHaveBeenCalled();
    expect(localStorage.setItem).not.toHaveBeenCalled();
    // If front-end blocks before API:
    // expect(mockLogin).not.toHaveBeenCalled();
  });

  test('FC-LOGIN-003: valid creds → token saved and redirect to /scan', async () => {
    const user = userEvent.setup();
    const { container } = render(<App />);

    const { submitBtn, emailInput, passInput } = await openLoginModal(user, container);

    mockLogin.mockResolvedValueOnce({
      accessToken: 'fake.jwt.token',
      user: { id: 'u1', email: 'user@example.com' },
      expiresAt: Date.now() + 3600_000,
    });

    await user.type(emailInput, 'user@example.com');
    await user.type(passInput, 'p@ssw0rd');
    await user.click(submitBtn);

    await waitFor(() => {
      expect(localStorage.setItem).toHaveBeenCalledWith('token', 'fake.jwt.token');
      expect(mockNavigate).toHaveBeenCalledWith('/scan');
    });
  });
});
