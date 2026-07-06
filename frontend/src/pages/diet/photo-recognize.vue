<template>
  <view class="photo-page">
    <view v-if="!imagePath" class="upload-block">
      <EmptyState emoji="📷" title="拍照识别食物" desc="支持拍照或从相册选择">
        <view class="upload-actions">
          <view class="up-btn" @tap="chooseCamera">📸 拍照</view>
          <view class="up-btn ghost" @tap="chooseAlbum">🖼️ 相册</view>
        </view>
      </EmptyState>
    </view>

    <view v-else-if="recognizing" class="recognizing">
      <image :src="imagePath" mode="aspectFill" class="preview-img" />
      <view class="recognizing-box">
        <view class="loader" />
        <view class="recognizing-text">正在识别食物...</view>
      </view>
    </view>

    <view v-else-if="!picked" class="candidates-block">
      <image :src="imagePath" mode="aspectFill" class="preview-img" />
      <view class="card">
        <view class="card-title">识别结果</view>
        <view v-if="candidates.length === 0" class="empty-tip">
          未能识别出食物，你可以手动搜索添加
        </view>
        <view v-else class="cand-list">
          <view
            v-for="c in candidates"
            :key="`${c.source}-${c.food_id}`"
            :class="['cand-item', { active: selectedCandidate === c }]"
            @tap="selectedCandidate = c"
          >
            <view class="cand-info">
              <view class="cand-name">{{ c.name }}</view>
              <view class="cand-meta">{{ Math.round(c.confidence * 100) }}% 置信度</view>
            </view>
            <view v-if="selectedCandidate === c" class="check">✓</view>
          </view>
        </view>

        <view v-if="selectedCandidate" class="form-block">
          <view class="form-row">
            <text class="form-label">克数</text>
            <input v-model.number="amount" type="digit" class="form-input" placeholder="克数" />
            <text class="form-unit">g</text>
          </view>
          <view class="form-row">
            <text class="form-label">餐次</text>
            <view class="meal-chips">
              <view
                v-for="m in mealTypes"
                :key="m.value"
                :class="['chip', { active: meal === m.value }]"
                @tap="meal = m.value as MealType"
              >{{ m.label }}</view>
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
          <view class="ghost" @tap="reset">重新选择</view>
          <view v-if="selectedCandidate" class="primary" @tap="save">保存记录</view>
          <view v-else class="primary" @tap="goSearch">搜索添加</view>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import EmptyState from '@/components/EmptyState.vue';
import { uploadApi } from '@/api/uploads';
import { aiApi, RecognitionCandidate } from '@/api/ai';
import { foodApi } from '@/api/food';
import { dietApi } from '@/api/diet';
import { useDietStore } from '@/store/diet';
import { MEAL_TYPES, MealType } from '@/utils/constants';
import { formatTime, today } from '@/utils/date';

const dietStore = useDietStore();
const mealTypes = MEAL_TYPES;

const imagePath = ref('');
const uploadedUrl = ref('');
const recognizing = ref(false);
const candidates = ref<RecognitionCandidate[]>([]);
const selectedCandidate = ref<RecognitionCandidate | null>(null);
const amount = ref(100);
const meal = ref<MealType>('lunch');
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
    uploadedUrl.value = up.file_url;
    const ai = await aiApi.recognizeFood({ file_id: up.file_id, image_url: up.file_url });
    candidates.value = ai.candidates || [];
  } catch (e: any) {
    uni.showToast({ title: e?.message || '识别失败', icon: 'none' });
    candidates.value = [];
  } finally {
    recognizing.value = false;
  }
}

function reset() {
  imagePath.value = '';
  uploadedUrl.value = '';
  candidates.value = [];
  selectedCandidate.value = null;
  amount.value = 100;
}

function goSearch() {
  uni.navigateTo({ url: `/pages/diet/add?date=${dietStore.selectedDate || today()}` });
}

async function save() {
  if (!selectedCandidate.value) return;
  const c = selectedCandidate.value;
  uni.showLoading({ title: '保存中...' });
  try {
    let food: any = null;
    try {
      food = await foodApi.getDetail(c.food_id, c.source);
    } catch {
      food = null;
    }
    await dietApi.create({
      record_date: dietStore.selectedDate || today(),
      record_time: formatTime(new Date()),
      meal_type: meal.value,
      food_source: c.source,
      food_id: c.source === 'system' ? c.food_id : null,
      custom_food_id: c.source === 'custom' ? c.food_id : null,
      food_name_snapshot: food?.name || c.name,
      unit_type: 'g',
      amount_g: amount.value,
      image_url: saveImage.value ? uploadedUrl.value : null,
      save_image: saveImage.value,
    });
    uni.hideLoading();
    uni.showToast({ title: '已保存', icon: 'success' });
    setTimeout(() => uni.navigateBack(), 600);
    dietStore.fetch();
  } catch (e: any) {
    uni.hideLoading();
    uni.showToast({ title: e?.message || '保存失败', icon: 'none' });
  }
}
</script>

<style lang="scss" scoped>
.photo-page {
  min-height: 100vh;
  background: $bg;
  padding: $gap-3;
}
.upload-block {
  padding-top: $gap-5;
}
.upload-actions {
  display: flex;
  gap: $gap-2;
  margin-top: $gap-3;
}
.up-btn {
  padding: 18rpx 36rpx;
  background: $primary;
  color: #fff;
  border-radius: $r-pill;
  font-size: $fs-md;
  &.ghost {
    background: $bg-2;
    color: $text-2;
  }
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
  background: $card;
  border-radius: $r-20;
  padding: $gap-3;
  box-shadow: $shadow-sm;
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
.chip {
  padding: 6rpx 16rpx;
  border-radius: $r-pill;
  background: $bg-2;
  font-size: $fs-xs;
  color: $text-2;
  &.active {
    background: $primary;
    color: #fff;
  }
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
.ghost, .primary {
  flex: 1;
  text-align: center;
  padding: 20rpx;
  border-radius: $r-16;
  font-size: $fs-md;
}
.ghost {
  background: $bg-2;
  color: $text-2;
}
.primary {
  background: $primary;
  color: #fff;
  font-weight: 500;
}
</style>