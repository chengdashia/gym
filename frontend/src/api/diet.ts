import { http } from '@/utils/request';
import type { MealType } from '@/utils/constants';
import type { FoodItem } from '@/api/food';
import type { CustomFoodPayload } from '@/api/food';

export interface RecentFood extends FoodItem { recent_amount?: number | null }

export interface DietRecord {
  id: number;
  user_id: number;
  record_date: string;
  record_time: string;
  meal_type: MealType;
  food_source: 'system' | 'custom';
  food_id: number | null;
  custom_food_id: number | null;
  food_name_snapshot: string;
  unit_type: 'g' | 'serving';
  amount_g: number | null;
  serving_count: number | null;
  image_url: string | null;
  save_image: boolean;
  calories_kcal: number;
  carbs_g: number;
  protein_g: number;
  fat_g: number;
  note: string | null;
}

export interface DietSummary {
  calories_kcal: number;
  carbs_g: number;
  protein_g: number;
  fat_g: number;
}

export interface DietRecordsResponse {
  date: string;
  summary: DietSummary;
  meals: Record<MealType, DietRecord[]>;
}

export interface SavedMealTemplate {
  id: number;
  name: string;
  source_meal_type: MealType;
  item_count: number;
  items: Array<{ food_name_snapshot: string; amount_g: number | null; serving_count: number | null }>;
  created_at: string;
}

export interface CreateDietPayload {
  record_date: string;
  record_time: string;
  meal_type: MealType;
  food_source: 'system' | 'custom';
  food_id?: number | null;
  custom_food_id?: number | null;
  food_name_snapshot?: string;
  unit_type: 'g' | 'serving';
  amount_g?: number | null;
  serving_count?: number | null;
  image_url?: string | null;
  image_file_id?: number | null;
  save_image?: boolean;
  note?: string;
}

export const dietApi = {
  savedMeals() {
    return http.get<{ items: SavedMealTemplate[] }>('/diet/saved-meals');
  },
  saveMealTemplate(payload: { source_date: string; source_meal_type: MealType; name: string }) {
    return http.post<SavedMealTemplate>('/diet/saved-meals/from-meal', payload);
  },
  recordSavedMeal(id: number, payload: { target_date: string; target_meal_type: MealType; record_time: string }) {
    return http.post<{ count: number; template_id: number }>(`/diet/saved-meals/${id}/record`, payload);
  },
  deleteSavedMeal(id: number) {
    return http.del(`/diet/saved-meals/${id}`);
  },
  recentFoods(limit = 10) {
    return http.get<{ items: RecentFood[] }>('/diet/recent-foods', { limit });
  },
  copyMeal(payload: {
    source_date: string;
    source_meal_type: MealType;
    target_date: string;
    target_meal_type: MealType;
    record_time: string;
  }) {
    return http.post<{ count: number }>('/diet/copy-meal', payload);
  },
  list(date: string) {
    return http.get<DietRecordsResponse>('/diet/records', { date });
  },
  getRecord(id: number) {
    return http.get<DietRecord>(`/diet/records/${id}`);
  },
  create(payload: CreateDietPayload) {
    return http.post<DietRecord>('/diet/records', payload);
  },
  createCustomFoodRecord(food: CustomFoodPayload, record: CreateDietPayload) {
    return http.post<{ food: Pick<FoodItem, 'id' | 'name' | 'source'>; record: DietRecord }>(
      '/diet/custom-food-record',
      { food, record: { ...record, food_source: 'custom' } },
    );
  },
  update(id: number, payload: Partial<CreateDietPayload>) {
    return http.put<DietRecord>(`/diet/records/${id}`, payload);
  },
  remove(id: number) {
    return http.del(`/diet/records/${id}`);
  },
};
