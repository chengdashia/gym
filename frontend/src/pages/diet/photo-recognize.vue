<template>
  <view class="photo-page">
    <view v-if="!imagePath" class="upload-block">
      <liquid-glass-card variant="light" :highlight="true" class="context-card">
        <view class="date-row">
          <text class="context-label">记录日期</text>
          <picker mode="date" :value="recordDate" @change="(e: any) => recordDate = e.detail.value">
            <text class="date-value">{{ recordDate }}</text>
          </picker>
        </view>
        <view class="meal-selector">
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
      </liquid-glass-card>

      <view class="camera-frame" @tap="chooseCamera">
        <view class="camera-icon">＋</view>
        <view class="camera-title">拍下你的食物</view>
        <view class="camera-desc">保持光线充足，让食物完整出现在画面中</view>
      </view>

      <view class="upload-actions">
        <liquid-glass-button variant="primary" size="lg" text="拍照识别" @tap="chooseCamera" />
        <liquid-glass-button variant="ghost" size="lg" text="从相册选择" @tap="chooseAlbum" />
      </view>
      <view class="privacy-note">图片仅用于本次食物识别，我们会妥善保护你的隐私</view>
    </view>

    <view v-else-if="recognizing" class="recognizing">
      <image :src="imagePath" mode="aspectFill" class="preview-img" />
      <view class="recognizing-box">
        <view class="loader" />
        <view class="recognizing-text">正在识别食物...</view>
      </view>
    </view>

    <view v-else class="candidates-block">
      <image :src="imagePath" mode="aspectFill" class="preview-img" />
      <liquid-glass-card :highlight="true" class="card">
        <view class="card-title">确认{{ mealTypes.find(m => m.value === meal)?.label }}食物</view>
        <view class="simulation-note">模拟识别结果：当前不来自真实图片分析，请核对食物和实际克数。</view>
        <view v-if="items.length === 0" class="empty-tip">
          未能识别出食物，你可以手动搜索添加
        </view>
        <view v-else class="cand-list">
          <view
            v-for="(item, index) in items"
            :key="`${item.source}-${item.food_id ?? item.custom_food_id}-${index}`"
            class="cand-item"
          >
            <view class="cand-info">
              <view class="cand-name">{{ item.name }}</view>
              <view class="cand-meta">{{ Math.round(item.confidence * 100) }}% 置信度</view>
              <view v-if="item.saveError" class="save-error">{{ item.saveError }}</view>
              <view v-if="item.detailError" class="save-error" @tap="retryDetail(index)">{{ item.detailError }}（点此重试）</view>
            </view>
            <input v-model.number="item.estimated_amount_g" type="digit" class="amount-input" />
            <text class="form-unit">g</text>
            <text class="remove-item" @tap="items.splice(index, 1)">删除</text>
            <text class="remove-item" @tap="goSearch(index)">替换</text>
          </view>
        </view>

        <view v-if="items.length" class="form-block">
          <view class="nutrition-summary">整餐：{{ summary.calories }} kcal · 碳水 {{ summary.carbs }}g · 蛋白质 {{ summary.protein }}g · 脂肪 {{ summary.fat }}g</view>
          <view class="form-row">
            <text class="form-label">日期</text>
            <picker mode="date" :value="recordDate" @change="(e: any) => recordDate = e.detail.value">
              <view class="form-input">{{ recordDate }}</view>
            </picker>
          </view>
          <view class="form-row">
            <text class="form-label">时间</text>
            <picker mode="time" :value="recordTime" @change="(e: any) => recordTime = e.detail.value">
              <view class="form-input">{{ recordTime }}</view>
            </picker>
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

          <view class="save-row">
            <label class="save-img" @tap="saveImage = !saveImage">
              <view :class="['checkbox', { checked: saveImage }]">{{ saveImage ? '✓' : '' }}</view>
              <text>保存食物图片到记录</text>
            </label>
          </view>
        </view>

        <view class="card-actions">
          <liquid-glass-button variant="ghost" size="md" :block="false" custom-style="flex:1;" text="重新选择" @tap="reset" />
          <liquid-glass-button v-if="items.length" variant="primary" size="md" :block="false" custom-style="flex:1;" :text="`保存到${mealTypes.find(m => m.value === meal)?.label}`" @tap="save" />
          <liquid-glass-button variant="ghost" size="md" :block="false" custom-style="flex:1;" text="添加食物" @tap="goSearch(null)" />
        </view>
      </liquid-glass-card>
    </view>
  </view>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue';
import { onLoad } from '@dcloudio/uni-app';
import { uploadApi } from '@/api/uploads';
import { aiApi } from '@/api/ai';
import { foodApi } from '@/api/food';
import { dietApi } from '@/api/diet';
import { useDietStore } from '@/store/diet';
import { useAuthStore } from '@/store/auth';
import { MEAL_TYPES, MealType } from '@/utils/constants';
import { formatTime, today } from '@/utils/date';
import { safeNavigateBack } from '@/utils/nav';
import { requireAuth } from '@/utils/auth-guard';
import { buildDietEntryUrl, parseDietContext } from '@/utils/diet-context';
import { appendSelectionMode, hasUnresolvedDetails, hydrateRecognizedItems, mergeSelectedFood, summarizeRecognizedMeal, type RecognizedMealItem } from '@/utils/recognized-meal';

