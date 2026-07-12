import type { PlanDay } from '@/api/training';

interface TrainingPlanDraft {
  name: string;
  schedule_type: 'sequence' | 'weekly';
  days: PlanDay[];
}

export function templatePlanEditUrl(templateId?: number): string {
  return templateId ? `/pages/training/plan-edit?templateId=${templateId}` : '/pages/training/plan-edit';
}

export function validateTrainingPlan(plan: TrainingPlanDraft): string | null {
  if (!plan.name.trim()) return '请填写计划名称';
  if (!plan.days.length) return '请至少添加一个训练日';

  const weekdays = new Set<number>();
  for (const [dayIndex, day] of plan.days.entries()) {
    const dayName = day.day_name.trim();
    if (!dayName) return `请填写第${dayIndex + 1}个训练日名称`;

    if (plan.schedule_type === 'weekly') {
      if (!Number.isInteger(day.weekday) || day.weekday! < 1 || day.weekday! > 7) {
        return `请为训练日“${dayName}”选择星期`;
      }
      if (weekdays.has(day.weekday!)) return '每个训练日请选择不同的星期';
      weekdays.add(day.weekday!);
    }

    if (!day.is_rest_day && !day.exercises.length) {
      return `训练日“${dayName}”至少需要一个动作`;
    }

    for (const [exerciseIndex, exercise] of day.exercises.entries()) {
      const exerciseName = exercise.exercise_name_snapshot || `动作${exerciseIndex + 1}`;
      if (!Number.isInteger(exercise.target_sets) || exercise.target_sets < 1 || exercise.target_sets > 20) {
        return `动作“${exerciseName}”的组数需为1到20的整数`;
      }
      if (!Number.isInteger(exercise.target_reps) || exercise.target_reps < 1 || exercise.target_reps > 100) {
        return `动作“${exerciseName}”的次数需为1到100的整数`;
      }
      if (
        exercise.target_weight_kg != null &&
        (!Number.isFinite(exercise.target_weight_kg) || exercise.target_weight_kg < 0)
      ) {
        return `动作“${exerciseName}”的重量不能小于0`;
      }
      if (
        !Number.isInteger(exercise.rest_seconds) ||
        exercise.rest_seconds < 10 ||
        exercise.rest_seconds > 600
      ) {
        return `动作“${exerciseName}”的休息时间需为10到600秒的整数`;
      }
    }
  }

  return null;
}
