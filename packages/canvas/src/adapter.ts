export type Point = { x: number; y: number };

export type Viewport = { x: number; y: number; zoom: number };

export type ArtifactCustomData = {
  artifactId: string | null;
  projectionId: string;
  semanticHash?: string;
};

export type ProjectionRecord = {
  projectionId: string;
  artifactId: string | null;
  kind: 'card' | 'sketch';
  x: number;
  y: number;
  width: number;
  height: number;
  z: number;
  title: string;
  semanticHash?: string;
  card?: TypedCardData;
};

export type TypedCardData = {
  artifactType: string;
  alias: string;
  status: string;
  bodyPreview?: string;
  badges?: string[];
  relationSummary?: string[];
  provenanceLabel?: string;
  revision?: number;
};

export type ProjectionDelta =
  | { operation: 'upsert'; projection: ProjectionRecord }
  | { operation: 'remove'; projectionId: string };

export type LayoutDelta = {
  projectionId: string;
  artifactId: string | null;
  x: number;
  y: number;
  width: number;
  height: number;
  z: number;
};

export type SemanticEditIntent = {
  operation: 'update_title';
  artifactId: string;
  value: string;
};

export type ConnectIntent = {
  sourceArtifactId: string;
  targetArtifactId: string;
  edgeType: 'untyped';
};

export type PromoteSketchIntent = {
  projectionId: string;
  sceneJson: string;
};

export type AssetRef = {
  id: string;
  dataUrl: string;
  mimeType: string;
  created: number;
};
export type ViewRef = { projectionIds?: string[]; artifactIds?: string[] };
export type ExportFormat = 'svg' | 'png' | 'json';
export type MountOptions = { viewOnly?: boolean };
export type SceneSnapshot = { serialized: string; viewport: Viewport };
export type Unsubscribe = () => void;

export type CanvasCapabilities = {
  freehand: boolean;
  frames: boolean;
  customShapes: boolean;
  embeds: boolean;
  exportSvg: boolean;
  exportPng: boolean;
};

export interface CanvasAdapter {
  mount(element: HTMLElement, options: MountOptions): Promise<void>;
  unmount(): void;
  loadScene(projections: ProjectionRecord[], assets: AssetRef[]): Promise<void>;
  applyProjectionDelta(delta: ProjectionDelta[]): Promise<void>;
  readScene(): Promise<SceneSnapshot>;
  getArtifactIdAt(point: Point): string | null;
  getSelectedArtifactIds(): string[];
  setCustomData(elementId: string, data: ArtifactCustomData): Promise<void>;
  onLayoutChange(callback: (delta: LayoutDelta[]) => void): Unsubscribe;
  onSemanticEdit(callback: (intent: SemanticEditIntent) => void): Unsubscribe;
  onConnect(callback: (intent: ConnectIntent) => void): Unsubscribe;
  onPromoteSketch(callback: (intent: PromoteSketchIntent) => void): Unsubscribe;
  promoteSelectedSketches(): Promise<void>;
  onSelectionChange(callback: (ids: string[]) => void): Unsubscribe;
  onViewportChange(callback: (viewport: Viewport) => void): Unsubscribe;
  capabilities(): CanvasCapabilities;
  exportView(view: ViewRef, format: ExportFormat): Promise<Blob>;
  focusArtifact(artifactId: string): Promise<void>;
}
