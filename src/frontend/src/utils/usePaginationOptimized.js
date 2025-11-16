/**
 * Optimized Pagination Hook
 * Provides efficient pagination with caching and performance optimizations
 */

import { useState, useEffect, useCallback, useMemo } from 'react';
import { debounce } from 'lodash';

// Cache for storing paginated data
const paginationCache = new Map();

const usePaginationOptimized = (
  fetchFunction,
  options = {
    pageSize: 20,
    cacheSize: 5, // Number of pages to cache
    debounceMs: 300,
    initialPage: 1
  }
) => {
  const {
    pageSize = 20,
    cacheSize = 5,
    debounceMs = 300,
    initialPage = 1
  } = options;

  const [currentPage, setCurrentPage] = useState(initialPage);
  const [totalItems, setTotalItems] = useState(0);
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [filters, setFilters] = useState({});
  const [sortBy, setSortBy] = useState('createdAt');
  const [sortOrder, setSortOrder] = useState('desc');

  // Generate cache key based on filters and sort
  const cacheKey = useMemo(() => {
    return JSON.stringify({ filters, sortBy, sortOrder, pageSize });
  }, [filters, sortBy, sortOrder, pageSize]);

  // Get cached data or null if not available
  const getCachedData = useCallback((page) => {
    const pageKey = `${cacheKey}_page_${page}`;
    return paginationCache.get(pageKey) || null;
  }, [cacheKey]);

  // Cache data with size limit
  const setCachedData = useCallback((page, data) => {
    const pageKey = `${cacheKey}_page_${page}`;
    paginationCache.set(pageKey, data);

    // Implement cache size limit - remove oldest entries
    if (paginationCache.size > cacheSize) {
      const keysToDelete = Array.from(paginationCache.keys())
        .filter(key => key.startsWith(cacheKey))
        .slice(0, -cacheSize);

      keysToDelete.forEach(key => paginationCache.delete(key));
    }
  }, [cacheKey, cacheSize]);

  // Debounced fetch function to prevent rapid API calls
  const debouncedFetch = useMemo(
    () => debounce(async (page, fetchOptions) => {
      try {
        setLoading(true);
        setError(null);

        // Check cache first
        const cachedData = getCachedData(page);
        if (cachedData && !fetchOptions?.forceRefresh) {
          setItems(cachedData.items);
          setTotalItems(cachedData.total);
          setLoading(false);
          return;
        }

        // Fetch from API
        const response = await fetchFunction(page, pageSize, sortBy, sortOrder, filters);

        // Validate response
        if (!response || !Array.isArray(response.items)) {
          throw new Error('Invalid response format');
        }

        const { items: fetchedItems, total } = response;

        setItems(fetchedItems);
        setTotalItems(total);

        // Cache the results
        setCachedData(page, { items: fetchedItems, total });

      } catch (err) {
        setError(err.message || 'Failed to fetch data');
        setItems([]);
        setTotalItems(0);
      } finally {
        setLoading(false);
      }
    }, debounceMs),
    [fetchFunction, pageSize, sortBy, sortOrder, filters, getCachedData, setCachedData, debounceMs]
  );

  // Initial data fetch
  useEffect(() => {
    debouncedFetch(currentPage);
    return () => debouncedFetch.cancel();
  }, [currentPage, debouncedFetch]);

  // Optimized page navigation functions
  const goToPage = useCallback((page) => {
    if (page >= 1 && page <= totalPages && page !== currentPage) {
      setCurrentPage(page);
    }
  }, [currentPage, totalPages]);

  const nextPage = useCallback(() => {
    goToPage(currentPage + 1);
  }, [currentPage, goToPage]);

  const prevPage = useCallback(() => {
    goToPage(currentPage - 1);
  }, [currentPage, goToPage]);

  const firstPage = useCallback(() => {
    goToPage(1);
  }, [goToPage]);

  const lastPage = useCallback(() => {
    goToPage(totalPages);
  }, [goToPage, totalPages]);

  // Refresh current page
  const refresh = useCallback(() => {
    debouncedFetch(currentPage, { forceRefresh: true });
  }, [currentPage, debouncedFetch]);

  // Update filters with debouncing
  const updateFilters = useCallback((newFilters) => {
    setFilters(prev => ({ ...prev, ...newFilters }));
    setCurrentPage(1); // Reset to first page when filters change
  }, []);

  // Clear all filters
  const clearFilters = useCallback(() => {
    setFilters({});
    setCurrentPage(1);
  }, []);

  // Update sorting
  const updateSorting = useCallback((newSortBy, newSortOrder = 'desc') => {
    setSortBy(newSortBy);
    setSortOrder(newSortOrder);
    setCurrentPage(1); // Reset to first page when sort changes
  }, []);

  // Memoized pagination calculations
  const paginationInfo = useMemo(() => {
    const totalPages = Math.ceil(totalItems / pageSize);
    const hasNextPage = currentPage < totalPages;
    const hasPrevPage = currentPage > 1;
    const startIndex = (currentPage - 1) * pageSize;
    const endIndex = Math.min(startIndex + pageSize, totalItems);

    return {
      totalPages,
      hasNextPage,
      hasPrevPage,
      startIndex,
      endIndex,
      currentPage,
      pageSize,
      totalItems
    };
  }, [totalItems, pageSize, currentPage]);

  // Generate page numbers for pagination controls
  const pageNumbers = useMemo(() => {
    const { totalPages, currentPage } = paginationInfo;
    const delta = 2; // Number of pages to show on each side of current page
    const range = [];
    const rangeWithDots = [];

    for (let i = Math.max(2, currentPage - delta); i <= Math.min(totalPages - 1, currentPage + delta); i++) {
      range.push(i);
    }

    if (currentPage - delta > 2) {
      rangeWithDots.push(1, '...');
    } else {
      rangeWithDots.push(1);
    }

    rangeWithDots.push(...range);

    if (currentPage + delta < totalPages - 1) {
      rangeWithDots.push('...', totalPages);
    } else if (currentPage + delta < totalPages) {
      rangeWithDots.push(totalPages);
    }

    return rangeWithDots;
  }, [paginationInfo]);

  // Preload next page for better UX
  const preloadNextPage = useCallback(() => {
    const { hasNextPage, currentPage } = paginationInfo;
    if (hasNextPage && !getCachedData(currentPage + 1)) {
      debouncedFetch(currentPage + 1);
    }
  }, [paginationInfo, getCachedData, debouncedFetch]);

  // Clear cache when component unmounts or cache key changes
  useEffect(() => {
    return () => {
      // Optional: Clear cache when filters/sort changes significantly
      if (filters && Object.keys(filters).length > 0) {
        // You might want to clear cache when major filter changes happen
      }
    };
  }, [cacheKey, filters]);

  return {
    // State
    items,
    loading,
    error,
    currentPage,
    totalItems,

    // Computed
    ...paginationInfo,
    pageNumbers,

    // Actions
    goToPage,
    nextPage,
    prevPage,
    firstPage,
    lastPage,
    refresh,
    updateFilters,
    clearFilters,
    updateSorting,
    preloadNextPage,

    // Filters and sort state
    filters,
    sortBy,
    sortOrder,

    // Utilities
    isEmpty: items.length === 0 && !loading,
    isFirstLoad: currentPage === 1 && items.length === 0 && !loading && !error
  };
};

export default usePaginationOptimized;