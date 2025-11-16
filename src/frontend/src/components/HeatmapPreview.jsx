import React from 'react';
import { useNavigate } from 'react-router-dom';

const HeatmapPreview = ({ data = [], maxWeeks = 12, onClick, size = 'small' }) => {
  const navigate = useNavigate();

  const sizeClasses = {
    small: {
      container: 'p-4',
      title: 'text-lg',
      cell: 'w-3 h-3',
      label: 'text-xs'
    },
    default: {
      container: 'p-6',
      title: 'text-xl',
      cell: 'w-4 h-4',
      label: 'text-sm'
    },
    large: {
      container: 'p-8',
      title: 'text-2xl',
      cell: 'w-5 h-5',
      label: 'text-base'
    }
  };

  const currentSize = sizeClasses[size];

  // Ensure we have exactly maxWeeks of data
  const heatmapData = React.useMemo(() => {
    const paddedData = [...data];
    while (paddedData.length < maxWeeks) {
      paddedData.unshift({
        week: '',
        totalScans: 0,
        intensity: 0,
        diseaseCounts: {}
      });
    }
    return paddedData.slice(-maxWeeks);
  }, [data, maxWeeks]);

  const maxIntensity = Math.max(...heatmapData.map(d => d.intensity), 1);

  const handleClick = () => {
    if (onClick) {
      onClick();
    } else {
      navigate('/heatmap');
    }
  };

  const getCellColor = (intensity) => {
    if (intensity === 0) return 'bg-gray-100 dark:bg-gray-800';

    const ratio = intensity / maxIntensity;
    if (ratio < 0.2) return 'bg-green-200 dark:bg-green-900';
    if (ratio < 0.4) return 'bg-green-300 dark:bg-green-800';
    if (ratio < 0.6) return 'bg-green-400 dark:bg-green-700';
    if (ratio < 0.8) return 'bg-green-500 dark:bg-green-600';
    return 'bg-green-600 dark:bg-green-500';
  };

  const totalScans = heatmapData.reduce((sum, week) => sum + week.totalScans, 0);
  const activeWeeks = heatmapData.filter(week => week.totalScans > 0).length;

  return (
    <div
      className={`
        bg-white dark:bg-gray-800 rounded-xl shadow-lg border border-gray-200 dark:border-gray-700
        hover:shadow-xl transition-all duration-300 cursor-pointer group
        ${currentSize.container}
      `}
      onClick={handleClick}
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className={`font-bold text-gray-900 dark:text-white ${currentSize.title}`}>
            Disease Activity
          </h3>
          <p className="text-gray-500 dark:text-gray-400 text-sm">
            {activeWeeks} active weeks • {totalScans} total scans
          </p>
        </div>
        <svg
          className="w-5 h-5 text-gray-400 dark:text-gray-500 group-hover:text-gray-600 dark:group-hover:text-gray-300 transition-colors"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M9 5l7 7-7 7"
          />
        </svg>
      </div>

      {/* Heatmap Grid */}
      <div className="space-y-3">
        {/* Main heatmap row */}
        <div className="flex items-center space-x-2">
          {/* Label */}
          <span className={`text-gray-600 dark:text-gray-400 font-medium min-w-fit ${currentSize.label}`}>
            Activity
          </span>

          {/* Heatmap cells */}
          <div className="flex space-x-1 overflow-x-auto">
            {heatmapData.map((week, index) => (
              <div
                key={index}
                className={`
                  ${currentSize.cell} rounded-sm flex-shrink-0
                  ${getCellColor(week.intensity)}
                  ${week.totalScans > 0 ? 'hover:ring-2 hover:ring-primary-500 cursor-pointer' : ''}
                  transition-all duration-200
                `}
                title={week.week ? `${week.totalScans} scans` : 'No data'}
              />
            ))}
          </div>
        </div>

        {/* Disease breakdown bars */}
        <div className="space-y-2">
          {['bacterial_leaf_blight', 'leaf_blast', 'brown_spot'].map((disease) => {
            const diseaseTotal = heatmapData.reduce(
              (sum, week) => sum + (week.diseaseCounts[disease] || 0),
              0
            );

            if (diseaseTotal === 0) return null;

            const diseaseColors = {
              bacterial_leaf_blight: 'bg-red-500',
              leaf_blast: 'bg-violet-500',
              brown_spot: 'bg-amber-500'
            };

            const diseaseNames = {
              bacterial_leaf_blight: 'Leaf Blight',
              leaf_blast: 'Leaf Blast',
              brown_spot: 'Brown Spot'
            };

            const percentage = totalScans > 0 ? (diseaseTotal / totalScans) * 100 : 0;

            return (
              <div key={disease} className="flex items-center space-x-2">
                <span className={`text-gray-600 dark:text-gray-400 min-w-fit ${currentSize.label}`}>
                  {diseaseNames[disease]}
                </span>
                <div className="flex-1 bg-gray-200 dark:bg-gray-700 rounded-full h-2 overflow-hidden">
                  <div
                    className={`h-full ${diseaseColors[disease]} transition-all duration-500`}
                    style={{ width: `${Math.max(percentage, 2)}%` }}
                  />
                </div>
                <span className={`text-gray-500 dark:text-gray-400 min-w-fit ${currentSize.label}`}>
                  {diseaseTotal}
                </span>
              </div>
            );
          })}
        </div>

        {/* Activity intensity legend */}
        <div className="flex items-center justify-between pt-2 border-t border-gray-200 dark:border-gray-700">
          <span className="text-xs text-gray-500 dark:text-gray-400">Less</span>
          <div className="flex space-x-1">
            {[0, 0.2, 0.4, 0.6, 0.8, 1].map((intensity, index) => (
              <div
                key={index}
                className={`
                  ${currentSize.cell} rounded-sm
                  ${getCellColor(intensity)}
                `}
              />
            ))}
          </div>
          <span className="text-xs text-gray-500 dark:text-gray-400">More</span>
        </div>
      </div>

      {/* Click to view full heatmap hint */}
      <div className="mt-4 text-center">
        <span className="text-xs text-primary-600 dark:text-primary-400 font-medium">
          Click to view detailed heatmap →
        </span>
      </div>
    </div>
  );
};

export default HeatmapPreview;