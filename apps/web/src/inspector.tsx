/**
 * TSK-035: Schema-driven inspector forms with array editors.
 * TSK-036: Provenance, status and relation UI.
 *
 * The InspectorPanel renders all editable fields for a selected artifact
 * without requiring raw JSON editing. Each field type has an appropriate
 * input widget. Array fields support add/remove. Validation errors show inline.
 */
import { createElement, useState, useCallback } from 'react';
import { color, space, fontSize, fontFamily, radius } from './tokens';

// ── Types ─────────────────────────────────────────────────────────────────────

export type FieldSchema =
  | { kind: 'string'; label: string; multiline?: boolean; maxLength?: number }
  | { kind: 'enum'; label: string; options: string[] }
  | { kind: 'array'; label: string; itemLabel: string }
  | { kind: 'readonly'; label: string };

export type InspectorField = {
  key: string;
  schema: FieldSchema;
  value: unknown;
  error?: string;
};

export type ProvenanceInfo = {
  createdBy: string;
  createdAt: string;
  lastModifiedBy: string;
  lastModifiedAt: string;
  revisionNumber: number;
  promptVersion?: string;
  skillName?: string;
  approvedBy?: string;
  approvedAt?: string;
  sourceIds?: string[];
};

export type RelationEntry = {
  edgeType: string;
  targetAlias: string;
  targetTitle: string;
  targetId: string;
};

export type InspectorPanelProps = {
  artifactId: string | null;
  artifactType: string;
  alias: string;
  title: string;
  fields: InspectorField[];
  provenance?: ProvenanceInfo;
  relations?: RelationEntry[];
  onFieldChange: (key: string, value: unknown) => void;
  onNavigate?: (artifactId: string) => void;
};

// ── Shared styles ─────────────────────────────────────────────────────────────

const labelStyle: React.CSSProperties = {
  fontSize: fontSize.xs,
  fontWeight: 700,
  color: color.textMuted,
  textTransform: 'uppercase',
  letterSpacing: '0.06em',
  marginBottom: space.xxs,
  fontFamily: fontFamily.sans,
};

const inputStyle: React.CSSProperties = {
  width: '100%',
  boxSizing: 'border-box',
  padding: `${space.xs}px ${space.sm}px`,
  border: `1px solid ${color.borderStrong}`,
  borderRadius: radius.sm,
  fontSize: fontSize.base,
  fontFamily: fontFamily.sans,
  color: color.text,
  background: color.bg,
  outline: 'none',
};

const errorStyle: React.CSSProperties = {
  fontSize: fontSize.xs,
  color: color.danger,
  marginTop: space.xxs,
  fontFamily: fontFamily.sans,
};

const sectionHeadingStyle: React.CSSProperties = {
  fontSize: fontSize.xs,
  fontWeight: 700,
  color: color.textMuted,
  textTransform: 'uppercase',
  letterSpacing: '0.07em',
  padding: `${space.sm}px ${space.md}px`,
  borderBottom: `1px solid ${color.border}`,
  borderTop: `1px solid ${color.border}`,
  background: color.surface,
  fontFamily: fontFamily.sans,
};

// ── Field widgets ─────────────────────────────────────────────────────────────

function StringField({
  field,
  onChange,
}: {
  field: InspectorField & { schema: { kind: 'string'; label: string; multiline?: boolean; maxLength?: number } };
  onChange: (v: string) => void;
}) {
  const val = typeof field.value === 'string' ? field.value : '';
  const remaining = field.schema.maxLength !== undefined ? field.schema.maxLength - val.length : null;

  if (field.schema.multiline) {
    return createElement(
      'div',
      null,
      createElement('div', { style: labelStyle }, field.schema.label),
      createElement('textarea', {
        value: val,
        'aria-label': field.schema.label,
        onChange: (e: React.ChangeEvent<HTMLTextAreaElement>) => onChange(e.target.value),
        maxLength: field.schema.maxLength,
        rows: 4,
        style: { ...inputStyle, resize: 'vertical', minHeight: 80 },
      }),
      remaining !== null && createElement(
        'div',
        { style: { fontSize: fontSize.xs, color: remaining < 20 ? color.warn : color.textSubtle, textAlign: 'right' } },
        `${remaining} left`,
      ),
      field.error && createElement('div', { style: errorStyle, role: 'alert' }, field.error),
    );
  }

  return createElement(
    'div',
    null,
    createElement('div', { style: labelStyle }, field.schema.label),
    createElement('input', {
      type: 'text',
      value: val,
      'aria-label': field.schema.label,
      maxLength: field.schema.maxLength,
      onChange: (e: React.ChangeEvent<HTMLInputElement>) => onChange(e.target.value),
      style: inputStyle,
    }),
    field.error && createElement('div', { style: errorStyle, role: 'alert' }, field.error),
  );
}

