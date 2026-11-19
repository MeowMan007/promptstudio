import { describe, expect, it } from 'vitest';
import { PALETTE_GROUPS, ALL_STATES, missingDefaultStates } from './palette-data';
import type { ScreenControl } from './types';

describe('PALETTE_GROUPS', () => {
  it('contains all four groups', () => {
    const labels = PALETTE_GROUPS.map((g) => g.label);
    expect(labels).toContain('Input');
    expect(labels).toContain('Action');
    expect(labels).toContain('Display');
    expect(labels).toContain('Other');
  });

  it('has at least one item per group', () => {
    for (const group of PALETTE_GROUPS) {
      expect(group.items.length).toBeGreaterThan(0);
    }
  });

  it('every item has a non-empty type, label and icon', () => {
    for (const group of PALETTE_GROUPS) {
      for (const item of group.items) {
        expect(item.type.length).toBeGreaterThan(0);
        expect(item.label.length).toBeGreaterThan(0);
        expect(item.icon.length).toBeGreaterThan(0);
      }
    }
  });
});

describe('ALL_STATES', () => {
  it('includes "default"', () => {
    expect(ALL_STATES).toContain('default');
  });

  it('has six states', () => {
    expect(ALL_STATES).toHaveLength(6);
  });
});

describe('missingDefaultStates', () => {
  function ctrl(overrides: Partial<ScreenControl>): ScreenControl {
    return {
      id: 'c1',
      region_id: 'r1',
      control_type: 'button',
      label: 'OK',
      x: 0,
      y: 0,
      width: 80,
      height: 32,
      ...overrides,
    };
  }

  it('returns empty when all types have a default state', () => {
    const controls: ScreenControl[] = [
      ctrl({ control_type: 'button', state: 'default' }),
      ctrl({ control_type: 'input', state: 'default' }),
    ];
    expect(missingDefaultStates(controls)).toHaveLength(0);
  });

  it('returns empty when state is undefined (treated as default)', () => {
    const controls: ScreenControl[] = [
      ctrl({ control_type: 'button', state: undefined }),
    ];
    expect(missingDefaultStates(controls)).toHaveLength(0);
  });

  it('flags a type that only has non-default states', () => {
    const controls: ScreenControl[] = [
      ctrl({ control_type: 'button', state: 'default' }),
      ctrl({ control_type: 'input', state: 'disabled' }), // no default for input
    ];
    const missing = missingDefaultStates(controls);
    expect(missing).toContain('input');
    expect(missing).not.toContain('button');
  });

  it('returns empty for an empty controls array', () => {
    expect(missingDefaultStates([])).toHaveLength(0);
  });
});
