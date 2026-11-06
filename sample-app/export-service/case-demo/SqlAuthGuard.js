'use strict';

module.exports = function guard(token) {
  return typeof token === 'string' && token.length > 0;
};
