export interface RecognizedMealItem {
  food_id: number;
  source: 'system' | 'custom';
  name: string;
  confidence: number;
  estimated_amount_g: number;
  calories_per_100g: number;
  carbs_per_100g: number;
  protein_per_100g: number;
  fat_per_100g: number;
  saveError?: string;
}

export function summarizeRecognizedMeal(items: RecognizedMealItem[]) {
  const total = items.reduce((sum, item) => {
    const ratio = Number(item.estimated_amount_g) / 100;
    sum.calories += item.calories_per_100g * ratio;
    sum.carbs += item.carbs_per_100g * ratio;
    sum.protein += item.protein_per_100g * ratio;
    sum.fat += item.fat_per_100g * ratio;
    return sum;
  }, { calories: 0, carbs: 0, protein: 0, fat: 0 });
  return Object.fromEntries(Object.entries(total).map(([key, value]) => [key, Math.round(value * 10) / 10])) as typeof total;
}
