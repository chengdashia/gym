<template>
  <view :style="{ width: '100%', height: height + 'rpx' }">
    <!--
      MP-WEIXIN: 直接渲染 <canvas type="2d">，绕过 echarts-for-weixin 的 ec-canvas 自定义组件。
      原因：uni-app 把 <ec-canvas> 编译到 wxml 时会用 uP 透传 props，导致 uni-app 运行时调用
      Ma(t.uP)（期望 "name,index" 字符串）实际却拿到对象 {canvas-id, ec}，从而触发
      t.split is not a function（vendor.js Ma → Ka → pi.attached）。
      自己拿 canvas 节点后直接 echarts.init(canvasNode)，行为与 ec-canvas 内部 initByNewWay 一致。

      H5：直接渲染 <view ref>，echarts.init(ref) 即可。
    -->
    <!-- #ifdef MP-WEIXIN -->
    <canvas
      type="2d"
      :id="canvasId"
      :canvas-id="canvasId"
      class="ec-canvas"
      :style="{ width: '100%', height: height + 'rpx' }"
      @touchstart="onTouchStart"
      @touchmove="onTouchMove"
      @touchend="onTouchEnd"
    />
    <!-- #endif -->

    <!-- #ifndef MP-WEIXIN -->
    <view
      ref="chartEl"
      class="chart"
      :style="{ width: '100%', height: height + 'rpx' }"
    />
    <!-- #endif -->
  </view>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, watch } from 'vue';
import * as echarts from 'echarts';

declare const wx: any;

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

function refresh(option: any) {
  if (!option || !chartInstance) return;
  chartInstance.setOption(option, true);
}

onMounted(() => {
  // #ifdef MP-WEIXIN
  // 节点需要在 componentDidMount / ready 后才能 select 到；这里用 setTimeout 让 render 先 commit
  const query = wx.createSelectorQuery();
  query.select('#' + props.canvasId)
    .fields({ node: true, size: true })
    .exec((res: any[]) => {
      const node = res && res[0] && res[0].node;
      if (!node) return;
      const dpr = (uni.getWindowInfo().pixelRatio || 1) as number;
      chartInstance = echarts.init(node, null, { devicePixelRatio: dpr });
      if (props.option) chartInstance.setOption(props.option, true);
    });
  // #endif

  // #ifdef H5
  if (chartEl.value && !chartInstance) {
    chartInstance = echarts.init(chartEl.value as any);
    if (props.option) chartInstance.setOption(props.option);
  }
  // #endif
});

function onTouchStart(e: any) {
  if (!chartInstance || !e.touches || !e.touches.length) return;
  const t = e.touches[0];
  const h = chartInstance.getZr().handler;
  h.dispatch('mousedown', { zrX: t.x, zrY: t.y });
  h.dispatch('mousemove', { zrX: t.x, zrY: t.y });
}
function onTouchMove(e: any) {
  if (!chartInstance || !e.touches || !e.touches.length) return;
  const t = e.touches[0];
  chartInstance.getZr().handler.dispatch('mousemove', { zrX: t.x, zrY: t.y });
}
function onTouchEnd(e: any) {
  if (!chartInstance) return;
  const t = (e.changedTouches && e.changedTouches[0]) || {};
  const h = chartInstance.getZr().handler;
  h.dispatch('mouseup', { zrX: t.x, zrY: t.y });
  h.dispatch('click', { zrX: t.x, zrY: t.y });
}

watch(() => props.option, (v) => refresh(v));

onBeforeUnmount(() => {
  if (chartInstance) {
    chartInstance.dispose();
    chartInstance = null;
  }
});
</script>

<style lang="scss" scoped>
.ec-canvas {
  width: 100%;
  height: 100%;
}
.chart {
  width: 100%;
}
</style>