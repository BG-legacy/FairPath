# State Management Setup - Implementation Summary

## ✅ Completed Tasks

### 1. Dependencies Installed
- ✅ `@tanstack/react-query` - For server state management
- ✅ `zustand` - For global UI state management

### 2. QueryClient Provider Setup
- ✅ Created `src/providers/QueryProvider.tsx` with optimized configuration
- ✅ Integrated into `App.tsx` to wrap the entire application
- ✅ Configured default cache settings (5min stale time, 30min GC time)
- ✅ Set up refetch strategies (on window focus, on mount)

### 3. Zustand Store for Global State
- ✅ Created `src/store/useAppStore.ts` with:
  - User profile/intake data (persisted)
  - Selected career (persisted)
  - API loading states
  - Error states
  - Cached occupation catalog
- ✅ Configured localStorage persistence for user profile and selected career

### 4. Query Hooks for GET Endpoints
Created comprehensive query hooks in `src/hooks/queries/`:

- ✅ **useDataQueries.ts** - All data/catalog endpoints
  - `useOccupationCatalog()` - Get catalog with pagination
  - `useOccupationById()` - Get specific occupation
  - `useDataDictionary()` - Get data dictionary
  - `useDataStats()` - Get statistics
  - `useProcessedData()` - Get processed data
  - `useProcessedDataVersion()` - Get version info
  - `useProcessedOccupation()` - Get processed occupation

- ✅ **useRecommendationsQueries.ts**
  - `useModelStatus()` - Get ML model status

- ✅ **useOutlookQueries.ts**
  - `useCareerOutlook()` - Get career outlook
  - `useOutlookAssumptions()` - Get assumptions

- ✅ **usePathsQueries.ts**
  - `useEducationPathways()` - Get education pathways

- ✅ **useCertsQueries.ts**
  - `useCertifications()` - Get certifications

- ✅ **useTrustQueries.ts**
  - `useTrustPanel()` - Get trust panel
  - `useModelCards()` - Get model cards

- ✅ **useCareerSwitchQueries.ts**
  - `useSkillOverlap()` - Get skill overlap

### 5. Mutation Hooks for POST Endpoints
Created mutation hooks in `src/hooks/mutations/`:

- ✅ **useIntakeMutations.ts**
  - `useNormalizeUserProfile()` - Normalizes profile and updates global store

- ✅ **useRecommendationsMutations.ts**
  - `useGetEnhancedRecommendations()` - Get enhanced recommendations
  - `useGetRecommendations()` - Get recommendations (legacy)

- ✅ **useCoachMutations.ts**
  - `useGetNextSteps()` - Get coaching next steps

- ✅ **useResumeMutations.ts**
  - `useAnalyzeResume()` - Analyze resume file
  - `useRewriteResumeBullets()` - Rewrite bullets (with optimistic update support)

- ✅ **useCareerSwitchMutations.ts**
  - `useAnalyzeCareerSwitch()` - Analyze career switch
  - `useGetCareerSwitch()` - Get career switch (formatted)

### 6. Cache Configuration
- ✅ Configured per-endpoint stale times:
  - Catalog: 5 minutes
  - Occupation details: 10 minutes
  - Dictionary: 1 hour (rarely changes)
  - Outlook: 10 minutes
  - Model status: 2 minutes (can change)
- ✅ Configured garbage collection times (30min - 24hrs based on data type)
- ✅ Set up query key factories for organized cache invalidation

### 7. Refetch Strategies
- ✅ Default: Refetch on window focus (keeps data fresh)
- ✅ Default: Refetch on mount if stale
- ✅ Per-query configuration support for custom refetch behavior
- ✅ Manual refetch support via `refetch()` function

### 8. Optimistic Updates
- ✅ Added support for optimistic updates in mutation hooks
- ✅ Example implementation in `useRewriteResumeBullets()` with rollback on error

### 9. Example Implementation
- ✅ Updated `RecommendationsPage.tsx` to demonstrate usage of mutation hooks
- ✅ Shows proper error handling, loading states, and success callbacks

## File Structure

```
frontend/src/
├── hooks/
│   ├── index.ts                    # Central export for all hooks
│   ├── queries/
│   │   ├── useDataQueries.ts
│   │   ├── useRecommendationsQueries.ts
│   │   ├── useOutlookQueries.ts
│   │   ├── usePathsQueries.ts
│   │   ├── useCertsQueries.ts
│   │   ├── useTrustQueries.ts
│   │   └── useCareerSwitchQueries.ts
│   └── mutations/
│       ├── useIntakeMutations.ts
│       ├── useRecommendationsMutations.ts
│       ├── useCoachMutations.ts
│       ├── useResumeMutations.ts
│       └── useCareerSwitchMutations.ts
├── store/
│   └── useAppStore.ts              # Zustand global state store
├── providers/
│   └── QueryProvider.tsx           # React Query provider
└── pages/
    └── RecommendationsPage.tsx     # Example implementation
```

## Usage

### Import Hooks
```tsx
import { 
  useOccupationCatalog, 
  useGetEnhancedRecommendations 
} from '../hooks';
```

### Use Query Hooks
```tsx
const { data, isLoading, error } = useOccupationCatalog({ limit: 10 });
```

### Use Mutation Hooks
```tsx
const getRecommendations = useGetEnhancedRecommendations({
  onSuccess: (data) => console.log('Success!', data),
});

getRecommendations.mutate(request);
```

### Use Global Store
```tsx
import { useAppStore } from '../store/useAppStore';

const userProfile = useAppStore((state) => state.userProfile);
const setUserProfile = useAppStore((state) => state.setUserProfile);
```

## Next Steps

1. **Migrate Other Pages**: Update remaining pages to use the new hooks
   - IntakePage.tsx - Use `useNormalizeUserProfile`
   - OutlookPage.tsx - Use `useCareerOutlook`
   - PathsPage.tsx - Use `useEducationPathways`
   - CertsPage.tsx - Use `useCertifications`
   - CoachPage.tsx - Use `useGetNextSteps`
   - ResumePage.tsx - Use `useAnalyzeResume` and `useRewriteResumeBullets`
   - CareerSwitchPage.tsx - Use `useAnalyzeCareerSwitch`
   - CatalogPage.tsx - Use `useOccupationCatalog`

2. **Add React Query DevTools** (Optional):
   ```bash
   npm install @tanstack/react-query-devtools
   ```
   Then add to QueryProvider for development debugging

3. **Consider Adding**:
   - Prefetching for common queries
   - Infinite queries for paginated data
   - Query invalidation on mutations

## Documentation

See `STATE_MANAGEMENT.md` for comprehensive documentation on:
- Architecture overview
- All available hooks
- Usage examples
- Cache configuration
- Refetch strategies
- Best practices
- Migration guide


