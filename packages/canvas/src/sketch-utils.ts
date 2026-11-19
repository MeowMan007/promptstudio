import type { ExcalidrawElement } from '@excalidraw/excalidraw/element/types';
import type { ProjectionRecord } from './adapter';

/**
 * Returns true if the element was created as a freehand sketch element
 * (customData.kind === 'sketch').
 */
export function isSketchElement(element: ExcalidrawElement): boolean {
  const data = element.customData as Record<string, unknown> | undefined;
  return data?.kind === 'sketch';
}

/**
 * Returns the count of sketch elements in the given element array.
 */
export function sketchElementCount(
  elements: readonly ExcalidrawElement[],
): number {
  return elements.filter(isSketchElement).length;
}

/**
 * Generates a projection id with a `sketch-` prefix backed by a random UUID.
 */
export function newSketchProjectionId(): string {
  return `sketch-${crypto.randomUUID()}`;
}

/**
 * Converts a raw Excalidraw element (which has no artifactId yet) into a
 * ProjectionRecord with kind='sketch'.
 */
export function sketchToProjectionRecord(
  element: ExcalidrawElement,
  projectionId: string,
): ProjectionRecord {
  const rec = element as unknown as Record<string, unknown>;
  return {
    projectionId,
    artifactId: null,
    kind: 'sketch',
    x: Number(rec.x ?? 0),
    y: Number(rec.y ?? 0),
    width: Number(rec.width ?? 0),
    height: Number(rec.height ?? 0),
    z: 0,
    title: 'Sketch',
  };
}
