import { defineStore } from 'pinia';
import { dietApi, DietRecordsResponse } from '@/api/diet';
import { today } from '@/utils/date';

export const useDietStore = defineStore('diet', {
  state: () => ({
    selectedDate: today(),
    summary: { calories_kcal: 0, carbs_g: 0, protein_g: 0, fat_g: 0 },
    meals: { breakfast: [], lunch: [], dinner: [], snack: [] } as DietRecordsResponse['meals'],
    loading: false,
  }),

  actions: {
    setDate(d: string) {
      this.selectedDate = d;
    },
    async fetch(date?: string) {
      const d = date || this.selectedDate;
      this.loading = true;
      try {
        const res = await dietApi.list(d);
        this.selectedDate = res.date;
        this.summary = res.summary;
        this.meals = res.meals;
      } finally {
        this.loading = false;
      }
    },
  },
});