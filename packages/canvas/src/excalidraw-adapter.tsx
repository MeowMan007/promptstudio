import {
  CaptureUpdateAction,
  Excalidraw,
  convertToExcalidrawElements,
  exportToBlob,
  exportToSvg,
  serializeAsJSON,
} from '@excalidraw/excalidraw';
import type {
  ExcalidrawElement,
  FileId,
} from '@excalidraw/excalidraw/element/types';
import type { ExcalidrawElementSkeleton } from '@excalidraw/excalidraw/data/transform';
import type {
  AppState,
  BinaryFileData,
  ExcalidrawImperativeAPI,
} from '@excalidraw/excalidraw/types';
import { createElement } from 'react';
import { createRoot, type Root } from 'react-dom/client';

import type {
  ArtifactCustomData,
  AssetRef,
  CanvasAdapter,
  ConnectIntent,
  ExportFormat,
  LayoutDelta,
  MountOptions,
  Point,
  ProjectionDelta,
  ProjectionRecord,
  PromoteSketchIntent,
  SceneSnapshot,
  SemanticEditIntent,
  TypedCardData,
  Unsubscribe,
  ViewRef,
  Viewport,
} from './adapter';

import '@excalidraw/excalidraw/index.css';
import './canvas-accessibility.css';

const layoutProperties = [
  'x',
  'y',
  'width',
  'height',
  'angle',
  'strokeColor',
  'backgroundColor',
  'fillStyle',
  'strokeWidth',
  'roughness',
  'opacity',
] as const;

export function projectionToElement(
  projection: ProjectionRecord,
): ExcalidrawElementSkeleton {
  const label = cardText(projection);
  return {
    type: 'rectangle',
    id: projection.projectionId,
    x: projection.x,
    y: projection.y,
    width: projection.width,
    height: projection.height,
    strokeColor: '#111827',
    backgroundColor: '#ffffff',
    fillStyle: 'solid',
    strokeWidth: 1,
    roughness: 0,
    opacity: 100,
    label: {
      text: label,
      fontSize: 16,
      textAlign: 'left',
      verticalAlign: 'top',
      x: projection.x + 12,
      y: projection.y + 12,
      customData: {
        artifactId: projection.artifactId,
        projectionId: projection.projectionId,
        semanticHash: projection.semanticHash,
        accessibleName: accessibleNameForProjection(projection),
      },
    },
    customData: {
      artifactId: projection.artifactId,
      projectionId: projection.projectionId,
      semanticHash: projection.semanticHash,
      kind: projection.kind,
      z: projection.z,
      accessibleName: accessibleNameForProjection(projection),
    },
  };
}

function cardText(projection: ProjectionRecord): string {
  const card = projection.card;
  if (!card) return projection.title;
  const lines = [
    `${typeGlyph(card.artifactType)} ${card.artifactType.toUpperCase()}  ${card.alias}  [${card.status.toUpperCase()}]`,
    projection.title,
  ];
  if (card.bodyPreview) lines.push(card.bodyPreview);
  if (card.badges?.length)
    lines.push(card.badges.map((badge) => `[${badge}]`).join('  '));
  if (card.relationSummary?.length)
    lines.push(card.relationSummary.join('  ·  '));
  if (card.provenanceLabel || card.revision !== undefined) {
    lines.push(
      [
        card.provenanceLabel,
        card.revision === undefined ? undefined : `rev ${card.revision}`,
      ]
        .filter(Boolean)
        .join('  ·  '),
    );
  }
  return lines.join('\n');
}

function typeGlyph(artifactType: string): string {
  const glyphs: Record<string, string> = {
    requirement: '◆',
    screen: '▣',
    component: '◈',
    task: '✓',
    decision: '●',
  };
  return glyphs[artifactType] ?? '■';
}

