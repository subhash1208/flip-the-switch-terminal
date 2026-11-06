'use strict';

const assert = require('node:assert');
const { exportTable } = require('./src/export');

const rows = [{ id: 1 }, { id: 2 }];

const ok = exportTable({ scopes: ['exports:write', 'exports:read'], table: 'orders' }, rows);
assert.strictEqual(ok.count, 2);
assert.deepStrictEqual(ok.scopes, ['exports:read', 'exports:write']);

assert.throws(
  () => exportTable({ scopes: ['exports:write'], table: 'orders' }, rows),
  /missing exports:read/,
);
assert.throws(
  () => exportTable({ scopes: ['exports:read'], table: 'orders; DROP TABLE' }, rows),
  /invalid table name/,
);

console.log('export-service: all checks passed');
