<template>
  <view class="diet-page">
    <view class="header">
      <view class="date-heading">
        <text class="date-heading-main">{{ selectedDateHeading }}</text>
        <text class="date-heading-tip">点击下方日期查看当天饮食</text>
      </view>
      <!-- 日期切换：玻璃药丸横向滚动 -->
      <view class="date-bar">
        <scroll-view scroll-x class="date-scroll" :show-scrollbar="false">
          <view class="date-row">
            <view
              v-for="d in weekDates"
              :key="d.date"
              :class="['date-cell', { selected: d.date === selectedDate, today: d.isToday }]"
              @tap="selectDate(d.date)"
            >
              <text class="date-weekday">{{ d.isToday ? '今天' : d.weekday }}</text>
              <text class="date-day">{{ d.label }}</text>
            </view>
          </view>
        </scroll-view>
      </view>

      <!-- 摘要面板 -->
      <liquid-glass-panel variant="light" :highlight="true" :ambient="true" class="summary-panel">
        <view class="sum-row">
          <view class="sum-main">
            <view class="sum-num">{{ Math.round(summary.calories_kcal) }}</view>
            <view class="sum-label">/ {{ Math.round(goalKcal) }} kcal</view>
          </view>
          <view class="sum-progress">
            <ProgressRing :value="summary.calories_kcal" :goal="goalKcal || 1" :size="100" :thickness="10" />
          </view>
        </view>
        <view class="sum-divider" />
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
      </liquid-glass-panel>
    </view>

    <view class="meal-list">
      <liquid-glass-card
        v-for="m in mealTypes"
        :key="m.value"
        :highlight="true"
        class="meal-card"
      >
        <view class="meal-head" @tap="toggleMeal(m.value)">
          <view class="meal-left">
            <line-icon :name="mealIcon(m.value).icon" :tint="mealIcon(m.value).tint" :size="56" class="meal-emoji" />
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

          <view class="meal-actions">
            <view class="meal-add" @tap="addMeal(m.value)">+ 添加食物</view>
            <view v-if="selectedDate !== todayString && (meals[m.value] || []).length" class="meal-add" @tap="copyMeal(m.value)">复制到今天</view>
          </view>
        </view>
      </liquid-glass-card>
    </view>

    <!-- FAB -->
    <view class="fab-wrap" @tap="showAddSheet = true">
      <view class="fab">
        <text class="fab-icon">+</text>
        <view class="fab-shine" />
      </view>
    </view>

    <!-- 添加方式选择：居中弹出玻璃面板 -->
    <view v-if="showAddSheet" class="sheet-mask" @tap="showAddSheet = false">
      <view class="sheet-wrap" @tap.stop>
        <view class="sheet-grip" />
        <view class="sheet-title">添加饮食</view>
        <view class="sheet-subtitle">先选择餐次，再选择记录方式</view>
        <view class="sheet-meals">
          <liquid-glass-pill
            v-for="mealType in mealTypes"
            :key="mealType.value"
            :text="mealType.label"
            :variant="addSheetMeal === mealType.value ? 'primary' : 'default'"
            size="sm"
            interactive
            :active="addSheetMeal === mealType.value"
            @tap="addSheetMeal = mealType.value"
          />
        </view>
        <view class="sheet-grid">
          <view
            v-for="opt in addOptions"
            :key="opt.action"
            class="sheet-grid-item"
            @tap="go(opt.action)"
          >
            <line-icon :name="opt.icon" :tint="opt.tint" :size="80" class="sheet-emoji" />
            <view class="sheet-text-wrap">
              <view class="sheet-text">{{ opt.text }}</view>
              <view class="sheet-desc">{{ opt.desc }}</view>
            </view>
            <text class="sheet-arrow">›</text>
          </view>
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
import { useAuthStore } from '@/store/auth';
import ProgressRing from '@/components/ProgressRing.vue';
import { MEAL_TYPES, MealType } from '@/utils/constants';
import { addDays, formatDate, weekdayCN } from '@/utils/date';
import { requireAuth } from '@/utils/auth-guard';
import { dietApi, type DietRecord } from '@/api/diet';
import { formatTime } from '@/utils/date';
import { compactDateLabel, dietDateHeading } from '@/utils/diet-date';
import { buildDietEntryUrl } from '@/utils/diet-context';

