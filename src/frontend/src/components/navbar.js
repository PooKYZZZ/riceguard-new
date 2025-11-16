import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import './navbar.css';

const Navbar = () => {
  const [user, setUser] = useState(null);
  const [showProfile, setShowProfile] = useState(false);
  const [darkMode, setDarkMode] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    // Get user from token
    const token = localStorage.getItem('token');
    if (token) {
      try {
        const payload = JSON.parse(atob(token.split('.')[1]));
        setUser({ email: payload.email, name: payload.name || 'User' });
      } catch (error) {
        localStorage.removeItem('token');
      }
    }

    // Load dark mode preference
    const savedDarkMode = localStorage.getItem('darkMode') === 'true';
    setDarkMode(savedDarkMode);
    if (savedDarkMode) {
      document.body.classList.add('dark');
    }
  }, []);

  const toggleDarkMode = () => {
    const newDarkMode = !darkMode;
    setDarkMode(newDarkMode);
    localStorage.setItem('darkMode', newDarkMode);
    document.body.classList.toggle('dark');
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    setUser(null);
    navigate('/');
  };

  const isActive = (path) => location.pathname === path;

  return (
    <nav className="navbar">
      <div className="navbar-content">
        <div className="navbar-brand">
          <span className="brand-text">RiceGuard</span>
        </div>

        <div className="navbar-links">
          {user && (
            <>
              <button
                className={`nav-link ${isActive('/dashboard') ? 'active' : ''}`}
                onClick={() => navigate('/dashboard')}
              >
                Dashboard
              </button>
              <button
                className={`nav-link ${isActive('/scan') ? 'active' : ''}`}
                onClick={() => navigate('/scan')}
              >
                Scan
              </button>
              <button
                className={`nav-link ${isActive('/history') ? 'active' : ''}`}
                onClick={() => navigate('/history')}
              >
                History
              </button>
            </>
          )}
        </div>

        <div className="navbar-actions">
          <button
            className="dark-mode-toggle"
            onClick={toggleDarkMode}
            title={darkMode ? "Light mode" : "Dark mode"}
          >
            {darkMode ? '☀️' : '🌙'}
          </button>

          {user && (
            <>
              <button
                className="profile-button"
                onClick={() => setShowProfile(!showProfile)}
              >
                <div className="avatar">
                  {user.name.charAt(0).toUpperCase()}
                </div>
              </button>

              {showProfile && (
                <div className="profile-dropdown">
                  <div className="profile-info">
                    <div className="profile-name">{user.name}</div>
                    <div className="profile-email">{user.email}</div>
                  </div>
                  <div className="profile-actions">
                    <button className="profile-action" onClick={handleLogout}>
                      Logout
                    </button>
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </nav>
  );
};

export default Navbar;