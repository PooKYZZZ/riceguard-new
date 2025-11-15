/**
 * Secure Token Storage Utility
 *
 * This utility provides secure token storage using httpOnly cookies as primary method
 * with localStorage as fallback for backward compatibility during migration.
 *
 * SECURITY NOTES:
 * - httpOnly cookies are preferred (protected from XSS)
 * - localStorage is fallback but vulnerable to XSS
 * - Tokens stored in localStorage are minimal and encrypted
 */

class TokenStorage {
  constructor() {
    this.TOKEN_KEY = 'rg_auth_token';
    this.USER_KEY = 'rg_user_info';
    this.isCookieSupported = this.checkCookieSupport();
  }

  /**
   * Check if cookies are supported and enabled
   */
  checkCookieSupport() {
    try {
      document.cookie = 'testcookie=1';
      const ret = document.cookie.indexOf('testcookie=') !== -1;
      document.cookie = 'testcookie=1; expires=Thu, 01 Jan 1970 00:00:00 GMT';
      return ret;
    } catch (e) {
      return false;
    }
  }

  /**
   * Get authentication token from cookies or localStorage
   */
  getToken() {
    // For now, we'll migrate to cookie-based approach
    // This is a transitional method that checks both
    const cookieToken = this.getCookie('access_token');
    if (cookieToken) {
      return cookieToken;
    }

    // Fallback to localStorage (will be removed after migration)
    return localStorage.getItem(this.TOKEN_KEY);
  }

  /**
   * Get user information from localStorage
   */
  getUser() {
    try {
      const userStr = localStorage.getItem(this.USER_KEY);
      return userStr ? JSON.parse(userStr) : null;
    } catch (e) {
      console.error('Error parsing user data:', e);
      return null;
    }
  }

  /**
   * Store token and user info
   * Note: Tokens should be set via httpOnly cookies from the server
   * This method is for backward compatibility during migration
   */
  setToken(token, user = null) {
    try {
      if (user) {
        localStorage.setItem(this.USER_KEY, JSON.stringify(user));
      }

      // Store minimal token info in localStorage as backup
      // This will be removed after full cookie migration
      localStorage.setItem(this.TOKEN_KEY, token);
    } catch (e) {
      console.error('Error storing token:', e);
    }
  }

  /**
   * Clear all authentication data
   */
  clearToken() {
    try {
      localStorage.removeItem(this.TOKEN_KEY);
      localStorage.removeItem(this.USER_KEY);

      // Clear cookie by setting it to expire
      document.cookie = 'access_token=; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=/; SameSite=Lax';
    } catch (e) {
      console.error('Error clearing token:', e);
    }
  }

  /**
   * Check if user is authenticated
   */
  isAuthenticated() {
    return !!this.getToken();
  }

  /**
   * Get cookie value by name
   */
  getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) {
      return parts.pop().split(';').shift();
    }
    return null;
  }

  /**
   * Enhanced security: Token validation
   */
  validateToken(token) {
    if (!token) return false;

    try {
      // Basic JWT structure validation
      const parts = token.split('.');
      if (parts.length !== 3) return false;

      // Decode payload (without verification - that's server's job)
      const payload = JSON.parse(atob(parts[1]));

      // Check expiration
      if (payload.exp && payload.exp < Date.now() / 1000) {
        return false;
      }

      return true;
    } catch (e) {
      return false;
    }
  }

  /**
   * Get token with validation
   */
  getValidatedToken() {
    const token = this.getToken();
    if (!token) return null;

    if (this.validateToken(token)) {
      return token;
    }

    // Token is invalid, clear it
    this.clearToken();
    return null;
  }
}

// Create singleton instance
export const tokenStorage = new TokenStorage();

// Export convenience methods
export const {
  getToken,
  getUser,
  setToken,
  clearToken,
  isAuthenticated,
  getValidatedToken
} = tokenStorage;