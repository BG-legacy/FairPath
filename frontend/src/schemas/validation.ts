/**
 * Validation Schemas
 * Zod schemas matching backend validation rules
 */
import { z } from 'zod';
import { RIASEC_CATEGORIES } from '../services/intake';
import { MAX_FILE_SIZE, ALLOWED_FILE_TYPES } from '../services/resume';

/**
 * Skills validation schema
 * - Non-empty strings
 * - Max 100 characters per skill
 * - Optional array
 */
export const skillsSchema = z
  .array(
    z
      .string()
      .min(1, 'Skill cannot be empty')
      .max(100, 'Skill must be 100 characters or less')
      .trim()
  )
  .optional()
  .default([]);

/**
 * RIASEC interest categories schema
 */
export const riasecCategorySchema = z.enum([
  RIASEC_CATEGORIES[0],
  ...RIASEC_CATEGORIES.slice(1),
] as [string, ...string[]], {
  message: `Invalid RIASEC category. Valid categories are: ${RIASEC_CATEGORIES.join(', ')}`,
});

/**
 * Interests validation schema for intake (array of RIASEC or text)
 * - Can be array of RIASEC categories or text description
 * - Text description: max 500 characters
 * - Optional
 */
export const interestsSchema = z
  .union([
    z.array(riasecCategorySchema),
    z
      .string()
      .min(1, 'Interest description cannot be empty')
      .max(500, 'Interest description must be 500 characters or less')
      .trim(),
  ])
  .optional()
  .nullable();

/**
 * Interests validation schema for recommendations (record of category -> score)
 * - Dict mapping RIASEC categories to scores (0-7)
 * - Optional
 */
export const interestsRecordSchema = z
  .record(
    z.string(),
    z.number().min(0, 'Interest score must be between 0 and 7').max(7, 'Interest score must be between 0 and 7')
  )
  .optional();

/**
 * Values validation schema
 * - impact, stability, flexibility (0-7 scale)
 * - Optional
 */
export const valuesSchema = z
  .object({
    impact: z
      .number()
      .min(0, 'Impact must be between 0 and 7')
      .max(7, 'Impact must be between 0 and 7')
      .optional(),
    stability: z
      .number()
      .min(0, 'Stability must be between 0 and 7')
      .max(7, 'Stability must be between 0 and 7')
      .optional(),
    flexibility: z
      .number()
      .min(0, 'Flexibility must be between 0 and 7')
      .max(7, 'Flexibility must be between 0 and 7')
      .optional(),
  })
  .optional();

/**
 * Constraints validation schema
 * - Supports both nested and legacy format
 * - Optional
 */
export const constraintsSchema = z
  .object({
    // Legacy format
    min_wage: z
      .number()
      .nonnegative('min_wage must be a non-negative number')
      .optional(),
    remote_preferred: z.boolean().optional(),
    max_education_level: z
      .number()
      .int('max_education_level must be an integer')
      .min(0, 'max_education_level must be between 0 and 5')
      .max(5, 'max_education_level must be between 0 and 5')
      .optional(),
    // Nested format
    cost: z
      .union([
        z.number().nonnegative(),
        z.object({
          min_wage: z.number().nonnegative().optional(),
        }),
      ])
      .optional(),
    time: z
      .object({
        max_hours: z
          .number()
          .positive('max_hours must be positive')
          .max(168, 'max_hours must be 168 or less')
          .optional(),
        flexible_hours: z.boolean().optional(),
      })
      .optional(),
    location: z
      .object({
        remote_preferred: z.boolean().optional(),
        location_preference: z
          .string()
          .min(1, 'location_preference must be a non-empty string')
          .trim()
          .optional(),
      })
      .optional(),
  })
  .optional();

/**
 * File upload validation schema
 */
export const fileSchema = z
  .instanceof(File, { message: 'File is required' })
  .refine(
    (file) => file.size > 0,
    { message: 'File cannot be empty' }
  )
  .refine(
    (file) => file.size <= MAX_FILE_SIZE,
    {
      message: `File size must be ${MAX_FILE_SIZE / (1024 * 1024)}MB or less`,
    }
  )
  .refine(
    (file) => {
      const extension = file.name.split('.').pop()?.toLowerCase();
      return extension && ALLOWED_FILE_TYPES.includes(extension as any);
    },
    {
      message: `File type not supported. Allowed types: ${ALLOWED_FILE_TYPES.join(', ')}`,
    }
  )
  .refine(
    (file) => {
      // Check for path traversal attempts
      return !file.name.includes('..') && 
             !file.name.includes('/') && 
             !file.name.includes('\\');
    },
    {
      message: 'Invalid filename: path traversal not allowed',
    }
  )
  .refine(
    (file) => file.name.length <= 255,
    {
      message: 'Filename is too long (maximum 255 characters)',
    }
  );

/**
 * Intake request validation schema
 */
export const intakeRequestSchema = z.object({
  skills: skillsSchema,
  interests: interestsSchema,
  values: valuesSchema,
  constraints: constraintsSchema,
});

/**
 * Recommendation request validation schema
 */
export const recommendationRequestSchema = z.object({
  skills: skillsSchema,
  interests: interestsRecordSchema,
  work_values: z
    .record(
      z.string(),
      z.number().min(0, 'Work value must be between 0 and 7').max(7, 'Work value must be between 0 and 7')
    )
    .optional(),
  constraints: constraintsSchema,
  top_n: z.number().int().min(1, 'top_n must be between 1 and 20').max(20, 'top_n must be between 1 and 20').default(5),
  use_ml: z.boolean().default(true),
});

/**
 * Type exports from schemas
 */
export type SkillsInput = z.infer<typeof skillsSchema>;
export type InterestsInput = z.infer<typeof interestsSchema>;
export type ValuesInput = z.infer<typeof valuesSchema>;
export type ConstraintsInput = z.infer<typeof constraintsSchema>;
export type IntakeRequestInput = z.infer<typeof intakeRequestSchema>;
export type RecommendationRequestInput = z.infer<typeof recommendationRequestSchema>;

