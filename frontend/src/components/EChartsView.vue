<template>
  <view :style="{ width: '100%', height: height + 'rpx' }">
    <!-- #ifdef MP-WEIXIN -->
    <canvas type="2d" :id="canvasId" :canvas-id="canvasId" class="chart" :style="{ width: '100%', height: height + 'rpx' }" />
    <!-- #endif -->
    <!-- #ifndef MP-WEIXIN -->
    <view ref="chartEl" class="chart" :style="{ width: '100%', height: height + 'rpx' }" />
    <!-- #endif -->
  </view>
</template>

<script setup lang="ts">
import { getCurrentInstance, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue';
// #ifdef H5
import * as echarts from 'echarts';
// #endif

const props = withDefaults(defineProps<{ option: any; height?: number; canvasId?: string }>(), {
  height: 400,
  canvasId: 'chart-canvas',
});

const chartEl = ref<HTMLElement | null>(null);
const instance = getCurrentInstance();
let chartInstance: any = null;
let nativeCanvas: any = null;
let nativeWidth = 0;
let nativeHeight = 0;

function numericSeries(option: any) {
  return (option?.series || []).filter((series: any) => Array.isArray(series.data));
}

function drawNative(option: any) {
  if (!nativeCanvas || !nativeWidth || !nativeHeight || !option) return;
  const dpr = Number(uni.getWindowInfo().pixelRatio || 1);
  nativeCanvas.width = nativeWidth * dpr;
  nativeCanvas.height = nativeHeight * dpr;
  const ctx = nativeCanvas.getContext('2d');
  ctx.scale(dpr, dpr);
  ctx.clearRect(0, 0, nativeWidth, nativeHeight);

  const labels = option?.xAxis?.data || [];
  const series = numericSeries(option);
  const values = series.flatMap((item: any) => item.data).filter((value: any) => Number.isFinite(Number(value))).map(Number);
  if (!values.length) return;
  const showLegend = option?.legend?.show !== false;
  const dualAxis = series.length === 2
    && String(series[0]?.name).includes('容量')
    && String(series[1]?.name).includes('次数');
  const padding = { left: 50, right: dualAxis ? 42 : 18, top: showLegend ? 42 : 26, bottom: 34 };
  const width = nativeWidth - padding.left - padding.right;
  const height = nativeHeight - padding.top - padding.bottom;
  const x = (index: number) => padding.left + (labels.length <= 1 ? width / 2 : index / (labels.length - 1) * width);

  ctx.strokeStyle = '#E6ECEA';
  ctx.lineWidth = 1;
  for (let row = 0; row <= 3; row += 1) {
    const py = padding.top + row / 3 * height;
    ctx.beginPath(); ctx.moveTo(padding.left, py); ctx.lineTo(nativeWidth - padding.right, py); ctx.stroke();
  }
  ctx.fillStyle = '#8FA3A1';
  ctx.font = '10px sans-serif';
  ctx.textAlign = 'center';
  labels.forEach((label: string, index: number) => {
    if (labels.length <= 7 || index % Math.ceil(labels.length / 7) === 0 || index === labels.length - 1) ctx.fillText(label, x(index), nativeHeight - 10);
  });

  const colors = ['#5BC89A', '#FFB77D', '#6BA8D6', '#C490E0'];
  const formatValue = (value: number, name = '') => {
    const number = Math.abs(value % 1) > .001 ? value.toFixed(1) : String(Math.round(value));
    if (name.includes('体重') || name.includes('容量')) return `${number}kg`;
    if (name.includes('次数')) return `${number}次`;
    if (name.includes('热量')) return `${number}kcal`;
    return `${number}g`;
  };
  const bounds = (items: number[], name = '') => {
    if (name.includes('体重')) {
      const rawMin = Math.min(...items);
      const rawMax = Math.max(...items);
      const spread = rawMax - rawMin || 1;
      return { min: Math.max(0, rawMin - spread * .35), max: rawMax + spread * .35 };
    }
    return { min: Math.min(0, ...items), max: Math.max(1, ...items) };
  };

  const primaryValues = series[0].data.filter((value: any) => Number.isFinite(Number(value))).map(Number);
  const primaryBounds = bounds(primaryValues, series[0].name);
  ctx.fillStyle = '#8FA3A1';
  ctx.textAlign = 'right';
  ctx.font = '9px sans-serif';
  for (let row = 0; row <= 3; row += 1) {
    const value = primaryBounds.min + (primaryBounds.max - primaryBounds.min) * (3 - row) / 3;
    ctx.fillText(formatValue(value, series[0].name), padding.left - 6, padding.top + row / 3 * height + 3);
  }
  if (dualAxis) {
    const secondaryValues = series[1].data.filter((value: any) => Number.isFinite(Number(value))).map(Number);
    const secondaryBounds = bounds(secondaryValues, series[1].name);
    ctx.textAlign = 'left';
    for (let row = 0; row <= 3; row += 1) {
      const value = secondaryBounds.min + (secondaryBounds.max - secondaryBounds.min) * (3 - row) / 3;
      ctx.fillText(formatValue(value, series[1].name), nativeWidth - padding.right + 6, padding.top + row / 3 * height + 3);
    }
  }

  series.forEach((item: any, seriesIndex: number) => {
    const data = item.data.map((value: any) => value == null ? null : Number(value));
    const ownValues = data.filter((value: number | null) => value !== null) as number[];
    const ownBounds = bounds(ownValues, item.name);
    const ownMin = ownBounds.min;
    const ownMax = ownBounds.max;
    const ownRange = ownMax - ownMin || 1;
    const seriesY = (value: number) => padding.top + height - (value - ownMin) / ownRange * height;
    const color = item?.itemStyle?.color || colors[seriesIndex % colors.length];
    if (showLegend) {
      ctx.fillStyle = color;
      ctx.textAlign = 'left';
      ctx.font = '10px sans-serif';
      ctx.fillText(`● ${item.name || `数据${seriesIndex + 1}`}`, padding.left + seriesIndex * 86, 16 + (seriesIndex > 2 ? 14 : 0));
    }
    const meaningful = data.map((value: number | null, index: number) => ({ value, index })).filter(({ value }) => value !== null && (Number(value) !== 0 || String(item.name).includes('体重')));
    const labelStep = Math.max(1, Math.ceil(meaningful.length / 10));
    const shouldLabel = (index: number) => {
      const position = meaningful.findIndex((point) => point.index === index);
      return position >= 0 && (position % labelStep === 0 || position === meaningful.length - 1);
    };
    if (item.type === 'bar') {
      const barWidth = Math.max(4, Math.min(18, width / Math.max(data.length, 1) * .55));
      data.forEach((value: number | null, index: number) => {
        if (value == null) return;
        const py = seriesY(value);
        ctx.fillStyle = color;
        ctx.fillRect(x(index) - barWidth / 2, py, barWidth, padding.top + height - py);
        if (shouldLabel(index)) {
          ctx.fillStyle = '#5C6B6A'; ctx.textAlign = 'center'; ctx.font = '9px sans-serif';
          ctx.fillText(formatValue(value, item.name), x(index), Math.max(padding.top - 7, py - 7));
        }
      });
      return;
    }
    ctx.strokeStyle = color;
    ctx.lineWidth = 2.5;
    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';
    ctx.beginPath();
    let started = false;
    data.forEach((value: number | null, index: number) => {
      if (value == null) { started = false; return; }
      const px = x(index); const py = seriesY(value);
      if (!started) { ctx.moveTo(px, py); started = true; } else ctx.lineTo(px, py);
    });
    ctx.stroke();
    data.forEach((value: number | null, index: number) => {
      if (value == null) return;
      ctx.fillStyle = '#FFFFFF'; ctx.beginPath(); ctx.arc(x(index), seriesY(value), 4, 0, Math.PI * 2); ctx.fill();
      ctx.fillStyle = color; ctx.beginPath(); ctx.arc(x(index), seriesY(value), 2.5, 0, Math.PI * 2); ctx.fill();
      if (shouldLabel(index)) {
        ctx.fillStyle = '#5C6B6A'; ctx.textAlign = 'center'; ctx.font = '9px sans-serif';
        const py = seriesY(value);
        const labelY = dualAxis && seriesIndex === 1
          ? Math.min(padding.top + height - 6, py + 15)
          : Math.max(padding.top - 7, py - 8);
        ctx.fillText(formatValue(value, item.name), x(index), labelY);
      }
    });
  });
}

onMounted(async () => {
  // #ifdef MP-WEIXIN
  await nextTick();
  uni.createSelectorQuery().in(instance?.proxy).select('#' + props.canvasId)
    .fields({ node: true, size: true }, () => {})
    .exec((result: any[]) => {
      nativeCanvas = result?.[0]?.node;
      nativeWidth = Number(result?.[0]?.width || 0);
      nativeHeight = Number(result?.[0]?.height || 0);
      drawNative(props.option);
    });
  // #endif
  // #ifdef H5
  if (chartEl.value) { chartInstance = echarts.init(chartEl.value as any); chartInstance.setOption(props.option); }
  // #endif
});

watch(() => props.option, (option) => {
  // #ifdef MP-WEIXIN
  drawNative(option);
  // #endif
  // #ifdef H5
  chartInstance?.setOption(option, true);
  // #endif
}, { deep: true });

onBeforeUnmount(() => { chartInstance?.dispose?.(); chartInstance = null; nativeCanvas = null; });
</script>

<style lang="scss" scoped>
.chart { width: 100%; height: 100%; }
</style>
