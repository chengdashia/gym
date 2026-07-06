<template>
  <view class="diet-page">
    <view class="header">
      <view class="date-bar">
        <scroll-view scroll-x class="date-scroll" :show-scrollbar="false">
          <view class="date-row">
            <view
              v-for="d in weekDates"
              :key="d.date"
              :class="['date-item', { active: d.date === selectedDate }]"
              @tap="selectDate(d.date)"
            >
              <view class="date-weekday">{{ d.weekday }}</view>
              <view class="date-day">{{ d.day }}</view>
            </view>
          </view>
        </scroll-view>
      </view>

      <view class="summary-card">
        <view class="sum-row">
          <view class="sum-main">
            <view class="sum-num">{{ Math.round(summary.calories_kcal) }}</view>
            <view class="sum-label">/ {{ Math.round(goalKcal) }} kcal</view>
          </view>
          <view class="sum-progress">
            <ProgressRing :value="summary.calories_kcal" :goal="goalKcal || 1" :size="100" :thickness="10" />
          </view>
        </view>
        <view class="sum-macros">
          <view class="sm-cell">
            <view class="sm-name">碳水</view>
            <view class="sm-val">{{ Math.round(summary.carbs_g) }}<text class="sm-goal">/{{ Math.round(goalCarbs) }}</text></view>
          </view>
          <view class="sm-cell">
            <view class="sm-name">蛋白质</view>
            <view class="sm-val">{{ Math.round(summary.protein_g) }}<text class="sm-goal">/{{ Math.round(goalProtein) }}</text></view>
          </view>
          <view class="sm-cell">
            <view class="sm-name">脂肪</view>
            <view class="sm-val">{{ Math.round(summary.fat_g) }}<text class="sm-goal">/{{ Math.round(goalFat) }}</text></view>
          </view>
        </view>
      </view>
    </view>

    <view class="meal-list">
      <view v-for="m in mealTypes" :key="m.value" class="meal-card">
        <view class="meal-head" @tap="toggleMeal(m.value)">
          <view class="meal-left">
            <view class="meal-emoji">{{ mEmoji(m.value) }}</view>
            <view class="meal-info">
              <view class="meal-name">{{ m.label }}</view>
              <view class="meal-sub">{{ mealSubText(m.value) }}</view>
            </view>
          </view>
          <view class="meal-right">
            <view class="meal-cal">{{ Math.round(mealCal(m.value)) }} kcal</view>
            <text class="meal-arrow">{{ expanded[m.value] ? '▾' : '▸' }}</text>
          </view>
        </view>

        <view v-if="expanded[m.value]" class="meal-body">
          <view v-if="(meals[m.value] || []).length === 0" class="meal-empty">
            <text>暂无记录</text>
          </view>
          <view
            v-for="r in meals[m.value] || []"
            :key="r.id"
            class="record-row"
            @tap="editRecord(r)"
          >
            <view class="record-info">
              <view class="record-name">{{ r.food_name_snapshot }}</view>
              <view class="record-amount">
                {{ formatAmount(r) }} · {{ r.record_time }}
              </view>
            </view>
            <view class="record-nut">
              <view class="record-cal">{{ Math.round(r.calories_kcal) }} kcal</view>
              <view class="record-macros">
                C{{ r.carbs_g }}g · P{{ r.protein_g }}g · F{{ r.fat_g }}g
              </view>
            </view>
          </view>

          <view class="meal-add" @tap="addMeal(m.value)">+ 添加食物</view>
        </view>
      </view>
    </view>

    <view class="fab-wrap">
      <Fab icon="+" @tap="showAddSheet = true" />
    </view>

    <!-- 添加方式选择 -->
    <view v-if="showAddSheet" class="sheet-mask" @tap="showAddSheet = false">
      <view class="sheet" @tap.stop>
        <view class="sheet-title">添加饮食</view>
        <view class="sheet-item" @tap="go('add')">
          <view class="sheet-emoji">🔍</view>
          <view class="sheet-text">搜索食物</view>
        </view>
        <view class="sheet-item" @tap="go('custom')">
          <view class="sheet-emoji">✏️</view>
          <view class="sheet-text">自定义食物</view>
        </view>
        <view class="sheet-item" @tap="go('photo')">
          <view class="sheet-emoji">📷</view>
          <view class="sheet-text">拍照识别</view>
        </view>
        <view class="sheet-cancel" @tap="showAddSheet = false">取消</view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { onShow } from '@dcloudio/uni-app';
