/**
 * Command: executes a use case that may change application state.
 * Override validate() or hasPermission() only when the operation needs them.
 */
export class Command {
  /** @returns {boolean | Promise<boolean>} */
  validate() {
    return true;
  }

  /** @returns {boolean | Promise<boolean>} */
  hasPermission() {
    return true;
  }

  /** @returns {Promise<import('./results.js').CommandResult<unknown>>} */
  async execute() {
    throw new Error(`${this.constructor.name}.execute() is not implemented.`);
  }
}

/**
 * Query: reads application state without intentionally changing it.
 * Override validate() or hasPermission() only when the operation needs them.
 */
export class Query {
  /** @returns {boolean | Promise<boolean>} */
  validate() {
    return true;
  }

  /** @returns {boolean | Promise<boolean>} */
  hasPermission() {
    return true;
  }

  /** @returns {Promise<import('./results.js').QueryResult<unknown>>} */
  async execute() {
    throw new Error(`${this.constructor.name}.execute() is not implemented.`);
  }
}
