/**
 * API Error Handler Utility - Optimized Version
 *
 * Provides centralized error handling for API requests
 * Console logs removed for production performance
 */

import { tokenStorage } from './secureStorage.js';

class APIErrorHandler {
  constructor() {
    this.errorListeners = [];
  }

  /**
   * Add error listener for custom error handling
   */
  addErrorListener(listener) {
    this.errorListeners.push(listener);
  }

  /**
   * Remove error listener
   */
  removeErrorListener(listener) {
    const index = this.errorListeners.indexOf(listener);
    if (index > -1) {
      this.errorListeners.splice(index, 1);
    }
  }

  /**
   * Notify all error listeners
   */
  notifyListeners(error, context) {
    this.errorListeners.forEach(listener => {
      try {
        listener(error, context);
      } catch (e) {
        // Error in error listener - silently ignore to prevent infinite loops
      }
    });
  }

  /**
   * Handle API response errors
   */
  async handleAPIError(response, url, options = {}) {
    let errorData;

    try {
      errorData = await response.json().catch(() => ({}));
    } catch (e) {
      errorData = {
        error: true,
        message: `HTTP ${response.status}: ${response.statusText}`,
        status_code: response.status
      };
    }

    const error = new Error(errorData.message || `HTTP ${response.status}`);
    error.status = response.status;
    error.data = errorData;
    error.url = url;
    error.options = options;

    // Handle authentication errors
    if (response.status === 401) {
      this.handleAuthError(error, errorData);
    }

    // Handle server errors
    if (response.status >= 500) {
      this.handleServerError(error, errorData);
    }

    // Handle client errors
    if (response.status >= 400 && response.status < 500) {
      this.handleClientError(error, errorData);
    }

    // Notify listeners
    this.notifyListeners(error, { url, response, errorData });

    return error;
  }

  /**
   * Handle authentication errors
   */
  handleAuthError(error, errorData) {
    // Clear stored tokens
    tokenStorage.clearToken();

    // Redirect to login if not already there
    if (window.location.pathname !== '/') {
      // Store the attempted URL for redirect after login (with validation)
      const currentPath = window.location.pathname + window.location.search;
      const validPaths = ['/scan', '/history', '/settings', '/dashboard'];

      // Only store redirect if it's a valid internal path
      if (validPaths.some(path => currentPath.startsWith(path))) {
        sessionStorage.setItem('redirectAfterLogin', currentPath);
      }

      // Show user-friendly message
      if (errorData.message.includes('token')) {
        this.showUserMessage('Your session has expired. Please log in again.');
      } else {
        this.showUserMessage('Please log in to continue.');
      }

      // Redirect to login
      setTimeout(() => {
        window.location.href = '/';
      }, 2000);
    }
  }

  /**
   * Handle server errors
   */
  handleServerError(error, errorData) {
    // Show user-friendly message
    this.showUserMessage('Server error occurred. Please try again later.');
  }

  /**
   * Handle client errors
   */
  handleClientError(error, errorData) {
    // Show specific messages for common errors
    switch (error.status) {
      case 400:
        this.showUserMessage(errorData.message || 'Invalid request. Please check your input.');
        break;
      case 403:
        this.showUserMessage('You do not have permission to perform this action.');
        break;
      case 404:
        this.showUserMessage('The requested resource was not found.');
        break;
      case 413:
        this.showUserMessage('File too large. Please upload a smaller file.');
        break;
      case 415:
        this.showUserMessage('Unsupported file type. Please upload a valid image file.');
        break;
      case 429:
        this.showUserMessage('Too many requests. Please wait and try again.');
        break;
      default:
        this.showUserMessage(errorData.message || 'Request failed. Please try again.');
    }
  }

  /**
   * Show user-friendly message (can be customized based on UI framework)
   */
  showUserMessage(message, type = 'error') {
    // Simple alert for now (replace with better UI in production)
    if (process.env.NODE_ENV === 'development') {
      // In development, show more details
      alert(`Error: ${message}`);
    }
    // In production, you might want to use a toast library
    // Note: Consider integrating with a proper notification system
  }

  /**
   * Wrap fetch calls with error handling
   */
  async fetchWithHandling(url, options = {}) {
    try {
      const response = await fetch(url, {
        ...options,
        // Add default headers
        headers: {
          'Content-Type': 'application/json',
          ...options.headers
        }
      });

      if (!response.ok) {
        throw await this.handleAPIError(response, url, options);
      }

      return response;
    } catch (error) {
      // If it's already an API error, re-throw it
      if (error.status) {
        throw error;
      }

      // Handle network errors
      this.showUserMessage('Network error. Please check your connection and try again.');

      const networkError = new Error('Network error');
      networkError.isNetworkError = true;
      throw networkError;
    }
  }

  /**
   * Retry failed requests with exponential backoff
   */
  async fetchWithRetry(url, options = {}, maxRetries = 3, delay = 1000) {
    let lastError;

    for (let attempt = 1; attempt <= maxRetries; attempt++) {
      try {
        return await this.fetchWithHandling(url, options);
      } catch (error) {
        lastError = error;

        // Don't retry on client errors (4xx) except 429 (rate limit)
        if (error.status >= 400 && error.status < 500 && error.status !== 429) {
          throw error;
        }

        // Don't retry on network errors if this is the last attempt
        if (error.isNetworkError && attempt === maxRetries) {
          throw error;
        }

        if (attempt < maxRetries) {
          // Exponential backoff with jitter
          const backoffDelay = delay * Math.pow(2, attempt - 1) + Math.random() * 1000;
          await new Promise(resolve => setTimeout(resolve, backoffDelay));
        }
      }
    }

    throw lastError;
  }
}

// Create singleton instance
export const errorHandler = new APIErrorHandler();

// Export convenience functions
export const { fetchWithHandling, fetchWithRetry, addErrorListener, removeErrorListener } = errorHandler;

// Enhanced fetch wrapper for use throughout the app
export const safeFetch = (url, options = {}) => {
  return errorHandler.fetchWithHandling(url, options);
};

export const safeFetchWithRetry = (url, options = {}, maxRetries = 3) => {
  return errorHandler.fetchWithRetry(url, options, maxRetries);
};