import { useDietStore } from '@/store/diet';
import { useUserStore } from '@/store/user';
import ProgressRing from '@/components/ProgressRing.vue';
import Fab from '@/components/Fab.vue';
import { MEAL_TYPES, MealType } from '@/utils/constants';
import { addDays, formatDate, weekdayCN, today } from '@/utils/date';
import type { DietRecord } from '@/api/diet';

const dietStore = useDietStore();
const userStore = useUserStore();

const mealTypes = MEAL_TYPES;
const selectedDate = computed(() => dietStore.selectedDate);
const summary = computed(() => dietStore.summary);
const meals = computed(() => dietStore.meals);
const goalKcal = computed(() => userStore.goal.calories_kcal);
const goalCarbs = computed(() => userStore.goal.carbs_g);
const goalProtein = computed(() => userStore.goal.protein_g);
const goalFat = computed(() => userStore.goal.fat_g);

const showAddSheet = ref(false);
const expanded = ref<Record<string, boolean>>({ breakfast: true, lunch: true, dinner: true, snack: true });

const weekDates = computed(() => {
  const t = new Date();
  const list = [];
  for (let i = -7; i <= 7; i++) {
    const d = addDays(t, i);
    list.push({
      date: formatDate(d),
      weekday: weekdayCN(formatDate(d))[1],
      day: d.getDate(),
    });
  }
  return list;
});

async function load() {
  if (!userStore.goal?.calories_kcal) await userStore.fetchGoal().catch(() => {});
  await dietStore.fetch();
}

onMounted(load);
onShow(load);

function selectDate(d: string) {
  dietStore.setDate(d);
  dietStore.fetch();
}

function toggleMeal(v: MealType) {
  expanded.value[v] = !expanded.value[v];
}

function mealCal(v: MealType) {
  return (meals.value[v] || []).reduce((s, r) => s + r.calories_kcal, 0);
}

function mealSubText(v: MealType) {
  const list = meals.value[v] || [];
  if (!list.length) return '尚未记录';
  return `${list.length} 条记录`;
}

function mEmoji(v: MealType) {
  return { breakfast: '🌅', lunch: '🍱', dinner: '🌙', snack: '🍪' }[v];
}

function formatAmount(r: DietRecord) {
  if (r.unit_type === 'g') return `${r.amount_g}g`;
  return `${r.serving_count} 份`;
}

function addMeal(v: MealType) {
  uni.navigateTo({ url: `/pages/diet/add?date=${selectedDate.value}&meal=${v}` });
}

function editRecord(r: DietRecord) {
  uni.navigateTo({ url: `/pages/diet/record-edit?id=${r.id}` });
}

function go(action: 'add' | 'custom' | 'photo') {
  showAddSheet.value = false;
  const url =
    action === 'add' ? `/pages/diet/add?date=${selectedDate.value}` :
    action === 'custom' ? '/pages/diet/custom-food' :
    '/pages/diet/photo-recognize';
  uni.navigateTo({ url });
}
</script>

<style lang="scss" scoped>
.diet-page {
  min-height: 100vh;
  background: $bg;
  padding-bottom: 200rpx;
}

