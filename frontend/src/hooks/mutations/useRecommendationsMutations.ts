/**
 * Recommendations Mutation Hooks
 * React Query mutation hooks for recommendation endpoints
 */
import { useMutation, UseMutationOptions } from '@tanstack/react-query';
import recommendationsService, {
  RecommendationRequest,
  EnhancedRecommendationsResponse,
  RecommendationsResponse,
} from '../../services/recommendations';

/**
 * Get enhanced recommendations mutation
 * Uses mutation instead of query because it's a POST request with variable parameters
 */
export const useGetEnhancedRecommendations = (
  options?: Omit<UseMutationOptions<EnhancedRecommendationsResponse, Error, RecommendationRequest>, 'mutationFn'>
) => {
  return useMutation({
    mutationFn: (request: RecommendationRequest) =>
      recommendationsService.getEnhancedRecommendations(request),
    ...options,
  });
};

/**
 * Get recommendations mutation (legacy)
 */
export const useGetRecommendations = (
  options?: Omit<UseMutationOptions<RecommendationsResponse, Error, RecommendationRequest>, 'mutationFn'>
) => {
  return useMutation({
    mutationFn: (request: RecommendationRequest) =>
      recommendationsService.getRecommendations(request),
    ...options,
  });
};

