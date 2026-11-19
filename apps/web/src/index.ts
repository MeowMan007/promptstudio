/**
 * Prompt Studio — apps/web entry point.
 * Composes: WorkspaceShell + OutlinePanel + InspectorPanel + CommandPalette +
 * FocusEditor + CanvasAdapter + SkipNav + LiveRegion.
 *
 * This module exports the top-level <App> component and re-exports all
 * sub-components so the web app package is a single import surface.
 */
export { WorkspaceShell } from './shell';
export type { WorkspaceShellProps, PanelId } from './shell';

export { OutlinePanel } from './outline';
export type { OutlineItem, OutlinePanelProps } from './outline';

export { InspectorPanel } from './inspector';
export type {
  InspectorField,
  InspectorPanelProps,
  FieldSchema,
  ProvenanceInfo,
  RelationEntry,
} from './inspector';

export { CommandPalette, useCommandPalette } from './command-palette';
export type { CommandItem, CommandPaletteProps } from './command-palette';

export { FocusEditor } from './focus-editor';
export type { FocusEditorProps, FocusEditorMode } from './focus-editor';

export {
  SkipNav,
  useFocusTrap,
  useLiveAnnouncer,
  useGlobalShortcuts,
  contrastRatio,
  passesWCAG_AA,
} from './a11y';

export { color, space, radius, zIndex, fontSize, fontFamily } from './tokens';
