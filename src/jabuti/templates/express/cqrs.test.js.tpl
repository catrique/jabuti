import assert from 'node:assert/strict';
import { test } from 'node:test';

import {
  ApplicationError,
  Command,
  CommandResult,
  ErrorCode,
  Query,
  handleCommand,
  handleQuery,
} from '../src/application/cqrs/index.js';

class Rename extends Command {
  constructor(name) {
    super();
    this.name = name;
  }

  validate() {
    return Boolean(this.name);
  }

  async execute() {
    return CommandResult.ok(this.name, 1);
  }
}

class Missing extends Query {
  async execute() {
    throw new ApplicationError(ErrorCode.NOT_FOUND, 'Not found.');
  }
}

test('command runs only after validation', async () => {
  assert.equal((await handleCommand(new Rename('new'))).data, 'new');
  const rejected = await handleCommand(new Rename(''));
  assert.equal(rejected.errorCode, ErrorCode.INVALID_REQUEST);
});

test('known query failure keeps its error code', async () => {
  const result = await handleQuery(new Missing());
  assert.equal(result.success, false);
  assert.equal(result.errorCode, ErrorCode.NOT_FOUND);
});
