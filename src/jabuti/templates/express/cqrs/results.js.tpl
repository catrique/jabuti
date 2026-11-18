/**
 * @template T
 * @typedef {object} CommandResult
 * @property {boolean} success
 * @property {T} [data]
 * @property {number} [rows]
 * @property {string} [errorCode]
 * @property {string} [errorMessage]
 */

/**
 * @template T
 * @typedef {object} QueryResult
 * @property {boolean} success
 * @property {T} [data]
 * @property {number | null} [totalRows] Only for listings; null for single reads.
 * @property {string} [errorCode]
 * @property {string} [errorMessage]
 */

export const CommandResult = Object.freeze({
  /** @template T @param {T} [data] @param {number} [rows] @returns {CommandResult<T>} */
  ok: (data, rows) => ({ success: true, data, rows }),
  /** @param {string} errorCode @param {string} errorMessage @returns {CommandResult<never>} */
  fail: (errorCode, errorMessage) => ({ success: false, errorCode, errorMessage }),
});

export const QueryResult = Object.freeze({
  /** @template T @param {T} data @param {number | null} [totalRows] @returns {QueryResult<T>} */
  ok: (data, totalRows = null) => ({ success: true, data, totalRows }),
  /** @param {string} errorCode @param {string} errorMessage @returns {QueryResult<never>} */
  fail: (errorCode, errorMessage) => ({ success: false, errorCode, errorMessage }),
});
