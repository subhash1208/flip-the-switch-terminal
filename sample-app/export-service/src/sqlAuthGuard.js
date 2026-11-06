'use strict';

const REQUIRED_SCOPE = 'exports:read';

function guardExport(scopes, table) {
  // Array.prototype.toSorted needs Node 20+. On Node 18 this line throws.
  const sorted = scopes.toSorted((a, b) => a.localeCompare(b));
  if (!sorted.includes(REQUIRED_SCOPE)) {
    throw new Error(`forbidden: missing ${REQUIRED_SCOPE}`);
  }
  if (!/^[A-Za-z_][A-Za-z0-9_]*$/.test(table)) {
    throw new Error(`invalid table name: ${table}`);
  }
  return sorted;
}

module.exports = { guardExport };
