<template>
  <view class="reminders-page">
    <view class="head-card">
      <view class="head-emoji">🔔</view>
      <view class="head-text">每日提醒</view>
      <view class="head-sub">开启提醒后，会通过系统通知按时提示</view>
    </view>

    <view class="reminder-list">
      <view v-for="r in items" :key="r.reminder_type" class="reminder-card">
        <view class="rc-head">
          <view class="rc-icon" :style="iconStyle(r.reminder_type)">
            {{ iconText(r.reminder_type) }}
          </view>
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
      </view>
    </view>

    <view class="actions">
      <PrimaryButton text="保存设置" @tap="save" />
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue';
import PrimaryButton from '@/components/PrimaryButton.vue';
import { useUserStore } from '@/store/user';
import { ReminderItem } from '@/api/user';

const userStore = useUserStore();

const weekdayLabels = ['一', '二', '三', '四', '五', '六', '日'];

const items = ref<ReminderItem[]>([
  { reminder_type: 'diet', enabled: false, reminder_time: '08:30', weekdays: '1,2,3,4,5,6,7' },
  { reminder_type: 'training', enabled: false, reminder_time: '19:00', weekdays: '1,3,5' },
  { reminder_type: 'weight', enabled: false, reminder_time: '07:30', weekdays: '1,7' },
]);

onMounted(async () => {
  await userStore.fetchReminders().catch(() => {});
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
function iconText(t: string) {
  return { diet: '🥗', training: '🏋️', weight: '⚖️' }[t] || '🔔';
}
function iconStyle(t: string) {
  const colors: any = {
    diet: { background: '#EAF8F1', color: '#3FA67C' },
    training: { background: '#E0F0FA', color: '#2F6DA0' },
    weight: { background: '#FFF3DC', color: '#B86A1F' },
  };
  return colors[t] || {};
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
    uni.hideLoading();
    uni.showToast({ title: '已保存', icon: 'success' });
    setTimeout(() => uni.navigateBack(), 600);
  } catch (e: any) {
    uni.hideLoading();
    uni.showToast({ title: e?.message || '保存失败', icon: 'none' });
  }
}
</script>

<style lang="scss" scoped>
.reminders-page {
  min-height: 100vh;
  background: $bg;
  padding: $gap-3;
}
.head-card {
  background: $gradient-primary;
  border-radius: $r-24;
  padding: $gap-3;
  margin-bottom: $gap-3;
  text-align: center;
  color: #fff;
}
.head-emoji {
  font-size: 56rpx;
}
.head-text {
  margin-top: $gap-1;
  font-size: 28rpx;
  font-weight: 700;
}
.head-sub {
  margin-top: 4rpx;
  font-size: $fs-xs;
  opacity: 0.85;
}

.reminder-card {
  background: $card;
  border-radius: $r-20;
  padding: $gap-3;
  margin-bottom: $gap-2;
  box-shadow: $shadow-sm;
}
.rc-head {
  display: flex;
  align-items: center;
  gap: $gap-2;
}
.rc-icon {
  width: 72rpx;
  height: 72rpx;
  border-radius: $r-16;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 32rpx;
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