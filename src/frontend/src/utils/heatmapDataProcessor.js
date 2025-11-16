// src/utils/heatmapDataProcessor.js
import { format, startOfDay, subDays, isWithinInterval, parseISO } from 'date-fns';

// Disease configuration
export const DISEASE_CONFIG = {
  bacterial_leaf_blight: {
    label: 'Bacterial Leaf Blight',
    color: '#FF6B6B',
    order: 0
  },
  brown_spot: {
    label: 'Brown Spot',
    color: '#FFA06B',
    order: 1
  },
  healthy: {
    label: 'Healthy',
    color: '#51CF66',
    order: 2
  },
  leaf_blast: {
    label: 'Leaf Blast',
    color: '#FF8E8E',
    order: 3
  },
  leaf_scald: {
    label: 'Leaf Scald',
    color: '#FFD93D',
    order: 4
  },
  narrow_brown_spot: {
    label: 'Narrow Brown Spot',
    color: '#FFB366',
    order: 5
  },
  uncertain: {
    label: 'Uncertain',
    color: '#CCCCCC',
    order: 6
  }
};

// Date range presets
export const DATE_RANGES = {
  last7days: {
    label: 'Last 7 Days',
    days: 7,
    groupBy: 'day'
  },
  last30days: {
    label: 'Last 30 Days',
    days: 30,
    groupBy: 'day'
  },
  last90days: {
    label: 'Last 90 Days',
    days: 90,
    groupBy: 'week'
  }
};

/**
 * Process scan data for heatmap visualization
 */
export function processHeatmapData(scans, dateRange, selectedDiseases = null) {
  if (!scans || scans.length === 0) {
    return {
      data: [],
      labels: { x: [], y: [] },
      metadata: { totalScans: 0, dateRange }
    };
  }

  // Filter by date range
  const endDate = new Date();
  const startDate = subDays(startOfDay(endDate), dateRange.days);

  const filteredScans = scans.filter(scan => {
    try {
      const scanDate = parseISO(scan.createdAt);
      return isWithinInterval(scanDate, { start: startDate, end: endDate });
    } catch (error) {
      return false;
    }
  });

  // Filter by selected diseases if specified
  const diseaseFilteredScans = selectedDiseases && selectedDiseases.length > 0
    ? filteredScans.filter(scan => selectedDiseases.includes(scan.label))
    : filteredScans;

  // Group scans by time period and disease
  const timeGroups = groupScansByTime(diseaseFilteredScans, dateRange.groupBy, startDate, endDate);

  // Build matrix data for Chart.js
  const { matrixData, xLabels, yLabels } = buildHeatmapMatrix(timeGroups, selectedDiseases);

  return {
    data: matrixData,
    labels: { x: xLabels, y: yLabels },
    metadata: {
      totalScans: diseaseFilteredScans.length,
      dateRange,
      startDate,
      endDate,
      diseaseBreakdown: calculateDiseaseBreakdown(diseaseFilteredScans)
    }
  };
}

/**
 * Group scans by time period (day/week)
 */
function groupScansByTime(scans, groupBy, startDate, endDate) {
  const groups = {};

  // Initialize all time periods
  const timePeriods = generateTimePeriods(groupBy, startDate, endDate);
  timePeriods.forEach(period => {
    groups[period.key] = {};
  });

  // Group scans
  scans.forEach(scan => {
    const periodKey = getTimePeriodKey(parseISO(scan.createdAt), groupBy);
    if (!groups[periodKey]) {
      groups[periodKey] = {};
    }

    if (!groups[periodKey][scan.label]) {
      groups[periodKey][scan.label] = 0;
    }
    groups[periodKey][scan.label]++;
  });

  return groups;
}

/**
 * Generate time period labels
 */
function generateTimePeriods(groupBy, startDate, endDate) {
  const periods = [];
  const current = new Date(startDate);

  while (current <= endDate) {
    const key = getTimePeriodKey(current, groupBy);
    const label = formatTimePeriod(current, groupBy);
    periods.push({ key, label, date: new Date(current) });

    if (groupBy === 'day') {
      current.setDate(current.getDate() + 1);
    } else if (groupBy === 'week') {
      current.setDate(current.getDate() + 7);
    }
  }

  return periods;
}

/**
 * Get time period key for grouping
 */
