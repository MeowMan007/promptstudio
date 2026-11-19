# ADR-002: Canvas Engine Selection

* Status: Accepted
* Date: 2026-11-17
* Deciders: Prompt Studio core team
* Technical Story: Choose a canvas rendering engine for the prompt-native visual workspace

---

## Context and Problem Statement

Prompt Studio requires a canvas engine to power its visual design workspace. The canvas is the primary surface on which users arrange, connect, and annotate prompt nodes. The engine must feel snappy at scale, support freehand sketching alongside structured editing, produce portable export formats, and ship without licence friction.

The `packages/canvas` boundary (the `CanvasAdapter` interface) insulates application code from engine internals, so swapping engines later is possible but still costly — the right choice now matters.

## Decision Drivers

| Driver | Requirement |
|---|---|
| **Licence** | Must allow commercial use without per-seat or revenue-share fees |
| **Performance** | Smooth at ≥ 500 nodes; low-latency pointer events |
| **Accessibility (a11y)** | Keyboard navigation, ARIA labels, screen-reader support |
| **Export** | First-class SVG and/or PNG export; portable, open file format |
| **Freehand** | Natural freehand drawing integrated with structured shapes |
| **Editing UX** | Rich selection, grouping, text editing, undo/redo |

## Considered Options

* **Option A — Excalidraw (MIT)**
* **Option B — tldraw (Business Source Licence / commercial)**

---

## Decision Outcome

**Chosen: Option A — Excalidraw**

Excalidraw is selected as the canvas engine for Prompt Studio. The MIT licence removes all commercial and legal friction now and in the future. Its JSON scene format pairs well with Prompt Studio's typed project graph — scenes can be diffed, versioned, and round-tripped through the export pipeline without proprietary lock-in. SVG export is robust out of the box. The freehand primitive aligns with the prompt-native, sketch-first philosophy of the workspace. Community momentum reduces long-term maintenance risk.

tldraw's Business Source Licence was the disqualifying factor; accepting a revenue-dependent commercial licence creates budget and legal uncertainty that outweighs its UX and multiplayer advantages at this stage.

### Positive Consequences

* **Free for commercial use** — MIT licence imposes no restrictions as the product grows.
* **Portable file format** — JSON scenes are human-readable, diffable, and importable by third-party tools.
* **SVG export** — high-fidelity vector export is available without custom pipeline work.
* **Freehand drawing** — native support, no additional library integration required.
* **Active community** — bugs are fixed upstream; the project benefits from ecosystem momentum.
* **CanvasAdapter boundary** — the `packages/canvas` abstraction scopes any future engine migration to one package, leaving semantic artifact contracts untouched.

### Negative Consequences

* **No built-in multiplayer** — real-time collaborative editing requires a separate Y.js / CRDT integration if added in the future.
* **Limited custom shape API** — adding novel node types (e.g. prompt-block, branch-merge) requires compositing on top of core or upstream contribution, rather than a first-class shape registry.

---

## Pros and Cons of the Options

### Option A — Excalidraw (MIT)

* ✅ MIT licence — unrestricted commercial use, zero runtime fee
* ✅ Built-in SVG and PNG export; JSON scene format is open and version-control friendly
* ✅ Freehand drawing is a first-class primitive
* ✅ React-first component API; straightforward embedding
* ✅ Active community; regular upstream releases
* ✅ Reasonable ARIA / keyboard support with ongoing a11y improvements
* ❌ No built-in real-time multiplayer (requires Y.js or equivalent)
* ❌ Custom shape types require compositing or patching rather than a registered extension point

### Option B — tldraw (BSL 1.1 / commercial)

* ✅ Polished, Figma-like editing UX
* ✅ Strong typed custom shape API (`ShapeUtil` registry)
* ✅ Real-time multiplayer via tldraw sync (included)
* ✅ Well-documented keyboard and screen-reader support
* ❌ Business Source Licence (BSL 1.1) — commercial deployment requires a paid licence; pricing is quote-based and ongoing
* ❌ Licence cost introduces budget uncertainty at every growth milestone
* ❌ SVG export less comprehensive than Excalidraw's out of the box

---

## CanvasAdapter Interface

All interaction between the application and the canvas engine is mediated by the `CanvasAdapter` interface located in `packages/canvas`. Application code **must not** import Excalidraw APIs directly. This boundary ensures:

1. Engine internals do not leak into business logic or the React component tree outside `packages/canvas`.
2. Layout changes remain separate from semantic graph mutations (canonical truth lives in the project graph, not in engine records).
3. A future engine swap affects only the adapter implementation, not upstream call sites.

```
packages/canvas/
  src/
    CanvasAdapter.ts        ← interface definition
    ExcalidrawAdapter.ts    ← Excalidraw implementation (the chosen engine)
    types.ts                ← shared layout / node types
  index.ts                  ← public surface; exports adapter factory only
```

Editable `.excalidraw` JSON and raster/SVG exports are treated as *projections* of the canonical project graph, not as the source of truth.

---

## Links

* [Excalidraw repository](https://github.com/excalidraw/excalidraw)
* [Excalidraw licence (MIT)](https://github.com/excalidraw/excalidraw/blob/master/LICENSE)
* [tldraw pricing and production licensing](https://tldraw.dev/pricing)
* [tldraw accessibility](https://tldraw.dev/sdk-features/accessibility)
* [tldraw BSL licence](https://github.com/tldraw/tldraw/blob/main/LICENSE.md)
* `packages/canvas` — CanvasAdapter interface (this repository)
* ADR-001 — Project graph canonical model (`docs/adr/ADR-001-*.md`)
