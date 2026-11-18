/** Why an operation failed, as seen by the application (not HTTP). */
export const ErrorCode = Object.freeze({
  INVALID_REQUEST: 'INVALID_REQUEST',
  UNAUTHENTICATED: 'UNAUTHENTICATED',
  FORBIDDEN: 'FORBIDDEN',
  NOT_FOUND: 'NOT_FOUND',
  CONFLICT: 'CONFLICT',
  BAD_GATEWAY: 'BAD_GATEWAY',
  INTERNAL_ERROR: 'INTERNAL_ERROR',
});

/**
 * A known failure thrown by an operation. Handlers keep its code instead of
 * turning it into INTERNAL_ERROR, so callers can tell NOT_FOUND, CONFLICT...
 */
export class ApplicationError extends Error {
  /**
   * @param {keyof typeof ErrorCode} code
   * @param {string} message
   */
  constructor(code, message) {
    super(message);
    this.name = 'ApplicationError';
    this.code = code;
  }
}