function getTimePeriodKey(date, groupBy) {
  if (groupBy === 'day') {
    return format(date, 'yyyy-MM-dd');
  } else if (groupBy === 'week') {
    // Use Monday as week start
    const monday = new Date(date);
    monday.setDate(date.getDate() - date.getDay() + 1);
    return format(monday, 'yyyy-\'W\'ww');
  }
  return format(date, 'yyyy-MM-dd');
}

/**
 * Format time period for display
 */
function formatTimePeriod(date, groupBy) {
  if (groupBy === 'day') {
    return format(date, 'MMM dd');
  } else if (groupBy === 'week') {
    return format(date, 'MMM dd');
  }
  return format(date, 'MMM dd');
}

/**
 * Build matrix data for Chart.js heatmap
 */
function buildHeatmapMatrix(timeGroups, selectedDiseases) {
  // Get disease list (filtered or all)
  const diseases = selectedDiseases && selectedDiseases.length > 0
    ? selectedDiseases
    : Object.keys(DISEASE_CONFIG).filter(key => key !== 'healthy'); // Exclude healthy from main view

  // Sort diseases by configured order
  diseases.sort((a, b) => DISEASE_CONFIG[a]?.order - DISEASE_CONFIG[b]?.order);

  const matrixData = [];
  const xLabels = [];
  const yLabels = diseases.map(disease => DISEASE_CONFIG[disease]?.label || disease);

  // Get sorted time periods
  const sortedTimeKeys = Object.keys(timeGroups).sort();

  sortedTimeKeys.forEach(timeKey => {
    xLabels.push(timeGroups[timeKey]?.label || timeKey);

    diseases.forEach((disease, diseaseIndex) => {
      const count = timeGroups[timeKey]?.[disease] || 0;

      matrixData.push({
        x: diseaseIndex,
        y: sortedTimeKeys.indexOf(timeKey),
        v: count,
        disease: disease,
        timePeriod: timeKey,
        percentage: calculatePercentage(count, timeGroups[timeKey])
      });
    });
  });

  return { matrixData, xLabels, yLabels };
}

/**
 * Calculate percentage for a disease in a time period
 */
function calculatePercentage(count, timeGroup) {
  if (!timeGroup || count === 0) return 0;

  const total = Object.values(timeGroup).reduce((sum, val) => sum + val, 0);
  return total > 0 ? Math.round((count / total) * 100) : 0;
}

/**
 * Calculate overall disease breakdown
 */
function calculateDiseaseBreakdown(scans) {
  const breakdown = {};

  scans.forEach(scan => {
    if (!breakdown[scan.label]) {
      breakdown[scan.label] = 0;
    }
    breakdown[scan.label]++;
  });

  return breakdown;
}

/**
 * Get color for intensity value
 */
export function getHeatmapColor(value, maxValue) {
  if (value === 0) return 'rgba(240, 240, 240, 0.8)'; // Very light gray for zero

  const intensity = Math.min(value / Math.max(maxValue, 1), 1);

  if (intensity < 0.33) {
    // Green to Yellow
    const ratio = intensity / 0.33;
    return `rgba(${Math.round(81 + (255 - 81) * ratio)}, ${Math.round(207 - 46 * ratio)}, ${Math.round(102 - 102 * ratio)}, 0.9)`;
  } else if (intensity < 0.67) {
    // Yellow to Orange
    const ratio = (intensity - 0.33) / 0.34;
    return `rgba(255, ${Math.round(161 - 61 * ratio)}, ${Math.round(0 + 107 * ratio)}, 0.9)`;
  } else {
    // Orange to Red
    const ratio = (intensity - 0.67) / 0.33;
    return `rgba(${Math.round(255 - 0 * ratio)}, ${Math.round(100 - 44 * ratio)}, ${Math.round(107 - 43 * ratio)}, 0.9)`;
  }
}

/**
 * Export data to CSV format
 */
export function exportToCSV(heatmapData) {
  const { data, labels } = heatmapData;

  let csv = 'Time Period,' + labels.y.join(',') + '\n';

  // Group data by y position (time period)
  const dataByY = {};
  data.forEach(item => {
    if (!dataByY[item.y]) {
      dataByY[item.y] = {};
    }
    dataByY[item.y][item.x] = item.v;
  });

  // Add rows for each time period
  labels.x.forEach((period, yIndex) => {
    const row = [period];
    labels.y.forEach((_, xIndex) => {
      row.push(dataByY[yIndex]?.[xIndex] || 0);
    });
    csv += row.join(',') + '\n';
  });

  return csv;
}