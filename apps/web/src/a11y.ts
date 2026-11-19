/**
 * TSK-039: Accessibility utilities for core flows.
 *
 * - Focus trap for modals (keeps Tab/Shift+Tab inside the dialog)
 * - Skip-nav link
 * - Live region announcer (aria-live)
 * - Keyboard shortcut registry with collision detection
 */
import { createElement, useEffect, useRef, useCallback, useState } from 'react';

// ── Focus trap ────────────────────────────────────────────────────────────────

const FOCUSABLE = [
  'a[href]',
  'button:not([disabled])',
  'input:not([disabled])',
  'select:not([disabled])',
  'textarea:not([disabled])',
  '[tabindex]:not([tabindex="-1"])',
].join(', ');

export function useFocusTrap(active: boolean) {
  const ref = useRef<HTMLElement | null>(null);

  useEffect(() => {
    if (!active || !ref.current) return;
    const container = ref.current;
    const focusable = (): NodeListOf<HTMLElement> =>
      container.querySelectorAll<HTMLElement>(FOCUSABLE);

    function handleKeyDown(e: KeyboardEvent) {
      if (e.key !== 'Tab') return;
      const els = Array.from(focusable());
      if (!els.length) { e.preventDefault(); return; }
      const first = els[0];
      const last = els[els.length - 1];
      if (e.shiftKey) {
        if (document.activeElement === first) {
          e.preventDefault();
          last.focus();
        }
      } else {
        if (document.activeElement === last) {
          e.preventDefault();
          first.focus();
        }
      }
    }

    container.addEventListener('keydown', handleKeyDown);
    // Move focus to first focusable element
    const firstEl = focusable()[0];
    firstEl?.focus();

    return () => container.removeEventListener('keydown', handleKeyDown);
  }, [active]);

  return ref;
}

// ── Skip nav ──────────────────────────────────────────────────────────────────

export function SkipNav({ targetId = 'main-canvas' }: { targetId?: string }) {
  return createElement(
    'a',
    {
      href: `#${targetId}`,
      style: {
        position: 'absolute',
        top: -999,
        left: -999,
        zIndex: 9999,
        padding: '8px 16px',
        background: '#2563eb',
        color: '#fff',
        fontSize: 13,
        fontFamily: 'sans-serif',
        borderRadius: 4,
        textDecoration: 'none',
        fontWeight: 600,
      },
      onFocus: (e: React.FocusEvent<HTMLAnchorElement>) => {
        e.currentTarget.style.top = '8px';
        e.currentTarget.style.left = '8px';
      },
      onBlur: (e: React.FocusEvent<HTMLAnchorElement>) => {
        e.currentTarget.style.top = '-999px';
        e.currentTarget.style.left = '-999px';
      },
    },
    'Skip to canvas',
  );
}

// ── Live region announcer ─────────────────────────────────────────────────────

type Politeness = 'polite' | 'assertive';

export function useLiveAnnouncer() {
  const [message, setMessage] = useState('');
  const [politeness, setPoliteness] = useState<Politeness>('polite');

  const announce = useCallback((msg: string, level: Politeness = 'polite') => {
    setMessage('');
    setTimeout(() => {
      setMessage(msg);
      setPoliteness(level);
    }, 50);
  }, []);

  const LiveRegion = useCallback(
    () =>
      createElement('div', {
        role: 'status',
        'aria-live': politeness,
        'aria-atomic': 'true',
        style: {
          position: 'absolute',
          width: 1,
          height: 1,
          overflow: 'hidden',
          clip: 'rect(0,0,0,0)',
          whiteSpace: 'nowrap',
        },
      }, message),
    [message, politeness],
  );

  return { announce, LiveRegion };
}

// ── Keyboard shortcut registry ────────────────────────────────────────────────

type ShortcutDef = {
  key: string;
  ctrl?: boolean;
  meta?: boolean;
  shift?: boolean;
  description: string;
  action: () => void;
};

type ShortcutId = string;

const globalRegistry = new Map<ShortcutId, ShortcutDef>();

function shortcutId(def: Pick<ShortcutDef, 'key' | 'ctrl' | 'meta' | 'shift'>): ShortcutId {
  return [
    def.ctrl ? 'ctrl' : '',
    def.meta ? 'meta' : '',
    def.shift ? 'shift' : '',
    def.key.toLowerCase(),
  ]
    .filter(Boolean)
    .join('+');
}

export function registerShortcut(id: string, def: ShortcutDef): () => void {
  const sid = shortcutId(def);
  if (globalRegistry.has(sid)) {
    console.warn(`[a11y] Shortcut collision: ${sid} already registered`);
  }
  globalRegistry.set(sid, def);
  return () => { if (globalRegistry.get(sid) === def) globalRegistry.delete(sid); };
}

export function useGlobalShortcuts(shortcuts: ShortcutDef[]) {
  useEffect(() => {
    const unregisters = shortcuts.map((s) => registerShortcut(shortcutId(s), s));

    function onKeyDown(e: KeyboardEvent) {
      const id = shortcutId({
        key: e.key,
        ctrl: e.ctrlKey,
        meta: e.metaKey,
        shift: e.shiftKey,
      });
      const def = globalRegistry.get(id);
      if (def) {
        // Don't fire when typing in an input unless it's an explicit ctrl shortcut
        const tag = (e.target as HTMLElement).tagName;
        const isTyping = ['INPUT', 'TEXTAREA', 'SELECT'].includes(tag);
        if (isTyping && !e.ctrlKey && !e.metaKey) return;
        e.preventDefault();
        def.action();
      }
    }

    window.addEventListener('keydown', onKeyDown);
    return () => {
      window.removeEventListener('keydown', onKeyDown);
      unregisters.forEach((u) => u());
    };
  }, [shortcuts]);
}

// ── Colour contrast check (WCAG AA) ──────────────────────────────────────────

function relativeLuminance(hex: string): number {
  const clean = hex.replace('#', '');
  const r = parseInt(clean.slice(0, 2), 16) / 255;
  const g = parseInt(clean.slice(2, 4), 16) / 255;
  const b = parseInt(clean.slice(4, 6), 16) / 255;
  const lin = (c: number) => (c <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4);
  return 0.2126 * lin(r) + 0.7152 * lin(g) + 0.0722 * lin(b);
}

export function contrastRatio(hex1: string, hex2: string): number {
  const l1 = relativeLuminance(hex1);
  const l2 = relativeLuminance(hex2);
  const lighter = Math.max(l1, l2);
  const darker = Math.min(l1, l2);
  return (lighter + 0.05) / (darker + 0.05);
}

/** Returns true if the pair passes WCAG AA (≥4.5 for normal text, ≥3.0 for large) */
export function passesWCAG_AA(fg: string, bg: string, largeText = false): boolean {
  return contrastRatio(fg, bg) >= (largeText ? 3.0 : 4.5);
}
