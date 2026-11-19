import { createElement, useState, useEffect } from 'react';
import type { CanvasAdapter } from './adapter';

export type SketchToolbarProps = {
  adapter: CanvasAdapter | null;
  onPromote: () => void;
};

type SketchTool =
  | 'freedraw'
  | 'rectangle'
  | 'ellipse'
  | 'text'
  | 'sticky-note'
  | 'image';

const TOOL_BUTTONS: { tool: SketchTool; label: string; emoji: string }[] = [
  { tool: 'freedraw', label: 'Pencil (freehand)', emoji: '✏️' },
  { tool: 'rectangle', label: 'Rectangle', emoji: '▭' },
  { tool: 'ellipse', label: 'Ellipse', emoji: '◯' },
  { tool: 'text', label: 'Text', emoji: 'T' },
  { tool: 'sticky-note', label: 'Sticky note', emoji: '🗒' },
  { tool: 'image', label: 'Upload image', emoji: '🖼' },
];

const containerStyle: React.CSSProperties = {
  position: 'absolute',
  top: 12,
  left: '50%',
  transform: 'translateX(-50%)',
  display: 'flex',
  flexDirection: 'row',
  gap: 4,
  padding: '6px 10px',
  background: '#ffffff',
  border: '1px solid #d1d5db',
  borderRadius: 8,
  boxShadow: '0 2px 8px rgba(0,0,0,0.12)',
  zIndex: 100,
  alignItems: 'center',
};

const buttonBase: React.CSSProperties = {
  display: 'inline-flex',
  alignItems: 'center',
  justifyContent: 'center',
  width: 36,
  height: 36,
  border: '1px solid transparent',
  borderRadius: 6,
  cursor: 'pointer',
  fontSize: 18,
  background: 'none',
  padding: 0,
  transition: 'background 0.1s',
};

const activeButton: React.CSSProperties = {
  ...buttonBase,
  background: '#eff6ff',
  border: '1px solid #3b82f6',
};

const dividerStyle: React.CSSProperties = {
  width: 1,
  height: 24,
  background: '#e5e7eb',
  margin: '0 4px',
};

const promoteStyle: React.CSSProperties = {
  ...buttonBase,
  fontSize: 13,
  fontWeight: 600,
  width: 'auto',
  padding: '0 10px',
  letterSpacing: 0,
  color: '#1d4ed8',
  border: '1px solid #3b82f6',
  borderRadius: 6,
  background: '#eff6ff',
  cursor: 'pointer',
};

const promoteDisabledStyle: React.CSSProperties = {
  ...promoteStyle,
  opacity: 0.4,
  cursor: 'default',
};

function activeTool(adapter: CanvasAdapter | null): SketchTool | null {
  // We track it via local state; this is just a placeholder for
  // cases where the adapter would expose its own active-tool query.
  return null;
}

export function SketchToolbar({
  adapter,
  onPromote,
}: SketchToolbarProps): React.ReactElement {
  const [active, setActive] = useState<SketchTool | null>(null);
  const [hasSketchSelected, setHasSketchSelected] = useState(false);

  useEffect(() => {
    if (!adapter) return;
    // Subscribe to selection changes so we can enable/disable the Promote button.
    const unsub = adapter.onSelectionChange((ids) => {
      // The promote button is enabled when any selected element is a sketch.
      // We use a heuristic: if the adapter exposes promoteSelectedSketches and
      // at least one id is selected, optimistically enable; a fuller
      // implementation would inspect customData via adapter.readScene().
      setHasSketchSelected(ids.length > 0);
    });
    return unsub;
  }, [adapter]);

  function handleToolClick(tool: SketchTool): void {
    setActive(tool);

    if (!adapter) return;

    // Map our tool names to Excalidraw tool names and trigger them through
    // the imperative API if available.
    const api = (
      adapter as unknown as {
        api?: { setActiveTool?: (opts: { type: string }) => void };
      }
    ).api;

    if (!api?.setActiveTool) return;

    if (tool === 'sticky-note') {
      // Sticky notes are rectangles with yellow fill — set tool then update
      // scene appState via setActiveTool with rectangle type; colour is set
      // by the user's fill choice in Excalidraw's own toolbar, but we select
      // the rectangle tool here.
      api.setActiveTool({ type: 'rectangle' });
    } else if (tool === 'image') {
      api.setActiveTool({ type: 'image' });
    } else {
      api.setActiveTool({ type: tool });
    }
  }

  function handlePromote(): void {
    if (!hasSketchSelected) return;
    void adapter?.promoteSelectedSketches();
    onPromote();
  }

  return createElement(
    'div',
    { style: containerStyle, role: 'toolbar', 'aria-label': 'Sketch tools' },
    ...TOOL_BUTTONS.map(({ tool, label, emoji }) =>
      createElement(
        'button',
        {
          key: tool,
          type: 'button',
          'aria-label': label,
          'aria-pressed': active === tool,
          style: active === tool ? activeButton : buttonBase,
          onClick: () => handleToolClick(tool),
          title: label,
        },
        emoji,
      ),
    ),
    createElement('div', { style: dividerStyle }),
    createElement(
      'button',
      {
        type: 'button',
        'aria-label': 'Promote sketch to artifact',
        disabled: !hasSketchSelected,
        style: hasSketchSelected ? promoteStyle : promoteDisabledStyle,
        onClick: handlePromote,
        title: 'Promote sketch to artifact',
      },
      'Promote',
    ),
  );
}
