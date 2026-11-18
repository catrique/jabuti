import type { Observable } from 'rxjs';

/**
 * Lightweight CQRS for the UI: components call Queries to read and Commands
 * to change state. Concrete operations are injectable classes that depend on
 * ApiClient (infrastructure/api), never on HttpClient directly.
 */

/** An operation that may change state (create, update, delete, send...). */
export interface Command<TInput = void, TResult = void> {
  execute(input: TInput): Observable<TResult>;
}

/** A read-only operation. */
export interface Query<TInput = void, TResult = unknown> {
  execute(input: TInput): Observable<TResult>;
}

/**
 * Optional result shapes. An operation may return any type that fits its API,
 * including the response of an external service.
 */
export interface CommandResult<T = void> {
  data?: T;
  rows?: number;
}

export interface QueryResult<T> {
  data: T;
  /** Only for listings (for example, the total before pagination). */
  totalRows?: number | null;
}
