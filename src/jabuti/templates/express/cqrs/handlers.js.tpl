import { ApplicationError, ErrorCode } from './errors.js';
import { CommandResult, QueryResult } from './results.js';

/**
 * Handlers validate, authorize, execute and turn unexpected errors into a
 * generic INTERNAL_ERROR. They never open transactions, commit, publish
 * events or know about HTTP.
 */

/** @param {import('./operations.js').Command} command */
export function handleCommand(command) {
  return run(command, CommandResult.fail);
}

/** @param {import('./operations.js').Query} query */
export function handleQuery(query) {
  return run(query, QueryResult.fail);
}

async function run(operation, fail) {
  try {
    if (!(await operation.validate())) {
      return fail(ErrorCode.INVALID_REQUEST, 'Invalid request.');
    }
    if (!(await operation.hasPermission())) {
      return fail(ErrorCode.FORBIDDEN, 'Permission denied.');
    }
    return await operation.execute();
  } catch (error) {
    if (error instanceof ApplicationError) {
      return fail(error.code, error.message);
    }
    // The stack trace stays in the server log; the caller gets a generic message.
    console.error(`Unexpected error in ${operation.constructor.name}`, error);
    return fail(ErrorCode.INTERNAL_ERROR, 'Unexpected error.');
  }
}
