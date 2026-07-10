<template>
  <view class="reminders-page">
    <liquid-glass-card variant="tint" :highlight="true" custom-style="margin-bottom:0">
      <view class="head-content">
        <line-icon name="bell" tint="warm" :size="96" class="head-icon" />
        <view class="head-text">每日提醒</view>
        <view class="head-sub">开启提醒后，会通过系统通知按时提示</view>
      </view>
    </liquid-glass-card>

    <view class="reminder-list">
      <liquid-glass-card
        v-for="r in items"
        :key="r.reminder_type"
        variant="light"
        :highlight="true"
        custom-style="margin-top:16rpx;margin-bottom:0"
      >
        <view class="rc-head">
          <line-icon :name="reminderIcon(r.reminder_type).icon" :tint="reminderIcon(r.reminder_type).tint" :size="64" class="rc-icon" />
          <view class="rc-info">
            <view class="rc-name">{{ typeLabel(r.reminder_type) }}</view>
            <view class="rc-desc">{{ typeDesc(r.reminder_type) }}</view>
          </view>
          <switch
            :checked="r.enabled"
            @change="(e: any) => toggle(r.reminder_type, e.detail.value)"
            color="#5BC89A"
          />
        </view>

        <view v-if="r.enabled" class="rc-body">
          <view class="rc-row">
            <text class="rc-label">提醒时间</text>
            <picker mode="time" :value="r.reminder_time" @change="(e: any) => update(r.reminder_type, { reminder_time: e.detail.value })">
              <text class="rc-value">{{ r.reminder_time }}</text>
            </picker>
          </view>
          <view class="rc-row column">
            <text class="rc-label">重复</text>
            <view class="weekday-list">
              <view
                v-for="(d, i) in weekdayLabels"
                :key="i"
                :class="['wd', { active: r.weekdays.includes(String(i + 1)) }]"
                @tap="toggleWeekday(r.reminder_type, i + 1)"
              >{{ d }}</view>
            </view>
          </view>
        </view>
      </liquid-glass-card>
    </view>

    <view class="actions">
      <liquid-glass-button text="保存设置" variant="primary" @tap="save" />
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import LiquidGlassCard from '@/components/LiquidGlassCard.vue';
import LiquidGlassButton from '@/components/LiquidGlassButton.vue';
import { useUserStore } from '@/store/user';
import { useAuthStore } from '@/store/auth';
import { safeNavigateBack } from '@/utils/nav';
import { requireAuth } from '@/utils/auth-guard';
import { ReminderItem } from '@/api/user';

const userStore = useUserStore();
const auth = useAuthStore();

const weekdayLabels = ['一', '二', '三', '四', '五', '六', '日'];

const items = ref<ReminderItem[]>([
  { reminder_type: 'diet', enabled: false, reminder_time: '08:30', weekdays: '1,2,3,4,5,6,7' },
  { reminder_type: 'training', enabled: false, reminder_time: '19:00', weekdays: '1,3,5' },
  { reminder_type: 'weight', enabled: false, reminder_time: '07:30', weekdays: '1,7' },
]);

onMounted(async () => {
  if (!auth.ready) await auth.bootstrap();
  if (!auth.isLogged) {
    requireAuth({ redirect: '/pages/mine/reminders' });
    return;
  }
  await userStore.fetchReminders().catch(() => {
    uni.showToast({ title: '加载失败', icon: 'none' });
  });
  if (userStore.reminders?.length) {
    items.value = items.value.map((it) => {
      const found = userStore.reminders.find((r) => r.reminder_type === it.reminder_type);
      return found || it;
    });
  }
});

function typeLabel(t: string) {
  return { diet: '饮食提醒', training: '训练提醒', weight: '体重提醒' }[t] || t;
}
function typeDesc(t: string) {
  return { diet: '按时记录每餐', training: '不要错过训练日', weight: '记得记录体重' }[t] || '';
}
function reminderIcon(t: string): { icon: string; tint: 'mint' | 'warm' | 'sky' | 'violet' | 'rose' | 'neutral' } {
  const icons = {
    diet: { icon: 'bento', tint: 'mint' },
    training: { icon: 'dumbbell', tint: 'warm' },
    weight: { icon: 'scale', tint: 'sky' },
  } as const;
  return icons[t as keyof typeof icons] || { icon: 'bell', tint: 'neutral' };
}

function toggle(type: string, val: boolean) {
  const it = items.value.find((r) => r.reminder_type === type);
  if (it) it.enabled = val;
}

function update(type: string, patch: Partial<ReminderItem>) {
  const it = items.value.find((r) => r.reminder_type === type);
  if (it) Object.assign(it, patch);
}

function toggleWeekday(type: string, day: number) {
  const it = items.value.find((r) => r.reminder_type === type);
  if (!it) return;
  const list = it.weekdays.split(',').filter(Boolean);
  const idx = list.indexOf(String(day));
  if (idx >= 0) list.splice(idx, 1);
  else list.push(String(day));
  list.sort((a, b) => Number(a) - Number(b));
  it.weekdays = list.join(',') || '1,2,3,4,5,6,7';
}

async function save() {
  uni.showLoading({ title: '保存中...' });
  try {
    await userStore.updateReminders(items.value);
    uni.showToast({ title: '已保存', icon: 'success' });
    setTimeout(() => safeNavigateBack('/pages/mine/index'), 600);
  } catch (e: any) {
    uni.showToast({ title: e?.message || '保存失败', icon: 'none' });
  } finally {
    uni.hideLoading();
  }
}
</script>

<style lang="scss" scoped>
.reminders-page {
  background: $bg;
  padding: $gap-3;
}
.head-content {
  text-align: center;
}
.head-icon {
  margin: 0 auto $gap-2;
}
.head-text {
  margin-top: $gap-1;
  font-size: 28rpx;
  font-weight: 700;
  color: $primary-deep;
}
.head-sub {
  margin-top: 4rpx;
  font-size: $fs-xs;
  color: $text-2;
  opacity: 0.85;
}

.reminder-list {
  margin-top: $gap-3;
}
.rc-head {
  display: flex;
  align-items: center;
  gap: $gap-2;
}
.rc-icon {
  flex-shrink: 0;
}
.rc-info {
  flex: 1;
}
.rc-name {
  font-size: $fs-md;
  font-weight: 600;
  color: $text-1;
}
.rc-desc {
  font-size: $fs-xs;
  color: $text-3;
  margin-top: 2rpx;
}
.rc-body {
  margin-top: $gap-2;
  padding-top: $gap-2;
  border-top: 1rpx solid $divider;
}
.rc-row {
  display: flex;
  align-items: center;
  padding: $gap-1 0;
  gap: $gap-2;
  &.column {
    flex-direction: column;
    align-items: stretch;
  }
}
.rc-label {
  color: $text-2;
  font-size: $fs-sm;
  width: 120rpx;
}
.rc-value {
  flex: 1;
  text-align: right;
  font-size: $fs-md;
  color: $primary;
}
.weekday-list {
  display: flex;
  gap: 12rpx;
  margin-top: $gap-1;
}
.wd {
  width: 64rpx;
  height: 64rpx;
  border-radius: 50%;
  background: $bg-2;
  color: $text-2;
  font-size: $fs-sm;
  display: flex;
  align-items: center;
  justify-content: center;
  &.active {
    background: $primary;
    color: #fff;
  }
}
.actions {
  margin-top: $gap-4;
}
</style>
