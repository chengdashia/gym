import { describe, expect, it } from 'vitest';
import { calcNutrition } from './nutrition';

describe('calcNutrition', () => {
  it('按克数计算营养快照', () => {
    const result = calcNutrition(
      { calories_per_100g: 130, carbs_per_100g: 28, protein_per_100g: 2.7, fat_per_100g: 0.3 },
      { unit_type: 'g', amount_g: 150, serving_count: null },
    );
    expect(result.calories).toBe(195);
    expect(result.carbs).toBe(42);
  });
});
