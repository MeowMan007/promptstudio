/**
 * TSK-034: Semantic outline / tree view with filters.
 * Shows all artifacts in a project, keyboard navigable, sortable, with
 * type/status filter chips. Parity with canvas (same artifact set).
 */
import { createElement, useState, useCallback, useMemo, useRef, type KeyboardEvent } from 'react';
import { color, space, fontSize, fontFamily, radius } from './tokens';

// ── Types ─────────────────────────────────────────────────────────────────────

export type OutlineItem = {
  id: string;
  alias: string;
  title: string;
  type: string;
  status: string;
  tags?: string[];
  /** Child item ids for tree nesting */
  childIds?: string[];
  parentId?: string | null;
};

export type OutlinePanelProps = {
  items: OutlineItem[];
  selectedId: string | null;
  onSelect: (id: string) => void;
  onFocus?: (id: string) => void;
};

// ── Helpers ───────────────────────────────────────────────────────────────────

const TYPE_GLYPHS: Record<string, string> = {
  requirement: '◆',
  screen: '▣',
  component: '◈',
  task: '✓',
  decision: '●',
  brief: '☰',
  persona: '◎',
  user_story: '◇',
  risk: '⚠',
  test_case: '⬡',
  prompt: '⟨⟩',
  skill: '⚙',
};

const STATUS_COLORS: Record<string, string> = {
  draft: color.statusDraft,
  in_progress: color.statusInProgress,
  review: color.statusReview,
  approved: color.statusApproved,
  deprecated: color.statusDeprecated,
};

function typeGlyph(type: string): string {
  return TYPE_GLYPHS[type] ?? '■';
}

function statusColor(status: string): string {
  return STATUS_COLORS[status] ?? color.textSubtle;
}

// ── Filter bar ────────────────────────────────────────────────────────────────

type FilterState = { type: string | null; status: string | null; query: string };

function FilterBar({
  types,
  statuses,
  filter,
  onChange,
}: {
  types: string[];
  statuses: string[];
  filter: FilterState;
  onChange: (f: FilterState) => void;
}) {
  const chipStyle = (active: boolean): React.CSSProperties => ({
    display: 'inline-flex',
    alignItems: 'center',
    padding: `2px ${space.sm}px`,
    borderRadius: radius.pill,
    border: `1px solid ${active ? color.primary : color.borderStrong}`,
    background: active ? '#eff6ff' : color.bg,
    color: active ? color.primary : color.textMuted,
    fontSize: fontSize.xs,
    cursor: 'pointer',
    fontFamily: fontFamily.sans,
    fontWeight: active ? 600 : 400,
    whiteSpace: 'nowrap',
  });

  return createElement(
    'div',
    {
      style: {
        padding: `${space.sm}px ${space.md}px`,
        borderBottom: `1px solid ${color.border}`,
        display: 'flex',
        flexDirection: 'column',
        gap: space.xs,
      },
    },
    // Search input
    createElement('input', {
      type: 'search',
      placeholder: 'Filter…',
      value: filter.query,
      'aria-label': 'Filter outline',
      onChange: (e: React.ChangeEvent<HTMLInputElement>) =>
        onChange({ ...filter, query: e.target.value }),
      style: {
        width: '100%',
        boxSizing: 'border-box',
        padding: `${space.xs}px ${space.sm}px`,
        border: `1px solid ${color.borderStrong}`,
        borderRadius: radius.md,
        fontSize: fontSize.base,
        fontFamily: fontFamily.sans,
        outline: 'none',
        background: color.bg,
      },
    }),
    // Type chips
    createElement(
      'div',
      { style: { display: 'flex', flexWrap: 'wrap' as const, gap: space.xs } },
      createElement(
        'button',
        {
          type: 'button',
          style: chipStyle(!filter.type),
          onClick: () => onChange({ ...filter, type: null }),
        },
        'All types',
      ),
      ...types.map((t) =>
        createElement(
          'button',
          {
            key: t,
            type: 'button',
            style: chipStyle(filter.type === t),
            onClick: () => onChange({ ...filter, type: filter.type === t ? null : t }),
          },
          `${typeGlyph(t)} ${t}`,
        ),
      ),
    ),
    // Status chips
    createElement(
      'div',
      { style: { display: 'flex', flexWrap: 'wrap' as const, gap: space.xs } },
      createElement(
        'button',
        {
          type: 'button',
          style: chipStyle(!filter.status),
          onClick: () => onChange({ ...filter, status: null }),
        },
        'All statuses',
      ),
      ...statuses.map((s) =>
        createElement(
          'button',
          {
            key: s,
            type: 'button',
            style: { ...chipStyle(filter.status === s), borderColor: statusColor(s), color: filter.status === s ? statusColor(s) : color.textMuted },
            onClick: () => onChange({ ...filter, status: filter.status === s ? null : s }),
          },
          s,
        ),
      ),
    ),
  );
}

// ── Outline row ───────────────────────────────────────────────────────────────

