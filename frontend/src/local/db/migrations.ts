import { SCHEMA_V1, SCHEMA_VERSION } from './schema';
import type { SqlDatabase } from './types';

export async function migrateDatabase(db: SqlDatabase): Promise<void> {
  await db.execute('PRAGMA foreign_keys = ON');
  const rows = await db.query<{ user_version: number }>('PRAGMA user_version');
  const current = Number(rows[0]?.user_version || 0);

  if (current > SCHEMA_VERSION) {
    throw new Error(`数据库版本 ${current} 高于应用支持版本 ${SCHEMA_VERSION}`);
  }
  if (current === SCHEMA_VERSION) return;

  await db.transaction(async (tx) => {
    for (const sql of SCHEMA_V1) await tx.execute(sql);
    await tx.execute(`PRAGMA user_version = ${SCHEMA_VERSION}`);
  });
}
