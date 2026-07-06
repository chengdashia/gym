import { http } from '@/utils/request';

export interface FoodItem {
  id: number;
  source: 'system' | 'custom';
  name: string;
  category?: string;
  calories_per_100g: number;
  carbs_per_100g: number;
  protein_per_100g: number;
  fat_per_100g: number;
  default_unit: 'g' | 'serving';
  serving_weight_g?: number | null;
}

export interface FoodSearchResult {
  items: FoodItem[];
  total: number;
}

export interface CustomFoodPayload {
  name: string;
  category?: string;
  calories_per_100g: number;
  carbs_per_100g: number;
  protein_per_100g: number;
  fat_per_100g: number;
  default_unit?: 'g' | 'serving';
  serving_weight_g?: number | null;
}

export const foodApi = {
  search(params: { keyword?: string; category?: string; page?: number; page_size?: number }) {
    return http.get<FoodSearchResult>('/foods/search', params);
  },
  getDetail(id: number, source: 'system' | 'custom') {
    return http.get<FoodItem>(`/foods/${id}`, { source });
  },
  createCustom(payload: CustomFoodPayload) {
    return http.post<FoodItem>('/foods/custom', payload);
  },
};