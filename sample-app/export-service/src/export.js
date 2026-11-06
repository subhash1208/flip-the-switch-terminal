'use strict';

const { guardExport } = require('./sqlAuthGuard');

function exportTable(request, rows) {
  const scopes = guardExport(request.scopes, request.table);
  return { table: request.table, scopes, count: rows.length, rows };
}

module.exports = { exportTable };
