<template>
  <view class="agreement-page">
    <view class="title">{{ title }}</view>
    <view class="meta">版本：v1.0 · 最后更新：2026-07-06</view>

    <liquid-glass-card variant="light" :highlight="true" custom-style="margin-top:24rpx;margin-bottom:0">
      <view v-for="(s, i) in sections" :key="i" class="section">
        <view class="s-title">{{ i + 1 }}. {{ s.title }}</view>
        <view v-for="(p, j) in s.paragraphs" :key="j" class="p">{{ p }}</view>
      </view>
    </liquid-glass-card>

    <view class="footer">本协议最终解释权归健身饮食小程序所有</view>
  </view>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import LiquidGlassCard from '@/components/LiquidGlassCard.vue';

const type = ref<'agreement' | 'privacy'>('agreement');

const userAgreement = [
  {
    title: '服务说明',
    paragraphs: [
      '欢迎使用健身饮食小程序。本小程序提供饮食记录、训练计划、体重管理、数据统计等功能，旨在帮助你建立良好的健康管理习惯。',
      '小程序通过微信登录识别用户身份，数据存储在你授权的后端服务中。',
    ],
  },
  {
    title: '用户行为规范',
    paragraphs: [
      '你应使用真实有效的身体数据，以便获得合理的营养目标推荐。',
      '请勿录入明显异常的饮食或训练数据，这会影响统计结果的准确性。',
      '请勿将本服务用于任何商业用途或违法活动。',
    ],
  },
  {
    title: '数据使用',
    paragraphs: [
      '你的饮食、训练、体重等个人数据仅用于提供核心功能展示与统计。',
      '我们不会将你的个人健康数据用于精准营销或对外出售。',
      '你可以随时查看、编辑或删除你的个人数据。',
    ],
  },
  {
    title: '免责声明',
    paragraphs: [
      '本小程序提供的营养目标、训练容量等数据仅供参考，不构成医疗建议。',
      '如有慢性疾病、孕期或特殊情况，请咨询专业医生或营养师。',
      '使用本服务进行健身或饮食调整，风险由你自行承担。',
    ],
  },
];

const privacy = [
  {
    title: '我们收集的信息',
    paragraphs: [
      '微信登录：用于识别用户身份（openid、unionid）。',
      '基础资料：昵称、头像、性别、年龄、身高、体重等身体数据。',
      '饮食与训练记录：你主动录入的饮食记录、训练记录、体重记录。',
      '图片（可选）：你拍照上传用于食物识别的图片，可选择是否保存。',
    ],
  },
  {
    title: '信息的使用',
    paragraphs: [
      '用于生成首页摘要、统计图表、个性化提醒等核心功能。',
      '用于在你授权的设备上展示历史数据。',
      '我们不会将以上信息用于精准广告投放。',
    ],
  },
  {
    title: '信息共享',
    paragraphs: [
      '我们不会主动与第三方共享你的个人健康数据。',
      '根据法律法规要求或维护公共利益时，可能依法披露必要信息。',
    ],
  },
  {
    title: '你的权利',
    paragraphs: [
      '你可以在「我的-账号与数据」中随时删除个人数据或注销账号。',
      '注销账号后，你的个人数据将被立即清除（系统基础食物/动作库不受影响）。',
    ],
  },
];

const sections = computed(() => (type.value === 'privacy' ? privacy : userAgreement));
const title = computed(() => (type.value === 'privacy' ? '隐私政策' : '用户协议'));

onMounted(() => {
  const pages = getCurrentPages();
  const opt = (pages[pages.length - 1] as any)?.options || {};
  type.value = (opt.type as any) || 'agreement';
  uni.setNavigationBarTitle({ title: title.value });
});
</script>

<style lang="scss" scoped>
.agreement-page {
  background: $bg;
  padding: $gap-3;
}
.title {
  font-size: 40rpx;
  font-weight: 700;
  color: $text-1;
}
.meta {
  margin-top: 4rpx;
  font-size: $fs-sm;
  color: $text-3;
}
.section {
  margin-bottom: $gap-3;
  &:last-child { margin-bottom: 0; }
}
.s-title {
  font-size: $fs-md;
  font-weight: 600;
  color: $text-1;
  margin-bottom: $gap-1;
}
.p {
  font-size: $fs-sm;
  color: $text-2;
  line-height: 1.7;
  margin-bottom: $gap-1;
}
.footer {
  text-align: center;
  color: $text-3;
  font-size: $fs-xs;
  padding: $gap-3 0;
}
</style>
