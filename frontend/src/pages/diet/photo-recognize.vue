<template>
  <view class="photo-page">
    <view v-if="!imagePath" class="upload-block">
      <EmptyState icon="camera" tint="sky" title="拍照识别食物" desc="支持拍照或从相册选择">
        <view class="upload-actions">
          <liquid-glass-button variant="primary" size="md" :block="false" text="拍照" @tap="chooseCamera" />
          <liquid-glass-button variant="ghost" size="md" :block="false" text="相册" @tap="chooseAlbum" />
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

    <view v-else class="candidates-block">
      <image :src="imagePath" mode="aspectFill" class="preview-img" />
      <liquid-glass-card :highlight="true" class="card">
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
          <liquid-glass-button v-if="selectedCandidate" variant="primary" size="md" :block="false" custom-style="flex:1;" text="保存记录" @tap="save" />
          <liquid-glass-button v-else variant="primary" size="md" :block="false" custom-style="flex:1;" text="搜索添加" @tap="goSearch" />
        </view>
      </liquid-glass-card>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import EmptyState from '@/components/EmptyState.vue';
import { uploadApi } from '@/api/uploads';
import { aiApi, RecognitionCandidate } from '@/api/ai';
import { foodApi } from '@/api/food';
import { dietApi } from '@/api/diet';
import { useDietStore } from '@/store/diet';
import { useAuthStore } from '@/store/auth';
import { MEAL_TYPES, MealType } from '@/utils/constants';
import { formatTime, today } from '@/utils/date';
import { safeNavigateBack } from '@/utils/nav';
import { requireAuth } from '@/utils/auth-guard';

const dietStore = useDietStore();
const mealTypes = MEAL_TYPES;
const auth = useAuthStore();

onMounted(async () => {
  if (!auth.ready) await auth.bootstrap();
  if (!auth.isLogged) {
    requireAuth({ redirect: '/pages/diet/photo-recognize' });
  }
});

const imagePath = ref('');
const uploadedUrl = ref('');
const uploadedFileId = ref<number | null>(null);
const recognizing = ref(false);
const candidates = ref<RecognitionCandidate[]>([]);
const selectedCandidate = ref<RecognitionCandidate | null>(null);
const amount = ref(100);
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
  uploadedFileId.value = null;
  candidates.value = [];
  selectedCandidate.value = null;
  amount.value = 100;
}

function goSearch() {
  uni.navigateTo({ url: `/pages/diet/add?date=${dietStore.selectedDate || today()}` });
}

async function save() {
  if (!selectedCandidate.value) return;
  if (!Number.isFinite(amount.value) || amount.value <= 0) {
    uni.showToast({ title: '请输入有效克数', icon: 'none' });
    return;
  }
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
      record_date: recordDate.value,
      record_time: recordTime.value,
      meal_type: meal.value,
      food_source: c.source,
      food_id: c.source === 'system' ? c.food_id : null,
      custom_food_id: c.source === 'custom' ? c.food_id : null,
      food_name_snapshot: food?.name || c.name,
      unit_type: 'g',
      amount_g: amount.value,
      image_url: saveImage.value ? uploadedUrl.value : null,
      image_file_id: uploadedFileId.value,
      save_image: saveImage.value,
    });
    uni.hideLoading();
    uni.showToast({ title: '已保存', icon: 'success' });
    setTimeout(() => safeNavigateBack('/pages/diet/index'), 600);
    dietStore.fetch();
  } catch (e: any) {
    uni.hideLoading();
    uni.showToast({ title: e?.message || '保存失败', icon: 'none' });
  }
}
</script>

<style lang="scss" scoped>
.photo-page {
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
  justify-content: center;
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
