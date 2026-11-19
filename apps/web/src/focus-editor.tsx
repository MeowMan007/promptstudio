/**
 * TSK-038: Focus mode editors — markdown, mermaid, json, yaml, sql.
 * Opens as a modal overlay over the canvas. Preserves canvas position on
 * close. Validates on save (round-trip validation).
 */
import { createElement, useState, useEffect, useRef, useCallback } from 'react';
import { color, space, fontSize, fontFamily, radius, zIndex } from './tokens';

export type FocusEditorMode = 'markdown' | 'mermaid' | 'json' | 'yaml' | 'sql';

export type FocusEditorProps = {
  mode: FocusEditorMode;
  initialValue: string;
  artifactTitle?: string;
  /** Called when user saves valid content */
  onSave: (value: string) => void;
  onClose: () => void;
};

type ValidationResult = { valid: boolean; error?: string };

// ── Per-mode validators ───────────────────────────────────────────────────────

function validateContent(mode: FocusEditorMode, value: string): ValidationResult {
  if (value.trim() === '') return { valid: true };

  if (mode === 'json') {
    try {
      JSON.parse(value);
      return { valid: true };
    } catch (e) {
      return { valid: false, error: `JSON parse error: ${(e as Error).message}` };
    }
  }

  if (mode === 'mermaid') {
    // Basic check: must start with graph/flowchart/sequenceDiagram/etc.
    const firstLine = value.trim().split('\n')[0]?.trim() ?? '';
    const valid = /^(graph|flowchart|sequenceDiagram|classDiagram|stateDiagram|erDiagram|gantt|pie|gitGraph)/i.test(firstLine);
    return valid
      ? { valid: true }
      : { valid: false, error: 'Must begin with a Mermaid diagram type (graph, flowchart, sequenceDiagram, …)' };
  }

  if (mode === 'yaml') {
    // Minimal YAML check — look for obvious parse errors (unbalanced quotes)
    const unbalanced = (value.match(/"/g) ?? []).length % 2 !== 0;
    return unbalanced
      ? { valid: false, error: 'Possible YAML syntax error: unbalanced quotes detected.' }
      : { valid: true };
  }

  return { valid: true };
}

// ── Mode metadata ─────────────────────────────────────────────────────────────

const MODE_META: Record<FocusEditorMode, { label: string; lang: string; placeholder: string }> = {
  markdown: { label: 'Markdown', lang: 'markdown', placeholder: '# Title\n\nWrite your content…' },
  mermaid: { label: 'Mermaid', lang: 'mermaid', placeholder: 'graph TD\n    A --> B' },
  json: { label: 'JSON', lang: 'json', placeholder: '{\n  \n}' },
  yaml: { label: 'YAML', lang: 'yaml', placeholder: 'key: value\n' },
  sql: { label: 'SQL', lang: 'sql', placeholder: 'SELECT *\nFROM table\nWHERE condition;' },
};

// ── Component ─────────────────────────────────────────────────────────────────

export function FocusEditor({ mode, initialValue, artifactTitle, onSave, onClose }: FocusEditorProps) {
  const [value, setValue] = useState(initialValue);
  const [validation, setValidation] = useState<ValidationResult>({ valid: true });
  const [dirty, setDirty] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const meta = MODE_META[mode];

  useEffect(() => {
    requestAnimationFrame(() => textareaRef.current?.focus());
  }, []);

  const handleSave = useCallback(() => {
    const result = validateContent(mode, value);
    setValidation(result);
    if (result.valid) {
      onSave(value);
      onClose();
    }
  }, [mode, value, onSave, onClose]);

  useEffect(() => {
    function onKeyDown(e: KeyboardEvent) {
      if (e.key === 'Escape' && !dirty) onClose();
      if ((e.ctrlKey || e.metaKey) && e.key === 's') {
        e.preventDefault();
        handleSave();
      }
    }
    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, [dirty, onClose, handleSave]);

  const lineCount = value.split('\n').length;

  return createElement(
    'div',
    {
      role: 'dialog',
      'aria-modal': 'true',
      'aria-label': `${meta.label} editor`,
      style: {
        position: 'fixed',
        inset: 0,
        background: 'rgba(0,0,0,0.5)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: zIndex.modal,
        padding: space.xl,
      },
    },
    createElement(
      'div',
      {
        style: {
          width: '100%',
          maxWidth: 760,
          background: color.bg,
          borderRadius: radius.lg,
          boxShadow: '0 20px 60px rgba(0,0,0,0.3)',
          display: 'flex',
          flexDirection: 'column',
          maxHeight: '90vh',
          overflow: 'hidden',
        },
      },
      // Header
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
        createElement(
          'span',
          {
            style: {
              fontSize: fontSize.xs,
              fontWeight: 700,
              color: color.primaryText,
              background: color.primary,
              borderRadius: radius.sm,
              padding: `2px ${space.xs}px`,
              fontFamily: fontFamily.sans,
            },
          },
          meta.label,
        ),
        createElement(
          'span',
          { style: { fontSize: fontSize.base, fontWeight: 600, color: color.text, fontFamily: fontFamily.sans } },
          artifactTitle ?? 'Edit',
        ),
        createElement('div', { style: { flex: 1 } }),
        createElement(
          'span',
          { style: { fontSize: fontSize.xs, color: color.textSubtle, fontFamily: fontFamily.sans } },
          `${lineCount} lines · ${value.length} chars`,
        ),
        dirty && createElement(
          'span',
          { style: { fontSize: fontSize.xs, color: color.warn, fontFamily: fontFamily.sans } },
          '● Unsaved',
        ),
      ),
      // Editor
      createElement('textarea', {
        ref: textareaRef,
        value,
        placeholder: meta.placeholder,
        'aria-label': `${meta.label} source code editor`,
        spellCheck: false,
        onChange: (e: React.ChangeEvent<HTMLTextAreaElement>) => {
          setValue(e.target.value);
          setDirty(true);
          setValidation({ valid: true });
        },
        style: {
          flex: 1,
          resize: 'none',
          border: 'none',
          outline: 'none',
          padding: `${space.md}px ${space.lg}px`,
          fontFamily: fontFamily.mono,
          fontSize: fontSize.base,
          lineHeight: 1.7,
          color: color.text,
          background: '#fafafa',
          minHeight: 360,
          tabSize: 2,
        },
      }),
      // Validation error
      !validation.valid &&
        createElement(
          'div',
          {
            role: 'alert',
            style: {
              padding: `${space.sm}px ${space.lg}px`,
              background: '#fef2f2',
              borderTop: `1px solid #fecaca`,
              color: color.danger,
              fontSize: fontSize.sm,
              fontFamily: fontFamily.sans,
            },
          },
          `⚠ ${validation.error}`,
        ),
      // Footer
      createElement(
        'div',
        {
          style: {
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            padding: `${space.sm}px ${space.lg}px`,
            borderTop: `1px solid ${color.border}`,
            gap: space.sm,
          },
        },
        createElement(
          'span',
          { style: { fontSize: fontSize.xs, color: color.textSubtle, fontFamily: fontFamily.sans } },
          'Ctrl+S to save · Esc to cancel',
        ),
        createElement(
          'div',
          { style: { display: 'flex', gap: space.sm } },
          createElement(
            'button',
            {
              type: 'button',
              onClick: onClose,
              style: {
                padding: `${space.xs}px ${space.md}px`,
                border: `1px solid ${color.borderStrong}`,
                borderRadius: radius.md,
                background: color.bg,
                color: color.textMuted,
                fontSize: fontSize.base,
                cursor: 'pointer',
                fontFamily: fontFamily.sans,
              },
            },
            'Cancel',
          ),
          createElement(
            'button',
            {
              type: 'button',
              onClick: handleSave,
              style: {
                padding: `${space.xs}px ${space.md}px`,
                border: 'none',
                borderRadius: radius.md,
                background: color.primary,
                color: color.primaryText,
                fontSize: fontSize.base,
                fontWeight: 600,
                cursor: 'pointer',
                fontFamily: fontFamily.sans,
              },
            },
            'Save',
          ),
        ),
      ),
    ),
  );
}
