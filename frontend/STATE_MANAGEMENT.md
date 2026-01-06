# State Management Documentation

This project uses **React Query (TanStack Query)** for server state management and **Zustand** for global UI state management.

## Architecture Overview

### React Query (TanStack Query)
- **Purpose**: Manages all server state (API calls, caching, refetching)
- **Location**: `src/hooks/queries/` and `src/hooks/mutations/`
- **Provider**: `src/providers/QueryProvider.tsx`

### Zustand
- **Purpose**: Manages global UI state (user profile, selected career, loading states)
- **Location**: `src/store/useAppStore.ts`
- **Persistence**: User profile and selected career are persisted to localStorage

## Available Hooks

### Query Hooks (GET requests)

#### Data Queries (`useDataQueries.ts`)
- `useOccupationCatalog(params?)` - Get occupation catalog with pagination
- `useOccupationById(careerId)` - Get specific occupation
- `useDataDictionary()` - Get data dictionary
- `useDataStats()` - Get data statistics
- `useProcessedData(careerId?)` - Get processed data
- `useProcessedDataVersion()` - Get processed data version
- `useProcessedOccupation(careerId)` - Get processed occupation data

#### Recommendations Queries (`useRecommendationsQueries.ts`)
- `useModelStatus()` - Get ML model status

#### Outlook Queries (`useOutlookQueries.ts`)
- `useCareerOutlook(careerId)` - Get career outlook
- `useOutlookAssumptions()` - Get outlook assumptions

#### Paths Queries (`usePathsQueries.ts`)
- `useEducationPathways(careerId)` - Get education pathways

#### Certifications Queries (`useCertsQueries.ts`)
- `useCertifications(careerId)` - Get certifications

#### Trust Queries (`useTrustQueries.ts`)
- `useTrustPanel()` - Get trust panel data
- `useModelCards()` - Get model cards data

#### Career Switch Queries (`useCareerSwitchQueries.ts`)
- `useSkillOverlap(sourceCareerId, targetCareerId)` - Get skill overlap

### Mutation Hooks (POST requests)

#### Intake Mutations (`useIntakeMutations.ts`)
- `useNormalizeUserProfile()` - Normalize user profile (updates global store on success)

#### Recommendations Mutations (`useRecommendationsMutations.ts`)
- `useGetEnhancedRecommendations()` - Get enhanced recommendations
- `useGetRecommendations()` - Get recommendations (legacy)

#### Coach Mutations (`useCoachMutations.ts`)
- `useGetNextSteps()` - Get coaching next steps

#### Resume Mutations (`useResumeMutations.ts`)
- `useAnalyzeResume()` - Analyze resume file
- `useRewriteResumeBullets()` - Rewrite resume bullets

#### Career Switch Mutations (`useCareerSwitchMutations.ts`)
- `useAnalyzeCareerSwitch()` - Analyze career switch
- `useGetCareerSwitch()` - Get career switch (formatted)

## Usage Examples

### Using Query Hooks

```tsx
import { useOccupationCatalog, useCareerOutlook } from '../hooks';

function MyComponent() {
  // Query with automatic caching and refetching
  const { data, isLoading, error, refetch } = useOccupationCatalog({
    limit: 10,
    offset: 0,
  });

  const { data: outlook } = useCareerOutlook('career-123', {
    enabled: !!selectedCareerId, // Only fetch when career is selected
  });

  if (isLoading) return <div>Loading...</div>;
  if (error) return <div>Error: {error.message}</div>;

  return <div>{/* Render data */}</div>;
}
```

### Using Mutation Hooks

```tsx
import { useNormalizeUserProfile, useGetEnhancedRecommendations } from '../hooks';

function MyComponent() {
  const normalizeProfile = useNormalizeUserProfile({
    onSuccess: (data) => {
      console.log('Profile normalized:', data);
      // Profile is automatically saved to global store
    },
    onError: (error) => {
      console.error('Failed to normalize:', error);
    },
  });

  const getRecommendations = useGetEnhancedRecommendations();

  const handleSubmit = async () => {
    // Mutations return promises
    try {
      const result = await normalizeProfile.mutateAsync({
        skills: ['JavaScript', 'React'],
        interests: ['Realistic', 'Investigative'],
      });
    } catch (error) {
      // Handle error
    }
  };

  return (
    <button
      onClick={handleSubmit}
      disabled={normalizeProfile.isPending}
    >
      {normalizeProfile.isPending ? 'Processing...' : 'Submit'}
    </button>
  );
}
```

### Using Zustand Store