const dietStore = useDietStore();
const mealTypes = MEAL_TYPES;
const auth = useAuthStore();

const imagePath = ref('');
const uploadedUrl = ref('');
const uploadedFileId = ref<number | null>(null);
const recognizing = ref(false);
const items = ref<RecognizedMealItem[]>([]);
const summary = computed(() => summarizeRecognizedMeal(items.value));
const meal = ref<MealType>('lunch');
const recordDate = ref(dietStore.selectedDate || today());
const recordTime = ref(formatTime(new Date()));
const saveImage = ref(true);

function getCurrentMeal(): MealType {
  const h = new Date().getHours();
  if (h < 10) return 'breakfast';
  if (h < 14) return 'lunch';
  if (h < 17) return 'snack';
  if (h < 21) return 'dinner';
  return 'snack';
}
meal.value = getCurrentMeal();

onLoad(async (options: any) => {
  const context = parseDietContext(options, {
    date: recordDate.value,
    meal: meal.value,
    time: recordTime.value,
  });
  recordDate.value = context.date;
  meal.value = context.meal;
  recordTime.value = context.time;

  if (!auth.ready) await auth.bootstrap();
  if (!auth.isLogged) {
    requireAuth({ redirect: buildDietEntryUrl('/pages/diet/photo-recognize', context) });
  }
});

function chooseCamera() {
  uni.chooseImage({
    count: 1,
    sourceType: ['camera'],
    success: (res) => handleImage(res.tempFilePaths[0]),
  });
}

function chooseAlbum() {
  uni.chooseImage({
    count: 1,
    sourceType: ['album'],
    success: (res) => handleImage(res.tempFilePaths[0]),
  });
}

async function handleImage(path: string) {
  imagePath.value = path;
  recognizing.value = true;
  try {
    const up = await uploadApi.image(path, 'food_recognition', true);
    uploadedFileId.value = up.file_id;
    uploadedUrl.value = up.file_url;
    const ai = await aiApi.recognizeFood({ file_id: up.file_id, image_url: up.file_url });
    items.value = await hydrateRecognizedItems(ai.recognized_items, foodApi.getDetail);
  } catch (e: any) {
    uni.showToast({ title: e?.message || '识别失败', icon: 'none' });
    items.value = [];
  } finally {
    recognizing.value = false;
  }
}

function reset() {
  imagePath.value = '';
  uploadedUrl.value = '';
  uploadedFileId.value = null;
  items.value = [];
}

function goSearch(replaceIndex: number | null) {
  uni.navigateTo({
    url: appendSelectionMode(buildDietEntryUrl('/pages/diet/add', {
      date: recordDate.value,
      meal: meal.value,
      time: recordTime.value,
    }), true),
    success: res => res.eventChannel.on('foodSelected', food => {
      items.value = mergeSelectedFood(items.value, food, replaceIndex);
    }),
  });
}

async function retryDetail(index: number) {
  const [item] = await hydrateRecognizedItems([items.value[index]], foodApi.getDetail);
  items.value.splice(index, 1, item);
}

async function save() {
  if (!items.value.length) return;
  if (hasUnresolvedDetails(items.value)) {
    uni.showToast({ title: '请先重试或替换营养详情加载失败的食物', icon: 'none' });
    return;
  }
  if (items.value.some(item => !Number.isFinite(item.estimated_amount_g) || item.estimated_amount_g <= 0)) {
    uni.showToast({ title: '请输入有效克数', icon: 'none' });
    return;
  }
  uni.showLoading({ title: '保存中...' });
  try {
    const failed: RecognizedMealItem[] = [];
    for (const item of items.value) {
      try {
        await dietApi.create({
          record_date: recordDate.value, record_time: recordTime.value, meal_type: meal.value,
          food_source: item.source,
          food_id: item.source === 'system' ? item.food_id : null,
          custom_food_id: item.source === 'custom' ? item.custom_food_id : null,
          food_name_snapshot: item.name, unit_type: 'g', amount_g: item.estimated_amount_g,
          image_url: saveImage.value ? uploadedUrl.value : null,
          image_file_id: uploadedFileId.value, save_image: saveImage.value,
        });
      } catch (e: any) {
        failed.push({ ...item, saveError: e?.message || '保存失败，请重试' });
      }
    }
    if (failed.length) {
      items.value = failed;
      uni.showToast({ title: `${failed.length} 项保存失败，草稿已保留`, icon: 'none' });
      return;
    }
    uni.showToast({ title: '已保存', icon: 'success' });
    setTimeout(() => safeNavigateBack('/pages/diet/index'), 600);
    dietStore.fetch();
  } finally {
    (uni.hideLoading as any)({ fail: () => {} });
  }
}
</script>

