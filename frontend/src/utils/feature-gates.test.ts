import { describe, expect, it } from 'vitest';
import { FEATURE_GATES, hasExperimentalFeature, hasNutritionGoal } from './feature-gates';

describe('unfinished feature gates', () => {
  it('keeps membership hidden', () => {
    expect(FEATURE_GATES.membership).toBe(false);
  });

  it('only enables experiments returned by the account API', () => {
    expect(hasExperimentalFeature({ experimental_features: ['diet_programs'] }, 'diet_programs')).toBe(true);
    expect(hasExperimentalFeature({ experimental_features: ['diet_programs'] }, 'food_recognition')).toBe(false);
    expect(hasExperimentalFeature(null, 'diet_programs')).toBe(false);
  });
});

describe('nutrition feature gate', () => {
  it('does not require a goal when a positive calorie target exists', () => {
    expect(hasNutritionGoal({ calories_kcal: 1800 })).toBe(true);
  });

  it('requires a goal when no calorie target exists', () => {
    expect(hasNutritionGoal(null)).toBe(false);
    expect(hasNutritionGoal({ calories_kcal: 0 })).toBe(false);
  });
});
