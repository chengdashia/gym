<template>
  <view class="custom-food">
    <liquid-glass-card variant="light" :highlight="true" class="form-card">
      <view class="form-row">
        <text class="form-label">食物名称</text>
        <input v-model="form.name" placeholder="例如：自制鸡胸饭" class="form-input" />
      </view>
      <view class="form-row">
        <text class="form-label">分类</text>
        <view class="cat-chips">
          <liquid-glass-pill
            v-for="c in categories"
            :key="c"
            :text="c"
            :variant="form.category === c ? 'primary' : 'default'"
            size="sm"
            interactive
            :active="form.category === c"
            @tap="form.category = c"
          />
        </view>
      </view>

      <view class="divider" />

      <view class="hint">每 100g 营养数据</view>
      <view class="form-row">
        <text class="form-label">热量 (kcal)</text>
        <input v-model.number="form.calories_per_100g" type="digit" placeholder="0" class="form-input" />
      </view>
      <view class="form-row">
        <text class="form-label">碳水 (g)</text>
        <input v-model.number="form.carbs_per_100g" type="digit" placeholder="0" class="form-input" />
      </view>
      <view class="form-row">
        <text class="form-label">蛋白质 (g)</text>
        <input v-model.number="form.protein_per_100g" type="digit" placeholder="0" class="form-input" />
      </view>
      <view class="form-row">
        <text class="form-label">脂肪 (g)</text>
        <input v-model.number="form.fat_per_100g" type="digit" placeholder="0" class="form-input" />
      </view>

      <view class="form-row">
        <text class="form-label">单份重量</text>
        <input v-model.number="form.serving_weight_g" type="digit" placeholder="可选，例 200" class="form-input" />
        <text class="form-unit">g</text>
      </view>
    </liquid-glass-card>

    <view class="action-bar">
      <liquid-glass-button variant="primary" text="保存食物" @tap="save" />
    </view>
  </view>
</template>

<script setup lang="ts">
import { reactive, onMounted } from 'vue';
import { foodApi } from '@/api/food';
import { useAuthStore } from '@/store/auth';
import { FOOD_CATEGORIES } from '@/utils/constants';
import { safeNavigateBack } from '@/utils/nav';
import { requireAuth } from '@/utils/auth-guard';

const categories = FOOD_CATEGORIES;
const auth = useAuthStore();

onMounted(async () => {
  if (!auth.ready) await auth.bootstrap();
  if (!auth.isLogged) {
    requireAuth({ redirect: '/pages/diet/custom-food' });
  }
});

const form = reactive({
  name: '',
  category: '其他',
  calories_per_100g: 0,
  carbs_per_100g: 0,
  protein_per_100g: 0,
  fat_per_100g: 0,
  serving_weight_g: undefined as number | undefined,
});

async function save() {
  if (!form.name.trim()) {
    uni.showToast({ title: '请输入食物名称', icon: 'none' });
    return;
  }
  const nums = [form.calories_per_100g, form.carbs_per_100g, form.protein_per_100g, form.fat_per_100g];
  if (nums.some(n => !Number.isFinite(n) || n < 0)) {
    uni.showToast({ title: '营养值需为非负数字', icon: 'none' });
    return;
  }
  uni.showLoading({ title: '保存中...' });
  try {
    await foodApi.createCustom({
      name: form.name.trim(),
      category: form.category,
      calories_per_100g: form.calories_per_100g,
      carbs_per_100g: form.carbs_per_100g,
      protein_per_100g: form.protein_per_100g,
      fat_per_100g: form.fat_per_100g,
      default_unit: 'g',
      serving_weight_g: form.serving_weight_g || null,
    });
    uni.hideLoading();
    uni.showToast({ title: '已保存', icon: 'success' });
    setTimeout(() => safeNavigateBack('/pages/diet/index'), 600);
  } catch (e: any) {
    uni.hideLoading();
    uni.showToast({ title: e?.message || '保存失败', icon: 'none' });
  }
}
</script>

<style lang="scss" scoped>
.custom-food {
  background: $bg;
  padding: $gap-3;
}
.form-card {
  margin-bottom: 0;
}
.form-row {
  display: flex;
  align-items: center;
  padding: $gap-2 0;
  border-bottom: 1rpx solid $divider;
  gap: $gap-2;
  &:last-child { border-bottom: none; }
}
.form-label {
  width: 200rpx;
  color: $text-2;
  font-size: $fs-md;
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
.cat-chips {
  flex: 1;
  display: flex;
  flex-wrap: wrap;
  gap: 12rpx;
  justify-content: flex-end;
}
.divider {
  height: 1rpx;
  background: $divider;
  margin: $gap-2 0;
}
.hint {
  font-size: $fs-sm;
  color: $text-3;
  padding: $gap-1 0;
}
.action-bar {
  margin-top: $gap-4;
}
</style>
