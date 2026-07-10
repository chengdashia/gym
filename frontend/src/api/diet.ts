import { http } from '@/utils/request';
import type { MealType } from '@/utils/constants';
import type { FoodItem } from '@/api/food';

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
  update(id: number, payload: Partial<CreateDietPayload>) {
    return http.put<DietRecord>(`/diet/records/${id}`, payload);
  },
  remove(id: number) {
    return http.del(`/diet/records/${id}`);
  },
};
