/**
 * useRecommendationForm Hook
 * Example hook demonstrating React Hook Form usage with validation schemas
 */
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { recommendationRequestSchema, RecommendationRequestInput } from '../schemas/validation';
import { RecommendationRequest } from '../services/recommendations';

const defaultValues: RecommendationRequestInput = {
  skills: [],
  interests: {},
  work_values: {
    impact: 3.5,
    stability: 3.5,
    flexibility: 3.5,
  },
  constraints: {},
  top_n: 5,
  use_ml: true,
};

export function useRecommendationForm() {
  const form = useForm({
    resolver: zodResolver(recommendationRequestSchema),
    defaultValues,
    mode: 'onChange', // Validate on change for better UX
  });

  // Helper to convert form data to API request format
  const getRequestData = (): RecommendationRequest => {
    const data = form.getValues();
    return {
      skills: data.skills && data.skills.length > 0 ? data.skills : undefined,
      interests: data.interests && Object.keys(data.interests).length > 0 ? data.interests : undefined,
      work_values: data.work_values,
      constraints: data.constraints && Object.keys(data.constraints).length > 0 ? data.constraints : undefined,
      top_n: data.top_n,
      use_ml: data.use_ml,
    };
  };

  return {
    ...form,
    getRequestData,
  };
}

