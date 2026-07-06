import { http } from '@/utils/request';
import type { MealType } from '@/utils/constants';

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
  save_image?: boolean;
  note?: string;
}

export const dietApi = {
  list(date: string) {
    return http.get<DietRecordsResponse>('/diet/records', { date });
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