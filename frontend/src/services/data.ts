/**
 * Data Services
 * Service for accessing occupation catalog, data dictionary, and processed data
 */
import apiClient from './apiClient';
import { BaseResponse } from './types';

/**
 * Occupation types
 */
export interface Occupation {
  career_id: string;
  name: string;
  soc_code: string;
  description: string;
  onet_soc_code?: string;
  alternate_titles?: string[];
  job_zone?: number;
  created_at: string;
}

export interface Skill {
  skill_id: string;
  skill_name: string;
  element_id?: string;
  importance?: number;
  level?: number;
  soc_code: string;
}

export interface Task {
  task_id: string;
  task_description: string;
  task_type?: string;
  soc_code: string;
  incumbents_responding?: number;
}

export interface BLSProjection {
  soc_code: string;
  occupation_title: string;
  employment_2024?: number;
  employment_2034?: number;
  change_2024_2034?: number;
  percent_change?: number;
  annual_openings?: number;
  median_wage_2024?: number;
  typical_education?: string;
}

export interface OccupationCatalog {
  occupation: Occupation;
  skills: Skill[];
  tasks: Task[];
  bls_projection?: BLSProjection;
}

/**
 * Data dictionary types
 */
export interface DataDictionaryColumn {
  name: string;
  description: string;
  type: string;
}

export interface DataDictionary {
  file_name: string;
  file_type: string; // "O*NET" or "BLS"
  description: string;
  columns: DataDictionaryColumn[];
  source: string;
  last_updated?: string;
}

/**
 * Catalog response types
 */
export interface CatalogResponse {
  total: number;
  count: number;
  offset: number;
  occupations: OccupationCatalog[];
}

export interface OpenAICareerSearchResult {
  occupation: Occupation;
  match_explanation?: string;
  match_score?: number;
}

export interface OpenAICareerSearchResponse {
  count: number;
  query: string;
  results: OpenAICareerSearchResult[];
}

/**
 * Data statistics types
 */
export interface DataStats {
  total_occupations: number;
  total_skills: number;
  unique_skills: number;
  total_tasks: number;
  occupations_with_bls_data: number;
  occupations_with_skills: number;
  occupations_with_tasks: number;
}

/**
 * Processed data types
 */
export interface ProcessedOccupation {
  career_id: string;
  skill_vector?: number[];
  task_features?: Record<string, any>;
  outlook_features?: Record<string, any>;
  education_data?: Record<string, any>;
  [key: string]: any;
}

export interface ProcessedDataResponse {
  version: string;
  processed_date?: string;
  num_occupations: number;
  num_skills?: number;
  occupations: ProcessedOccupation[];
}

export interface ProcessedVersionResponse {
  version: string;
  processed_date?: string;
  num_occupations: number;
  num_skills?: number;
}

/**
 * Query parameters for catalog endpoint
 */
export interface CatalogQueryParams {
  limit?: number;
  offset?: number;
  soc_code?: string;
  search?: string;
}

/**
 * GET /api/data/catalog - Get occupation catalog
 * Returns filtered list of occupations with pagination, search, and filters
 */
export const getOccupationCatalog = async (
  params?: CatalogQueryParams
): Promise<CatalogResponse> => {
  const response = await apiClient.get<BaseResponse<CatalogResponse>>('/api/data/catalog', {
    params,
  });
  if (!response.data.success) {
    throw new Error(response.data.message || 'Failed to fetch occupation catalog');
  }
  return response.data.data!;
};

/**
 * GET /api/data/catalog/{career_id} - Get specific occupation
 * Returns a specific occupation by career_id
 */
export const getOccupationById = async (career_id: string): Promise<OccupationCatalog> => {
  const response = await apiClient.get<BaseResponse<OccupationCatalog>>(
    `/api/data/catalog/${career_id}`
  );
  if (!response.data.success) {
    throw new Error(response.data.message || 'Failed to fetch occupation');
  }
  return response.data.data!;
};

/**
 * GET /api/data/catalog/search/openai - Search careers using OpenAI
 * Uses OpenAI to find careers based on detailed search queries (job titles, descriptions, skills, industries, etc.)
 */
