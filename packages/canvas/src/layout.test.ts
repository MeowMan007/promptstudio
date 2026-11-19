import { describe, expect, it } from 'vitest';

import {
  autoLayout,
  DEFAULT_PROJECT_ZONES,
  minimapItems,
  snapCoordinate,
  snapLayout,
} from './layout';

const items = [
  {
    projectionId: 'b',
    artifactId: 'art-b',
    x: 500,
    y: 200,
    width: 100,
    height: 60,
    z: 2,
  },
  {
    projectionId: 'a',
    artifactId: 'art-a',
    x: 100,
    y: 20,
    width: 120,
    height: 80,
    z: 1,
  },
  {
    projectionId: 'c',
    artifactId: null,
    x: 0,
    y: 0,
    width: 80,
    height: 50,
    z: 3,
  },
];

describe('canvas layout utilities', () => {
  it('provides the nine default project zones with layout policies', () => {
    expect(DEFAULT_PROJECT_ZONES).toHaveLength(9);
    expect(DEFAULT_PROJECT_ZONES.map((zone) => zone.title)).toContain(
      'Open Questions',
    );
  });

  it('places a grid deterministically regardless of input order', () => {
    const first = autoLayout(items, 'grid', 32);
    const second = autoLayout([...items].reverse(), 'grid', 32);
    expect(first).toEqual(second);
    expect(first.map(({ projectionId, x, y }) => [projectionId, x, y])).toEqual(
      [
        ['a', 0, 0],
        ['b', 152, 0],
        ['c', 0, 112],
      ],
    );
  });

  it('lays out a column using the preceding card height', () => {
    const column = autoLayout(items, 'column', 20);
    expect(column.map(({ x, y }) => [x, y])).toEqual([
      [0, 0],
      [0, 100],
      [0, 180],
    ]);
  });

  it('lays out a tree deterministically by level and z order', () => {
    const tree = autoLayout(items, 'tree', 20);
    expect(tree[0]).toMatchObject({ projectionId: 'a', x: 0, y: 0 });
    expect(tree[1]).toMatchObject({ projectionId: 'b', x: -70, y: 100 });
    expect(tree[2]).toMatchObject({ projectionId: 'c', x: 70, y: 100 });
  });

  it('preserves free layout and snaps positions to a finite grid', () => {
    expect(autoLayout(items, 'free')).toEqual([items[1], items[0], items[2]]);
    expect(snapCoordinate(27, 16)).toBe(32);
    expect(snapLayout(items, 16).map(({ x, y }) => [x, y])).toEqual([
      [496, 208],
      [96, 16],
      [0, 0],
    ]);
    expect(() => snapCoordinate(3, 0)).toThrow(RangeError);
  });

  it('fits projections into a minimap while preserving artifact bindings', () => {
    const mini = minimapItems(items, 120, 80);
    expect(mini).toHaveLength(3);
    expect(mini.every((item) => item.x >= 4 && item.y >= 4)).toBe(true);
    expect(
      mini.find((item) => item.projectionId === 'c')?.artifactId,
    ).toBeNull();
    expect(mini.at(-1)?.x).toBeLessThanOrEqual(116);
  });
});
