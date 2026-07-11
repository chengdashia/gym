export interface RecognizedMealItem {
  food_id: number | null;
  custom_food_id?: number | null;
  source: 'system' | 'custom';
  name: string;
  confidence: number;
  estimated_amount_g: number;
  calories_per_100g: number;
  carbs_per_100g: number;
  protein_per_100g: number;
  fat_per_100g: number;
  saveError?: string;
  detailError?: string;
}

type RawRecognizedItem = Pick<RecognizedMealItem,
  'food_id' | 'source' | 'name' | 'confidence' | 'estimated_amount_g'> &
  { custom_food_id?: number | null };
type NutritionDetail = Pick<RecognizedMealItem,
  'calories_per_100g' | 'carbs_per_100g' | 'protein_per_100g' | 'fat_per_100g'>;
type SelectedFood = NutritionDetail & { id: number; source: 'system' | 'custom'; name: string };

export async function hydrateRecognizedItems(
  rawItems: RawRecognizedItem[],
  getDetail: (id: number, source: 'system' | 'custom') => Promise<NutritionDetail>,
): Promise<RecognizedMealItem[]> {
  return Promise.all(rawItems.map(async item => {
    const id = item.source === 'custom' ? item.custom_food_id : item.food_id;
    try {
      if (id == null) throw new Error('missing food id');
      return { ...item, custom_food_id: item.custom_food_id ?? null, ...await getDetail(id, item.source) };
    } catch {
      return {
        ...item, custom_food_id: item.custom_food_id ?? null,
        calories_per_100g: 0, carbs_per_100g: 0, protein_per_100g: 0, fat_per_100g: 0,
        detailError: '营养详情加载失败，可替换或重试',
      };
    }
  }));
}

export function mergeSelectedFood(
  items: RecognizedMealItem[], selected: SelectedFood, replaceIndex: number | null,
): RecognizedMealItem[] {
  const item: RecognizedMealItem = {
    food_id: selected.source === 'system' ? selected.id : null,
    custom_food_id: selected.source === 'custom' ? selected.id : null,
    source: selected.source, name: selected.name, confidence: 1, estimated_amount_g: 100,
    ...selected,
  };
  const next = [...items];
  if (replaceIndex == null) next.push(item);
  else next.splice(replaceIndex, 1, item);
  return next;
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
