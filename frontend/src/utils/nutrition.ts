// 营养计算

export interface FoodNutrition {
  calories_per_100g: number;
  carbs_per_100g: number;
  protein_per_100g: number;
  fat_per_100g: number;
  serving_weight_g?: number | null;
}

export interface NutritionResult {
  calories: number;
  carbs: number;
  protein: number;
  fat: number;
  amount_g: number;
}

function round(n: number, p = 1): number {
  const m = Math.pow(10, p);
  return Math.round(n * m) / m;
}

export function calcByGram(food: FoodNutrition, amount_g: number): NutritionResult {
  const k = amount_g / 100;
  return {
    calories: round(food.calories_per_100g * k),
    carbs: round(food.carbs_per_100g * k),
    protein: round(food.protein_per_100g * k),
    fat: round(food.fat_per_100g * k),
    amount_g,
  };
}

export function calcByServing(food: FoodNutrition, count: number): NutritionResult {
  const serving = food.serving_weight_g || 0;
  if (!serving) {
    return { calories: 0, carbs: 0, protein: 0, fat: 0, amount_g: 0 };
  }
  return calcByGram(food, serving * count);
}

export function calcNutrition(food: FoodNutrition, opts: { unit_type: 'g' | 'serving'; amount_g?: number; serving_count?: number }): NutritionResult {
  if (opts.unit_type === 'g') return calcByGram(food, opts.amount_g || 0);
  return calcByServing(food, opts.serving_count || 0);
}

export function sumNutrition(items: NutritionResult[]): NutritionResult {
  return items.reduce(
    (acc, it) => ({
      calories: round(acc.calories + it.calories),
      carbs: round(acc.carbs + it.carbs),
      protein: round(acc.protein + it.protein),
      fat: round(acc.fat + it.fat),
      amount_g: round(acc.amount_g + it.amount_g),
    }),
    { calories: 0, carbs: 0, protein: 0, fat: 0, amount_g: 0 },
  );
}

export function progress(value: number, goal: number, max = 1.5): number {
  if (!goal) return 0;
  return Math.min(value / goal, max);
}