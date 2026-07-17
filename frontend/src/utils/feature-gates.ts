import type { NutritionGoal } from '@/api/user';

export const FEATURE_GATES = {
  membership: false,
} as const;

export type ExperimentalFeature = 'diet_programs' | 'food_recognition';

export function hasExperimentalFeature(
  user: { experimental_features?: string[] } | null | undefined,
  feature: ExperimentalFeature,
): boolean {
  return user?.experimental_features?.includes(feature) === true;
}

export function hasNutritionGoal(goal: Partial<NutritionGoal> | null | undefined): boolean {
  return Number(goal?.calories_kcal || 0) > 0;
}
