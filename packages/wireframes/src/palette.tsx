/**
 * TSK-029: Wireframe component palette + states matrix UI.
 *
 * PalettePanel — a sidebar panel listing all available control types grouped
 * by category. Users drag or click to place a control on a ScreenRenderer.
 *
 * StatesMatrix — shows a grid of (control × state) combinations so designers
 * can verify every required state is specified. Cells missing state definitions
 * raise a VAL-11-equivalent warning.
 */
import React, { createElement } from 'react';
import type { ControlType, ControlState, ScreenControl } from './types';

// ── Palette data ─────────────────────────────────────────────────────────────

export type PaletteGroup = {
  label: string;
  items: { type: ControlType; label: string; icon: string }[];
};

export const PALETTE_GROUPS: PaletteGroup[] = [
  {
    label: 'Input',
    items: [
      { type: 'input', label: 'Text Input', icon: '▭' },
      { type: 'textarea', label: 'Text Area', icon: '▬' },
      { type: 'checkbox', label: 'Checkbox', icon: '☑' },
      { type: 'radio', label: 'Radio', icon: '◉' },
      { type: 'select', label: 'Select', icon: '⌄' },
    ],
  },
  {
    label: 'Action',
    items: [
      { type: 'button', label: 'Button', icon: '▭' },
      { type: 'link', label: 'Link', icon: '🔗' },
    ],
  },
  {
    label: 'Display',
    items: [
      { type: 'label', label: 'Label', icon: 'T' },
      { type: 'image', label: 'Image', icon: '🖼' },
      { type: 'icon', label: 'Icon', icon: '◎' },
      { type: 'divider', label: 'Divider', icon: '—' },
    ],
  },
  {
    label: 'Other',
    items: [{ type: 'custom', label: 'Custom', icon: '◇' }],
  },
];

export const ALL_STATES: ControlState[] = [
  'default',
  'hover',
  'active',
  'disabled',
  'error',
  'loading',
];

// ── VAL-11 warning helper ─────────────────────────────────────────────────────

/** Returns control types that are missing a 'default' state definition. */
export function missingDefaultStates(controls: ScreenControl[]): ControlType[] {
  const typesWithDefault = new Set(
    controls.filter((c) => !c.state || c.state === 'default').map((c) => c.control_type),
  );
  const allTypes = new Set(controls.map((c) => c.control_type));
  return [...allTypes].filter((t) => !typesWithDefault.has(t)) as ControlType[];
}

// ── Palette panel ─────────────────────────────────────────────────────────────

export type PalettePanelProps = {
  /** Called when the user selects a control type to add. */
  onSelectControl: (type: ControlType) => void;
};

const panelStyle: React.CSSProperties = {
  width: 180,
  borderRight: '1px solid #e5e7eb',
  background: '#f9fafb',
  overflowY: 'auto',
  fontFamily: 'sans-serif',
  fontSize: 12,
  padding: '8px 0',
};

const groupHeadingStyle: React.CSSProperties = {
  padding: '6px 12px 2px',
  color: '#6b7280',
  fontSize: 10,
  fontWeight: 700,
  textTransform: 'uppercase',
  letterSpacing: '0.08em',
};

const paletteItemStyle: React.CSSProperties = {
  display: 'flex',
  alignItems: 'center',
  gap: 8,
  padding: '5px 12px',
  cursor: 'pointer',
  borderRadius: 4,
  margin: '1px 4px',
  color: '#374151',
  userSelect: 'none',
};

export function PalettePanel({ onSelectControl }: PalettePanelProps): React.ReactElement {
  return createElement(
    'div',
    { style: panelStyle, role: 'list', 'aria-label': 'Wireframe component palette' },
    ...PALETTE_GROUPS.map((group) =>
      createElement(
        React.Fragment,
        { key: group.label },
        createElement('div', { style: groupHeadingStyle }, group.label),
        ...group.items.map((item) =>
          createElement(
            'div',
            {
              key: item.type,
              style: paletteItemStyle,
              role: 'listitem',
              tabIndex: 0,
              'aria-label': `Add ${item.label}`,
              onClick: () => onSelectControl(item.type),
              onKeyDown: (e: React.KeyboardEvent) => {
                if (e.key === 'Enter' || e.key === ' ') {
                  e.preventDefault();
                  onSelectControl(item.type);
                }
              },
            },
            createElement('span', { 'aria-hidden': 'true', style: { fontSize: 14, width: 18, textAlign: 'center' } }, item.icon),
            createElement('span', null, item.label),
          ),
        ),
      ),
    ),
  );
}

// ── States matrix ─────────────────────────────────────────────────────────────

export type StatesMatrixProps = {
  controls: ScreenControl[];
};

const matrixStyle: React.CSSProperties = {
  fontFamily: 'sans-serif',
  fontSize: 11,
  borderCollapse: 'collapse',
  width: '100%',
};

const thStyle: React.CSSProperties = {
  padding: '4px 8px',
  textAlign: 'left',
  background: '#f3f4f6',
  borderBottom: '1px solid #e5e7eb',
  fontWeight: 600,
  color: '#374151',
};

const tdStyle: React.CSSProperties = {
  padding: '4px 8px',
  borderBottom: '1px solid #f3f4f6',
  color: '#6b7280',
  textAlign: 'center',
};

const warnStyle: React.CSSProperties = {
  background: '#fef3c7',
  color: '#92400e',
  padding: '6px 10px',
  borderRadius: 4,
  fontSize: 11,
  margin: '8px 0',
};

export function StatesMatrix({ controls }: StatesMatrixProps): React.ReactElement {
  const types = [...new Set(controls.map((c) => c.control_type))];
  const warnings = missingDefaultStates(controls);

  // Build lookup: type → set of defined states
  const defined = new Map<string, Set<string>>();
  for (const c of controls) {
    if (!defined.has(c.control_type)) defined.set(c.control_type, new Set());
    defined.get(c.control_type)!.add(c.state ?? 'default');
  }

  const warningEl = warnings.length > 0
    ? createElement(
        'div',
        { style: warnStyle, role: 'alert' },
        `VAL-11: Missing default state for: ${warnings.join(', ')}`,
      )
    : null;

  const table = createElement(
    'table',
    { style: matrixStyle, 'aria-label': 'Control states matrix' },
    createElement(
      'thead',
      null,
      createElement(
        'tr',
        null,
        createElement('th', { style: thStyle }, 'Control type'),
        ...ALL_STATES.map((s) => createElement('th', { key: s, style: thStyle }, s)),
      ),
    ),
    createElement(
      'tbody',
      null,
      ...types.map((type) =>
        createElement(
          'tr',
          { key: type },
          createElement('td', { style: { ...tdStyle, fontWeight: 600, textAlign: 'left', color: '#111827' } }, type),
          ...ALL_STATES.map((s) => {
            const has = defined.get(type)?.has(s) ?? false;
            return createElement(
              'td',
              { key: s, style: { ...tdStyle, color: has ? '#16a34a' : '#d1d5db' } },
              has ? '✓' : '·',
            );
          }),
        ),
      ),
    ),
  );

  return createElement(React.Fragment, null, warningEl, table);
}
