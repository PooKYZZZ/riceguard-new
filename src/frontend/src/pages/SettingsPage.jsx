import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import Navbar from '../components/navbar';
import { useTheme } from '../contexts/ThemeContext';
import './SettingsPage.css';

const SettingsPage = () => {
  const { isDark, toggleTheme } = useTheme();
  const [user, setUser] = useState(null);
  const [notifications, setNotifications] = useState(true);
  const [autoSave, setAutoSave] = useState(true);
  const [imageQuality, setImageQuality] = useState('high');
  const [confidence, setConfidence] = useState(80);
  const navigate = useNavigate();

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (!token) {
      navigate('/');
      return;
    }

    try {
      const payload = JSON.parse(atob(token.split('.')[1]));
      setUser({ email: payload.email, name: payload.name || 'User' });
    } catch (error) {
      console.error('Invalid token');
      navigate('/');
    }

    // Load saved settings
    const savedSettings = localStorage.getItem('riceguard-settings');
    if (savedSettings) {
      const settings = JSON.parse(savedSettings);
      setNotifications(settings.notifications ?? true);
      setAutoSave(settings.autoSave ?? true);
      setImageQuality(settings.imageQuality ?? 'high');
      setConfidence(settings.confidence ?? 80);
    }
  }, [navigate]);

  const saveSettings = () => {
    const settings = {
      notifications,
      autoSave,
      imageQuality,
      confidence
    };
    localStorage.setItem('riceguard-settings', JSON.stringify(settings));
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('riceguard-settings');
    navigate('/');
  };

  return (
    <div className={`settings-page ${isDark ? 'dark' : ''}`}>
      <Navbar />

      <div className="settings-content">
        <div className="settings-header">
          <div className="header-text">
            <h1>Settings</h1>
            <p className="settings-subtitle">
              Customize your RiceGuard experience
            </p>
          </div>
        </div>

        <div className="settings-grid">
          {/* Profile Section */}
          <div className="settings-section">
            <div className="section-header">
              <h2>👤 Profile</h2>
            </div>
            <div className="section-content">
              <div className="profile-info">
                <div className="avatar-large">
                  {user?.name?.charAt(0).toUpperCase() || 'U'}
                </div>
                <div className="profile-details">
                  <div className="profile-name">{user?.name || 'User'}</div>
                  <div className="profile-email">{user?.email}</div>
                </div>
              </div>
            </div>
          </div>

          {/* Appearance Section */}
          <div className="settings-section">
            <div className="section-header">
              <h2>🎨 Appearance</h2>
            </div>
            <div className="section-content">
              <div className="setting-item">
                <div className="setting-info">
                  <label className="setting-label">Dark Mode</label>
                  <p className="setting-description">Toggle dark theme for the interface</p>
                </div>
                <button
                  className={`toggle-button ${isDark ? 'active' : ''}`}
                  onClick={toggleTheme}
                >
                  <div className="toggle-slider"></div>
                </button>
              </div>
            </div>
          </div>

          {/* Detection Settings */}
          <div className="settings-section">
            <div className="section-header">
              <h2>🔍 Detection Settings</h2>
            </div>
            <div className="section-content">
              <div className="setting-item">
                <div className="setting-info">
                  <label className="setting-label">Confidence Threshold</label>
                  <p className="setting-description">Minimum confidence for disease detection</p>
                </div>
                <div className="confidence-control">
                  <input
                    type="range"
                    min="50"
                    max="95"
                    value={confidence}
                    onChange={(e) => setConfidence(Number(e.target.value))}
                    className="confidence-slider"
                  />
                  <span className="confidence-value">{confidence}%</span>
                </div>
              </div>

              <div className="setting-item">
                <div className="setting-info">
                  <label className="setting-label">Image Quality</label>
                  <p className="setting-description">Upload image quality for scanning</p>
                </div>
                <select
                  value={imageQuality}
                  onChange={(e) => setImageQuality(e.target.value)}
                  className="quality-select"
                >
                  <option value="low">Low (Faster)</option>
                  <option value="medium">Medium</option>
                  <option value="high">High (Recommended)</option>
                </select>
              </div>
            </div>
          </div>

          {/* Notifications */}
          <div className="settings-section">
            <div className="section-header">
              <h2>🔔 Notifications</h2>
            </div>
            <div className="section-content">
              <div className="setting-item">
                <div className="setting-info">
                  <label className="setting-label">Push Notifications</label>
                  <p className="setting-description">Receive alerts about new features</p>
                </div>
                <button
                  className={`toggle-button ${notifications ? 'active' : ''}`}
                  onClick={() => setNotifications(!notifications)}
                >
                  <div className="toggle-slider"></div>
                </button>
              </div>

              <div className="setting-item">
                <div className="setting-info">
                  <label className="setting-label">Auto-save Scans</label>
                  <p className="setting-description">Automatically save scan results</p>
                </div>
                <button
                  className={`toggle-button ${autoSave ? 'active' : ''}`}
                  onClick={() => setAutoSave(!autoSave)}
                >
                  <div className="toggle-slider"></div>
                </button>
              </div>
            </div>
          </div>

          {/* Storage */}
          <div className="settings-section">
            <div className="section-header">
              <h2>💾 Storage</h2>
            </div>
            <div className="section-content">
              <div className="storage-info">
                <div className="storage-stat">
                  <span className="storage-label">Cached Data</span>
                  <span className="storage-value">2.4 MB</span>
                </div>
                <button className="clear-cache-button">
                  Clear Cache
                </button>
              </div>
            </div>
          </div>

          {/* Actions */}
          <div className="settings-section">
            <div className="section-header">
              <h2>⚡ Actions</h2>
            </div>
            <div className="section-content">
              <div className="action-buttons">
                <button
                  onClick={saveSettings}
                  className="action-button primary"
                >
                  💾 Save Settings
                </button>
                <button
                  onClick={handleLogout}
                  className="action-button danger"
                >
                  🚪 Logout
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SettingsPage;