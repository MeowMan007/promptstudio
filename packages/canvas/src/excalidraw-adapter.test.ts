import { afterEach, describe, expect, it, vi } from 'vitest';

vi.mock('@excalidraw/excalidraw', () => ({
  CaptureUpdateAction: { NEVER: 'never' },
  Excalidraw: () => null,
  convertToExcalidrawElements: (elements: unknown[]) => elements,
  exportToBlob: async () => new Blob(),
  exportToSvg: async () => ({ outerHTML: '<svg />' }),
  serializeAsJSON: () => JSON.stringify({ type: 'excalidraw' }),
}));
vi.mock('@excalidraw/excalidraw/index.css', () => ({}));
vi.mock('./canvas-accessibility.css', () => ({}));

import type { ExcalidrawElement } from '@excalidraw/excalidraw/element/types';
import type {
  AppState,
  ExcalidrawImperativeAPI,
} from '@excalidraw/excalidraw/types';
import {
  accessibleNameForProjection,
  ExcalidrawCanvasAdapter,
  projectionToElement,
} from './excalidraw-adapter';
import type { ProjectionRecord } from './adapter';

const projection = (
  overrides: Partial<ProjectionRecord> = {},
): ProjectionRecord => ({
  projectionId: 'projection-1',
  artifactId: 'art_00000000000000000000000001',
  kind: 'card',
  x: 20,
  y: 30,
  width: 240,
  height: 100,
  z: 1,
  title: 'Requirement',
  semanticHash: 'hash-1',
  ...overrides,
});

const element = (
  id: string,
  overrides: Record<string, unknown> = {},
): ExcalidrawElement =>
  ({
    id,
    type: 'rectangle',
    x: 20,
    y: 30,
    width: 240,
    height: 100,
    isDeleted: false,
    customData: {
      artifactId: 'art_00000000000000000000000001',
      projectionId: id,
      z: 1,
    },
    ...overrides,
  }) as unknown as ExcalidrawElement;

const appState = (selectedElementIds: Record<string, boolean> = {}) =>
  ({
    selectedElementIds,
    scrollX: 11,
    scrollY: 17,
    zoom: { value: 1.25 },
  }) as AppState;

function attachApi(
  adapter: ExcalidrawCanvasAdapter,
  api: Record<string, unknown>,
): void {
  (adapter as unknown as { api: ExcalidrawImperativeAPI }).api =
    api as unknown as ExcalidrawImperativeAPI;
}

