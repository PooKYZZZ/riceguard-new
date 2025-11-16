// Data aggregation utilities for dashboard statistics

export const DISEASE_CATEGORIES = {
  bacterial_leaf_blight: {
    name: 'Bacterial Leaf Blight',
    color: 'bacterial_leaf_blight',
    icon: '🔴',
    description: 'Bacterial infection causing leaf blight'
  },
  brown_spot: {
    name: 'Brown Spot',
    color: 'brown_spot',
    icon: '🟠',
    description: 'Fungal disease causing brown spots'
  },
  healthy: {
    name: 'Healthy',
    color: 'healthy',
    icon: '🟢',
    description: 'Healthy rice plant'
  },
  leaf_blast: {
    name: 'Leaf Blast',
    color: 'leaf_blast',
    icon: '🟣',
    description: 'Fungal disease causing leaf lesions'
  },
  leaf_scald: {
    name: 'Leaf Scald',
    color: 'leaf_scald',
    icon: '🔵',
    description: 'Bacterial disease causing scalding'
  },
  narrow_brown_spot: {
    name: 'Narrow Brown Spot',
    color: 'narrow_brown_spot',
    icon: '🟤',
    description: 'Fungal disease causing narrow brown spots'
  }
};

/**
 * Calculate comprehensive dashboard statistics from scan data
 */
export function calculateDashboardStats(scans = []) {
  if (!Array.isArray(scans)) {
    return getEmptyStats();
  }

  const now = new Date();
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  const thisWeek = new Date(today);
  thisWeek.setDate(today.getDate() - today.getDay()); // Start of week
  const thisMonth = new Date(now.getFullYear(), now.getMonth(), 1);

  // Filter scans by time periods
  const todayScans = scans.filter(scan => new Date(scan.createdAt) >= today);
  const thisWeekScans = scans.filter(scan => new Date(scan.createdAt) >= thisWeek);
  const thisMonthScans = scans.filter(scan => new Date(scan.createdAt) >= thisMonth);

  // Calculate disease counts
  const diseaseCounts = {};
  const diseaseConfidence = {};

  scans.forEach(scan => {
    const disease = scan.prediction?.disease || 'unknown';
    const confidence = scan.prediction?.confidence || 0;

    diseaseCounts[disease] = (diseaseCounts[disease] || 0) + 1;

    if (!diseaseConfidence[disease]) {
      diseaseConfidence[disease] = { total: 0, count: 0 };
    }
    diseaseConfidence[disease].total += confidence;
    diseaseConfidence[disease].count += 1;
  });

  // Calculate average confidence per disease
  const avgConfidence = {};
  Object.entries(diseaseConfidence).forEach(([disease, data]) => {
    avgConfidence[disease] = data.count > 0 ? data.total / data.count : 0;
  });

  // Find top disease
  const topDisease = Object.entries(diseaseCounts)
    .sort(([,a], [,b]) => b - a)[0]?.[0] || 'none';

  // Calculate accuracy rate (confidence > 0.8)
  const highConfidenceScans = scans.filter(scan =>
    (scan.prediction?.confidence || 0) > 0.8
  );
  const accuracyRate = scans.length > 0 ? (highConfidenceScans.length / scans.length) : 0;

  // Calculate trends (compare this week to last week)
  const lastWeek = new Date(thisWeek);
  lastWeek.setDate(thisWeek.getDate() - 7);
  const lastWeekScans = scans.filter(scan => {
    const scanDate = new Date(scan.createdAt);
    return scanDate >= lastWeek && scanDate < thisWeek;
  });

  const weeklyTrend = lastWeekScans.length > 0
    ? ((thisWeekScans.length - lastWeekScans.length) / lastWeekScans.length) * 100
    : 0;

  // Get recent scans (last 6, sorted by date)
  const recentScans = scans
    .slice()
    .sort((a, b) => new Date(b.createdAt) - new Date(a.createdAt))
    .slice(0, 6);

  // Calculate disease breakdown with percentages
  const diseaseBreakdown = Object.entries(diseaseCounts)
    .filter(([disease]) => disease !== 'unknown')
    .map(([disease, count]) => ({
      disease,
      count,
      percentage: scans.length > 0 ? (count / scans.length) * 100 : 0,
      avgConfidence: avgConfidence[disease] || 0,
      ...DISEASE_CATEGORIES[disease] || {
        name: disease.charAt(0).toUpperCase() + disease.slice(1).replace(/_/g, ' '),
        color: 'secondary',
        icon: '❓',
        description: 'Unknown disease'
      }
    }))
    .sort((a, b) => b.count - a.count);

  // Generate heatmap data (simplified for preview)
  const heatmapData = generateHeatmapData(scans);

  return {
    totalScans: scans.length,
    todayScans: todayScans.length,
    thisWeekScans: thisWeekScans.length,
    thisMonthScans: thisMonthScans.length,
    weeklyTrend: Math.round(weeklyTrend),
    accuracyRate: Math.round(accuracyRate * 100),
    topDisease: topDisease === 'none' ? 'None' : DISEASE_CATEGORIES[topDisease]?.name || topDisease,
    diseaseCounts,
    diseaseBreakdown,
    avgConfidence,
    recentScans,
    heatmapData,
    // Additional computed stats
    healthyCount: diseaseCounts.healthy || 0,
    diseasedCount: Object.entries(diseaseCounts)
      .filter(([disease]) => disease !== 'healthy' && disease !== 'unknown')
      .reduce((sum, [, count]) => sum + count, 0),
    mostConfidentPrediction: scans.reduce((best, scan) => {
      const confidence = scan.prediction?.confidence || 0;
      return confidence > (best?.prediction?.confidence || 0) ? scan : best;
    }, null),
    lastScanDate: scans.length > 0 ? new Date(Math.max(...scans.map(s => new Date(s.createdAt)))) : null
  };
}

