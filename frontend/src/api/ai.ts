import { http } from '@/utils/request';

export interface RecognitionCandidate {
  food_id: number;
  source: 'system' | 'custom';
  name: string;
  confidence: number;
}

export interface RecognizedItem extends RecognitionCandidate {
  estimated_amount_g: number;
}

export const aiApi = {
  recognizeFood(payload: { file_id?: number; image_url?: string }) {
    return http.post<{
      recognition_id: number;
      provider: string;
      recognized_items: RecognizedItem[];
      /** Migration compatibility only. */
      candidates: RecognitionCandidate[];
    }>('/ai/food-recognition', payload);
  },
};
