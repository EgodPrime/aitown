import { describe, it, expect } from 'vitest';
import { PROMPT_MAX_LENGTH } from '../../src/config';

describe('config', () => {
  it('PROMPT_MAX_LENGTH is a positive integer', () => {
    expect(typeof PROMPT_MAX_LENGTH).toBe('number');
    expect(Number.isInteger(PROMPT_MAX_LENGTH)).toBe(true);
    expect(PROMPT_MAX_LENGTH).toBeGreaterThan(0);
  });
});