function EnumField({
  field,
  onChange,
}: {
  field: InspectorField & { schema: { kind: 'enum'; label: string; options: string[] } };
  onChange: (v: string) => void;
}) {
  const val = typeof field.value === 'string' ? field.value : '';
  return createElement(
    'div',
    null,
    createElement('div', { style: labelStyle }, field.schema.label),
    createElement(
      'select',
      {
        value: val,
        'aria-label': field.schema.label,
        onChange: (e: React.ChangeEvent<HTMLSelectElement>) => onChange(e.target.value),
        style: inputStyle,
      },
      ...field.schema.options.map((opt) =>
        createElement('option', { key: opt, value: opt }, opt),
      ),
    ),
    field.error && createElement('div', { style: errorStyle, role: 'alert' }, field.error),
  );
}

function ArrayField({
  field,
  onChange,
}: {
  field: InspectorField & { schema: { kind: 'array'; label: string; itemLabel: string } };
  onChange: (v: string[]) => void;
}) {
  const arr: string[] = Array.isArray(field.value) ? (field.value as string[]) : [];

  return createElement(
    'div',
    null,
    createElement('div', { style: labelStyle }, field.schema.label),
    ...arr.map((item, idx) =>
      createElement(
        'div',
        { key: idx, style: { display: 'flex', gap: space.xs, marginBottom: space.xxs } },
        createElement('input', {
          type: 'text',
          value: item,
          'aria-label': `${field.schema.itemLabel} ${idx + 1}`,
          onChange: (e: React.ChangeEvent<HTMLInputElement>) => {
            const next = [...arr];
            next[idx] = e.target.value;
            onChange(next);
          },
          style: { ...inputStyle, flex: 1 },
        }),
        createElement(
          'button',
          {
            type: 'button',
            'aria-label': `Remove ${field.schema.itemLabel} ${idx + 1}`,
            onClick: () => onChange(arr.filter((_, i) => i !== idx)),
            style: {
              border: 'none',
              background: 'none',
              color: color.danger,
              cursor: 'pointer',
              fontSize: fontSize.md,
              padding: `0 ${space.xs}px`,
            },
          },
          '×',
        ),
      ),
    ),
    createElement(
      'button',
      {
        type: 'button',
        'aria-label': `Add ${field.schema.itemLabel}`,
        onClick: () => onChange([...arr, '']),
        style: {
          fontSize: fontSize.sm,
          color: color.primary,
          background: 'none',
          border: `1px dashed ${color.primary}`,
          borderRadius: radius.sm,
          padding: `${space.xxs}px ${space.sm}px`,
          cursor: 'pointer',
          width: '100%',
          fontFamily: fontFamily.sans,
        },
      },
      `+ Add ${field.schema.itemLabel}`,
    ),
    field.error && createElement('div', { style: errorStyle, role: 'alert' }, field.error),
  );
}

function ReadonlyField({ field }: { field: InspectorField }) {
  return createElement(
    'div',
    null,
    createElement('div', { style: labelStyle }, (field.schema as { label: string }).label),
    createElement(
      'div',
      {
        style: {
          fontSize: fontSize.base,
          color: color.textMuted,
          fontFamily: fontFamily.mono,
          padding: `${space.xs}px ${space.sm}px`,
          background: color.surface,
          borderRadius: radius.sm,
          border: `1px solid ${color.border}`,
          wordBreak: 'break-all',
        },
      },
      String(field.value ?? '—'),
    ),
  );
}

// ── Provenance section ────────────────────────────────────────────────────────

