/**
 * TSK-033: Workspace shell layout.
 *
 * Five regions per spec §5.1:
 *   ┌─────────────────────── top-bar ───────────────────────┐
 *   │  left-nav  │        canvas / main                     │
 *   │            ├────────────────────────────── right-panel │
 *   └────────────┴──────────────── status-bar ──────────────┘
 *
 * All layout is in pure CSS (inline styles via tokens) so it works without
 * any build step and without React-specific tooling.
 */
import { createElement, useState, type ReactNode } from 'react';
import { color, space, zIndex, fontSize, fontFamily } from './tokens';

// ── Types ─────────────────────────────────────────────────────────────────────

export type PanelId = 'outline' | 'search' | 'provenance' | 'inspector';

export type WorkspaceShellProps = {
  /** Project name shown in top bar */
  projectName: string;
  /** Username / avatar label */
  userLabel: string;
  /** Save state: 'saved' | 'saving' | 'unsaved' */
  saveState: 'saved' | 'saving' | 'unsaved';
  /** Currently active left-nav panel */
  activePanel: PanelId;
  onPanelChange: (panel: PanelId) => void;
  /** Main canvas area */
  children: ReactNode;
  /** Right panel content (inspector) */
  rightPanel?: ReactNode;
  /** Left panel content (outline / search / …) */
  leftPanel?: ReactNode;
  /** Status bar extra content */
  statusExtra?: ReactNode;
  onCommandPalette?: () => void;
};

// ── Top bar ───────────────────────────────────────────────────────────────────

function SaveIndicator({ state }: { state: WorkspaceShellProps['saveState'] }) {
  const label = state === 'saved' ? 'Saved' : state === 'saving' ? 'Saving…' : 'Unsaved';
  const col = state === 'saved' ? color.textSubtle : state === 'saving' ? color.textMuted : color.warn;
  return createElement(
    'span',
    { style: { fontSize: fontSize.sm, color: col, fontFamily: fontFamily.sans } },
    label,
  );
}

