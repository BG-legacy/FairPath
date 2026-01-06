/**
 * Career Switch Service
 * Service for analyzing career transitions and skill overlaps
 */
import apiClient from './apiClient';
import { BaseResponse } from './types';

/**
 * Career switch request
 */
export interface CareerSwitchRequest {
  source_career_id: string;
  target_career_id: string;
}

/**
 * Career switch by name request
 */
export interface CareerSwitchByNameRequest {
  source_career_name: string;
  target_career_name: string;
}

/**
 * Skill item structure
 */
export interface SkillItem {
  skill: string;
  source_level: number;
  target_level: number;
  gap?: number; // Only present in needs_learning
}

/**
 * Skill translation map
 */
export interface SkillTranslationMap {
  transfers_directly: SkillItem[];
  needs_learning: SkillItem[];
  optional_skills: SkillItem[];
}

/**
 * Success and risk factors
 */
export interface SuccessRiskAssessment {
  success_factors: string[];
  risk_factors: string[];
  overall_assessment?: string;
}

/**
 * Career switch analysis response (from /analyze endpoint)
 */
export interface CareerSwitchAnalysis {
  skill_overlap: {
    percentage: number;
    similarity_score: number;
  };
  transfer_map: SkillTranslationMap;
  difficulty: 'Low' | 'Medium' | 'High';
  transition_time: {
    min_months: number;
    max_months: number;
    range: string;
    note?: string;
  };
  success_risk_assessment: SuccessRiskAssessment;
  source_career: {
    career_id: string;
    name: string;
    soc_code: string;
  };
  target_career: {
    career_id: string;
    name: string;
    soc_code: string;
  };
}

/**
 * Factor item structure
 */
export interface FactorItem {
  factor: string;
  description: string;
  impact: 'positive' | 'negative';
}

/**
 * Formatted career switch response (from /switch endpoint)
 */
export interface CareerSwitchFormatted {
  overlap_percentage: number;
  difficulty: 'Low' | 'Medium' | 'High';
  transition_time_range: {
    min_months: number;
    max_months: number;
    range: string;
    note?: string;
  };
  skill_translation_map: SkillTranslationMap;
  success_factors: FactorItem[];
  risk_factors: FactorItem[];
  overall_assessment?: string;
  source_career: {
    career_id: string;
    name: string;
    soc_code: string;
  };
  target_career: {
    career_id: string;
    name: string;
    soc_code: string;
  };
}

/**
 * Skill overlap response (from /overlap endpoint)
 */
export interface SkillOverlap {
  overlap_percentage: number;
  similarity_score: number;
  transfer_map: SkillTranslationMap;
  source_career: {
    career_id: string;
    name: string;
  };
  target_career: {
    career_id: string;
    name: string;
  };
}

/**
 * POST /api/career-switch/analyze - Analyze career switch
 * Returns detailed analysis of career transition including skill overlap, transfer map, difficulty, and time estimates
 */
export const analyzeCareerSwitch = async (
  request: CareerSwitchRequest
): Promise<CareerSwitchAnalysis> => {
  const response = await apiClient.post<BaseResponse<CareerSwitchAnalysis>>(
    '/api/career-switch/analyze',
    request
  );

  if (!response.data.success) {
    throw new Error(response.data.message || 'Failed to analyze career switch');
  }

  return response.data.data!;
};

/**
 * POST /api/career-switch/switch - Career switch (formatted response)
 * Returns formatted career switch analysis with overlap percentage, difficulty, transition time, and skill translation map
 */
export const getCareerSwitch = async (
  request: CareerSwitchRequest
): Promise<CareerSwitchFormatted> => {
  const response = await apiClient.post<BaseResponse<CareerSwitchFormatted>>(
    '/api/career-switch/switch',
    request
  );

  if (!response.data.success) {
    throw new Error(response.data.message || 'Failed to get career switch analysis');
  }

  return response.data.data!;
};

/**
 * POST /api/career-switch/switch-by-name - Career switch using career names directly
 * Uses OpenAI to generate analysis based on the career names provided (no database lookup)
 */
export const getCareerSwitchByName = async (
  request: CareerSwitchByNameRequest
): Promise<CareerSwitchFormatted> => {
  const response = await apiClient.post<BaseResponse<CareerSwitchFormatted>>(
    '/api/career-switch/switch-by-name',
    request
  );

  if (!response.data.success) {
    throw new Error(response.data.message || 'Failed to get career switch analysis');
  }

  return response.data.data!;
};

/**
 * GET /api/career-switch/overlap - Get skill overlap (query params)
 * Quick endpoint for just the overlap data between two careers
 */
export const getSkillOverlap = async (
  source: string,
  target: string
): Promise<SkillOverlap> => {
  const response = await apiClient.get<BaseResponse<SkillOverlap>>(
    '/api/career-switch/overlap',
    {
      params: {
        source,
        target,
      },
    }
  );

  if (!response.data.success) {
    throw new Error(response.data.message || 'Failed to get skill overlap');
  }

  return response.data.data!;
};

/**
 * Career switch service object with all methods
 */
export const careerSwitchService = {
  analyzeCareerSwitch,
  getCareerSwitch,
  getCareerSwitchByName,
  getSkillOverlap,
};

export default careerSwitchService;

