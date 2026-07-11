import { describe, expect, it } from 'vitest';
import { hydrateRecognizedItems, mergeSelectedFood, summarizeRecognizedMeal, type RecognizedMealItem } from './recognized-meal';

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
    expect(summarizeRecognizedMeal(items)).toEqual({ calories: 526, carbs: 51.8, protein: 36.2, fat: 4.2 });
  });

  it('returns zero nutrition for an empty meal and rounds fractional grams', () => {
    expect(summarizeRecognizedMeal([])).toEqual({ calories: 0, carbs: 0, protein: 0, fat: 0 });
    expect(summarizeRecognizedMeal([{
      food_id: 1, custom_food_id: null, source: 'system', name: 'x', confidence: 1,
      estimated_amount_g: 33.3, calories_per_100g: 100, carbs_per_100g: 10,
      protein_per_100g: 1, fat_per_100g: 0,
    }]).calories).toBe(33.3);
  });

  it('keeps every draft when one detail lookup fails and supports custom IDs', async () => {
    const raw = [
      { food_id: 1, custom_food_id: null, source: 'system' as const, name: '米饭', confidence: .9, estimated_amount_g: 100 },
      { food_id: null, custom_food_id: 8, source: 'custom' as const, name: '便当', confidence: .8, estimated_amount_g: 120 },
    ];
    const items = await hydrateRecognizedItems(raw, async (id, source) => {
      if (source === 'custom') throw new Error('offline');
      return { calories_per_100g: 100, carbs_per_100g: 10, protein_per_100g: 2, fat_per_100g: 1 };
    });
    expect(items).toHaveLength(2);
    expect(items[1]).toMatchObject({ custom_food_id: 8, detailError: '营养详情加载失败，可替换或重试' });
  });

  it('replaces one draft or appends a selected food without saving it', () => {
    const selected = { id: 9, source: 'custom' as const, name: '沙拉', calories_per_100g: 80, carbs_per_100g: 8, protein_per_100g: 3, fat_per_100g: 4 };
    expect(mergeSelectedFood([], selected, null)[0]).toMatchObject({ food_id: null, custom_food_id: 9, name: '沙拉' });
  });
});
