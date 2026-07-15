import initSqlJs, { type Database } from 'sql.js';

import type { SqlDatabase, SqlPrimitive, SqlResult } from './types';

class MemoryDatabase implements SqlDatabase {
  constructor(private readonly db: Database) {}

  async execute(sql: string, params: SqlPrimitive[] = []): Promise<SqlResult> {
    this.db.run(sql, params);
    const rowsAffected = this.db.getRowsModified();
    const id = this.db.exec('SELECT last_insert_rowid() AS id')[0]?.values[0]?.[0];
    return { rowsAffected, insertId: typeof id === 'number' ? id : undefined };
  }

  async query<T extends Record<string, unknown>>(sql: string, params: SqlPrimitive[] = []): Promise<T[]> {
    const statement = this.db.prepare(sql, params);
    const rows: T[] = [];
    try {
      while (statement.step()) rows.push(statement.getAsObject() as T);
      return rows;
    } finally {
      statement.free();
    }
  }

  async transaction<T>(work: (tx: SqlDatabase) => Promise<T>): Promise<T> {
    this.db.run('BEGIN IMMEDIATE');
    try {
      const result = await work(this);
      this.db.run('COMMIT');
      return result;
    } catch (error) {
      this.db.run('ROLLBACK');
      throw error;
    }
  }

  async close(): Promise<void> {
    this.db.close();
  }
}

export async function createMemoryDatabase(): Promise<SqlDatabase> {
  const SQL = await initSqlJs();
  return new MemoryDatabase(new SQL.Database());
}
