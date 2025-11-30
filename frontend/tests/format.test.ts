import { test, strict as assert } from 'node:test';
import { fmtPaceSec, fmtHHMMSS, to12h } from '../src/lib/format';

test('fmtPaceSec formats mm:ss', () => {
  assert.equal(fmtPaceSec(0), '0:00');
  assert.equal(fmtPaceSec(65), '1:05');
  assert.equal(fmtPaceSec(600), '10:00');
});

test('fmtHHMMSS formats H:MM:SS with collapse', () => {
  assert.equal(fmtHHMMSS(59), '0:59');
  assert.equal(fmtHHMMSS(61), '1:01');
  assert.equal(fmtHHMMSS(3661), '1:01:01');
});

test('to12h converts HH:MM', () => {
  assert.equal(to12h('00:15'), '12:15 AM');
  assert.equal(to12h('12:30'), '12:30 PM');
  assert.equal(to12h('18:45'), '6:45 PM');
});