export const searchCareersOpenAI = async (
  query: string,
  maxResults: number = 10
): Promise<OpenAICareerSearchResponse> => {
  const response = await apiClient.get<BaseResponse<OpenAICareerSearchResponse>>(
    '/api/data/catalog/search/openai',
    {
      params: {
        query,
        max_results: maxResults,
      },
    }
  );
  if (!response.data.success) {
    throw new Error(response.data.message || 'Failed to search careers');
  }
  return response.data.data!;
};

export interface ValidatedCareer {
  career_id: string;
  name: string;
  soc_code: string;
  match_explanation?: string;
  match_score?: number;
  occupation: Occupation;
}

/**
 * GET /api/data/catalog/validate - Validate and normalize a career name using OpenAI
 * Takes a career name/description and returns the best matching career from the database
 */
export const validateCareerName = async (
  careerInput: string
): Promise<ValidatedCareer | null> => {
  if (!careerInput.trim()) {
    return null;
  }
  
  const response = await apiClient.get<BaseResponse<ValidatedCareer>>(
    '/api/data/catalog/validate',
    {
      params: {
        career_input: careerInput,
      },
    }
  );
  
  if (!response.data.success || !response.data.data) {
    return null;
  }
  
  return response.data.data;
};

/**
 * GET /api/data/dictionary - Get data dictionary
 * Returns data dictionary documenting all data files
 */
export const getDataDictionary = async (): Promise<DataDictionary[]> => {
  const response = await apiClient.get<BaseResponse<DataDictionary[]>>('/api/data/dictionary');
  if (!response.data.success) {
    throw new Error(response.data.message || 'Failed to fetch data dictionary');
  }
  return response.data.data!;
};

/**
 * GET /api/data/stats - Get data statistics
 * Returns statistics about the loaded data
 */
export const getDataStats = async (): Promise<DataStats> => {
  const response = await apiClient.get<BaseResponse<DataStats>>('/api/data/stats');
  if (!response.data.success) {
    throw new Error(response.data.message || 'Failed to fetch data statistics');
  }
  return response.data.data!;
};

/**
 * GET /api/data/processed - Get processed data
 * Returns processed datasets with skill vectors, task features, outlook features, education data
 */
export const getProcessedData = async (
  career_id?: string
): Promise<ProcessedDataResponse> => {
  const params = career_id ? { career_id } : undefined;
  const response = await apiClient.get<BaseResponse<ProcessedDataResponse>>(
    '/api/data/processed',
    { params }
  );
  if (!response.data.success) {
    throw new Error(response.data.message || 'Failed to fetch processed data');
  }
  return response.data.data!;
};

/**
 * GET /api/data/processed/version - Get processed data version
 * Returns version information for processed data
 */
export const getProcessedDataVersion = async (): Promise<ProcessedVersionResponse> => {
  const response = await apiClient.get<BaseResponse<ProcessedVersionResponse>>(
    '/api/data/processed/version'
  );
  if (!response.data.success) {
    throw new Error(response.data.message || 'Failed to fetch processed data version');
  }
  return response.data.data!;
};

/**
 * GET /api/data/processed/{career_id} - Get processed occupation data
 * Returns processed data for a specific occupation by career_id
 */
export const getProcessedOccupation = async (
  career_id: string
): Promise<{ version: string; processed_date?: string; occupation: ProcessedOccupation }> => {
  const response = await apiClient.get<
    BaseResponse<{ version: string; processed_date?: string; occupation: ProcessedOccupation }>
  >(`/api/data/processed/${career_id}`);
  if (!response.data.success) {
    throw new Error(response.data.message || 'Failed to fetch processed occupation data');
  }
  return response.data.data!;
};

/**
 * Data service object with all methods
 */
export const dataService = {
  getOccupationCatalog,
  getOccupationById,
  searchCareersOpenAI,
  validateCareerName,
  getDataDictionary,
  getDataStats,
  getProcessedData,
  getProcessedDataVersion,
  getProcessedOccupation,
};

export default dataService;

