<template>
  <view class="stats-page">
    <!-- Range 切换：玻璃药丸 -->
    <view class="range-bar">
      <liquid-glass-pill
        v-for="r in ranges"
        :key="r.value"
        :text="r.label"
        :variant="range === r.value ? 'primary' : 'default'"
        size="md"
        interactive
        :active="range === r.value"
        @tap="setRange(r.value as 7 | 30 | 90)"
      />
    </view>

    <view v-if="loading" class="loading">加载中...</view>

    <!-- 饮食 -->
    <liquid-glass-card :highlight="true" class="chart-card">
      <view class="chart-head">
        <view class="chart-title-row">
          <text class="chart-emoji">🥗</text>
          <text class="chart-title">饮食热量与营养</text>
        </view>
        <view class="chart-sub">平均 {{ Math.round(avgCalories) }} kcal / 天</view>
      </view>
      <view class="chart-box">
        <EChartsView v-if="dietOption" :option="dietOption" canvas-id="diet-chart" />
        <view v-else class="chart-empty">暂无数据</view>
      </view>
      <view class="macros-summary">
        <view class="ms-cell">
          <view class="ms-num">{{ Math.round(avgCarbs) }}</view>
          <view class="ms-name">碳水 g/天</view>
        </view>
        <view class="ms-cell">
          <view class="ms-num">{{ Math.round(avgProtein) }}</view>
          <view class="ms-name">蛋白质 g/天</view>
        </view>
        <view class="ms-cell">
          <view class="ms-num">{{ Math.round(avgFat) }}</view>
          <view class="ms-name">脂肪 g/天</view>
        </view>
      </view>
    </liquid-glass-card>

    <!-- 训练 -->
    <liquid-glass-card :highlight="true" class="chart-card">
      <view class="chart-head">
        <view class="chart-title-row">
          <text class="chart-emoji">🏋️</text>
          <text class="chart-title">训练容量与次数</text>
        </view>
        <view class="chart-sub">{{ totalSessions }} 次训练 · 容量 {{ Math.round(totalVolume) }} kg</view>
      </view>
      <view class="chart-box">
        <EChartsView v-if="trainingOption" :option="trainingOption" canvas-id="training-chart" />
        <view v-else class="chart-empty">暂无训练数据</view>
      </view>
    </liquid-glass-card>

    <!-- 体重 -->
    <liquid-glass-card :highlight="true" class="chart-card">
      <view class="chart-head">
        <view class="chart-title-row">
          <text class="chart-emoji">⚖️</text>
          <text class="chart-title">体重趋势</text>
        </view>
        <view v-if="weightChange !== null" class="chart-sub" :class="{ down: weightChange < 0, up: weightChange > 0 }">
          {{ weightChange > 0 ? '+' : '' }}{{ weightChange.toFixed(1) }} kg
        </view>
      </view>
      <view class="chart-box">
        <EChartsView v-if="weightOption" :option="weightOption" canvas-id="weight-chart" />
        <view v-else class="chart-empty">暂无体重记录</view>
      </view>
    </liquid-glass-card>
  </view>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { onShow } from '@dcloudio/uni-app';
import { statsApi, DietStatPoint, TrainingStatPoint, WeightStatPoint } from '@/api/stats';
import { useAuthStore } from '@/store/auth';
import { chartTheme } from '@/utils/echarts';
import EChartsView from '@/components/EChartsView.vue';

// 同步自定义 tabBar 高亮
function syncTabBar() {
  const pages = getCurrentPages();
  const page = pages[pages.length - 1];
  const tabBar = (page as any)?.getTabBar?.();
  if (tabBar) tabBar.setData({ activeIdx: 3 });
}

const auth = useAuthStore();

const ranges = [
  { value: 7, label: '7 天' },
  { value: 30, label: '30 天' },
  { value: 90, label: '90 天' },
];

const range = ref<7 | 30 | 90>(30);

const dietData = ref<DietStatPoint[]>([]);
const trainingData = ref<TrainingStatPoint[]>([]);
const weightData = ref<WeightStatPoint[]>([]);

const avgCalories = computed(() => {
  if (!dietData.value.length) return 0;
  return dietData.value.reduce((s, d) => s + d.calories_kcal, 0) / dietData.value.length;
});
const avgCarbs = computed(() => {
  if (!dietData.value.length) return 0;
  return dietData.value.reduce((s, d) => s + d.carbs_g, 0) / dietData.value.length;
});
const avgProtein = computed(() => {
  if (!dietData.value.length) return 0;
  return dietData.value.reduce((s, d) => s + d.protein_g, 0) / dietData.value.length;
});
const avgFat = computed(() => {
  if (!dietData.value.length) return 0;
  return dietData.value.reduce((s, d) => s + d.fat_g, 0) / dietData.value.length;
});
const totalSessions = computed(() => trainingData.value.reduce((s, d) => s + d.session_count, 0));
const totalVolume = computed(() => trainingData.value.reduce((s, d) => s + d.total_volume, 0));
const weightChange = computed<number | null>(() => {
  const valid = weightData.value.filter((d) => d.weight_kg != null);
  if (valid.length < 2) return null;
  return (valid[valid.length - 1].weight_kg as number) - (valid[0].weight_kg as number);
});

