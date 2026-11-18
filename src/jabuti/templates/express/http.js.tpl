import { ErrorCode } from './application/cqrs/index.js';

/** Express adapter: maps application error codes to HTTP status codes. */
export const HTTP_STATUS = Object.freeze({
  [ErrorCode.INVALID_REQUEST]: 400,
  [ErrorCode.UNAUTHENTICATED]: 401,
  [ErrorCode.FORBIDDEN]: 403,
  [ErrorCode.NOT_FOUND]: 404,
  [ErrorCode.CONFLICT]: 409,
  [ErrorCode.BAD_GATEWAY]: 502,
  [ErrorCode.INTERNAL_ERROR]: 500,
});

/** @param {string | undefined} errorCode */
export function httpStatus(errorCode) {
  return HTTP_STATUS[errorCode] ?? 500;
}

/**
 * Send a Command/Query result as JSON: its data on success, or the error
 * code and message with the matching HTTP status.
 */
export function sendResult(response, result, successStatus = 200) {
  if (result.success) {
    return response.status(successStatus).json(result.data ?? null);
  }
  return response
    .status(httpStatus(result.errorCode))
    .json({ errorCode: result.errorCode, message: result.errorMessage });
}
