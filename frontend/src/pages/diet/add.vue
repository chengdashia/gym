<template>
  <view class="add-page">
    <view class="search-bar">
      <view class="search-input">
        <image class="search-icon-img" :src="searchIconSrc" mode="aspectFit" />
        <input
          v-model="keyword"
          placeholder="搜索食物"
          placeholder-class="ph"
          confirm-type="search"
          @confirm="search"
          @input="onSearchInput"
          class="input"
        />
        <text v-if="searching" class="searching-tip">搜索中...</text>
        <view v-if="keyword" class="clear" @tap="clearSearch">✕</view>
      </view>
    </view>

    <view v-if="!keyword && recentFoods.length" class="recent-section">
      <view class="recent-title">最近吃过</view>
      <view class="recent-list">
        <view v-for="food in recentFoods" :key="`${food.source}-${food.id}`" class="recent-item" @tap="pickRecent(food)">
          {{ food.name }}
        </view>
      </view>
    </view>

    <view v-if="results.length" class="result-list">
      <liquid-glass-card :highlight="true" padding="0" class="result-card">
        <view
          v-for="r in results"
          :key="`${r.source}-${r.id}`"
          class="result-item"
          @tap="pickFood(r)"
        >
          <view class="ri-info">
            <view class="ri-name">{{ r.name }}</view>
            <view class="ri-cat">{{ r.category || '-' }} · {{ Math.round(r.calories_per_100g) }} kcal/100g</view>
          </view>
          <view class="ri-tag">
            <Tag :text="r.source === 'custom' ? '自定义' : '系统'" :variant="r.source === 'custom' ? 'warn' : 'soft'" />
          </view>
        </view>
      </liquid-glass-card>
    </view>

    <view v-else-if="searched" class="empty-block">
      <EmptyState icon="diet" tint="warm" title="没有找到相关食物" desc="试试更短的关键词，或自定义食物">
        <view class="empty-actions">
          <liquid-glass-button variant="primary" size="sm" :block="false" text="自定义食物" @tap="goCustom" />
        </view>
      </EmptyState>
    </view>

    <view v-else class="empty-block">
      <EmptyState icon="search" tint="mint" title="输入关键词搜索" desc="支持中文、英文、拼音首字母" />
    </view>

    <!-- 选食物后填写克数 -->
    <view v-if="picked" class="picker-mask" @tap="cancelPick">
      <view class="picker" @tap.stop>
        <view class="picker-title">{{ picked.name }}</view>
        <view class="picker-cat">{{ picked.category || '-' }} · {{ picked.calories_per_100g }} kcal/100g</view>

        <view class="seg">
          <liquid-glass-pill
            text="按克数"
            :variant="unit === 'g' ? 'primary' : 'default'"
            size="md"
            interactive
            :active="unit === 'g'"
            @tap="setUnit('g')"
          />
          <liquid-glass-pill
            text="按份数"
            :variant="unit === 'serving' ? 'primary' : 'default'"
            size="md"
            interactive
            :active="unit === 'serving'"
            :custom-style="picked.serving_weight_g ? '' : 'opacity:0.4;'"
            @tap="picked.serving_weight_g && setUnit('serving')"
          />
        </view>

        <view v-if="unit === 'g'" class="form-row">
          <text class="form-label">克数</text>
          <input v-model.number="amount" type="digit" class="form-input" placeholder="克数" />
          <text class="form-unit">g</text>
        </view>
        <view v-else class="form-row">
          <text class="form-label">份数</text>
          <input v-model.number="amount" type="digit" class="form-input" placeholder="份数" />
          <text class="form-unit">份 · {{ picked.serving_weight_g }}g/份</text>
        </view>

        <view class="form-row">
          <text class="form-label">餐次</text>
          <view class="meal-chips">
            <liquid-glass-pill
              v-for="m in mealTypes"
              :key="m.value"
              :text="m.label"
              :variant="meal === m.value ? 'primary' : 'default'"
              size="sm"
              interactive
              :active="meal === m.value"
              @tap="meal = m.value as MealType"
            />
          </view>
        </view>

        <view class="form-row">
          <text class="form-label">日期</text>
          <picker mode="date" :value="date" @change="(e: any) => date = e.detail.value" class="time-picker">
            <view class="time-text">{{ date }}</view>
          </picker>
        </view>

        <view class="form-row">
          <text class="form-label">时间</text>
          <picker mode="time" :value="time" @change="(e: any) => time = e.detail.value" class="time-picker">
            <view class="time-text">{{ time }}</view>
          </picker>
        </view>

        <view class="preview">
          <view class="preview-num">{{ previewCal }} kcal</view>
          <view class="preview-macros">碳 {{ previewMacros.carbs }}g · 蛋 {{ previewMacros.protein }}g · 脂 {{ previewMacros.fat }}g</view>
        </view>

        <view class="picker-actions">
          <liquid-glass-button variant="ghost" size="md" :block="false" text="取消" @tap="cancelPick" />
          <liquid-glass-button variant="primary" size="md" :block="false" :text="selectMode ? '加入识别草稿' : '保存记录'" @tap="save" />
        </view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';