function TopBar({
  projectName,
  userLabel,
  saveState,
  onCommandPalette,
}: Pick<WorkspaceShellProps, 'projectName' | 'userLabel' | 'saveState' | 'onCommandPalette'>) {
  return createElement(
    'header',
    {
      role: 'banner',
      style: {
        display: 'flex',
        alignItems: 'center',
        gap: space.md,
        height: 48,
        padding: `0 ${space.xl}px`,
        background: color.bg,
        borderBottom: `1px solid ${color.border}`,
        zIndex: zIndex.topBar,
        flexShrink: 0,
        fontFamily: fontFamily.sans,
      },
    },
    // Logo / brand
    createElement(
      'span',
      { style: { fontWeight: 700, fontSize: fontSize.md, color: color.text, letterSpacing: '-0.01em' } },
      '⬡ Prompt Studio',
    ),
    // Separator
    createElement('span', { style: { color: color.border, fontSize: fontSize.lg }, 'aria-hidden': 'true' }, '/'),
    // Project name
    createElement(
      'span',
      { style: { fontSize: fontSize.base, color: color.textMuted, maxWidth: 240, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' } },
      projectName,
    ),
    // Save indicator
    createElement(SaveIndicator, { state: saveState }),
    // Spacer
    createElement('div', { style: { flex: 1 } }),
    // Command palette button
    createElement(
      'button',
      {
        type: 'button',
        'aria-label': 'Open command palette (Ctrl+K)',
        title: 'Command palette (Ctrl+K)',
        onClick: onCommandPalette,
        style: {
          display: 'flex',
          alignItems: 'center',
          gap: space.xs,
          padding: `${space.xs}px ${space.sm}px`,
          border: `1px solid ${color.borderStrong}`,
          borderRadius: 6,
          background: color.surface,
          color: color.textMuted,
          fontSize: fontSize.sm,
          cursor: 'pointer',
          fontFamily: fontFamily.sans,
        },
      },
      '⌘K  Search…',
    ),
    // User avatar
    createElement(
      'span',
      {
        'aria-label': `Signed in as ${userLabel}`,
        title: userLabel,
        style: {
          width: 28,
          height: 28,
          borderRadius: '50%',
          background: color.primary,
          color: color.primaryText,
          display: 'inline-flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontSize: fontSize.sm,
          fontWeight: 700,
          flexShrink: 0,
          cursor: 'default',
        },
      },
      userLabel.slice(0, 2).toUpperCase(),
    ),
  );
}

// ── Left nav ──────────────────────────────────────────────────────────────────

type NavItem = { id: PanelId; label: string; icon: string };

const NAV_ITEMS: NavItem[] = [
  { id: 'outline', label: 'Outline', icon: '≡' },
  { id: 'search', label: 'Search', icon: '⌕' },
  { id: 'provenance', label: 'Provenance', icon: '⊕' },
  { id: 'inspector', label: 'Inspector', icon: '◧' },
];

function LeftNav({
  active,
  onChange,
}: {
  active: PanelId;
  onChange: (id: PanelId) => void;
}) {
  return createElement(
    'nav',
    {
      'aria-label': 'Left navigation',
      style: {
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        width: 48,
        background: color.surface,
        borderRight: `1px solid ${color.border}`,
        padding: `${space.sm}px 0`,
        gap: space.xs,
        flexShrink: 0,
        zIndex: zIndex.panel,
      },
    },
    ...NAV_ITEMS.map((item) =>
      createElement(
        'button',
        {
          key: item.id,
          type: 'button',
          'aria-label': item.label,
          'aria-pressed': active === item.id,
          title: item.label,
          onClick: () => onChange(item.id),
          style: {
            width: 36,
            height: 36,
            border: 'none',
            borderRadius: 6,
            background: active === item.id ? color.primaryText : 'none',
            boxShadow: active === item.id ? `0 0 0 1.5px ${color.primary}` : 'none',
            color: active === item.id ? color.primary : color.textMuted,
            fontSize: 18,
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            transition: 'background 0.1s',
          },
        },
        item.icon,
      ),
    ),
  );
}

// ── Status bar ────────────────────────────────────────────────────────────────

function StatusBar({ extra }: { extra?: ReactNode }) {
  return createElement(
    'footer',
    {
      role: 'contentinfo',
      'aria-label': 'Status bar',
      style: {
        display: 'flex',
        alignItems: 'center',
        height: 24,
        padding: `0 ${space.md}px`,
        background: color.primary,
        color: color.primaryText,
        fontSize: fontSize.xs,
        fontFamily: fontFamily.sans,
        gap: space.md,
        flexShrink: 0,
        zIndex: zIndex.statusBar,
      },
    },
    createElement('span', null, 'Prompt Studio v0.1'),
    createElement('span', { style: { opacity: 0.6 } }, '·'),
    createElement('span', { 'aria-live': 'polite' }, extra ?? null),
  );
}

// ── Shell ─────────────────────────────────────────────────────────────────────

const LEFT_PANEL_WIDTH = 260;
const RIGHT_PANEL_WIDTH = 300;

export function WorkspaceShell({
  projectName,
  userLabel,
  saveState,
  activePanel,
  onPanelChange,
  children,
  rightPanel,
  leftPanel,
  statusExtra,
  onCommandPalette,
}: WorkspaceShellProps) {
  return createElement(
    'div',
    {
      style: {
        display: 'flex',
        flexDirection: 'column',
        height: '100vh',
        overflow: 'hidden',
        fontFamily: fontFamily.sans,
        background: color.bg,
      },
    },
    createElement(TopBar, { projectName, userLabel, saveState, onCommandPalette }),
    createElement(
      'div',
      { style: { display: 'flex', flex: 1, overflow: 'hidden' } },
      createElement(LeftNav, { active: activePanel, onChange: onPanelChange }),
      // Left panel drawer
      leftPanel
        ? createElement(
            'aside',
            {
              'aria-label': `${activePanel} panel`,
              style: {
                width: LEFT_PANEL_WIDTH,
                flexShrink: 0,
                borderRight: `1px solid ${color.border}`,
                background: color.surface,
                overflowY: 'auto',
                display: 'flex',
                flexDirection: 'column',
              },
            },
            leftPanel,
          )
        : null,
      // Main area
      createElement(
        'main',
        {
          id: 'main-canvas',
          'aria-label': 'Canvas workspace',
          style: { flex: 1, overflow: 'hidden', position: 'relative', background: color.bg },
        },
        children,
      ),
      // Right panel
      rightPanel
        ? createElement(
            'aside',
            {
              'aria-label': 'Inspector panel',
              style: {
                width: RIGHT_PANEL_WIDTH,
                flexShrink: 0,
                borderLeft: `1px solid ${color.border}`,
                background: color.surface,
                overflowY: 'auto',
                display: 'flex',
                flexDirection: 'column',
              },
            },
            rightPanel,
          )
        : null,
    ),
    createElement(StatusBar, { extra: statusExtra }),
  );
}
