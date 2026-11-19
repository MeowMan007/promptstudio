import { describe, expect, it } from 'vitest';
import { workspaceScaffold } from './index';

describe('web workspace scaffold', () => {
  it('exports its scaffold marker', () => {
    expect(workspaceScaffold).toBe(true);
  });
});
