/**
 * Performance Monitoring Utility
 * Monitors and reports application performance metrics
 */

class PerformanceMonitor {
  constructor() {
    this.metrics = new Map();
    this.observers = [];
    this.enabled = process.env.NODE_ENV !== 'production';
    this.thresholds = {
      renderTime: 16.67, // 60fps target
      apiResponseTime: 2000, // 2 seconds
      imageLoadTime: 3000, // 3 seconds
      memoryUsage: 50 * 1024 * 1024, // 50MB
    };
  }

  // Initialize performance monitoring
  init() {
    if (!this.enabled) return;

    this.observeNavigation();
    this.observeResourceTiming();
    this.observeMemoryUsage();
    this.observeLongTasks();
    this.observeFirstContentfulPaint();
  }

  // Measure render performance
  measureRender(componentName, renderFn) {
    if (!this.enabled) return renderFn();

    const startTime = performance.now();
    const result = renderFn();
    const endTime = performance.now();

    const renderTime = endTime - startTime;
    this.recordMetric(`render_${componentName}`, renderTime);

    if (renderTime > this.thresholds.renderTime) {
      console.warn(`Slow render detected: ${componentName} took ${renderTime.toFixed(2)}ms`);
    }

    return result;
  }

  // Measure API response time
  measureApiCall(apiName, apiCall) {
    if (!this.enabled) return apiCall;

    const startTime = performance.now();
    return apiCall()
      .then(response => {
        const endTime = performance.now();
        const responseTime = endTime - startTime;
        this.recordMetric(`api_${apiName}`, responseTime);

        if (responseTime > this.thresholds.apiResponseTime) {
          console.warn(`Slow API response: ${apiName} took ${responseTime.toFixed(2)}ms`);
        }

        return response;
      })
      .catch(error => {
        const endTime = performance.now();
        const responseTime = endTime - startTime;
        this.recordMetric(`api_${apiName}_error`, responseTime);
        throw error;
      });
  }

  // Measure image load time
  measureImageLoad(imageUrl) {
    if (!this.enabled) return Promise.resolve();

    return new Promise((resolve, reject) => {
      const startTime = performance.now();
      const img = new Image();

      img.onload = () => {
        const endTime = performance.now();
        const loadTime = endTime - startTime;
        this.recordMetric(`image_load_${imageUrl}`, loadTime);

        if (loadTime > this.thresholds.imageLoadTime) {
          console.warn(`Slow image load: ${imageUrl} took ${loadTime.toFixed(2)}ms`);
        }

        resolve(img);
      };

      img.onerror = () => {
        const endTime = performance.now();
        const loadTime = endTime - startTime;
        this.recordMetric(`image_load_error_${imageUrl}`, loadTime);
        reject(new Error(`Failed to load image: ${imageUrl}`));
      };

      img.src = imageUrl;
    });
  }

  // Record custom metrics
  recordMetric(name, value, unit = 'ms') {
    if (!this.enabled) return;

    if (!this.metrics.has(name)) {
      this.metrics.set(name, {
        values: [],
        min: Infinity,
        max: -Infinity,
        total: 0,
        count: 0,
        unit
      });
    }

    const metric = this.metrics.get(name);
    metric.values.push({
      value,
      timestamp: performance.now()
    });
    metric.min = Math.min(metric.min, value);
    metric.max = Math.max(metric.max, value);
    metric.total += value;
    metric.count++;

    // Keep only last 100 values to prevent memory leaks
    if (metric.values.length > 100) {
      metric.values.shift();
    }
  }

  // Get performance report
  getReport() {
    if (!this.enabled) return null;

    const report = {
      timestamp: new Date().toISOString(),
      metrics: {},
      summary: {
        totalMetrics: this.metrics.size,
        memoryUsage: this.getMemoryUsage()
      }
    };

    for (const [name, metric] of this.metrics.entries()) {
      report.metrics[name] = {
        average: metric.total / metric.count,
        min: metric.min,
        max: metric.max,
        count: metric.count,
        unit: metric.unit,
        recent: metric.values.slice(-10) // Last 10 measurements
      };
    }

    return report;
  }

  // Get memory usage
  getMemoryUsage() {
    if (performance.memory) {
      return {
        used: performance.memory.usedJSHeapSize,
        total: performance.memory.totalJSHeapSize,
        limit: performance.memory.jsHeapSizeLimit,
        percentage: (performance.memory.usedJSHeapSize / performance.memory.jsHeapSizeLimit) * 100
      };
    }
    return null;
  }

