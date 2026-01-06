/**
 * Intake Mutation Hooks
 * React Query mutation hooks for user intake/profile endpoints
 */
import { useMutation, UseMutationOptions } from '@tanstack/react-query';
import intakeService, { IntakeRequest, IntakeResponse } from '../../services/intake';
import { useAppStore } from '../../store/useAppStore';

/**
 * Normalize user profile mutation
 * Updates global store with normalized profile on success
 */
export const useNormalizeUserProfile = (
  options?: Omit<UseMutationOptions<IntakeResponse, Error, IntakeRequest>, 'mutationFn'>
) => {
  const setUserProfile = useAppStore((state) => state.setUserProfile);

  return useMutation({
    mutationFn: (request: IntakeRequest) => intakeService.normalizeUserProfile(request),
    onSuccess: (data) => {
      // Update global store with normalized profile
      setUserProfile(data);
    },
    ...options,
  });
};

