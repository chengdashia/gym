import { describe, expect, it } from 'vitest';
import { FEATURE_GATES, hasNutritionGoal } from './feature-gates';

describe('unfinished feature gates', () => {
  it('keeps photo recognition and membership hidden', () => {
    expect(FEATURE_GATES.photoRecognition).toBe(false);
    expect(FEATURE_GATES.membership).toBe(false);
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
