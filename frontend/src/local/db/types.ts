export type SqlPrimitive = string | number | null;

export interface SqlResult {
  rowsAffected: number;
  insertId?: number;
}

export interface SqlDatabase {
  execute(sql: string, params?: SqlPrimitive[]): Promise<SqlResult>;
  query<T extends Record<string, unknown> = Record<string, unknown>>(
    sql: string,
    params?: SqlPrimitive[],
  ): Promise<T[]>;
  transaction<T>(work: (tx: SqlDatabase) => Promise<T>): Promise<T>;
  close(): Promise<void>;
}
