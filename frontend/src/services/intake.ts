/**
 * Intake Service
 * Service for normalizing user profiles and validating intake forms
 */
import apiClient from './apiClient';
import { BaseResponse } from './types';

/**
 * RIASEC interest categories
 */
export const RIASEC_CATEGORIES = [
  'Realistic',
  'Investigative',
  'Artistic',
  'Social',
  'Enterprising',
  'Conventional',
] as const;

export type RIASECCategory = typeof RIASEC_CATEGORIES[number];

/**
 * Career values
 */
export const CAREER_VALUES = ['impact', 'stability', 'flexibility'] as const;

export type CareerValue = typeof CAREER_VALUES[number];

/**
 * Intake request types
 */
export interface IntakeConstraints {
  cost?: number | { min_wage?: number };
  time?: {
    max_hours?: number;
    flexible_hours?: boolean;
  };
  location?: {
    remote_preferred?: boolean;
    location_preference?: string;
  };
  // Legacy format support
  min_wage?: number;
  remote_preferred?: boolean;
  max_education_level?: number;
}

export interface IntakeValues {
  impact?: number;
  stability?: number;
  flexibility?: number;
}

export interface IntakeRequest {
  skills?: string[];
  interests?: string[] | string; // RIASEC categories or text description
  constraints?: IntakeConstraints;
  values?: IntakeValues;
}

/**
 * Feature vectors in normalized profile
 */
export interface FeatureVectors {
  skill_vector: number[];
  interest_vector: number[];
  values_vector: number[];
  constraint_features: number[];
  combined_vector: number[];
}

/**
 * Interests structure in normalized profile
 */
export interface NormalizedInterests {
  riasec_scores: Record<string, number>;
  raw_input: string[] | string | null;
}

/**
 * Normalized profile structure (matches backend response)
 */
export interface NormalizedProfileData {
  skills: string[];
  interests: NormalizedInterests;
  values: Record<string, number>;
  constraints: Record<string, any>;
  feature_vectors: FeatureVectors;
}

/**
 * Dominant interest/value in summary
 */
export interface DominantItem {
  category?: string;
  value?: string;
  score: number;
}

/**
 * Feature vector statistics
 */
export interface FeatureVectorStats {
  dimension: number;
  non_zero_count: number;
  max_value: number;
  mean_value: number;
  std_value: number;
}

/**
 * Constraints summary
 */
export interface ConstraintsSummary {
  has_wage_constraint: boolean;
  has_location_constraint: boolean;
  has_time_constraint: boolean;
  constraint_count: number;
}

/**
 * Derived features summary (matches backend response)
 */
export interface DerivedFeaturesSummary {
  profile_completeness: number;
  dominant_interests: DominantItem[];
  dominant_values: DominantItem[];
  feature_vector_stats: FeatureVectorStats;
  constraints_summary: ConstraintsSummary;
}

/**
 * Complete intake response structure (matches backend response)
 */
export interface IntakeResponse {
  normalized_profile: NormalizedProfileData;
  derived_features_summary: DerivedFeaturesSummary;
}

/**
 * Normalized profile response (for backward compatibility)
 * @deprecated Use IntakeResponse instead
 */
export interface NormalizedProfile extends IntakeResponse {
  [key: string]: any;
}

/**
 * Validation errors
 */
export interface ValidationErrors {
  skills?: string;
  interests?: string;
  constraints?: string;
  values?: string;
  [key: string]: string | undefined;
}

/**
 * Validate skills input
 * @param skills - List of skill strings
 * @returns Error message if invalid, undefined if valid
 */
export const validateSkills = (skills?: string[]): string | undefined => {
  if (!skills || skills.length === 0) {
    return undefined; // Skills are optional
  }

  // Check if all items are non-empty strings
  const invalidSkills = skills.filter(
    (skill) => !skill || typeof skill !== 'string' || !skill.trim()
  );

  if (invalidSkills.length > 0) {
    return 'All skills must be non-empty strings';
  }

  // Check for reasonable length
  const tooLongSkills = skills.filter((skill) => skill.length > 100);
  if (tooLongSkills.length > 0) {
    return 'Skills must be 100 characters or less';
  }

  return undefined;
};

/**
 * Validate interests input
 * @param interests - RIASEC categories (list) or text description
 * @returns Error message if invalid, undefined if valid
 */
export const validateInterests = (
  interests?: string[] | string
): string | undefined => {
  if (!interests) {
    return undefined; // Interests are optional
  }

  if (typeof interests === 'string') {
    // Text description - validate length
    if (interests.trim().length === 0) {
      return 'Interest description cannot be empty';
    }
    if (interests.length > 500) {
      return 'Interest description must be 500 characters or less';
    }
    return undefined;
  }

  if (Array.isArray(interests)) {
    if (interests.length === 0) {
      return undefined; // Empty array is valid
    }

    // Validate RIASEC categories
    const validCategories = new Set(
      RIASEC_CATEGORIES.map((cat) => cat.toLowerCase())
    );
    const invalidCategories = interests.filter(
      (interest) =>
        !interest ||
        typeof interest !== 'string' ||
        !validCategories.has(interest.trim().toLowerCase())
    );

    if (invalidCategories.length > 0) {
      return `Invalid RIASEC categories. Valid categories are: ${RIASEC_CATEGORIES.join(', ')}`;
    }

    return undefined;
  }

  return 'Interests must be a string or an array of strings';
};