// 同步自定义 tabBar 高亮
function syncTabBar() {
  const pages = getCurrentPages();
  const page = pages[pages.length - 1];
  const tabBar = (page as any)?.getTabBar?.();
  if (tabBar) tabBar.setData({ activeIdx: 1 });
}

const dietStore = useDietStore();
const userStore = useUserStore();
const auth = useAuthStore();

const mealTypes = MEAL_TYPES;
const selectedDate = computed(() => dietStore.selectedDate);
const summary = computed(() => dietStore.summary);
const meals = computed(() => dietStore.meals);
const goalKcal = computed(() => userStore.goal.calories_kcal);
const goalCarbs = computed(() => userStore.goal.carbs_g);
const goalProtein = computed(() => userStore.goal.protein_g);
const goalFat = computed(() => userStore.goal.fat_g);
const todayString = formatDate(new Date());
const selectedDateHeading = computed(() => dietDateHeading(selectedDate.value, todayString));

const showAddSheet = ref(false);
const addSheetMeal = ref<MealType>('lunch');
const expanded = ref<Record<string, boolean>>({ breakfast: true, lunch: true, dinner: true, snack: true });
const copying = ref(false);

const addOptions = [
  { action: 'add' as const,    icon: 'search', tint: 'mint' as const,  text: '搜索食物', desc: '从食物库查找' },
  { action: 'custom' as const, icon: 'edit',  tint: 'warm' as const,  text: '自定义食物', desc: '手动录入营养' },
  { action: 'photo' as const,  icon: 'camera', tint: 'sky' as const,   text: '拍照识别', desc: 'AI 智能识别' },
];

const weekDates = computed(() => {
  const t = new Date();
  const displayedMonth = t.getMonth() + 1;
  const list = [];
  for (let i = -7; i <= 7; i++) {
    const d = addDays(t, i);
    list.push({
      date: formatDate(d),
      weekday: weekdayCN(formatDate(d))[1],
      label: compactDateLabel(formatDate(d), displayedMonth),
      isToday: formatDate(d) === todayString,
    });
  }
  return list;
});

async function load() {
  if (!auth.ready) await auth.bootstrap();
  if (!auth.isLogged) return;
  if (!userStore.goal?.calories_kcal) await userStore.fetchGoal().catch(() => {});
  await dietStore.fetch();
}

onMounted(load);
onShow(() => {
  syncTabBar();
  if (auth.isLogged) load();
});

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

function mealIcon(v: MealType): { icon: string; tint: 'mint' | 'warm' | 'sky' | 'violet' } {
  const icons = {
    breakfast: { icon: 'sunrise', tint: 'warm' },
    lunch: { icon: 'bento', tint: 'mint' },
    dinner: { icon: 'moon', tint: 'sky' },
    snack: { icon: 'cookie', tint: 'violet' },
  } as const;
  return icons[v];
}

function formatAmount(r: DietRecord) {
  if (r.unit_type === 'g') return `${r.amount_g}g`;
  return `${r.serving_count} 份`;
}

function addMeal(v: MealType) {
  const url = buildDietEntryUrl('/pages/diet/add', {
    date: selectedDate.value,
    meal: v,
    time: formatTime(new Date()),
  });
  if (!requireAuth({ redirect: url })) return;
  uni.navigateTo({ url });
}

function editRecord(r: DietRecord) {
  const url = `/pages/diet/record-edit?id=${r.id}`;
  if (!requireAuth({ redirect: url })) return;
  uni.navigateTo({ url });
}

async function copyMeal(sourceMeal: MealType) {
  if (copying.value) return;
  copying.value = true;
  try {
    const result = await dietApi.copyMeal({
      source_date: selectedDate.value,
      source_meal_type: sourceMeal,
      target_date: todayString,
      target_meal_type: sourceMeal,
      record_time: formatTime(new Date()),
    });
    uni.showToast({ title: `已复制 ${result.count} 条`, icon: 'success' });
    dietStore.setDate(todayString);
    await dietStore.fetch();
  } catch (e: any) {
    uni.showToast({ title: e?.message || '复制失败', icon: 'none' });
  } finally {
    copying.value = false;
  }
}