const dietOption = computed(() => {
  if (!dietData.value.length) return null;
  const dates = dietData.value.map((d) => d.date.slice(5));
  const cals = dietData.value.map((d) => d.calories_kcal);
  const carbs = dietData.value.map((d) => d.carbs_g);
  const protein = dietData.value.map((d) => d.protein_g);
  const fat = dietData.value.map((d) => d.fat_g);
  const goal = dietData.value[0]?.calories_goal || 0;

  return {
    color: [chartTheme.primary, chartTheme.accent, chartTheme.info, chartTheme.purple],
    grid: { left: 40, right: 16, top: 16, bottom: 28 },
    tooltip: { trigger: 'axis' },
    legend: { show: false },
    xAxis: {
      type: 'category',
      data: dates,
      axisLine: { lineStyle: { color: chartTheme.divider } },
      axisLabel: { color: chartTheme.text3, fontSize: 10 },
      axisTick: { show: false },
    },
    yAxis: [
      {
        type: 'value',
        name: '热量',
        position: 'left',
        axisLabel: { color: chartTheme.text3, fontSize: 10 },
        splitLine: { lineStyle: { color: chartTheme.grid, type: 'dashed' } },
        axisLine: { show: false },
      },
      {
        type: 'value',
        name: 'g',
        position: 'right',
        axisLabel: { color: chartTheme.text3, fontSize: 10 },
        splitLine: { show: false },
        axisLine: { show: false },
      },
    ],
    series: [
      {
        name: '热量',
        type: 'line',
        smooth: true,
        data: cals,
        lineStyle: { width: 3 },
        areaStyle: {
          color: {
            type: 'linear',
            x: 0, y: 0, x2: 0, y2: 1,
            colorStops: [
              { offset: 0, color: 'rgba(91, 200, 154, 0.35)' },
              { offset: 1, color: 'rgba(91, 200, 154, 0)' },
            ],
          },
        },
        markLine: goal ? {
          symbol: 'none',
          lineStyle: { color: chartTheme.warm, type: 'dashed' },
          data: [{ yAxis: goal, name: '目标' }],
          label: { color: chartTheme.warm, fontSize: 10 },
        } : undefined,
      },
      {
        name: '碳水',
        type: 'line',
        yAxisIndex: 1,
        smooth: true,
        data: carbs,
        symbol: 'circle',
        symbolSize: 6,
      },
      {
        name: '蛋白质',
        type: 'line',
        yAxisIndex: 1,
        smooth: true,
        data: protein,
        symbol: 'circle',
        symbolSize: 6,
      },
      {
        name: '脂肪',
        type: 'line',
        yAxisIndex: 1,
        smooth: true,
        data: fat,
        symbol: 'circle',
        symbolSize: 6,
      },
    ],
  };
});

const trainingOption = computed(() => {
  if (!trainingData.value.length) return null;
  const dates = trainingData.value.map((d) => d.date.slice(5));
  const volume = trainingData.value.map((d) => d.total_volume);
  const count = trainingData.value.map((d) => d.session_count);

  return {
    color: [chartTheme.primary, chartTheme.warm],
    grid: { left: 40, right: 16, top: 16, bottom: 28 },
    tooltip: { trigger: 'axis' },
    legend: {
      icon: 'circle',
      bottom: 0,
      itemWidth: 8,
      itemHeight: 8,
      textStyle: { color: chartTheme.text2, fontSize: 11 },
    },
    xAxis: {
      type: 'category',
      data: dates,
      axisLine: { lineStyle: { color: chartTheme.divider } },
      axisLabel: { color: chartTheme.text3, fontSize: 10 },
      axisTick: { show: false },
    },
    yAxis: [
      {
        type: 'value',
        name: '容量',
        axisLabel: { color: chartTheme.text3, fontSize: 10 },
        splitLine: { lineStyle: { color: chartTheme.grid, type: 'dashed' } },
        axisLine: { show: false },
      },
      {
        type: 'value',
        name: '次数',
        position: 'right',
        axisLabel: { color: chartTheme.text3, fontSize: 10 },
        splitLine: { show: false },
        axisLine: { show: false },
      },
    ],
    series: [
      {
        name: '训练容量',
        type: 'bar',
        data: volume,
        barWidth: '50%',
        itemStyle: { color: chartTheme.primary, borderRadius: [6, 6, 0, 0] },
      },
      {
        name: '训练次数',
        type: 'line',
        yAxisIndex: 1,
        smooth: true,
        data: count,
        symbol: 'circle',
        symbolSize: 6,
      },
    ],
  };
});

