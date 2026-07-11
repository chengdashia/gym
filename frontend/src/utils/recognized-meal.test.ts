import { describe, expect, it } from 'vitest';
import { summarizeRecognizedMeal, type RecognizedMealItem } from './recognized-meal';

describe('recognized meal', () => {
  it('sums nutrition for edited recognized items', () => {
    const items: RecognizedMealItem[] = [
      {
        food_id: 1, source: 'system', name: '米饭', confidence: 0.92,
        estimated_amount_g: 200, calories_per_100g: 116,
        carbs_per_100g: 25.9, protein_per_100g: 2.6, fat_per_100g: 0.3,
      },
      {
        food_id: 2, source: 'system', name: '鸡胸肉', confidence: 0.81,
        estimated_amount_g: 100, calories_per_100g: 294,
        carbs_per_100g: 0, protein_per_100g: 31, fat_per_100g: 3.6,
      },
    ];

    expect(summarizeRecognizedMeal(items).calories).toBe(526);
  });
});
