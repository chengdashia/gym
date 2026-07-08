// 全局基础配置
export const API_BASE = 'http://127.0.0.1:8000/api/v1';

export const APP_NAME = '健身饮食';

export const STORAGE_KEYS = {
  // 加 v3 后缀让 v1/v2 残留的 token/user 立即失效，等同于「清除掉一直存在的旧登录信息」
  token: 'gym_token_v3',
  user: 'gym_user_v3',
  cachePrefix: 'gym_cache_',
};

export const MEAL_TYPES = [
  { value: 'breakfast', label: '早餐', icon: 'sunny' },
  { value: 'lunch', label: '午餐', icon: 'food' },
  { value: 'dinner', label: '晚餐', icon: 'moon' },
  { value: 'snack', label: '加餐', icon: 'snack' },
] as const;

export type MealType = typeof MEAL_TYPES[number]['value'];

export const WEEKDAY_CN = ['周日', '周一', '周二', '周三', '周四', '周五', '周六'];

export const FITNESS_GOALS = [
  { value: 'fat_loss', label: '减脂', color: '#5BC89A' },
  { value: 'muscle_gain', label: '增肌', color: '#FF8A65' },
  { value: 'maintain', label: '维持', color: '#6BA8D6' },
  { value: 'shaping', label: '塑形', color: '#C490E0' },
] as const;

export type FitnessGoal = typeof FITNESS_GOALS[number]['value'];

export const TRAINING_FREQUENCIES = [
  { value: '1-2', label: '每周 1-2 次' },
  { value: '3-4', label: '每周 3-4 次' },
  { value: '5-6', label: '每周 5-6 次' },
  { value: 'daily', label: '每天' },
];

export const SCHEDULE_TYPES = [
  { value: 'sequence', label: '顺序循环', desc: 'Day1 → Day2 → Day3 循环' },
  { value: 'weekly', label: '按周排期', desc: '绑定星期几训练' },
];

export const BODY_PARTS = [
  { value: 'chest', label: '胸' },
  { value: 'back', label: '背' },
  { value: 'shoulder', label: '肩' },
  { value: 'leg', label: '腿' },
  { value: 'arm', label: '手臂' },
  { value: 'core', label: '核心' },
  { value: 'cardio', label: '有氧' },
  { value: 'other', label: '其他' },
];

export const FOOD_CATEGORIES = [
  '主食', '肉蛋奶', '蔬菜', '水果', '坚果', '饮品', '零食', '其他',
];