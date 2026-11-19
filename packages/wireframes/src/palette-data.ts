/**
 * Pure palette data and logic — no React dependency.
 * UI components (PalettePanel, StatesMatrix) live in palette-ui.tsx.
 */
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
    controls
      .filter((c) => !c.state || c.state === 'default')
      .map((c) => c.control_type),
  );
  const allTypes = new Set(controls.map((c) => c.control_type));
  return [...allTypes].filter((t) => !typesWithDefault.has(t)) as ControlType[];
}
