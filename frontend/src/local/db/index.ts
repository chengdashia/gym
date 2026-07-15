import { migrateDatabase } from './migrations';
import { openPlusSqliteDatabase } from './plus-sqlite';
import type { SqlDatabase } from './types';
import { installSeeds } from '@/local/seed';

let database: SqlDatabase | null = null;

export async function initializeLocalDatabase(): Promise<SqlDatabase> {
  if (database) return database;
  database = await openPlusSqliteDatabase();
  try {
    await migrateDatabase(database);
    await installSeeds(database);
    return database;
  } catch (error) {
    await database.close();
    database = null;
    throw error;
  }
}

export function getLocalDatabase(): SqlDatabase {
  if (!database) throw new Error('本地数据库尚未初始化');
  return database;
}

export function setDatabaseForTests(value: SqlDatabase | null): void {
  database = value;
}

export type { SqlDatabase, SqlPrimitive, SqlResult } from './types';
