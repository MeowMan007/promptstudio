import type { LayoutDelta } from './adapter';

export type AutoLayoutPolicy = 'free' | 'grid' | 'column' | 'tree';

export type ZoneDefinition = {
  id: string;
  title: string;
  order: number;
  stageBinding: string | null;
  scopeFilter: string[];
  autoLayoutPolicy: AutoLayoutPolicy;
};

export const DEFAULT_PROJECT_ZONES: ZoneDefinition[] = [
  {
    id: 'discovery',
    title: 'Discovery',
    order: 1,
    stageBinding: 'S1_capture',
    scopeFilter: ['brief', 'idea', 'problem', 'persona'],
    autoLayoutPolicy: 'free',
  },
  {
    id: 'requirements',
    title: 'Requirements',
    order: 2,
    stageBinding: 'S2_define',
    scopeFilter: ['user_story', 'requirement', 'constraint', 'decision'],
    autoLayoutPolicy: 'grid',
  },
  {
    id: 'ux',
    title: 'UX',
    order: 3,
    stageBinding: 'S3_experience',
    scopeFilter: ['user_flow', 'screen', 'interaction'],
    autoLayoutPolicy: 'grid',
  },
  {
    id: 'architecture',
    title: 'Architecture',
    order: 4,
    stageBinding: 'S4_architecture',
    scopeFilter: ['component', 'integration'],
    autoLayoutPolicy: 'tree',
  },
  {
    id: 'data-api',
    title: 'Data / API',
    order: 5,
    stageBinding: 'S4_architecture',
    scopeFilter: ['data_entity', 'api_endpoint', 'event_contract'],
    autoLayoutPolicy: 'grid',
  },
  {
    id: 'prompt-lab',
    title: 'Prompt Lab',
    order: 6,
    stageBinding: 'S5_prompts',
    scopeFilter: ['prompt', 'prompt_flow', 'skill'],
    autoLayoutPolicy: 'grid',
  },
  {
    id: 'quality',
    title: 'Quality',
    order: 7,
    stageBinding: 'S6_quality',
    scopeFilter: ['risk', 'test_case', 'evaluation_case'],
    autoLayoutPolicy: 'grid',
  },
  {
    id: 'delivery',
    title: 'Delivery',
    order: 8,
    stageBinding: 'S7_delivery',
    scopeFilter: ['epic', 'task', 'milestone'],
    autoLayoutPolicy: 'tree',
  },
  {
    id: 'open-questions',
    title: 'Open Questions',
    order: 9,
    stageBinding: null,
    scopeFilter: ['question', 'issue'],
    autoLayoutPolicy: 'column',
  },
];

export type LayoutItem = Pick<
  LayoutDelta,
  'projectionId' | 'artifactId' | 'x' | 'y' | 'width' | 'height' | 'z'
>;

export function snapCoordinate(value: number, gridSize = 16): number {
  if (!Number.isFinite(value) || !Number.isFinite(gridSize) || gridSize <= 0) {
    throw new RangeError(
      'Coordinate and grid size must be finite; grid size must be positive',
    );
  }
  return Math.round(value / gridSize) * gridSize;
}

export function snapLayout(items: LayoutItem[], gridSize = 16): LayoutDelta[] {
  return items.map((item) => ({
    ...item,
    x: snapCoordinate(item.x, gridSize),
    y: snapCoordinate(item.y, gridSize),
  }));
}

export function autoLayout(
  items: LayoutItem[],
  policy: AutoLayoutPolicy,
  gap = 32,
): LayoutDelta[] {
  if (!Number.isFinite(gap) || gap < 0)
    throw new RangeError('Layout gap must be nonnegative');
  const ordered = [...items].sort(
    (left, right) =>
      left.z - right.z || left.projectionId.localeCompare(right.projectionId),
  );
  if (policy === 'free' || ordered.length === 0)
    return ordered.map((item) => ({ ...item }));
  const cellWidth = Math.max(...ordered.map((item) => item.width));
  const cellHeight = Math.max(...ordered.map((item) => item.height));
  if (policy === 'column') {
    let y = 0;
    return ordered.map((item) => {
      const placed = { ...item, x: 0, y };
      y += item.height + gap;
      return placed;
    });
  }
  if (policy === 'tree') {
    return ordered.map((item, index) => {
      const level = Math.floor(Math.log2(index + 1));
      const firstAtLevel = 2 ** level - 1;
      const position = index - firstAtLevel;
      return {
        ...item,
        x: (position - (2 ** level - 1) / 2) * (cellWidth + gap),
        y: level * (cellHeight + gap),
      };
    });
  }
  const columns = Math.ceil(Math.sqrt(ordered.length));
  return ordered.map((item, index) => ({
    ...item,
    x: (index % columns) * (cellWidth + gap),
    y: Math.floor(index / columns) * (cellHeight + gap),
  }));
}

export type MinimapItem = {
  projectionId: string;
  artifactId: string | null;
  x: number;
  y: number;
  width: number;
  height: number;
};

export function minimapItems(
  items: LayoutItem[],
  width = 160,
  height = 100,
  padding = 4,
): MinimapItem[] {
  if (items.length === 0) return [];
  const minX = Math.min(...items.map((item) => item.x));
  const minY = Math.min(...items.map((item) => item.y));
  const maxX = Math.max(...items.map((item) => item.x + item.width));
  const maxY = Math.max(...items.map((item) => item.y + item.height));
  const scale = Math.min(
    (width - 2 * padding) / Math.max(maxX - minX, 1),
    (height - 2 * padding) / Math.max(maxY - minY, 1),
  );
  return items.map((item) => ({
    projectionId: item.projectionId,
    artifactId: item.artifactId,
    x: padding + (item.x - minX) * scale,
    y: padding + (item.y - minY) * scale,
    width: Math.max(2, item.width * scale),
    height: Math.max(2, item.height * scale),
  }));
}
