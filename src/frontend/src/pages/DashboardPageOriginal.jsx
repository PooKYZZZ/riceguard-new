import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import Navbar from '../components/navbar';
import { listScans } from '../api';
import './DashboardPage.css';

const DashboardPage = () => {
  const [stats, setStats] = useState({
    totalScans: 0,
    todayScans: 0,
    accuracyRate: 0,
    topDisease: 'None'
  });
  const [recentScans, setRecentScans] = useState([]);
  const [loading, setLoading] = useState(true);
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
      const scans = scansData.data || [];

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

      // Get recent scans (last 6)
      const sortedScans = scans
        .sort((a, b) => new Date(b.createdAt) - new Date(a.createdAt))
        .slice(0, 6);

      setRecentScans(sortedScans);
    } catch (error) {
      console.error('Error loading dashboard data:', error);
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
      <div className="dashboard-page">
        <div className="loading-spinner">Loading dashboard...</div>
      </div>
    );
  }

  return (
    <div className="dashboard-page">
      <Navbar />

      <div className="dashboard-content">
        <div className="dashboard-header">
          <h1>Dashboard</h1>
          <p className="dashboard-subtitle">
            Monitor your rice disease detection activity
          </p>
        </div>

        {/* Stats Cards */}
        <div className="stats-grid">
          <div className="stat-card">
            <div className="stat-icon total">
              📊
            </div>
            <div className="stat-info">
              <div className="stat-number">{stats.totalScans}</div>
              <div className="stat-label">Total Scans</div>
            </div>
          </div>

          <div className="stat-card">
            <div className="stat-icon today">
              🌱
            </div>
            <div className="stat-info">
              <div className="stat-number">{stats.todayScans}</div>
              <div className="stat-label">Today's Scans</div>
            </div>
          </div>

          <div className="stat-card">
            <div className="stat-icon accuracy">
              🎯
            </div>
            <div className="stat-info">
              <div className="stat-number">{stats.accuracyRate}%</div>
              <div className="stat-label">Accuracy Rate</div>
            </div>
          </div>

          <div className="stat-card">
            <div className="stat-icon disease" style={{ color: getDiseaseColor(stats.topDisease) }}>
              🔍
            </div>
            <div className="stat-info">
              <div className="stat-number">{stats.topDisease}</div>
              <div className="stat-label">Top Disease</div>
            </div>
          </div>
        </div>

        {/* Quick Actions */}
        <div className="quick-actions">
          <button
            className="action-button primary"
            onClick={() => navigate('/scan')}
          >
            📷 New Scan
          </button>
          <button
            className="action-button secondary"
            onClick={() => navigate('/history')}
          >
            📋 View History
          </button>
          <button
            className="action-button secondary"
          >
            ⚙️ Settings
          </button>
        </div>

        {/* Recent Scans */}
        <div className="recent-scans-section">
          <h2>Recent Scans</h2>
          <div className="recent-scans-grid">
            {recentScans.map((scan) => (
              <div key={scan._id} className="scan-card">
                <div className="scan-image">
                  <img
                    src={`http://127.0.0.1:8000/uploads/${scan.imageFilename}`}
                    alt="Scan"
                    onError={(e) => {
                      e.target.src = 'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100" viewBox="0 0 100 100"><rect width="100" height="100" fill="%23f3f4f6"/><text x="50" y="50" text-anchor="middle" dy=".3em" fill="%239ca3af">No Image</text></svg>';
                    }}
                  />
                </div>
                <div className="scan-info">
                  <div
                    className="disease-badge"
                    style={{ backgroundColor: getDiseaseColor(scan.prediction?.disease) }}
                  >
                    {scan.prediction?.disease || 'Unknown'}
                  </div>
                  <div className="scan-date">{formatDate(scan.createdAt)}</div>
                  <div className="scan-confidence">
                    {Math.round((scan.prediction?.confidence || 0) * 100)}% confidence
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default DashboardPage;