const weightOption = computed(() => {
  const valid = weightData.value.filter((d) => d.weight_kg != null);
  if (!valid.length) return null;
  const dates = weightData.value.map((d) => d.date.slice(5));
  const weights = weightData.value.map((d) => d.weight_kg);
  const target = valid[0]?.target_weight_kg;

  return {
    color: [chartTheme.primary, chartTheme.warm],
    grid: { left: 40, right: 16, top: 16, bottom: 28 },
    tooltip: { trigger: 'axis' },
    xAxis: {
      type: 'category',
      data: dates,
      axisLine: { lineStyle: { color: chartTheme.divider } },
      axisLabel: { color: chartTheme.text3, fontSize: 10 },
      axisTick: { show: false },
    },
    yAxis: {
      type: 'value',
      scale: true,
      axisLabel: { color: chartTheme.text3, fontSize: 10 },
      splitLine: { lineStyle: { color: chartTheme.grid, type: 'dashed' } },
      axisLine: { show: false },
    },
    series: [
      {
        name: '体重',
        type: 'line',
        smooth: true,
        data: weights,
        lineStyle: { width: 3 },
        symbol: 'circle',
        symbolSize: 6,
        areaStyle: {
          color: {
            type: 'linear',
            x: 0, y: 0, x2: 0, y2: 1,
            colorStops: [
              { offset: 0, color: 'rgba(91, 200, 154, 0.3)' },
              { offset: 1, color: 'rgba(91, 200, 154, 0)' },
            ],
          },
        },
        markLine: target ? {
          symbol: 'none',
          lineStyle: { color: chartTheme.warm, type: 'dashed' },
          data: [{ yAxis: target, name: '目标' }],
          label: { color: chartTheme.warm, fontSize: 10 },
        } : undefined,
        connectNulls: true,
      },
    ],
  };
});

const loading = ref(false);

async function load() {
  if (!auth.ready) await auth.bootstrap();
  if (!auth.isLogged) return;
  loading.value = true;
  try {
    const [d, t, w] = await Promise.all([
      statsApi.diet(range.value),
      statsApi.training(range.value),
      statsApi.weight(range.value),
    ]);
    dietData.value = d.items || [];
    trainingData.value = t.items || [];
    weightData.value = w.items || [];
  } catch {
    uni.showToast({ title: '加载失败，请重试', icon: 'none' });
    dietData.value = [];
    trainingData.value = [];
    weightData.value = [];
  } finally {
    loading.value = false;
  }
}

function setRange(r: 7 | 30 | 90) {
  range.value = r;
  load();
}

onMounted(() => {
  syncTabBar();
  load();
});

onShow(() => {
  syncTabBar();
  if (auth.isLogged) load();
});
</script>

<style lang="scss" scoped>
.stats-page {
  padding: $gap-3;
  padding-bottom: calc(#{$tabbar-height} + #{$gap-4} + #{$gap-2});
  animation: lg-fade-up 0.4s $ease-spring both;
}

.range-bar {
  display: flex;
  gap: 12rpx;
  margin-bottom: $gap-3;
  padding: 6rpx 0;
}

.loading {
  text-align: center;
  padding: $gap-4 0;
  color: $text-3;
  font-size: $fs-sm;
}

.chart-card {
  padding: $gap-3;
  margin-bottom: $gap-3;
}

.chart-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: $gap-2;
}

.chart-title-row {
  display: flex;
  align-items: center;
  gap: 8rpx;
}

.chart-emoji {
  font-size: $fs-lg;
  filter: drop-shadow(0 2rpx 4rpx rgba(95, 175, 145, 0.15));
}

.chart-title {
  font-size: $fs-lg;
  font-weight: 700;
  color: $text-1;
  letter-spacing: 0.3rpx;
}

.chart-sub {
  font-size: $fs-sm;
  color: $primary;
  font-weight: 600;
  background: rgba(234, 248, 241, 0.6);
  padding: 4rpx 14rpx;
  border-radius: $r-pill;
  &.up { color: $warn; background: rgba(255, 238, 217, 0.7); }
  &.down { color: $primary; background: rgba(234, 248, 241, 0.7); }
}

.chart-box {
  height: 400rpx;
  width: 100%;
}

.chart-empty {
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: $text-3;
  font-size: $fs-sm;
}

.macros-summary {
  display: flex;
  justify-content: space-around;
  margin-top: $gap-2;
  padding-top: $gap-2;
  border-top: 1rpx solid $divider;
}

.ms-cell {
  text-align: center;
}

.ms-num {
  font-size: $fs-xl;
  font-weight: 800;
  color: $primary-deep;
  letter-spacing: -0.5rpx;
}

.ms-name {
  font-size: $fs-xs;
  color: $text-3;
  margin-top: 2rpx;
}
</style>