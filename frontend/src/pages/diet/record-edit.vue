<template>
  <view class="edit-page">
    <view v-if="loading" class="loading-skeleton">加载中...</view>
    <template v-else-if="record">
      <liquid-glass-card variant="light" :highlight="true" class="form-card">
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
            <liquid-glass-pill
              v-for="m in mealTypes"
              :key="m.value"
              :text="m.label"
              :variant="record.meal_type === m.value ? 'primary' : 'default'"
              size="sm"
              interactive
              :active="record.meal_type === m.value"
              @tap="record.meal_type = m.value as MealType"
            />
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
      </liquid-glass-card>

      <view class="actions">
        <liquid-glass-button variant="primary" text="保存修改" @tap="save" />
        <liquid-glass-button variant="danger" text="删除记录" @tap="confirmDelete" />
      </view>
    </template>

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
import { ref } from 'vue';
import { onLoad } from '@dcloudio/uni-app';
import ModalConfirm from '@/components/ModalConfirm.vue';
import { dietApi, DietRecord } from '@/api/diet';
import { useDietStore } from '@/store/diet';
import { useAuthStore } from '@/store/auth';
import { MEAL_TYPES, MealType } from '@/utils/constants';
import { safeNavigateBack } from '@/utils/nav';
import { requireAuth } from '@/utils/auth-guard';

const mealTypes = MEAL_TYPES;
const dietStore = useDietStore();

const id = ref(0);
const record = ref<DietRecord | null>(null);
const amountG = ref(0);
const amountS = ref(0);
const showDelete = ref(false);
const loading = ref(false);
const auth = useAuthStore();

onLoad((options: any) => {
  const recordId = Number(options?.id || 0);
  if (!auth.ready) {
    auth.bootstrap().then(() => {
      if (!auth.isLogged) {
        const redirect = recordId
          ? `/pages/diet/record-edit?id=${recordId}`
          : '/pages/diet/record-edit';
        requireAuth({ redirect });
      }
    });
  } else if (!auth.isLogged) {
    const redirect = recordId
      ? `/pages/diet/record-edit?id=${recordId}`
      : '/pages/diet/record-edit';
    requireAuth({ redirect });
  }

  id.value = recordId;
  load();
});

async function load() {
  if (!id.value) return;
  loading.value = true;
  try {
    const r = await dietApi.getRecord(id.value);
    record.value = r;
    amountG.value = r.amount_g || 0;
    amountS.value = r.serving_count || 0;
  } catch (e) {
    uni.showToast({ title: '加载失败', icon: 'none' });
    setTimeout(() => safeNavigateBack('/pages/diet/index'), 800);
  } finally {
    loading.value = false;
  }
}

async function save() {
  if (!record.value) return;
  const amount = record.value.unit_type === 'g' ? amountG.value : amountS.value;
  if (!Number.isFinite(amount) || amount <= 0) {
    uni.showToast({ title: '请输入有效数量', icon: 'none' });
    return;
  }
  uni.showLoading({ title: '保存中...' });
  try {
    await dietApi.update(record.value.id, {
      record_date: record.value.record_date,
      record_time: record.value.record_time,
      meal_type: record.value.meal_type,
      amount_g: record.value.unit_type === 'g' ? amountG.value : null,
      serving_count: record.value.unit_type === 'serving' ? amountS.value : null,
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

function confirmDelete() {
  showDelete.value = true;
}

async function remove() {
  showDelete.value = false;
  if (!record.value) return;
  uni.showLoading({ title: '删除中...' });
  try {
    await dietApi.remove(record.value.id);
    uni.showToast({ title: '已删除', icon: 'success' });
    setTimeout(() => safeNavigateBack('/pages/diet/index'), 600);
    dietStore.fetch();
  } catch (e: any) {
    uni.showToast({ title: e?.message || '删除失败', icon: 'none' });
  } finally {
    uni.hideLoading();
  }
}
</script>

<style lang="scss" scoped>
.edit-page {
  background: $bg;
  padding: $gap-3;
}
.loading-skeleton {
  padding: $gap-5 $gap-3;
  text-align: center;
  color: $text-3;
  font-size: $fs-md;
}
.form-card {
  margin-bottom: 0;
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
</style>
