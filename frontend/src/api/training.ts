import { http } from '@/utils/request';

export interface PlanExercise {
  exercise_source: 'system' | 'custom';
  exercise_id?: number | null;
  custom_exercise_id?: number | null;
  exercise_name_snapshot: string;
  body_part_snapshot?: string;
  target_sets: number;
  target_reps: number;
  target_weight_kg?: number | null;
  rest_seconds: number;
  sort_order: number;
  note?: string;
}

export interface PlanDay {
  id?: number;
  day_index: number;
  day_name: string;
  is_rest_day: boolean;
  weekday?: number | null;
  sort_order?: number;
  exercises: PlanExercise[];
}

export interface TrainingPlan {
  id: number;
  user_id: number;
  name: string;
  schedule_type: 'sequence' | 'weekly';
  source_template_id?: number | null;
  current_day_index: number;
  is_active: boolean;
  status: string;
  days?: PlanDay[];
}

export interface TemplateDay {
  id: number;
  day_index: number;
  day_name: string;
  is_rest_day: boolean;
  weekday?: number | null;
  exercises: Array<PlanExercise & { id: number }>;
}

export interface TrainingTemplate {
  id: number;
  name: string;
  description?: string;
  split_type: string;
  difficulty?: string;
  goal?: string;
  days: TemplateDay[];
}

export interface SessionSet {
  id?: number;
  set_id?: number;
  set_index: number;
  target_reps?: number | null;
  target_weight_kg?: number | null;
  actual_reps?: number | null;
  actual_weight_kg?: number | null;
  completed: boolean;
  note?: string;
}

export interface SessionExercise {
  session_exercise_id?: number;
  exercise_name_snapshot: string;
  body_part_snapshot?: string;
  sort_order: number;
  planned_sets: number;
  completed_sets: number;
  rest_seconds: number;
  sets: SessionSet[];
}

export interface TrainingSession {
  id: number;
  user_id: number;
  plan_id: number | null;
  plan_day_id: number | null;
  session_date: string;
  session_name: string;
  status: 'in_progress' | 'paused' | 'completed' | 'cancelled';
  started_at: string;
  ended_at: string | null;
  duration_seconds: number;
  total_volume: number;
  note?: string;
  exercises?: SessionExercise[];
}

export interface TodayTraining {
  has_plan: boolean;
  is_rest_day: boolean;
  plan_id: number | null;
  plan_day_id: number | null;
  session_id: number | null;
  session_status: string | null;
  title: string | null;
  exercise_count: number;
  schedule_type: string | null;
  today_completed?: boolean;
}

export const trainingApi = {
  getTemplates() {
    return http.get<{ items: TrainingTemplate[] }>('/training/templates');
  },
  getPlans() {
    return http.get<{ items: TrainingPlan[] }>('/training/plans');
  },
  getPlan(id: number) {
    return http.get<TrainingPlan>(`/training/plans/${id}`);
  },
  createPlan(payload: { name: string; schedule_type: 'sequence' | 'weekly'; source_template_id?: number | null; days: PlanDay[] }) {
    return http.post<TrainingPlan>('/training/plans', payload);
  },
  updatePlan(id: number, payload: any) {
    return http.put<TrainingPlan>(`/training/plans/${id}`, payload);
  },
  deletePlan(id: number) {
    return http.del(`/training/plans/${id}`);
  },
  setActive(id: number) {
    return http.post(`/training/plans/${id}/activate`);
  },
  getToday(date?: string) {
    return http.get<TodayTraining>('/training/today', { date });
  },
  createSession(payload: { plan_id: number; plan_day_id: number; session_date: string }) {
    return http.post<TrainingSession>('/training/sessions', payload);
  },
  getSession(id: number) {
    return http.get<TrainingSession>(`/training/sessions/${id}`);
  },
  updateSession(id: number, payload: { status: string; exercises: SessionExercise[] }) {
    return http.put<TrainingSession>(`/training/sessions/${id}`, payload);
  },
  finishSession(id: number) {
    return http.post<TrainingSession>(`/training/sessions/${id}/finish`);
  },
  cancelSession(id: number) {
    return http.post<TrainingSession>(`/training/sessions/${id}/cancel`);
  },
  deleteSession(id: number) {
    return http.del(`/training/sessions/${id}`);
  },
  listSessions(params: { start_date?: string; end_date?: string }) {
    return http.get<{ items: TrainingSession[] }>('/training/sessions', params);
  },
};