function OutlineRow({
  item,
  selected,
  depth,
  onSelect,
  onKeyDown,
  rowRef,
}: {
  item: OutlineItem;
  selected: boolean;
  depth: number;
  onSelect: () => void;
  onKeyDown: (e: KeyboardEvent<HTMLDivElement>) => void;
  rowRef?: React.Ref<HTMLDivElement>;
}) {
  return createElement(
    'div',
    {
      ref: rowRef,
      role: 'treeitem',
      tabIndex: selected ? 0 : -1,
      'aria-selected': selected,
      'aria-label': `${item.type} ${item.alias}: ${item.title}, status ${item.status}`,
      onClick: onSelect,
      onKeyDown,
      style: {
        display: 'flex',
        alignItems: 'center',
        gap: space.xs,
        padding: `${space.xs + 1}px ${space.sm}px`,
        paddingLeft: space.sm + depth * 16,
        background: selected ? '#eff6ff' : 'transparent',
        cursor: 'pointer',
        borderLeft: selected ? `2px solid ${color.primary}` : '2px solid transparent',
        outline: 'none',
        userSelect: 'none',
      },
    },
    // Type glyph
    createElement(
      'span',
      {
        'aria-hidden': 'true',
        style: { fontSize: fontSize.sm, color: color.textMuted, width: 14, textAlign: 'center', flexShrink: 0 },
      },
      typeGlyph(item.type),
    ),
    // Alias badge
    createElement(
      'span',
      {
        style: {
          fontSize: fontSize.xs,
          color: color.textSubtle,
          fontFamily: fontFamily.mono,
          flexShrink: 0,
          minWidth: 36,
        },
      },
      item.alias,
    ),
    // Title
    createElement(
      'span',
      {
        style: {
          flex: 1,
          fontSize: fontSize.base,
          color: color.text,
          overflow: 'hidden',
          textOverflow: 'ellipsis',
          whiteSpace: 'nowrap',
        },
      },
      item.title,
    ),
    // Status dot
    createElement('span', {
      'aria-hidden': 'true',
      title: item.status,
      style: {
        width: 7,
        height: 7,
        borderRadius: '50%',
        background: statusColor(item.status),
        flexShrink: 0,
      },
    }),
  );
}

// ── Outline panel ─────────────────────────────────────────────────────────────

export function OutlinePanel({ items, selectedId, onSelect, onFocus }: OutlinePanelProps) {
  const [filter, setFilter] = useState<FilterState>({ type: null, status: null, query: '' });
  const rowRefs = useRef<Map<string, HTMLDivElement>>(new Map());

  const types = useMemo(() => [...new Set(items.map((i) => i.type))].sort(), [items]);
  const statuses = useMemo(() => [...new Set(items.map((i) => i.status))].sort(), [items]);

  const visible = useMemo(
    () =>
      items.filter((item) => {
        if (filter.type && item.type !== filter.type) return false;
        if (filter.status && item.status !== filter.status) return false;
        if (filter.query) {
          const q = filter.query.toLowerCase();
          return (
            item.title.toLowerCase().includes(q) ||
            item.alias.toLowerCase().includes(q) ||
            item.type.toLowerCase().includes(q)
          );
        }
        return true;
      }),
    [items, filter],
  );

  const handleKeyDown = useCallback(
    (id: string, e: KeyboardEvent<HTMLDivElement>) => {
      const idx = visible.findIndex((i) => i.id === id);
      if (e.key === 'ArrowDown' && idx < visible.length - 1) {
        e.preventDefault();
        const next = visible[idx + 1];
        onSelect(next.id);
        rowRefs.current.get(next.id)?.focus();
      } else if (e.key === 'ArrowUp' && idx > 0) {
        e.preventDefault();
        const prev = visible[idx - 1];
        onSelect(prev.id);
        rowRefs.current.get(prev.id)?.focus();
      } else if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        onFocus?.(id);
      }
    },
    [visible, onSelect, onFocus],
  );

  return createElement(
    'div',
    {
      style: { display: 'flex', flexDirection: 'column', height: '100%', fontFamily: fontFamily.sans },
    },
    // Panel header
    createElement(
      'div',
      {
        style: {
          padding: `${space.sm}px ${space.md}px`,
          borderBottom: `1px solid ${color.border}`,
          fontSize: fontSize.sm,
          fontWeight: 700,
          color: color.textMuted,
          textTransform: 'uppercase' as const,
          letterSpacing: '0.07em',
        },
      },
      `Outline (${visible.length})`,
    ),
    createElement(FilterBar, { types, statuses, filter, onChange: setFilter }),
    createElement(
      'div',
      {
        role: 'tree',
        'aria-label': 'Semantic outline',
        style: { flex: 1, overflowY: 'auto' as const },
      },
      visible.length === 0
        ? createElement(
            'div',
            { style: { padding: space.xl, color: color.textSubtle, fontSize: fontSize.base, textAlign: 'center' as const } },
            'No artifacts match the current filter.',
          )
        : visible.map((item) =>
            createElement(OutlineRow, {
              key: item.id,
              item,
              selected: item.id === selectedId,
              depth: 0,
              onSelect: () => onSelect(item.id),
              onKeyDown: (e) => handleKeyDown(item.id, e),
              rowRef: (el: HTMLDivElement | null) => {
                if (el) rowRefs.current.set(item.id, el);
                else rowRefs.current.delete(item.id);
              },
            }),
          ),
    ),
  );
}
