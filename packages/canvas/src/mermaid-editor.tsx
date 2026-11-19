/**
 * TSK-030: Mermaid focus editor.
 * A modal editor for Mermaid diagram source. When the user saves, it calls
 * onProposePatch with the new source so the caller can open a patch review.
 */
import { createElement, useEffect, useRef, useState } from 'react';

export type MermaidEditorProps = {
  initialSource: string;
  onProposePatch: (newSource: string) => void;
  onClose: () => void;
};

const overlayStyle: React.CSSProperties = {
  position: 'fixed',
  inset: 0,
  background: 'rgba(0,0,0,0.45)',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  zIndex: 1000,
};

const dialogStyle: React.CSSProperties = {
  background: '#fff',
  borderRadius: 10,
  boxShadow: '0 8px 32px rgba(0,0,0,0.22)',
  padding: 24,
  width: 580,
  maxWidth: '95vw',
  display: 'flex',
  flexDirection: 'column',
  gap: 12,
};

const headingStyle: React.CSSProperties = {
  margin: 0,
  fontSize: 16,
  fontWeight: 700,
  color: '#111827',
  fontFamily: 'sans-serif',
};

const textareaStyle: React.CSSProperties = {
  fontFamily: 'ui-monospace, "Cascadia Code", Menlo, monospace',
  fontSize: 13,
  lineHeight: 1.6,
  minHeight: 300,
  resize: 'vertical',
  border: '1.5px solid #d1d5db',
  borderRadius: 6,
  padding: '10px 12px',
  outline: 'none',
  color: '#111827',
  background: '#f9fafb',
  width: '100%',
  boxSizing: 'border-box',
};

const footerStyle: React.CSSProperties = {
  display: 'flex',
  justifyContent: 'space-between',
  alignItems: 'center',
  gap: 8,
};

const charCountStyle: React.CSSProperties = {
  fontSize: 11,
  color: '#6b7280',
  fontFamily: 'sans-serif',
};

const btnPrimary: React.CSSProperties = {
  padding: '7px 16px',
  border: 'none',
  borderRadius: 6,
  background: '#2563eb',
  color: '#fff',
  fontWeight: 600,
  fontSize: 13,
  cursor: 'pointer',
  fontFamily: 'sans-serif',
};

const btnSecondary: React.CSSProperties = {
  padding: '7px 16px',
  border: '1px solid #d1d5db',
  borderRadius: 6,
  background: '#fff',
  color: '#374151',
  fontWeight: 500,
  fontSize: 13,
  cursor: 'pointer',
  fontFamily: 'sans-serif',
};

const headingId = 'mermaid-editor-heading';

export function MermaidEditor({
  initialSource,
  onProposePatch,
  onClose,
}: MermaidEditorProps): React.ReactElement {
  const [source, setSource] = useState(initialSource);
  const textareaRef = useRef<HTMLTextAreaElement | null>(null);

  // Focus the textarea when the dialog opens
  useEffect(() => {
    textareaRef.current?.focus();
  }, []);

  // Keyboard handling
  useEffect(() => {
    function handleKeyDown(e: KeyboardEvent): void {
      if (e.key === 'Escape') {
        e.preventDefault();
        onClose();
      }
      if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
        e.preventDefault();
        onProposePatch(source);
      }
    }
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [onClose, onProposePatch, source]);

  return createElement(
    'div',
    { style: overlayStyle, onClick: (e: React.MouseEvent) => { if (e.target === e.currentTarget) onClose(); } },
    createElement(
      'div',
      {
        style: dialogStyle,
        role: 'dialog',
        'aria-modal': 'true',
        'aria-labelledby': headingId,
      },
      createElement('h2', { id: headingId, style: headingStyle }, 'Edit Diagram Source'),
      createElement('textarea', {
        ref: textareaRef,
        style: textareaStyle,
        value: source,
        onChange: (e: React.ChangeEvent<HTMLTextAreaElement>) => setSource(e.target.value),
        spellCheck: false,
        'aria-label': 'Mermaid diagram source code',
      }),
      createElement(
        'div',
        { style: footerStyle },
        createElement('span', { style: charCountStyle }, `${source.length} characters`),
        createElement(
          'div',
          { style: { display: 'flex', gap: 8 } },
          createElement(
            'button',
            { type: 'button', style: btnSecondary, onClick: onClose, 'aria-label': 'Cancel editing' },
            'Cancel',
          ),
          createElement(
            'button',
            {
              type: 'button',
              style: btnPrimary,
              onClick: () => onProposePatch(source),
              'aria-label': 'Save and propose patch',
              title: 'Save & Propose Patch (Ctrl+Enter)',
            },
            'Save & Propose Patch',
          ),
        ),
      ),
    ),
  );
}
