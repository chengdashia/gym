import { http } from '@/utils/request';

export interface RecognitionCandidate {
  food_id: number | null;
  custom_food_id?: number | null;
  source: 'system' | 'custom';
  name: string;
  confidence: number;
}

export interface RecognizedItem extends RecognitionCandidate {
  estimated_amount_g: number;
}

export interface FoodModelLabel {
  index: number;
  name: string;
  food_id: number | null;
  density_low: number;
  density_high: number;
}

export interface FoodModelManifest {
  version: string;
  model_url: string;
  input_size: number;
  input_name: string;
  output_names: { scores: string; labels: string; area_ratios: string };
  score_threshold: number;
  labels: FoodModelLabel[];
}

export const aiApi = {
  getFoodModelManifest() {
    return http.get<FoodModelManifest>('/ai/food-recognition/model-manifest');
  },
};