/**
 * Validate constraints input
 * @param constraints - Constraints object
 * @returns Error message if invalid, undefined if valid
 */
export const validateConstraints = (
  constraints?: IntakeConstraints
): string | undefined => {
  if (!constraints) {
    return undefined; // Constraints are optional
  }

  // Validate cost constraint
  if (constraints.cost !== undefined) {
    if (typeof constraints.cost === 'number') {
      if (constraints.cost < 0) {
        return 'Cost (min_wage) must be non-negative';
      }
    } else if (typeof constraints.cost === 'object') {
      if (
        constraints.cost.min_wage !== undefined &&
        (typeof constraints.cost.min_wage !== 'number' ||
          constraints.cost.min_wage < 0)
      ) {
        return 'min_wage must be a non-negative number';
      }
    } else {
      return 'Cost constraint must be a number or object with min_wage';
    }
  }

  // Validate time constraints
  if (constraints.time) {
    if (
      constraints.time.max_hours !== undefined &&
      (typeof constraints.time.max_hours !== 'number' ||
        constraints.time.max_hours <= 0 ||
        constraints.time.max_hours > 168)
    ) {
      return 'max_hours must be a number between 0 and 168';
    }

    if (
      constraints.time.flexible_hours !== undefined &&
      typeof constraints.time.flexible_hours !== 'boolean'
    ) {
      return 'flexible_hours must be a boolean';
    }
  }

  // Validate location constraints
  if (constraints.location) {
    if (
      constraints.location.remote_preferred !== undefined &&
      typeof constraints.location.remote_preferred !== 'boolean'
    ) {
      return 'remote_preferred must be a boolean';
    }

    if (
      constraints.location.location_preference !== undefined &&
      (typeof constraints.location.location_preference !== 'string' ||
        constraints.location.location_preference.trim().length === 0)
    ) {
      return 'location_preference must be a non-empty string';
    }
  }

  // Validate legacy format
  if (
    constraints.min_wage !== undefined &&
    (typeof constraints.min_wage !== 'number' || constraints.min_wage < 0)
  ) {
    return 'min_wage must be a non-negative number';
  }

  if (
    constraints.remote_preferred !== undefined &&
    typeof constraints.remote_preferred !== 'boolean'
  ) {
    return 'remote_preferred must be a boolean';
  }

  if (
    constraints.max_education_level !== undefined &&
    (typeof constraints.max_education_level !== 'number' ||
      constraints.max_education_level < 0 ||
      constraints.max_education_level > 5)
  ) {
    return 'max_education_level must be a number between 0 and 5';
  }

  return undefined;
};

/**
 * Validate values input
 * @param values - Values object with impact, stability, flexibility (0-7 scale)
 * @returns Error message if invalid, undefined if valid
 */
export const validateValues = (values?: IntakeValues): string | undefined => {
  if (!values) {
    return undefined; // Values are optional
  }

  const validKeys = new Set(CAREER_VALUES);
  const valueRange = { min: 0, max: 7 };

  for (const [key, value] of Object.entries(values)) {
    if (!validKeys.has(key as CareerValue)) {
      return `Invalid value key: ${key}. Valid keys are: ${CAREER_VALUES.join(', ')}`;
    }

    if (typeof value !== 'number') {
      return `Value ${key} must be a number`;
    }

    if (value < valueRange.min || value > valueRange.max) {
      return `Value ${key} must be between ${valueRange.min} and ${valueRange.max}`;
    }
  }

  return undefined;
};

/**
 * Validate entire intake request
 * @param request - Intake request object
 * @returns Validation errors object (empty if valid)
 */
export const validateIntakeRequest = (
  request: IntakeRequest
): ValidationErrors => {
  const errors: ValidationErrors = {};

  const skillsError = validateSkills(request.skills);
  if (skillsError) {
    errors.skills = skillsError;
  }

  const interestsError = validateInterests(request.interests);
  if (interestsError) {
    errors.interests = interestsError;
  }

  const constraintsError = validateConstraints(request.constraints);
  if (constraintsError) {
    errors.constraints = constraintsError;
  }

  const valuesError = validateValues(request.values);
  if (valuesError) {
    errors.values = valuesError;
  }

  return errors;
};

/**
 * POST /api/intake/intake - Normalize user profile
 * Validates and normalizes user profile data
 */
export const normalizeUserProfile = async (
  request: IntakeRequest
): Promise<IntakeResponse> => {
  // Validate request before sending
  const validationErrors = validateIntakeRequest(request);
  const hasErrors = Object.keys(validationErrors).length > 0;

  if (hasErrors) {
    throw new Error(
      `Validation failed: ${Object.values(validationErrors).join(', ')}`
    );
  }

  const response = await apiClient.post<BaseResponse<IntakeResponse>>(
    '/api/intake/intake',
    request
  );

  if (!response.data.success) {
    throw new Error(response.data.message || 'Failed to normalize user profile');
  }

  return response.data.data!;
};

/**
 * Intake service object with all methods
 */
export const intakeService = {
  normalizeUserProfile,
  validateSkills,
  validateInterests,
  validateConstraints,
  validateValues,
  validateIntakeRequest,
};

export default intakeService;

