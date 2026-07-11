import { MEAL_TYPES, type MealType } from './constants';

export interface DietRecordContext {
  date: string;
  meal: MealType;
  time: string;
}

type DietContextOptions = Partial<Record<keyof DietRecordContext, string>>;

const meals = new Set<string>(MEAL_TYPES.map(item => item.value));

export function buildDietEntryUrl(path: string, context: DietRecordContext) {
  const query = `date=${encodeURIComponent(context.date)}&meal=${encodeURIComponent(context.meal)}&time=${encodeURIComponent(context.time)}`;
  return `${path}?${query}`;
}

export function parseDietContext(options: DietContextOptions | undefined, fallback: DietRecordContext): DietRecordContext {
  return {
    date: options?.date || fallback.date,
    meal: options?.meal && meals.has(options.meal) ? options.meal as MealType : fallback.meal,
    time: options?.time || fallback.time,
  };
}
