<template>
  <view :style="{ width: '100%', height: height + 'rpx' }">
    <!-- #ifdef MP-WEIXIN -->
    <ec-canvas
      :canvas-id="canvasId"
      :ec="ec"
      class="ec-canvas"
    />
    <!-- #endif -->

    <!-- #ifndef MP-WEIXIN -->
    <view ref="chartEl" class="chart" :style="{ width: '100%', height: height + 'rpx' }" />
    <!-- #endif -->
  </view>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, watch } from 'vue';
import * as echarts from 'echarts';

const props = withDefaults(defineProps<{
  option: any;
  height?: number;
  canvasId?: string;
}>(), {
  height: 400,
  canvasId: 'echarts-canvas',
});

const chartEl = ref<HTMLElement | null>(null);
let chartInstance: any = null;

const ec = ref<any>({
  // 小程序端 echarts-for-weixin 初始化对象
  lazyLoad: true,
});

// #ifdef MP-WEIXIN
const EcCanvas = require('echarts-for-weixin').default;
// #endif

function render(option: any) {
  if (!option) return;
  // H5 端
  // #ifdef H5
  if (chartEl.value && !chartInstance) {
    chartInstance = echarts.init(chartEl.value);
  }
  if (chartInstance) {
    chartInstance.setOption(option, true);
  }
  // #endif

  // 小程序端
  // #ifdef MP-WEIXIN
  if (ec.value && ec.value.lazyLoad) {
    ec.value.lazyLoad = false;
    ec.value.chart = null;
    ec.value.onInit = (canvas: any, width: number, height: number, dpr: number) => {
      const chart = echarts.init(canvas, null, {
        width,
        height,
        devicePixelRatio: dpr,
      });
      chart.setOption(option);
      return chart;
    };
    ec.value.refresh = () => {
      if (ec.value.chart) ec.value.chart.setOption(option, true);
    };
  }
  // #endif
}

onMounted(() => {
  render(props.option);
});

watch(() => props.option, (v) => render(v));

onBeforeUnmount(() => {
  if (chartInstance) {
    chartInstance.dispose();
    chartInstance = null;
  }
});
</script>

<style lang="scss" scoped>
.chart {
  width: 100%;
}
</style>