/**
 * Global Application Store
 * Uses Zustand for lightweight global state management
 * Handles UI state, user profile, selected career, etc.
 */
import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import type { IntakeResponse } from '../services/intake';
import type { CareerRecommendation } from '../services/recommendations';

/**
 * Application state interface
 */
interface AppState {
  // User profile/intake data
  userProfile: IntakeResponse | null;
  setUserProfile: (profile: IntakeResponse | null) => void;

  // Selected career
  selectedCareer: CareerRecommendation | null;
  setSelectedCareer: (career: CareerRecommendation | null) => void;

  // UI state
  isLoading: boolean;
  setIsLoading: (loading: boolean) => void;

  // Error state
  error: string | null;
  setError: (error: string | null) => void;

  // Cached occupation catalog (for quick access)
  cachedCatalog: any[] | null;
  setCachedCatalog: (catalog: any[] | null) => void;

  // Reset all state
  reset: () => void;
}

/**
 * Initial state
 */
const initialState = {
  userProfile: null,
  selectedCareer: null,
  isLoading: false,
  error: null,
  cachedCatalog: null,
};

/**
 * Create Zustand store with persistence
 * User profile and selected career are persisted to localStorage
 */
export const useAppStore = create<AppState>()(
  persist(
    (set) => ({
      ...initialState,

      setUserProfile: (profile) => set({ userProfile: profile }),

      setSelectedCareer: (career) => set({ selectedCareer: career }),

      setIsLoading: (loading) => set({ isLoading: loading }),

      setError: (error) => set({ error }),

      setCachedCatalog: (catalog) => set({ cachedCatalog: catalog }),

      reset: () => set(initialState),
    }),
    {
      name: 'fairpath-app-storage',
      storage: createJSONStorage(() => localStorage),
      // Only persist user profile and selected career
      partialize: (state) => ({
        userProfile: state.userProfile,
        selectedCareer: state.selectedCareer,
      }),
    }
  )
);