<style lang="scss" scoped>
.photo-page {
  background: $bg;
  padding: $gap-3;
  min-height: 100vh;
  box-sizing: border-box;
}
.upload-block {
  display: flex;
  flex-direction: column;
  gap: $gap-3;
  padding-bottom: calc(#{$gap-4} + env(safe-area-inset-bottom));
}
.context-card {
  margin-bottom: 0;
}
.date-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  min-height: 88rpx;
  border-bottom: 1rpx solid $divider;
}
.context-label {
  color: $text-2;
  font-size: $fs-md;
}
.date-value {
  color: $primary;
  font-size: $fs-md;
  font-weight: 600;
}
.meal-selector {
  display: flex;
  justify-content: space-between;
  gap: 8rpx;
  padding-top: $gap-2;
}
.camera-frame {
  min-height: 400rpx;
  border: 2rpx dashed rgba(91, 200, 154, 0.55);
  border-radius: $r-20;
  background: linear-gradient(145deg, rgba(255, 255, 255, 0.88), rgba(166, 227, 197, 0.2));
  box-shadow: $shadow-sm;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: $gap-3;
  box-sizing: border-box;
}
.camera-icon {
  width: 96rpx;
  height: 96rpx;
  border-radius: 50%;
  background: $primary-tint;
  color: $primary;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 56rpx;
  line-height: 1;
}
.camera-title {
  margin-top: $gap-2;
  color: $text-1;
  font-size: $fs-lg;
  font-weight: 600;
}
.camera-desc {
  margin-top: $gap-1;
  color: $text-3;
  font-size: $fs-sm;
  text-align: center;
}
.upload-actions {
  display: flex;
  flex-direction: column;
  gap: $gap-2;
}
.privacy-note {
  color: $text-3;
  font-size: $fs-xs;
  line-height: 1.6;
  text-align: center;
  padding: 0 $gap-2;
}

.preview-img {
  width: 100%;
  height: 480rpx;
  border-radius: $r-20;
  background: $bg-2;
}

.recognizing {
  position: relative;
}
.recognizing-box {
  position: absolute;
  inset: 0;
  background: rgba(0,0,0,0.4);
  border-radius: $r-20;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #fff;
}
.loader {
  width: 60rpx;
  height: 60rpx;
  border: 4rpx solid rgba(255,255,255,0.3);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}
.recognizing-text {
  margin-top: $gap-2;
  font-size: $fs-md;
}
@keyframes spin { to { transform: rotate(360deg); } }

.candidates-block {
  display: flex;
  flex-direction: column;
  gap: $gap-3;
}
.card {
  margin-bottom: 0;
}
.card-title {
  font-size: $fs-lg;
  font-weight: 600;
  color: $text-1;
  margin-bottom: $gap-2;
}
.empty-tip {
  color: $text-3;
  font-size: $fs-sm;
  padding: $gap-2 0;
}
.cand-list {
  display: flex;
  flex-direction: column;
  gap: 12rpx;
}
.cand-item {
  display: flex;
  align-items: center;
  padding: $gap-2;
  background: $bg-2;
  border-radius: $r-12;
  &.active {
    background: $primary-tint;
    border: 2rpx solid $primary;
  }
}
.amount-input {
  width: 110rpx;
  text-align: right;
  padding: 8rpx;
  background: #fff;
  border-radius: $r-8;
}
.remove-item, .save-error {
  color: $danger;
  font-size: $fs-xs;
}
.remove-item { margin-left: $gap-2; }
.nutrition-summary {
  color: $text-2;
  font-size: $fs-sm;
  line-height: 1.6;
  padding-bottom: $gap-2;
}
.cand-info {
  flex: 1;
}
.cand-name {
  font-size: $fs-md;
  color: $text-1;
  font-weight: 500;
}
.cand-meta {
  font-size: $fs-xs;
  color: $text-3;
  margin-top: 2rpx;
}
.check {
  width: 40rpx;
  height: 40rpx;
  border-radius: 50%;
  background: $primary;
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: $fs-md;
}

.form-block {
  margin-top: $gap-3;
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
  text-align: right;
  font-size: $fs-md;
}
.form-unit {
  color: $text-3;
  font-size: $fs-sm;
}
.meal-chips {
  flex: 1;
  display: flex;
  gap: 8rpx;
  justify-content: flex-end;
  flex-wrap: wrap;
}
.save-row {
  padding: $gap-2 0;
}
.save-img {
  display: flex;
  align-items: center;
  gap: $gap-2;
  font-size: $fs-sm;
  color: $text-2;
}
.checkbox {
  width: 32rpx;
  height: 32rpx;
  border-radius: 6rpx;
  border: 2rpx solid $primary;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  background: #fff;
  &.checked {
    background: $primary;
  }
}

.card-actions {
  display: flex;
  gap: $gap-2;
  margin-top: $gap-3;
}
</style>
