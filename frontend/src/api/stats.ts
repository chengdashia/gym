import { http } from '@/utils/request';

export type StatsRange = 7 | 30 | 90;

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
export interface ExerciseStat {
  exercise_name: string;
  body_part: string | null;
  completed_sets: number;
  total_reps: number;
  max_weight_kg: number;
  total_volume: number;
  has_weight?: boolean;
}

export const statsApi = {
  diet(range: StatsRange = 7) {
    return http.get<{ items: DietStatPoint[] }>('/stats/diet', { range });
  },
  training(range: StatsRange = 7) {
    return http.get<{ items: TrainingStatPoint[] }>('/stats/training', { range });
  },
  weight(range: StatsRange = 7) {
    return http.get<{ items: WeightStatPoint[] }>('/stats/weight', { range });
  },
  exercises(range: StatsRange = 7) {
    return http.get<{ items: ExerciseStat[] }>('/stats/exercises', { range });
  },
};