.header {
  background: $gradient-card;
  border-radius: 0 0 $r-24 $r-24;
  padding: $gap-3;
  margin-bottom: $gap-3;
}
.date-bar {
  margin-bottom: $gap-2;
}
.date-scroll {
  white-space: nowrap;
  width: 100%;
}
.date-row {
  display: inline-flex;
  gap: 12rpx;
  padding: 4rpx 0;
}
.date-item {
  flex-shrink: 0;
  width: 80rpx;
  padding: 14rpx 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  border-radius: $r-16;
  background: $card;
  &.active {
    background: $primary;
    .date-weekday, .date-day { color: #fff; }
  }
}
.date-weekday {
  font-size: $fs-xs;
  color: $text-3;
}
.date-day {
  margin-top: 4rpx;
  font-size: $fs-lg;
  font-weight: 600;
  color: $text-1;
}

.summary-card {
  background: $card;
  border-radius: $r-20;
  padding: $gap-3;
  box-shadow: $shadow-md;
}
.sum-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.sum-main {
  display: flex;
  align-items: baseline;
  gap: 8rpx;
}
.sum-num {
  font-size: 64rpx;
  font-weight: 700;
  color: $text-1;
  line-height: 1;
}
.sum-label {
  font-size: $fs-md;
  color: $text-3;
}
.sum-progress { padding: 0; }
.sum-macros {
  display: flex;
  justify-content: space-around;
  margin-top: $gap-3;
  padding-top: $gap-2;
  border-top: 1rpx solid $divider;
}
.sm-cell {
  text-align: center;
}
.sm-name {
  font-size: $fs-xs;
  color: $text-3;
}
.sm-val {
  margin-top: 4rpx;
  font-size: $fs-lg;
  font-weight: 600;
  color: $text-1;
}
.sm-goal {
  font-size: $fs-xs;
  color: $text-3;
  font-weight: 400;
  margin-left: 4rpx;
}

.meal-list {
  padding: 0 $gap-3;
}
.meal-card {
  background: $card;
  border-radius: $r-20;
  margin-bottom: $gap-2;
  overflow: hidden;
  box-shadow: $shadow-sm;
}
.meal-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: $gap-3;
}
.meal-left {
  display: flex;
  align-items: center;
  gap: $gap-2;
}
.meal-emoji {
  width: 80rpx;
  height: 80rpx;
  border-radius: $r-16;
  background: $primary-tint;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 40rpx;
}
.meal-name {
  font-size: $fs-lg;
  font-weight: 600;
  color: $text-1;
}
.meal-sub {
  font-size: $fs-sm;
  color: $text-3;
  margin-top: 4rpx;
}
.meal-right {
  display: flex;
  align-items: center;
  gap: $gap-2;
}
.meal-cal {
  font-size: $fs-md;
  color: $primary;
  font-weight: 600;
}
.meal-arrow {
  color: $text-3;
  font-size: $fs-md;
}

.meal-body {
  padding: 0 $gap-3 $gap-3;
}
.meal-empty {
  text-align: center;
  color: $text-3;
  font-size: $fs-sm;
  padding: $gap-3 0;
}
.record-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: $gap-2 0;
  border-bottom: 1rpx solid $divider;
  &:last-of-type { border-bottom: none; }
}
.record-info {
  flex: 1;
}
.record-name {
  font-size: $fs-md;
  color: $text-1;
}
.record-amount {
  margin-top: 4rpx;
  font-size: $fs-xs;
  color: $text-3;
}
.record-nut {
  text-align: right;
}
.record-cal {
  font-size: $fs-md;
  color: $primary;
  font-weight: 600;
}
.record-macros {
  font-size: $fs-xs;
  color: $text-3;
}
.meal-add {
  text-align: center;
  padding: $gap-2;
  margin-top: $gap-1;
  background: $primary-tint;
  border-radius: $r-12;
  color: $primary-deep;
  font-size: $fs-sm;
  font-weight: 500;
}

.fab-wrap {
  position: fixed;
  right: $gap-3;
  bottom: calc(#{$tabbar-height} + #{$gap-3});
  z-index: 30;
}

.sheet-mask {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.4);
  z-index: 200;
  display: flex;
  align-items: flex-end;
}
.sheet {
  width: 100%;
  background: $card;
  border-radius: $r-24 $r-24 0 0;
  padding: $gap-3 $gap-3 calc(#{$gap-3} + env(safe-area-inset-bottom));
}
.sheet-title {
  text-align: center;
  font-size: $fs-md;
  font-weight: 600;
  color: $text-1;
  margin-bottom: $gap-3;
}
.sheet-item {
  display: flex;
  align-items: center;
  padding: $gap-3 $gap-2;
  border-radius: $r-12;
  margin-bottom: $gap-1;
}
.sheet-emoji {
  width: 64rpx;
  height: 64rpx;
  border-radius: $r-16;
  background: $primary-tint;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 32rpx;
  margin-right: $gap-2;
}
.sheet-text {
  font-size: $fs-md;
  color: $text-1;
}
.sheet-cancel {
  margin-top: $gap-2;
  text-align: center;
  padding: $gap-3;
  background: $bg-2;
  border-radius: $r-16;
  color: $text-2;
  font-size: $fs-md;
}
</style>