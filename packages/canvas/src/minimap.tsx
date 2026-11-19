import { createElement } from 'react';

import { minimapItems, type LayoutItem } from './layout';

export type CanvasMinimapProps = {
  items: LayoutItem[];
  width?: number;
  height?: number;
  onFocusArtifact?: (artifactId: string) => void;
};

export function CanvasMinimap({
  items,
  width = 160,
  height = 100,
  onFocusArtifact,
}: CanvasMinimapProps) {
  const shapes = minimapItems(items, width, height);
  return createElement(
    'svg',
    {
      role: 'img',
      'aria-label': 'Canvas minimap',
      viewBox: `0 0 ${width} ${height}`,
      width,
      height,
      className: 'canvas-minimap',
    },
    createElement('rect', {
      x: 0,
      y: 0,
      width,
      height,
      fill: '#fff',
      stroke: '#111827',
    }),
    ...shapes.map((shape) =>
      createElement('rect', {
        key: shape.projectionId,
        x: shape.x,
        y: shape.y,
        width: shape.width,
        height: shape.height,
        fill: shape.artifactId ? '#6b7280' : '#fff',
        stroke: '#111827',
        tabIndex: shape.artifactId ? 0 : undefined,
        role: shape.artifactId ? 'button' : undefined,
        'aria-label': shape.artifactId
          ? `Focus ${shape.artifactId}`
          : undefined,
        onClick: () => {
          if (shape.artifactId) onFocusArtifact?.(shape.artifactId);
        },
      }),
    ),
  );
}
