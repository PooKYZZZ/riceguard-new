import React from 'react';

const StatsCard = ({
  title,
  value,
  subtitle,
  icon,
  color = 'primary',
  trend = null,
  loading = false,
  size = 'default' // 'default', 'small', 'large'
}) => {
  const sizeClasses = {
    small: 'p-4',
    default: 'p-6',
    large: 'p-8'
  };

  const titleSizes = {
    small: 'text-sm',
    default: 'text-sm md:text-base',
    large: 'text-base md:text-lg'
  };

  const valueSizes = {
    small: 'text-2xl',
    default: 'text-3xl md:text-4xl',
    large: 'text-4xl md:text-5xl'
  };

  const colorClasses = {
    primary: 'bg-primary-500',
    secondary: 'bg-gray-500',
    success: 'bg-green-500',
    warning: 'bg-yellow-500',
    error: 'bg-red-500',
    info: 'bg-blue-500',
    healthy: 'bg-emerald-500',
    bacterial_leaf_blight: 'bg-red-500',
    brown_spot: 'bg-amber-500',
    leaf_blast: 'bg-violet-500',
    leaf_scald: 'bg-cyan-500',
    narrow_brown_spot: 'bg-pink-500'
  };

  const textDarkClasses = {
    primary: 'text-primary-600 dark:text-primary-400',
    secondary: 'text-gray-600 dark:text-gray-400',
    success: 'text-green-600 dark:text-green-400',
    warning: 'text-yellow-600 dark:text-yellow-400',
    error: 'text-red-600 dark:text-red-400',
    info: 'text-blue-600 dark:text-blue-400',
    healthy: 'text-emerald-600 dark:text-emerald-400',
    bacterial_leaf_blight: 'text-red-600 dark:text-red-400',
    brown_spot: 'text-amber-600 dark:text-amber-400',
    leaf_blast: 'text-violet-600 dark:text-violet-400',
    leaf_scald: 'text-cyan-600 dark:text-cyan-400',
    narrow_brown_spot: 'text-pink-600 dark:text-pink-400'
  };

  if (loading) {
    return (
      <div className={`bg-white dark:bg-gray-800 rounded-xl shadow-lg border border-gray-200 dark:border-gray-700 ${sizeClasses[size]}`}>
        <div className="animate-pulse">
          <div className="flex items-center justify-between mb-4">
            <div className="h-12 w-12 bg-gray-200 dark:bg-gray-700 rounded-lg"></div>
            <div className="h-4 w-20 bg-gray-200 dark:bg-gray-700 rounded"></div>
          </div>
          <div className="h-8 w-24 bg-gray-200 dark:bg-gray-700 rounded mb-2"></div>
          <div className="h-4 w-32 bg-gray-200 dark:bg-gray-700 rounded"></div>
        </div>
      </div>
    );
  }

  return (
    <div className={`bg-white dark:bg-gray-800 rounded-xl shadow-lg border border-gray-200 dark:border-gray-700 hover:shadow-xl transition-all duration-300 ${sizeClasses[size]}`}>
      <div className="flex items-start justify-between mb-4">
        <div className={`p-3 rounded-lg ${colorClasses[color]} bg-opacity-10`}>
          <div className={`w-6 h-6 ${colorClasses[color]} rounded flex items-center justify-center text-white`}>
            {icon}
          </div>
        </div>
        {trend && (
          <div className={`flex items-center text-sm font-medium ${
            trend.value > 0 ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'
          }`}>
            <span className="mr-1">
              {trend.value > 0 ? '↑' : '↓'}
            </span>
            {Math.abs(trend.value)}%
          </div>
        )}
      </div>

      <div className="space-y-1">
        <div className={`font-bold text-gray-900 dark:text-white ${valueSizes[size]}`}>
          {value}
        </div>
        <div className={`${titleSizes[size]} text-gray-600 dark:text-gray-400 font-medium`}>
          {title}
        </div>
        {subtitle && (
          <div className={`text-xs ${textDarkClasses[color]}`}>
            {subtitle}
          </div>
        )}
      </div>
    </div>
  );
};

export default StatsCard;