export function accessibleNameForProjection(
  projection: ProjectionRecord,
): string {
  const card: TypedCardData | undefined = projection.card;
  if (!card) return projection.title;
  return [
    `${card.artifactType} ${card.alias}`,
    projection.title,
    `status ${card.status}`,
    ...(card.badges ?? []),
    ...(card.relationSummary ?? []),
    card.provenanceLabel,
    card.revision === undefined ? undefined : `revision ${card.revision}`,
  ]
    .filter(Boolean)
    .join(', ');
}

function asRecord(element: ExcalidrawElement): Record<string, unknown> {
  return element as unknown as Record<string, unknown>;
}

function customDataOf(element: ExcalidrawElement): ArtifactCustomData | null {
  const value = asRecord(element).customData;
  if (!value || typeof value !== 'object') return null;
  const data = value as Record<string, unknown>;
  if (typeof data.projectionId !== 'string') return null;
  return {
    artifactId: typeof data.artifactId === 'string' ? data.artifactId : null,
    projectionId: data.projectionId,
    ...(typeof data.semanticHash === 'string'
      ? { semanticHash: data.semanticHash }
      : {}),
  };
}

function layoutOf(element: ExcalidrawElement): LayoutDelta | null {
  const custom = customDataOf(element);
  if (!custom) return null;
  const record = asRecord(element);
  return {
    projectionId: custom.projectionId,
    artifactId: custom.artifactId,
    x: Number(record.x ?? 0),
    y: Number(record.y ?? 0),
    width: Number(record.width ?? 0),
    height: Number(record.height ?? 0),
    z: Number(
      (record.customData as Record<string, unknown> | undefined)?.z ?? 0,
    ),
  };
}

function selectedIds(
  appState: AppState,
  elements: readonly ExcalidrawElement[],
): string[] {
  const selected = appState.selectedElementIds;
  return elements
    .filter((element) => selected[element.id])
    .map((element) => customDataOf(element)?.artifactId)
    .filter((id): id is string => Boolean(id));
}

export class ExcalidrawCanvasAdapter implements CanvasAdapter {
  private root: Root | null = null;
  private api: ExcalidrawImperativeAPI | null = null;
  private viewOnly = false;
  private projectionCards = new Map<string, ProjectionRecord>();
  private previous = new Map<string, ExcalidrawElement>();
  private previousSelection = '';
  private applyingProjection = false;
  private pendingLayouts = new Map<string, LayoutDelta>();
  private layoutTimer: ReturnType<typeof setTimeout> | null = null;
  private layoutListeners = new Set<(delta: LayoutDelta[]) => void>();
  private semanticListeners = new Set<(intent: SemanticEditIntent) => void>();
  private connectListeners = new Set<(intent: ConnectIntent) => void>();
  private promoteSketchListeners = new Set<
    (intent: PromoteSketchIntent) => void
  >();
  private selectionListeners = new Set<(ids: string[]) => void>();
  private viewportListeners = new Set<(viewport: Viewport) => void>();
  private unsubscribeViewport: (() => void) | null = null;

  async mount(element: HTMLElement, options: MountOptions): Promise<void> {
    this.unmount();
    this.root = createRoot(element);
    this.viewOnly = options.viewOnly ?? false;
    this.renderRoot();
    const startedAt = performance.now();
    await new Promise<void>((resolve, reject) => {
      const waitForApi = () => {
        if (this.api) {
          resolve();
          return;
        }
        if (performance.now() - startedAt > 5000) {
          reject(new Error('Excalidraw did not finish mounting'));
          return;
        }
        requestAnimationFrame(waitForApi);
      };
      requestAnimationFrame(waitForApi);
    });
  }

  unmount(): void {
    this.unsubscribeViewport?.();
    this.unsubscribeViewport = null;
    if (this.layoutTimer !== null) clearTimeout(this.layoutTimer);
    this.layoutTimer = null;
    this.pendingLayouts.clear();
    this.api = null;
    this.root?.unmount();
    this.root = null;
    this.previous.clear();
    this.previousSelection = '';
    this.projectionCards.clear();
  }

