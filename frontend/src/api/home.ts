import { http } from '@/utils/request';

export interface HomeSummaryDiet {
  calories_kcal: number;
  calories_goal: number;
  carbs_g: number;
  carbs_goal: number;
  protein_g: number;
  protein_goal: number;
  fat_g: number;
  fat_goal: number;
  record_count: number;
  calories_remaining: number;
  calories_over: number;
  protein_remaining: number;
}

export interface HomeSummaryTraining {
  status: 'no_plan' | 'rest_day' | 'in_progress' | 'not_started' | 'completed';
  plan_id: number | null;
  plan_day_id: number | null;
  session_id: number | null;
  title: string | null;
  exercise_count: number;
  is_rest_day: boolean;
}

export interface HomeSummaryWeight {
  current_weight_kg: number | null;
  target_weight_kg: number | null;
  diff_kg: number | null;
  last_recorded_at: string | null;
}

export interface HomeSummary {
  date: string;
  primary_action: {
    type: 'complete_profile' | 'set_nutrition_goal' | 'record_meal' | 'resume_training' | 'start_training' | 'record_weight' | 'day_complete';
    title: string;
    description: string;
    url: string;
  };
  diet: HomeSummaryDiet;
  training: HomeSummaryTraining;
  weight: HomeSummaryWeight;
  weekly: {
    diet_days: number;
    nutrition_target_days: number;
    training_sessions: number;
    weight_days: number;
    streak_days: number;
  } | null;
}

export const homeApi = {
  summary(date?: string) {
    return http.get<HomeSummary>('/home/summary', { date });
  },
};
