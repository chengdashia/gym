import { defineStore } from 'pinia';

export const useAppStore = defineStore('app', {
  state: () => ({
    ready: false,
    theme: 'fresh',
    networkOk: true,
  }),
  actions: {
    init() {
      this.ready = true;
    },
  },
});