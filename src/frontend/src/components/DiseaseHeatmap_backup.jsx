// src/components/DiseaseHeatmap.jsx
import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  Tooltip,
  Legend,
  Filler
} from 'chart.js';
import { Scatter } from 'react-chartjs-2';
import { saveAs } from 'file-saver';
import { processHeatmapData, DISEASE_CONFIG, DATE_RANGES, getHeatmapColor, exportToCSV } from '../utils/heatmapDataProcessor';
import { listScans } from '../api';
import './DiseaseHeatmap.css';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  Tooltip,
  Legend,
  Filler
);

function DiseaseHeatmap({ onCellClick }) {
  const [scans, setScans] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedDateRange, setSelectedDateRange] = useState(DATE_RANGES.last30days);
  const [selectedDiseases, setSelectedDiseases] = useState(
    Object.keys(DISEASE_CONFIG).filter(key => key !== 'healthy')
  );
  const [heatmapData, setHeatmapData] = useState(null);
  const [maxValue, setMaxValue] = useState(0);
  const chartRef = useRef(null);

  // Load scan data
  useEffect(() => {
    loadScanData();
  }, []);

  // Process data when dependencies change
  useEffect(() => {
    if (scans.length > 0) {
      const processed = processHeatmapData(scans, selectedDateRange, selectedDiseases);
      setHeatmapData(processed);

      // Calculate max value for color scaling
      const maxCount = Math.max(...processed.data.map(item => item.v), 1);
      setMaxValue(maxCount);
    }
  }, [scans, selectedDateRange, selectedDiseases]);

  const loadScanData = async () => {
    try {
      setLoading(true);
      setError(null);

      // Fetch all scans with a large page size for heatmap analysis
      let allScans = [];
      let page = 1;
      let hasMore = true;

      while (hasMore) {
        const response = await listScans(page, 100, 'createdAt', 'desc');
        allScans = [...allScans, ...response.items];
        hasMore = response.hasNext;
        page++;

        // Safety limit to prevent infinite loops
        if (page > 50) break;
      }

      setScans(allScans);
    } catch (err) {
      setError('Failed to load scan data. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  // Toggle disease selection
  const toggleDisease = (diseaseKey) => {
    setSelectedDiseases(prev => {
      if (prev.includes(diseaseKey)) {
        return prev.filter(d => d !== diseaseKey);
      } else {
        return [...prev, diseaseKey];
      }
    });
  };

  // Select all diseases
  const selectAllDiseases = () => {
    setSelectedDiseases(Object.keys(DISEASE_CONFIG).filter(key => key !== 'healthy'));
  };

  // Clear disease selection
  const clearDiseaseSelection = () => {
    setSelectedDiseases([]);
  };

  // Export as PNG
  const exportAsPNG = useCallback(() => {
    if (chartRef.current) {
      const chart = chartRef.current;
      const url = chart.toBase64Image();
      saveAs(url, `disease-heatmap-${new Date().toISOString().split('T')[0]}.png`);
    }
  }, []);

  // Export as CSV
  const exportAsCSV = useCallback(() => {
    if (heatmapData) {
      const csv = exportToCSV(heatmapData);
      const blob = new Blob([csv], { type: 'text/csv;charset=utf-8' });
      saveAs(blob, `disease-heatmap-${new Date().toISOString().split('T')[0]}.csv`);
    }
  }, [heatmapData]);

  // Handle cell click
  const handleCellClick = useCallback((elements) => {
    if (elements.length > 0 && onCellClick) {
      const element = elements[0];
      const dataPoint = heatmapData.data[element.index];
      if (dataPoint && dataPoint.v > 0) {
        onCellClick({
          disease: dataPoint.disease,
          timePeriod: dataPoint.timePeriod,
          count: dataPoint.v,
          percentage: dataPoint.percentage
        });
      }
    }
  }, [heatmapData, onCellClick]);

  // Chart configuration
  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    onClick: (event, elements) => handleCellClick(elements),
    plugins: {
      legend: {
        display: false
      },
      tooltip: {
        callbacks: {
          title: function(context) {
            const dataPoint = context[0].dataset.data[context[0].dataIndex];
            return `${DISEASE_CONFIG[dataPoint.disease]?.label || dataPoint.disease}`;
          },
          label: function(context) {
            const dataPoint = context.dataset.data[context.dataIndex];
            return [
              `Time Period: ${dataPoint.timePeriod}`,
              `Count: ${dataPoint.v}`,
              `Percentage: ${dataPoint.percentage}%`
            ];
          }
        },
        backgroundColor: 'rgba(0, 0, 0, 0.8)',
        titleColor: '#fff',
        bodyColor: '#fff',
        borderColor: '#ddd',
        borderWidth: 1,
        padding: 10,
        displayColors: false
      }
    },
    scales: {
      x: {
        type: 'category',
        labels: heatmapData?.labels?.y || [],
        title: {
          display: true,
          text: 'Disease Types',
          font: {
            size: 14,
            weight: 'bold'
          }
        },
        grid: {
          display: false
        }
      },
      y: {
        type: 'category',
        labels: heatmapData?.labels?.x || [],
        title: {
          display: true,
          text: 'Time Period',
          font: {
            size: 14,
            weight: 'bold'
          }
        },
        grid: {
          display: false
        }
      }
    },
    elements: {
      point: {
        radius: 15,
        hoverRadius: 18
      }
    }
  };

  // Prepare chart data
  const chartData = {
    datasets: [{
      data: heatmapData?.data || [],
      backgroundColor: (context) => {
        const dataPoint = context.dataset.data[context.dataIndex];
        return getHeatmapColor(dataPoint.v, maxValue);
      },
      borderColor: (context) => {
        const dataPoint = context.dataset.data[context.dataIndex];
        return dataPoint.v > 0 ? '#333' : '#ddd';
      },
      borderWidth: 1
    }]
  };

  if (loading) {
    return (
      <div className="heatmap-loading">
        <div className="loading-spinner"></div>
        <p>Loading heatmap data...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="heatmap-error">
        <h3>Error</h3>
        <p>{error}</p>
        <button onClick={loadScanData} className="retry-button">
          Retry
        </button>
      </div>
    );
  }

  if (!heatmapData || heatmapData.data.length === 0) {
    return (
      <div className="heatmap-empty">
        <h3>No Data Available</h3>
        <p>No scan data found for the selected criteria.</p>
        <button onClick={loadScanData} className="retry-button">
          Refresh Data
        </button>
      </div>
    );
  }

  return (
    <div className="disease-heatmap">
      {/* Header */}
      <div className="heatmap-header">
        <h2>Disease Heatmap Visualization</h2>
        <p className="heatmap-subtitle">
          Showing {heatmapData.metadata.totalScans} scans from {selectedDateRange.label}
        </p>
      </div>

      {/* Controls */}
      <div className="heatmap-controls">
        <div className="control-group">
          <label>Date Range:</label>
          <select
            value={selectedDateRange.label}
            onChange={(e) => {
              const range = Object.values(DATE_RANGES).find(r => r.label === e.target.value);
              if (range) setSelectedDateRange(range);
            }}
            className="date-range-select"
          >
            {Object.values(DATE_RANGES).map(range => (
              <option key={range.label} value={range.label}>
                {range.label}
              </option>
            ))}
          </select>
        </div>

        <div className="control-group">
          <label>Diseases:</label>
          <div className="disease-controls">
            <button
              onClick={selectAllDiseases}
              className="disease-control-button"
              disabled={selectedDiseases.length === Object.keys(DISEASE_CONFIG).length - 1}
            >
              Select All
            </button>
            <button
              onClick={clearDiseaseSelection}
              className="disease-control-button"
              disabled={selectedDiseases.length === 0}
            >
              Clear All
            </button>
          </div>
        </div>

        <div className="control-group">
          <label>Export:</label>
          <div className="export-controls">
            <button onClick={exportAsPNG} className="export-button">
              Export PNG
            </button>
            <button onClick={exportAsCSV} className="export-button">
              Export CSV
            </button>
          </div>
        </div>
      </div>

      {/* Disease Toggles */}
      <div className="disease-toggles">
        {Object.entries(DISEASE_CONFIG)
          .filter(([key]) => key !== 'healthy')
          .sort(([, a], [, b]) => a.order - b.order)
          .map(([key, config]) => (
            <label key={key} className="disease-toggle">
              <input
                type="checkbox"
                checked={selectedDiseases.includes(key)}
                onChange={() => toggleDisease(key)}
              />
              <span
                className="disease-color"
                style={{ backgroundColor: config.color }}
              ></span>
              <span className="disease-label">{config.label}</span>
            </label>
          ))}
      </div>

      {/* Chart */}
      <div className="heatmap-chart-container">
        <Scatter
          ref={chartRef}
          data={chartData}
          options={chartOptions}
          height={400}
        />
      </div>

      {/* Statistics */}
      <div className="heatmap-statistics">
        <h3>Statistics</h3>
        <div className="stats-grid">
          <div className="stat-item">
            <label>Total Scans:</label>
            <span>{heatmapData.metadata.totalScans}</span>
          </div>
          <div className="stat-item">
            <label>Diseases Shown:</label>
            <span>{selectedDiseases.length}</span>
          </div>
          <div className="stat-item">
            <label>Time Periods:</label>
            <span>{heatmapData.labels.x.length}</span>
          </div>
          <div className="stat-item">
            <label>Max Count:</label>
            <span>{maxValue}</span>
          </div>
        </div>

        {heatmapData.metadata.diseaseBreakdown && (
          <div className="disease-breakdown">
            <h4>Disease Breakdown</h4>
            {Object.entries(heatmapData.metadata.diseaseBreakdown)
              .sort(([, a], [, b]) => b - a)
              .map(([disease, count]) => (
                <div key={disease} className="breakdown-item">
                  <span className="disease-name">
                    {DISEASE_CONFIG[disease]?.label || disease}
                  </span>
                  <span className="disease-count">{count}</span>
                </div>
              ))}
          </div>
        )}
      </div>

      {/* Legend */}
      <div className="heatmap-legend">
        <h4>Intensity Scale</h4>
        <div className="legend-scale">
          <div className="legend-item">
            <div className="legend-color" style={{ backgroundColor: 'rgba(240, 240, 240, 0.8)' }}></div>
            <span>0 (None)</span>
          </div>
          <div className="legend-item">
            <div className="legend-color" style={{ backgroundColor: 'rgba(81, 207, 102, 0.9)' }}></div>
            <span>Low</span>
          </div>
          <div className="legend-item">
            <div className="legend-color" style={{ backgroundColor: 'rgba(255, 161, 0, 0.9)' }}></div>
            <span>Medium</span>
          </div>
          <div className="legend-item">
            <div className="legend-color" style={{ backgroundColor: 'rgba(255, 107, 107, 0.9)' }}></div>
            <span>High</span>
          </div>
        </div>
      </div>
    </div>
  );
}

export default DiseaseHeatmap;