  async loadScene(
    projections: ProjectionRecord[],
    assets: AssetRef[],
  ): Promise<void> {
    const api = this.requireApi();
    const elements = convertToExcalidrawElements(
      projections.map(projectionToElement),
      { regenerateIds: false },
    );
    this.projectionCards = new Map(
      projections.map((projection) => [projection.projectionId, projection]),
    );
    this.renderRoot();
    this.applyingProjection = true;
    api.updateScene({ elements, captureUpdate: CaptureUpdateAction.NEVER });
    if (assets.length) {
      api.addFiles(
        assets.map((asset) => ({
          id: asset.id as FileId,
          dataURL: asset.dataUrl as BinaryFileData['dataURL'],
          mimeType: asset.mimeType as BinaryFileData['mimeType'],
          created: asset.created,
        })),
      );
    }
    this.previous = new Map(elements.map((item) => [item.id, item]));
    queueMicrotask(() => {
      this.applyingProjection = false;
    });
  }

  async applyProjectionDelta(delta: ProjectionDelta[]): Promise<void> {
    const api = this.requireApi();
    const byId = new Map(
      delta
        .filter(
          (
            change,
          ): change is Extract<ProjectionDelta, { operation: 'upsert' }> =>
            change.operation === 'upsert',
        )
        .map((change) => [change.projection.projectionId, change.projection]),
    );
    const removedIds = new Set(
      delta
        .filter(
          (
            change,
          ): change is Extract<ProjectionDelta, { operation: 'remove' }> =>
            change.operation === 'remove',
        )
        .map((change) => change.projectionId),
    );
    const preserved = api
      .getSceneElements()
      .filter((item) => !removedIds.has(item.id) && !byId.has(item.id));
    const converted = convertToExcalidrawElements(
      [...byId.values()].map(projectionToElement),
      { regenerateIds: false },
    );
    const elements = [...preserved, ...converted];
    for (const change of delta) {
      if (change.operation === 'remove')
        this.projectionCards.delete(change.projectionId);
      else
        this.projectionCards.set(
          change.projection.projectionId,
          change.projection,
        );
    }
    this.renderRoot();
    this.applyingProjection = true;
    api.updateScene({
      elements,
      captureUpdate: CaptureUpdateAction.NEVER,
    });
    this.previous = new Map(elements.map((item) => [item.id, item]));
    queueMicrotask(() => {
      this.applyingProjection = false;
    });
  }

  async readScene(): Promise<SceneSnapshot> {
    const api = this.requireApi();
    const appState = api.getAppState();
    return {
      serialized: serializeAsJSON(
        api.getSceneElementsIncludingDeleted(),
        appState,
        api.getFiles(),
        'local',
      ),
      viewport: {
        x: appState.scrollX,
        y: appState.scrollY,
        zoom: appState.zoom.value,
      },
    };
  }

  getArtifactIdAt(point: Point): string | null {
    const elements = this.requireApi()
      .getSceneElements()
      .filter((element) => {
        const record = asRecord(element);
        return (
          point.x >= Number(record.x) &&
          point.x <= Number(record.x) + Number(record.width) &&
          point.y >= Number(record.y) &&
          point.y <= Number(record.y) + Number(record.height)
        );
      });
    const match = elements.at(-1);
    return match ? (customDataOf(match)?.artifactId ?? null) : null;
  }

  getSelectedArtifactIds(): string[] {
    const api = this.requireApi();
    return selectedIds(api.getAppState(), api.getSceneElements());
  }

  async setCustomData(
    elementId: string,
    data: ArtifactCustomData,
  ): Promise<void> {
    const api = this.requireApi();
    const element = api
      .getSceneElements()
      .find((item) => item.id === elementId);
    if (!element) return;
    const record = asRecord(element);
    api.updateScene({
      elements: [
        {
          ...element,
          customData: { ...(record.customData as object | undefined), ...data },
        } as ExcalidrawElement,
      ],
      captureUpdate: CaptureUpdateAction.NEVER,
    });
  }

  onLayoutChange(callback: (delta: LayoutDelta[]) => void): Unsubscribe {
    this.layoutListeners.add(callback);
    return () => this.layoutListeners.delete(callback);
  }

