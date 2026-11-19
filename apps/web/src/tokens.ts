/**
 * Design tokens — single source of truth for colours, spacing, z-indices.
 * All shell components import from here; never hard-code values elsewhere.
 */
export const color = {
  bg: '#ffffff',
  surface: '#f9fafb',
  surfaceHover: '#f3f4f6',
  border: '#e5e7eb',
  borderStrong: '#d1d5db',
  text: '#111827',
  textMuted: '#6b7280',
  textSubtle: '#9ca3af',
  primary: '#2563eb',
  primaryHover: '#1d4ed8',
  primaryText: '#ffffff',
  danger: '#dc2626',
  warn: '#d97706',
  success: '#16a34a',
  statusDraft: '#6b7280',
  statusInProgress: '#2563eb',
  statusReview: '#d97706',
  statusApproved: '#16a34a',
  statusDeprecated: '#dc2626',
} as const;

export const space = {
  xxs: 2,
  xs: 4,
  sm: 8,
  md: 12,
  lg: 16,
  xl: 24,
  xxl: 32,
} as const;

export const radius = {
  sm: 4,
  md: 6,
  lg: 10,
  pill: 999,
} as const;

export const zIndex = {
  statusBar: 10,
  topBar: 20,
  panel: 30,
  modal: 100,
  tooltip: 200,
} as const;

export const fontSize = {
  xs: 10,
  sm: 11,
  base: 13,
  md: 14,
  lg: 16,
  xl: 18,
} as const;

export const fontFamily = {
  sans: 'system-ui, -apple-system, "Segoe UI", Roboto, sans-serif',
  mono: 'ui-monospace, "Cascadia Code", Menlo, monospace',
} as const;
