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
        // 使用 modern API，消除 legacy-js-api 弃用警告
        api: 'modern',
        // uni-app 插件内部仍走 legacy API，静默该警告
        silenceDeprecations: ['legacy-js-api'],
        // 自动注入到每个 <style lang="scss">，使 mixin 和变量全局可用
        additionalData: `
          @use "@/styles/variables.scss" as *;
          @use "@/styles/glass.scss" as *;
        `,
      },
    },
  },
});