import { onLoad } from '@dcloudio/uni-app';
import EmptyState from '@/components/EmptyState.vue';
import Tag from '@/components/Tag.vue';
import { foodApi, FoodItem } from '@/api/food';
import { dietApi, RecentFood } from '@/api/diet';
import { useDietStore } from '@/store/diet';
import { useAuthStore } from '@/store/auth';
import { MEAL_TYPES, MealType } from '@/utils/constants';
import { calcNutrition } from '@/utils/nutrition';
import { formatTime, today } from '@/utils/date';
import { safeNavigateBack } from '@/utils/nav';
import { iconSrc } from '@/utils/icons';
import { requireAuth } from '@/utils/auth-guard';
import { buildDietEntryUrl, parseDietContext } from '@/utils/diet-context';
import { appendSelectionMode } from '@/utils/recognized-meal';

const searchIconSrc = iconSrc('search', '#8FA3A1', 1.8);

const mealTypes = MEAL_TYPES;
const dietStore = useDietStore();

const keyword = ref('');
const results = ref<FoodItem[]>([]);
const searched = ref(false);
const searching = ref(false);
const picked = ref<FoodItem | null>(null);
const unit = ref<'g' | 'serving'>('g');
const amount = ref<number>(100);
const meal = ref<MealType>(getCurrentMeal());
const time = ref(formatTime(new Date()));
const date = ref(dietStore.selectedDate || today());
const auth = useAuthStore();
const recentFoods = ref<RecentFood[]>([]);
const selectMode = ref(false);

let searchTimer: ReturnType<typeof setTimeout> | null = null;

onLoad((options: any) => {
  selectMode.value = options?.mode === 'select';
  const context = parseDietContext(options, { date: date.value, meal: meal.value, time: time.value });
  date.value = context.date;
  meal.value = context.meal;
  time.value = context.time;

  if (!auth.ready) {
    auth.bootstrap().then(() => {
      if (!auth.isLogged) {
        const redirect = appendSelectionMode(buildDietEntryUrl('/pages/diet/add', context), selectMode.value);
        requireAuth({ redirect });
      }
    });
  } else if (!auth.isLogged) {
    const redirect = appendSelectionMode(buildDietEntryUrl('/pages/diet/add', context), selectMode.value);
    requireAuth({ redirect });
  }
  loadRecentFoods();
});

async function loadRecentFoods() {
  if (!auth.ready) await auth.bootstrap();
  if (!auth.isLogged) return;
  const res = await dietApi.recentFoods().catch(() => ({ items: [] }));
  recentFoods.value = res.items || [];
}

function pickRecent(food: RecentFood) {
  pickFood(food);
  amount.value = Number(food.recent_amount) || (food.default_unit === 'serving' ? 1 : 100);
}

function getCurrentMeal(): MealType {
  const h = new Date().getHours();
  if (h < 10) return 'breakfast';
  if (h < 14) return 'lunch';
  if (h < 17) return 'snack';
  if (h < 21) return 'dinner';
  return 'snack';
}

function onSearchInput() {
  if (searchTimer) clearTimeout(searchTimer);
  searchTimer = setTimeout(() => {
    search();
  }, 300);
}

async function search() {
  if (searchTimer) { clearTimeout(searchTimer); searchTimer = null; }
  if (!keyword.value.trim()) {
    results.value = [];
    searched.value = false;
    searching.value = false;
    return;
  }
  searching.value = true;
  try {
    const res = await foodApi.search({ keyword: keyword.value.trim(), page_size: 50 });
    results.value = res.items || [];
    searched.value = true;
  } catch {
    results.value = [];
  } finally {
    searching.value = false;
  }
}

function clearSearch() {
  keyword.value = '';
  results.value = [];
  searched.value = false;
  searching.value = false;
}

function pickFood(f: FoodItem) {
  picked.value = f;
  unit.value = f.default_unit || 'g';
  amount.value = unit.value === 'serving' ? 1 : 100;
}

function setUnit(u: 'g' | 'serving') {
  unit.value = u;
  amount.value = u === 'serving' ? 1 : 100;
}

function cancelPick() {
  picked.value = null;
}

const previewCal = computed(() => {
  if (!picked.value) return 0;
  const r = calcNutrition(
    {
      calories_per_100g: picked.value.calories_per_100g,
      carbs_per_100g: picked.value.carbs_per_100g,
      protein_per_100g: picked.value.protein_per_100g,
      fat_per_100g: picked.value.fat_per_100g,
      serving_weight_g: picked.value.serving_weight_g,
    },
    { unit_type: unit.value, amount_g: amount.value, serving_count: amount.value },
  );
  return Math.round(r.calories);
});

const previewMacros = computed(() => {
  if (!picked.value) return { carbs: 0, protein: 0, fat: 0 };
  const r = calcNutrition(
    {
      calories_per_100g: picked.value.calories_per_100g,
      carbs_per_100g: picked.value.carbs_per_100g,
      protein_per_100g: picked.value.protein_per_100g,
      fat_per_100g: picked.value.fat_per_100g,
      serving_weight_g: picked.value.serving_weight_g,
    },
    { unit_type: unit.value, amount_g: amount.value, serving_count: amount.value },
  );
  return { carbs: r.carbs, protein: r.protein, fat: r.fat };
});

