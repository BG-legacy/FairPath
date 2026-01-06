/**
 * React Query Provider
 * Sets up QueryClient with optimized configuration for the application
 */
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactNode } from 'react';

/**
 * Create QueryClient with optimized defaults and global error handling
 */
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      // Default stale time: 5 minutes
      staleTime: 5 * 60 * 1000,
      // Default garbage collection time: 30 minutes
      gcTime: 30 * 60 * 1000,
      // Retry failed requests 1 time
      retry: 1,
      // Refetch on window focus (good for keeping data fresh)
      refetchOnWindowFocus: true,
      // Don't refetch on reconnect by default (can be overridden per query)
      refetchOnReconnect: false,
      // Don't refetch on mount if data is fresh
      refetchOnMount: true,
    },
    mutations: {
      // Retry failed mutations 0 times (mutations should not be retried automatically)
      retry: 0,
    },
  },
});

interface QueryProviderProps {
  children: ReactNode;
}

/**
 * QueryProvider component
 * Wraps the app with React Query's QueryClientProvider
 */
export const QueryProvider = ({ children }: QueryProviderProps) => {
  return (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  );
};

/**
 * Export queryClient for use outside of React components
 * (e.g., in service files, for programmatic cache invalidation)
 */
export { queryClient };

