import React from 'react';
import PropTypes from 'prop-types';

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
      retryCount: 0
    };
  }

  static getDerivedStateFromError(error) {
    // Update state so the next render will show the fallback UI
    return { hasError: true };
  }

  componentDidCatch(error, errorInfo) {
    // Log error to monitoring service
    console.error('ErrorBoundary caught an error:', error, errorInfo);

    // Store error details for debugging
    this.setState({
      error: error,
      errorInfo: errorInfo
    });

    // Log to external monitoring service in production
    if (process.env.NODE_ENV === 'production') {
      // In production, you would send this to a service like Sentry, LogRocket, etc.
      this.logErrorToService(error, errorInfo);
    }
  }

  logErrorToService = (error, errorInfo) => {
    // Example: Send error to logging service
    try {
      // This is where you would integrate with error tracking services
      const errorData = {
        message: error.toString(),
        stack: error.stack,
        componentStack: errorInfo.componentStack,
        timestamp: new Date().toISOString(),
        userAgent: navigator.userAgent,
        url: window.location.href
      };

      // For now, just log to console (in production, replace with actual service call)
      console.error('Production Error:', errorData);

      // You could also send to your backend:
      // fetch('/api/v1/errors', {
      //   method: 'POST',
      //   headers: { 'Content-Type': 'application/json' },
      //   body: JSON.stringify(errorData)
      // }).catch(err => console.error('Failed to log error:', err));
    } catch (e) {
      console.error('Failed to log error:', e);
    }
  };

  handleRetry = () => {
    this.setState(prevState => ({
      hasError: false,
      error: null,
      errorInfo: null,
      retryCount: prevState.retryCount + 1
    }));

    // If retry count exceeds threshold, reload the page
    if (this.state.retryCount >= 3) {
      window.location.reload();
    }
  };

  render() {
    if (this.state.hasError) {
      // You can render any custom fallback UI
      return (
        <div style={{
          padding: '20px',
          margin: '20px',
          border: '2px solid #ff6b6b',
          borderRadius: '8px',
          backgroundColor: '#ffe0e0',
          textAlign: 'center',
          fontFamily: 'Arial, sans-serif'
        }}>
          <h2 style={{ color: '#d63031', marginBottom: '16px' }}>
            Something went wrong
          </h2>

          <p style={{ marginBottom: '16px', color: '#636e72' }}>
            We're sorry, but something unexpected happened. Our team has been notified.
          </p>

          {process.env.NODE_ENV === 'development' && this.state.error && (
            <details style={{
              textAlign: 'left',
              margin: '20px auto',
              padding: '15px',
              backgroundColor: '#f8f9fa',
              border: '1px solid #dee2e6',
              borderRadius: '4px',
              maxWidth: '600px'
            }}>
              <summary style={{ cursor: 'pointer', fontWeight: 'bold', marginBottom: '10px' }}>
                Error Details (Development Only)
              </summary>
              <pre style={{
                overflow: 'auto',
                fontSize: '12px',
                color: '#495057',
                whiteSpace: 'pre-wrap'
              }}>
                {this.state.error && this.state.error.toString()}
                <br />
                {this.state.errorInfo.componentStack}
              </pre>
            </details>
          )}

          <div style={{ marginTop: '20px' }}>
            <button
              onClick={this.handleRetry}
              style={{
                backgroundColor: '#0984e3',
                color: 'white',
                border: 'none',
                padding: '10px 20px',
                borderRadius: '5px',
                cursor: 'pointer',
                marginRight: '10px',
                fontSize: '14px'
              }}
              onMouseOver={(e) => e.target.style.backgroundColor = '#74b9ff'}
              onMouseOut={(e) => e.target.style.backgroundColor = '#0984e3'}
            >
              Try Again
            </button>

            <button
              onClick={() => window.location.reload()}
              style={{
                backgroundColor: '#636e72',
                color: 'white',
                border: 'none',
                padding: '10px 20px',
                borderRadius: '5px',
                cursor: 'pointer',
                fontSize: '14px'
              }}
              onMouseOver={(e) => e.target.style.backgroundColor = '#2d3436'}
              onMouseOut={(e) => e.target.style.backgroundColor = '#636e72'}
            >
              Reload Page
            </button>
          </div>

          {this.state.retryCount > 0 && (
            <p style={{
              marginTop: '15px',
              fontSize: '12px',
              color: '#636e72'
            }}>
              Retry attempt: {this.state.retryCount}
            </p>
          )}
        </div>
      );
    }

    return this.props.children;
  }
}

ErrorBoundary.propTypes = {
  children: PropTypes.node.isRequired
};

export default ErrorBoundary;