const test = require('node:test');
const assert = require('node:assert');
const { cleanFilename, getHeaders, formatSrtTime } = require('./utils.js');

test('cleanFilename should remove invalid Windows filename characters', () => {
  assert.strictEqual(cleanFilename('Hello/World: *?\"<>|'), 'Hello_World_ ______');
});

test('getHeaders should construct correct HTTP headers with cookie', () => {
  const headers = getHeaders('SESSDATA=123');
  assert.strictEqual(headers['Referer'], 'https://www.bilibili.com/');
  assert.strictEqual(headers['Cookie'], 'SESSDATA=123');
});

test('formatSrtTime should format seconds to SRT timestamp', () => {
  assert.strictEqual(formatSrtTime(1.5), '00:00:01,500');
  assert.strictEqual(formatSrtTime(3661.085), '01:01:01,085');
});
