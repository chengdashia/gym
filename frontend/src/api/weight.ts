import { http } from '@/utils/request';

export interface WeightRecord {
  id: number;
  user_id: number;
  record_date: string;
  record_time: string;
  weight_kg: number;
  note?: string | null;
}

export const weightApi = {
  list(range: number = 90) {
    return http.get<{ items: WeightRecord[] }>('/weight/records', { range });
  },
  create(payload: { record_date: string; record_time: string; weight_kg: number; note?: string }) {
    return http.post<WeightRecord>('/weight/records', payload);
  },
  update(id: number, payload: Partial<{ record_date: string; record_time: string; weight_kg: number; note: string }>) {
    return http.put<WeightRecord>(`/weight/records/${id}`, payload);
  },
  remove(id: number) {
    return http.del(`/weight/records/${id}`);
  },
};