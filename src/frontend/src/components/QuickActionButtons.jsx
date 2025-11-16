import React from 'react';
import { useNavigate } from 'react-router-dom';

const QuickActionButtons = ({ size = 'default', className = '' }) => {
  const navigate = useNavigate();

  const actions = [
    {
      id: 'scan',
      label: 'New Scan',
      icon: '📷',
      description: 'Upload and analyze rice leaf images',
      primary: true,
      onClick: () => navigate('/scan')
    },
    {
      id: 'history',
      label: 'View History',
      icon: '📋',
      description: 'Browse your scan history and results',
      primary: false,
      onClick: () => navigate('/history')
    },
    {
      id: 'profile',
      label: 'Profile',
      icon: '👤',
      description: 'Manage your account and preferences',
      primary: false,
      onClick: () => navigate('/profile')
    },
    {
      id: 'heatmap',
      label: 'Disease Map',
      icon: '🗺️',
      description: 'View disease distribution heatmap',
      primary: false,
      onClick: () => navigate('/heatmap')
    }
  ];

  const sizeClasses = {
    small: {
      container: 'grid grid-cols-2 gap-3',
      button: 'px-3 py-2 text-sm',
      icon: 'text-lg',
      label: 'text-xs'
    },
    default: {
      container: 'grid grid-cols-2 md:grid-cols-4 gap-4',
      button: 'px-4 py-3 text-base',
      icon: 'text-xl',
      label: 'text-sm'
    },
    large: {
      container: 'grid grid-cols-2 md:grid-cols-4 gap-6',
      button: 'px-6 py-4 text-lg',
      icon: 'text-2xl',
      label: 'text-base'
    }
  };

  const currentSize = sizeClasses[size];

  return (
    <div className={`${currentSize.container} ${className}`}>
      {actions.map((action) => (
        <button
          key={action.id}
          onClick={action.onClick}
          className={`
            group relative overflow-hidden rounded-xl
            bg-white dark:bg-gray-800
            border border-gray-200 dark:border-gray-700
            hover:border-primary-300 dark:hover:border-primary-600
            hover:shadow-lg hover:shadow-primary-500/10
            transform transition-all duration-300
            hover:scale-105 active:scale-95
            focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2
            ${currentSize.button}
          `}
        >
          {/* Gradient overlay for primary action */}
          {action.primary && (
            <div className="absolute inset-0 bg-gradient-to-r from-primary-500 to-primary-600 opacity-0 group-hover:opacity-10 transition-opacity duration-300" />
          )}

          {/* Button content */}
          <div className="relative flex flex-col items-center space-y-2">
            {/* Icon */}
            <div className={`${currentSize.icon} group-hover:scale-110 transition-transform duration-300`}>
              {action.icon}
            </div>

            {/* Label */}
            <span className={`font-medium text-gray-900 dark:text-white ${currentSize.label}`}>
              {action.label}
            </span>

            {/* Primary indicator */}
            {action.primary && (
              <div className="w-1 h-1 bg-primary-500 rounded-full group-hover:scale-150 transition-transform duration-300" />
            )}
          </div>

          {/* Hover tooltip */}
          <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-3 py-1 bg-gray-900 dark:bg-gray-100 text-white dark:text-gray-900 text-xs rounded-lg opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none whitespace-nowrap z-10">
            {action.description}
            <div className="absolute top-full left-1/2 transform -translate-x-1/2 -mt-1">
              <div className="w-0 h-0 border-l-4 border-r-4 border-t-4 border-transparent border-t-gray-900 dark:border-t-gray-100" />
            </div>
          </div>

          {/* Keyboard shortcut hint */}
          {action.id === 'scan' && (
            <div className="absolute top-2 right-2 px-1.5 py-0.5 bg-gray-100 dark:bg-gray-700 text-gray-500 dark:text-gray-400 text-xs rounded">
              ⌘S
            </div>
          )}
        </button>
      ))}
    </div>
  );
};

export default QuickActionButtons;