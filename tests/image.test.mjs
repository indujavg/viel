import test from 'node:test';
import assert from 'node:assert/strict';
import { validateFile, validateDimensions, MAX_BYTES, MAX_PIXELS } from '../src/lib/image.ts';

test('accepts supported nonempty images at the byte limit', () => {
  for (const type of ['image/png', 'image/jpeg']) assert.equal(validateFile({type, size:MAX_BYTES}), null);
});
test('rejects unsupported, empty, and oversized files', () => {
  for (const file of [{type:'image/svg+xml',size:12},{type:'image/png',size:0},{type:'image/jpeg',size:MAX_BYTES+1}]) assert.ok(validateFile(file));
});
test('bounds decoded dimensions', () => {
  assert.equal(validateDimensions(6000,4000),null);
  assert.ok(validateDimensions(MAX_PIXELS+1,1));
  assert.ok(validateDimensions(0,1));
  assert.ok(validateDimensions(NaN,1));
});