async function save() {
  if (!picked.value) return;
  if (!Number.isFinite(amount.value) || amount.value <= 0) {
    uni.showToast({ title: '请输入有效的数量', icon: 'none' });
    return;
  }
  if (selectMode.value) {
    const food = { ...picked.value };
    const pages = getCurrentPages();
    (pages[pages.length - 1] as any).getOpenerEventChannel().emit('foodSelected', food);
    safeNavigateBack('/pages/diet/photo-recognize');
    return;
  }
  uni.showLoading({ title: '保存中...' });
  try {
    await dietApi.create({
      record_date: date.value,
      record_time: time.value,
      meal_type: meal.value,
      food_source: picked.value.source,
      food_id: picked.value.source === 'system' ? picked.value.id : null,
      custom_food_id: picked.value.source === 'custom' ? picked.value.id : null,
      food_name_snapshot: picked.value.name,
      unit_type: unit.value,
      amount_g: unit.value === 'g' ? amount.value : null,
      serving_count: unit.value === 'serving' ? amount.value : null,
    });
    uni.showToast({ title: '已保存', icon: 'success' });
    setTimeout(() => safeNavigateBack('/pages/diet/index'), 600);
    dietStore.fetch();
  } catch (e: any) {
    uni.showToast({ title: e?.message || '保存失败', icon: 'none' });
  } finally {
    uni.hideLoading();
  }
}

function goCustom() {
  uni.navigateTo({
    url: buildDietEntryUrl('/pages/diet/custom-food', {
      date: date.value,
      meal: meal.value,
      time: time.value,
    }),
  });
}
</script>

<style lang="scss" scoped>
.add-page {
  background: $bg;
  padding: $gap-3;
}
.search-bar {
  margin-bottom: $gap-3;
}
.search-input {
  display: flex;
  align-items: center;
  background: $card;
  border-radius: $r-16;
  padding: 18rpx $gap-2;
  gap: $gap-1;
  box-shadow: $shadow-sm;
}
.search-icon-img {
  width: 32rpx;
  height: 32rpx;
  flex-shrink: 0;
  opacity: 0.7;
}
.input {
  flex: 1;
  font-size: $fs-md;
  color: $text-1;
}
.ph {
  color: $text-3;
}
.searching-tip {
  font-size: $fs-xs;
  color: $text-3;
  padding: 0 8rpx;
}
.clear {
  color: $text-3;
  padding: 4rpx 8rpx;
}

.result-list {
  margin-bottom: $gap-3;
}
.result-card {
  margin-bottom: 0;
  overflow: hidden;
}
.result-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: $gap-3;
  border-bottom: 1rpx solid $divider;
  &:last-child { border-bottom: none; }
}
.ri-info {
  flex: 1;
}
.ri-name {
  font-size: $fs-md;
  color: $text-1;
  font-weight: 500;
}
.ri-cat {
  font-size: $fs-xs;
  color: $text-3;
  margin-top: 4rpx;
}

.empty-block {
  margin-top: $gap-4;
}
.empty-actions {
  display: flex;
  gap: $gap-2;
  margin-top: $gap-3;
}

.picker-mask {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.4);
  display: flex;
  align-items: flex-end;
  z-index: 200;
}
.picker {
  width: 100%;
  background: $card;
  border-radius: $r-24 $r-24 0 0;
  padding: $gap-3;
  padding-bottom: calc(#{$gap-3} + env(safe-area-inset-bottom));
}
.picker-title {
  font-size: $fs-xl;
  font-weight: 600;
  color: $text-1;
}
.picker-cat {
  margin-top: 4rpx;
  font-size: $fs-sm;
  color: $text-3;
}

.seg {
  display: flex;
  gap: 12rpx;
  margin: $gap-3 0;
}

.form-row {
  display: flex;
  align-items: center;
  padding: $gap-2 0;
  border-bottom: 1rpx solid $divider;
  gap: $gap-2;
}
.form-label {
  width: 100rpx;
  color: $text-2;
  font-size: $fs-sm;
}
.form-input {
  flex: 1;
  font-size: $fs-md;
  color: $text-1;
  text-align: right;
}
.form-unit {
  color: $text-3;
  font-size: $fs-sm;
}
.meal-chips {
  flex: 1;
  display: flex;
  gap: 12rpx;
  justify-content: flex-end;
  flex-wrap: wrap;
}
.time-picker {
  flex: 1;
  text-align: right;
}
.time-text {
  font-size: $fs-md;
  color: $text-1;
}

.preview {
  margin-top: $gap-3;
  padding: $gap-3;
  background: $primary-tint;
  border-radius: $r-16;
  text-align: center;
}
.preview-num {
  font-size: 56rpx;
  font-weight: 700;
  color: $primary-deep;
}
.preview-macros {
  font-size: $fs-sm;
  color: $text-2;
  margin-top: 4rpx;
}

.picker-actions {
  display: flex;
  gap: $gap-2;
  align-items: center;
  margin-top: $gap-3;
  justify-content: flex-end;
}
</style>
