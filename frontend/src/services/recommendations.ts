/**
 * Recommendations Service
 * Service for getting career recommendations with various endpoints
 */
import apiClient from './apiClient';
import { BaseResponse } from './types';

/**
 * Recommendation request types
 */
export interface RecommendationConstraints {
  min_wage?: number;
  remote_preferred?: boolean;
  max_education_level?: number;
  [key: string]: any;
}

export interface RecommendationRequest {
  skills?: string[];
  skill_importance?: Record<string, number>; // 0-5 scale
  interests?: Record<string, number>; // RIASEC categories, 0-7 scale
  work_values?: Record<string, number>; // 0-7 scale
  constraints?: RecommendationConstraints;
  top_n?: number; // 1-20, default 5
  use_ml?: boolean; // default true
}

/**
 * Recommendation explanation types
 */
export interface TopFeature {
  feature: string;
  contribution: number;
  user_value: number;
  career_value: number;
}

export interface RecommendationExplanation {
  method: string;
  confidence: 'Low' | 'Med' | 'High';
  top_contributing_skills?: TopFeature[];
  why_points?: string[];
  [key: string]: any;
}

export interface OpenAIEnhancement {
  why_narrative?: string;
  refined_explanation?: string;
  [key: string]: any;
}

/**
 * Why narrative structure (can be string or object)
 */
export interface WhyNarrative {
  primary?: string;
  points?: string[];
  summary?: string;
  enhanced?: string;
  top_features?: string[];
  next_steps?: string;
  [key: string]: any;
}

/**
 * Single recommendation response
 */
export interface CareerRecommendation {
  career_id: string;
  name: string;
  soc_code: string;
  score: number;
  confidence: 'Low' | 'Med' | 'High';
  explanation: RecommendationExplanation;
  outlook?: Record<string, any>;
  education?: Record<string, any>;
  openai_enhancement?: OpenAIEnhancement;
  // Enhanced format fields
  confidence_band?: {
    level: 'Low' | 'Med' | 'High';
    score_range: [number, number];
  };
  explainability?: {
    top_features: TopFeature[];
    summary: string;
  };
  why?: string | WhyNarrative;
  [key: string]: any;
}

/**
 * Legacy recommendations response
 */
export interface RecommendationsResponse {
  recommendations: CareerRecommendation[];
  user_features: {
    num_skills_provided: number;
    interests_provided: boolean;
    values_provided: boolean;
    constraints_provided: boolean;
  };
  method: 'ml_model' | 'baseline';
}

/**
 * Enhanced recommendations response
 */
export interface EnhancedRecommendationsResponse {
  careers: CareerRecommendation[];
  alternatives: CareerRecommendation[];
  method: 'ml_model' | 'baseline';
  user_features: {
    num_skills_provided: number;
    interests_provided: boolean;
    values_provided: boolean;
    constraints_provided: boolean;
  };
}

/**
 * Model status response
 */
export interface ModelStatusResponse {
  model_loaded: boolean;
  scaler_loaded: boolean;
  model_version: string | null;
  fallback_to_baseline: boolean;
}

/**
 * Simple recommendations query parameters
 */
export interface SimpleRecommendationsParams {
  skills?: string; // Comma-separated list of skills
  top_n?: number; // 1-20, default 5
}

/**
 * POST /api/recommendations/recommendations - Enhanced recommendations
 * Returns 3-5 careers with confidence bands, explainability, alternatives, and why narrative
 */
export const getEnhancedRecommendations = async (
  request: RecommendationRequest
): Promise<EnhancedRecommendationsResponse> => {
  const response = await apiClient.post<BaseResponse<EnhancedRecommendationsResponse>>(
    '/api/recommendations/recommendations',
    {
      skills: request.skills,
      skill_importance: request.skill_importance,
      interests: request.interests,
      work_values: request.work_values,
      constraints: request.constraints,
      top_n: request.top_n ?? 5,
      use_ml: request.use_ml ?? true,
    }
  );

  if (!response.data.success) {
    throw new Error(response.data.message || 'Failed to get enhanced recommendations');
  }

  return response.data.data!;
};

/**
 * POST /api/recommendations/recommend - Legacy recommendations
 * Returns career recommendations based on user skills, interests, values, and constraints
 */
export const getRecommendations = async (
  request: RecommendationRequest
): Promise<RecommendationsResponse> => {
  const response = await apiClient.post<BaseResponse<RecommendationsResponse>>(
    '/api/recommendations/recommend',
    {
      skills: request.skills,
      skill_importance: request.skill_importance,
      interests: request.interests,
      work_values: request.work_values,
      constraints: request.constraints,
      top_n: request.top_n ?? 5,
      use_ml: request.use_ml ?? true,
    }
  );

  if (!response.data.success) {
    throw new Error(response.data.message || 'Failed to get recommendations');
  }

  return response.data.data!;
};

/**
 * GET /api/recommendations/recommend/simple - Simple recommendations (query params)
 * Quick endpoint for testing - just provide skills as comma-separated string
 */
export const getSimpleRecommendations = async (
  params: SimpleRecommendationsParams
): Promise<RecommendationsResponse> => {
  const queryParams: Record<string, string | number> = {};

  if (params.skills) {
    queryParams.skills = params.skills;
  }

  if (params.top_n !== undefined) {
    queryParams.top_n = params.top_n;
  }

  const response = await apiClient.get<BaseResponse<RecommendationsResponse>>(
    '/api/recommendations/recommend/simple',
    {
      params: queryParams,
    }
  );

  if (!response.data.success) {
    throw new Error(response.data.message || 'Failed to get simple recommendations');
  }

  return response.data.data!;
};

/**
 * GET /api/recommendations/model/status - Model status check
 * Returns status of the ML model - whether it's loaded and what version
 */
export const getModelStatus = async (): Promise<ModelStatusResponse> => {
  const response = await apiClient.get<BaseResponse<ModelStatusResponse>>(
    '/api/recommendations/model/status'
  );

  if (!response.data.success) {
    throw new Error(response.data.message || 'Failed to get model status');
  }

  return response.data.data!;
};

/**
 * Recommendations service object with all methods
 */
export const recommendationsService = {
  getEnhancedRecommendations,
  getRecommendations,
  getSimpleRecommendations,
  getModelStatus,
};

export default recommendationsService;