function go(action: 'add' | 'custom' | 'photo') {
  showAddSheet.value = false;
  const paths = {
    add: '/pages/diet/add',
    custom: '/pages/diet/custom-food',
    photo: '/pages/diet/photo-recognize',
  } as const;
  const url = buildDietEntryUrl(paths[action], {
    date: selectedDate.value,
    meal: addSheetMeal.value,
    time: formatTime(new Date()),
  });
  if (!requireAuth({ redirect: url })) return;
  uni.navigateTo({ url });
}
</script>

<style lang="scss" scoped>
.diet-page {
  padding-bottom: calc(#{$tabbar-height} + #{$gap-5});
  animation: diet-page-in 0.4s $ease-spring both;
}

// 仅淡入不使用 transform，避免破坏子元素 position:fixed 的定位基准
@keyframes diet-page-in {
  from { opacity: 0; }
  to { opacity: 1; }
}

// ----- Header -----
.header {
  background: linear-gradient(160deg, rgba(166, 227, 197, 0.35) 0%, rgba(91, 200, 154, 0.12) 100%);
  border-radius: 0 0 40rpx 40rpx;
  padding: $gap-3;
  margin-bottom: $gap-3;
  position: relative;
  overflow: hidden;
}

.header::before {
  content: '';
  position: absolute;
  top: -60rpx;
  left: -40rpx;
  width: 240rpx;
  height: 240rpx;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(255, 255, 255, 0.45) 0%, transparent 70%);
  pointer-events: none;
}

.date-bar {
  margin-bottom: $gap-3;
  position: relative;
  z-index: 1;
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
.date-heading {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  margin-bottom: $gap-2;
}
.date-heading-main { font-size: 40rpx; font-weight: 800; color: $text-1; }
.date-heading-tip { font-size: $fs-xs; color: $text-3; }
.date-cell {
  min-width: 76rpx;
  padding: 10rpx 8rpx;
  border-radius: $r-12;
  background: rgba(255, 255, 255, .7);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4rpx;
  color: $text-2;
  &.today { box-shadow: inset 0 0 0 2rpx rgba(91, 200, 154, .35); }
  &.selected { background: $gradient-primary; color: #fff; box-shadow: 0 6rpx 16rpx rgba(95, 175, 145, .3); }
}
.date-weekday { font-size: 20rpx; }
.date-day { font-size: $fs-md; font-weight: 700; }

// ----- Summary Panel -----
.summary-panel {
  padding: $gap-3;
  position: relative;
  z-index: 1;
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
  font-weight: 800;
  color: $text-1;
  line-height: 1;
  letter-spacing: -1rpx;
}

.sum-label {
  font-size: $fs-md;
  color: $text-3;
}

.sum-divider {
  height: 1rpx;
  background: $divider;
  margin: $gap-3 0 $gap-2;
}

.sum-macros {
  display: flex;
  justify-content: space-around;
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
  font-weight: 700;
  color: $text-1;
}

.sm-goal {
  font-size: $fs-xs;
  color: $text-3;
  font-weight: 400;
  margin-left: 4rpx;
}

// ----- Meal List -----
.meal-list {
  padding: 0 $gap-3;
}

.meal-card {
  padding: 0;
  margin-bottom: $gap-2;
  overflow: hidden;
}

.meal-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: $gap-3;
  transition: background 0.3s $ease-glass;
}

.meal-head:active {
  background: rgba(255, 255, 255, 0.5);
}

.meal-left {
  display: flex;
  align-items: center;
  gap: $gap-2;
}

.meal-emoji {
  flex-shrink: 0;
}

.meal-name {
  font-size: $fs-lg;
  font-weight: 700;
  color: $text-1;
  letter-spacing: 0.3rpx;
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
  font-weight: 700;
}

.meal-arrow {
  color: $text-3;
  font-size: $fs-md;
  transition: transform 0.3s $ease-glass;
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
  transition: background 0.2s $ease-glass;

  &:active {
    background: rgba(255, 255, 255, 0.5);
  }

  &:last-of-type { border-bottom: none; }
}

.record-info {
  flex: 1;
}

.record-name {
  font-size: $fs-md;
  color: $text-1;
  font-weight: 500;
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
  font-weight: 700;
}

.record-macros {
  font-size: $fs-xs;
  color: $text-3;
}

.meal-add {
  text-align: center;
  padding: $gap-2;
  margin-top: $gap-1;
  background: rgba(234, 248, 241, 0.6);
  border-radius: $r-12;
  color: $primary-deep;
  font-size: $fs-sm;
  font-weight: 600;
  transition: background 0.3s $ease-glass, transform 0.3s $ease-spring;

  &:active {
    background: rgba(234, 248, 241, 0.85);
    transform: scale(0.92);
  }
}

// ----- FAB -----
.fab-wrap {
  position: fixed;
  right: $gap-3;
  top: 50%;
  transform: translateY(-50%);
  z-index: $z-fab;
}

.fab {
  position: relative;
  width: 110rpx;
  height: 110rpx;
  border-radius: 50%;
  background: $gradient-primary;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow:
    0 8rpx 24rpx rgba(95, 175, 145, 0.4),
    inset 0 1rpx 0 rgba(255, 255, 255, 0.4);
  overflow: hidden;
  transition: transform 0.3s $ease-spring;
}

.fab:active {
  transform: scale(0.92);
}

.fab-icon {
  font-size: 56rpx;
  color: #fff;
  font-weight: 300;
  line-height: 1;
}

.fab-shine {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 50%;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.4) 0%, rgba(255, 255, 255, 0) 100%);
  pointer-events: none;
}

