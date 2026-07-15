export const SCHEMA_VERSION = 1;

export const SCHEMA_V1 = [
  `CREATE TABLE IF NOT EXISTS app_meta (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
  )`,
  `CREATE TABLE IF NOT EXISTS local_profile (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    nickname TEXT,
    avatar_path TEXT,
    gender TEXT,
    age INTEGER,
    height_centi INTEGER,
    current_weight_centi INTEGER,
    target_weight_centi INTEGER,
    fitness_goal TEXT,
    training_frequency TEXT,
    onboarding_step TEXT NOT NULL DEFAULT 'profile',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
  )`,
  `CREATE TABLE IF NOT EXISTS nutrition_goals (
    id INTEGER PRIMARY KEY,
    calories_centi INTEGER NOT NULL DEFAULT 0,
    carbs_centi INTEGER NOT NULL DEFAULT 0,
    protein_centi INTEGER NOT NULL DEFAULT 0,
    fat_centi INTEGER NOT NULL DEFAULT 0,
    source TEXT NOT NULL DEFAULT 'manual',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
  )`,
  `CREATE TABLE IF NOT EXISTS foods (
    id INTEGER PRIMARY KEY,
    stable_key TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    category TEXT,
    calories_centi INTEGER NOT NULL DEFAULT 0,
    carbs_centi INTEGER NOT NULL DEFAULT 0,
    protein_centi INTEGER NOT NULL DEFAULT 0,
    fat_centi INTEGER NOT NULL DEFAULT 0,
    fiber_centi INTEGER,
    default_unit TEXT NOT NULL DEFAULT 'g',
    serving_weight_centi INTEGER,
    status TEXT NOT NULL DEFAULT 'active'
  )`,
  `CREATE TABLE IF NOT EXISTS custom_foods (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    category TEXT,
    calories_centi INTEGER NOT NULL DEFAULT 0,
    carbs_centi INTEGER NOT NULL DEFAULT 0,
    protein_centi INTEGER NOT NULL DEFAULT 0,
    fat_centi INTEGER NOT NULL DEFAULT 0,
    fiber_centi INTEGER,
    default_unit TEXT NOT NULL DEFAULT 'g',
    serving_weight_centi INTEGER,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    deleted_at TEXT
  )`,
  `CREATE TABLE IF NOT EXISTS uploaded_files (
    id INTEGER PRIMARY KEY,
    relative_path TEXT NOT NULL UNIQUE,
    purpose TEXT NOT NULL,
    created_at TEXT NOT NULL,
    deleted_at TEXT
  )`,
  `CREATE TABLE IF NOT EXISTS diet_records (
    id INTEGER PRIMARY KEY,
    record_date TEXT NOT NULL,
    record_time TEXT NOT NULL,
    meal_type TEXT NOT NULL,
    food_source TEXT NOT NULL,
    food_id INTEGER,
    custom_food_id INTEGER,
    food_name_snapshot TEXT NOT NULL,
    unit_type TEXT NOT NULL,
    amount_centi INTEGER,
    serving_count_centi INTEGER,
    calories_centi INTEGER NOT NULL DEFAULT 0,
    carbs_centi INTEGER NOT NULL DEFAULT 0,
    protein_centi INTEGER NOT NULL DEFAULT 0,
    fat_centi INTEGER NOT NULL DEFAULT 0,
    uploaded_file_id INTEGER REFERENCES uploaded_files(id) ON DELETE SET NULL,
    note TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    deleted_at TEXT,
    FOREIGN KEY(food_id) REFERENCES foods(id),
    FOREIGN KEY(custom_food_id) REFERENCES custom_foods(id)
  )`,
  `CREATE TABLE IF NOT EXISTS exercises (
    id INTEGER PRIMARY KEY,
    stable_key TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    body_part TEXT,
    equipment TEXT,
    status TEXT NOT NULL DEFAULT 'active'
  )`,
  `CREATE TABLE IF NOT EXISTS custom_exercises (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    body_part TEXT,
    equipment TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    deleted_at TEXT
  )`,
  `CREATE TABLE IF NOT EXISTS training_templates (
    id INTEGER PRIMARY KEY,
    stable_key TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    description TEXT,
    payload_json TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'active'
  )`,
  `CREATE TABLE IF NOT EXISTS training_plans (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    schedule_type TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'active',
    start_date TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    deleted_at TEXT
  )`,
  `CREATE TABLE IF NOT EXISTS training_plan_days (
    id INTEGER PRIMARY KEY,
    plan_id INTEGER NOT NULL REFERENCES training_plans(id) ON DELETE CASCADE,
    day_number INTEGER NOT NULL,
    weekday INTEGER,
    name TEXT NOT NULL,
    is_rest_day INTEGER NOT NULL DEFAULT 0
  )`,
  `CREATE TABLE IF NOT EXISTS training_plan_exercises (
    id INTEGER PRIMARY KEY,
    plan_day_id INTEGER NOT NULL REFERENCES training_plan_days(id) ON DELETE CASCADE,
    exercise_source TEXT NOT NULL,
    exercise_id INTEGER,
    custom_exercise_id INTEGER,
    exercise_name_snapshot TEXT NOT NULL,
    exercise_order INTEGER NOT NULL,
    target_sets INTEGER NOT NULL,
    target_reps TEXT,
    rest_seconds INTEGER NOT NULL DEFAULT 60
  )`,
  `CREATE TABLE IF NOT EXISTS training_sessions (
    id INTEGER PRIMARY KEY,
    plan_id INTEGER REFERENCES training_plans(id) ON DELETE SET NULL,
    plan_day_id INTEGER REFERENCES training_plan_days(id) ON DELETE SET NULL,
    session_date TEXT NOT NULL,
    session_name TEXT NOT NULL,
    status TEXT NOT NULL,
    duration_seconds INTEGER NOT NULL DEFAULT 0,
    total_volume_centi INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    deleted_at TEXT
  )`,
  `CREATE TABLE IF NOT EXISTS training_session_exercises (
    id INTEGER PRIMARY KEY,
    session_id INTEGER NOT NULL REFERENCES training_sessions(id) ON DELETE CASCADE,
    exercise_name_snapshot TEXT NOT NULL,
    body_part_snapshot TEXT,
    exercise_order INTEGER NOT NULL
  )`,
  `CREATE TABLE IF NOT EXISTS training_session_sets (
    id INTEGER PRIMARY KEY,
    session_exercise_id INTEGER NOT NULL REFERENCES training_session_exercises(id) ON DELETE CASCADE,
    set_number INTEGER NOT NULL,
    weight_centi INTEGER,
    reps INTEGER,
    duration_seconds INTEGER,
    completed INTEGER NOT NULL DEFAULT 0,
    UNIQUE(session_exercise_id, set_number)
  )`,
  `CREATE TABLE IF NOT EXISTS weight_records (
    id INTEGER PRIMARY KEY,
    weight_centi INTEGER NOT NULL,
    recorded_at TEXT NOT NULL,
    note TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    deleted_at TEXT
  )`,
  `CREATE INDEX IF NOT EXISTS idx_diet_records_date ON diet_records(record_date, deleted_at)`,
  `CREATE INDEX IF NOT EXISTS idx_weight_records_date ON weight_records(recorded_at, deleted_at)`,
  `CREATE INDEX IF NOT EXISTS idx_training_sessions_date ON training_sessions(session_date, deleted_at)`,
  `CREATE INDEX IF NOT EXISTS idx_training_plan_days_plan ON training_plan_days(plan_id, day_number)`,
  `CREATE INDEX IF NOT EXISTS idx_training_plan_exercises_day ON training_plan_exercises(plan_day_id, exercise_order)`,
  `CREATE INDEX IF NOT EXISTS idx_uploaded_files_path ON uploaded_files(relative_path)`,
] as const;
