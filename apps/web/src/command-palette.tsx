/**
 * TSK-037: Command palette + global search UI.
 * Opens with Cmd/Ctrl+K. Groups results by type, fully keyboard navigable.
 */
import { createElement, useState, useEffect, useRef, useCallback } from 'react';
import { color, space, fontSize, fontFamily, radius, zIndex } from './tokens';

export type CommandItem = {
  id: string;
  label: string;
  description?: string;
  group: string;
  icon?: string;
  shortcut?: string;
  action: () => void;
};

export type CommandPaletteProps = {
  open: boolean;
  onClose: () => void;
  commands: CommandItem[];
  /** Extra search results (artifacts) appended when query is non-empty */
  searchResults?: CommandItem[];
};

export function CommandPalette({ open, onClose, commands, searchResults = [] }: CommandPaletteProps) {
  const [query, setQuery] = useState('');
  const [cursor, setCursor] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);
  const listRef = useRef<HTMLDivElement>(null);

  // Filter + group
  const all = [...commands, ...searchResults];
  const filtered = query
    ? all.filter(
        (c) =>
          c.label.toLowerCase().includes(query.toLowerCase()) ||
          c.description?.toLowerCase().includes(query.toLowerCase()),
      )
    : commands;

  const groups = [...new Set(filtered.map((c) => c.group))];

  const flat = filtered; // flat list for cursor navigation

  useEffect(() => {
    if (open) {
      setQuery('');
      setCursor(0);
      requestAnimationFrame(() => inputRef.current?.focus());
    }
  }, [open]);

  useEffect(() => {
    // scroll active item into view
    const el = listRef.current?.querySelector('[aria-selected="true"]');
    el?.scrollIntoView({ block: 'nearest' });
  }, [cursor]);

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === 'ArrowDown') {
        e.preventDefault();
        setCursor((c) => Math.min(c + 1, flat.length - 1));
      } else if (e.key === 'ArrowUp') {
        e.preventDefault();
        setCursor((c) => Math.max(c - 1, 0));
      } else if (e.key === 'Enter') {
        e.preventDefault();
        flat[cursor]?.action();
        onClose();
      } else if (e.key === 'Escape') {
        onClose();
      }
    },
    [flat, cursor, onClose],
  );

  if (!open) return null;

  return createElement(
    'div',
    {
      role: 'dialog',
      'aria-modal': 'true',
      'aria-label': 'Command palette',
      style: {
        position: 'fixed',
        inset: 0,
        background: 'rgba(0,0,0,0.4)',
        display: 'flex',
        alignItems: 'flex-start',
        justifyContent: 'center',
        paddingTop: 80,
        zIndex: zIndex.modal,
      },
      onClick: (e: React.MouseEvent) => { if (e.target === e.currentTarget) onClose(); },
    },
    createElement(
      'div',
      {
        style: {
          width: 560,
          maxWidth: '95vw',
          background: color.bg,
          borderRadius: radius.lg,
          boxShadow: '0 20px 60px rgba(0,0,0,0.3)',
          overflow: 'hidden',
          display: 'flex',
          flexDirection: 'column',
          maxHeight: '70vh',
        },
        onKeyDown: handleKeyDown,
      },
      // Input
      createElement(
        'div',
        {
          style: {
            display: 'flex',
            alignItems: 'center',
            gap: space.sm,
            padding: `${space.md}px ${space.lg}px`,
            borderBottom: `1px solid ${color.border}`,
          },
        },
        createElement('span', { 'aria-hidden': 'true', style: { color: color.textMuted, fontSize: 18 } }, '⌕'),
        createElement('input', {
          ref: inputRef,
          type: 'text',
          value: query,
          placeholder: 'Search commands and artifacts…',
          'aria-label': 'Command palette search',
          'aria-autocomplete': 'list',
          'aria-controls': 'command-palette-list',
          onChange: (e: React.ChangeEvent<HTMLInputElement>) => {
            setQuery(e.target.value);
            setCursor(0);
          },
          style: {
            flex: 1,
            border: 'none',
            outline: 'none',
            fontSize: fontSize.lg,
            color: color.text,
            background: 'transparent',
            fontFamily: fontFamily.sans,
          },
        }),
        createElement(
          'kbd',
          { style: { fontSize: fontSize.xs, color: color.textSubtle, background: color.surface, border: `1px solid ${color.border}`, borderRadius: radius.sm, padding: `1px ${space.xs}px` } },
          'Esc',
        ),
      ),
      // Results
      createElement(
        'div',
        { id: 'command-palette-list', ref: listRef, role: 'listbox', style: { overflowY: 'auto', flex: 1 } },
        filtered.length === 0
          ? createElement('div', { style: { padding: space.xl, textAlign: 'center', color: color.textSubtle, fontSize: fontSize.base, fontFamily: fontFamily.sans } }, 'No results.')
          : groups.map((group) => {
              const groupItems = filtered.filter((c) => c.group === group);
              return createElement(
                'div',
                { key: group },
                createElement('div', {
                  style: {
                    padding: `${space.xs}px ${space.lg}px`,
                    fontSize: fontSize.xs,
                    fontWeight: 700,
                    color: color.textSubtle,
                    textTransform: 'uppercase',
                    letterSpacing: '0.07em',
                    fontFamily: fontFamily.sans,
                    background: color.surface,
                  },
                }, group),
                ...groupItems.map((item) => {
                  const idx = flat.indexOf(item);
                  const active = idx === cursor;
                  return createElement(
                    'div',
                    {
                      key: item.id,
                      role: 'option',
                      'aria-selected': active,
                      onClick: () => { item.action(); onClose(); },
                      onMouseEnter: () => setCursor(idx),
                      style: {
                        display: 'flex',
                        alignItems: 'center',
                        gap: space.sm,
                        padding: `${space.sm}px ${space.lg}px`,
                        background: active ? '#eff6ff' : 'transparent',
                        cursor: 'pointer',
                        borderLeft: `2px solid ${active ? color.primary : 'transparent'}`,
                      },
                    },
                    item.icon && createElement('span', { 'aria-hidden': 'true', style: { width: 18, textAlign: 'center', flexShrink: 0 } }, item.icon),
                    createElement(
                      'div',
                      { style: { flex: 1, minWidth: 0 } },
                      createElement('div', { style: { fontSize: fontSize.base, color: color.text, fontFamily: fontFamily.sans, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' } }, item.label),
                      item.description && createElement('div', { style: { fontSize: fontSize.xs, color: color.textMuted, fontFamily: fontFamily.sans } }, item.description),
                    ),
                    item.shortcut && createElement(
                      'kbd',
                      { style: { fontSize: fontSize.xs, color: color.textSubtle, background: color.surface, border: `1px solid ${color.border}`, borderRadius: radius.sm, padding: `1px ${space.xs}px`, flexShrink: 0 } },
                      item.shortcut,
                    ),
                  );
                }),
              );
            }),
      ),
    ),
  );
}

/** Hook: bind Cmd/Ctrl+K to toggle the palette open state */
export function useCommandPalette() {
  const [open, setOpen] = useState(false);

  useEffect(() => {
    function onKeyDown(e: KeyboardEvent) {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        setOpen((v) => !v);
      }
    }
    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, []);

  return { open, setOpen };
}
