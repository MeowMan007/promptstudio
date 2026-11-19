import { describe, expect, it, vi } from 'vitest';
import { createElement } from 'react';
import { renderToStaticMarkup } from 'react-dom/server';
import {
  allowedEdgeTypes,
  EdgeClassificationPicker,
  type EdgeRegistry,
} from './edge-classification';

const registry: EdgeRegistry = {
  implements: { from: ['component'], to: ['requirement'] },
  realized_by: { from: [], to: [], derived_inverse_of: 'implements' },
  relates_to: { from: ['*'], to: ['*'] },
  untyped: { from: ['*'], to: ['*'] },
};

describe('edge classification', () => {
  it('filters allowed pairs and omits derived inverses', () => {
    expect(allowedEdgeTypes(registry, 'component', 'requirement')).toEqual([
      'implements',
      'relates_to',
      'untyped',
    ]);
    expect(allowedEdgeTypes(registry, 'note', 'requirement')).toEqual([
      'relates_to',
      'untyped',
    ]);
  });

  it('renders only allowed classifications and reports rejected pairs', () => {
    const onClassify = vi.fn();
    const markup = renderToStaticMarkup(
      createElement(EdgeClassificationPicker, {
        registry,
        sourceType: 'component',
        targetType: 'requirement',
        onClassify,
      }),
    );
    expect(markup).toContain('implements');
    expect(markup).toContain('relates_to');
    expect(markup).not.toContain('realized_by');
    expect(markup).not.toContain('untyped</option>');
    const rejected = renderToStaticMarkup(
      createElement(EdgeClassificationPicker, {
        registry: { implements: registry.implements },
        sourceType: 'note',
        targetType: 'requirement',
        onClassify,
      }),
    );
    expect(rejected).toContain('role="alert"');
    expect(rejected).toContain('connector remains untyped');
  });
});
