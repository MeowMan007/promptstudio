import { createElement } from 'react';

export type EdgeDefinition = {
  from: string[];
  to: string[];
  derived_inverse_of?: string;
};

export type EdgeRegistry = Record<string, EdgeDefinition>;

function allows(types: string[], artifactType: string): boolean {
  return types.includes('*') || types.includes(artifactType);
}

export function allowedEdgeTypes(
  registry: EdgeRegistry,
  sourceType: string,
  targetType: string,
): string[] {
  return Object.entries(registry)
    .filter(
      ([, edge]) =>
        !edge.derived_inverse_of &&
        allows(edge.from, sourceType) &&
        allows(edge.to, targetType),
    )
    .map(([edgeType]) => edgeType)
    .sort();
}

export function EdgeClassificationPicker({
  registry,
  sourceType,
  targetType,
  onClassify,
}: {
  registry: EdgeRegistry;
  sourceType: string;
  targetType: string;
  onClassify: (edgeType: string) => void;
}) {
  const options = allowedEdgeTypes(registry, sourceType, targetType).filter(
    (edgeType) => edgeType !== 'untyped',
  );
  if (!options.length)
    return createElement(
      'p',
      { role: 'alert', className: 'edge-classification-error' },
      `No edge types allow ${sourceType} → ${targetType}. The connector remains untyped.`,
    );
  return createElement(
    'label',
    { className: 'edge-classification-picker' },
    createElement('span', null, 'Classify untyped connector'),
    createElement(
      'select',
      {
        'aria-label': 'Classify untyped connector',
        defaultValue: '',
        onChange: (event: { currentTarget: { value: string } }) => {
          if (event.currentTarget.value) onClassify(event.currentTarget.value);
        },
      },
      createElement(
        'option',
        { value: '', disabled: true },
        'Choose edge type',
      ),
      ...options.map((option) =>
        createElement('option', { key: option, value: option }, option),
      ),
    ),
  );
}
