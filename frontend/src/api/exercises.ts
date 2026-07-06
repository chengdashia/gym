import { http } from '@/utils/request';

export interface ExerciseItem {
  id: number;
  source?: 'system' | 'custom';
  name: string;
  body_part: string;
  description?: string;
}

export interface ExerciseSearchResult {
  items: ExerciseItem[];
  total: number;
}

export const exerciseApi = {
  search(params: { keyword?: string; body_part?: string; page?: number; page_size?: number }) {
    return http.get<ExerciseSearchResult>('/exercises/search', params);
  },
  createCustom(payload: { name: string; body_part: string; description?: string }) {
    return http.post<ExerciseItem>('/exercises/custom', payload);
  },
};