  onSemanticEdit(callback: (intent: SemanticEditIntent) => void): Unsubscribe {
    this.semanticListeners.add(callback);
    return () => this.semanticListeners.delete(callback);
  }

  onConnect(callback: (intent: ConnectIntent) => void): Unsubscribe {
    this.connectListeners.add(callback);
    return () => this.connectListeners.delete(callback);
  }

  onPromoteSketch(
    callback: (intent: PromoteSketchIntent) => void,
  ): Unsubscribe {
    this.promoteSketchListeners.add(callback);
    return () => this.promoteSketchListeners.delete(callback);
  }

  async promoteSelectedSketches(): Promise<void> {
    const api = this.requireApi();
    const selected = api.getAppState().selectedElementIds;
    const sketchIds = api
      .getSceneElements()
      .filter((element) => {
        const custom = asRecord(element).customData as
          Record<string, unknown> | undefined;
        return selected[element.id] && custom?.kind === 'sketch';
      })
      .map((element) => customDataOf(element)?.projectionId)
      .filter((id): id is string => Boolean(id));
    if (!sketchIds.length) return;
    const scene = await this.readScene();
    for (const projectionId of sketchIds) {
      this.promoteSketchListeners.forEach((listener) =>
        listener({ projectionId, sceneJson: scene.serialized }),
      );
    }
  }

  onSelectionChange(callback: (ids: string[]) => void): Unsubscribe {
    this.selectionListeners.add(callback);
    return () => this.selectionListeners.delete(callback);
  }

  onViewportChange(callback: (viewport: Viewport) => void): Unsubscribe {
    this.viewportListeners.add(callback);
    return () => this.viewportListeners.delete(callback);
  }

  capabilities() {
    return {
      freehand: true,
      frames: true,
      customShapes: false,
      embeds: true,
      exportSvg: true,
      exportPng: true,
    };
  }

  async exportView(view: ViewRef, format: ExportFormat): Promise<Blob> {
    const api = this.requireApi();
    const all = api.getSceneElements().filter((element) => {
      const custom = customDataOf(element);
      const ids = view.projectionIds ?? [];
      const artifactIds = view.artifactIds ?? [];
      if (!ids.length && !artifactIds.length) return true;
      return Boolean(
        custom &&
        (ids.includes(custom.projectionId) ||
          (custom.artifactId && artifactIds.includes(custom.artifactId))),
      );
    });
    if (format === 'json') {
      const content = serializeAsJSON(
        all,
        api.getAppState(),
        api.getFiles(),
        'local',
      );
      return new Blob([content], { type: 'application/json' });
    }
    if (format === 'svg') {
      const svg = await exportToSvg({
        elements: all,
        appState: api.getAppState(),
        files: api.getFiles(),
      });
      return new Blob([svg.outerHTML], { type: 'image/svg+xml' });
    }
    return exportToBlob({
      elements: all,
      appState: api.getAppState(),
      files: api.getFiles(),
      mimeType: 'image/png',
    });
  }

  async focusArtifact(artifactId: string): Promise<void> {
    const api = this.requireApi();
    const matches = api
      .getSceneElements()
      .filter((element) => customDataOf(element)?.artifactId === artifactId);
    api.updateScene({
      appState: {
        selectedElementIds: Object.fromEntries(
          matches.map((element) => [element.id, true]),
        ),
      },
      captureUpdate: CaptureUpdateAction.NEVER,
    });
    api.scrollToContent(matches);
  }

