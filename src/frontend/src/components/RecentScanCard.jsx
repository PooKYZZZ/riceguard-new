import React from 'react';
import { buildImageUrl } from '../api';
import { formatRelativeTime, getDiseaseIcon, getDiseaseName } from '../utils/dashboardStats';

const RecentScanCard = ({ scan, onClick, size = 'default' }) => {
  const disease = scan.prediction?.disease || 'unknown';
  const confidence = Math.round((scan.prediction?.confidence || 0) * 100);
  const imageUrl = buildImageUrl(scan.imageFilename);

  const sizeClasses = {
    small: 'p-3',
    default: 'p-4',
    large: 'p-6'
  };

  const imageSizes = {
    small: 'h-20 w-20',
    default: 'h-24 w-24',
    large: 'h-32 w-32'
  };

  const textSizes = {
    small: 'text-xs',
    default: 'text-sm',
    large: 'text-base'
  };

  const diseaseColors = {
    bacterial_leaf_blight: 'bg-red-500',
    brown_spot: 'bg-amber-500',
    healthy: 'bg-emerald-500',
    leaf_blast: 'bg-violet-500',
    leaf_scald: 'bg-cyan-500',
    narrow_brown_spot: 'bg-pink-500',
    unknown: 'bg-gray-500'
  };

  const handleImageError = (e) => {
    e.target.src = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTAwIiBoZWlnaHQ9IjEwMCIgdmlld0JveD0iMCAwIDEwMCAxMDAiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+CjxyZWN0IHdpZHRoPSIxMDAiIGhlaWdodD0iMTAwIiBmaWxsPSIjRjNGNEY2Ii8+CjxwYXRoIGQ9Ik01MCAzMUMzOS43MTUzIDMxIDMyIDM4LjcxNTMgMzIgNDlDzIgNTkuMjg0NyAzOS43MTUzIDY3IDUwIDY3QzYwLjI4NDcgNjcgNjggNTkuMjg0NyA2OCA0OUM2OCAzOC43MTUzIDYwLjI4NDcgMzEgNTAgMzFaIiBzdHJva2U9IiM5Q0EzQUYiIHN0cm9rZS13aWR0aD0iMiIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIiBzdHJva2UtbGluZWpvaW49InJvdW5kIi8+CjxwYXRoIGQ9Ik00MSA0NUw0NSA0OUw1MSA0M0w1NyA1MUw2MSA0NyIgc3Ryb2tlPSIjOUNBM0FGIiBzdHJva2Utd2lkdGg9IjIiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIgc3Ryb2tlLWxpbmVqb2luPSJyb3VuZCIvPgo8L3N2Zz4=';
  };

  return (
    <div
      className={`bg-white dark:bg-gray-800 rounded-xl shadow-lg border border-gray-200 dark:border-gray-700 hover:shadow-xl transition-all duration-300 cursor-pointer ${sizeClasses[size]}`}
      onClick={() => onClick && onClick(scan)}
    >
      <div className="flex items-start space-x-4">
        {/* Scan Image Thumbnail */}
        <div className={`relative ${imageSizes[size]} rounded-lg overflow-hidden flex-shrink-0 bg-gray-100 dark:bg-gray-700`}>
          <img
            src={imageUrl}
            alt="Scan result"
            className="w-full h-full object-cover"
            onError={handleImageError}
          />
          {/* Disease Badge Overlay */}
          <div className="absolute top-2 right-2 w-3 h-3 rounded-full bg-white dark:bg-gray-800 border-2 border-white dark:border-gray-800">
            <div className={`w-full h-full rounded-full ${diseaseColors[disease]}`} />
          </div>
        </div>

        {/* Scan Information */}
        <div className="flex-1 min-w-0">
          {/* Disease Name with Icon */}
          <div className="flex items-center space-x-2 mb-2">
            <span className="text-lg">{getDiseaseIcon(disease)}</span>
            <h3 className={`font-semibold text-gray-900 dark:text-white ${textSizes[size]}`}>
              {getDiseaseName(disease)}
            </h3>
          </div>

          {/* Confidence Badge */}
          <div className="inline-flex items-center space-x-1 mb-2">
            <div className={`px-2 py-1 rounded-full text-xs font-medium ${
              confidence >= 80
                ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
                : confidence >= 60
                ? 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200'
                : 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'
            }`}>
              {confidence}% confidence
            </div>
          </div>

          {/* Timestamp */}
          <div className="flex flex-col space-y-1">
            <time className={`text-gray-500 dark:text-gray-400 ${textSizes[size]}`}>
              {formatRelativeTime(scan.createdAt)}
            </time>
            {scan.notes && (
              <p className={`text-gray-600 dark:text-gray-300 ${textSizes[size]} line-clamp-2`}>
                {scan.notes}
              </p>
            )}
          </div>

          {/* Additional Metadata */}
          <div className="flex items-center space-x-4 mt-3">
            {scan.modelVersion && (
              <span className={`text-gray-400 dark:text-gray-500 ${textSizes[size]}`}>
                v{scan.modelVersion}
              </span>
            )}
            {scan.location && (
              <span className={`text-gray-400 dark:text-gray-500 ${textSizes[size]}`}>
                📍 {scan.location}
              </span>
            )}
          </div>
        </div>

        {/* Quick Action Arrow */}
        <div className="flex-shrink-0">
          <svg
            className="w-5 h-5 text-gray-400 dark:text-gray-500"
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
      </div>

      {/* Disease Color Indicator Bar */}
      <div className="mt-4 h-1 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
        <div
          className={`h-full ${diseaseColors[disease]} transition-all duration-500`}
          style={{ width: `${confidence}%` }}
        />
      </div>
    </div>
  );
};

export default RecentScanCard;