```tsx
import { useAppStore } from '../store/useAppStore';

function MyComponent() {
  // Access global state
  const userProfile = useAppStore((state) => state.userProfile);
  const selectedCareer = useAppStore((state) => state.selectedCareer);
  const isLoading = useAppStore((state) => state.isLoading);

  // Access actions
  const setUserProfile = useAppStore((state) => state.setUserProfile);
  const setSelectedCareer = useAppStore((state) => state.setSelectedCareer);
  const reset = useAppStore((state) => state.reset);

  // Update state
  const handleSelectCareer = (career: CareerRecommendation) => {
    setSelectedCareer(career);
  };

  return (
    <div>
      {userProfile && <div>Profile loaded</div>}
      {selectedCareer && <div>Selected: {selectedCareer.name}</div>}
    </div>
  );
}
```

## Cache Configuration

### Default Cache Settings
- **Stale Time**: 5 minutes (data is considered fresh for 5 minutes)
- **Garbage Collection Time**: 30 minutes (unused cache is cleared after 30 minutes)
- **Retry**: 1 time for queries, 0 times for mutations
- **Refetch on Window Focus**: Enabled (keeps data fresh when user returns to tab)

### Per-Query Configuration

Each query hook accepts an `options` parameter to override defaults:

```tsx
const { data } = useOccupationCatalog(
  { limit: 10 },
  {
    staleTime: 10 * 60 * 1000, // 10 minutes
    gcTime: 60 * 60 * 1000, // 1 hour
    refetchOnWindowFocus: false, // Disable refetch on focus
  }
);
```

## Refetch Strategies

### Automatic Refetching
- **On Window Focus**: Enabled by default (keeps data fresh)
- **On Reconnect**: Disabled by default
- **On Mount**: Enabled by default (refetches if data is stale)

### Manual Refetching

```tsx
const { data, refetch } = useOccupationCatalog();

// Refetch manually
<button onClick={() => refetch()}>Refresh</button>
```

### Programmatic Cache Invalidation

```tsx
import { queryClient } from '../providers/QueryProvider';

// Invalidate all data queries
queryClient.invalidateQueries({ queryKey: ['data'] });

// Invalidate specific query
queryClient.invalidateQueries({ queryKey: ['data', 'catalog'] });
```

## Optimistic Updates

Optimistic updates are available for mutations where appropriate. For example, resume rewriting can show a loading state immediately:

```tsx
const rewriteBullets = useRewriteResumeBullets({
  onMutate: async (newData) => {
    // Cancel outgoing refetches
    await queryClient.cancelQueries({ queryKey: ['resume'] });
    
    // Snapshot previous value
    const previous = queryClient.getQueryData(['resume']);
    
    // Optimistically update
    queryClient.setQueryData(['resume'], newData);
    
    return { previous };
  },
  onError: (err, newData, context) => {
    // Rollback on error
    queryClient.setQueryData(['resume'], context?.previous);
  },
});
```

## Best Practices

1. **Use Query Hooks for GET requests**: All data fetching should use query hooks
2. **Use Mutation Hooks for POST/PUT/DELETE**: All data modifications should use mutation hooks
3. **Use Zustand for UI State**: Only use Zustand for non-server state (user selections, UI toggles, etc.)
4. **Leverage Caching**: React Query automatically caches responses - don't duplicate this logic
5. **Handle Loading States**: Always handle `isLoading` and `error` states from hooks
6. **Persist Important State**: User profile and selected career are automatically persisted

## Migration Guide

### Before (using services directly)

```tsx
const [data, setData] = useState(null);
const [isLoading, setIsLoading] = useState(false);
const [error, setError] = useState(null);

const fetchData = async () => {
  setIsLoading(true);
  try {
    const result = await dataService.getOccupationCatalog();
    setData(result);
  } catch (err) {
    setError(err);
  } finally {
    setIsLoading(false);
  }
};

useEffect(() => {
  fetchData();
}, []);
```

### After (using React Query)

```tsx
const { data, isLoading, error } = useOccupationCatalog();
// That's it! Caching, refetching, and error handling are automatic
```

## Query Keys

Query keys are organized hierarchically for easy invalidation:

- `['data']` - All data queries
- `['data', 'catalog']` - Catalog queries
- `['data', 'catalog', params]` - Specific catalog query with params
- `['recommendations']` - All recommendation queries
- `['outlook', 'career', careerId]` - Specific career outlook

This structure allows for targeted cache invalidation:

```tsx
// Invalidate all catalog queries
queryClient.invalidateQueries({ queryKey: ['data', 'catalog'] });

// Invalidate all data queries
queryClient.invalidateQueries({ queryKey: ['data'] });
```


