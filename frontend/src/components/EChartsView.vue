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
// mp 端 <ec-canvas> 是 echarts-for-weixin 提供的第三方组件，需要在 EChartsView.json 的
// usingComponents 中显式注册（路径：/echarts-for-weixin/ec-canvas/index）。
// 这里的 require 把 echarts-for-weixin 的 JS 打进依赖图，确保 ECharts 库可用。
// #ifdef MP-WEIXIN
// eslint-disable-next-line @typescript-eslint/no-var-requires
require('echarts-for-weixin');
// #endif

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
  lazyLoad: true,
  chart: null,
  onInit: null as null | ((canvas: any, width: number, height: number, dpr: number) => any),
  refresh: null as null | (() => void),
});

function bindEcInit(option: any) {
  ec.value.chart = null;
  ec.value.lazyLoad = false;
  ec.value.onInit = (canvas: any, width: number, height: number, dpr: number) => {
    const chart = echarts.init(canvas, null, {
      width,
      height,
      devicePixelRatio: dpr,
    });
    chart.setOption(option);
    ec.value.chart = chart;
    return chart;
  };
  ec.value.refresh = () => {
    if (ec.value.chart) ec.value.chart.setOption(option, true);
  };
}

function render(option: any) {
  if (!option) return;
  // #ifdef H5
  if (chartEl.value && !chartInstance) {
    chartInstance = echarts.init(chartEl.value);
  }
  if (chartInstance) {
    chartInstance.setOption(option, true);
  }
  return;
  // #endif

  // #ifdef MP-WEIXIN
  if (!ec.value.onInit) {
    bindEcInit(option);
  } else if (ec.value.chart) {
    ec.value.chart.setOption(option, true);
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
  ec.value.chart = null;
  ec.value.onInit = null;
  ec.value.refresh = null;
});
</script>

<style lang="scss" scoped>
.chart {
  width: 100%;
}
</style>