function ProvenanceSection({ info }: { info: ProvenanceInfo }) {
  const row = (label: string, value: string | undefined | null) =>
    value
      ? createElement(
          'div',
          { style: { display: 'flex', justifyContent: 'space-between', padding: `${space.xxs}px 0` } },
          createElement('span', { style: { fontSize: fontSize.xs, color: color.textMuted, fontFamily: fontFamily.sans } }, label),
          createElement('span', { style: { fontSize: fontSize.xs, color: color.text, fontFamily: fontFamily.mono, maxWidth: 160, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' } }, value),
        )
      : null;

  return createElement(
    'div',
    { style: { padding: `${space.sm}px ${space.md}px` } },
    row('Revision', `#${info.revisionNumber}`),
    row('Created by', info.createdBy),
    row('Created', info.createdAt),
    row('Modified by', info.lastModifiedBy),
    row('Modified', info.lastModifiedAt),
    row('Prompt version', info.promptVersion),
    row('Skill', info.skillName),
    row('Approved by', info.approvedBy),
    row('Approved', info.approvedAt),
  );
}

// ── Relations section ─────────────────────────────────────────────────────────

function RelationsSection({
  relations,
  onNavigate,
}: {
  relations: RelationEntry[];
  onNavigate?: (id: string) => void;
}) {
  if (!relations.length)
    return createElement(
      'div',
      { style: { padding: `${space.sm}px ${space.md}px`, color: color.textSubtle, fontSize: fontSize.sm } },
      'No relations.',
    );

  return createElement(
    'div',
    { style: { padding: `${space.xs}px ${space.md}px` } },
    ...relations.map((rel, idx) =>
      createElement(
        'div',
        {
          key: idx,
          style: {
            display: 'flex',
            alignItems: 'center',
            gap: space.sm,
            padding: `${space.xs}px 0`,
            borderBottom: `1px solid ${color.border}`,
          },
        },
        createElement('span', { style: { fontSize: fontSize.xs, color: color.textSubtle, width: 80, flexShrink: 0, fontFamily: fontFamily.sans } }, rel.edgeType),
        createElement(
          onNavigate ? 'button' : 'span',
          {
            type: onNavigate ? 'button' : undefined,
            onClick: onNavigate ? () => onNavigate(rel.targetId) : undefined,
            'aria-label': onNavigate ? `Navigate to ${rel.targetTitle}` : undefined,
            style: {
              fontSize: fontSize.base,
              color: onNavigate ? color.primary : color.text,
              background: 'none',
              border: 'none',
              padding: 0,
              cursor: onNavigate ? 'pointer' : 'default',
              textAlign: 'left',
              textDecoration: onNavigate ? 'underline' : 'none',
              fontFamily: fontFamily.sans,
            },
          },
          `${rel.targetAlias} ${rel.targetTitle}`,
        ),
      ),
    ),
  );
}

// ── Inspector panel ───────────────────────────────────────────────────────────

type InspectorTab = 'fields' | 'provenance' | 'relations';

export function InspectorPanel({
  artifactId,
  artifactType,
  alias,
  title,
  fields,
  provenance,
  relations = [],
  onFieldChange,
  onNavigate,
}: InspectorPanelProps) {
  const [tab, setTab] = useState<InspectorTab>('fields');

  if (!artifactId) {
    return createElement(
      'div',
      { style: { padding: space.xl, color: color.textSubtle, fontSize: fontSize.base, textAlign: 'center', fontFamily: fontFamily.sans } },
      'Select an artifact to inspect.',
    );
  }

  const tabBtn = (id: InspectorTab, label: string) =>
    createElement(
      'button',
      {
        type: 'button',
        role: 'tab',
        'aria-selected': tab === id,
        onClick: () => setTab(id),
        style: {
          flex: 1,
          padding: `${space.sm}px 0`,
          border: 'none',
          borderBottom: `2px solid ${tab === id ? color.primary : 'transparent'}`,
          background: 'none',
          color: tab === id ? color.primary : color.textMuted,
          fontWeight: tab === id ? 700 : 400,
          fontSize: fontSize.sm,
          cursor: 'pointer',
          fontFamily: fontFamily.sans,
        },
      },
      label,
    );

  return createElement(
    'div',
    { style: { display: 'flex', flexDirection: 'column', height: '100%', fontFamily: fontFamily.sans } },
    // Header
    createElement(
      'div',
      { style: { padding: `${space.sm}px ${space.md}px`, borderBottom: `1px solid ${color.border}` } },
      createElement('div', { style: { fontSize: fontSize.xs, color: color.textMuted, fontFamily: fontFamily.mono } }, alias),
      createElement('div', { style: { fontSize: fontSize.md, fontWeight: 700, color: color.text, marginTop: space.xxs } }, title),
      createElement(
        'div',
        {
          style: {
            display: 'inline-block',
            marginTop: space.xs,
            padding: `1px ${space.xs}px`,
            borderRadius: radius.sm,
            background: color.surface,
            border: `1px solid ${color.border}`,
            fontSize: fontSize.xs,
            color: color.textMuted,
          },
        },
        artifactType,
      ),
    ),
    // Tabs
    createElement(
      'div',
      { role: 'tablist', style: { display: 'flex', borderBottom: `1px solid ${color.border}` } },
      tabBtn('fields', 'Fields'),
      tabBtn('provenance', 'Provenance'),
      tabBtn('relations', 'Relations'),
    ),
    // Content
    createElement(
      'div',
      { style: { flex: 1, overflowY: 'auto' } },
      tab === 'fields' &&
        createElement(
          'div',
          { style: { padding: space.md, display: 'flex', flexDirection: 'column', gap: space.md } },
          ...fields.map((field) => {
            if (field.schema.kind === 'string')
              return createElement(StringField, {
                key: field.key,
                field: field as InspectorField & { schema: { kind: 'string'; label: string; multiline?: boolean; maxLength?: number } },
                onChange: (v) => onFieldChange(field.key, v),
              });
            if (field.schema.kind === 'enum')
              return createElement(EnumField, {
                key: field.key,
                field: field as InspectorField & { schema: { kind: 'enum'; label: string; options: string[] } },
                onChange: (v) => onFieldChange(field.key, v),
              });
            if (field.schema.kind === 'array')
              return createElement(ArrayField, {
                key: field.key,
                field: field as InspectorField & { schema: { kind: 'array'; label: string; itemLabel: string } },
                onChange: (v) => onFieldChange(field.key, v),
              });
            return createElement(ReadonlyField, { key: field.key, field });
          }),
        ),
      tab === 'provenance' &&
        (provenance
          ? createElement(ProvenanceSection, { info: provenance })
          : createElement('div', { style: { padding: space.xl, color: color.textSubtle, fontSize: fontSize.base } }, 'No provenance data.')),
      tab === 'relations' && createElement(RelationsSection, { relations, onNavigate }),
    ),
  );
}