  // Observe page navigation
  observeNavigation() {
    if (!('PerformanceObserver' in window)) return;

    const observer = new PerformanceObserver((list) => {
      for (const entry of list.getEntries()) {
        if (entry.entryType === 'navigation') {
          this.recordMetric('navigation_load', entry.loadEventEnd - entry.fetchStart);
          this.recordMetric('dom_content_loaded', entry.domContentLoadedEventEnd - entry.domContentLoadedEventStart);
        }
      }
    });

    observer.observe({ entryTypes: ['navigation'] });
    this.observers.push(observer);
  }

  // Observe resource timing
  observeResourceTiming() {
    if (!('PerformanceObserver' in window)) return;

    const observer = new PerformanceObserver((list) => {
      for (const entry of list.getEntries()) {
        if (entry.entryType === 'resource') {
          const url = new URL(entry.name).pathname;
          this.recordMetric(`resource_${url}`, entry.duration);
        }
      }
    });

    observer.observe({ entryTypes: ['resource'] });
    this.observers.push(observer);
  }

  // Observe memory usage
  observeMemoryUsage() {
    if (!performance.memory) return;

    setInterval(() => {
      const memory = this.getMemoryUsage();
      if (memory && memory.used > this.thresholds.memoryUsage) {
        console.warn(`High memory usage detected: ${(memory.used / 1024 / 1024).toFixed(2)}MB`);
      }
      this.recordMetric('memory_usage', memory.used, 'bytes');
    }, 30000); // Check every 30 seconds
  }

  // Observe long tasks
  observeLongTasks() {
    if (!('PerformanceObserver' in window)) return;

    const observer = new PerformanceObserver((list) => {
      for (const entry of list.getEntries()) {
        if (entry.entryType === 'longtask') {
          this.recordMetric('long_task', entry.duration);
          if (entry.duration > 50) {
            console.warn(`Long task detected: ${entry.duration.toFixed(2)}ms`);
          }
        }
      }
    });

    observer.observe({ entryTypes: ['longtask'] });
    this.observers.push(observer);
  }

  // Observe First Contentful Paint
  observeFirstContentfulPaint() {
    if (!('PerformanceObserver' in window)) return;

    const observer = new PerformanceObserver((list) => {
      for (const entry of list.getEntries()) {
        if (entry.name === 'first-contentful-paint') {
          this.recordMetric('first_contentful_paint', entry.startTime);
        }
      }
    });

    observer.observe({ entryTypes: ['paint'] });
    this.observers.push(observer);
  }

  // Measure component render time using React Profiler
  measureComponentRender(id, phase, actualDuration) {
    if (!this.enabled) return;

    this.recordMetric(`component_${id}_${phase}`, actualDuration);

    if (actualDuration > this.thresholds.renderTime) {
      console.warn(`Slow component render: ${id} ${phase} took ${actualDuration.toFixed(2)}ms`);
    }
  }

  // Create React Profiler callback
  createProfilerCallback(componentName) {
    return (id, phase, actualDuration) => {
      this.measureComponentRender(componentName, phase, actualDuration);
    };
  }

  // Clear all metrics
  clearMetrics() {
    this.metrics.clear();
  }

  // Export metrics for analysis
  exportMetrics() {
    return JSON.stringify(this.getReport(), null, 2);
  }

  // Cleanup observers
  cleanup() {
    this.observers.forEach(observer => observer.disconnect());
    this.observers = [];
    this.metrics.clear();
  }
}

// Create singleton instance
const performanceMonitor = new PerformanceMonitor();

// React hook for performance monitoring
export const usePerformanceMonitor = (componentName) => {
  return {
    measureRender: (renderFn) => performanceMonitor.measureRender(componentName, renderFn),
    measureApiCall: (apiName, apiCall) => performanceMonitor.measureApiCall(apiName, apiCall),
    measureImageLoad: (imageUrl) => performanceMonitor.measureImageLoad(imageUrl),
    recordMetric: (name, value, unit) => performanceMonitor.recordMetric(name, value, unit)
  };
};

// Profiler component for React
export const PerformanceProfiler = ({ children, componentName }) => {
  if (!performanceMonitor.enabled) {
    return children;
  }

  return React.createElement(
    React.Profiler,
    {
      id: componentName,
      onRender: performanceMonitor.createProfilerCallback(componentName)
    },
    children
  );
};

// Initialize monitoring
if (typeof window !== 'undefined') {
  performanceMonitor.init();
}

export default performanceMonitor;