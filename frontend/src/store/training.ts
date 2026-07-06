import { defineStore } from 'pinia';
import { trainingApi, TrainingPlan, TodayTraining, TrainingSession } from '@/api/training';

export const useTrainingStore = defineStore('training', {
  state: () => ({
    plans: [] as TrainingPlan[],
    today: null as TodayTraining | null,
    currentSession: null as TrainingSession | null,
    loading: false,
  }),

  getters: {
    activePlan: (s) => s.plans.find((p) => p.is_active) || null,
  },

  actions: {
    async fetchPlans() {
      const res = await trainingApi.getPlans();
      this.plans = res.items || [];
    },
    async fetchToday(date?: string) {
      this.today = await trainingApi.getToday(date);
      return this.today;
    },
    async startSession(plan_id: number, plan_day_id: number, session_date: string) {
      this.currentSession = await trainingApi.createSession({ plan_id, plan_day_id, session_date });
      return this.currentSession;
    },
    async fetchSession(id: number) {
      this.currentSession = await trainingApi.getSession(id);
      return this.currentSession;
    },
    async saveSession(id: number, payload: any) {
      this.currentSession = await trainingApi.updateSession(id, payload);
      return this.currentSession;
    },
    async finishSession(id: number) {
      this.currentSession = await trainingApi.finishSession(id);
      return this.currentSession;
    },
    async cancelSession(id: number) {
      this.currentSession = await trainingApi.cancelSession(id);
      return this.currentSession;
    },
    clearCurrent() {
      this.currentSession = null;
    },
  },
});