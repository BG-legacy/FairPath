/**
 * Trust & Transparency Service
 * Service for trust panel and model cards information
 */
import apiClient from './apiClient';
import { BaseResponse } from './types';

/**
 * Trust panel data types
 */
export interface TrustPanelData {
  what_is_collected: {
    description: string;
    data_types: Array<{
      type: string;
      description: string;
      source: string;
      usage: string;
    }>;
    note: string;
  };
  what_is_not_collected: {
    resumes: {
      description: string;
      details: string[];
      endpoints: string[];
    };
    personal_identifying_information: {
      description: string;
      details: string[];
    };
    user_activity: {
      description: string;
      details: string[];
    };
  };
  retention_policy: {
    resumes: {
      policy: string;
      details: string[];
    };
    user_profile_data: {
      policy: string;
      details: string[];
      note?: string;
    };
  };
  limitations: {
    data_coverage: {
      description: string;
      details: string[];
    };
    model_limitations: {
      description: string;
      details: string[];
    };
    processing_limitations: {
      description: string;
      details: string[];
    };
  };
}

/**
 * Model cards data types
 */
export interface ModelCardsData {
  datasets_used: {
    onet_database: {
      name: string;
      version: string;
      release_date: string;
      source: string;
      license: string;
      description: string;
      files_used: string[];
      coverage: string;
    };
    bls_employment_projections: {
      name: string;
      version: string;
      release_date: string;
      source: string;
      license: string;
      description: string;
      files_used: string[];
      coverage: string;
      time_horizon: string;
    };
    training_data: {
      name: string;
      description: string;
      sample_size: string;
      generation_method: string;
      note: string;
    };
  };
  model_types: {
    career_recommendation_model: {
      name: string;
      type: string;
      version: string;
      library: string;
      purpose: string;
      architecture: {
        algorithm: string;
        solver: string;
        max_iter: number;
        random_state: number;
        features: string;
        preprocessing: string;
      };
      input_features: string[];
      output: string;
    };
    baseline_model: {
      name: string;
      type: string;
      description: string;
      algorithm: string;
      usage: string;
    };
  };
  evaluation_metrics: {
    performance_metrics: {
      training_accuracy: string;
      test_accuracy: string;
      precision: string;
      recall: string;
      f1_score: string;
      evaluation_note: string;
    };
    test_set_details: {
      test_size: string;
      train_size: string;
      stratification: string;
      metrics_included: string[];
    };
    model_statistics: {
      total_features: number;
      non_zero_coefficients: number;
      interpretation: string;
    };
  };
  known_limitations: {
    training_data_limitations: {
      issue: string;
      impact: string;
      mitigation: string[];
    };
    coverage_limitations: {
      issue: string;
      impact: string;
      mitigation: string[];
    };
    data_quality_limitations: {
      issue: string;
      impact: string;
      mitigation: string[];
    };
    temporal_limitations: {
      issue: string;
      impact: string;
      mitigation: string[];
    };
    model_assumptions: {
      issue: string;
      impact: string;
      mitigation: string[];
    };
  };
  mitigation_steps: {
    model_improvement: string[];
    transparency: string[];
    fallback_mechanisms: string[];
    data_quality: string[];
  };
}

/**
 * GET /trust-panel - Trust panel data
 * Returns information about data collection, retention, and limitations
 */
export const getTrustPanel = async (): Promise<TrustPanelData> => {
  const response = await apiClient.get<BaseResponse<TrustPanelData>>('/trust-panel');
  if (!response.data.success || !response.data.data) {
    throw new Error(response.data.message || 'Failed to fetch trust panel data');
  }
  return response.data.data;
};

/**
 * GET /model-cards - Model cards information
 * Returns information about datasets, model types, evaluation metrics, and limitations
 */
export const getModelCards = async (): Promise<ModelCardsData> => {
  const response = await apiClient.get<BaseResponse<ModelCardsData>>('/model-cards');
  if (!response.data.success || !response.data.data) {
    throw new Error(response.data.message || 'Failed to fetch model cards data');
  }
  return response.data.data;
};

/**
 * Trust service object with all methods
 */
export const trustService = {
  getTrustPanel,
  getModelCards,
};

export default trustService;

