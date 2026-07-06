import { http } from '@/utils/request';

export interface RecognitionCandidate {
  food_id: number;
  source: 'system' | 'custom';
  name: string;
  confidence: number;
}

export const aiApi = {
  recognizeFood(payload: { file_id?: number; image_url?: string }) {
    return http.post<{
      recognition_id: number;
      provider: string;
      candidates: RecognitionCandidate[];
    }>('/ai/food-recognition', payload);
  },
};