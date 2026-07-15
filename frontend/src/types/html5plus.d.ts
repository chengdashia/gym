declare const plus: {
  sqlite: {
    isOpenDatabase(options: { name: string; path: string }): boolean;
    openDatabase(options: { name: string; path: string; success(): void; fail(error: unknown): void }): void;
    closeDatabase(options: { name: string; success(): void; fail(error: unknown): void }): void;
    executeSql(options: { name: string; sql: string; success(result?: unknown): void; fail(error: unknown): void }): void;
    selectSql(options: { name: string; sql: string; success(rows: unknown[]): void; fail(error: unknown): void }): void;
  };
};
