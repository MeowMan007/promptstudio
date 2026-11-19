import { describe, expect, it } from 'vitest';
import type { ExcalidrawElement } from '@excalidraw/excalidraw/element/types';
import {
  isSketchElement,
  newSketchProjectionId,
  sketchElementCount,
  sketchToProjectionRecord,
} from './sketch-utils';

function makeElement(overrides: Record<string, unknown> = {}): ExcalidrawElement {
  return {
    id: 'el-1',
    type: 'rectangle',
    x: 10,
    y: 20,
    width: 100,
    height: 60,
    angle: 0,
    strokeColor: '#000',
    backgroundColor: 'transparent',
    fillStyle: 'solid',
    strokeWidth: 1,
    roughness: 0,
    opacity: 100,
    isDeleted: false,
    groupIds: [],
    frameId: null,
    seed: 0,
    version: 1,
    versionNonce: 0,
    index: 'a0',
    updated: 0,
    link: null,
    locked: false,
    boundElements: null,
    ...overrides,
  } as unknown as ExcalidrawElement;
}

describe('isSketchElement', () => {
  it('returns false for a card element (no customData)', () => {
    expect(isSketchElement(makeElement())).toBe(false);
  });

  it('returns false for a card element with kind=card', () => {
    expect(isSketchElement(makeElement({ customData: { kind: 'card', projectionId: 'p-1', artifactId: 'a-1' } }))).toBe(false);
  });

  it('returns true for a sketch element', () => {
    expect(isSketchElement(makeElement({ customData: { kind: 'sketch', projectionId: 'sketch-abc' } }))).toBe(true);
  });
});

describe('sketchElementCount', () => {
  it('returns 0 for empty array', () => {
    expect(sketchElementCount([])).toBe(0);
  });

  it('counts only sketch elements among mixed elements', () => {
    const elements = [
      makeElement({ customData: { kind: 'card' } }),
      makeElement({ customData: { kind: 'sketch' } }),
      makeElement({ customData: { kind: 'sketch' } }),
      makeElement(),
    ];
    expect(sketchElementCount(elements)).toBe(2);
  });
});

describe('newSketchProjectionId', () => {
  it('returns a string starting with "sketch-"', () => {
    const id = newSketchProjectionId();
    expect(id).toMatch(/^sketch-/);
  });

  it('returns different ids on each call', () => {
    const a = newSketchProjectionId();
    const b = newSketchProjectionId();
    expect(a).not.toBe(b);
  });
});

describe('sketchToProjectionRecord', () => {
  it('converts an element into a ProjectionRecord with kind=sketch and artifactId=null', () => {
    const el = makeElement({ x: 50, y: 75, width: 200, height: 120 });
    const record = sketchToProjectionRecord(el, 'sketch-xyz');
    expect(record.kind).toBe('sketch');
    expect(record.artifactId).toBeNull();
    expect(record.projectionId).toBe('sketch-xyz');
    expect(record.x).toBe(50);
    expect(record.y).toBe(75);
    expect(record.width).toBe(200);
    expect(record.height).toBe(120);
    expect(record.title).toBe('Sketch');
    expect(record.z).toBe(0);
  });
});