describe('Excalidraw adapter conformance TC-020..029', () => {
  afterEach(() => {
    vi.useRealTimers();
  });

  it('TC-020 maps projection identity into engine custom data', () => {
    const sceneElement = projectionToElement(projection());
    expect(sceneElement.customData).toMatchObject({
      artifactId: 'art_00000000000000000000000001',
      projectionId: 'projection-1',
      semanticHash: 'hash-1',
    });
  });

  it('TC-021 keeps pure sketches valid without an artifact binding', () => {
    const sceneElement = projectionToElement(
      projection({
        projectionId: 'sketch-1',
        artifactId: null,
        kind: 'sketch',
      }),
    );
    expect(sceneElement.type).toBe('rectangle');
    expect(sceneElement.customData?.artifactId).toBeNull();
  });

  it('renders typed labels and readable, accessible card names', () => {
    const card = projection({
      card: {
        artifactType: 'requirement',
        alias: 'REQ-014',
        status: 'in_review',
        bodyPreview: 'A creator can publish a payment form.',
        badges: ['MUST', '3 criteria'],
        relationSummary: ['implements → SVC-001'],
        provenanceLabel: 'src: 2 · owner: A',
        revision: 7,
      },
    });
    const sceneElement = projectionToElement(card);
    const name = accessibleNameForProjection(card);
    const rendered = sceneElement as unknown as {
      label?: { text: string };
      strokeColor?: string;
      backgroundColor?: string;
      customData?: Record<string, unknown>;
    };
    expect(rendered.label?.text).toContain('REQUIREMENT  REQ-014  [IN_REVIEW]');
    expect(rendered.label?.text).toContain('[MUST]  [3 criteria]');
    expect(rendered.strokeColor).toBe('#111827');
    expect(rendered.backgroundColor).toBe('#ffffff');
    expect(rendered.customData?.accessibleName).toBe(name);
    expect(name).toContain('requirement REQ-014');
    expect(name).toContain('status in_review');
    expect(name).toContain('revision 7');
  });

  it('TC-022 loads and applies projection deltas without emitting semantic edits', async () => {
    const adapter = new ExcalidrawCanvasAdapter();
    const updateScene = vi.fn();
    attachApi(adapter, {
      updateScene,
      getSceneElements: () => [],
    });
    const semantic = vi.fn();
    adapter.onSemanticEdit(semantic);

    await adapter.loadScene([projection()], []);
    await adapter.applyProjectionDelta([
      {
        operation: 'upsert',
        projection: projection({ title: 'Updated', x: 60 }),
      },
      {
        operation: 'upsert',
        projection: projection({
          projectionId: 'sketch-1',
          artifactId: null,
          kind: 'sketch',
        }),
      },
    ]);

    expect(updateScene).toHaveBeenCalledTimes(2);
    expect(semantic).not.toHaveBeenCalled();
    expect(updateScene.mock.calls[1][0].elements).toHaveLength(2);
  });

  it('TC-023 reads a serializable scene and viewport', async () => {
    const adapter = new ExcalidrawCanvasAdapter();
    attachApi(adapter, {
      getSceneElementsIncludingDeleted: () => [],
      getAppState: () => appState(),
      getFiles: () => ({}),
    });
    const snapshot = await adapter.readScene();
    expect(JSON.parse(snapshot.serialized).type).toBe('excalidraw');
    expect(snapshot.viewport).toEqual({ x: 11, y: 17, zoom: 1.25 });
  });

  it('promotes selected sketch projections with the persisted scene snapshot', async () => {
    const adapter = new ExcalidrawCanvasAdapter();
    const sketch = element('sketch-projection', {
      customData: {
        artifactId: null,
        projectionId: 'sketch-projection',
        kind: 'sketch',
      },
    });
    attachApi(adapter, {
      getAppState: () => appState({ 'sketch-projection': true }),
      getSceneElements: () => [sketch],
      getSceneElementsIncludingDeleted: () => [sketch],
      getFiles: () => ({}),
    });
    const promote = vi.fn();
    adapter.onPromoteSketch(promote);
    await adapter.promoteSelectedSketches();
    expect(promote).toHaveBeenCalledWith({
      projectionId: 'sketch-projection',
      sceneJson: '{"type":"excalidraw"}',
    });
  });

  it('TC-024 resolves the artifact under a scene point', () => {
    const adapter = new ExcalidrawCanvasAdapter();
    const card = element('projection-1');
    attachApi(adapter, { getSceneElements: () => [card] });
    expect(adapter.getArtifactIdAt({ x: 24, y: 35 })).toBe(
      card.customData?.artifactId,
    );
    expect(adapter.getArtifactIdAt({ x: 900, y: 900 })).toBeNull();
  });

  it('TC-025 reports only selected artifact-backed elements', () => {
    const adapter = new ExcalidrawCanvasAdapter();
    const card = element('projection-1');
    const sketch = element('sketch-1', {
      customData: { artifactId: null, projectionId: 'sketch-1' },
    });
    attachApi(adapter, {
      getSceneElements: () => [card, sketch],
      getAppState: () => appState({ 'projection-1': true, 'sketch-1': true }),
    });
    expect(adapter.getSelectedArtifactIds()).toEqual([
      card.customData?.artifactId,
    ]);
  });

  it('TC-026 converts attached text edits to semantic intents', () => {
    const adapter = new ExcalidrawCanvasAdapter();
    const before = element('projection-1', { type: 'text', text: 'Before' });
    const after = element('projection-1', { type: 'text', text: 'After' });
    const internals = adapter as unknown as {
      previous: Map<string, ExcalidrawElement>;
      handleChange(elements: ExcalidrawElement[], appState: AppState): void;
    };
    internals.previous.set(before.id, before);
    const semantic = vi.fn();
    const source = element('source', {
      customData: { artifactId: 'source-artifact', projectionId: 'source' },
    });
    const target = element('target', {
      customData: { artifactId: 'target-artifact', projectionId: 'target' },
    });
    const arrow = element('arrow', {
      type: 'arrow',
      startBinding: { elementId: 'source' },
      endBinding: { elementId: 'target' },
    });
    const connect = vi.fn();
    adapter.onSemanticEdit(semantic);
    adapter.onConnect(connect);
    internals.handleChange([after, source, target, arrow], appState());
    expect(semantic).toHaveBeenCalledWith({
      operation: 'update_title',
      artifactId: 'art_00000000000000000000000001',
      value: 'After',
    });
    expect(connect).toHaveBeenCalledWith({
      sourceArtifactId: 'source-artifact',
      targetArtifactId: 'target-artifact',
      edgeType: 'untyped',
    });
  });

  it('TC-027 batches layout changes after the 100 ms debounce window', async () => {
    vi.useFakeTimers();
    const adapter = new ExcalidrawCanvasAdapter();
    const before = element('projection-1');
    const moved = element('projection-1', { x: 70, y: 80 });
    const internals = adapter as unknown as {
      previous: Map<string, ExcalidrawElement>;
      handleChange(elements: ExcalidrawElement[], appState: AppState): void;
    };
    internals.previous.set(before.id, before);
    const layout = vi.fn();
    adapter.onLayoutChange(layout);
    internals.handleChange([moved], appState());
    expect(layout).not.toHaveBeenCalled();
    await vi.advanceTimersByTimeAsync(100);
    expect(layout).toHaveBeenCalledTimes(1);
    expect(layout.mock.calls[0][0][0]).toMatchObject({
      projectionId: 'projection-1',
      x: 70,
      y: 80,
    });
  });

  it('TC-028 updates custom data and focuses all projections for an artifact', async () => {
    const adapter = new ExcalidrawCanvasAdapter();
    const card = element('projection-1');
    const updateScene = vi.fn();
    const scrollToContent = vi.fn();
    attachApi(adapter, {
      getSceneElements: () => [card],
      updateScene,
      scrollToContent,
    });
    await adapter.setCustomData('projection-1', {
      artifactId: 'art_00000000000000000000000002',
      projectionId: 'projection-1',
    });
    await adapter.focusArtifact('art_00000000000000000000000001');
    expect(updateScene).toHaveBeenCalled();
    expect(scrollToContent).toHaveBeenCalledWith([card]);
  });

  it('TC-029 reports supported capabilities and exports a JSON scene', async () => {
    const adapter = new ExcalidrawCanvasAdapter();
    attachApi(adapter, {
      getSceneElements: () => [],
      getAppState: () => appState(),
      getFiles: () => ({}),
    });
    expect(adapter.capabilities()).toEqual({
      freehand: true,
      frames: true,
      customShapes: false,
      embeds: true,
      exportSvg: true,
      exportPng: true,
    });
    const blob = await adapter.exportView({}, 'json');
    expect(JSON.parse(await blob.text()).type).toBe('excalidraw');
  });
});
