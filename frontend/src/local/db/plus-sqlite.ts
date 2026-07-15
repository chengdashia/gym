import type { SqlDatabase, SqlPrimitive, SqlResult } from './types';

const DB_NAME = 'gym-local';
const DB_PATH = '_doc/gym-local.db';

function literal(value: SqlPrimitive): string {
  if (value === null) return 'NULL';
  if (typeof value === 'number') {
    if (!Number.isFinite(value)) throw new Error('SQL 参数必须是有限数字');
    return String(value);
  }
  return `'${value.replaceAll("'", "''")}'`;
}

export function formatSql(sql: string, params: SqlPrimitive[] = []): string {
  let index = 0;
  const formatted = sql.replace(/\?/g, () => {
    if (index >= params.length) throw new Error('SQL 参数不足');
    return literal(params[index++]);
  });
  if (index !== params.length) throw new Error('SQL 参数过多');
  return formatted;
}

class PlusSqliteDatabase implements SqlDatabase {
  private queue: Promise<unknown> = Promise.resolve();

  private serialize<T>(operation: () => Promise<T>): Promise<T> {
    const result = this.queue.then(operation, operation);
    this.queue = result.then(() => undefined, () => undefined);
    return result;
  }

  async execute(sql: string, params: SqlPrimitive[] = []): Promise<SqlResult> {
    return this.serialize(() => new Promise((resolve, reject) => {
      plus.sqlite.executeSql({
        name: DB_NAME,
        sql: [formatSql(sql, params)],
        success: (result: any) => resolve({
          rowsAffected: Number(result?.rowsAffected || 0),
          insertId: result?.insertId == null ? undefined : Number(result.insertId),
        }),
        fail: reject,
      });
    }));
  }

  async query<T extends Record<string, unknown>>(sql: string, params: SqlPrimitive[] = []): Promise<T[]> {
    return this.serialize(() => new Promise((resolve, reject) => {
      plus.sqlite.selectSql({
        name: DB_NAME,
        sql: formatSql(sql, params),
        success: (rows: unknown[]) => resolve(rows as T[]),
        fail: reject,
      });
    }));
  }

  async transaction<T>(work: (tx: SqlDatabase) => Promise<T>): Promise<T> {
    await this.execute('BEGIN IMMEDIATE');
    try {
      const result = await work(this);
      await this.execute('COMMIT');
      return result;
    } catch (error) {
      await this.execute('ROLLBACK');
      throw error;
    }
  }

  async close(): Promise<void> {
    await this.queue;
    if (!plus.sqlite.isOpenDatabase({ name: DB_NAME, path: DB_PATH })) return;
    await new Promise<void>((resolve, reject) => plus.sqlite.closeDatabase({ name: DB_NAME, success: resolve, fail: reject }));
  }
}

export async function openPlusSqliteDatabase(): Promise<SqlDatabase> {
  if (!plus.sqlite.isOpenDatabase({ name: DB_NAME, path: DB_PATH })) {
    await new Promise<void>((resolve, reject) => plus.sqlite.openDatabase({ name: DB_NAME, path: DB_PATH, success: resolve, fail: reject }));
  }
  return new PlusSqliteDatabase();
}