/**
 * Generate empty stats structure
 */
function getEmptyStats() {
  return {
    totalScans: 0,
    todayScans: 0,
    thisWeekScans: 0,
    thisMonthScans: 0,
    weeklyTrend: 0,
    accuracyRate: 0,
    topDisease: 'None',
    diseaseCounts: {},
    diseaseBreakdown: [],
    avgConfidence: {},
    recentScans: [],
    heatmapData: [],
    healthyCount: 0,
    diseasedCount: 0,
    mostConfidentPrediction: null,
    lastScanDate: null
  };
}

/**
 * Generate simplified heatmap data for dashboard preview
 */
function generateHeatmapData(scans) {
  const heatmapData = [];
  const now = new Date();

  // Generate data for the last 12 weeks
  for (let week = 11; week >= 0; week--) {
    const weekStart = new Date(now);
    weekStart.setDate(now.getDate() - (week * 7) - now.getDay());
    weekStart.setHours(0, 0, 0, 0);

    const weekEnd = new Date(weekStart);
    weekEnd.setDate(weekStart.getDate() + 7);

    const weekScans = scans.filter(scan => {
      const scanDate = new Date(scan.createdAt);
      return scanDate >= weekStart && scanDate < weekEnd;
    });

    // Count diseases in this week
    const weekDiseaseCounts = {};
    weekScans.forEach(scan => {
      const disease = scan.prediction?.disease || 'unknown';
      weekDiseaseCounts[disease] = (weekDiseaseCounts[disease] || 0) + 1;
    });

    heatmapData.push({
      week: weekStart.toISOString().split('T')[0],
      totalScans: weekScans.length,
      diseaseCounts: weekDiseaseCounts,
      intensity: Math.min(weekScans.length / 10, 1) // Normalize to 0-1
    });
  }

  return heatmapData;
}

/**
 * Format date for display
 */
export function formatDate(dateString, options = {}) {
  const date = new Date(dateString);

  const defaultOptions = {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  };

  return date.toLocaleDateString('en-US', { ...defaultOptions, ...options });
}

/**
 * Format relative time (e.g., "2 hours ago", "3 days ago")
 */
export function formatRelativeTime(dateString) {
  const date = new Date(dateString);
  const now = new Date();
  const diffMs = now - date;
  const diffMins = Math.floor(diffMs / (1000 * 60));
  const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

  if (diffMins < 1) return 'Just now';
  if (diffMins < 60) return `${diffMins} minute${diffMins !== 1 ? 's' : ''} ago`;
  if (diffHours < 24) return `${diffHours} hour${diffHours !== 1 ? 's' : ''} ago`;
  if (diffDays < 7) return `${diffDays} day${diffDays !== 1 ? 's' : ''} ago`;

  return formatDate(dateString, { month: 'short', day: 'numeric' });
}

/**
 * Get disease color from disease key
 */
export function getDiseaseColor(disease) {
  return DISEASE_CATEGORIES[disease]?.color || 'secondary';
}

/**
 * Get disease icon from disease key
 */
export function getDiseaseIcon(disease) {
  return DISEASE_CATEGORIES[disease]?.icon || '❓';
}

/**
 * Get disease name from disease key
 */
export function getDiseaseName(disease) {
  return DISEASE_CATEGORIES[disease]?.name || disease?.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()) || 'Unknown';
}

/**
 * Calculate percentage with proper rounding
 */
export function calculatePercentage(value, total, decimals = 1) {
  if (total === 0) return 0;
  return Number(((value / total) * 100).toFixed(decimals));
}