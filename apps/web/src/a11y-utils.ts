/**
 * Pure a11y logic — no React imports.
 * React hooks live in a11y.ts; this file is test-friendly.
 */

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

/** Returns true if the pair passes WCAG AA (≥4.5 normal, ≥3.0 large text) */
export function passesWCAG_AA(fg: string, bg: string, largeText = false): boolean {
  return contrastRatio(fg, bg) >= (largeText ? 3.0 : 4.5);
}
