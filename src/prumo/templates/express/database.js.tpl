import mysql from 'mysql2/promise';

let pool;

// The pool is created lazily; credentials always come from environment variables.
export function getPool() {
  pool ??= mysql.createPool({
    host: process.env.DB_HOST ?? 'localhost',
    port: Number(process.env.DB_PORT ?? 3306),
    database: process.env.DB_NAME,
    user: process.env.DB_USER,
    password: process.env.DB_PASSWORD,
    connectionLimit: 10,
  });

  return pool;
}
