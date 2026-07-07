import { defineConfig } from 'vite';
import uni from '@dcloudio/vite-plugin-uni';

export default defineConfig({
  plugins: [uni()],
  resolve: {
    alias: {
      '@': '/src',
    },
  },
  css: {
    preprocessorOptions: {
      scss: {
        // 自动注入到每个 <style lang="scss">，使 mixin 和变量全局可用
        additionalData: `
          @import "@/styles/variables.scss";
          @import "@/styles/glass.scss";
        `,
      },
    },
  },
});