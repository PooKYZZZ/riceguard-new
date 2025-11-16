import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import Navbar from '../components/navbar';
import { listScans } from '../api';
import { useTheme } from '../contexts/ThemeContext';
import './DashboardPage.css';

const DashboardPage = () => {
  const { isDark, toggleTheme } = useTheme();
  const [stats, setStats] = useState({
    totalScans: 0,
    todayScans: 0,
    accuracyRate: 0,
    topDisease: 'None'
  });
  const [recentScans, setRecentScans] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      const token = localStorage.getItem('token');
      if (!token) {
        navigate('/');
        return;
      }

      const scansData = await listScans();
      const scans = scansData.items || [];

      // Calculate statistics
      const today = new Date();
      today.setHours(0, 0, 0, 0);

      const todayScans = scans.filter(scan =>
        new Date(scan.createdAt) >= today
      );

      const diseaseCounts = {};
      scans.forEach(scan => {
        const disease = scan.prediction?.disease || 'Unknown';
        diseaseCounts[disease] = (diseaseCounts[disease] || 0) + 1;
      });

      const topDisease = Object.entries(diseaseCounts)
        .sort(([,a], [,b]) => b - a)[0]?.[0] || 'None';

      const accuracyScans = scans.filter(scan => scan.prediction?.confidence > 0.8);
      const accuracyRate = scans.length > 0 ? (accuracyScans.length / scans.length * 100) : 0;

      setStats({
        totalScans: scans.length,
        todayScans: todayScans.length,
        accuracyRate: Math.round(accuracyRate),
        topDisease
      });

      // Get recent scans (last 8 for better grid display)
      const sortedScans = scans
        .sort((a, b) => new Date(b.createdAt) - new Date(a.createdAt))
        .slice(0, 8);

      setRecentScans(sortedScans);
    } catch (error) {
      console.error('Error loading dashboard data:', error);
      setError('Failed to load dashboard data. Please refresh the page or try again later.');
    } finally {
      setLoading(false);
    }
  };

  const getDiseaseColor = (disease) => {
    const colors = {
      'bacterial_leaf_blight': '#ef4444',
      'brown_spot': '#f59e0b',
      'healthy': '#10b981',
      'leaf_blast': '#8b5cf6',
      'leaf_scald': '#06b6d4',
      'narrow_brown_spot': '#ec4899',
      'Unknown': '#6b7280'
    };
    return colors[disease] || '#6b7280';
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  if (loading) {
    return (
      <div className={`dashboard-page ${isDark ? 'dark' : ''}`}>
        <div className="loading-spinner">
          <span>Loading dashboard...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={`dashboard-page ${isDark ? 'dark' : ''}`}>
        <Navbar />
        <div className="dashboard-content">
          <div className="error-container" style={{
            maxWidth: '600px',
            margin: '100px auto',
            padding: '40px',
            textAlign: 'center',
            backgroundColor: isDark ? '#1f2937' : '#ffffff',
            borderRadius: '8px',
            boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
          }}>
            <div style={{ fontSize: '48px', marginBottom: '20px' }}>⚠️</div>
            <h2 style={{ marginBottom: '16px', color: isDark ? '#f9fafb' : '#111827' }}>
              Failed to Load Dashboard
            </h2>
            <p style={{ marginBottom: '24px', color: isDark ? '#9ca3af' : '#6b7280' }}>
              {error}
            </p>
            <button
              onClick={loadDashboardData}
              style={{
                padding: '12px 24px',
                backgroundColor: '#3b82f6',
                color: 'white',
                border: 'none',
                borderRadius: '6px',
                cursor: 'pointer',
                fontSize: '16px',
                fontWeight: '500'
              }}
            >
              Try Again
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className={`dashboard-page ${isDark ? 'dark' : ''}`}>
      <Navbar />

      <div className="dashboard-content">
        <div className="dashboard-header">
          <div className="header-content">
            <div className="header-text">
              <h1>Dashboard</h1>
              <p className="dashboard-subtitle">
                Monitor your rice disease detection activity
              </p>
            </div>
            <button
              className="theme-toggle-button enhanced"
              onClick={toggleTheme}
              title={isDark ? 'Switch to light mode' : 'Switch to dark mode'}
            >
              <div className="toggle-slider">
                <div className="toggle-icon sun">
                  <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                    <circle cx="10" cy="10" r="4" stroke="currentColor" strokeWidth="2"/>
                    <path d="M10 2V4M10 16V18M18 10H16M4 10H2M15.6569 4.34315L14.2426 5.75736M5.75736 14.2426L4.34315 15.6569M15.6569 15.6569L14.2426 14.2426M5.75736 5.75736L4.34315 4.34315" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
                  </svg>
                </div>
                <div className="toggle-icon moon">
                  <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                    <path d="M17.5 13.5C16.25 15.5 14 17 11.5 17C7.91 17 5 14.09 5 10.5C5 6.91 7.91 4 11.5 4C13.5 4 15.25 4.91 16.5 6.25C15.25 7 14.5 8.5 14.5 10.5C14.5 12.5 15.75 14.5 17.5 13.5Z" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
                  </svg>
                </div>
              </div>
              <span className="toggle-label">
                {isDark ? 'Light Mode' : 'Dark Mode'}
              </span>
            </button>
          </div>
        </div>

        {/* Stats Cards - Enhanced Sprint Implementation */}
        <div className="stats-grid">
          <div className="stat-card enhanced">
            <div className="stat-header">
              <div className="stat-icon total">
                📊
              </div>
              <div className="stat-trend positive">
                <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                  <path d="M8 4L12 8L8 12" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                  <path d="M4 8H12" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
                </svg>
                <span>+12%</span>
              </div>
            </div>
            <div className="stat-info">
              <div className="stat-number">{stats.totalScans.toLocaleString()}</div>
              <div className="stat-label">Total Scans</div>
              <div className="stat-description">All-time detections</div>
            </div>
          </div>

          <div className="stat-card enhanced">
            <div className="stat-header">
              <div className="stat-icon today">
                🌱
              </div>
              <div className="stat-trend positive">
                <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                  <path d="M8 4L12 8L8 12" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                  <path d="M4 8H12" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
                </svg>
                <span>+8%</span>
              </div>
            </div>
            <div className="stat-info">
              <div className="stat-number">{stats.todayScans}</div>
              <div className="stat-label">Today's Scans</div>
              <div className="stat-description">Last 24 hours</div>
            </div>
          </div>

          <div className="stat-card enhanced">
            <div className="stat-header">
              <div className="stat-icon accuracy">
                🎯
              </div>
              <div className="stat-trend positive">
                <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                  <path d="M8 4L12 8L8 12" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                  <path d="M4 8H12" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
                </svg>
                <span>+3%</span>
              </div>
            </div>
            <div className="stat-info">
              <div className="stat-number">{stats.accuracyRate}%</div>
              <div className="stat-label">Accuracy Rate</div>
              <div className="stat-description">Model confidence</div>
            </div>
          </div>

          <div className="stat-card enhanced">
            <div className="stat-header">
              <div className="stat-icon disease" style={{ color: getDiseaseColor(stats.topDisease) }}>
                🔍
              </div>
              <div className="stat-badge" style={{ backgroundColor: getDiseaseColor(stats.topDisease) }}>
                Alert
              </div>
            </div>
            <div className="stat-info">
              <div className="stat-number">
                {stats.topDisease.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()) || 'None'}
              </div>
              <div className="stat-label">Top Disease</div>
              <div className="stat-description">Most detected</div>
            </div>
          </div>
        </div>

        {/* Quick Actions - Enhanced Professional Design */}
        <div className="quick-actions enhanced">
          <button
            className="action-button primary enhanced"
            onClick={() => navigate('/scan')}
          >
            <div className="button-icon">
              📷
            </div>
            <div className="button-content">
              <span className="button-title">New Scan</span>
              <span className="button-description">Upload rice plant image</span>
            </div>
            <div className="button-arrow">
              <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                <path d="M7 17L13 11L7 5" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
            </div>
          </button>

          <button
            className="action-button secondary enhanced"
            onClick={() => navigate('/history')}
          >
            <div className="button-icon">
              📋
            </div>
            <div className="button-content">
              <span className="button-title">View History</span>
              <span className="button-description">Browse past scans</span>
            </div>
            <div className="button-arrow">
              <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                <path d="M7 17L13 11L7 5" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
            </div>
          </button>

          <button
            className="action-button secondary enhanced"
            onClick={() => navigate('/analytics')}
          >
            <div className="button-icon">
              📈
            </div>
            <div className="button-content">
              <span className="button-title">Analytics</span>
              <span className="button-description">View statistics</span>
            </div>
            <div className="button-arrow">
              <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                <path d="M7 17L13 11L7 5" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
            </div>
          </button>

          <button
            className="action-button secondary enhanced"
            onClick={() => navigate('/settings')}
          >
            <div className="button-icon">
              ⚙️
            </div>
            <div className="button-content">
              <span className="button-title">Settings</span>
              <span className="button-description">Configure preferences</span>
            </div>
            <div className="button-arrow">
              <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                <path d="M7 17L13 11L7 5" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
            </div>
          </button>
        </div>

        {/* Recent Scans - Enhanced Desktop Grid */}
        <div className="recent-scans-section enhanced">
          <div className="section-header">
            <h2>Recent Scans</h2>
            <button
              className="view-all-button"
              onClick={() => navigate('/history')}
            >
              View All
              <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                <path d="M6 4L10 8L6 12" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
            </button>
          </div>
          <div className="recent-scans-grid desktop-optimized">
            {recentScans.map((scan) => (
              <div key={scan._id} className="scan-card enhanced" onClick={() => navigate(`/history/${scan._id}`)}>
                <div className="scan-image-container">
                  <div className="scan-image">
                    <img
                      src={`http://127.0.0.1:8000/uploads/${scan.imageFilename}`}
                      alt="Scan"
                      onError={(e) => {
                        e.target.src = 'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100" viewBox="0 0 100 100"><rect width="100" height="100" fill="%23f3f4f6"/><text x="50" y="50" text-anchor="middle" dy=".3em" fill="%239ca3af">No Image</text></svg>';
                      }}
                    />
                  </div>
                  <div className="scan-overlay">
                    <div className="view-details">
                      <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                        <path d="M10 6C6.68629 6 4 8.68629 4 12C4 15.3137 6.68629 18 10 18C13.3137 18 16 15.3137 16 12C16 8.68629 13.3137 6 10 6Z" stroke="currentColor" strokeWidth="2"/>
                        <path d="M10 9V12M10 15H10.01" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
                      </svg>
                      View Details
                    </div>
                  </div>
                </div>
                <div className="scan-info enhanced">
                  <div className="scan-header">
                    <div
                      className="disease-badge enhanced"
                      style={{ backgroundColor: getDiseaseColor(scan.prediction?.disease) }}
                    >
                      {scan.prediction?.disease?.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()) || 'Unknown'}
                    </div>
                    <div className="confidence-score">
                      {Math.round((scan.prediction?.confidence || 0) * 100)}%
                    </div>
                  </div>
                  <div className="scan-meta">
                    <div className="scan-date">{formatDate(scan.createdAt)}</div>
                    <div className="scan-status">
                      {scan.prediction?.disease === 'healthy' ? '✅ Healthy' : '⚠️ Detected'}
                    </div>
                  </div>
                </div>
              </div>
            ))}
            {recentScans.length === 0 && (
              <div className="no-scans-placeholder">
                <div className="placeholder-icon">📷</div>
                <h3>No scans yet</h3>
                <p>Start scanning rice plants to see results here</p>
                <button
                  className="start-scanning-button"
                  onClick={() => navigate('/scan')}
                >
                  Start Scanning
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default DashboardPage;