  private handleChange(
    elements: readonly ExcalidrawElement[],
    appState: AppState,
  ): void {
    if (this.applyingProjection) return;
    const current = new Map(elements.map((element) => [element.id, element]));
    for (const element of elements) {
      const custom = customDataOf(element);
      const before = this.previous.get(element.id);
      if (before && custom?.artifactId) {
        const oldRecord = asRecord(before);
        const nextRecord = asRecord(element);
        if (
          oldRecord.text !== nextRecord.text &&
          typeof nextRecord.text === 'string'
        ) {
          this.semanticListeners.forEach((listener) =>
            listener({
              operation: 'update_title',
              artifactId: custom.artifactId!,
              value: nextRecord.text as string,
            }),
          );
        }
        if (
          layoutProperties.some(
            (property) => oldRecord[property] !== nextRecord[property],
          )
        ) {
          const layout = layoutOf(element);
          if (layout) this.queueLayout(layout);
        }
      }
      const record = asRecord(element);
      const start = record.startBinding as
        { elementId?: string } | null | undefined;
      const end = record.endBinding as
        { elementId?: string } | null | undefined;
      const oldRecord = before ? asRecord(before) : null;
      const oldStart = oldRecord?.startBinding as
        { elementId?: string } | null | undefined;
      const oldEnd = oldRecord?.endBinding as
        { elementId?: string } | null | undefined;
      const bindingChanged =
        !before ||
        oldStart?.elementId !== start?.elementId ||
        oldEnd?.elementId !== end?.elementId;
      if (
        element.type === 'arrow' &&
        bindingChanged &&
        start?.elementId &&
        end?.elementId
      ) {
        const source = current.get(start.elementId);
        const target = current.get(end.elementId);
        const sourceId = source ? customDataOf(source)?.artifactId : null;
        const targetId = target ? customDataOf(target)?.artifactId : null;
        if (sourceId && targetId) {
          this.connectListeners.forEach((listener) =>
            listener({
              sourceArtifactId: sourceId,
              targetArtifactId: targetId,
              edgeType: 'untyped',
            }),
          );
        }
      }
    }
    const selection = selectedIds(appState, elements).sort().join(',');
    if (selection !== this.previousSelection) {
      this.previousSelection = selection;
      const ids = selection ? selection.split(',') : [];
      this.selectionListeners.forEach((listener) => listener(ids));
    }
    this.previous = current;
  }

  private queueLayout(delta: LayoutDelta): void {
    this.pendingLayouts.set(delta.projectionId, delta);
    if (this.layoutTimer !== null) return;
    this.layoutTimer = setTimeout(() => {
      const batch = [...this.pendingLayouts.values()];
      this.pendingLayouts.clear();
      this.layoutTimer = null;
      if (batch.length)
        this.layoutListeners.forEach((listener) => listener(batch));
    }, 100);
  }

  private renderRoot(): void {
    if (!this.root) return;
    const canvas = createElement(Excalidraw, {
      viewModeEnabled: this.viewOnly,
      excalidrawAPI: (api: ExcalidrawImperativeAPI) => {
        this.api = api;
        this.unsubscribeViewport = api.onScrollChange((x, y, zoom) => {
          const viewport = { x, y, zoom: zoom.value };
          this.viewportListeners.forEach((listener) => listener(viewport));
        });
      },
      onChange: (elements, appState) => this.handleChange(elements, appState),
    });
    const accessibleCards = [...this.projectionCards.values()]
      .filter((projection) => projection.artifactId && projection.card)
      .map((projection) =>
        createElement(
          'button',
          {
            key: projection.projectionId,
            type: 'button',
            'aria-label': accessibleNameForProjection(projection),
            'data-projection-id': projection.projectionId,
            onFocus: () => {
              if (projection.artifactId)
                void this.focusArtifact(projection.artifactId);
            },
            onClick: () => {
              if (projection.artifactId)
                void this.focusArtifact(projection.artifactId);
            },
          },
          accessibleNameForProjection(projection),
        ),
      );
    const accessibilityLayer = createElement(
      'div',
      {
        className: 'canvas-accessibility-list',
        role: 'list',
        'aria-label': 'Canvas artifact cards',
      },
      ...accessibleCards,
    );
    this.root.render(
      createElement(
        'div',
        { className: 'canvas-adapter-root' },
        canvas,
        accessibilityLayer,
      ),
    );
  }

  private requireApi(): ExcalidrawImperativeAPI {
    if (!this.api) throw new Error('Canvas adapter is not mounted');
    return this.api;
  }
}
