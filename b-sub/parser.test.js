const test = require('node:test');
const assert = require('node:assert');
const { bccToSrt } = require('./parser.js');

test('bccToSrt should convert BCC JSON body to SRT format', () => {
  const bccJson = {
    body: [
      { from: 1.5, to: 3.08, content: "Hello World" },
      { from: 4.0, to: 5.5, content: "Second subtitle" }
    ]
  };
  const expectedSrt = [
    '1',
    '00:00:01,500 --> 00:00:03,080',
    'Hello World',
    '',
    '2',
    '00:00:04,000 --> 00:00:05,500',
    'Second subtitle',
    ''
  ].join('\r\n');
  
  assert.strictEqual(bccToSrt(bccJson), expectedSrt);
});