// ----- Sheet (居中弹窗) -----
.sheet-mask {
  position: fixed;
  inset: 0;
  background: rgba(31, 42, 42, 0.45);
  z-index: $z-sheet;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: $gap-4;
  animation: sheet-fade-in 0.3s $ease-glass both;
}

@keyframes sheet-fade-in {
  from { background: rgba(31, 42, 42, 0); }
  to { background: rgba(31, 42, 42, 0.45); }
}

.sheet-wrap {
  width: 100%;
  max-width: 580rpx;
  background: rgba(247, 250, 248, 0.97);
  // #ifdef H5 || APP-PLUS
  backdrop-filter: blur(40rpx) saturate(180%);
  -webkit-backdrop-filter: blur(40rpx) saturate(180%);
  // #endif
  border-radius: 36rpx;
  padding: $gap-3 $gap-3 $gap-3;
  box-shadow: 0 24rpx 64rpx rgba(31, 42, 42, 0.25);
  animation: sheet-pop 0.35s $ease-spring both;
}

@keyframes sheet-pop {
  from { opacity: 0; transform: scale(0.92); }
  to { opacity: 1; transform: scale(1); }
}

.sheet-grip {
  width: 64rpx;
  height: 6rpx;
  background: rgba(143, 163, 161, 0.35);
  border-radius: $r-pill;
  margin: 0 auto $gap-2;
}

.sheet-title {
  text-align: center;
  font-size: $fs-xl;
  font-weight: 700;
  color: $text-1;
  letter-spacing: 0.5rpx;
}

.sheet-subtitle {
  text-align: center;
  font-size: $fs-xs;
  color: $text-3;
  margin-top: 4rpx;
  margin-bottom: $gap-3;
}

.sheet-meals {
  display: flex;
  justify-content: space-between;
  gap: 8rpx;
  margin-bottom: $gap-3;
}

.sheet-grid {
  display: flex;
  flex-direction: column;
  gap: $gap-2;
}

.sheet-grid-item {
  display: flex;
  align-items: center;
  padding: $gap-3;
  background: rgba(255, 255, 255, 0.65);
  border-radius: 24rpx;
  border: 1rpx solid rgba(255, 255, 255, 0.5);
  transition: transform 0.2s $ease-spring, background 0.3s $ease-glass;

  &:active {
    transform: scale(0.92);
    background: rgba(255, 255, 255, 0.85);
  }
}

.sheet-emoji {
  margin-right: $gap-3;
  flex-shrink: 0;
}

.sheet-text-wrap {
  flex: 1;
}

.sheet-text {
  font-size: $fs-md;
  color: $text-1;
  font-weight: 600;
  letter-spacing: 0.3rpx;
}

.sheet-desc {
  font-size: $fs-xs;
  color: $text-3;
  margin-top: 4rpx;
}

.sheet-arrow {
  font-size: $fs-lg;
  color: $text-3;
  flex-shrink: 0;
}

.sheet-cancel {
  margin-top: $gap-3;
  text-align: center;
  padding: $gap-2;
  color: $text-2;
  font-size: $fs-md;
  font-weight: 500;

  &:active {
    opacity: 0.6;
  }
}
</style>
