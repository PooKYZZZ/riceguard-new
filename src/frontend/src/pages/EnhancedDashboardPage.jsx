import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import Navbar from '../components/navbar';
import StatsCard from '../components/StatsCard';
import RecentScanCard from '../components/RecentScanCard';
import QuickActionButtons from '../components/QuickActionButtons';
import HeatmapPreview from '../components/HeatmapPreview';
import { listScans } from '../api';
import { calculateDashboardStats, formatRelativeTime } from '../utils/dashboardStats';

const EnhancedDashboardPage = () => {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      setError(null);

      // Fetch all scans (increase pageSize to get comprehensive data)
      const response = await listScans(1, 100, 'createdAt', 'desc');
      const scans = response.data?.items || response.data || [];

      // Calculate comprehensive statistics
      const calculatedStats = calculateDashboardStats(scans);
      setStats(calculatedStats);

    } catch (error) {
      setError('Failed to load dashboard data. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleScanClick = (scan) => {
    navigate(`/scan/${scan._id}`, { state: { scan } });
  };

  const handleRefresh = () => {
    loadDashboardData();
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
        <Navbar />
        <div className="container mx-auto px-4 py-8">
          {/* Loading skeleton */}
          <div className="animate-pulse">
            <div className="h-8 w-48 bg-gray-200 dark:bg-gray-700 rounded mb-4"></div>
            <div className="h-4 w-96 bg-gray-200 dark:bg-gray-700 rounded mb-8"></div>

            {/* Stats grid skeleton */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
              {[...Array(8)].map((_, i) => (
                <div key={i} className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-lg">
                  <div className="h-6 w-24 bg-gray-200 dark:bg-gray-700 rounded mb-4"></div>
                  <div className="h-8 w-32 bg-gray-200 dark:bg-gray-700 rounded mb-2"></div>
                  <div className="h-4 w-40 bg-gray-200 dark:bg-gray-700 rounded"></div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
        <Navbar />
        <div className="container mx-auto px-4 py-8">
          <div className="text-center py-16">
            <div className="text-red-500 text-6xl mb-4">⚠️</div>
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
              Something went wrong
            </h2>
            <p className="text-gray-600 dark:text-gray-400 mb-6">{error}</p>
            <button
              onClick={handleRefresh}
              className="px-6 py-2 bg-primary-500 text-white rounded-lg hover:bg-primary-600 transition-colors"
            >
              Try Again
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <Navbar />

      {/* Main Content */}
      <div className="container mx-auto px-4 py-8 max-w-7xl">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h1 className="text-3xl md:text-4xl font-bold text-gray-900 dark:text-white">
                Dashboard
              </h1>
              <p className="text-gray-600 dark:text-gray-400 mt-2">
                Monitor your rice disease detection activity and insights
              </p>
            </div>
            <button
              onClick={handleRefresh}
              className="p-2 rounded-lg bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
              title="Refresh dashboard"
            >
              <svg className="w-5 h-5 text-gray-600 dark:text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
            </button>
          </div>

          {/* Quick stats summary */}
          {stats.lastScanDate && (
            <div className="flex items-center space-x-4 text-sm text-gray-600 dark:text-gray-400">
              <span>Last scan: {formatRelativeTime(stats.lastScanDate)}</span>
              <span>•</span>
              <span>Total accuracy: {stats.accuracyRate}%</span>
            </div>
          )}
        </div>

        {/* Main Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          {/* Total Scans */}
          <StatsCard
            title="Total Scans"
            value={stats.totalScans.toLocaleString()}
            subtitle="All time scans"
            icon="📊"
            color="primary"
            trend={{
              value: stats.weeklyTrend,
              label: 'vs last week'
            }}
          />

          {/* Today's Scans */}
          <StatsCard
            title="Today's Scans"
            value={stats.todayScans.toLocaleString()}
            subtitle="Scans completed today"
            icon="🌱"
            color="success"
          />

          {/* Accuracy Rate */}
          <StatsCard
            title="Accuracy Rate"
            value={`${stats.accuracyRate}%`}
            subtitle="High confidence predictions"
            icon="🎯"
            color="info"
          />

          {/* Top Disease */}
          <StatsCard
            title="Top Disease"
            value={stats.topDisease}
            subtitle="Most frequently detected"
            icon="🔍"
            color={getDiseaseColor(stats.topDisease?.toLowerCase()?.replace(/\s+/g, '_'))}
          />
        </div>

        {/* Disease Breakdown */}
        <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6 mb-8">
          {stats.diseaseBreakdown.slice(0, 6).map((disease) => (
            <StatsCard
              key={disease.disease}
              title={disease.name}
              value={disease.count.toLocaleString()}
              subtitle={`${disease.percentage.toFixed(1)}% of total scans • ${Math.round(disease.avgConfidence * 100)}% avg confidence`}
              icon={disease.icon}
              color={disease.color}
              size="small"
            />
          ))}
        </div>

        {/* Quick Actions */}
        <div className="mb-8">
          <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-4">Quick Actions</h2>
          <QuickActionButtons size="default" />
        </div>

        {/* Recent Scans and Heatmap */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 mb-8">
          {/* Recent Scans - takes 2 columns on large screens */}
          <div className="lg:col-span-2">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-bold text-gray-900 dark:text-white">
                Recent Scans
              </h2>
              <button
                onClick={() => navigate('/history')}
                className="text-primary-600 dark:text-primary-400 hover:text-primary-700 dark:hover:text-primary-300 font-medium text-sm"
              >
                View All →
              </button>
            </div>

            {stats.recentScans.length > 0 ? (
              <div className="space-y-4">
                {stats.recentScans.map((scan) => (
                  <RecentScanCard
                    key={scan._id}
                    scan={scan}
                    onClick={handleScanClick}
                    size="default"
                  />
                ))}
              </div>
            ) : (
              <div className="bg-white dark:bg-gray-800 rounded-xl p-8 text-center border border-gray-200 dark:border-gray-700">
                <div className="text-6xl mb-4">📷</div>
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                  No scans yet
                </h3>
                <p className="text-gray-600 dark:text-gray-400 mb-4">
                  Start by uploading your first rice leaf image for analysis
                </p>
                <button
                  onClick={() => navigate('/scan')}
                  className="px-6 py-2 bg-primary-500 text-white rounded-lg hover:bg-primary-600 transition-colors"
                >
                  New Scan
                </button>
              </div>
            )}
          </div>

          {/* Heatmap Preview - takes 1 column on large screens */}
          <div>
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-bold text-gray-900 dark:text-white">
                Activity Heatmap
              </h2>
              <button
                onClick={() => navigate('/heatmap')}
                className="text-primary-600 dark:text-primary-400 hover:text-primary-700 dark:hover:text-primary-300 font-medium text-sm"
              >
                Full View →
              </button>
            </div>
            <HeatmapPreview
              data={stats.heatmapData}
              onClick={() => navigate('/heatmap')}
              size="small"
            />
          </div>
        </div>

        {/* Health Overview */}
        <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-lg border border-gray-200 dark:border-gray-700">
          <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-4">Health Overview</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="text-center">
              <div className="text-3xl font-bold text-emerald-600 dark:text-emerald-400 mb-2">
                {stats.healthyCount}
              </div>
              <div className="text-gray-600 dark:text-gray-400">Healthy Plants</div>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold text-amber-600 dark:text-amber-400 mb-2">
                {stats.diseasedCount}
              </div>
              <div className="text-gray-600 dark:text-gray-400">Diseased Detected</div>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold text-blue-600 dark:text-blue-400 mb-2">
                {stats.totalScans > 0 ? Math.round((stats.healthyCount / stats.totalScans) * 100) : 0}%
              </div>
              <div className="text-gray-600 dark:text-gray-400">Overall Health</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

// Helper function to get disease color
function getDiseaseColor(disease) {
  const colors = {
    bacterial_leaf_blight: 'error',
    brown_spot: 'warning',
    healthy: 'success',
    leaf_blast: 'info',
    leaf_scald: 'primary',
    narrow_brown_spot: 'secondary'
  };
  return colors[disease] || 'secondary';
}

export default EnhancedDashboardPage;