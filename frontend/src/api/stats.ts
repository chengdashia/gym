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
  average_7d: number | null;
}
export interface WeightTrendMeta {
  record_days: number;
  has_trend: boolean;
  average_change: number | null;
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
export interface WeeklySummary {
  diet_days: number;
  average_calories: number;
  protein_goal_days: number;
  training_sessions: number;
  total_volume: number;
  weight_change: number | null;
  streak_days: number;
  actions: string[];
}

export const statsApi = {
  weeklySummary(end_date?: string) {
    return http.get<WeeklySummary>('/stats/weekly-summary', { end_date });
  },
  diet(range: StatsRange = 7) {
    return http.get<{ items: DietStatPoint[] }>('/stats/diet', { range });
  },
  training(range: StatsRange = 7) {
    return http.get<{ items: TrainingStatPoint[] }>('/stats/training', { range });
  },
  weight(range: StatsRange = 7) {
    return http.get<{ items: WeightStatPoint[]; meta: WeightTrendMeta }>('/stats/weight', { range });
  },
  exercises(range: StatsRange = 7) {
    return http.get<{ items: ExerciseStat[] }>('/stats/exercises', { range });
  },
};
