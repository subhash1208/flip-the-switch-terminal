'use strict';

// The file is SqlAuthGuard.js; this require uses a lowercase s.
// Resolves on case-insensitive filesystems (APFS, NTFS); throws MODULE_NOT_FOUND on ext4.
const guard = require('./sqlAuthGuard');

if (guard('token') !== true) {
  throw new Error('guard rejected a valid token');
}
console.log('consumer: sqlAuthGuard resolved and works');
