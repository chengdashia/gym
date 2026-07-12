import { describe, expect, it } from 'vitest';
import { templatePlanEditUrl, validateTrainingPlan } from './training-plan';

describe('validateTrainingPlan', () => {
  const validPlan = () => ({
    name: '计划',
    schedule_type: 'sequence',
    days: [{
      day_name: 'Day1',
      is_rest_day: false,
      weekday: null,
      exercises: [{
        exercise_name_snapshot: '深蹲',
        target_sets: 4,
        target_reps: 10,
        target_weight_kg: 0,
        rest_seconds: 90,
      }],
    }],
  });

  it('rejects a workout day with no exercises', () => {
    expect(validateTrainingPlan({
      name: '计划', schedule_type: 'sequence',
      days: [{ day_name: 'Day1', is_rest_day: false, weekday: null, exercises: [] }],
    } as any)).toBe('训练日“Day1”至少需要一个动作');
  });

  it('requires a plan name and at least one day', () => {
    expect(validateTrainingPlan({ ...validPlan(), name: '  ' } as any)).toBe('请填写计划名称');
    expect(validateTrainingPlan({ ...validPlan(), days: [] } as any)).toBe('请至少添加一个训练日');
  });

  it('requires each training day to have a name', () => {
    const plan = validPlan();
    plan.days[0].day_name = '  ';
    expect(validateTrainingPlan(plan as any)).toBe('请填写第1个训练日名称');
  });

  it('allows a rest day with no exercises', () => {
    const plan = validPlan();
    plan.days[0].is_rest_day = true;
    plan.days[0].exercises = [];
    expect(validateTrainingPlan(plan as any)).toBeNull();
  });

  it('requires unique weekdays for weekly plans', () => {
    const plan = validPlan();
    plan.schedule_type = 'weekly';
    plan.days[0].weekday = 1;
    plan.days.push({ ...plan.days[0], day_name: 'Day2', weekday: 1 });
    expect(validateTrainingPlan(plan as any)).toBe('每个训练日请选择不同的星期');
  });

  it('requires weekdays from one to seven for weekly plans', () => {
    const plan = validPlan();
    plan.schedule_type = 'weekly';
    plan.days[0].weekday = null;
    expect(validateTrainingPlan(plan as any)).toBe('请为训练日“Day1”选择星期');
  });

  it.each([
    ['target_sets', 0, '动作“深蹲”的组数需为1到20的整数'],
    ['target_sets', 21, '动作“深蹲”的组数需为1到20的整数'],
    ['target_reps', 0, '动作“深蹲”的次数需为1到100的整数'],
    ['target_reps', 101, '动作“深蹲”的次数需为1到100的整数'],
    ['target_weight_kg', -1, '动作“深蹲”的重量不能小于0'],
    ['rest_seconds', 9, '动作“深蹲”的休息时间需为10到600秒的整数'],
    ['rest_seconds', 601, '动作“深蹲”的休息时间需为10到600秒的整数'],
  ])('rejects an invalid %s', (field, value, message) => {
    const plan = validPlan();
    Object.assign(plan.days[0].exercises[0], { [field]: value });
    expect(validateTrainingPlan(plan as any)).toBe(message);
  });

  it('accepts all numeric boundary values', () => {
    const plan = validPlan();
    Object.assign(plan.days[0].exercises[0], {
      target_sets: 20,
      target_reps: 100,
      target_weight_kg: null,
      rest_seconds: 600,
    });
    expect(validateTrainingPlan(plan as any)).toBeNull();
  });
});

describe('templatePlanEditUrl', () => {
  it('opens the blank plan editor when no template is chosen', () => {
    expect(templatePlanEditUrl()).toBe('/pages/training/plan-edit');
  });

  it('opens template configuration instead of creating a plan directly', () => {
    expect(templatePlanEditUrl(42)).toBe('/pages/training/plan-edit?templateId=42');
  });
});
