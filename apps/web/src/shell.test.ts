/**
 * EPIC-04 unit tests: tokens, a11y utilities, outline filtering logic.
 * These tests run in vitest without a DOM (pure logic only).
 */
import { describe, expect, it, vi } from 'vitest';
import { contrastRatio, passesWCAG_AA } from './a11y-utils';
import { color } from './tokens';

// ── Token sanity ──────────────────────────────────────────────────────────────

describe('design tokens', () => {
  it('color.primary is a valid hex string', () => {
    expect(color.primary).toMatch(/^#[0-9a-fA-F]{6}$/);
  });

  it('color.text is a valid hex string', () => {
    expect(color.text).toMatch(/^#[0-9a-fA-F]{6}$/);
  });
});

// ── WCAG contrast ─────────────────────────────────────────────────────────────

describe('contrastRatio', () => {
  it('black on white is ~21:1', () => {
    expect(contrastRatio('#000000', '#ffffff')).toBeCloseTo(21, 0);
  });

  it('white on white is 1:1', () => {
    expect(contrastRatio('#ffffff', '#ffffff')).toBeCloseTo(1, 2);
  });

  it('is symmetric', () => {
    const a = contrastRatio('#2563eb', '#ffffff');
    const b = contrastRatio('#ffffff', '#2563eb');
    expect(a).toBeCloseTo(b, 10);
  });
});

describe('passesWCAG_AA', () => {
  it('black on white passes normal text', () => {
    expect(passesWCAG_AA('#000000', '#ffffff')).toBe(true);
  });

  it('white on white fails', () => {
    expect(passesWCAG_AA('#ffffff', '#ffffff')).toBe(false);
  });

  it('primary text on primary bg passes large text threshold', () => {
    // #ffffff on #2563eb — may not pass 4.5 but should pass 3.0 for large text
    expect(passesWCAG_AA('#ffffff', '#2563eb', true)).toBe(true);
  });
});
