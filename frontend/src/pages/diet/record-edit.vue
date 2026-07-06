<template>
  <view v-if="record" class="edit-page">
    <view class="form-card">
      <view class="row">
        <text class="label">食物</text>
        <text class="value">{{ record.food_name_snapshot }}</text>
      </view>
      <view class="row">
        <text class="label">日期</text>
        <picker mode="date" :value="record.record_date" @change="(e: any) => record.record_date = e.detail.value">
          <text class="value">{{ record.record_date }}</text>
        </picker>
      </view>
      <view class="row">
        <text class="label">时间</text>
        <picker mode="time" :value="record.record_time" @change="(e: any) => record.record_time = e.detail.value">
          <text class="value">{{ record.record_time }}</text>
        </picker>
      </view>

      <view class="row">
        <text class="label">餐次</text>
        <view class="meal-chips">
          <view
            v-for="m in mealTypes"
            :key="m.value"
            :class="['chip', { active: record.meal_type === m.value }]"
            @tap="record.meal_type = m.value as MealType"
          >{{ m.label }}</view>
        </view>
      </view>

      <view v-if="record.unit_type === 'g'" class="row">
        <text class="label">克数</text>
        <input v-model.number="amountG" type="digit" class="form-input" />
        <text class="unit">g</text>
      </view>
      <view v-else class="row">
        <text class="label">份数</text>
        <input v-model.number="amountS" type="digit" class="form-input" />
        <text class="unit">份</text>
      </view>

      <view class="row preview">
        <text class="label">预览</text>
        <view class="preview-info">
          <text class="cal">{{ Math.round(record.calories_kcal) }} kcal</text>
          <text class="macros">C{{ record.carbs_g }} · P{{ record.protein_g }} · F{{ record.fat_g }}</text>
        </view>
      </view>
    </view>

    <view class="actions">
      <PrimaryButton text="保存修改" @tap="save" />
      <view class="btn-danger" @tap="confirmDelete">删除记录</view>
    </view>

    <ModalConfirm
      :visible="showDelete"
      title="删除记录"
      message="确定要删除这条饮食记录吗？删除后无法恢复。"
      confirm-text="删除"
      danger
      @confirm="remove"
      @cancel="showDelete = false"
    />
  </view>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import PrimaryButton from '@/components/PrimaryButton.vue';
import ModalConfirm from '@/components/ModalConfirm.vue';
import { dietApi, DietRecord } from '@/api/diet';
import { useDietStore } from '@/store/diet';
import { MEAL_TYPES, MealType } from '@/utils/constants';

const mealTypes = MEAL_TYPES;
const dietStore = useDietStore();

const id = ref(0);
const record = ref<DietRecord | null>(null);
const amountG = ref(0);
const amountS = ref(0);
const showDelete = ref(false);

onMounted(() => {
  const pages = getCurrentPages();
  const cur = pages[pages.length - 1] as any;
  const opt = cur?.options || {};
  id.value = Number(opt.id || 0);
  load();
});

async function load() {
  if (!id.value) return;
  try {
    const list = await dietApi.list(dietStore.selectedDate);
    const found = [
      ...(list.meals.breakfast || []),
      ...(list.meals.lunch || []),
      ...(list.meals.dinner || []),
      ...(list.meals.snack || []),
    ].find((r) => r.id === id.value);
    if (found) {
      record.value = found;
      amountG.value = found.amount_g || 0;
      amountS.value = found.serving_count || 0;
    }
  } catch (e) {}
}

async function save() {
  if (!record.value) return;
  uni.showLoading({ title: '保存中...' });
  try {
    await dietApi.update(record.value.id, {
      record_date: record.value.record_date,
      record_time: record.value.record_time,
      meal_type: record.value.meal_type,
      amount_g: record.value.unit_type === 'g' ? amountG.value : null,
      serving_count: record.value.unit_type === 'serving' ? amountS.value : null,
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

function confirmDelete() {
  showDelete.value = true;
}

async function remove() {
  showDelete.value = false;
  if (!record.value) return;
  uni.showLoading({ title: '删除中...' });
  try {
    await dietApi.remove(record.value.id);
    uni.hideLoading();
    uni.showToast({ title: '已删除', icon: 'success' });
    setTimeout(() => uni.navigateBack(), 600);
    dietStore.fetch();
  } catch (e: any) {
    uni.hideLoading();
    uni.showToast({ title: e?.message || '删除失败', icon: 'none' });
  }
}
</script>

<style lang="scss" scoped>
.edit-page {
  min-height: 100vh;
  background: $bg;
  padding: $gap-3;
}
.form-card {
  background: $card;
  border-radius: $r-20;
  padding: $gap-3;
  box-shadow: $shadow-sm;
}
.row {
  display: flex;
  align-items: center;
  padding: $gap-2 0;
  border-bottom: 1rpx solid $divider;
  gap: $gap-2;
  &:last-child { border-bottom: none; }
  &.preview {
    background: $primary-tint;
    border-radius: $r-12;
    padding: $gap-2;
    margin-top: $gap-2;
    border-bottom: none;
  }
}
.label {
  width: 120rpx;
  color: $text-2;
  font-size: $fs-sm;
}
.value {
  flex: 1;
  text-align: right;
  font-size: $fs-md;
  color: $text-1;
}
.form-input {
  flex: 1;
  text-align: right;
  font-size: $fs-md;
}
.unit {
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
.preview-info {
  flex: 1;
  text-align: right;
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 2rpx;
}
.cal {
  font-size: $fs-lg;
  font-weight: 600;
  color: $primary-deep;
}
.macros {
  font-size: $fs-xs;
  color: $text-2;
}

.actions {
  margin-top: $gap-4;
  display: flex;
  flex-direction: column;
  gap: $gap-2;
}
.btn-danger {
  text-align: center;
  padding: 24rpx;
  background: #FFE2E2;
  border-radius: $r-16;
  color: $danger;
  font-size: $fs-md;
  font-weight: 500;
}
</style>