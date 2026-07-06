import { http } from '@/utils/request';

export interface DietStatPoint {
  date: string;
  calories_kcal: number;
  carbs_g: number;
  protein_g: number;
  fat_g: number;
  calories_goal: number;
  completion_rate: number;
}

export interface TrainingStatPoint {
  date: string;
  session_count: number;
  duration_seconds: number;
  total_volume: number;
}

export interface WeightStatPoint {
  date: string;
  weight_kg: number | null;
  target_weight_kg: number | null;
  diff_kg: number | null;
  change_from_start: number | null;
}

export const statsApi = {
  diet(range: 7 | 30 | 90 = 7) {
    return http.get<{ items: DietStatPoint[] }>('/stats/diet', { range });
  },
  training(range: 7 | 30 | 90 = 30) {
    return http.get<{ items: TrainingStatPoint[] }>('/stats/training', { range });
  },
  weight(range: 7 | 30 | 90 = 30) {
    return http.get<{ items: WeightStatPoint[] }>('/stats/weight', { range });
  },
};