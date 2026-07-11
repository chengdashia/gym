import { http } from '@/utils/request';

export type DietProgramCode = 'balanced_cut' | 'time_restricted_16_8' | 'carb_taper_532' | 'ketogenic';

export interface DietTemplate {
  code: DietProgramCode;
  name: string;
  description: string;
  version: number;
  rules: { strict?: boolean; requires_fiber?: boolean };
}

export interface DietPreferencePayload {
  meal_count: number;
  allergens: string[];
  vegetarian_type: 'none' | 'lacto_ovo' | 'lacto' | 'ovo' | 'vegan';
  avoid_foods: string[];
  eating_window_start?: string | null;
  eating_window_end?: string | null;
  budget_level?: 'low' | 'medium' | 'high';
  cooking_setup?: 'full_kitchen' | 'simple_heating' | 'none';
  cuisine_preference?: 'home_chinese' | 'light_meal' | 'takeout';
}

export interface EligibilityPayload {
  under_18: boolean;
  pregnant_or_breastfeeding: boolean;
  diabetes: boolean;
  serious_liver_kidney_gallbladder: boolean;
  eating_disorder_history: boolean;
}

export interface ProgramStage {
  id: number;
  stage_number: number;
  status: string;
  calories_kcal: number;
  carbs_g: number;
  protein_g: number;
  fat_g: number;
}
export interface ActiveDietProgram {
  id: number; template_code: DietProgramCode; template_name: string; stage: ProgramStage;
  meal_count: number; eating_window_start?: string | null; eating_window_end?: string | null;
}

export interface MealPlanItem { id: number; name: string; role: string; amount_g: number; nutrition: Record<string, number> }
export interface MealPlanMeal { id: number; meal_type: string; planned_time: string; recorded: boolean; items: MealPlanItem[] }
export interface MealPlanDay { id: number; plan_date: string; totals: Record<string, number>; meals: MealPlanMeal[] }

export const dietProgramApi = {
  templates: () => http.get<{ items: DietTemplate[] }>('/diet-programs/templates'),
  active: () => http.get<ActiveDietProgram | null>('/diet-programs/active'),
  savePreferences: (body: DietPreferencePayload) => http.put('/diet-programs/preferences', body),
  create: (body: { template_code: DietProgramCode; calories_kcal: number; macro_ratio: '532' | '442'; activity_level: 'sedentary' | 'light' | 'moderate' | 'very_active'; target_loss_rate: number; eligibility: EligibilityPayload }) => http.post<{ id: number; stage: ProgramStage }>('/diet-programs', body),
  confirm: (id: number) => http.post<{ id: number; status: string; stage: ProgramStage }>(`/diet-programs/${id}/confirm`),
  mealPlan: (id: number) => http.get<{ program_id: number; stage_id: number; days: MealPlanDay[] }>(`/diet-programs/${id}/meal-plan`),
  recordMeal: (id: number) => http.post<{ created_count: number }>(`/meal-plan/meals/${id}/record`),
};
