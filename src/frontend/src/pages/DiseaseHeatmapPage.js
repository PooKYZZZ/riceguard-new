// src/pages/DiseaseHeatmapPage.js - Optimized Version
import React, { useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import DiseaseHeatmap from '../components/DiseaseHeatmap';
import './DiseaseHeatmapPage.css';

function DiseaseHeatmapPage() {
  const [filterState, setFilterState] = useState(null);
  const navigate = useNavigate();

  // Handle cell click from heatmap - optimized with useCallback
  const handleCellClick = useCallback((cellData) => {
    // Set filter state for display
    setFilterState(cellData);

    // Optionally navigate to history page with filters
    // This could be extended to pass query parameters to HistoryPage
    // navigate('/history', {
    //   state: {
    //     disease: cellData.disease,
    //     timePeriod: cellData.timePeriod
    //   }
    // });
  }, []);

  // Clear filters - optimized with useCallback
  const clearFilters = useCallback(() => {
    setFilterState(null);
  }, []);

  return (
    <div className="heatmap-page">
      {/* Header with navigation */}
      <div className="heatmap-page-header">
        <div className="header-content">
          <div className="logo-section">
            <img
              src={`${process.env.PUBLIC_URL}/logo.png`}
              alt="Rice Guard Logo"
              className="heatmap-logo"
            />
          </div>

          <nav className="nav-links">
            <button onClick={() => navigate('/scan')}>Scan</button>
            <button onClick={() => navigate('/history')}>History</button>
            <button className="active">Analytics</button>
            <button onClick={() => {
              localStorage.removeItem('token');
              localStorage.removeItem('user');
              navigate('/');
            }}>Log Out</button>
          </nav>
        </div>
      </div>

      {/* Main content */}
      <div className="heatmap-page-content">
        {/* Active Filter Display */}
        {filterState && (
          <div className="active-filter-banner">
            <div className="filter-info">
              <h4>Active Filter:</h4>
              <p>
                <strong>Disease:</strong> {getDiseaseDisplayName(filterState.disease)} |
                <strong> Time Period:</strong> {filterState.timePeriod} |
                <strong> Count:</strong> {filterState.count} cases
                ({filterState.percentage}%)
              </p>
            </div>
            <div className="filter-actions">
              <button onClick={() => navigate('/history')} className="view-history-btn">
                View in History
              </button>
              <button onClick={clearFilters} className="clear-filter-btn">
                Clear Filter
              </button>
            </div>
          </div>
        )}

        {/* Heatmap Component */}
        <div className="heatmap-container">
          <DiseaseHeatmap onCellClick={handleCellClick} />
        </div>

        {/* Instructions */}
        <div className="heatmap-instructions">
          <h3>How to Use This Heatmap</h3>
          <div className="instructions-grid">
            <div className="instruction-item">
              <div className="instruction-icon">🔍</div>
              <h4>Explore Patterns</h4>
              <p>View disease occurrences over time with color-coded intensity</p>
            </div>
            <div className="instruction-item">
              <div className="instruction-icon">📊</div>
              <h4>Interactive Filtering</h4>
              <p>Click on cells to filter and see detailed information</p>
            </div>
            <div className="instruction-item">
              <div className="instruction-icon">📅</div>
              <h4>Time Selection</h4>
              <p>Choose different date ranges to analyze trends</p>
            </div>
            <div className="instruction-item">
              <div className="instruction-icon">🎨</div>
              <h4>Disease Focus</h4>
              <p>Toggle specific diseases on/off for focused analysis</p>
            </div>
            <div className="instruction-item">
              <div className="instruction-icon">💾</div>
              <h4>Export Data</h4>
              <p>Download heatmap as PNG or data as CSV for reports</p>
            </div>
            <div className="instruction-item">
              <div className="instruction-icon">📈</div>
              <h4>Statistics</h4>
              <p>View detailed breakdowns and trends at the bottom</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

// Helper function to get display name for disease - memoized
const getDiseaseDisplayName = (diseaseKey) => {
  const diseaseNames = {
    bacterial_leaf_blight: 'Bacterial Leaf Blight',
    brown_spot: 'Brown Spot',
    healthy: 'Healthy',
    leaf_blast: 'Leaf Blast',
    leaf_scald: 'Leaf Scald',
    narrow_brown_spot: 'Narrow Brown Spot',
    uncertain: 'Uncertain'
  };
  return diseaseNames[diseaseKey] || diseaseKey;
};

export default React.memo(DiseaseHeatmapPage);