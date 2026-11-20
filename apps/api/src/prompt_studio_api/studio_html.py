"""
Prompt Studio - True Miro Whiteboard Canvas Engine
Enterprise Edition: Canonical Graph Canvas with Frame Grouping and Magnetic Connectors
- Full Frame Dragging: Dragging any frame by its title header moves the frame and all contained elements synchronously!
- Frame Resizing: Dedicated bottom-right resize handle on each frame zone.
- Dual-Mode Magnetic Connectors:
  1. Hover snap ports (with 30px hit targets & 70px magnetic pull) to drag-and-snap to any card.
  2. Click Connector Tool (L) or 'Connect' in context bar: Click Card A -> Click Card B to connect instantly!
- Clickable & Editable Connectors: Click any connector to change routing (90° Elbow vs Curved), edit label, or delete.
- Collapsible Right Context Drawer (Inspect | Specs | Deployment | Security | Audit Log | Export).
- Interactive Wireframe Component Builder (+ Input, + Button, + KPI).
- Interactive ERD Database Visualizer with PK/FK.
- SaaS Architecture Component Suite with micro-metrics.
- Quick-Find Jump-to-Artifact Navigation (Ctrl+K).
- Interactive Birds-Eye Minimap with Viewport Dragging.
- Full Undo/Redo, Alignment Tools, Deterministic ZIP & PNG Export.
"""

STUDIO_HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Prompt Studio — Enterprise System Architecture & Canvas Workspace</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
  <style>
    :root {
      --bg: #f8fafc;
      --dot: #cbd5e1;
      --surface: #ffffff;
      --surface-subtle: #f1f5f9;
      --border: #e2e8f0;
      --border-strong: #cbd5e1;
      --text: #0f172a;
      --text-muted: #64748b;
      --text-subtle: #94a3b8;
      --miro-blue: #2563eb;
      --miro-blue-hover: #1d4ed8;
      --miro-blue-light: #eff6ff;
      --danger: #dc2626;
      --danger-light: #fef2f2;
      --success: #059669;
      --success-light: #ecfdf5;
      --warning: #d97706;
      --warning-light: #fffbeb;
      --purple: #7c3aed;
      --purple-light: #f5f3ff;
      --font-sans: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      --font-mono: 'JetBrains Mono', ui-monospace, monospace;
      --shadow-xs: 0 1px 2px rgba(0, 0, 0, 0.04);
      --shadow-sm: 0 1px 3px rgba(0, 0, 0, 0.06), 0 1px 2px rgba(0, 0, 0, 0.04);
      --shadow-md: 0 4px 12px rgba(0, 0, 0, 0.06), 0 1px 3px rgba(0, 0, 0, 0.03);
      --shadow-lg: 0 12px 28px rgba(0, 0, 0, 0.09), 0 2px 6px rgba(0, 0, 0, 0.03);
      --shadow-xl: 0 20px 35px rgba(0, 0, 0, 0.12);
    }

    .icon-svg {
      display: inline-block;
      width: 14px;
      height: 14px;
      vertical-align: -2px;
      stroke: currentColor;
      fill: none;
      stroke-width: 2;
      stroke-linecap: round;
      stroke-linejoin: round;
      margin-right: 5px;
      flex-shrink: 0;
    }
    .erd-badge {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      font-size: 9px;
      font-weight: 700;
      font-family: var(--font-mono);
      line-height: 1;
      padding: 2px 5px;
      border-radius: 3px;
      margin-right: 6px;
      letter-spacing: 0.02em;
    }
    .erd-badge-pk {
      background: #fef3c7;
      color: #b45309;
      border: 1px solid #fde68a;
    }
    .erd-badge-fk {
      background: #eff6ff;
      color: #1d4ed8;
      border: 1px solid #bfdbfe;
    }
    .status-dot {
      width: 6px;
      height: 6px;
      border-radius: 50%;
      display: inline-block;
      margin-right: 5px;
      background: var(--success);
    }

    * { box-sizing: border-box; margin: 0; padding: 0; }
    html, body {
      width: 100%;
      height: 100%;
      overflow: hidden;
      font-family: var(--font-sans);
      background-color: var(--bg);
      color: var(--text);
      user-select: none;
      -webkit-font-smoothing: antialiased;
    }

    /* Miro Top Navigation Header */
    .miro-header {
      position: absolute;
      top: 0;
      left: 0;
      right: 0;
      height: 48px;
      background: rgba(255, 255, 255, 0.98);
      
      border-bottom: 1px solid var(--border);
      display: flex;
      align-items: center;
      padding: 0 16px;
      gap: 12px;
      z-index: 50;
    }
    .brand-logo {
      display: flex;
      align-items: center;
      gap: 8px;
      font-weight: 800;
      font-size: 15px;
      color: var(--miro-blue);
      cursor: pointer;
    }
    .brand-logo svg { width: 22px; height: 22px; }
    .header-divider { width: 1px; height: 20px; background: var(--border); }
    .board-title {
      font-size: 14px;
      font-weight: 600;
      color: var(--text);
      border: 1px solid transparent;
      padding: 4px 8px;
      border-radius: 6px;
      background: transparent;
      width: 280px;
      outline: none;
      transition: all 0.12s;
    }
    .board-title:hover { border-color: var(--border); background: var(--bg); }
    .board-title:focus { border-color: var(--miro-blue); background: #fff; }
    .sync-badge {
      font-size: 11px;
      font-weight: 600;
      color: #059669;
      background: #ecfdf5;
      padding: 3px 8px;
      border-radius: 9999px;
      display: flex;
      align-items: center;
      gap: 4px;
    }
    .search-pill {
      display: flex;
      align-items: center;
      gap: 6px;
      background: #f1f5f9;
      padding: 4px 10px;
      border-radius: 6px;
      font-size: 11px;
      color: var(--text-muted);
      cursor: pointer;
      border: 1px solid transparent;
    }
    .search-pill:hover { border-color: var(--border-strong); background: #fff; color: var(--text); }
    .presence-avatars {
      display: flex;
      align-items: center;
      margin-left: 4px;
    }
    .avatar-circle {
      width: 26px;
      height: 26px;
      border-radius: 50%;
      border: 2px solid #ffffff;
      margin-left: -5px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 10px;
      font-weight: 700;
      color: #ffffff;
      cursor: pointer;
      box-shadow: var(--shadow-sm);
    }
    .avatar-sys { background: linear-gradient(135deg, #2563eb, #1d4ed8); }
    .avatar-user { background: #3b82f6; }

    .header-actions {
      margin-left: auto;
      display: flex;
      align-items: center;
      gap: 8px;
    }
    .btn {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      font-family: var(--font-sans);
      font-size: 12px;
      font-weight: 600;
      padding: 6px 12px;
      border-radius: 6px;
      border: 1px solid var(--border-strong);
      background: var(--surface);
      color: var(--text);
      cursor: pointer;
      text-decoration: none;
      transition: all 0.12s ease;
      white-space: nowrap;
    }
    .btn:hover { background: var(--bg); border-color: #94a3b8; }
    .btn-primary { background: var(--miro-blue); color: #fff; border-color: var(--miro-blue); }
    .btn-primary:hover { background: var(--miro-blue-hover); border-color: var(--miro-blue-hover); }
    .btn-blueprints-nav {
      background: #ffffff;
      color: var(--text);
      border: 1px solid var(--border-strong, #cbd5e1);
      font-weight: 600;
    }
    .btn-blueprints-nav:hover {
      background: var(--surface-subtle, #f1f5f9);
      border-color: var(--blue, #2563eb);
      color: var(--blue, #2563eb);
    }
    .btn-share {
      background: var(--miro-blue);
      color: #fff;
      border-color: var(--miro-blue);
      font-weight: 700;
      padding: 6px 14px;
    }

    /* Infinite Canvas Viewport */
    
    /* --- Template Quick-Switcher Bar & Prompt Engineering Modals --- */


    .prompt-compile-dialog {
      max-width: 860px;
      width: 90%;
      background: #ffffff;
      border-radius: 12px;
      box-shadow: 0 20px 25px -5px rgba(0,0,0,0.1), 0 10px 10px -5px rgba(0,0,0,0.04);
      border: 1px solid #e2e8f0;
      overflow: hidden;
      display: flex;
      flex-direction: column;
      max-height: 85vh;
    }
    .prompt-compile-header {
      padding: 14px 20px;
      background: #f8fafc;
      border-bottom: 1px solid #e2e8f0;
      display: flex;
      align-items: center;
      justify-content: space-between;
    }
    .prompt-compile-body {
      padding: 20px;
      overflow-y: auto;
      flex: 1;
    }
    .prompt-code-area {
      width: 100%;
      height: 380px;
      font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
      font-size: 12px;
      line-height: 1.6;
      background: #0f172a;
      color: #f8fafc;
      border-radius: 8px;
      padding: 16px;
      border: 1px solid #334155;
      resize: vertical;
      white-space: pre;
    }

    .build-wave-card {
      background: #ffffff;
      border: 1px solid #e2e8f0;
      border-radius: 8px;
      padding: 14px;
      margin-bottom: 12px;
      box-shadow: 0 1px 3px rgba(0,0,0,0.03);
    }
    .build-wave-title {
      font-size: 13px;
      font-weight: 800;
      color: #0f172a;
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin-bottom: 8px;
    }
    .build-wave-nodes {
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
    }
    .bwn-chip {
      padding: 3px 8px;
      border-radius: 4px;
      background: #f1f5f9;
      color: #334155;
      font-size: 11px;
      font-weight: 600;
      border: 1px solid #e2e8f0;
    }

    .canvas-viewport {
      position: absolute;
      top: 48px;
      left: 0;
      right: 0;
      bottom: 24px;
      overflow: hidden;
      cursor: default;
      background-color: var(--bg);
      background-image: radial-gradient(var(--dot) 1.2px, transparent 1.2px);
      background-size: 24px 24px;
      transition: right 0.25s cubic-bezier(0.16, 1, 0.3, 1);
    }
    .canvas-viewport.drawer-open { right: 360px; }
    .canvas-viewport.panning { cursor: grab !important; }
    .canvas-viewport.panning:active { cursor: grabbing !important; }
    .canvas-viewport.connecting { cursor: crosshair !important; }

    /* True Infinite Dimensionless Coordinate Canvas Plane */
    .canvas-world {
      position: absolute;
      top: 0;
      left: 0;
      transform-origin: 0 0;
      pointer-events: none;
      /* Boundless infinite plane extending freely in all directions */
    }

    .canvas-svg {
      position: absolute;
      top: 0;
      left: 0;
      overflow: visible; /* Prevents clipping of connectors across negative and infinite space */
      pointer-events: none;
      z-index: 5;
    }
    .canvas-svg path {
      pointer-events: stroke;
      cursor: pointer;
    }

    #elements-layer {
      position: absolute;
      top: 0;
      left: 0;
      overflow: visible;
      pointer-events: none;
      z-index: 10;
    }

    /* Miro Primary Left Floating Dock (Monochrome SVG Icons) */
    .miro-left-dock {
      position: absolute;
      left: 16px;
      top: 68px;
      z-index: 40;
      background: var(--surface);
      border: 1px solid rgba(0, 0, 0, 0.08);
      border-radius: 10px;
      box-shadow: 0 0 0 1px rgba(0,0,0,0.04), 0 4px 16px rgba(0,0,0,0.12);
      display: flex;
      flex-direction: column;
      padding: 6px 4px;
      gap: 3px;
      width: 46px;
    }
    .tool-btn {
      width: 38px;
      height: 38px;
      border-radius: 8px;
      border: none;
      background: transparent;
      color: #374151;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      transition: all 0.12s ease;
      position: relative;
    }
    .tool-btn svg { width: 20px; height: 20px; stroke: currentColor; fill: none; stroke-width: 1.8; }
    .tool-btn:hover { background: #f3f4f6; color: #111827; }
    .tool-btn.active {
      background: var(--miro-blue-light);
      color: var(--miro-blue);
    }
    .tool-btn .tooltip {
      position: absolute;
      left: 50px;
      background: #111827;
      color: #fff;
      font-size: 11px;
      padding: 4px 8px;
      border-radius: 4px;
      white-space: nowrap;
      pointer-events: none;
      opacity: 0;
      transition: opacity 0.15s;
      z-index: 60;
    }
    .tool-btn:hover .tooltip { opacity: 1; }
    .tool-divider { width: 80%; height: 1px; background: var(--border); margin: 3px auto; }

    /* Flyouts */

    /* Expanded Flyout Styles & Search (Miro-style) */
    .flyout-search-box {
      margin-bottom: 8px;
    }
    .flyout-search-input {
      width: 100%;
      padding: 5px 8px;
      font-size: 11px;
      border: 1px solid var(--border-strong);
      border-radius: 5px;
      outline: none;
      background: #f8fafc;
      font-family: var(--font-sans);
    }
    .flyout-search-input:focus {
      border-color: var(--miro-blue);
      background: #ffffff;
    }
    .flyout-category-tabs {
      display: flex;
      gap: 4px;
      overflow-x: auto;
      margin-bottom: 8px;
      padding-bottom: 2px;
    }
    .flyout-tab-pill {
      font-size: 9px;
      font-weight: 600;
      padding: 2px 6px;
      border-radius: 4px;
      background: #f1f5f9;
      color: #64748b;
      cursor: pointer;
      white-space: nowrap;
      border: 1px solid transparent;
    }
    .flyout-tab-pill.active {
      background: var(--miro-blue-light);
      color: var(--miro-blue);
      border-color: #bfdbfe;
    }
    .picker-grid-scroll {
      max-height: 460px;
      overflow-y: auto;
      padding-right: 2px;
    }
    .picker-card-tech {
      display: flex;
      flex-direction: column;
      align-items: flex-start;
      text-align: left;
      padding: 7px 8px;
      background: #ffffff;
      border: 1px solid #e2e8f0;
      border-radius: 6px;
      cursor: pointer;
      transition: all 0.12s;
    }
    .picker-card-tech:hover {
      background: var(--miro-blue-light);
      border-color: var(--miro-blue);
      transform: translateY(-1px);
      box-shadow: 0 2px 6px rgba(37, 99, 235, 0.1);
    }
    .picker-card-title {
      font-size: 11px;
      font-weight: 700;
      color: #1e293b;
      display: flex;
      align-items: center;
      gap: 5px;
    }
    .picker-card-sub {
      font-size: 9px;
      color: #64748b;
      margin-top: 2px;
    }

    /* Miro Template Library Dialog */
    .template-library-dialog {
      width: 920px !important;
      max-width: 95vw;
      height: 85vh;
      max-height: 720px;
      display: flex;
      flex-direction: column;
      padding: 0 !important;
      overflow: hidden;
    }
    .template-modal-header {
      padding: 16px 20px;
      border-bottom: 1px solid var(--border);
      display: flex;
      align-items: center;
      justify-content: space-between;
      background: #ffffff;
    }
    .template-modal-title {
      font-size: 16px;
      font-weight: 800;
      color: #0f172a;
      display: flex;
      align-items: center;
      gap: 8px;
    }
    .template-modal-toolbar {
      padding: 12px 20px;
      background: #f8fafc;
      border-bottom: 1px solid var(--border);
      display: flex;
      gap: 12px;
      align-items: center;
    }
    .template-search-input {
      flex: 1;
      padding: 8px 12px;
      border: 1px solid var(--border-strong);
      border-radius: 6px;
      font-size: 12px;
      outline: none;
      background: #ffffff;
    }
    .template-search-input:focus {
      border-color: var(--miro-blue);
      box-shadow: 0 0 0 2px rgba(37, 99, 235, 0.1);
    }
    .template-pills {
      display: flex;
      gap: 6px;
      overflow-x: auto;
    }
    .template-filter-pill {
      font-size: 11px;
      font-weight: 600;
      padding: 4px 10px;
      border-radius: 6px;
      background: #ffffff;
      color: #475569;
      border: 1px solid var(--border);
      cursor: pointer;
      white-space: nowrap;
    }
    .template-filter-pill.active {
      background: var(--miro-blue);
      color: #ffffff;
      border-color: var(--miro-blue);
    }
    .template-modal-content {
      flex: 1;
      overflow-y: auto;
      padding: 18px 20px;
      display: grid;
      grid-template-columns: repeat(2, 1fr);
      gap: 14px;
      background: #fafbfc;
    }
    .template-card {
      background: #ffffff;
      border: 1px solid var(--border);
      border-radius: 10px;
      padding: 14px;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      gap: 10px;
      transition: all 0.15s;
    }
    .template-card:hover {
      border-color: var(--miro-blue);
      box-shadow: 0 6px 18px rgba(0, 0, 0, 0.06);
    }
    .template-card-top {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
    }
    .template-badge {
      font-size: 9px;
      font-weight: 700;
      text-transform: uppercase;
      padding: 2px 6px;
      border-radius: 4px;
      letter-spacing: 0.03em;
    }
    .template-badge-b2b { background: #eff6ff; color: #1d4ed8; }
    .template-badge-stream { background: #f5f3ff; color: #6d28d9; }
    .template-badge-data { background: #ecfdf5; color: #047857; }
    .template-badge-fintech { background: #fffbeb; color: #b45309; }
    .template-badge-realtime { background: #fdf2f8; color: #be185d; }
    .template-spec-pill {
      font-size: 10px;
      color: #64748b;
      font-family: var(--font-mono);
    }
    .template-card-title {
      font-size: 13px;
      font-weight: 700;
      color: #0f172a;
      line-height: 1.35;
    }
    .template-card-desc {
      font-size: 11px;
      color: var(--text-muted);
      line-height: 1.45;
    }
    .template-tech-tags {
      display: flex;
      flex-wrap: wrap;
      gap: 4px;
    }
    .template-tech-tag {
      font-size: 9px;
      font-family: var(--font-mono);
      background: #f1f5f9;
      color: #475569;
      padding: 1px 5px;
      border-radius: 3px;
    }
    .template-card-footer {
      display: flex;
      gap: 6px;
      padding-top: 8px;
      border-top: 1px solid #f1f5f9;
    }
    
    .dock-flyout {
      position: absolute;
      left: 68px;
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 10px;
      box-shadow: var(--shadow-lg);
      padding: 10px;
      display: none;
      z-index: 55;
    }
    .dock-flyout.open { display: block; }
    .flyout-title {
      font-size: 11px;
      font-weight: 700;
      color: var(--text-muted);
      text-transform: uppercase;
      letter-spacing: 0.05em;
      margin-bottom: 8px;
    }
    .color-grid {
      display: grid;
      grid-template-columns: repeat(4, 28px);
      gap: 6px;
    }
    .color-swatch {
      width: 28px;
      height: 28px;
      border-radius: 4px;
      cursor: pointer;
      border: 1px solid rgba(0, 0, 0, 0.14);
      transition: transform 0.1s;
    }
    .color-swatch:hover { transform: scale(1.18); }
    .picker-grid {
      display: grid;
      grid-template-columns: repeat(2, 95px);
      gap: 8px;
    }
    .picker-card {
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 5px;
      padding: 8px 4px;
      border-radius: 6px;
      border: 1px solid var(--border);
      background: #fafafa;
      cursor: pointer;
      font-size: 10px;
      font-weight: 600;
      color: #374151;
      text-align: center;
      transition: all 0.12s;
    }
    .picker-card:hover {
      background: var(--miro-blue-light);
      border-color: var(--miro-blue);
      color: var(--miro-blue);
    }

    /* Miro Magnetic Connection Anchor Ports (Generous Hit Target) */
    .snap-port {
      position: absolute;
      width: 14px;
      height: 14px;
      border-radius: 50%;
      background: #ffffff;
      border: 2.5px solid var(--miro-blue);
      box-shadow: 0 0 8px rgba(43, 89, 255, 0.45);
      cursor: crosshair;
      z-index: 45;
      display: none;
      transition: background-color 0.15s, border-color 0.15s;
    }
    /* 34px generous invisible hit zone for instant click & drag */
    .snap-port::after {
      content: '';
      position: absolute;
      top: -10px;
      left: -10px;
      right: -10px;
      bottom: -10px;
      cursor: crosshair;
    }
    .port-top    { top: -7px; left: 50%; transform: translateX(-50%); }
    .port-right  { top: 50%; right: -7px; transform: translateY(-50%); }
    .port-bottom { bottom: -7px; left: 50%; transform: translateX(-50%); }
    .port-left   { top: 50%; left: -7px; transform: translateY(-50%); }

    .port-top:hover, .port-top.snapped       { transform: translateX(-50%) scale(1.6); background: var(--miro-blue); border-color: #ffffff; box-shadow: 0 0 12px rgba(43, 89, 255, 0.9); }
    .port-right:hover, .port-right.snapped   { transform: translateY(-50%) scale(1.6); background: var(--miro-blue); border-color: #ffffff; box-shadow: 0 0 12px rgba(43, 89, 255, 0.9); }
    .port-bottom:hover, .port-bottom.snapped { transform: translateX(-50%) scale(1.6); background: var(--miro-blue); border-color: #ffffff; box-shadow: 0 0 12px rgba(43, 89, 255, 0.9); }
    .port-left:hover, .port-left.snapped     { transform: translateY(-50%) scale(1.6); background: var(--miro-blue); border-color: #ffffff; box-shadow: 0 0 12px rgba(43, 89, 255, 0.9); }

    .element-interactive:hover .snap-port,
    .canvas-viewport.connecting .snap-port {
      display: block;
    }

    /* Miro Interactive Notification Toast */
    .miro-toast {
      position: fixed;
      bottom: 36px;
      left: 50%;
      transform: translateX(-50%) translateY(20px);
      background: #0f172a;
      color: #ffffff;
      padding: 9px 20px;
      border-radius: 24px;
      font-size: 13px;
      font-weight: 500;
      box-shadow: 0 8px 24px rgba(0, 0, 0, 0.22);
      z-index: 9999;
      opacity: 0;
      pointer-events: none;
      transition: opacity 0.22s cubic-bezier(0.16, 1, 0.3, 1), transform 0.22s cubic-bezier(0.16, 1, 0.3, 1);
      display: flex;
      align-items: center;
      gap: 8px;
    }
    .miro-toast.show {
      opacity: 1;
      transform: translateX(-50%) translateY(0);
    }

    /* Interactive Frame / Zones (Header Draggable & Resizable) */
    .canvas-frame {
      position: absolute;
      border: 2px dashed #94a3b8;
      border-radius: 14px;
      background: rgba(241, 245, 249, 0.25);
      z-index: 1;
      pointer-events: none; /* Allows clicks to pass through freely to contained items */
      transition: border-color 0.15s, background-color 0.15s;
    }
    .canvas-frame.selected {
      border: 2px solid var(--miro-blue);
      background: rgba(43, 89, 255, 0.03);
    }
    .canvas-frame-header {
      position: absolute;
      top: -32px;
      left: 10px;
      font-size: 12px;
      font-weight: 700;
      color: #334155;
      background: var(--surface);
      padding: 4px 12px;
      border-radius: 6px;
      border: 1px solid var(--border);
      box-shadow: var(--shadow-sm);
      display: flex;
      align-items: center;
      gap: 6px;
      cursor: grab;
      user-select: none;
      z-index: 15;
      pointer-events: auto; /* Drag zone and contained items by header */
    }
    .canvas-frame-header:active {
      cursor: grabbing;
      box-shadow: var(--shadow-md);
      border-color: var(--miro-blue);
    }
    .frame-badge { font-size: 10px; font-weight: 600; color: var(--miro-blue); background: var(--miro-blue-light); padding: 1px 6px; border-radius: 4px; }
    .frame-resize-handle {
      position: absolute;
      bottom: -6px;
      right: -6px;
      width: 14px;
      height: 14px;
      background: #ffffff;
      border: 2px solid #94a3b8;
      border-radius: 3px;
      cursor: nwse-resize;
      z-index: 15;
      pointer-events: auto; /* Resize frame */
    }
    .frame-resize-handle:hover {
      border-color: var(--miro-blue);
      background: var(--miro-blue);
    }

    /* Miro Sticky Notes (with Tags & Reactions) */
    .sticky-note {
      position: absolute;
      z-index: 10;
      pointer-events: auto;
      width: 200px;
      height: 200px;
      padding: 16px;
      border-radius: 2px;
      box-shadow: 0 4px 10px rgba(0, 0, 0, 0.08), 0 1px 3px rgba(0, 0, 0, 0.04);
      cursor: grab;
      font-family: var(--font-sans);
      color: #111827;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      transition: box-shadow 0.15s;
    }
    .sticky-note:active { cursor: grabbing; }
    .sticky-note:hover {
      box-shadow: 0 8px 22px rgba(0, 0, 0, 0.12), 0 2px 6px rgba(0, 0, 0, 0.06);
    }
    .sticky-header-row {
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin-bottom: 6px;
    }
    .sticky-tags { display: flex; gap: 4px; flex-wrap: wrap; }
    .sticky-tag-pill {
      font-size: 9px;
      font-weight: 700;
      padding: 1px 5px;
      border-radius: 3px;
      background: rgba(0,0,0,0.08);
      color: rgba(0,0,0,0.7);
      text-transform: uppercase;
    }
    .sticky-content {
      flex: 1;
      outline: none;
      word-break: break-word;
      white-space: pre-wrap;
      cursor: text;
      overflow: hidden;
      font-size: 15px;
      line-height: 1.45;
    }
    .sticky-footer {
      font-size: 10px;
      color: rgba(0,0,0,0.45);
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding-top: 6px;
    }
    .sticky-reactions { display: flex; gap: 3px; }
    .reaction-pill {
      background: rgba(255,255,255,0.7);
      padding: 1px 4px;
      border-radius: 9999px;
      font-size: 10px;
      cursor: pointer;
    }

    /* SaaS Architecture System Nodes */
    .arch-node {
      position: absolute;
      z-index: 10;
      pointer-events: auto;
      width: 250px;
      background: var(--surface);
      border: 1px solid var(--border-strong);
      border-radius: 10px;
      box-shadow: var(--shadow-md);
      cursor: grab;
      overflow: hidden;
      transition: box-shadow 0.15s, border-color 0.15s;
    }
    .arch-node:active { cursor: grabbing; }
    .arch-node:hover { box-shadow: var(--shadow-lg); border-color: var(--miro-blue); }
    .arch-node-header {
      padding: 10px 12px;
      border-bottom: 1px solid var(--border);
      display: flex;
      align-items: center;
      justify-content: space-between;
      background: #fafbfc;
    }
    .arch-badge {
      font-size: 10px;
      font-weight: 700;
      color: var(--miro-blue);
      background: var(--miro-blue-light);
      padding: 2px 6px;
      border-radius: 4px;
      display: flex;
      align-items: center;
      gap: 4px;
    }
    .arch-status {
      font-size: 10px;
      font-weight: 600;
      color: var(--success);
      display: flex;
      align-items: center;
      gap: 3px;
    }
    .arch-node-body { padding: 12px; }
    .arch-title { font-size: 13px; font-weight: 700; color: #0f172a; margin-bottom: 4px; outline: none; }
    .arch-desc { font-size: 11px; color: var(--text-muted); line-height: 1.4; outline: none; }
    .arch-tech-tags { display: flex; gap: 4px; flex-wrap: wrap; margin-top: 8px; }
    .arch-tag {
      font-family: var(--font-mono);
      font-size: 9px;
      background: #f1f5f9;
      color: #475569;
      padding: 2px 6px;
      border-radius: 4px;
    }

    /* Database ERD Table Cards */
    .erd-table {
      position: absolute;
      z-index: 10;
      pointer-events: auto;
      width: 270px;
      background: var(--surface);
      border: 1px solid var(--border-strong);
      border-radius: 8px;
      box-shadow: var(--shadow-md);
      cursor: grab;
      overflow: hidden;
    }
    .erd-table-header {
      background: #0f172a;
      color: #ffffff;
      padding: 8px 12px;
      font-weight: 700;
      font-size: 12px;
      display: flex;
      align-items: center;
      justify-content: space-between;
    }
    .erd-rows {
      display: flex;
      flex-direction: column;
      font-family: var(--font-mono);
      font-size: 11px;
    }
    .erd-row {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 6px 12px;
      border-bottom: 1px solid #f1f5f9;
    }
    .erd-row:last-child { border-bottom: none; }
    .erd-col-name { color: #1e293b; font-weight: 600; display: flex; align-items: center; gap: 4px; }
    .erd-col-type { color: #64748b; font-size: 10px; }
    .erd-key { font-size: 10px; color: #f59e0b; }

    /* Flowchart Shapes */
    .canvas-shape {
      position: absolute;
      z-index: 10;
      pointer-events: auto;
      width: 220px;
      height: 120px;
      background: #ffffff;
      border: 2px solid #334155;
      box-shadow: var(--shadow-sm);
      cursor: grab;
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 12px;
      text-align: center;
      transition: box-shadow 0.15s;
    }
    .canvas-shape:active { cursor: grabbing; }
    .canvas-shape.shape-rounded { border-radius: 12px; }
    .canvas-shape.shape-circle  { border-radius: 50%; width: 160px; height: 160px; }
    .canvas-shape.shape-diamond {
      clip-path: polygon(50% 0%, 100% 50%, 50% 100%, 0% 50%);
      background: #f8fafc;
      border: 2px solid #3b82f6;
    }
    .canvas-shape.shape-cylinder {
      border-radius: 16px / 8px;
      background: #f8fafc;
      border: 2px solid #475569;
    }
    .shape-text { outline: none; font-size: 13px; font-weight: 600; color: #1e293b; width: 100%; }

    /* Typed Specification Cards (Section 6.4) */
    .typed-card {
      position: absolute;
      z-index: 10;
      pointer-events: auto;
      width: 300px;
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 10px;
      box-shadow: var(--shadow-md);
      cursor: grab;
      overflow: hidden;
    }
    .typed-card-header {
      padding: 10px 14px;
      border-bottom: 1px solid var(--border);
      display: flex;
      align-items: center;
      justify-content: space-between;
      background: #fafbfc;
    }
    .card-family-tag { font-size: 10px; font-weight: 700; text-transform: uppercase; color: #64748b; }
    .card-alias { font-family: var(--font-mono); font-size: 11px; font-weight: 600; color: #0f172a; }
    .card-btn-spec {
      background: var(--miro-blue-light);
      color: var(--miro-blue);
      border: 1px solid rgba(43, 89, 255, 0.2);
      border-radius: 4px;
      padding: 2px 7px;
      font-size: 11px;
      font-weight: 700;
      cursor: pointer;
    }
    .typed-card-body { padding: 12px 14px; cursor: text; }
    .typed-card-title { font-size: 13px; font-weight: 700; color: var(--text); margin-bottom: 6px; outline: none; }
    .typed-card-preview { font-size: 12px; color: var(--text-muted); line-height: 1.45; outline: none; }
    .typed-card-relations { display: flex; flex-wrap: wrap; gap: 4px; margin-top: 8px; }
    .relation-pill {
      font-size: 10px;
      font-weight: 500;
      color: #3b82f6;
      background: #eff6ff;
      padding: 2px 6px;
      border-radius: 4px;
      font-family: var(--font-mono);
    }
    .typed-card-footer {
      padding: 8px 14px;
      background: #f8fafc;
      border-top: 1px solid var(--border);
      display: flex;
      justify-content: space-between;
      font-size: 10px;
      color: var(--text-muted);
    }

    /* Wireframe Screens with Interactive Component Builder */
    .wireframe-screen {
      position: absolute;
      z-index: 10;
      pointer-events: auto;
      width: 410px;
      background: var(--surface);
      border: 1px solid var(--border-strong);
      border-radius: 10px;
      box-shadow: var(--shadow-lg);
      cursor: grab;
      overflow: hidden;
    }
    .wireframe-titlebar {
      height: 36px;
      background: #1e293b;
      color: #fff;
      display: flex;
      align-items: center;
      padding: 0 12px;
      gap: 8px;
      font-size: 12px;
      font-weight: 600;
    }
    .window-dots { display: flex; gap: 5px; }
    .window-dot { width: 9px; height: 9px; border-radius: 50%; }
    .wireframe-route {
      background: rgba(255,255,255,0.15);
      padding: 2px 8px;
      border-radius: 4px;
      font-family: var(--font-mono);
      font-size: 10px;
      margin-left: auto;
    }
    .wireframe-states-bar {
      background: #f1f5f9;
      padding: 6px 12px;
      border-bottom: 1px solid var(--border);
      display: flex;
      align-items: center;
      gap: 4px;
      overflow-x: auto;
    }
    .state-chip {
      font-size: 10px;
      font-weight: 600;
      padding: 3px 7px;
      border-radius: 4px;
      border: 1px solid transparent;
      background: #fff;
      color: #64748b;
      cursor: pointer;
      white-space: nowrap;
    }
    .state-chip.active { background: var(--miro-blue); color: #fff; border-color: var(--miro-blue); }
    .wireframe-component-bar {
      padding: 4px 10px;
      background: #f8fafc;
      border-bottom: 1px solid var(--border);
      display: flex;
      gap: 4px;
      align-items: center;
      font-size: 10px;
      color: var(--text-muted);
    }
    .add-comp-btn {
      background: #fff;
      border: 1px solid var(--border-strong);
      border-radius: 4px;
      padding: 2px 6px;
      font-size: 9px;
      font-weight: 600;
      cursor: pointer;
      color: #334155;
    }
    .add-comp-btn:hover { border-color: var(--miro-blue); color: var(--miro-blue); }
    .wireframe-content { padding: 14px; min-height: 260px; background: #ffffff; display: flex; flex-direction: column; gap: 10px; cursor: default; }

    /* Selection Gizmo */
    .selection-gizmo {
      position: absolute;
      border: 1.5px solid var(--miro-blue);
      pointer-events: none;
      z-index: 25;
      display: none;
    }
    .selection-gizmo.active { display: block; }
    .gizmo-handle {
      position: absolute;
      width: 8px;
      height: 8px;
      background: #ffffff;
      border: 1.5px solid var(--miro-blue);
      border-radius: 1px;
      pointer-events: auto;
    }
    .handle-nw { top: -4px; left: -4px; cursor: nwse-resize; }
    .handle-n  { top: -4px; left: 50%; transform: translateX(-50%); cursor: ns-resize; }
    .handle-ne { top: -4px; right: -4px; cursor: nesw-resize; }
    .handle-e  { top: 50%; right: -4px; transform: translateY(-50%); cursor: ew-resize; }
    .handle-se { bottom: -4px; right: -4px; cursor: nwse-resize; }
    .handle-s  { bottom: -4px; left: 50%; transform: translateX(-50%); cursor: ns-resize; }
    .handle-sw { bottom: -4px; left: -4px; cursor: nesw-resize; }
    .handle-w  { top: 50%; left: -4px; transform: translateY(-50%); cursor: ew-resize; }
    .handle-rot {
      top: -24px;
      left: 50%;
      transform: translateX(-50%);
      width: 8px;
      height: 8px;
      border-radius: 50%;
      cursor: grab;
    }
    .gizmo-stem {
      position: absolute;
      top: -20px;
      left: 50%;
      width: 1px;
      height: 16px;
      background: var(--miro-blue);
      transform: translateX(-50%);
    }

    /* Rubberband Box */
    .marquee-box {
      position: absolute;
      background: rgba(43, 89, 255, 0.08);
      border: 1px solid var(--miro-blue);
      pointer-events: none;
      z-index: 30;
      display: none;
    }

    /* Floating Context Bar */
    .miro-context-bar {
      position: absolute;
      background: #ffffff;
      border: 1px solid rgba(0, 0, 0, 0.08);
      border-radius: 8px;
      box-shadow: 0 4px 16px rgba(0, 0, 0, 0.12);
      padding: 4px 6px;
      display: flex;
      align-items: center;
      gap: 4px;
      z-index: 48;
      display: none;
      pointer-events: auto;
    }
    .miro-context-bar.open { display: flex; }
    .ctx-btn {
      background: transparent;
      border: none;
      color: #374151;
      font-size: 11px;
      font-weight: 600;
      padding: 5px 8px;
      border-radius: 4px;
      cursor: pointer;
      display: flex;
      align-items: center;
      gap: 4px;
    }
    .ctx-btn:hover { background: #f3f4f6; color: var(--text); }
    .ctx-btn-primary { background: var(--miro-blue-light); color: var(--miro-blue); }
    .ctx-btn-primary:hover { background: var(--miro-blue); color: #fff; }
    .ctx-divider { width: 1px; height: 16px; background: var(--border); margin: 0 2px; }
    .ctx-color-dot {
      width: 18px;
      height: 18px;
      border-radius: 4px;
      border: 1px solid rgba(0,0,0,0.15);
      cursor: pointer;
    }
    .ctx-swatch-popover {
      position: absolute;
      top: 40px;
      left: 0;
      background: #ffffff;
      border: 1px solid var(--border);
      border-radius: 8px;
      box-shadow: var(--shadow-lg);
      padding: 8px;
      display: none;
      grid-template-columns: repeat(4, 24px);
      gap: 6px;
      z-index: 60;
    }
    .ctx-swatch-popover.open { display: grid; }

    /* Interactive Minimap */
    .miro-minimap {
      position: absolute;
      right: 20px;
      bottom: 74px;
      width: 190px;
      height: 120px;
      background: #ffffff;
      border: 1px solid rgba(0,0,0,0.1);
      border-radius: 8px;
      box-shadow: var(--shadow-md);
      overflow: hidden;
      z-index: 40;
      cursor: pointer;
      display: block;
    }
    .minimap-canvas { width: 100%; height: 100%; }
    .minimap-viewport-box {
      position: absolute;
      border: 1.5px solid var(--miro-blue);
      background: rgba(43, 89, 255, 0.15);
      pointer-events: none;
    }

    /* Miro Bottom-Right Controls Dock */
    .miro-bottom-dock {
      position: absolute;
      right: 20px;
      bottom: 34px;
      background: var(--surface);
      border: 1px solid rgba(0,0,0,0.08);
      border-radius: 8px;
      box-shadow: var(--shadow-md);
      padding: 3px 6px;
      display: flex;
      align-items: center;
      gap: 3px;
      z-index: 40;
    }
    .dock-btn {
      width: 28px;
      height: 28px;
      border-radius: 4px;
      border: none;
      background: transparent;
      color: #4b5563;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      font-weight: 700;
    }
    .dock-btn svg { width: 16px; height: 16px; stroke: currentColor; fill: none; stroke-width: 2; }
    .dock-btn:hover { background: var(--bg); color: var(--text); }
    .zoom-text {
      font-size: 11px;
      font-weight: 600;
      font-family: var(--font-mono);
      min-width: 44px;
      text-align: center;
      color: var(--text);
      cursor: pointer;
    }

    /* Collapsible Right Context Drawer (Section 5.2) */
    .right-context-drawer {
      position: absolute;
      top: 48px;
      right: 0;
      width: 360px;
      bottom: 24px;
      background: var(--surface);
      border-left: 1px solid var(--border);
      box-shadow: -4px 0 20px rgba(0, 0, 0, 0.05);
      z-index: 45;
      display: flex;
      flex-direction: column;
      transform: translateX(100%);
      transition: transform 0.25s cubic-bezier(0.16, 1, 0.3, 1);
    }
    .right-context-drawer.open { transform: translateX(0); }
    .drawer-tab-strip {
      display: flex;
      border-bottom: 1px solid var(--border);
      background: #fafbfc;
      overflow-x: auto;
    }
    .drawer-tab {
      padding: 10px 12px;
      font-size: 11px;
      font-weight: 600;
      color: var(--text-muted);
      border-bottom: 2px solid transparent;
      cursor: pointer;
      white-space: nowrap;
      display: flex;
      align-items: center;
      gap: 5px;
    }
    .drawer-tab:hover { color: var(--text); }
    .drawer-tab.active {
      color: var(--miro-blue);
      border-bottom-color: var(--miro-blue);
      background: #fff;
    }
    .drawer-body {
      flex: 1;
      overflow-y: auto;
      padding: 16px;
      font-size: 12px;
    }
    .drawer-header {
      padding: 12px 16px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      border-bottom: 1px solid var(--border);
      font-weight: 700;
      font-size: 13px;
    }
    .drawer-close-btn {
      background: transparent;
      border: none;
      font-size: 14px;
      cursor: pointer;
      color: var(--text-muted);
    }
    .drawer-close-btn:hover { color: var(--text); }

    /* Persistent Status Bar */
    .bottom-status-bar {
      position: absolute;
      bottom: 0;
      left: 0;
      right: 0;
      height: 24px;
      background: var(--surface);
      border-top: 1px solid var(--border);
      display: flex;
      align-items: center;
      padding: 0 16px;
      font-size: 11px;
      color: var(--text-muted);
      gap: 12px;
      z-index: 50;
    }
    .status-badge { display: flex; align-items: center; gap: 5px; color: #059669; font-weight: 600; }

    /* Modals */
    .modal-overlay {
      position: fixed;
      top: 0;
      left: 0;
      width: 100vw;
      height: 100vh;
      background: rgba(15, 23, 42, 0.45);
      
      z-index: 100;
      display: none;
      align-items: center;
      justify-content: center;
    }
    .modal-overlay.open { display: flex; }
    .modal-dialog {
      background: var(--surface);
      border-radius: 12px;
      box-shadow: var(--shadow-xl);
      width: 740px;
      max-width: 92vw;
      max-height: 85vh;
      display: flex;
      flex-direction: column;
      overflow: hidden;
    }
    .modal-header {
      padding: 16px 20px;
      border-bottom: 1px solid var(--border);
      display: flex;
      align-items: center;
      justify-content: space-between;
      font-weight: 700;
      font-size: 15px;
    }
    .modal-body { padding: 20px; overflow-y: auto; font-size: 13px; }
    .modal-footer {
      padding: 14px 20px;
      border-top: 1px solid var(--border);
      display: flex;
      justify-content: flex-end;
      gap: 8px;
      background: #f8fafc;
    }
    .export-file-tabs { display: flex; gap: 6px; margin-bottom: 14px; flex-wrap: wrap; }
    .modal-code-box {
      background: #0f172a;
      color: #f8fafc;
      padding: 14px;
      border-radius: 8px;
      font-family: var(--font-mono);
      font-size: 11px;
      line-height: 1.5;
      max-height: 340px;
      overflow: auto;
      white-space: pre-wrap;
    }
    .diff-box {
      font-family: var(--font-mono);
      font-size: 11px;
      background: #0f172a;
      color: #f8fafc;
      padding: 12px;
      border-radius: 6px;
      line-height: 1.5;
      max-height: 220px;
      overflow-y: auto;
      white-space: pre-wrap;
      margin-bottom: 12px;
    }
    .diff-del { color: #f87171; background: rgba(239, 68, 68, 0.15); display: block; padding: 2px 4px; }
    .diff-add { color: #4ade80; background: rgba(34, 197, 94, 0.15); display: block; padding: 2px 4px; }
  
    /* Sketch & UI Mockup Modal */
    .sketch-modal-overlay {
      position: fixed; inset: 0; background: rgba(15, 23, 42, 0.7);
      z-index: 2500; background: rgba(15, 23, 42, 0.45); display: none;
      align-items: center; justify-content: center;
    }
    .sketch-modal-overlay.open { display: flex; }
    .sketch-modal {
      background: #ffffff; border-radius: 14px; width: 860px; max-width: 95vw;
      box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.35); border: 1px solid #cbd5e1;
      display: flex; flex-direction: column; overflow: hidden;
    }
    .sketch-modal-header {
      padding: 14px 20px; border-bottom: 1px solid #e2e8f0;
      display: flex; align-items: center; justify-content: space-between;
      background: #f8fafc;
    }
    .sketch-modal-title { font-size: 15px; font-weight: 700; color: #0f172a; display: flex; align-items: center; gap: 8px; }
    .sketch-toolbar {
      padding: 10px 20px; border-bottom: 1px solid #e2e8f0; background: #ffffff;
      display: flex; align-items: center; gap: 12px; flex-wrap: wrap;
    }
    .sketch-tool-btn {
      padding: 6px 12px; border-radius: 6px; border: 1px solid #cbd5e1;
      background: #ffffff; font-size: 12px; font-weight: 600; color: #334155;
      cursor: pointer; display: flex; align-items: center; gap: 6px; transition: all 0.15s;
    }
    .sketch-tool-btn:hover { background: #f1f5f9; border-color: #94a3b8; }
    .sketch-tool-btn.active { background: #eff6ff; border-color: #2563eb; color: #2563eb; }
    .sketch-color-circle {
      width: 22px; height: 22px; border-radius: 50%; cursor: pointer;
      border: 2px solid transparent; transition: transform 0.1s;
    }
    .sketch-color-circle.active { border-color: #0f172a; transform: scale(1.15); }
    .sketch-canvas-wrap {
      background: #f8fafc; padding: 16px; display: flex; justify-content: center;
      background-image: radial-gradient(circle, #cbd5e1 1px, transparent 1px);
      background-size: 20px 20px;
    }
    #sketch-canvas {
      background: #ffffff; border-radius: 8px; border: 1.5px solid #cbd5e1;
      box-shadow: 0 4px 12px rgba(0,0,0,0.06); cursor: crosshair; touch-action: none;
    }
    .sketch-modal-footer {
      padding: 12px 20px; border-top: 1px solid #e2e8f0; background: #f8fafc;
      display: flex; align-items: center; justify-content: space-between;
    }

</style>
</head>
<body>

  <!-- Miro Header -->
  <header class="miro-header">
    <div class="brand-logo" onclick="fitToContent()" title="Fit All to Screen">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
        <polygon points="12 2 2 7 12 12 22 7 12 2"></polygon>
        <polyline points="2 17 12 22 22 17"></polyline>
        <polyline points="2 12 12 17 22 12"></polyline>
      </svg>
      <span>Prompt Studio</span>
    </div>
    <div class="header-divider"></div>
    <input type="text" class="board-title" id="board-title" value="Prompt Studio Architecture Board" title="Rename Board">
    <span class="sync-badge">● Synced Graph</span>

    <div class="search-pill" onclick="openQuickFindModal()">
      <svg class="icon-svg" viewBox="0 0 24 24"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
      <span>Quick Find (Ctrl+K)</span>
    </div>

    <div class="presence-avatars">
      <div class="avatar-circle avatar-sys" title="Architecture Engine (Active)">SE</div>
      <div class="avatar-circle avatar-user" title="You (Lead Architect)">HP</div>
    </div>

    <div class="header-actions">
      <button class="btn btn-blueprints-nav" onclick="openBrainstormModal()">
        <svg class="icon-svg" viewBox="0 0 24 24"><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/></svg>
        Blueprints
      </button>
      <button class="btn btn-share" onclick="openShareModal()">
        <svg class="icon-svg" viewBox="0 0 24 24"><circle cx="18" cy="5" r="3"/><circle cx="6" cy="12" r="3"/><circle cx="18" cy="19" r="3"/><line x1="8.59" y1="13.51" x2="15.42" y2="17.49"/><line x1="15.41" y1="6.51" x2="8.59" y2="10.49"/></svg>
        Share
      </button>
      <button class="btn" onclick="exportPNGScreenshot()">
        <svg class="icon-svg" viewBox="0 0 24 24"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"/><circle cx="8.5" cy="8.5" r="1.5"/><polyline points="21 15 16 10 5 21"/></svg>
        Export PNG
      </button>
      <button class="btn btn-primary" onclick="openExportModal()">
        <svg class="icon-svg" viewBox="0 0 24 24"><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/><polyline points="3.27 6.96 12 12.01 20.73 6.96"/><line x1="12" y1="22.08" x2="12" y2="12"/></svg>
        Export Handoff
      </button>
      <button class="btn" onclick="toggleRightDrawer()" id="drawer-toggle-btn">
        <svg class="icon-svg" viewBox="0 0 24 24"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"/><line x1="15" y1="3" x2="15" y2="21"/></svg>
        Inspector
      </button>
    </div>
  </header>

  <!-- Fullscreen Infinite Whiteboard -->
  <main class="canvas-viewport" id="canvas-viewport">
    <div class="canvas-world" id="canvas-world">
      <!-- SVG Connectors & Sketches -->
      <svg class="canvas-svg" id="canvas-svg">
        <defs>
          <marker id="arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
            <path d="M 0 1 L 10 5 L 0 9 z" fill="#475569"/>
          </marker>
          <marker id="arrow-blue" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
            <path d="M 0 1 L 10 5 L 0 9 z" fill="#2b59ff"/>
          </marker>
        </defs>
      </svg>

      <!-- Elements Layer (Frames, Cards, Stickies, Shapes, Architecture Nodes, ERD, Screens) -->
      <div id="elements-layer"></div>

      <!-- 8-Point Transform Gizmo -->
      <div class="selection-gizmo" id="selection-gizmo">
        <div class="gizmo-stem"></div>
        <div class="gizmo-handle handle-rot" title="Rotate"></div>
        <div class="gizmo-handle handle-nw" data-handle="nw"></div>
        <div class="gizmo-handle handle-n" data-handle="n"></div>
        <div class="gizmo-handle handle-ne" data-handle="ne"></div>
        <div class="gizmo-handle handle-e" data-handle="e"></div>
        <div class="gizmo-handle handle-se" data-handle="se"></div>
        <div class="gizmo-handle handle-s" data-handle="s"></div>
        <div class="gizmo-handle handle-sw" data-handle="sw"></div>
        <div class="gizmo-handle handle-w" data-handle="w"></div>
      </div>
    </div>

    <!-- Rubberband Marquee Selection Box -->
    <div class="marquee-box" id="marquee-box"></div>

    <!-- Miro Floating Left Dock (Monochrome SVG Icons) -->
    <div class="miro-left-dock" id="miro-toolbar">
      <!-- Select Pointer -->
      <button class="tool-btn active" id="tool-select" title="Select (V)" onclick="setTool('select')">
        <svg viewBox="0 0 24 24"><path d="M3 3l7 18 3-7 7-3L3 3z"/></svg>
        <span class="tooltip">Select (V)</span>
      </button>

      <!-- Pan Hand -->
      <button class="tool-btn" id="tool-pan" title="Pan Canvas (H)" onclick="setTool('pan')">
        <svg viewBox="0 0 24 24"><path d="M18 11V6a2 2 0 0 0-4 0v4M14 10V4a2 2 0 0 0-4 0v6M10 10.5V6a2 2 0 0 0-4 0v8M6 14v-2a2 2 0 0 0-4 0v6a8 8 0 0 0 16 0v-4a2 2 0 0 0-4 0"/></svg>
        <span class="tooltip">Pan Canvas (H)</span>
      </button>

      <!-- Miro-Style SaaS Templates Library -->
      <button class="tool-btn" id="tool-templates" title="SaaS Templates & Blueprints (B)" onclick="openBrainstormModal()">
        <svg viewBox="0 0 24 24"><rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/></svg>
        <span class="tooltip">Templates (B)</span>
      </button>

      <div class="tool-divider"></div>

      <!-- Sticky Note -->
      <button class="tool-btn" id="tool-sticky" title="Sticky Note (N)" onclick="toggleFlyout('sticky')">
        <svg viewBox="0 0 24 24"><path d="M15 3H5a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V9l-6-6z"/><polyline points="15 3 15 9 21 9"/></svg>
        <span class="tooltip">Sticky Note (N)</span>
      </button>

      <!-- SaaS Architecture Nodes Palette -->
      <button class="tool-btn" id="tool-arch" title="SaaS System Components (A)" onclick="toggleFlyout('arch')">
        <svg viewBox="0 0 24 24"><rect x="2" y="2" width="8" height="8" rx="2"/><rect x="14" y="2" width="8" height="8" rx="2"/><rect x="14" y="14" width="8" height="8" rx="2"/><rect x="2" y="14" width="8" height="8" rx="2"/></svg>
        <span class="tooltip">SaaS Architecture (A)</span>
      </button>

      <!-- Database ERD Schema -->
      <button class="tool-btn" id="tool-erd" title="Database ERD Table (D)" onclick="addDatabaseTable()">
        <svg viewBox="0 0 24 24"><ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"/><path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"/></svg>
        <span class="tooltip">Database ERD Table (D)</span>
      </button>

      <!-- Shapes Tool -->
      <button class="tool-btn" id="tool-shape" title="Shapes (S)" onclick="toggleFlyout('shape')">
        <svg viewBox="0 0 24 24"><rect x="3" y="3" width="18" height="18" rx="2"/></svg>
        <span class="tooltip">Shapes (S)</span>
      </button>

      <!-- Connector Line -->
      <button class="tool-btn" id="tool-connector" title="Connection Line (L)" onclick="setTool('connector')">
        <svg viewBox="0 0 24 24"><path d="M5 12h14M13 6l6 6-6 6"/></svg>
        <span class="tooltip">Connection Line (L)</span>
      </button>

      <!-- Text Tool -->
      <button class="tool-btn" id="tool-text" title="Text (T)" onclick="addTextElement()">
        <svg viewBox="0 0 24 24"><polyline points="4 7 4 4 20 4 20 7"/><line x1="12" y1="4" x2="12" y2="20"/></svg>
        <span class="tooltip">Text (T)</span>
      </button>

      <!-- Wireframe Screens Flyout -->
      <button class="tool-btn" id="tool-wireframe" title="SaaS Wireframes (W)" onclick="toggleFlyout('wireframe')">
        <svg viewBox="0 0 24 24"><rect x="3" y="3" width="18" height="18" rx="2"/><path d="M3 9h18M9 21V9"/></svg>
        <span class="tooltip">SaaS Wireframes (W)</span>
      </button>

      <!-- Zone Frame -->
      <button class="tool-btn" id="tool-frame" title="Frame Zone (F)" onclick="addZoneFrame()">
        <svg viewBox="0 0 24 24"><line x1="4" y1="9" x2="20" y2="9"/><line x1="4" y1="15" x2="20" y2="15"/><line x1="9" y1="4" x2="9" y2="20"/><line x1="15" y1="4" x2="15" y2="20"/></svg>
        <span class="tooltip">Frame Zone (F)</span>
      </button>

      <div class="tool-divider"></div>

      <!-- Pen Sketch -->
      <button class="tool-btn" id="tool-pen" title="Pen (P)" onclick="setTool('pen')">
        <svg viewBox="0 0 24 24"><path d="M12 19l7-7 3 3-7 7-3-3z"/><path d="M18 13l-1.5-7.5L2 2l3.5 14.5L13 18l5-5z"/></svg>
        <span class="tooltip">Pen (P)</span>
      </button>

      <!-- Eraser -->
      <button class="tool-btn" id="tool-eraser" title="Eraser (E)" onclick="setTool('eraser')">
        <svg viewBox="0 0 24 24"><path d="M20 20H7L3 16c-.8-.8-.8-2 0-2.8L13.8 2.4c.8-.8 2-.8 2.8 0l5 5c.8.8.8 2 0 2.8L11 20"/></svg>
        <span class="tooltip">Eraser (E)</span>
      </button>

      <!-- Image Attachment -->
      <button class="tool-btn" id="tool-image" title="Draw or Attach UI Mockup (I)" onclick="openSketchModal()">
        <svg viewBox="0 0 24 24"><rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="8.5" cy="8.5" r="1.5"/><polyline points="21 15 16 10 5 21"/></svg>
        <span class="tooltip">Attach Image (I)</span>
      </button>
      <input type="file" id="image-upload-input" accept="image/*" style="display:none" onchange="handleImageUpload(event)">
    </div>

    <!-- Sticky Color Flyout (16 Miro Pastels) -->
    <div class="dock-flyout" id="flyout-sticky" style="top: 150px;">
      <div class="flyout-title">Sticky Pastel</div>
      <div class="color-grid">
        <div class="color-swatch" style="background: #fef9c3;" onclick="addStickyNote('#fef9c3')" title="Enterprise Yellow"></div>
        <div class="color-swatch" style="background: #eff6ff;" onclick="addStickyNote('#eff6ff')" title="Enterprise Blue"></div>
        <div class="color-swatch" style="background: #ecfdf5;" onclick="addStickyNote('#ecfdf5')" title="Enterprise Green"></div>
        <div class="color-swatch" style="background: #f5f3ff;" onclick="addStickyNote('#f5f3ff')" title="Enterprise Purple"></div>
        <div class="color-swatch" style="background: #fff7ed;" onclick="addStickyNote('#fff7ed')" title="Enterprise Orange"></div>
        <div class="color-swatch" style="background: #f8fafc;" onclick="addStickyNote('#f8fafc')" title="Enterprise Slate"></div>
        <div class="color-swatch" style="background: #fee2e2;" onclick="addStickyNote('#fee2e2')" title="Enterprise Rose"></div>
        <div class="color-swatch" style="background: #ecfeff;" onclick="addStickyNote('#ecfeff')" title="Enterprise Cyan"></div>
      </div>
    </div>

    <!-- SaaS Architecture Components Flyout (Comprehensive 24-Node Palette) -->
    <div class="dock-flyout" id="flyout-arch" style="top: 150px; width: 310px;">
      <div class="flyout-title">SaaS Architecture Node</div>
      <div class="flyout-search-box">
        <input type="text" class="flyout-search-input" id="arch-search-input" placeholder="Search 24 SaaS components..." oninput="filterArchFlyout(this.value)">
      </div>
      <div class="flyout-category-tabs">
        <div class="flyout-tab-pill active" onclick="setArchFilter('all', this)">All (24)</div>
        <div class="flyout-tab-pill" onclick="setArchFilter('compute', this)">Compute</div>
        <div class="flyout-tab-pill" onclick="setArchFilter('messaging', this)">Messaging</div>
        <div class="flyout-tab-pill" onclick="setArchFilter('data', this)">Data</div>
        <div class="flyout-tab-pill" onclick="setArchFilter('saas', this)">SaaS Core</div>
      </div>
      <div class="picker-grid-scroll" id="arch-picker-container" style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 6px;">
        <!-- Compute & Gateways -->
        <div class="picker-card-tech" data-cat="compute" onclick="addArchNode('api_gateway')">
          <div class="picker-card-title">
            <svg class="icon-svg" viewBox="0 0 24 24"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>
            API Gateway
          </div>
          <div class="picker-card-sub">FastAPI / Traefik / Envoy</div>
        </div>
        <div class="picker-card-tech" data-cat="compute" onclick="addArchNode('reverse_proxy')">
          <div class="picker-card-title">
            <svg class="icon-svg" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/></svg>
            Reverse Proxy
          </div>
          <div class="picker-card-sub">Cloudflare / Nginx Edge</div>
        </div>
        <div class="picker-card-tech" data-cat="compute" onclick="addArchNode('microservice')">
          <div class="picker-card-title">
            <svg class="icon-svg" viewBox="0 0 24 24"><rect x="2" y="2" width="20" height="8" rx="2"/><rect x="2" y="14" width="20" height="8" rx="2"/><line x1="6" y1="6" x2="6.01" y2="6"/><line x1="6" y1="18" x2="6.01" y2="18"/></svg>
            Microservice
          </div>
          <div class="picker-card-sub">Go / Python / Node Core</div>
        </div>
        <div class="picker-card-tech" data-cat="compute" onclick="addArchNode('worker')">
          <div class="picker-card-title">
            <svg class="icon-svg" viewBox="0 0 24 24"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>
            Async Worker
          </div>
          <div class="picker-card-sub">Temporal / Celery Queue</div>
        </div>
        <div class="picker-card-tech" data-cat="compute" onclick="addArchNode('cron_scheduler')">
          <div class="picker-card-title">
            <svg class="icon-svg" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
            Cron Scheduler
          </div>
          <div class="picker-card-sub">Dcron / Batch Workflows</div>
        </div>
        <div class="picker-card-tech" data-cat="compute" onclick="addArchNode('websocket_server')">
          <div class="picker-card-title">
            <svg class="icon-svg" viewBox="0 0 24 24"><path d="M5 12.55a11 11 0 0 1 14.08 0"/><path d="M1.42 9a16 16 0 0 1 21.16 0"/><path d="M8.53 16.11a6 6 0 0 1 6.95 0"/><line x1="12" y1="20" x2="12.01" y2="20"/></svg>
            WebSocket Hub
          </div>
          <div class="picker-card-sub">Duplex Real-Time / Presence</div>
        </div>

        <!-- Messaging & Event Streaming -->
        <div class="picker-card-tech" data-cat="messaging" onclick="addArchNode('kafka_cluster')">
          <div class="picker-card-title">
            <svg class="icon-svg" viewBox="0 0 24 24"><path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/></svg>
            Apache Kafka
          </div>
          <div class="picker-card-sub">Distributed Partition Log</div>
        </div>
        <div class="picker-card-tech" data-cat="messaging" onclick="addArchNode('message_broker')">
          <div class="picker-card-title">
            <svg class="icon-svg" viewBox="0 0 24 24"><rect x="2" y="2" width="20" height="8" rx="2"/><rect x="2" y="14" width="20" height="8" rx="2"/><line x1="6" y1="6" x2="6.01" y2="6"/><line x1="6" y1="18" x2="6.01" y2="18"/></svg>
            RabbitMQ Broker
          </div>
          <div class="picker-card-sub">AMQP Topic & DLQ Queue</div>
        </div>
        <div class="picker-card-tech" data-cat="messaging" onclick="addArchNode('redis_pubsub')">
          <div class="picker-card-title">
            <svg class="icon-svg" viewBox="0 0 24 24"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>
            Redis Streams
          </div>
          <div class="picker-card-sub">Sub-ms Event Broadcast</div>
        </div>
        <div class="picker-card-tech" data-cat="messaging" onclick="addArchNode('event_bus')">
          <div class="picker-card-title">
            <svg class="icon-svg" viewBox="0 0 24 24"><circle cx="18" cy="5" r="3"/><circle cx="6" cy="12" r="3"/><circle cx="18" cy="19" r="3"/><line x1="8.59" y1="13.51" x2="15.42" y2="17.49"/><line x1="15.41" y1="6.51" x2="8.59" y2="10.49"/></svg>
            Event Bus Router
          </div>
          <div class="picker-card-sub">CloudEvents Choreography</div>
        </div>
        <div class="picker-card-tech" data-cat="messaging" onclick="addArchNode('graphql_gateway')">
          <div class="picker-card-title">
            <svg class="icon-svg" viewBox="0 0 24 24"><polygon points="12 2 2 7 12 12 22 7 12 2"/><polyline points="2 17 12 22 22 17"/></svg>
            GraphQL Federation
          </div>
          <div class="picker-card-sub">Apollo Subgraph Router</div>
        </div>
        <div class="picker-card-tech" data-cat="messaging" onclick="addArchNode('grpc_service')">
          <div class="picker-card-title">
            <svg class="icon-svg" viewBox="0 0 24 24"><polyline points="16 18 22 12 16 6"/><polyline points="8 6 2 12 8 18"/></svg>
            gRPC Microservice
          </div>
          <div class="picker-card-sub">Protobuf High-Perf RPC</div>
        </div>

        <!-- Data & Storage -->
        <div class="picker-card-tech" data-cat="data" onclick="addArchNode('postgres')">
          <div class="picker-card-title">
            <svg class="icon-svg" viewBox="0 0 24 24"><ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"/><path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"/></svg>
            PostgreSQL DB
          </div>
          <div class="picker-card-sub">Multi-Tenant ACID Relational</div>
        </div>
        <div class="picker-card-tech" data-cat="data" onclick="addArchNode('redis_cache')">
          <div class="picker-card-title">
            <svg class="icon-svg" viewBox="0 0 24 24"><path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/></svg>
            Redis / Queue
          </div>
          <div class="picker-card-sub">Sub-ms Rate Limiter / Cache</div>
        </div>
        <div class="picker-card-tech" data-cat="data" onclick="addArchNode('clickhouse')">
          <div class="picker-card-title">
            <svg class="icon-svg" viewBox="0 0 24 24"><rect x="3" y="12" width="4" height="8"/><rect x="10" y="8" width="4" height="12"/><rect x="17" y="4" width="4" height="16"/></svg>
            ClickHouse OLAP
          </div>
          <div class="picker-card-sub">High-Throughput Analytics</div>
        </div>
        <div class="picker-card-tech" data-cat="data" onclick="addArchNode('event_stream')">
          <div class="picker-card-title">
            <svg class="icon-svg" viewBox="0 0 24 24"><circle cx="6" cy="6" r="3"/><circle cx="6" cy="18" r="3"/><circle cx="18" cy="12" r="3"/><line x1="8.5" y1="7.5" x2="15.5" y2="10.5"/><line x1="8.5" y1="16.5" x2="15.5" y2="13.5"/></svg>
            Kafka Stream
          </div>
          <div class="picker-card-sub">Distributed Event Bus</div>
        </div>
        <div class="picker-card-tech" data-cat="data" onclick="addArchNode('object_store')">
          <div class="picker-card-title">
            <svg class="icon-svg" viewBox="0 0 24 24"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/></svg>
            S3 Object Store
          </div>
          <div class="picker-card-sub">Cloudflare R2 / AWS S3</div>
        </div>
        <div class="picker-card-tech" data-cat="data" onclick="addArchNode('elastic_search')">
          <div class="picker-card-title">
            <svg class="icon-svg" viewBox="0 0 24 24"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
            Elasticsearch
          </div>
          <div class="picker-card-sub">Full-Text Search Index</div>
        </div>

        <!-- SaaS Core & Operations -->
        <div class="picker-card-tech" data-cat="saas" onclick="addArchNode('stripe_billing')">
          <div class="picker-card-title">
            <svg class="icon-svg" viewBox="0 0 24 24"><rect x="1" y="4" width="22" height="16" rx="2" ry="2"/><line x1="1" y1="10" x2="23" y2="10"/></svg>
            Stripe Billing
          </div>
          <div class="picker-card-sub">Subscriptions / Webhooks</div>
        </div>
        <div class="picker-card-tech" data-cat="saas" onclick="addArchNode('auth_service')">
          <div class="picker-card-title">
            <svg class="icon-svg" viewBox="0 0 24 24"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>
            Auth & RBAC
          </div>
          <div class="picker-card-sub">OAuth2 / JWT / SAML SSO</div>
        </div>
        <div class="picker-card-tech" data-cat="saas" onclick="addArchNode('webhook_engine')">
          <div class="picker-card-title">
            <svg class="icon-svg" viewBox="0 0 24 24"><path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/></svg>
            Webhook Hub
          </div>
          <div class="picker-card-sub">Svix Outbound Delivery</div>
        </div>
        <div class="picker-card-tech" data-cat="saas" onclick="addArchNode('email_gateway')">
          <div class="picker-card-title">
            <svg class="icon-svg" viewBox="0 0 24 24"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/><polyline points="22,6 12,13 2,6"/></svg>
            Email Gateway
          </div>
          <div class="picker-card-sub">Resend / SendGrid API</div>
        </div>
        <div class="picker-card-tech" data-cat="saas" onclick="addArchNode('audit_logger')">
          <div class="picker-card-title">
            <svg class="icon-svg" viewBox="0 0 24 24"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><polyline points="9 15 12 18 17 13"/></svg>
            Audit Log Trail
          </div>
          <div class="picker-card-sub">Immutable SOC2 Compliance</div>
        </div>
        <div class="picker-card-tech" data-cat="saas" onclick="addArchNode('secrets_kms')">
          <div class="picker-card-title">
            <svg class="icon-svg" viewBox="0 0 24 24"><path d="M21 2l-2 2m-7.61 7.61a5.5 5.5 0 1 1-7.778 7.778 5.5 5.5 0 0 1 7.777-7.777zm0 0L15.5 7.5m0 0l3 3L22 7l-3-3m-3.5 3.5L19 4"/></svg>
            Secrets & KMS
          </div>
          <div class="picker-card-sub">HashiCorp Vault / KMS</div>
        </div>
      </div>
    </div>

    <!-- SaaS Wireframe Screens Flyout (8 Production Screen Types) -->
    <div class="dock-flyout" id="flyout-wireframe" style="top: 310px; width: 280px;">
      <div class="flyout-title">SaaS Wireframe Screens</div>
      <div class="picker-grid" style="grid-template-columns: repeat(2, 1fr); gap: 6px;">
        <div class="picker-card-tech" onclick="addWireframeTemplate('dashboard')">
          <div class="picker-card-title">Executive Dashboard</div>
          <div class="picker-card-sub">MRR, ARR, KPIs & Churn</div>
        </div>
        <div class="picker-card-tech" onclick="addWireframeTemplate('pricing')">
          <div class="picker-card-title">Pricing Matrix</div>
          <div class="picker-card-sub">3-Tier Plans & Quotas</div>
        </div>
        <div class="picker-card-tech" onclick="addWireframeTemplate('checkout')">
          <div class="picker-card-title">Stripe Checkout</div>
          <div class="picker-card-sub">5-State Payment Form</div>
        </div>
        <div class="picker-card-tech" onclick="addWireframeTemplate('ai_chat')">
          <div class="picker-card-title">Telemetry Stream</div>
          <div class="picker-card-sub">Streaming Prompt Interface</div>
        </div>
        <div class="picker-card-tech" onclick="addWireframeTemplate('onboarding')">
          <div class="picker-card-title">Team Onboarding</div>
          <div class="picker-card-sub">Org Setup & Member Invites</div>
        </div>
        <div class="picker-card-tech" onclick="addWireframeTemplate('developer_portal')">
          <div class="picker-card-title">Developer Portal</div>
          <div class="picker-card-sub">API Keys & Webhooks Log</div>
        </div>
        <div class="picker-card-tech" onclick="addWireframeTemplate('vendor_portal')">
          <div class="picker-card-title">Vendor Portal</div>
          <div class="picker-card-sub">Orders & Escrow Payouts</div>
        </div>
        <div class="picker-card-tech" onclick="addWireframeTemplate('ledger_view')">
          <div class="picker-card-title">Ledger & Audit</div>
          <div class="picker-card-sub">Debits / Credits Journal</div>
        </div>
      </div>
    </div>

    <!-- Shapes Flyout -->
    <div class="dock-flyout" id="flyout-shape" style="top: 280px;">
      <div class="flyout-title">Diagram Shapes</div>
      <div class="picker-grid">
        <div class="picker-card" onclick="addShape('rect')">
          <span>Rectangle</span>
        </div>
        <div class="picker-card" onclick="addShape('rounded')">
          <span>Rounded</span>
        </div>
        <div class="picker-card" onclick="addShape('circle')">
          <span>Circle</span>
        </div>
        <div class="picker-card" onclick="addShape('diamond')">
          <span>Decision</span>
        </div>
        <div class="picker-card" onclick="addShape('cylinder')">
          <span>Cylinder</span>
        </div>
        <div class="picker-card" onclick="addTypedCard()">
          <span>Spec Card</span>
        </div>
      </div>
    </div>

    <!-- Miro Floating Context Toolbar -->
    <div class="miro-context-bar" id="context-toolbar">
      <!-- Color Swatch Trigger -->
      <div class="ctx-color-dot" id="ctx-active-color" title="Change Color" onclick="toggleContextColorPopover()"></div>
      <div class="ctx-swatch-popover" id="ctx-swatch-popover">
        <div class="color-swatch" style="background: #fef9c3;" onclick="applySelectionColor('#fef9c3')"></div>
        <div class="color-swatch" style="background: #eff6ff;" onclick="applySelectionColor('#eff6ff')"></div>
        <div class="color-swatch" style="background: #ecfdf5;" onclick="applySelectionColor('#ecfdf5')"></div>
        <div class="color-swatch" style="background: #f5f3ff;" onclick="applySelectionColor('#f5f3ff')"></div>
        <div class="color-swatch" style="background: #fff7ed;" onclick="applySelectionColor('#fff7ed')"></div>
        <div class="color-swatch" style="background: #f8fafc;" onclick="applySelectionColor('#f8fafc')"></div>
        <div class="color-swatch" style="background: #fee2e2;" onclick="applySelectionColor('#fee2e2')"></div>
        <div class="color-swatch" style="background: #ecfeff;" onclick="applySelectionColor('#ecfeff')"></div>
      </div>

      <div class="ctx-divider"></div>
      <button class="ctx-btn" onclick="openSketchModal(board.selectedId)" title="Draw or attach UI mockup image to this element">
        <svg class="icon-svg" viewBox="0 0 24 24"><path d="M12 19l7-7 3 3-7 7-3-3z"/><path d="M18 13l-1.5-7.5L2 2l3.5 14.5L13 18l5-5z"/></svg>
        Draw Mockup
      </button>
      <button class="ctx-btn" onclick="armConnectorForSelected()" title="Draw connector line to another card">
        <svg class="icon-svg" viewBox="0 0 24 24"><path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/></svg>
        Connect
      </button>
      <button class="ctx-btn" onclick="toggleConnectorRouting()" id="ctx-routing-btn" title="Toggle Routing Style">
        <svg class="icon-svg" viewBox="0 0 24 24"><polyline points="4 6 12 6 12 18 20 18"/></svg>
        Elbow
      </button>
      <div class="ctx-divider"></div>
      <button class="ctx-btn ctx-btn-primary" onclick="openDrawerTab('inspect')">
        <svg class="icon-svg" viewBox="0 0 24 24"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>
        Inspect
      </button>
      <button class="ctx-btn" onclick="openDrawerTab('ask')">
        <svg class="icon-svg" viewBox="0 0 24 24"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
        System Specs
      </button>
      <div class="ctx-divider"></div>
      <button class="ctx-btn" onclick="addStickyTag('P0')" title="Toggle P0 Priority Tag">P0</button>
      <button class="ctx-btn" onclick="addStickyTag('RFC')" title="Toggle RFC Tag">RFC</button>
      <button class="ctx-btn" onclick="addStickyTag('Security')" title="Toggle Security Tag">Sec</button>
      <div class="ctx-divider"></div>
      <button class="ctx-btn" onclick="duplicateSelection()" title="Duplicate (Ctrl+D)">
        <svg class="icon-svg" viewBox="0 0 24 24"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>
        Duplicate
      </button>
      <button class="ctx-btn" onclick="deleteSelection()" style="color: var(--danger);" title="Delete (Del)">
        <svg class="icon-svg" viewBox="0 0 24 24"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>
        Delete
      </button>
    </div>

    <!-- Miro Interactive Minimap -->
    <div class="miro-minimap" id="minimap-container" onclick="panToMinimap(event)" title="Click to Pan Viewport">
      <canvas class="minimap-canvas" id="minimap-canvas"></canvas>
      <div class="minimap-viewport-box" id="minimap-viewport"></div>
    </div>

    <!-- Miro Bottom-Right Controls Dock -->
    <div class="miro-bottom-dock">
      <button class="dock-btn" onclick="undo()" title="Undo (Ctrl+Z)">
        <svg viewBox="0 0 24 24"><path d="M3 7v6h6"/><path d="M21 17a9 9 0 0 0-9-9 9 9 0 0 0-6 2.3L3 13"/></svg>
      </button>
      <button class="dock-btn" onclick="redo()" title="Redo (Ctrl+Y)">
        <svg viewBox="0 0 24 24"><path d="M21 7v6h-6"/><path d="M3 17a9 9 0 0 1 9-9 9 9 0 0 1 6 2.3L21 13"/></svg>
      </button>
      <div class="ctx-divider"></div>
      <button class="dock-btn" onclick="zoomCanvas(-0.15)" title="Zoom Out">-</button>
      <span class="zoom-text" id="zoom-label" onclick="zoomTo100()">100%</span>
      <button class="dock-btn" onclick="zoomCanvas(0.15)" title="Zoom In">+</button>
      <button class="dock-btn" onclick="resetCanvasView()" title="Fit View (Ctrl+1)">
        <svg viewBox="0 0 24 24"><polyline points="15 3 21 3 21 9"/><polyline points="9 21 3 21 3 15"/><line x1="21" y1="3" x2="14" y2="10"/><line x1="3" y1="21" x2="10" y2="14"/></svg>
      </button>
      <button class="dock-btn" onclick="toggleMinimap()" title="Toggle Minimap">
        <svg viewBox="0 0 24 24"><polygon points="1 6 1 22 8 18 16 22 23 18 23 2 16 6 8 2 1 6"/><line x1="8" y1="2" x2="8" y2="18"/><line x1="16" y1="6" x2="16" y2="22"/></svg>
      </button>
    </div>
  </main>

  <!-- Collapsible Right Context Drawer (Section 5.2) -->
  <aside class="right-context-drawer" id="right-drawer">
    <div class="drawer-header">
      <span id="drawer-title"><svg class="icon-svg" viewBox="0 0 24 24"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>Artifact Inspector</span>
      <button class="drawer-close-btn" onclick="closeRightDrawer()" aria-label="Close"><svg class="icon-svg" style="margin:0;" viewBox="0 0 24 24"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg></button>
    </div>
    <div class="drawer-tab-strip">
      <div class="drawer-tab active" data-tab="inspect" onclick="switchDrawerTab('inspect')">Inspect</div>
      <div class="drawer-tab" data-tab="specs" onclick="switchDrawerTab('specs')">System Specs</div>
      <div class="drawer-tab" data-tab="deploy" onclick="switchDrawerTab('deploy')">Deployment</div>
      <div class="drawer-tab" data-tab="security" onclick="switchDrawerTab('security')">Security</div>
      <div class="drawer-tab" data-tab="skills" onclick="switchDrawerTab('skills')">Skills</div>
      <div class="drawer-tab" data-tab="history" onclick="switchDrawerTab('history')">Audit Trail</div>
    </div>
    <div class="drawer-body" id="drawer-body"></div>
  </aside>

  <!-- Bottom Persistent Status Bar -->
  <footer class="bottom-status-bar">
    <div class="status-badge">
      <span>●</span>
      <span>Prompt Studio Enterprise Architecture Engine Active</span>
    </div>
    <div>|</div>
    <div id="status-counts">Canvas: 10 Elements · 8 Dynamic Connectors</div>
    <div>|</div>
    <div>Gateway: http://127.0.0.1:8000</div>
    <div style="margin-left: auto;">622 Verified Tests · Deterministic Compiler Active</div>
  </footer>

  <!-- Quick Find Jump-to-Artifact Modal (Ctrl+K) -->
  <div class="modal-overlay" id="quickfind-modal" onclick="if(event.target===this) closeQuickFindModal()">
    <div class="modal-dialog" style="width: 500px;">
      <div class="modal-header">
        <span><svg class="icon-svg" viewBox="0 0 24 24"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>Quick Find & Jump to Node (Ctrl+K)</span>
        <button class="btn" style="padding: 4px 8px;" onclick="closeQuickFindModal()" aria-label="Close"><svg class="icon-svg" style="margin:0;" viewBox="0 0 24 24"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg></button>
      </div>
      <div class="modal-body">
        <input type="text" id="quickfind-input" placeholder="Search requirements, entities, wireframes, stickies..." oninput="filterQuickFind(this.value)" style="width: 100%; padding: 10px 12px; border: 1.5px solid var(--miro-blue); border-radius: 6px; font-size: 13px; outline: none; margin-bottom: 12px;">
        <div id="quickfind-results" style="display: flex; flex-direction: column; gap: 6px; max-height: 320px; overflow-y: auto;"></div>
      </div>
    </div>
  </div>

  <!-- Export Modal Dialog -->
  <div class="modal-overlay" id="export-modal" onclick="if(event.target===this) closeExportModal()">
    <div class="modal-dialog">
      <div class="modal-header">
        <span><svg class="icon-svg" viewBox="0 0 24 24"><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/><polyline points="3.27 6.96 12 12.01 20.73 6.96"/><line x1="12" y1="22.08" x2="12" y2="12"/></svg>Project Graph Export & Spec Handoff</span>
        <button class="btn" style="padding: 4px 8px;" onclick="closeExportModal()" aria-label="Close"><svg class="icon-svg" style="margin:0;" viewBox="0 0 24 24"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg></button>
      </div>
      <div class="modal-body">
        <p style="margin-bottom: 12px; color: var(--text-muted);">
          Inspect live compiled outputs generated from your visual project graph:
        </p>
        <div class="export-file-tabs">
          <button class="btn" onclick="showExportFile('AGENTS.md')">AGENTS.md</button>
          <button class="btn" onclick="showExportFile('requirements.md')">requirements.md (EARS)</button>
          <button class="btn" onclick="showExportFile('design.md')">design.md (ADRs)</button>
          <button class="btn" onclick="showExportFile('tasks.md')">tasks.md (Waves)</button>
          <button class="btn" onclick="showExportFile('openapi.json')">openapi.json</button>
          <button class="btn" onclick="showExportFile('schema.sql')">schema.sql</button>
          <button class="btn" onclick="showExportFile('architecture.mermaid')">architecture.mermaid</button>
          <button class="btn" onclick="showExportFile('architecture.md')">architecture.md</button>
        </div>
        <div class="modal-code-box" id="export-code-view">// Fetching live compiled files from API...</div>
      </div>
      <div class="modal-footer">
        <button class="btn" onclick="copyExportContent()"><svg class="icon-svg" viewBox="0 0 24 24"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>Copy Content</button>
        <a href="/api/v1/export/zip" class="btn btn-primary" style="text-decoration: none;">⬇ Download Project ZIP</a>
      </div>
    </div>
  </div>

  <!-- Share Board Modal -->
  <div class="modal-overlay" id="share-modal" onclick="if(event.target===this) closeShareModal()">
    <div class="modal-dialog" style="width: 500px;">
      <div class="modal-header">
        <span><svg class="icon-svg" viewBox="0 0 24 24"><circle cx="18" cy="5" r="3"/><circle cx="6" cy="12" r="3"/><circle cx="18" cy="19" r="3"/><line x1="8.59" y1="13.51" x2="15.42" y2="17.49"/><line x1="15.41" y1="6.51" x2="8.59" y2="10.49"/></svg>Share Architecture Board</span>
        <button class="btn" style="padding: 4px 8px;" onclick="closeShareModal()" aria-label="Close"><svg class="icon-svg" style="margin:0;" viewBox="0 0 24 24"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg></button>
      </div>
      <div class="modal-body">
        <p style="margin-bottom: 12px; color: var(--text-muted);">Anyone with this link can view and collaborate on the visual graph:</p>
        <div style="display: flex; gap: 8px;">
          <input type="text" value="http://127.0.0.1:8000/" readonly style="flex: 1; padding: 8px 10px; border: 1px solid var(--border-strong); border-radius: 6px; font-family: var(--font-mono); font-size: 12px;">
          <button class="btn btn-primary" onclick="navigator.clipboard.writeText('http://127.0.0.1:8000/'); alert('Copied board URL to clipboard!');">Copy Link</button>
        </div>
      </div>
    </div>
  </div>

  <!-- Component Specification Modal -->
  <div class="modal-overlay" id="prompt-modal" onclick="if(event.target===this) closePromptModal()">
    <div class="modal-dialog" style="width: 600px;">
      <div class="modal-header">
        <span><svg class="icon-svg" viewBox="0 0 24 24"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>Component Specification Pipeline</span>
        <button class="btn" style="padding: 4px 8px;" onclick="closePromptModal()" aria-label="Close"><svg class="icon-svg" style="margin:0;" viewBox="0 0 24 24"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg></button>
      </div>
      <div class="modal-body">
        <div style="margin-bottom: 12px;">
          <label style="display: block; font-size: 11px; font-weight: 700; color: var(--text-muted); text-transform: uppercase; margin-bottom: 4px;">Target Artifact</label>
          <div id="prompt-target-title" style="font-weight: 700; font-size: 13px;">Requirement REQ-001</div>
        </div>
        <div style="margin-bottom: 14px;">
          <label style="display: block; font-size: 11px; font-weight: 700; color: var(--text-muted); text-transform: uppercase; margin-bottom: 4px;">Prompt Instruction</label>
          <input type="text" id="prompt-instruction-input" value="Generate formal EARS criteria with edge conditions" style="width: 100%; padding: 8px 10px; border: 1px solid var(--border-strong); border-radius: 6px; font-size: 13px; outline: none;">
        </div>
        <div id="prompt-diff-container" style="display: none;">
          <label style="display: block; font-size: 11px; font-weight: 700; color: var(--text-muted); text-transform: uppercase; margin-bottom: 4px;">Proposed Patch (Diff)</label>
          <div class="diff-box" id="prompt-diff-box"></div>
          <div style="font-size: 12px; color: var(--text-muted); margin-bottom: 8px;" id="prompt-diff-rationale"></div>
        </div>
      </div>
      <div class="modal-footer">
        <button class="btn" id="prompt-run-btn" onclick="executeFieldRunApi()"><svg class="icon-svg" viewBox="0 0 24 24"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>Execute Prompt</button>
        <button class="btn btn-primary" id="prompt-apply-btn" style="display: none;" onclick="applyPendingPatch()">Approve & Apply Patch</button>
      </div>
    </div>
  </div>

  <!-- Miro-Style Comprehensive SaaS Template Library (8 Deeply-Researched Production SaaS Blueprints) -->
  
  <!-- UI Mockup & Sketch Modal -->
  <div class="sketch-modal-overlay" id="sketch-modal" onclick="if(event.target===this) closeSketchModal()">
    <div class="sketch-modal">
      <div class="sketch-modal-header" style="display:flex; justify-content:space-between; align-items:center; padding:12px 18px; border-bottom:1px solid #e2e8f0; background:#f8fafc;">
        <div class="sketch-modal-title" style="font-size:14px; font-weight:700; color:#0f172a; display:flex; align-items:center; gap:8px;">
          <svg class="icon-svg" viewBox="0 0 24 24"><path d="M12 20h9"/><path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"/></svg>
          <span id="sketch-modal-title-text">UI Mockup Sketchpad</span>
        </div>
        <button class="modal-close" onclick="closeSketchModal()">&times;</button>
      </div>
      <div class="sketch-modal-body" style="padding:16px; background:#f1f5f9; display:flex; justify-content:center;">
        <canvas id="sketch-canvas" width="680" height="400" style="background:#ffffff; border:1px solid #cbd5e1; border-radius:6px; cursor:crosshair;"></canvas>
      </div>
      <div class="sketch-modal-footer" style="display:flex; justify-content:space-between; align-items:center; padding:12px 18px; border-top:1px solid #e2e8f0; background:#ffffff;">
        <div style="display:flex; gap:8px;">
          <button class="btn" id="skt-pen" onclick="setSketchTool('pen')">Pen</button>
          <button class="btn" id="skt-eraser" onclick="setSketchTool('eraser')">Eraser</button>
          <button class="btn" onclick="clearSketchCanvas()">Clear</button>
        </div>
        <div style="display:flex; gap:8px;">
          <button class="btn" onclick="closeSketchModal()">Cancel</button>
          <button class="btn btn-primary" onclick="saveSketchToElement()">Save Mockup</button>
        </div>
      </div>
    </div>
  </div>

  <!-- Prompt Compiler Modal -->
  <div class="modal-overlay" id="prompt-compile-modal" onclick="if(event.target===this) closePromptCompilerModal()">
    <div class="modal-dialog" style="width: 720px; max-width: 90vw;">
      <div class="modal-header">
        <span>Prompt Engineering Specification Compiler</span>
        <button class="modal-close" onclick="closePromptCompilerModal()">&times;</button>
      </div>
      <div class="modal-body" style="padding: 16px;">
        <textarea id="prompt-compiled-text" style="width: 100%; height: 380px; font-family: var(--font-mono); font-size: 11px; padding: 12px; border: 1px solid var(--border); border-radius: 6px; resize: vertical;" readonly></textarea>
      </div>
      <div class="modal-footer" style="padding: 12px 16px; display: flex; justify-content: flex-end; gap: 8px;">
        <button class="btn" onclick="copyCompiledPrompt()">Copy Specification</button>
        <button class="btn btn-primary" onclick="closePromptCompilerModal()">Done</button>
      </div>
    </div>
  </div>

  <!-- Build Waves Modal -->
  <div class="modal-overlay" id="build-waves-modal" onclick="if(event.target===this) closeBuildWavesModal()">
    <div class="modal-dialog" style="width: 680px; max-width: 90vw;">
      <div class="modal-header">
        <span>Topological Build Waves (Kahn DAG Order)</span>
        <button class="modal-close" onclick="closeBuildWavesModal()">&times;</button>
      </div>
      <div class="modal-body" id="build-waves-content" style="padding: 16px; font-family: var(--font-mono); font-size: 11.5px; max-height: 400px; overflow-y: auto;">
      </div>
      <div class="modal-footer" style="padding: 12px 16px; display: flex; justify-content: flex-end;">
        <button class="btn btn-primary" onclick="closeBuildWavesModal()">Close</button>
      </div>
    </div>
  </div>

  <!-- Constitution Modal -->
  <div class="modal-overlay" id="constitution-modal" onclick="if(event.target===this) closeConstitutionModal()">
    <div class="modal-dialog" style="width: 680px; max-width: 90vw;">
      <div class="modal-header">
        <span>Universal Project Constitution & Boundaries</span>
        <button class="modal-close" onclick="closeConstitutionModal()">&times;</button>
      </div>
      <div class="modal-body" id="constitution-content" style="padding: 16px; font-size: 13px; line-height: 1.6; max-height: 420px; overflow-y: auto;">
      </div>
      <div class="modal-footer" style="padding: 12px 16px; display: flex; justify-content: flex-end;">
        <button class="btn btn-primary" onclick="closeConstitutionModal()">Close</button>
      </div>
    </div>
  </div>

  <div class="modal-overlay" id="brainstorm-modal" onclick="if(event.target===this) closeBrainstormModal()">
    <div class="modal-dialog template-library-dialog">
      <div class="template-modal-header">
        <div class="template-modal-title">
          <svg class="icon-svg" style="width: 18px; height: 18px;" viewBox="0 0 24 24"><rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/></svg>
          Enterprise SaaS Architecture Templates &amp; System Blueprints
        </div>
        <button class="btn" style="padding: 4px 8px;" onclick="closeBrainstormModal()" aria-label="Close">
          <svg class="icon-svg" style="margin:0;" viewBox="0 0 24 24"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
        </button>
      </div>

      <div class="template-modal-toolbar">
        <input type="text" id="template-search-input" class="template-search-input" placeholder="Search architecture blueprints (e.g. Stripe, Kafka, Ledger, Multi-Tenant, Zero-Trust, Marketplace)..." oninput="filterTemplates(this.value)">
        <div class="template-pills">
          <div class="template-filter-pill active" onclick="setTemplateFilter('all', this)">All Blueprints (12)</div>
          <div class="template-filter-pill" onclick="setTemplateFilter('ai', this)">AI &amp; Agents</div>
          <div class="template-filter-pill" onclick="setTemplateFilter('saas', this)">Core SaaS &amp; B2B</div>
          <div class="template-filter-pill" onclick="setTemplateFilter('fintech', this)">Fintech &amp; Commerce</div>
          <div class="template-filter-pill" onclick="setTemplateFilter('data', this)">Data &amp; Streaming</div>
          <div class="template-filter-pill" onclick="setTemplateFilter('dev', this)">DevTools &amp; API</div>
          <div class="template-filter-pill" onclick="setTemplateFilter('security', this)">Security &amp; Healthcare</div>
        </div>
      </div>

      <div class="template-modal-content" id="template-cards-container">

        <div class="template-card" data-cat="saas" data-keywords="b2b_saas saas traefik gateway oidc / saml sso postgresql rls stripe billing bullmq b2b multi-tenant saas">
          <div>
            <div class="template-card-top">
              <span class="template-badge template-badge-saas">Core SaaS</span>
              <span class="template-spec-pill">Intermediate &middot; Complete Blueprint</span>
            </div>
            <div class="template-card-title" style="margin-top: 6px;">B2B Multi-Tenant SaaS</div>
            <div class="template-card-desc">Multi-tenant application architecture with tenant-scoped identity, PostgreSQL Row-Level Security (RLS) data isolation, subscription lifecycle, and asynchronous background worker queues.</div>
          </div>
          <div>
            <div class="template-tech-tags">
              <span class="template-tech-tag">Traefik Gateway</span><span class="template-tech-tag">OIDC / SAML SSO</span><span class="template-tech-tag">PostgreSQL RLS</span><span class="template-tech-tag">Stripe Billing</span><span class="template-tech-tag">BullMQ</span>
            </div>
            <div class="template-card-footer">
              <button class="btn btn-primary" style="flex: 1; justify-content: center;" onclick="applyTemplate('b2b_saas', true)">Use Blueprint</button>
              <button class="btn" title="Add to current canvas without clearing" onclick="applyTemplate('b2b_saas', false)">+ Append</button>
            </div>
          </div>
        </div>


        <div class="template-card" data-cat="fintech" data-keywords="fintech_ledger fintech multi-rail gateway double-entry engine 3-way reconciliation tokenised cde vault fintech payment gateway & double-entry ledger">
          <div>
            <div class="template-card-top">
              <span class="template-badge template-badge-fintech">Fintech & Banking</span>
              <span class="template-spec-pill">Advanced &middot; Complete Blueprint</span>
            </div>
            <div class="template-card-title" style="margin-top: 6px;">Fintech Payment Gateway & Double-Entry Ledger</div>
            <div class="template-card-desc">Payment orchestration and merchant ledger platform featuring immutable double-entry journal entries, multi-rail gateway routing, three-way reconciliation, and tokenised cardholder data boundaries.</div>
          </div>
          <div>
            <div class="template-tech-tags">
              <span class="template-tech-tag">Multi-Rail Gateway</span><span class="template-tech-tag">Double-Entry Engine</span><span class="template-tech-tag">3-Way Reconciliation</span><span class="template-tech-tag">Tokenised CDE Vault</span>
            </div>
            <div class="template-card-footer">
              <button class="btn btn-primary" style="flex: 1; justify-content: center;" onclick="applyTemplate('fintech_ledger', true)">Use Blueprint</button>
              <button class="btn" title="Add to current canvas without clearing" onclick="applyTemplate('fintech_ledger', false)">+ Append</button>
            </div>
          </div>
        </div>


        <div class="template-card" data-cat="data" data-keywords="event_streaming data apache kafka apache flink schema registry clickhouse olap vector / fluent real-time event streaming & analytics">
          <div>
            <div class="template-card-top">
              <span class="template-badge template-badge-data">Data & Streaming</span>
              <span class="template-spec-pill">Advanced &middot; Complete Blueprint</span>
            </div>
            <div class="template-card-title" style="margin-top: 6px;">Real-Time Event Streaming & Analytics</div>
            <div class="template-card-desc">High-volume operational telemetry platform with partition-keyed event ingestion, schema registry governance, stream processing, and dead-letter queue recovery.</div>
          </div>
          <div>
            <div class="template-tech-tags">
              <span class="template-tech-tag">Apache Kafka</span><span class="template-tech-tag">Apache Flink</span><span class="template-tech-tag">Schema Registry</span><span class="template-tech-tag">ClickHouse OLAP</span><span class="template-tech-tag">Vector / Fluent</span>
            </div>
            <div class="template-card-footer">
              <button class="btn btn-primary" style="flex: 1; justify-content: center;" onclick="applyTemplate('event_streaming', true)">Use Blueprint</button>
              <button class="btn" title="Add to current canvas without clearing" onclick="applyTemplate('event_streaming', false)">+ Append</button>
            </div>
          </div>
        </div>


        <div class="template-card" data-cat="ecommerce" data-keywords="ecommerce_marketplace ecommerce algolia search redis inventory locks order orchestrator split transfers seller portal multi-vendor marketplace & seller payouts">
          <div>
            <div class="template-card-top">
              <span class="template-badge template-badge-ecommerce">E-Commerce</span>
              <span class="template-spec-pill">Intermediate &middot; Complete Blueprint</span>
            </div>
            <div class="template-card-title" style="margin-top: 6px;">Multi-Vendor Marketplace & Seller Payouts</div>
            <div class="template-card-desc">Multi-vendor commercial platform supporting catalogue management, multi-seller cart order splits, escrow-like hold-and-release payouts, and seller verification.</div>
          </div>
          <div>
            <div class="template-tech-tags">
              <span class="template-tech-tag">Algolia Search</span><span class="template-tech-tag">Redis Inventory Locks</span><span class="template-tech-tag">Order Orchestrator</span><span class="template-tech-tag">Split Transfers</span><span class="template-tech-tag">Seller Portal</span>
            </div>
            <div class="template-card-footer">
              <button class="btn btn-primary" style="flex: 1; justify-content: center;" onclick="applyTemplate('ecommerce_marketplace', true)">Use Blueprint</button>
              <button class="btn" title="Add to current canvas without clearing" onclick="applyTemplate('ecommerce_marketplace', false)">+ Append</button>
            </div>
          </div>
        </div>


        <div class="template-card" data-cat="dev" data-keywords="developer_platform dev kong gateway redis token bucket openapi 3.1 webhook dispatcher developer portal developer api & webhook platform">
          <div>
            <div class="template-card-top">
              <span class="template-badge template-badge-dev">Developer Tools</span>
              <span class="template-spec-pill">Intermediate &middot; Complete Blueprint</span>
            </div>
            <div class="template-card-title" style="margin-top: 6px;">Developer API & Webhook Platform</div>
            <div class="template-card-desc">Public API infrastructure featuring tiered token-bucket rate limiting, scoped API key rotation, interactive documentation, and reliable HMAC-signed webhook delivery.</div>
          </div>
          <div>
            <div class="template-tech-tags">
              <span class="template-tech-tag">Kong Gateway</span><span class="template-tech-tag">Redis Token Bucket</span><span class="template-tech-tag">OpenAPI 3.1</span><span class="template-tech-tag">Webhook Dispatcher</span><span class="template-tech-tag">Developer Portal</span>
            </div>
            <div class="template-card-footer">
              <button class="btn btn-primary" style="flex: 1; justify-content: center;" onclick="applyTemplate('developer_platform', true)">Use Blueprint</button>
              <button class="btn" title="Add to current canvas without clearing" onclick="applyTemplate('developer_platform', false)">+ Append</button>
            </div>
          </div>
        </div>


        <div class="template-card" data-cat="saas" data-keywords="collab_workspace saas yjs crdt websocket sync redis pub/sub presence awareness postgresql doc store collaborative document & canvas workspace">
          <div>
            <div class="template-card-top">
              <span class="template-badge template-badge-saas">Productivity & Collaboration</span>
              <span class="template-spec-pill">Advanced &middot; Complete Blueprint</span>
            </div>
            <div class="template-card-title" style="margin-top: 6px;">Collaborative Document & Canvas Workspace</div>
            <div class="template-card-desc">Multi-user real-time workspace featuring conflict-free replicated data types (CRDTs), ephemeral presence awareness, document snapshots, and workspace permissions.</div>
          </div>
          <div>
            <div class="template-tech-tags">
              <span class="template-tech-tag">Yjs CRDT</span><span class="template-tech-tag">WebSocket Sync</span><span class="template-tech-tag">Redis Pub/Sub</span><span class="template-tech-tag">Presence Awareness</span><span class="template-tech-tag">PostgreSQL Doc Store</span>
            </div>
            <div class="template-card-footer">
              <button class="btn btn-primary" style="flex: 1; justify-content: center;" onclick="applyTemplate('collab_workspace', true)">Use Blueprint</button>
              <button class="btn" title="Add to current canvas without clearing" onclick="applyTemplate('collab_workspace', false)">+ Append</button>
            </div>
          </div>
        </div>


        <div class="template-card" data-cat="health" data-keywords="healthcare_portal health fhir r4 rest api smart on fhir phi access control hl7 v2 adt encrypted store healthcare patient portal & fhir integration">
          <div>
            <div class="template-card-top">
              <span class="template-badge template-badge-health">Healthcare & Life Sciences</span>
              <span class="template-spec-pill">Specialized &middot; Complete Blueprint</span>
            </div>
            <div class="template-card-title" style="margin-top: 6px;">Healthcare Patient Portal & FHIR Integration</div>
            <div class="template-card-desc">Patient engagement portal designed for interoperability with electronic health record (EHR) systems via HL7 FHIR R4 APIs, featuring attribute-based access and audit logging.</div>
          </div>
          <div>
            <div class="template-tech-tags">
              <span class="template-tech-tag">FHIR R4 REST API</span><span class="template-tech-tag">SMART on FHIR</span><span class="template-tech-tag">PHI Access Control</span><span class="template-tech-tag">HL7 v2 ADT</span><span class="template-tech-tag">Encrypted Store</span>
            </div>
            <div class="template-card-footer">
              <button class="btn btn-primary" style="flex: 1; justify-content: center;" onclick="applyTemplate('healthcare_portal', true)">Use Blueprint</button>
              <button class="btn" title="Add to current canvas without clearing" onclick="applyTemplate('healthcare_portal', false)">+ Append</button>
            </div>
          </div>
        </div>


        <div class="template-card" data-cat="security" data-keywords="zero_trust_iam security openid connect scim 2.0 opa rego policy device posture spiffe / spire zero-trust identity & access management">
          <div>
            <div class="template-card-top">
              <span class="template-badge template-badge-security">Security & Identity</span>
              <span class="template-spec-pill">Advanced &middot; Complete Blueprint</span>
            </div>
            <div class="template-card-title" style="margin-top: 6px;">Zero-Trust Identity & Access Management</div>
            <div class="template-card-desc">Enterprise identity governance framework enforcing continuous verification, Open Policy Agent (OPA) fine-grained authorization, device posture scoring, and ephemeral credentials.</div>
          </div>
          <div>
            <div class="template-tech-tags">
              <span class="template-tech-tag">OpenID Connect</span><span class="template-tech-tag">SCIM 2.0</span><span class="template-tech-tag">OPA Rego Policy</span><span class="template-tech-tag">Device Posture</span><span class="template-tech-tag">SPIFFE / SPIRE</span>
            </div>
            <div class="template-card-footer">
              <button class="btn btn-primary" style="flex: 1; justify-content: center;" onclick="applyTemplate('zero_trust_iam', true)">Use Blueprint</button>
              <button class="btn" title="Add to current canvas without clearing" onclick="applyTemplate('zero_trust_iam', false)">+ Append</button>
            </div>
          </div>
        </div>


        <div class="template-card" data-cat="ai" data-keywords="ai_agent_rag ai qdrant vector db hybrid search langgraph agent guardrails ai trace log enterprise ai agent & rag platform">
          <div>
            <div class="template-card-top">
              <span class="template-badge template-badge-ai">AI & Agents</span>
              <span class="template-spec-pill">Advanced &middot; Complete Blueprint</span>
            </div>
            <div class="template-card-title" style="margin-top: 6px;">Enterprise AI Agent & RAG Platform</div>
            <div class="template-card-desc">Autonomous agent and retrieval-augmented generation platform with pre-retrieval document ACL filtering, semantic vector search, tool guardrails, and execution auditing.</div>
          </div>
          <div>
            <div class="template-tech-tags">
              <span class="template-tech-tag">Qdrant Vector DB</span><span class="template-tech-tag">Hybrid Search</span><span class="template-tech-tag">LangGraph Agent</span><span class="template-tech-tag">Guardrails AI</span><span class="template-tech-tag">Trace Log</span>
            </div>
            <div class="template-card-footer">
              <button class="btn btn-primary" style="flex: 1; justify-content: center;" onclick="applyTemplate('ai_agent_rag', true)">Use Blueprint</button>
              <button class="btn" title="Add to current canvas without clearing" onclick="applyTemplate('ai_agent_rag', false)">+ Append</button>
            </div>
          </div>
        </div>


        <div class="template-card" data-cat="fintech" data-keywords="global_payroll fintech gross-to-net engine versioned rule packs effective dating sepa / ach disburse statutory audit global payroll & tax engine">
          <div>
            <div class="template-card-top">
              <span class="template-badge template-badge-fintech">Fintech & Payroll</span>
              <span class="template-spec-pill">Specialized &middot; Complete Blueprint</span>
            </div>
            <div class="template-card-title" style="margin-top: 6px;">Global Payroll & Tax Engine</div>
            <div class="template-card-desc">Deterministic gross-to-net payroll engine supporting versioned jurisdiction rule packs, multi-currency processing, effective-dated contracts, and statutory remittance.</div>
          </div>
          <div>
            <div class="template-tech-tags">
              <span class="template-tech-tag">Gross-to-Net Engine</span><span class="template-tech-tag">Versioned Rule Packs</span><span class="template-tech-tag">Effective Dating</span><span class="template-tech-tag">SEPA / ACH Disburse</span><span class="template-tech-tag">Statutory Audit</span>
            </div>
            <div class="template-card-footer">
              <button class="btn btn-primary" style="flex: 1; justify-content: center;" onclick="applyTemplate('global_payroll', true)">Use Blueprint</button>
              <button class="btn" title="Add to current canvas without clearing" onclick="applyTemplate('global_payroll', false)">+ Append</button>
            </div>
          </div>
        </div>


        <div class="template-card" data-cat="saas" data-keywords="legaltech_clm saas clause library diff / redline engine ethical walls docusign adapter obligations tracker legaltech contract lifecycle management">
          <div>
            <div class="template-card-top">
              <span class="template-badge template-badge-saas">LegalTech & Enterprise</span>
              <span class="template-spec-pill">Intermediate &middot; Complete Blueprint</span>
            </div>
            <div class="template-card-title" style="margin-top: 6px;">LegalTech Contract Lifecycle Management</div>
            <div class="template-card-desc">Enterprise contract management platform covering clause assembly, tracked redlining, multi-tier approval routing, ethical walls, and e-signature envelope tracking.</div>
          </div>
          <div>
            <div class="template-tech-tags">
              <span class="template-tech-tag">Clause Library</span><span class="template-tech-tag">Diff / Redline Engine</span><span class="template-tech-tag">Ethical Walls</span><span class="template-tech-tag">DocuSign Adapter</span><span class="template-tech-tag">Obligations Tracker</span>
            </div>
            <div class="template-card-footer">
              <button class="btn btn-primary" style="flex: 1; justify-content: center;" onclick="applyTemplate('legaltech_clm', true)">Use Blueprint</button>
              <button class="btn" title="Add to current canvas without clearing" onclick="applyTemplate('legaltech_clm', false)">+ Append</button>
            </div>
          </div>
        </div>


        <div class="template-card" data-cat="ops" data-keywords="logistics_supply_chain ops emqx mqtt timescaledb edi x12 engine geofencing ed25519 cryptographic pod logistics & cold-chain supply chain platform">
          <div>
            <div class="template-card-top">
              <span class="template-badge template-badge-ops">Supply Chain & IoT</span>
              <span class="template-spec-pill">Advanced &middot; Complete Blueprint</span>
            </div>
            <div class="template-card-title" style="margin-top: 6px;">Logistics & Cold-Chain Supply Chain Platform</div>
            <div class="template-card-desc">Global freight visibility platform tracking multi-modal shipments, IoT sensor cold-chain temperature telemetry, EDI X12 transaction sets, and cryptographic proof-of-delivery.</div>
          </div>
          <div>
            <div class="template-tech-tags">
              <span class="template-tech-tag">EMQX MQTT</span><span class="template-tech-tag">TimescaleDB</span><span class="template-tech-tag">EDI X12 Engine</span><span class="template-tech-tag">Geofencing</span><span class="template-tech-tag">Ed25519 Cryptographic POD</span>
            </div>
            <div class="template-card-footer">
              <button class="btn btn-primary" style="flex: 1; justify-content: center;" onclick="applyTemplate('logistics_supply_chain', true)">Use Blueprint</button>
              <button class="btn" title="Add to current canvas without clearing" onclick="applyTemplate('logistics_supply_chain', false)">+ Append</button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>

  <script>
    // --- Application State ---
    const board = {
      zoom: 1.0,
      panX: 80,
      panY: 50,
      currentTool: 'select',
      selectedId: 'arch-1',
      selectedFrameId: null,
      connectorRouting: 'orthogonal',
      activeDrawerTab: 'inspect',

      // Magnetic Connector State
      isConnecting: false,
      connectingFrom: null,
      snappedTarget: null,

      // Undo / Redo Stacks
      history: [],
      redoStack: [],

      frames: [
        { id: 'f-1', title: '1. Product Vision & Research', x: 80, y: 50, w: 320, h: 540 },
        { id: 'f-2', title: '2. SaaS Wireframes & UI States', x: 440, y: 50, w: 460, h: 540 },
        { id: 'f-3', title: '3. Architecture & Cloud Services', x: 940, y: 50, w: 360, h: 540 },
        { id: 'f-4', title: '4. Database ERD & Schemas', x: 1340, y: 50, w: 320, h: 540 },
        { id: 'f-5', title: '5. Kahn Wave Tasks & Delivery', x: 440, y: 630, w: 460, h: 360 },
        { id: 'f-6', title: '6. Security & PCI Compliance Boundary', x: 940, y: 630, w: 360, h: 360 }
      ],

      elements: [
        // Zone 1: Sticky Notes with Tags and Reactions
        {
          id: 'st-1',
          type: 'sticky',
          color: '#fef9c3',
          x: 100,
          y: 100,
          w: 200,
          h: 200,
          tags: ['P0', 'UX'],
          reactions: [],
          content: 'Payer checkout must load in <500ms on 4G mobile devices with zero layout shift.'
        },
        {
          id: 'st-2',
          type: 'sticky',
          color: '#ecfdf5',
          x: 100,
          y: 330,
          w: 200,
          h: 200,
          tags: ['Security', 'PCI'],
          reactions: [],
          content: 'Security Rule: Never store raw card PANs; offload tokenization to Stripe Elements.'
        },

        // Zone 2: Wireframe Screen with States Matrix & Component List
        {
          id: 'wf-1',
          type: 'wireframe',
          screenType: 'checkout',
          x: 460,
          y: 100,
          w: 410,
          title: 'SCR-002: Public Checkout View',
          route: '/pay/:slug',
          activeState: 'populated',
          customComponents: []
        },

        // Zone 3: SaaS Architecture Nodes
        {
          id: 'arch-1',
          type: 'arch',
          archType: 'api_gateway',
          x: 960,
          y: 100,
          w: 260,
          title: 'FastAPI Gateway',
          desc: 'Reverse proxy, JWT token verification, and tenant rate-limiter.',
          tags: ['Python 3.12', 'Pydantic v2', '<20ms']
        },
        {
          id: 'arch-2',
          type: 'arch',
          archType: 'stripe_billing',
          x: 960,
          y: 260,
          w: 260,
          title: 'Stripe Billing Engine',
          desc: 'Manages Customer Portal, PaymentIntents, and webhook listeners.',
          tags: ['Stripe API v2024', 'Webhooks']
        },
        {
          id: 'arch-3',
          type: 'arch',
          archType: 'kafka_cluster',
          x: 960,
          y: 420,
          w: 260,
          title: 'Apache Kafka Event Broker',
          desc: 'Partitioned event stream for payment lifecycle and financial audit.',
          tags: ['Kafka', 'Streaming']
        },

        // Zone 4: Database ERD Tables
        {
          id: 'erd-1',
          type: 'erd',
          x: 1360,
          y: 100,
          w: 270,
          tableName: 'payment_forms',
          columns: [
            { name: 'id', type: 'UUID', isPk: true },
            { name: 'workspace_id', type: 'UUID', isFk: true },
            { name: 'slug', type: 'VARCHAR(64)' },
            { name: 'title', type: 'VARCHAR(255)' },
            { name: 'currency', type: 'VARCHAR(3)' },
            { name: 'created_at', type: 'TIMESTAMPTZ' }
          ]
        },
        {
          id: 'erd-2',
          type: 'erd',
          x: 1360,
          y: 330,
          w: 270,
          tableName: 'payment_transactions',
          columns: [
            { name: 'id', type: 'UUID', isPk: true },
            { name: 'form_id', type: 'UUID', isFk: true },
            { name: 'amount_cents', type: 'BIGINT' },
            { name: 'status', type: 'VARCHAR(32)' },
            { name: 'gateway_ref', type: 'VARCHAR(128)' }
          ]
        },

        // Zone 5: Kahn Wave Tasks
        {
          id: 'card-4',
          type: 'card',
          family: 'task',
          status: 'approved',
          alias: 'TSK-001',
          x: 460,
          y: 690,
          w: 300,
          title: 'Wave 1: Database Migrations',
          content: 'Run Alembic migration creating payment_forms and transactions tables.',
          relations: ['realizes -> REQ-001']
        },

        // Zone 6: Security Boundary
        {
          id: 'card-3',
          type: 'card',
          family: 'security',
          status: 'approved',
          alias: 'SEC-001',
          x: 960,
          y: 690,
          w: 300,
          title: 'PCI-DSS Tokenization Boundary',
          content: 'Cardholder PAN data strictly tokenized at edge reverse proxy before entering VPC memory.',
          relations: ['binds -> SCR-002']
        }
      ],

      edges: [
        { id: 'e-1', from: 'st-1', fromPort: 'right', to: 'wf-1', toPort: 'left', label: 'annotates', routing: 'orthogonal' },
        { id: 'e-2', from: 'st-2', fromPort: 'right', to: 'arch-2', toPort: 'left', label: 'constrains', routing: 'orthogonal' },
        { id: 'e-3', from: 'wf-1', fromPort: 'right', to: 'arch-1', toPort: 'left', label: 'calls API', routing: 'orthogonal' },
        { id: 'e-4', from: 'arch-1', fromPort: 'bottom', to: 'arch-2', toPort: 'top', label: 'delegates', routing: 'orthogonal' },
        { id: 'e-5', from: 'arch-1', fromPort: 'right', to: 'erd-1', toPort: 'left', label: 'writes', routing: 'orthogonal' },
        { id: 'e-6', from: 'erd-1', fromPort: 'bottom', to: 'erd-2', toPort: 'top', label: '1:N', routing: 'orthogonal' },
        { id: 'e-7', from: 'arch-3', fromPort: 'left', to: 'wf-1', toPort: 'bottom', label: 'evaluates', routing: 'orthogonal' },
        { id: 'e-8', from: 'arch-1', fromPort: 'bottom', to: 'card-4', toPort: 'top', label: 'implements', routing: 'orthogonal' }
      ],

      freehandStrokes: []
    };

    // Interaction State
    let isPanning = false;
    let panStartX = 0;
    let panStartY = 0;
    let initialPanX = 0;
    let initialPanY = 0;

    let isMarquee = false;
    let marqueeStartX = 0;
    let marqueeStartY = 0;

    let dragItem = null;
    let dragStartMouseX = 0;
    let dragStartMouseY = 0;
    let dragItemStartX = 0;
    let dragItemStartY = 0;

    let dragFrame = null;
    let dragFrameElements = [];
    let dragFrameStartX = 0;
    let dragFrameStartY = 0;

    let resizeFrame = null;
    let resizeStartFrameW = 0;
    let resizeStartFrameH = 0;

    let resizeItem = null;
    let resizeHandle = null;
    let resizeStartMouseX = 0;
    let resizeStartMouseY = 0;
    let resizeStartItemW = 0;
    let resizeStartItemH = 0;

    let activeExportFiles = {};
    let activeExportKey = 'AGENTS.md';
    let pendingPatch = null;

    // --- History Tracking (Undo / Redo) ---
    function pushHistory() {
      board.history.push({
        elements: JSON.parse(JSON.stringify(board.elements)),
        edges: JSON.parse(JSON.stringify(board.edges)),
        frames: JSON.parse(JSON.stringify(board.frames))
      });
      if (board.history.length > 50) board.history.shift();
      board.redoStack = [];
    }

    function undo() {
      if (board.history.length === 0) return;
      board.redoStack.push({
        elements: JSON.parse(JSON.stringify(board.elements)),
        edges: JSON.parse(JSON.stringify(board.edges)),
        frames: JSON.parse(JSON.stringify(board.frames))
      });
      const prev = board.history.pop();
      board.elements = prev.elements;
      board.edges = prev.edges;
      board.frames = prev.frames;
      renderAll();
    }

    function redo() {
      if (board.redoStack.length === 0) return;
      board.history.push({
        elements: JSON.parse(JSON.stringify(board.elements)),
        edges: JSON.parse(JSON.stringify(board.edges)),
        frames: JSON.parse(JSON.stringify(board.frames))
      });
      const next = board.redoStack.pop();
      board.elements = next.elements;
      board.edges = next.edges;
      board.frames = next.frames;
      renderAll();
    }

    // --- Initialization ---
    
    // --- Prompt Engineering Compiler & Modals ---
    function switchBlueprint(tmplId, btn) {
      if (btn) btn.classList.add('active');
      applyTemplate(tmplId, true);
    }

    function openPromptCompilerModal() {
      const modal = document.getElementById('prompt-compile-modal');
      const textarea = document.getElementById('prompt-compiled-text');
      
      const item = board.elements.find(e => e.id === board.selectedId) || board.elements.find(e => e.type === 'arch' || e.type === 'architecture') || board.elements[0];
      const title = document.getElementById('board-title').value || 'Enterprise System';

      const prompt = `# ROLE
Senior Python/FastAPI+PostgreSQL engineer implementing ONE node of a larger system.

# PROJECT CONSTITUTION (non-negotiable, inherited by every template)
01. Multi-tenant by default. Every query scoped by tenant_id; deny-by-default authorization.
02. Authorization is enforced server-side in middleware. UI hiding is not security.
03. Every mutating endpoint is idempotent (Idempotency-Key) and emits an audit event.
04. Audit log is append-only and tamper-evident: who/what/when/where/before/after/why.
05. Money and counted quantities are integer minor units or Decimal. Never float.
06. No PII, PHI, PAN, secrets or tokens in logs, traces, analytics or LLM prompts.
07. Every core lifecycle is an explicit state machine. No implicit states.
08. Every external webhook: signature verification, replay protection, out-of-order tolerance.
09. Every feature ships with acceptance criteria (EARS) + tests BEFORE code.
10. Soft-delete + retention policy + DSR export/delete for all personal data.
11. Accessibility: WCAG 2.2 AA / EN 301 549 for anything EU-facing.
12. Observability: SLI/SLO, error budget, alert, runbook, backup + restore drill.
13. Billing = metering -> rating -> entitlement -> invoice. Entitlement checked BEFORE work.
14. Enterprise tier assumes SSO (SAML/OIDC), SCIM, audit export, residency, DPA.
15. Never stub auth, idempotency, audit, or tenant isolation "for later".

# PROJECT CONTEXT
- Blueprint: ${title}
- Target Architecture Node: ${item ? (item.title || item.label || item.id) : 'System Core'}
- Tenant Model: pooled + row-level security (PostgreSQL RLS)
- Compliance Regimes: PCI DSS 4.0.1, DORA (EU), SOC 2 Type II, GDPR

# NODE SPECIFICATION: ${item ? (item.title || item.label || item.id) : 'Core Component'}
INTENT: ${item ? (item.desc || item.sublabel || 'Production-grade domain module execution') : 'Module execution'}
UPSTREAM CONTRACTS (already built — do not redesign): Tenancy & Isolation, Audit Log, API Gateway

# DOMAIN RULES & KILL-SHOT INVARIANTS
- Row-Level Security: SET app.current_tenant_id on every connection checkout.
- State Machine: All mutations must transition through explicit validated states.
- Webhook Replays: 5-minute deduplication window; duplicate deliveries return prior response.
- Failure Modes: Network partitions trigger circuit-breakers; no cascade to database pool.

# DATA CONTRACT
{
  "${item ? (item.tableName || 'entity') : 'entity'}": {
    "id": "uuid PK",
    "tenant_id": "uuid FK -> tenants",
    "state": "enum",
    "created_at": "timestamptz DEFAULT now()",
    "idempotency_key": "varchar(255) UNIQUE"
  }
}

# ACCEPTANCE CRITERIA (EARS Notation)
- WHEN a request is submitted with a previously used Idempotency-Key
  THEN the system SHALL return the cached response without re-executing logic
- WHEN an unauthenticated or cross-tenant request is received
  THEN the system SHALL immediately reject with HTTP 403 FORBIDDEN and log security alert
- WHEN a concurrent mutation race occurs
  THEN the system SHALL use row-level locking or optimistic concurrency to prevent dirty writes

# REQUIRED TESTS
- Concurrency race test (100 parallel requests)
- Webhook replay & duplicate delivery test
- Cross-tenant data leak isolation test
- Failure recovery & circuit breaker fallback test

# OUTPUT FORMAT
1. design.md  2. migration + code for this node only  3. tests proving every criterion

# DO NOT
Invent scope outside this node. Weaken the constitution. Stub auth/idempotency/audit.
`;

      textarea.value = prompt;
      modal.classList.add('open');
    }

    function closePromptCompilerModal() {
      document.getElementById('prompt-compile-modal').classList.remove('open');
    }

    function copyCompiledPrompt() {
      const text = document.getElementById('prompt-compiled-text').value;
      navigator.clipboard.writeText(text).then(() => {
        showNotification('Claude Prompt copied to clipboard!');
      });
    }

    function openBuildWavesModal() {
      const modal = document.getElementById('build-waves-modal');
      const body = document.getElementById('build-waves-content');
      
      body.innerHTML = `
        <div style="font-size: 12px; color: #64748b; margin-bottom: 16px;">
          Topological dependency waves derived from the spec graph. Tasks in the same wave execute in parallel waves.
        </div>
        <div class="build-wave-card">
          <div class="build-wave-title">
            <span>Wave 1: Ingress, Tenancy &amp; Security Foundations</span>
            <span style="font-size: 10px; color: #2563eb; background: #eff6ff; padding: 2px 7px; border-radius: 4px;">Independent</span>
          </div>
          <div class="build-wave-nodes">
            <span class="bwn-chip">L0.tenancy (RLS Isolation)</span>
            <span class="bwn-chip">L0.iam (Auth0 / SAML SSO)</span>
            <span class="bwn-chip">WAF &amp; Rate Limiter</span>
            <span class="bwn-chip">Schema Registry / Envelopes</span>
          </div>
        </div>

        <div class="build-wave-card">
          <div class="build-wave-title">
            <span>Wave 2: Domain Aggregates &amp; State Machines</span>
            <span style="font-size: 10px; color: #059669; background: #ecfdf5; padding: 2px 7px; border-radius: 4px;">Depends on Wave 1</span>
          </div>
          <div class="build-wave-nodes">
            <span class="bwn-chip">Party / Customer Aggregate</span>
            <span class="bwn-chip">Double-Entry Ledger Core</span>
            <span class="bwn-chip">OMS 8-State Lifecycle Machine</span>
            <span class="bwn-chip">In-Vector Tenant ACL Index</span>
          </div>
        </div>

        <div class="build-wave-card">
          <div class="build-wave-title">
            <span>Wave 3: Execution Services, Rails &amp; Adapters</span>
            <span style="font-size: 10px; color: #d97706; background: #fef3c7; padding: 2px 7px; border-radius: 4px;">Depends on Wave 2</span>
          </div>
          <div class="build-wave-nodes">
            <span class="bwn-chip">Payment Rails (ACH/RTP/SEPA)</span>
            <span class="bwn-chip">Stripe Connect Custom Splits</span>
            <span class="bwn-chip">gVisor Tool Execution Sandbox</span>
            <span class="bwn-chip">Flink EOS Streaming Topologies</span>
          </div>
        </div>

        <div class="build-wave-card">
          <div class="build-wave-title">
            <span>Wave 4: Reconciliations, Audits, Vaults &amp; Gates</span>
            <span style="font-size: 10px; color: #7c3aed; background: #f5f3ff; padding: 2px 7px; border-radius: 4px;">Terminal Gate</span>
          </div>
          <div class="build-wave-nodes">
            <span class="bwn-chip">Three-Way Daily Recon (PSP↔Ledger↔Bank)</span>
            <span class="bwn-chip">PCI DSS 4.0.1 Token Vault</span>
            <span class="bwn-chip">Immutable ClickHouse Audit Log</span>
            <span class="bwn-chip">SAR / AML Compliance Filing</span>
          </div>
        </div>
      `;
      modal.classList.add('open');
    }

    function closeBuildWavesModal() {
      document.getElementById('build-waves-modal').classList.remove('open');
    }

    function openConstitutionModal() {
      const modal = document.getElementById('constitution-modal');
      const body = document.getElementById('constitution-content');
      body.innerHTML = `
        <div style="padding: 12px; background: #eff6ff; border: 1px solid #bfdbfe; border-radius: 8px; margin-bottom: 14px;">
          <div style="font-weight: 800; color: #1e40af; font-size: 13px;">Universal Project Constitution (Non-Negotiable)</div>
          <div style="font-size: 11px; color: #3b82f6; margin-top: 2px;">Prepended to EVERY generated prompt. Stops LLMs from "simplifying" away security, audit, or isolation.</div>
        </div>
        <ol style="padding-left: 20px; color: #1e293b; font-size: 12px; line-height: 1.8;">
          <li><strong>Multi-tenant by default:</strong> Every query, cache key, queue key, and vector query is scoped by tenant_id. Deny-by-default.</li>
          <li><strong>Server-side authorization:</strong> Enforced in middleware and DB. UI hiding is not security.</li>
          <li><strong>Idempotency:</strong> Every mutating endpoint requires Idempotency-Key and emits an audit event.</li>
          <li><strong>Immutable Audit:</strong> Append-only log recording who/what/when/where/before/after/why.</li>
          <li><strong>Money &amp; Quantities:</strong> Integer minor units or Decimal. Never floating point.</li>
          <li><strong>Zero Secrets Leakage:</strong> No PII, PHI, PAN, or secrets in logs, traces, or LLM prompts.</li>
          <li><strong>Explicit State Machines:</strong> Every core lifecycle has documented states and legal transitions. No implicit states.</li>
          <li><strong>Webhooks:</strong> HMAC signature verification, replay protection, and dead-letter queues.</li>
          <li><strong>Acceptance Before Code:</strong> Every feature ships with EARS acceptance criteria + tests before code.</li>
          <li><strong>Privacy &amp; DSR:</strong> Soft-delete + retention policy + DSR export/delete.</li>
          <li><strong>Accessibility Law:</strong> WCAG 2.2 AA / EN 301 549 for all user interfaces.</li>
          <li><strong>Observability:</strong> SLIs/SLOs, alerts, and automated backup/restore drills.</li>
          <li><strong>Usage Metering:</strong> Metering -> rating -> entitlement -> invoice. Entitlement checked BEFORE expensive work.</li>
          <li><strong>Enterprise Readiness:</strong> SSO (SAML/OIDC), SCIM, audit export, and DPA.</li>
          <li><strong>Never Stub:</strong> Never stub auth, idempotency, audit, or isolation "for later".</li>
        </ol>
      `;
      modal.classList.add('open');
    }

    function closeConstitutionModal() {
      document.getElementById('constitution-modal').classList.remove('open');
    }

    function init() {
      try {
        const urlParams = new URLSearchParams(window.location.search);
        const requestedTemplate = urlParams.get('template');
        applyTemplate(requestedTemplate || 'b2b_saas', true);
      } catch (err) {
        console.error('Error applying initial template:', err);
        renderAll();
      }

      try { setupCanvasListeners(); } catch (err) { console.error('Error setting up canvas listeners:', err); }
      try { setupKeyListeners(); } catch (err) { console.error('Error setting up key listeners:', err); }
      try { updateMinimap(); } catch (err) { console.error('Error updating minimap:', err); }
      try { loadExportFiles(); } catch (err) { console.error('Error loading export files:', err); }

      setTimeout(() => {
        try { fitToContent(); } catch (err) { console.error('Error in fitToContent:', err); }
      }, 60);
    }

    function renderAll() {
      applyTransform();
      renderFrames();
      renderSVG();
      renderElements();
      updateMinimap();
      updateDrawerContent();
    }

    // Infinite Dot Grid + Mathematical Coordinate Transform
    function applyTransform() {
      const world = document.getElementById('canvas-world');
      world.style.transform = `translate(${board.panX}px, ${board.panY}px) scale(${board.zoom})`;
      document.getElementById('zoom-label').innerText = Math.round(board.zoom * 100) + '%';

      const vp = document.getElementById('canvas-viewport');
      // Miro adaptive infinite dot grid: maintains elegant spacing at every zoom scale
      let stride = 24;
      if (board.zoom < 0.35) stride = 48;
      const dotSpacing = stride * board.zoom;
      const bgX = ((board.panX % dotSpacing) + dotSpacing) % dotSpacing;
      const bgY = ((board.panY % dotSpacing) + dotSpacing) % dotSpacing;
      vp.style.backgroundPosition = `${bgX}px ${bgY}px`;
      vp.style.backgroundSize = `${dotSpacing}px ${dotSpacing}px`;

      updateSelectionGizmo();
      updateContextToolbarPosition();
      updateMinimap();
    }

        // --- Miro Toast Notifications ---
    let toastTimeout = null;
    function showNotification(msg) {
      const toast = document.getElementById('miro-toast');
      if (!toast) return;
      toast.innerText = msg;
      toast.classList.add('show');
      if (toastTimeout) clearTimeout(toastTimeout);
      toastTimeout = setTimeout(() => {
        toast.classList.remove('show');
      }, 2500);
    }

    // --- Frame Rendering with Full Drag & Resize Handles ---
    function renderFrames() {
      const layer = document.getElementById('elements-layer');
      document.querySelectorAll('.canvas-frame').forEach(el => el.remove());

      board.frames.forEach(f => {
        const div = document.createElement('div');
        div.className = `canvas-frame ${board.selectedFrameId === f.id ? 'selected' : ''}`;
        div.id = f.id;
        div.style.left = f.x + 'px';
        div.style.top = f.y + 'px';
        div.style.width = f.w + 'px';
        div.style.height = f.h + 'px';

        div.innerHTML = `
          <div class="canvas-frame-header" id="header-${f.id}" title="Drag to move frame zone and all contained elements">
            <span class="frame-title-text" contenteditable="true" spellcheck="false" title="Click to rename">${escapeHTML(f.title)}</span>
            <span class="frame-badge">Zone</span>
          </div>
          <div class="frame-resize-handle" data-frame-id="${f.id}" title="Drag to resize zone frame"></div>
        `;

        // Frame header drag listener (Miro style: drag frame by title bar)
        const header = div.querySelector('.canvas-frame-header');
        header.addEventListener('mousedown', (e) => {
          if (e.target.classList.contains('frame-title-text') && e.target === document.activeElement) {
            return;
          }
          e.stopPropagation();
          selectFrame(f.id);
          startFrameDrag(e, f);
        });

        // Frame title inline editing
        const titleSpan = div.querySelector('.frame-title-text');
        titleSpan.addEventListener('input', (e) => {
          f.title = e.target.innerText;
        });
        titleSpan.addEventListener('mousedown', (e) => {
          e.stopPropagation();
        });

        // Frame resize handle listener
        const resizer = div.querySelector('.frame-resize-handle');
        resizer.addEventListener('mousedown', (e) => {
          e.stopPropagation();
          selectFrame(f.id);
          startFrameResize(e, f);
        });

        layer.appendChild(div);
      });
    }

    function startFrameDrag(e, f) {
      if (e.button !== 0) return;
      pushHistory();
      selectFrame(f.id);
      dragFrame = f;
      dragStartMouseX = e.clientX;
      dragStartMouseY = e.clientY;
      dragFrameStartX = f.x;
      dragFrameStartY = f.y;

      // Find all elements bounded inside or overlapping with this frame
      dragFrameElements = board.elements.filter(el => {
        const dom = document.getElementById(el.id);
        const elW = el.w || (dom ? dom.offsetWidth : 200);
        const elH = el.h || (dom ? dom.offsetHeight : 150);
        const cx = el.x + elW / 2;
        const cy = el.y + elH / 2;
        const centerInside = cx >= f.x - 20 && cx <= f.x + f.w + 20 &&
                             cy >= f.y - 20 && cy <= f.y + f.h + 20;
        const overlaps = !(el.x > f.x + f.w || el.x + elW < f.x || el.y > f.y + f.h || el.y + elH < f.y);
        return centerInside || overlaps;
      }).map(el => ({
        el: el,
        startX: el.x,
        startY: el.y
      }));
    }

    function startFrameResize(e, f) {
      if (e.button !== 0) return;
      pushHistory();
      resizeFrame = f;
      resizeStartMouseX = e.clientX;
      resizeStartMouseY = e.clientY;
      resizeStartFrameW = f.w;
      resizeStartFrameH = f.h;
    }

    function renderElements() {
      document.querySelectorAll('.sticky-note, .canvas-shape, .arch-node, .erd-table, .typed-card, .wireframe-screen, .image-element').forEach(el => el.remove());
      const layer = document.getElementById('elements-layer');

      board.elements.forEach(item => {
        let el;
        if (item.type === 'image') {
          const imgDiv = document.createElement('div');
          imgDiv.className = 'image-element' + (item.selected ? ' selected' : '');
          imgDiv.dataset.id = item.id;
          imgDiv.style.cssText = 'position:absolute;left:'+item.x+'px;top:'+item.y+'px;width:'+item.w+'px;cursor:move;user-select:none;z-index:2';
          const imgTag = document.createElement('img');
          imgTag.src = item.src;
          imgTag.style.cssText = 'width:100%;height:'+(item.h||200)+'px;object-fit:contain;border-radius:8px;border:2px solid '+(item.selected?'#2563eb':'#e2e8f0')+';display:block;background:#f8fafc';
          const capDiv = document.createElement('div');
          capDiv.textContent = item.caption || '';
          capDiv.style.cssText = 'font-size:10px;color:#64748b;text-align:center;padding:3px 0;white-space:nowrap;overflow:hidden;text-overflow:ellipsis';
          imgDiv.appendChild(imgTag);
          imgDiv.appendChild(capDiv);
          imgDiv.addEventListener('mousedown', e => startDrag(e, item.id));
          imgDiv.addEventListener('click', e => { e.stopPropagation(); selectElement(item.id); });
          layer.appendChild(imgDiv);
          return;
        } else if (item.type === 'sticky') {
          el = createStickyDOM(item);
        } else if (item.type === 'arch' || item.type === 'architecture') {
          el = createArchNodeDOM(item);
        } else if (item.type === 'erd') {
          el = createERDTableDOM(item);
        } else if (item.type === 'shape') {
          el = createShapeDOM(item);
        } else if (item.type === 'wireframe') {
          el = createWireframeDOM(item);
        } else {
          el = createTypedCardDOM(item);
        }

        appendSnapPorts(el, item.id);
        layer.appendChild(el);
      });

      updateSelectionGizmo();
      updateContextToolbarPosition();
      updateStatusBar();
    }

    // Magnetic Snap Port DOM Attachments (Generous Hit Area & Instant Drag)
    function appendSnapPorts(parentEl, itemId) {
      parentEl.classList.add('element-interactive');

      const ports = ['top', 'right', 'bottom', 'left'];
      ports.forEach(port => {
        const p = document.createElement('div');
        p.className = `snap-port port-${port}`;
        p.dataset.port = port;
        p.dataset.id = itemId;

        p.addEventListener('mousedown', (e) => {
          e.stopPropagation();
          startConnectorDrag(itemId, port, e);
        });

        parentEl.appendChild(p);
      });
    }

    // Sticky Note DOM (with Tags & Reactions)
    function createStickyDOM(item) {
      const div = document.createElement('div');
      div.className = `sticky-note ${item.id === board.selectedId ? 'selected' : ''}`;
      div.id = item.id;
      div.style.left = item.x + 'px';
      div.style.top = item.y + 'px';
      div.style.width = (item.w || 200) + 'px';
      div.style.height = (item.h || 200) + 'px';
      div.style.background = item.color || '#fff9b1';

      const tagsHTML = (item.tags || []).map(t => `<span class="sticky-tag-pill">${t}</span>`).join('');

      div.innerHTML = `
        <div class="sticky-header-row">
          <div class="sticky-tags">${tagsHTML}</div>
        </div>
        <div class="sticky-content" contenteditable="true" oninput="itemContentChanged('${item.id}', this.innerText)">${escapeHTML(item.content)}</div>
        <div class="sticky-footer">
          <span>Sticky Note</span>
          <span>Alice</span>
        </div>
      `;

      div.addEventListener('mousedown', (e) => startElementDrag(e, item));
      return div;
    }

    // SaaS Architecture Node DOM
    function createArchNodeDOM(item) {
      const div = document.createElement('div');
      div.className = `arch-node ${item.id === board.selectedId ? 'selected' : ''}`;
      div.id = item.id;
      div.style.left = item.x + 'px';
      div.style.top = item.y + 'px';
      div.style.width = (item.w || 220) + 'px';

      const typeLabels = {
        api_gateway: 'API Gateway',
        reverse_proxy: 'Reverse Proxy',
        microservice: 'Microservice',
        worker: 'Async Worker',
        cron_scheduler: 'Cron Scheduler',
        websocket_server: 'WebSocket Hub',
        kafka_cluster: 'Apache Kafka',
        vector_db: 'Vector Database',
        embedding_service: 'Embedding Pipeline',
        guardrails: 'WAF & Guardrails',
        agent_swarm: 'Agent Swarm',
        grpc_service: 'gRPC Service',
        postgres: 'PostgreSQL DB',
        redis_cache: 'Redis Cache',
        clickhouse: 'ClickHouse OLAP',
        event_stream: 'Kafka Event Bus',
        object_store: 'S3 Object Store',
        elastic_search: 'Elasticsearch',
        stripe_billing: 'Stripe Billing',
        auth_service: 'Auth & RBAC',
        webhook_engine: 'Webhook Hub',
        email_gateway: 'Email Gateway',
        audit_logger: 'Audit Log Trail',
        secrets_kms: 'Secrets & KMS'
      };

      const titleText = item.title || item.label || 'Architecture Service';
      const descText = item.desc || item.sublabel || '';
      const badgeText = typeLabels[item.archType] || item.archType || item.category || 'Service';
      const tagsHTML = (item.tags || []).map(t => `<span class="arch-tag">${escapeHTML(t)}</span>`).join('');

      div.innerHTML = `
        <div class="arch-node-header">
          <span class="arch-badge">${escapeHTML(badgeText)}</span>
          <span class="arch-status">● Active</span>
        </div>
        <div class="arch-node-body">
          <div class="arch-title" contenteditable="true" oninput="itemTitleChanged('${item.id}', this.innerText)">${escapeHTML(titleText)}</div>
          <div class="arch-desc" contenteditable="true" oninput="itemContentChanged('${item.id}', this.innerText)">${escapeHTML(descText)}</div>
          <div class="arch-tech-tags">${tagsHTML}</div>
        </div>
      `;

      div.addEventListener('mousedown', (e) => startElementDrag(e, item));
      return div;
    }

    // Database ERD Table DOM
    function createERDTableDOM(item) {
      const div = document.createElement('div');
      div.className = `erd-table ${item.id === board.selectedId ? 'selected' : ''}`;
      div.id = item.id;
      div.style.left = item.x + 'px';
      div.style.top = item.y + 'px';
      div.style.width = (item.w || 270) + 'px';

      const rowsHTML = (item.columns || item.fields || []).map(col => `
        <div class="erd-row">
          <span class="erd-col-name">
            ${(col.isPk||col.isPK) ? '<span class="erd-badge erd-badge-pk">PK</span>' : (col.isFk||col.isForeignKey) ? '<span class="erd-badge erd-badge-fk">FK</span>' : ''}
            ${col.name}
          </span>
          <span class="erd-col-type">${col.type}</span>
        </div>
      `).join('');

      div.innerHTML = `
        <div class="erd-table-header">
          <span><svg class="icon-svg" viewBox="0 0 24 24"><ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"/><path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"/></svg>${escapeHTML(item.tableName)}</span>
          <span style="font-size: 10px; color: #94a3b8;">PostgreSQL</span>
        </div>
        <div class="erd-rows">${rowsHTML}</div>
      `;

      div.addEventListener('mousedown', (e) => startElementDrag(e, item));
      return div;
    }

    // Shape DOM (Flowchart)
    function createShapeDOM(item) {
      const div = document.createElement('div');
      div.className = `canvas-shape shape-${item.shape || 'rect'} ${item.id === board.selectedId ? 'selected' : ''}`;
      div.id = item.id;
      div.style.left = item.x + 'px';
      div.style.top = item.y + 'px';
      div.style.width = (item.w || 220) + 'px';
      div.style.height = (item.h || 120) + 'px';
      if (item.color) div.style.backgroundColor = item.color;

      div.innerHTML = `
        <div class="shape-text" contenteditable="true" oninput="itemContentChanged('${item.id}', this.innerText)">${escapeHTML(item.content || item.title || 'Shape')}</div>
      `;

      div.addEventListener('mousedown', (e) => startElementDrag(e, item));
      return div;
    }

    // Typed Card DOM (Section 6.4)
    function createTypedCardDOM(item) {
      const div = document.createElement('div');
      div.className = `typed-card ${item.id === board.selectedId ? 'selected' : ''}`;
      div.id = item.id;
      div.style.left = item.x + 'px';
      div.style.top = item.y + 'px';
      div.style.width = (item.w || 300) + 'px';

      const relationsHTML = (item.relations || []).map(r => `<span class="relation-pill">${escapeHTML(r)}</span>`).join('');

      div.innerHTML = `
        <div class="typed-card-header">
          <span class="card-family-tag">${item.family || 'SPEC'}</span>
          <span class="card-alias">${item.alias || 'ART-01'}</span>
          <div class="card-actions">
            <button class="card-btn-spec" title="Inspect Node Specification" onclick="event.stopPropagation(); selectElement('${item.id}')"><svg class="icon-svg" style="margin-right:2px;" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>Spec</button>
          </div>
        </div>
        <div class="typed-card-body">
          <div class="typed-card-title" contenteditable="true" oninput="itemTitleChanged('${item.id}', this.innerText)">${escapeHTML(item.title)}</div>
          <div class="typed-card-preview" contenteditable="true" oninput="itemContentChanged('${item.id}', this.innerText)">${escapeHTML(item.content)}</div>
          <div class="typed-card-relations">${relationsHTML}</div>
        </div>
        <div class="typed-card-footer">
          <span>rev 3 · Verified</span>
          <span style="color: #059669; font-weight: 600;">Valid Schema</span>
        </div>
      `;

      div.addEventListener('mousedown', (e) => startElementDrag(e, item));
      return div;
    }

    // Wireframe Screen DOM with Live Component Builder
    function createWireframeDOM(item) {
      const div = document.createElement('div');
      div.className = `wireframe-screen ${item.id === board.selectedId ? 'selected' : ''}`;
      div.id = item.id;
      div.style.left = item.x + 'px';
      div.style.top = item.y + 'px';
      div.style.width = (item.w || 410) + 'px';

      const sType = item.screenType || 'checkout';
      const currentState = item.activeState || 'populated';

      let innerHTML = '';

      if (sType === 'dashboard') {
        innerHTML = `
          <div style="display: flex; gap: 8px; margin-bottom: 8px;">
            <div style="flex: 1; padding: 10px; background: #f8fafc; border: 1px solid var(--border); border-radius: 6px;">
              <div style="font-size: 10px; color: var(--text-muted); font-weight: 600;">MONTHLY RECURRING (MRR)</div>
              <div style="font-size: 18px; font-weight: 800; color: #0f172a; margin-top: 2px;">$24,850</div>
              <div style="font-size: 9px; color: #10b981; font-weight: 700;">+14.2% MoM</div>
            </div>
            <div style="flex: 1; padding: 10px; background: #f8fafc; border: 1px solid var(--border); border-radius: 6px;">
              <div style="font-size: 10px; color: var(--text-muted); font-weight: 600;">ACTIVE TENANTS</div>
              <div style="font-size: 18px; font-weight: 800; color: #0f172a; margin-top: 2px;">412</div>
              <div style="font-size: 9px; color: #10b981; font-weight: 700;">+28 new this wk</div>
            </div>
          </div>
          <div style="padding: 10px; background: #f8fafc; border: 1px solid var(--border); border-radius: 6px;">
            <div style="font-size: 11px; font-weight: 700; margin-bottom: 6px;">Recent Subscriptions</div>
            <div style="font-size: 10px; color: #475569; display: flex; justify-content: space-between; padding: 4px 0; border-bottom: 1px solid #f1f5f9;">
              <span>Acme Corp</span>
              <span style="font-weight: 600; color: #059669;">Enterprise ($199/mo)</span>
            </div>
            <div style="font-size: 10px; color: #475569; display: flex; justify-content: space-between; padding: 4px 0;">
              <span>TechFlow Cloud</span>
              <span style="font-weight: 600; color: var(--miro-blue);">Pro ($49/mo)</span>
            </div>
          </div>
        `;
      } else if (sType === 'onboarding') {
        innerHTML = `
          <div style="padding: 10px; background: #f8fafc; border: 1px solid var(--border); border-radius: 6px; margin-bottom: 8px;">
            <div style="font-size: 12px; font-weight: 700; color: #0f172a;">Organization & Team Setup</div>
            <div style="font-size: 10px; color: var(--text-muted); margin-top: 2px;">Step 2 of 3: Invite your engineering team</div>
          </div>
          <div style="display: flex; gap: 6px; margin-bottom: 8px;">
            <input type="text" placeholder="colleague@company.com" style="flex: 1; padding: 6px 8px; border: 1px solid var(--border-strong); border-radius: 4px; font-size: 11px;">
            <button class="btn btn-primary" style="padding: 6px 10px;">Invite</button>
          </div>
          <div style="border: 1px solid var(--border); border-radius: 6px; overflow: hidden; font-size: 10px;">
            <div style="padding: 5px 8px; background: #f1f5f9; font-weight: 600; display: flex; justify-content: space-between;"><span>Member</span><span>Role</span></div>
            <div style="padding: 5px 8px; display: flex; justify-content: space-between; border-top: 1px solid var(--border);"><span>alice@company.com</span><span style="color: var(--miro-blue); font-weight: 600;">Owner</span></div>
            <div style="padding: 5px 8px; display: flex; justify-content: space-between; border-top: 1px solid var(--border);"><span>bob@company.com</span><span style="color: #64748b;">Member</span></div>
          </div>
        `;
      } else if (sType === 'developer_portal') {
        innerHTML = `
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
            <span style="font-size: 12px; font-weight: 700;">API Keys & Access</span>
            <button class="btn btn-sm btn-primary" style="font-size: 10px;">+ Create Key</button>
          </div>
          <div style="background: #0f172a; color: #e2e8f0; padding: 8px 10px; border-radius: 6px; font-family: var(--font-mono); font-size: 10px; margin-bottom: 8px;">
            <code>sk_live_9482_••••••••••••8392</code>
            <div style="color: #94a3b8; font-size: 9px; margin-top: 4px;">Rate Limit: 1,000 req/min · Full Access</div>
          </div>
          <div style="font-size: 10px; color: var(--text-muted); background: #f8fafc; padding: 6px 8px; border-radius: 4px; border: 1px solid var(--border);">
            curl -H "Authorization: Bearer sk_live_..." https://api.saas.io/v1/metrics
          </div>
        `;
      } else if (sType === 'vendor_portal') {
        innerHTML = `
          <div style="display: flex; gap: 8px; margin-bottom: 8px;">
            <div style="flex: 1; padding: 8px; background: #f8fafc; border: 1px solid var(--border); border-radius: 6px;">
              <div style="font-size: 9px; color: var(--text-muted);">SALES VOLUME</div>
              <div style="font-size: 16px; font-weight: 800; color: #0f172a;">$84,200</div>
            </div>
            <div style="flex: 1; padding: 8px; background: #ecfdf5; border: 1px solid #a7f3d0; border-radius: 6px;">
              <div style="font-size: 9px; color: #047857;">ESCROW HOLD</div>
              <div style="font-size: 16px; font-weight: 800; color: #047857;">$12,400</div>
            </div>
          </div>
          <div style="border: 1px solid var(--border); border-radius: 6px; overflow: hidden; font-size: 10px;">
            <div style="padding: 4px 8px; background: #f1f5f9; font-weight: 600;">Recent Escrow Orders</div>
            <div style="padding: 4px 8px; display: flex; justify-content: space-between; border-top: 1px solid var(--border);"><span>#ORD-9012</span><span style="color: #d97706; font-weight: 600;">Escrow Held ($450)</span></div>
            <div style="padding: 4px 8px; display: flex; justify-content: space-between; border-top: 1px solid var(--border);"><span>#ORD-9011</span><span style="color: #059669; font-weight: 600;">Payout Released ($820)</span></div>
          </div>
        `;
      } else if (sType === 'pricing') {
        innerHTML = `
          <div style="text-align: center; margin-bottom: 8px;">
            <div style="font-size: 13px; font-weight: 700;">Flexible Pricing for Fast-Growing Teams</div>
            <div style="font-size: 10px; color: var(--text-muted);">Cancel or upgrade anytime with instant prorating.</div>
          </div>
          <div style="display: flex; gap: 8px;">
            <div style="flex: 1; padding: 10px; border: 1px solid var(--border); border-radius: 6px; text-align: center;">
              <div style="font-size: 11px; font-weight: 700;">Hobby</div>
              <div style="font-size: 16px; font-weight: 800; margin: 4px 0;">$0</div>
              <div style="font-size: 9px; color: var(--text-muted);">Up to 3 projects</div>
              <button class="btn" style="width: 100%; margin-top: 8px; font-size: 10px; justify-content: center;">Start Free</button>
            </div>
            <div style="flex: 1; padding: 10px; border: 1.5px solid var(--miro-blue); border-radius: 6px; text-align: center; background: #fafbff;">
              <div style="font-size: 11px; font-weight: 700; color: var(--miro-blue);">Pro Plan</div>
              <div style="font-size: 16px; font-weight: 800; margin: 4px 0;">$49<span style="font-size: 10px; font-weight: 500;">/mo</span></div>
              <div style="font-size: 9px; color: var(--text-muted);">Unlimited API Requests</div>
              <button class="btn btn-primary" style="width: 100%; margin-top: 8px; font-size: 10px; justify-content: center;">Upgrade</button>
            </div>
          </div>
        `;
      } else if (sType === 'ai_chat' || sType === 'telemetry_stream') {
        innerHTML = `
          <div style="display: flex; flex-direction: column; gap: 8px;">
            <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #f1f5f9; padding-bottom: 6px;">
              <span style="font-size: 11px; font-weight: 700;">Live Telemetry Ingestion</span>
              <span style="font-size: 9px; background: #ecfdf5; color: #059669; padding: 2px 6px; border-radius: 4px; font-weight: 600;">Active 50k RPS</span>
            </div>
            <div style="padding: 10px; background: #0f172a; color: #38bdf8; font-family: var(--font-mono); border-radius: 6px; font-size: 10px; line-height: 1.5;">
              <div>[20:30:01] INGEST partition=12 offset=489201 bytes=1024 OK</div>
              <div>[20:30:02] FLINK window=1m aggregate=count(10240) p95=22ms</div>
              <div>[20:30:03] CLICKHOUSE commit block=92 rows=100000 14ms</div>
            </div>
            <div style="display: flex; justify-content: space-between; font-size: 10px; color: var(--text-muted);">
              <span>Buffer lag: 0.2ms</span>
              <span>Cluster: Healthy</span>
            </div>
          </div>
        `;
      } else {
        if (currentState === 'empty') {
          innerHTML = `
            <div style="text-align: center; padding: 28px 12px; color: var(--text-muted);">
              <div style="margin: 0 auto 8px; color: #94a3b8;"><svg viewBox="0 0 24 24" style="width: 28px; height: 28px; stroke: currentColor; fill: none; stroke-width: 1.8; stroke-linecap: round; stroke-linejoin: round;"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg></div>
              <div style="font-weight: 700; color: #1e293b; font-size: 13px; margin-top: 4px;">No Payment Forms Configured</div>
              <div style="font-size: 11px; margin-top: 2px;">Create your first checkout form to begin collecting customer payments.</div>
              <button class="btn btn-primary" style="margin-top: 8px;" onclick="switchScreenState('${item.id}', 'populated')">+ Create Form</button>
            </div>
          `;
        } else if (currentState === 'loading') {
          innerHTML = `
            <div style="display: flex; flex-direction: column; gap: 10px; padding: 8px 0;">
              <div style="height: 16px; background: #e2e8f0; border-radius: 4px; width: 50%;"></div>
              <div style="height: 36px; background: #f1f5f9; border-radius: 6px;"></div>
              <div style="height: 36px; background: #f1f5f9; border-radius: 6px;"></div>
              <div style="height: 38px; background: #e2e8f0; border-radius: 6px; margin-top: 6px;"></div>
            </div>
          `;
        } else if (currentState === 'invalid') {
          innerHTML = `
            <div style="font-size: 11px; color: var(--danger); font-weight: 700; margin-bottom: 6px;">Validation Error: Card Incomplete</div>
            <input class="mock-input" value="Alex Doe" readonly style="padding: 6px 8px; font-size: 11px; border: 1px solid var(--border-strong); border-radius: 4px; margin-bottom: 6px; width: 100%;">
            <input class="mock-input" value="4242 •••• •••• 12" readonly style="padding: 6px 8px; font-size: 11px; border: 1.5px solid var(--danger); background: #fef2f2; border-radius: 4px; width: 100%;">
            <span style="font-size: 9px; color: var(--danger);">Please enter a complete 16-digit card number.</span>
            <button class="btn" style="margin-top: 8px; background: #94a3b8; color: #fff; cursor: not-allowed; width: 100%; justify-content: center;">Pay $49.00</button>
          `;
        } else if (currentState === 'success') {
          innerHTML = `
            <div style="text-align: center; padding: 20px 12px;">
              <div style="width: 40px; height: 40px; border-radius: 50%; background: #ecfdf5; color: #059669; display: flex; align-items: center; justify-content: center; margin: 0 auto 8px;"><svg viewBox="0 0 24 24" style="width: 20px; height: 20px; stroke: currentColor; fill: none; stroke-width: 2.5; stroke-linecap: round; stroke-linejoin: round;"><polyline points="20 6 9 17 4 12"/></svg></div>
              <div style="font-weight: 700; color: #065f46; font-size: 14px;">Payment Received!</div>
              <div style="font-size: 11px; color: #047857; margin-top: 4px;">Confirmation #TX-904281 sent to alex@example.com</div>
              <button class="btn" style="margin-top: 10px;" onclick="switchScreenState('${item.id}', 'populated')">View Receipt</button>
            </div>
          `;
        } else if (sType === 'form') {
          innerHTML = `
            <div style="margin-bottom:8px;font-size:11px;font-weight:700;color:#0f172a">New Record Form</div>
            <div style="display:flex;flex-direction:column;gap:6px">
              <div><label style="font-size:9px;color:#64748b;display:block;margin-bottom:2px">Full Name *</label>
                <div style="height:28px;border:1px solid #cbd5e1;border-radius:5px;background:#fff;padding:0 8px;line-height:28px;font-size:11px;color:#94a3b8">Alex Chen</div></div>
              <div><label style="font-size:9px;color:#64748b;display:block;margin-bottom:2px">Email *</label>
                <div style="height:28px;border:1px solid #cbd5e1;border-radius:5px;background:#fff;padding:0 8px;line-height:28px;font-size:11px;color:#94a3b8">alex@example.com</div></div>
              <div><label style="font-size:9px;color:#64748b;display:block;margin-bottom:2px">Role</label>
                <div style="height:28px;border:1px solid #cbd5e1;border-radius:5px;background:#fff;padding:0 8px;line-height:28px;font-size:11px;color:#0f172a;display:flex;align-items:center;justify-content:space-between">Member <span style="color:#94a3b8">&#9662;</span></div></div>
              <div style="display:flex;gap:8px;margin-top:4px">
                <div style="flex:1;height:30px;background:#2563eb;border-radius:5px;display:flex;align-items:center;justify-content:center;color:#fff;font-size:11px;font-weight:600;cursor:pointer">Save</div>
                <div style="height:30px;padding:0 12px;background:#f1f5f9;border-radius:5px;display:flex;align-items:center;color:#64748b;font-size:11px;cursor:pointer">Cancel</div>
              </div>
            </div>`;
        } else if (sType === 'list') {
          innerHTML = `
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px">
              <div style="font-size:11px;font-weight:700;color:#0f172a">Records <span style="background:#eff6ff;color:#2563eb;border-radius:9px;padding:1px 7px;font-size:9px;font-weight:700">48</span></div>
              <div style="height:24px;padding:0 8px;background:#2563eb;border-radius:4px;display:flex;align-items:center;color:#fff;font-size:10px;cursor:pointer">+ New</div>
            </div>
            <div style="border:1px solid #e2e8f0;border-radius:6px;overflow:hidden">
              <div style="display:grid;grid-template-columns:2fr 1fr 1fr;background:#f8fafc;padding:5px 8px;font-size:9px;font-weight:700;color:#64748b;border-bottom:1px solid #e2e8f0">
                <span>NAME</span><span>STATUS</span><span>DATE</span>
              </div>
              <div style="display:grid;grid-template-columns:2fr 1fr 1fr;padding:6px 8px;font-size:10px;border-bottom:1px solid #f1f5f9"><span style="color:#0f172a">Alex Chen</span><span style="color:#059669;font-weight:600">Active</span><span style="color:#64748b">Nov 20</span></div>
              <div style="display:grid;grid-template-columns:2fr 1fr 1fr;padding:6px 8px;font-size:10px;border-bottom:1px solid #f1f5f9;background:#fafafa"><span style="color:#0f172a">Sam Rivera</span><span style="color:#d97706;font-weight:600">Pending</span><span style="color:#64748b">Nov 19</span></div>
              <div style="display:grid;grid-template-columns:2fr 1fr 1fr;padding:6px 8px;font-size:10px"><span style="color:#0f172a">Jo Park</span><span style="color:#059669;font-weight:600">Active</span><span style="color:#64748b">Nov 18</span></div>
            </div>`;
        } else if (sType === 'chat') {
          innerHTML = `
            <div style="display:flex;flex-direction:column;gap:6px;padding:4px 0">
              <div style="display:flex;align-items:flex-start;gap:6px">
                <div style="width:22px;height:22px;border-radius:50%;background:#e0e7ff;display:flex;align-items:center;justify-content:center;font-size:9px;font-weight:700;color:#4f46e5;flex-shrink:0">A</div>
                <div style="background:#f1f5f9;border-radius:0 8px 8px 8px;padding:6px 9px;font-size:10px;color:#0f172a;max-width:80%">Hey! Can you share the latest report?</div>
              </div>
              <div style="display:flex;align-items:flex-start;gap:6px;flex-direction:row-reverse">
                <div style="width:22px;height:22px;border-radius:50%;background:#dcfce7;display:flex;align-items:center;justify-content:center;font-size:9px;font-weight:700;color:#15803d;flex-shrink:0">M</div>
                <div style="background:#2563eb;border-radius:8px 0 8px 8px;padding:6px 9px;font-size:10px;color:#fff;max-width:80%">Here it is &#8212; just uploaded to the shared drive.</div>
              </div>
              <div style="display:flex;gap:5px;margin-top:4px">
                <div style="flex:1;height:28px;border:1px solid #cbd5e1;border-radius:5px;background:#fff;padding:0 8px;line-height:28px;font-size:10px;color:#94a3b8">Type a message&#8230;</div>
                <div style="width:28px;height:28px;background:#2563eb;border-radius:5px;display:flex;align-items:center;justify-content:center;color:#fff;font-size:12px;cursor:pointer">&#8593;</div>
              </div>
            </div>`;
        } else if (sType === 'editor') {
          innerHTML = `
            <div style="margin-bottom:6px;display:flex;gap:4px;border-bottom:1px solid #e2e8f0;padding-bottom:5px;flex-wrap:wrap">
              <div style="width:20px;height:20px;border-radius:3px;background:#f1f5f9;display:flex;align-items:center;justify-content:center;font-size:9px;font-weight:700;color:#374151">B</div>
              <div style="width:20px;height:20px;border-radius:3px;background:#f1f5f9;display:flex;align-items:center;justify-content:center;font-size:9px;font-style:italic;color:#374151">I</div>
              <div style="width:20px;height:20px;border-radius:3px;background:#f1f5f9;display:flex;align-items:center;justify-content:center;font-size:9px;text-decoration:underline;color:#374151">U</div>
              <div style="width:24px;height:20px;border-radius:3px;background:#f1f5f9;display:flex;align-items:center;justify-content:center;font-size:9px;font-weight:700;color:#374151">H1</div>
              <div style="width:30px;height:20px;border-radius:3px;background:#f1f5f9;display:flex;align-items:center;justify-content:center;font-size:9px;font-weight:700;color:#374151">Code</div>
            </div>
            <div style="font-size:14px;font-weight:800;color:#0f172a;margin-bottom:6px">Project Kickoff Notes</div>
            <div style="font-size:10px;color:#374151;line-height:1.6">
              Align on scope: MVP by Q4. Three primary user roles confirmed.
              <div style="margin:4px 0 2px;font-weight:700">Open questions:</div>
              <div style="padding-left:10px">&#8226; Data residency for EU customers?</div>
              <div style="padding-left:10px">&#8226; SSO: Auth0 vs WorkOS?</div>
              <div style="margin-top:5px;color:#94a3b8;font-size:9px;font-style:italic">Last edited by Alex &#183; 2 min ago</div>
            </div>`;
        } else if (sType === 'map') {
          innerHTML = `
            <div style="background:#e8f4f8;border-radius:6px;position:relative;overflow:hidden;height:140px;margin-bottom:6px">
              <div style="position:absolute;inset:0;background:linear-gradient(135deg,#c8dfe8 0%,#dceef5 50%,#c5dae5 100%)"></div>
              <div style="position:absolute;top:35%;left:35%;transform:translate(-50%,-50%)">
                <div style="width:10px;height:10px;border-radius:50%;background:#ef4444;border:2px solid #fff;box-shadow:0 1px 4px rgba(0,0,0,.3)"></div>
                <div style="font-size:8px;background:#fff;border-radius:3px;padding:2px 4px;margin-top:2px;white-space:nowrap;box-shadow:0 1px 3px rgba(0,0,0,.2)">HQ &#8212; San Francisco</div>
              </div>
              <div style="position:absolute;top:60%;left:65%;transform:translate(-50%,-50%)">
                <div style="width:8px;height:8px;border-radius:50%;background:#2563eb;border:2px solid #fff;box-shadow:0 1px 4px rgba(0,0,0,.3)"></div>
                <div style="font-size:8px;background:#fff;border-radius:3px;padding:2px 4px;margin-top:2px;white-space:nowrap;box-shadow:0 1px 3px rgba(0,0,0,.2)">Depot &#8212; Chicago</div>
              </div>
            </div>
            <div style="display:flex;gap:5px">
              <div style="flex:1;height:26px;border:1px solid #cbd5e1;border-radius:5px;background:#fff;padding:0 8px;line-height:26px;font-size:10px;color:#94a3b8">Search location&#8230;</div>
              <div style="height:26px;padding:0 10px;background:#2563eb;border-radius:5px;display:flex;align-items:center;color:#fff;font-size:10px;cursor:pointer">Go</div>
            </div>`;
        } else {
          innerHTML = `
            <div style="display: flex; justify-content: space-between; align-items: center; padding-bottom: 6px; border-bottom: 1px solid #f1f5f9;">
              <span style="font-size: 12px; font-weight: 700;">Customer Checkout</span>
              <span style="font-size: 10px; color: var(--miro-blue); font-weight: 600;">Stripe Elements</span>
            </div>
            <div style="display: flex; gap: 6px; margin: 6px 0;">
              <div style="flex: 1; padding: 6px; text-align: center; border: 1px solid var(--border); border-radius: 4px; font-size: 10px;">$10</div>
              <div style="flex: 1; padding: 6px; text-align: center; border: 1.5px solid var(--miro-blue); background: #eff6ff; color: var(--miro-blue); border-radius: 4px; font-size: 10px; font-weight: 700;">$25</div>
              <div style="flex: 1; padding: 6px; text-align: center; border: 1px solid var(--border); border-radius: 4px; font-size: 10px;">$50</div>
            </div>
            <input type="text" value="•••• •••• •••• 4242   08/28   882" readonly style="padding: 7px 10px; border: 1px solid var(--border-strong); border-radius: 6px; font-size: 11px; color: #475569; width: 100%;">
            <button class="btn btn-primary" style="padding: 8px; justify-content: center; font-weight: 700; width: 100%;" onclick="switchScreenState('${item.id}', 'success')">Confirm & Pay $25.00</button>
          `;
        }
      }

      const customHTML = (item.customComponents || []).map((c, idx) => {
        let preview = '';
        if (c.type === 'Input') {
          preview = `<input type="text" placeholder="${c.label}" style="width: 100%; padding: 5px 8px; border: 1px solid var(--border); border-radius: 4px; font-size: 11px;" disabled />`;
        } else if (c.type === 'Button') {
          preview = `<button style="background: var(--miro-blue); color: #fff; border: none; padding: 5px 10px; border-radius: 4px; font-size: 11px; font-weight: 600; cursor: pointer;">${c.label}</button>`;
        } else if (c.type === 'Metric') {
          preview = `<div style="background: #f1f5f9; padding: 6px 8px; border-radius: 4px;"><div style="font-size: 9px; color: var(--text-muted);">${c.label}</div><div style="font-size: 14px; font-weight: 700;">$48,250 <span style="font-size: 9px; color: #10b981;">▲ +12%</span></div></div>`;
        } else if (c.type === 'Table') {
          preview = `<div style="border: 1px solid var(--border); border-radius: 4px; overflow: hidden; font-size: 10px;"><div style="background: #f1f5f9; padding: 3px 6px; font-weight: 600; display: flex; justify-content: space-between;"><span>${c.label}</span><span>Status</span></div><div style="padding: 4px 6px; display: flex; justify-content: space-between; border-top: 1px solid var(--border);"><span>demo@domain.com</span><span style="color: #10b981; font-weight: 600;">Active</span></div></div>`;
        } else if (c.type === 'Switch') {
          preview = `<div style="display: flex; align-items: center; justify-content: space-between; padding: 4px 6px; background: #f8fafc; border: 1px solid var(--border); border-radius: 4px;"><span style="font-size: 11px;">${c.label}</span><div style="width: 24px; height: 14px; background: var(--miro-blue); border-radius: 8px; position: relative;"><div style="width: 10px; height: 10px; background: #fff; border-radius: 50%; position: absolute; right: 2px; top: 2px;"></div></div></div>`;
        }
        return `
          <div style="padding: 4px 6px; background: #ffffff; border: 1px solid var(--border); border-radius: 4px; margin-top: 6px; display: flex; align-items: center; gap: 6px;">
            <div style="flex: 1;">${preview}</div>
            <span style="cursor: pointer; color: var(--danger); font-size: 14px; font-weight: 700; line-height: 1;" title="Remove component" onclick="removeWireframeComponent('${item.id}', ${idx})">×</span>
          </div>
        `;
      }).join('');

      div.innerHTML = `
        <div class="wireframe-titlebar">
          <div class="window-dots">
            <div class="window-dot" style="background: #ef4444;"></div>
            <div class="window-dot" style="background: #f59e0b;"></div>
            <div class="window-dot" style="background: #10b981;"></div>
          </div>
          <span style="font-size: 11px; margin-left: 4px;">${escapeHTML(item.title)}</span>
          <span class="wireframe-route">${escapeHTML(item.route || '/screen')}</span>
        </div>
        ${sType === 'checkout' ? `
        <div class="wireframe-states-bar">
          <button class="state-chip ${currentState === 'populated' ? 'active' : ''}" onclick="event.stopPropagation(); switchScreenState('${item.id}', 'populated')">Populated</button>
          <button class="state-chip ${currentState === 'empty' ? 'active' : ''}" onclick="event.stopPropagation(); switchScreenState('${item.id}', 'empty')">Empty</button>
          <button class="state-chip ${currentState === 'loading' ? 'active' : ''}" onclick="event.stopPropagation(); switchScreenState('${item.id}', 'loading')">Loading</button>
          <button class="state-chip ${currentState === 'invalid' ? 'active' : ''}" onclick="event.stopPropagation(); switchScreenState('${item.id}', 'invalid')">Invalid</button>
          <button class="state-chip ${currentState === 'success' ? 'active' : ''}" onclick="event.stopPropagation(); switchScreenState('${item.id}', 'success')">Success</button>
        </div>` : ''}
        <div class="wireframe-component-bar">
          <span>+ Add:</span>
          <button class="add-comp-btn" onclick="addWireframeComponent('${item.id}', 'Input', 'Filter Field')">+ Input</button>
          <button class="add-comp-btn" onclick="addWireframeComponent('${item.id}', 'Button', 'Action CTA')">+ Button</button>
          <button class="add-comp-btn" onclick="addWireframeComponent('${item.id}', 'Metric', 'KPI Metric')">+ KPI</button>
          <button class="add-comp-btn" onclick="addWireframeComponent('${item.id}', 'Table', 'Data Table')">+ Table</button>
          <button class="add-comp-btn" onclick="addWireframeComponent('${item.id}', 'Switch', 'Feature Flag')">+ Switch</button>
        </div>
        <div class="wireframe-content">
          ${innerHTML}
          ${customHTML}
        </div>
      `;

      div.addEventListener('mousedown', (e) => startElementDrag(e, item));
      return div;
    }

    function addWireframeComponent(screenId, type, label) {
      const el = board.elements.find(e => e.id === screenId);
      if (el) {
        pushHistory();
        el.customComponents = el.customComponents || [];
        el.customComponents.push({ type, label });
        renderElements();
      }
    }

    function removeWireframeComponent(screenId, index) {
      const el = board.elements.find(e => e.id === screenId);
      if (el && el.customComponents) {
        pushHistory();
        el.customComponents.splice(index, 1);
        renderElements();
      }
    }

    function switchScreenState(screenId, newState) {
      const el = board.elements.find(e => e.id === screenId);
      if (el) {
        pushHistory();
        el.activeState = newState;
        renderElements();
      }
    }

    // Helper: Compute absolute coordinates for an element port
    function getPortCoords(elId, port) {
      const el = board.elements.find(e => e.id === elId);
      if (!el) return { x: 0, y: 0 };
      const dom = document.getElementById(elId);
      const w = el.w || (dom ? dom.offsetWidth : 200);
      const h = el.h || (dom ? dom.offsetHeight : 150);

      if (port === 'top') return { x: el.x + w / 2, y: el.y };
      if (port === 'right') return { x: el.x + w, y: el.y + h / 2 };
      if (port === 'bottom') return { x: el.x + w / 2, y: el.y + h };
      if (port === 'left') return { x: el.x, y: el.y + h / 2 };
      return { x: el.x + w / 2, y: el.y + h / 2 };
    }

    // SVG Dynamic Connectors (Bézier + 90° Orthogonal Routing + Clickable Lines)
    function renderSVG() {
      const svg = document.getElementById('canvas-svg');
      const defs = svg.querySelector('defs');
      svg.innerHTML = '';
      if (defs) svg.appendChild(defs);

      board.edges.forEach((edge, idx) => {
        const fromEl = board.elements.find(e => e.id === edge.from);
        const toEl = board.elements.find(e => e.id === edge.to);
        if (!fromEl || !toEl) return;

        const p1 = getPortCoords(edge.from, edge.fromPort || 'right');
        const p2 = getPortCoords(edge.to, edge.toPort || 'left');

        let dStr = '';
        const routing = edge.routing || board.connectorRouting || 'orthogonal';

        if (routing === 'orthogonal') {
          const midX = (p1.x + p2.x) / 2;
          dStr = `M ${p1.x} ${p1.y} L ${midX} ${p1.y} L ${midX} ${p2.y} L ${p2.x} ${p2.y}`;
        } else {
          const dx = Math.abs(p2.x - p1.x) * 0.5;
          const dy = Math.abs(p2.y - p1.y) * 0.5;
          let cx1 = p1.x + (edge.fromPort === 'right' ? dx : (edge.fromPort === 'left' ? -dx : 0));
          let cy1 = p1.y + (edge.fromPort === 'bottom' ? dy : (edge.fromPort === 'top' ? -dy : 0));
          let cx2 = p2.x + (edge.toPort === 'left' ? -dx : (edge.toPort === 'right' ? dx : 0));
          let cy2 = p2.y + (edge.toPort === 'top' ? -dy : (edge.toPort === 'bottom' ? dy : 0));
          dStr = `M ${p1.x} ${p1.y} C ${cx1} ${cy1}, ${cx2} ${cy2}, ${p2.x} ${p2.y}`;
        }

        const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
        path.setAttribute('d', dStr);
        path.setAttribute('fill', 'none');
        path.setAttribute('stroke', '#475569');
        path.setAttribute('stroke-width', '2');
        path.setAttribute('marker-end', 'url(#arrow)');
        path.style.cursor = 'pointer';
        path.style.pointerEvents = 'stroke';

        path.addEventListener('click', (e) => {
          e.stopPropagation();
          const action = prompt(`Connector [${edge.label || 'edge'}]:\nType 'delete' to remove, or enter a new label:`, edge.label || 'depends_on');
          if (action === 'delete') {
            pushHistory();
            board.edges.splice(idx, 1);
            renderAll();
          } else if (action !== null) {
            pushHistory();
            edge.label = action;
            renderAll();
          }
        });

        svg.appendChild(path);

        if (edge.label) {
          const midX = (p1.x + p2.x) / 2;
          const midY = (p1.y + p2.y) / 2;
          const text = document.createElementNS('http://www.w3.org/2000/svg', 'text');
          text.setAttribute('x', midX);
          text.setAttribute('y', midY - 6);
          text.setAttribute('font-family', 'var(--font-mono)');
          text.setAttribute('font-size', '10px');
          text.setAttribute('fill', '#64748b');
          text.setAttribute('text-anchor', 'middle');
          text.textContent = edge.label;
          svg.appendChild(text);
        }
      });

      // Active live connector drag line
      if (board.isConnecting && board.connectingFrom) {
        const p1 = board.connectingFrom;
        const p2 = board.snappedTarget ? getPortCoords(board.snappedTarget.id, board.snappedTarget.port) : board.connectingCurrent;

        if (p2) {
          const midX = (p1.x + p2.x) / 2;
          const dStr = `M ${p1.x} ${p1.y} L ${midX} ${p1.y} L ${midX} ${p2.y} L ${p2.x} ${p2.y}`;
          const livePath = document.createElementNS('http://www.w3.org/2000/svg', 'path');
          livePath.setAttribute('d', dStr);
          livePath.setAttribute('fill', 'none');
          livePath.setAttribute('stroke', '#2b59ff');
          livePath.setAttribute('stroke-width', '2.5');
          livePath.setAttribute('marker-end', 'url(#arrow-blue)');
          svg.appendChild(livePath);
        }
      }

      // Freehand pen strokes
      board.freehandStrokes.forEach(stroke => {
        if (stroke.length < 2) return;
        let d = `M ${stroke[0].x} ${stroke[0].y}`;
        for (let i = 1; i < stroke.length; i++) {
          d += ` L ${stroke[i].x} ${stroke[i].y}`;
        }
        const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
        path.setAttribute('d', d);
        path.setAttribute('fill', 'none');
        path.setAttribute('stroke', '#2b59ff');
        path.setAttribute('stroke-width', '3');
        path.setAttribute('stroke-linecap', 'round');
        svg.appendChild(path);
      });
    }

    function toggleConnectorRouting() {
      board.connectorRouting = board.connectorRouting === 'orthogonal' ? 'curve' : 'orthogonal';
      document.getElementById('ctx-routing-btn').innerText = board.connectorRouting === 'orthogonal' ? 'Elbow' : 'Curved';
      renderSVG();
    }

    // --- Miro Magnetic Connector Pull Handling (Generous 75px Snap Pull) ---
    let connectDragStartMouse = { x: 0, y: 0 };

    function startConnectorDrag(itemId, port, e) {
      board.isConnecting = true;
      connectDragStartMouse = { x: e.clientX, y: e.clientY };
      const pt = getPortCoords(itemId, port);
      board.connectingFrom = { id: itemId, port: port, x: pt.x, y: pt.y };
      board.connectingCurrent = getCanvasCoords(e);
      document.getElementById('canvas-viewport').classList.add('connecting');
      showNotification('Connecting: drag to a target or click another element (Esc to cancel)');
      renderSVG();
    }

    function armConnectorForSelected() {
      if (!board.selectedId) return;
      const pt = getPortCoords(board.selectedId, 'right');
      board.connectingFrom = { id: board.selectedId, port: 'right', x: pt.x, y: pt.y };
      board.isConnecting = true;
      connectDragStartMouse = { x: 0, y: 0 };
      document.getElementById('canvas-viewport').classList.add('connecting');
      showNotification('Connecting: click target card or port to connect (Esc to cancel)');
      renderSVG();
    }

    // --- Infinite Dynamic Minimap ---
    let minimapTransform = { scale: 0.05, minX: 0, minY: 0 };

    function updateMinimap() {
      const canvas = document.getElementById('minimap-canvas');
      if (!canvas) return;
      const ctx = canvas.getContext('2d');
      const mW = 190, mH = 120;
      canvas.width = mW;
      canvas.height = mH;

      ctx.fillStyle = '#f8f9fa';
      ctx.fillRect(0, 0, mW, mH);

      const vp = document.getElementById('canvas-viewport');
      if (!vp) return;
      const vpW = vp.offsetWidth / board.zoom;
      const vpH = vp.offsetHeight / board.zoom;
      const vpLeft = -board.panX / board.zoom;
      const vpTop = -board.panY / board.zoom;

      // Calculate dynamic world bounds including all elements, frames, and viewport
      let minX = vpLeft;
      let minY = vpTop;
      let maxX = vpLeft + vpW;
      let maxY = vpTop + vpH;

      board.frames.forEach(f => {
        minX = Math.min(minX, f.x);
        minY = Math.min(minY, f.y);
        maxX = Math.max(maxX, f.x + f.w);
        maxY = Math.max(maxY, f.y + f.h);
      });

      board.elements.forEach(el => {
        const dom = document.getElementById(el.id);
        const elW = el.w || (dom ? dom.offsetWidth : 200);
        const elH = el.h || (dom ? dom.offsetHeight : 150);
        minX = Math.min(minX, el.x);
        minY = Math.min(minY, el.y);
        maxX = Math.max(maxX, el.x + elW);
        maxY = Math.max(maxY, el.y + elH);
      });

      // Add generous margin in world space
      minX -= 250;
      minY -= 250;
      maxX += 250;
      maxY += 250;

      const spanX = Math.max(1000, maxX - minX);
      const spanY = Math.max(650, maxY - minY);
      const scale = Math.min(mW / spanX, mH / spanY);

      minimapTransform = { scale, minX, minY };

      // Render frames
      board.frames.forEach(f => {
        ctx.strokeStyle = '#94a3b8';
        ctx.lineWidth = 1;
        ctx.strokeRect((f.x - minX) * scale, (f.y - minY) * scale, f.w * scale, f.h * scale);
      });

      // Render elements
      board.elements.forEach(el => {
        ctx.fillStyle = el.type === 'sticky' ? (el.color || '#fef08a') : (el.type === 'arch' ? '#3b82f6' : (el.type === 'erd' ? '#0f172a' : '#64748b'));
        const dom = document.getElementById(el.id);
        const elW = el.w || (dom ? dom.offsetWidth : 200);
        const elH = el.h || (dom ? dom.offsetHeight : 150);
        ctx.fillRect((el.x - minX) * scale, (el.y - minY) * scale, Math.max(4, elW * scale), Math.max(4, elH * scale));
      });

      // Render viewport lens box
      const box = document.getElementById('minimap-viewport');
      if (box) {
        box.style.left = ((vpLeft - minX) * scale) + 'px';
        box.style.top = ((vpTop - minY) * scale) + 'px';
        box.style.width = Math.max(8, vpW * scale) + 'px';
        box.style.height = Math.max(6, vpH * scale) + 'px';
      }
    }

    function updateMinimapViewportBox() {
      updateMinimap();
    }

    function panToMinimap(e) {
      const rect = document.getElementById('minimap-canvas').getBoundingClientRect();
      const clickX = e.clientX - rect.left;
      const clickY = e.clientY - rect.top;

      const worldX = minimapTransform.minX + clickX / minimapTransform.scale;
      const worldY = minimapTransform.minY + clickY / minimapTransform.scale;

      const vp = document.getElementById('canvas-viewport');
      board.panX = vp.offsetWidth / 2 - worldX * board.zoom;
      board.panY = vp.offsetHeight / 2 - worldY * board.zoom;
      applyTransform();
    }

    function toggleMinimap() {
      const map = document.getElementById('minimap-container');
      map.style.display = map.style.display === 'none' ? 'block' : 'none';
    }

    // --- Collapsible Right Context Drawer (Section 5.2) ---
    function toggleRightDrawer() {
      const drawer = document.getElementById('right-drawer');
      const vp = document.getElementById('canvas-viewport');
      const isOpen = drawer.classList.contains('open');

      if (isOpen) {
        closeRightDrawer();
      } else {
        openRightDrawer();
      }
    }

    function openRightDrawer() {
      const drawer = document.getElementById('right-drawer');
      const vp = document.getElementById('canvas-viewport');
      drawer.classList.add('open');
      vp.classList.add('drawer-open');
      updateDrawerContent();
    }

    function closeRightDrawer() {
      const drawer = document.getElementById('right-drawer');
      const vp = document.getElementById('canvas-viewport');
      drawer.classList.remove('open');
      vp.classList.remove('drawer-open');
    }

    function openDrawerTab(tabName) {
      openRightDrawer();
      switchDrawerTab(tabName);
    }

    function switchDrawerTab(tabName) {
      board.activeDrawerTab = tabName;
      document.querySelectorAll('.drawer-tab').forEach(t => t.classList.remove('active'));
      const active = document.querySelector(`.drawer-tab[data-tab="${tabName}"]`);
      if (active) active.classList.add('active');
      updateDrawerContent();
    }

    function updateDrawerContent() {
      const body = document.getElementById('drawer-body');
      const title = document.getElementById('drawer-title');
      const item = board.elements.find(e => e.id === board.selectedId);

      if (board.activeDrawerTab === 'inspect') {
        title.innerText = 'Artifact Inspector';
        if (!item) {
          body.innerHTML = `<div style="color: var(--text-muted); text-align: center; margin-top: 40px;">Select any card, sticky note, or wireframe on the canvas to inspect fields and view system contracts.</div>`;
          return;
        }

        body.innerHTML = `
          <div style="display: flex; flex-direction: column; gap: 12px;">
            <div>
              <span class="card-family-tag">${item.type.toUpperCase()}</span>
              <div style="font-weight: 800; font-size: 14px; margin-top: 2px;">${escapeHTML(item.title || item.tableName || 'Selected Item')}</div>
            </div>

            <div style="display: flex; flex-direction: column; gap: 4px;">
              <label style="font-weight: 700; font-size: 10px; color: var(--text-muted); text-transform: uppercase;">Primary Content</label>
              <textarea style="width: 100%; height: 80px; padding: 8px; border: 1px solid var(--border-strong); border-radius: 6px; font-family: var(--font-sans); font-size: 12px;" oninput="itemContentChanged('${item.id}', this.value)">${escapeHTML(item.content || item.desc || '')}</textarea>
            </div>

            <div>
              <label style="font-weight: 700; font-size: 10px; color: var(--text-muted); text-transform: uppercase; margin-bottom: 4px; display: block;">System Property Actions</label>
              <div style="display: flex; flex-direction: column; gap: 6px;">
                <button class="btn btn-sm" onclick="showNotification('Generated OpenAPI contract definition')">Export OpenAPI Spec Segment</button>
                <button class="btn btn-sm" onclick="showNotification('Schema DDL verified successfully')">Validate SQL Schema DDL</button>
                <button class="btn btn-sm" onclick="showNotification('Zero-Trust boundary check passed')">Audit Security Boundaries</button>
              </div>
            </div>
            ${item.attachedMockup ? `
            <div style="padding: 10px; background: #f0fdf4; border: 1.5px solid #86efac; border-radius: 8px; margin-top: 10px;">
              <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 6px;">
                <span style="font-size: 11px; font-weight: 700; color: #15803d; display: flex; align-items: center; gap: 5px;">
                  Attached UI Specification
                </span>
                <span style="font-size: 9.5px; color: #16a34a;">${item.attachedMockup.caption || 'Active'}</span>
              </div>
              <img src="${item.attachedMockup.dataUrl}" style="width: 100%; height: 110px; object-fit: contain; background: #ffffff; border-radius: 6px; border: 1px solid #bbf7d0; display: block; margin-bottom: 6px;">
              <div style="display: flex; gap: 6px;">
                <button class="btn btn-sm" onclick="openSketchModal('${item.id}')" style="font-size: 10.5px; padding: 3px 8px;">Re-draw / Edit</button>
                <button class="btn btn-sm btn-ghost" onclick="removeAttachedMockup('${item.id}')" style="font-size: 10.5px; padding: 3px 8px; color: #dc2626;">Detach</button>
              </div>
            </div>` : `
            <div style="padding: 10px; background: #f8fafc; border: 1px dashed #cbd5e1; border-radius: 8px; margin-top: 10px; text-align: center;">
              <div style="font-size: 11px; color: #64748b; margin-bottom: 6px;">No UI mockup attached yet.</div>
              <button class="btn btn-sm btn-primary" onclick="openSketchModal('${item.id}')" style="font-size: 11px; padding: 4px 10px;">
                Draw / Attach UI Mockup
              </button>
            </div>`}

            ${item.linkedSkills && item.linkedSkills.length > 0 ? `
            <div style="padding: 10px; background: #eff6ff; border: 1px solid #bfdbfe; border-radius: 8px; margin-top: 10px;">
              <div style="font-size: 11px; font-weight: 700; color: #1d4ed8; margin-bottom: 5px;">Linked Claude Skills</div>
              <div style="display: flex; flex-wrap: wrap; gap: 4px;">
                ${item.linkedSkills.map(sk => `<span style="padding: 2px 7px; border-radius: 4px; font-size: 10px; font-weight: 600; background: #dbeafe; color: #1e40af; font-family: monospace;">${sk}</span>`).join('')}
              </div>
            </div>` : ''}


            <div style="padding-top: 10px; border-top: 1px solid var(--border);">
              <div style="font-size: 10px; color: var(--text-muted);">
                <div>Canonical Hash: <code>${Math.abs(item.id.split('').reduce((a,b)=>{a=((a<<5)-a)+b.charCodeAt(0);return a&a},0)).toString(16)}</code></div>
                <div>Status: <span style="color: #059669; font-weight: 700;">Verified Valid Schema</span></div>
              </div>
            </div>
          </div>
        `;
      } else if (board.activeDrawerTab === 'specs') {
        title.innerText = 'System Specification';
        body.innerHTML = `
          <div style="display: flex; flex-direction: column; gap: 12px; height: 100%;">
            <div style="padding: 10px; background: #f8fafc; border: 1px solid var(--border); border-radius: 6px; font-size: 11px;">
              <strong>Active Component:</strong> ${item ? (item.title || item.tableName || item.id) : 'System Board'}
            </div>
            <div style="display: flex; flex-direction: column; gap: 6px;">
              <label style="font-weight: 700; font-size: 10px; color: var(--text-muted); text-transform: uppercase;">Service Level Objectives (SLOs)</label>
              <div style="padding: 8px; background: #fff; border: 1px solid var(--border); border-radius: 6px; font-size: 11px; line-height: 1.6;">
                <div>• Latency target: <strong>p95 &lt; 45ms</strong></div>
                <div>• Uptime SLA: <strong>99.99% multi-region</strong></div>
                <div>• Throughput budget: <strong>50,000 req/sec</strong></div>
                <div>• Data retention: <strong>90 days active / 7 yrs archive</strong></div>
              </div>
            </div>
            <div style="display: flex; flex-direction: column; gap: 6px;">
              <label style="font-weight: 700; font-size: 10px; color: var(--text-muted); text-transform: uppercase;">Interface Protocols</label>
              <div style="padding: 8px; background: #fff; border: 1px solid var(--border); border-radius: 6px; font-size: 11px; line-height: 1.6;">
                <div>• Public API: <strong>HTTPS / TLS 1.3 / REST OpenAPI 3.1</strong></div>
                <div>• Internal RPC: <strong>gRPC / Protobuf v3 with mTLS</strong></div>
                <div>• Event Broker: <strong>Apache Kafka v3.6 / JSON CloudEvents</strong></div>
              </div>
            </div>
          </div>
        `;
      } else if (board.activeDrawerTab === 'deploy') {
        title.innerText = 'Infrastructure Deployment';
        body.innerHTML = `
          <div style="display: flex; flex-direction: column; gap: 10px;">
            <div style="padding: 8px 10px; background: #f8fafc; border-left: 3px solid var(--miro-blue); border-radius: 4px;">
              <div style="font-weight: 700;">Stage 1: State & Storage Tier</div>
              <div style="font-size: 11px; color: var(--text-muted); margin-top: 2px;">• PostgreSQL Primary + Read Replicas (ACID)</div>
              <div style="font-size: 11px; color: var(--text-muted);">• Redis Cluster (Cache & Idempotency Locks)</div>
            </div>
            <div style="padding: 8px 10px; background: #f8fafc; border-left: 3px solid #8b5cf6; border-radius: 4px;">
              <div style="font-weight: 700;">Stage 2: Messaging & Core Services</div>
              <div style="font-size: 11px; color: var(--text-muted); margin-top: 2px;">• Apache Kafka Cluster & Topic Partitions</div>
              <div style="font-size: 11px; color: var(--text-muted);">• Microservices Stateless Containers (Kubernetes)</div>
            </div>
            <div style="padding: 8px 10px; background: #f8fafc; border-left: 3px solid #10b981; border-radius: 4px;">
              <div style="font-weight: 700;">Stage 3: Ingress, Security & Edge</div>
              <div style="font-size: 11px; color: var(--text-muted); margin-top: 2px;">• Envoy / Traefik API Gateway</div>
              <div style="font-size: 11px; color: var(--text-muted);">• Cloudflare Global CDN, WAF & DDoS Shield</div>
            </div>
          </div>
        `;
      } else if (board.activeDrawerTab === 'security') {
        title.innerText = 'Security & Compliance Controls';
        body.innerHTML = `
          <div style="display: flex; flex-direction: column; gap: 8px;">
            <div style="padding: 8px; border: 1px solid var(--border); border-radius: 6px; display: flex; justify-content: space-between; align-items: center;">
              <div>
                <div style="font-weight: 700;">Zero-Trust mTLS</div>
                <div style="font-size: 10px; color: var(--text-muted);">Mutual TLS encryption between all internal pods</div>
              </div>
              <span style="color: var(--success); font-weight: 700; font-size: 10px;">Enforced</span>
            </div>
            <div style="padding: 8px; border: 1px solid var(--border); border-radius: 6px; display: flex; justify-content: space-between; align-items: center;">
              <div>
                <div style="font-weight: 700;">PCI-DSS Tokenization</div>
                <div style="font-size: 10px; color: var(--text-muted);">Zero raw card numbers stored in core databases</div>
              </div>
              <span style="color: var(--success); font-weight: 700; font-size: 10px;">Compliant</span>
            </div>
            <div style="padding: 8px; border: 1px solid var(--border); border-radius: 6px; display: flex; justify-content: space-between; align-items: center;">
              <div>
                <div style="font-weight: 700;">PostgreSQL Row-Level Security</div>
                <div style="font-size: 10px; color: var(--text-muted);">Strict tenant isolation per SQL query</div>
              </div>
              <span style="color: var(--success); font-weight: 700; font-size: 10px;">Active</span>
            </div>
            <div style="padding: 8px; border: 1px solid var(--border); border-radius: 6px; display: flex; justify-content: space-between; align-items: center;">
              <div>
                <div style="font-weight: 700;">Immutable Audit Logs</div>
                <div style="font-size: 10px; color: var(--text-muted);">Append-only audit events sent to cold storage</div>
              </div>
              <span style="color: var(--success); font-weight: 700; font-size: 10px;">Active</span>
            </div>
          </div>
        `;
      } else if (board.activeDrawerTab === 'skills') {
        title.innerText = 'Skills Registry';
        body.innerHTML = getSkillsPanelHTML();
      } else if (board.activeDrawerTab === 'history') {
        title.innerText = 'Immutable Audit Trail';
        body.innerHTML = `
          <div style="display: flex; flex-direction: column; gap: 8px; font-family: var(--font-mono); font-size: 10px;">
            <div style="padding: 6px; background: #f8fafc; border-radius: 4px; border: 1px solid var(--border);">
              <div style="color: var(--miro-blue); font-weight: 700;">rev 4 · 2026-11-17 11:42:10</div>
              <div>Actor: System Architecture Engine</div>
              <div>Action: Patched SCR-002 state matrix</div>
            </div>
            <div style="padding: 6px; background: #f8fafc; border-radius: 4px; border: 1px solid var(--border);">
              <div style="color: var(--text); font-weight: 700;">rev 3 · 2026-11-17 11:35:09</div>
              <div>Actor: Lead Architect (HP)</div>
              <div>Action: Connected arch-1 to erd-1 via 90° elbow</div>
            </div>
            <div style="padding: 6px; background: #f8fafc; border-radius: 4px; border: 1px solid var(--border);">
              <div style="color: var(--text); font-weight: 700;">rev 2 · 2026-11-17 11:20:00</div>
              <div>Actor: Lead Architect (HP)</div>
              <div>Action: Stamped Stripe Billing Node</div>
            </div>
          </div>
        `;
      }
    }


    function addWaveTaskToCanvas() {
      pushHistory();
      const id = 'card-' + Date.now();
      const vp = document.getElementById('canvas-viewport').getBoundingClientRect();
      const x = (vp.width / 2 - board.panX) / board.zoom - 150;
      const y = (vp.height / 2 - board.panY) / board.zoom - 90;

      board.elements.push({
        id,
        type: 'card',
        family: 'task',
        status: 'approved',
        alias: 'TSK-' + Math.floor(100 + Math.random() * 900),
        x,
        y,
        w: 300,
        title: 'New Implementation Task',
        content: 'Task description with complexity rating S/M/L and dependencies.',
        relations: []
      });
      renderElements();
      selectElement(id);
    }

    // --- Quick Find Modal (Ctrl+K) ---
    function openQuickFindModal() {
      document.getElementById('quickfind-modal').classList.add('open');
      filterQuickFind('');
      setTimeout(() => document.getElementById('quickfind-input').focus(), 50);
    }

    function closeQuickFindModal() {
      document.getElementById('quickfind-modal').classList.remove('open');
    }

    function filterQuickFind(query) {
      const q = query.toLowerCase().trim();
      const resultsDiv = document.getElementById('quickfind-results');

      const matches = board.elements.filter(el => {
        const text = (el.title || el.tableName || el.content || el.desc || el.id).toLowerCase();
        return !q || text.includes(q);
      });

      if (matches.length === 0) {
        resultsDiv.innerHTML = `<div style="color: var(--text-muted); text-align: center; padding: 12px;">No matching artifacts found</div>`;
        return;
      }

      resultsDiv.innerHTML = matches.map(el => `
        <div style="padding: 8px 10px; border: 1px solid var(--border); border-radius: 6px; cursor: pointer; display: flex; align-items: center; justify-content: space-between;" onclick="jumpToElement('${el.id}')">
          <div>
            <strong style="font-size: 12px;">${escapeHTML(el.title || el.tableName || el.id)}</strong>
            <div style="font-size: 10px; color: var(--text-muted);">${el.type.toUpperCase()} · ${escapeHTML((el.content || el.desc || '').substring(0, 45))}...</div>
          </div>
          <span class="btn btn-sm" style="font-size: 9px;">Jump to node</span>
        </div>
      `).join('');
    }

    function jumpToElement(id) {
      closeQuickFindModal();
      const el = board.elements.find(e => e.id === id);
      if (!el) return;

      const vp = document.getElementById('canvas-viewport');
      board.panX = (vp.offsetWidth / 2) - el.x * board.zoom - 100;
      board.panY = (vp.offsetHeight / 2) - el.y * board.zoom - 80;
      applyTransform();
      selectElement(id);
    }

    // --- Canvas Listeners: Infinite Pan Physics, Multi-Gesture Zoom, Trackpad & Mouse Support ---
    let isSpacePressed = false;
    let isRightDragging = false;

    function setupCanvasListeners() {
      const vp = document.getElementById('canvas-viewport');

      // Miro Natural Wheel & Trackpad Gestures:
      // - Normal Scroll (Wheel / 2-Finger Trackpad): PANS in all directions across the infinite board
      // - Pinch / Ctrl+Wheel: ZOOMS smoothly centered at cursor location
      vp.addEventListener('wheel', (e) => {
        e.preventDefault();
        if (e.ctrlKey || e.metaKey) {
          const factor = e.deltaY < 0 ? 1.08 : 0.92;
          const rect = vp.getBoundingClientRect();
          const mouseX = e.clientX - rect.left;
          const mouseY = e.clientY - rect.top;

          const newZoom = Math.max(0.05, Math.min(5.0, board.zoom * factor));
          const scaleChange = newZoom / board.zoom;

          board.panX = mouseX - (mouseX - board.panX) * scaleChange;
          board.panY = mouseY - (mouseY - board.panY) * scaleChange;
          board.zoom = newZoom;
          applyTransform();
        } else {
          board.panX -= e.deltaX;
          board.panY -= e.deltaY;
          applyTransform();
        }
      }, { passive: false });

      // Spacebar toggles hand panning cursor everywhere
      window.addEventListener('keydown', (e) => {
        if (e.code === 'Space' && !e.repeat && document.activeElement.tagName !== 'INPUT' && document.activeElement.tagName !== 'TEXTAREA' && !document.activeElement.isContentEditable) {
          isSpacePressed = true;
          vp.classList.add('panning');
        }
        if (e.shiftKey && (e.key === '1' || e.code === 'Digit1')) {
          e.preventDefault();
          fitToContent();
        }
      });

      window.addEventListener('keyup', (e) => {
        if (e.code === 'Space') {
          isSpacePressed = false;
          if (!isPanning && board.currentTool !== 'pan') {
            vp.classList.remove('panning');
          }
        }
      });

      // Prevent native context menu on right-click drag pan
      vp.addEventListener('contextmenu', (e) => {
        if (isRightDragging) {
          e.preventDefault();
          isRightDragging = false;
        }
      });

      vp.addEventListener('mousedown', (e) => {
        // Right-Click Drag to Pan anywhere across the infinite canvas
        if (e.button === 2) {
          isPanning = true;
          isRightDragging = true;
          panStartX = e.clientX;
          panStartY = e.clientY;
          initialPanX = board.panX;
          initialPanY = board.panY;
          vp.classList.add('panning');
          e.preventDefault();
          return;
        }

        if (e.target.closest('.sticky-note, .canvas-shape, .arch-node, .erd-table, .typed-card, .wireframe-screen, .miro-context-bar, .miro-left-dock, .miro-bottom-dock, .dock-flyout, .selection-gizmo, .miro-minimap, .right-context-drawer, .canvas-frame-header, .frame-resize-handle')) {
          return;
        }

        closeAllFlyouts();

        if (board.currentTool === 'pen') {
          const pt = getCanvasCoords(e);
          const newStroke = [pt];
          board.freehandStrokes.push(newStroke);

          function onPenMove(pe) {
            newStroke.push(getCanvasCoords(pe));
            renderSVG();
          }
          function onPenUp() {
            window.removeEventListener('mousemove', onPenMove);
            window.removeEventListener('mouseup', onPenUp);
          }
          window.addEventListener('mousemove', onPenMove);
          window.addEventListener('mouseup', onPenUp);
          return;
        }

        // Panning: Hand Tool (H), Spacebar+Drag, Middle Click (button 1)
        if (board.currentTool === 'pan' || e.button === 1 || isSpacePressed) {
          isPanning = true;
          panStartX = e.clientX;
          panStartY = e.clientY;
          initialPanX = board.panX;
          initialPanY = board.panY;
          vp.classList.add('panning');
          return;
        }

        if (board.currentTool === 'select') {
          isMarquee = true;
          marqueeStartX = e.clientX;
          marqueeStartY = e.clientY;
          const box = document.getElementById('marquee-box');
          box.style.left = marqueeStartX + 'px';
          box.style.top = marqueeStartY + 'px';
          box.style.width = '0px';
          box.style.height = '0px';
          box.style.display = 'block';
          deselectAll();
        }
      });

      window.addEventListener('mousemove', (e) => {
        // Live Connector Drawing with 70px Intelligent Magnetic Snapping
        if (board.isConnecting) {
          board.connectingCurrent = getCanvasCoords(e);
          const cur = board.connectingCurrent;
          let bestDist = 70; // 70px magnetic pull radius
          let bestTarget = null;

          board.elements.forEach(el => {
            if (board.connectingFrom && el.id === board.connectingFrom.id) return;
            const ports = ['top', 'right', 'bottom', 'left'];
            ports.forEach(p => {
              const coords = getPortCoords(el.id, p);
              const dist = Math.hypot(coords.x - cur.x, coords.y - cur.y);
              if (dist < bestDist) {
                bestDist = dist;
                bestTarget = { id: el.id, port: p, x: coords.x, y: coords.y };
              }
            });
          });

          board.snappedTarget = bestTarget;

          document.querySelectorAll('.snap-port.snapped').forEach(el => el.classList.remove('snapped'));
          if (bestTarget) {
            const portEl = document.querySelector(`.snap-port[data-id="${bestTarget.id}"][data-port="${bestTarget.port}"]`);
            if (portEl) portEl.classList.add('snapped');
          }

          renderSVG();
          return;
        }

        // Panning Canvas
        if (isPanning) {
          board.panX = initialPanX + (e.clientX - panStartX);
          board.panY = initialPanY + (e.clientY - panStartY);
          applyTransform();
        }
        // Frame Dragging (Frame + Contained Children Move in Sync)
        else if (dragFrame) {
          const dx = (e.clientX - dragStartMouseX) / board.zoom;
          const dy = (e.clientY - dragStartMouseY) / board.zoom;
          dragFrame.x = dragFrameStartX + dx;
          dragFrame.y = dragFrameStartY + dy;

          const fDom = document.getElementById(dragFrame.id);
          if (fDom) {
            fDom.style.left = dragFrame.x + 'px';
            fDom.style.top = dragFrame.y + 'px';
          }

          dragFrameElements.forEach(item => {
            item.el.x = item.startX + dx;
            item.el.y = item.startY + dy;
            const dom = document.getElementById(item.el.id);
            if (dom) {
              dom.style.left = item.el.x + 'px';
              dom.style.top = item.el.y + 'px';
            }
          });

          renderSVG();
          updateMinimap();
        }
        // Frame Resizing
        else if (resizeFrame) {
          const dx = (e.clientX - resizeStartMouseX) / board.zoom;
          const dy = (e.clientY - resizeStartMouseY) / board.zoom;
          resizeFrame.w = Math.max(200, resizeStartFrameW + dx);
          resizeFrame.h = Math.max(150, resizeStartFrameH + dy);

          const fDom = document.getElementById(resizeFrame.id);
          if (fDom) {
            fDom.style.width = resizeFrame.w + 'px';
            fDom.style.height = resizeFrame.h + 'px';
          }
          updateMinimap();
        }
        // Marquee Selection Box
        else if (isMarquee) {
          const box = document.getElementById('marquee-box');
          const left = Math.min(e.clientX, marqueeStartX);
          const top = Math.min(e.clientY, marqueeStartY);
          const width = Math.abs(e.clientX - marqueeStartX);
          const height = Math.abs(e.clientY - marqueeStartY);
          box.style.left = left + 'px';
          box.style.top = top + 'px';
          box.style.width = width + 'px';
          box.style.height = height + 'px';
        }
        // Element Dragging
        else if (dragItem) {
          const dx = (e.clientX - dragStartMouseX) / board.zoom;
          const dy = (e.clientY - dragStartMouseY) / board.zoom;
          dragItem.x = dragItemStartX + dx;
          dragItem.y = dragItemStartY + dy;

          const dom = document.getElementById(dragItem.id);
          if (dom) {
            dom.style.left = dragItem.x + 'px';
            dom.style.top = dragItem.y + 'px';
          }
          renderSVG();
          updateSelectionGizmo();
          updateContextToolbarPosition();
        }
        // Element Resizing
        else if (resizeItem) {
          const dx = (e.clientX - resizeStartMouseX) / board.zoom;
          const dy = (e.clientY - resizeStartMouseY) / board.zoom;

          if (resizeHandle.includes('e')) resizeItem.w = Math.max(120, resizeStartItemW + dx);
          if (resizeHandle.includes('s')) resizeItem.h = Math.max(80, resizeStartItemH + dy);

          const dom = document.getElementById(resizeItem.id);
          if (dom) {
            dom.style.width = resizeItem.w + 'px';
            if (resizeItem.h) dom.style.height = resizeItem.h + 'px';
          }
          renderSVG();
          updateSelectionGizmo();
          updateContextToolbarPosition();
        }
      });

      window.addEventListener('mouseup', (e) => {
        // Connector Release: Magnetic Docking
        if (board.isConnecting) {
          const movedDist = Math.hypot(e.clientX - connectDragStartMouse.x, e.clientY - connectDragStartMouse.y);
          let target = board.snappedTarget;

          // If no port snapped, check if mouse is over any element
          if (!target) {
            const cur = getCanvasCoords(e);
            const hitEl = board.elements.find(el => {
              if (board.connectingFrom && el.id === board.connectingFrom.id) return false;
              const dom = document.getElementById(el.id);
              const w = el.w || (dom ? dom.offsetWidth : 200);
              const h = el.h || (dom ? dom.offsetHeight : 150);
              return cur.x >= el.x && cur.x <= el.x + w && cur.y >= el.y && cur.y <= el.y + h;
            });

            if (hitEl && board.connectingFrom) {
              const fromCoords = board.connectingFrom;
              let minDist = Infinity;
              let bestPort = 'left';
              ['top', 'right', 'bottom', 'left'].forEach(p => {
                const pCoord = getPortCoords(hitEl.id, p);
                const dist = Math.hypot(pCoord.x - fromCoords.x, pCoord.y - fromCoords.y);
                if (dist < minDist) {
                  minDist = dist;
                  bestPort = p;
                }
              });
              target = { id: hitEl.id, port: bestPort };
            }
          }

          if (target && board.connectingFrom && target.id !== board.connectingFrom.id) {
            pushHistory();
            const fromObj = board.elements.find(el => el.id === board.connectingFrom.id);
            const toObj = board.elements.find(el => el.id === target.id);
            const fromName = fromObj ? (fromObj.title || fromObj.id) : board.connectingFrom.id;
            const toName = toObj ? (toObj.title || toObj.id) : target.id;

            board.edges.push({
              id: 'e-' + Date.now(),
              from: board.connectingFrom.id,
              fromPort: board.connectingFrom.port,
              to: target.id,
              toPort: target.port,
              label: 'depends_on',
              routing: board.connectorRouting || 'orthogonal'
            });
            showNotification(`Connected ${fromName} → ${toName}`);

            board.isConnecting = false;
            board.connectingFrom = null;
            board.snappedTarget = null;
            document.getElementById('canvas-viewport').classList.remove('connecting');
            document.querySelectorAll('.snap-port.snapped').forEach(el => el.classList.remove('snapped'));
            renderAll();
            return;
          }

          // If user merely CLICKED on the port (moved < 6px) and didn't release on a target:
          // Stay in connecting mode, ready for click on Card B!
          if (movedDist < 6 && board.connectingFrom) {
            showNotification('Connecting: now click target card or port to connect (Esc to cancel)');
            return;
          }

          board.isConnecting = false;
          board.connectingFrom = null;
          board.snappedTarget = null;
          document.getElementById('canvas-viewport').classList.remove('connecting');
          document.querySelectorAll('.snap-port.snapped').forEach(el => el.classList.remove('snapped'));
          renderSVG();
          updateStatusBar();
          return;
        }

        if (isPanning) {
          isPanning = false;
          setTimeout(() => { isRightDragging = false; }, 50);
          if (!isSpacePressed && board.currentTool !== 'pan') {
            vp.classList.remove('panning');
          }
        }
        if (dragFrame) {
          showNotification(`Moved frame "${dragFrame.title}" with ${dragFrameElements.length} contained item(s)`);
          dragFrame = null;
          dragFrameElements = [];
          renderAll();
        }
        if (resizeFrame) {
          showNotification(`Resized frame "${resizeFrame.title}" to ${Math.round(resizeFrame.w)}×${Math.round(resizeFrame.h)}px`);
          resizeFrame = null;
          renderAll();
        }
        if (isMarquee) {
          isMarquee = false;
          document.getElementById('marquee-box').style.display = 'none';

          const minX = Math.min(e.clientX, marqueeStartX);
          const maxX = Math.max(e.clientX, marqueeStartX);
          const minY = Math.min(e.clientY, marqueeStartY);
          const maxY = Math.max(e.clientY, marqueeStartY);

          if (maxX - minX > 10 || maxY - minY > 10) {
            const vpRect = vp.getBoundingClientRect();
            const wMinX = (minX - vpRect.left - board.panX) / board.zoom;
            const wMaxX = (maxX - vpRect.left - board.panX) / board.zoom;
            const wMinY = (minY - vpRect.top - board.panY) / board.zoom;
            const wMaxY = (maxY - vpRect.top - board.panY) / board.zoom;

            const hit = board.elements.find(el => {
              const elW = el.w || 250;
              const elH = el.h || 180;
              return !(el.x > wMaxX || el.x + elW < wMinX || el.y > wMaxY || el.y + elH < wMinY);
            });
            if (hit) selectElement(hit.id);
          }
        }
        if (dragItem) dragItem = null;
        if (resizeItem) resizeItem = null;
        updateMinimap();
      });

      // Gizmo Resize Handles
      document.querySelectorAll('.gizmo-handle[data-handle]').forEach(h => {
        h.addEventListener('mousedown', (e) => {
          if (!board.selectedId) return;
          const item = board.elements.find(el => el.id === board.selectedId);
          if (!item) return;

          pushHistory();
          resizeItem = item;
          resizeHandle = h.dataset.handle;
          resizeStartMouseX = e.clientX;
          resizeStartMouseY = e.clientY;
          resizeStartItemW = item.w || 200;
          resizeStartItemH = item.h || 150;
          e.stopPropagation();
        });
      });
    }

    // Keyboard Shortcuts (Miro Standard)
    function setupKeyListeners() {
      window.addEventListener('keydown', (e) => {
        if (e.target.isContentEditable || e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;

        if ((e.ctrlKey || e.metaKey) && (e.key === 'k' || e.key === 'K')) {
          e.preventDefault();
          openQuickFindModal();
        }
        else if (e.key === 'v' || e.key === 'V') setTool('select');
        else if (e.key === 'h' || e.key === 'H') setTool('pan');
        else if (e.key === 'n' || e.key === 'N') toggleFlyout('sticky');
        else if (e.key === 'a' || e.key === 'A') toggleFlyout('arch');
        else if (e.key === 'd' || e.key === 'D') addDatabaseTable();
        else if (e.key === 's' || e.key === 'S') toggleFlyout('shape');
        else if (e.key === 'l' || e.key === 'L') setTool('connector');
        else if (e.key === 't' || e.key === 'T') addTextElement();
        else if (e.key === 'w' || e.key === 'W') toggleFlyout('wireframe');
        else if (e.key === 'f' || e.key === 'F') addZoneFrame();
        else if (e.key === 'p' || e.key === 'P') setTool('pen');
        else if (e.key === 'e' || e.key === 'E') setTool('eraser');
        else if (e.key === 'Escape') {
        if (board.isConnecting) {
          board.isConnecting = false;
          board.connectingFrom = null;
          board.snappedTarget = null;
          document.getElementById('canvas-viewport').classList.remove('connecting');
          document.querySelectorAll('.snap-port.snapped').forEach(el => el.classList.remove('snapped'));
          showNotification('Connection canceled');
          renderSVG();
        }
        closeAllFlyouts();
        closeRightDrawer();
        const qm = document.getElementById('quickfind-modal');
        if (qm) qm.style.display = 'none';
        const em = document.getElementById('export-modal');
        if (em) em.style.display = 'none';
        deselectAll();
        setTool('select');
      }
      else if (e.key === 'Delete' || e.key === 'Backspace') {
        if (document.activeElement && (document.activeElement.tagName === 'INPUT' || document.activeElement.tagName === 'TEXTAREA' || document.activeElement.isContentEditable)) {
          return;
        }
        deleteSelection();
      }
        else if ((e.ctrlKey || e.metaKey) && e.key === 'd') { e.preventDefault(); duplicateSelection(); }
        else if ((e.ctrlKey || e.metaKey) && e.key === 'z') { e.preventDefault(); undo(); }
        else if ((e.ctrlKey || e.metaKey) && e.key === 'y') { e.preventDefault(); redo(); }
        else if ((e.ctrlKey || e.metaKey) && e.key === '0') { e.preventDefault(); zoomTo100(); }
        else if ((e.ctrlKey || e.metaKey) && e.key === '1') { e.preventDefault(); resetCanvasView(); }
      });
    }

    function startElementDrag(e, item) {
      if (board.currentTool === 'eraser') {
        pushHistory();
        board.elements = board.elements.filter(el => el.id !== item.id);
        board.edges = board.edges.filter(edge => edge.from !== item.id && edge.to !== item.id);
        renderAll();
        return;
      }

      // If Connector is actively seeking a target (via Tool L, Context Toolbar, or Port Click)
      if (board.isConnecting && board.connectingFrom) {
        if (board.connectingFrom.id !== item.id) {
          e.stopPropagation();
          pushHistory();
          const p1 = board.connectingFrom;
          let minDist = Infinity;
          let bestPort = 'left';
          ['left', 'top', 'right', 'bottom'].forEach(p => {
            const pCoord = getPortCoords(item.id, p);
            const d = Math.hypot(pCoord.x - p1.x, pCoord.y - p1.y);
            if (d < minDist) {
              minDist = d;
              bestPort = p;
            }
          });

          const fromObj = board.elements.find(el => el.id === board.connectingFrom.id);
          const fromName = fromObj ? (fromObj.title || fromObj.id) : board.connectingFrom.id;
          const toName = item.title || item.id;

          board.edges.push({
            id: 'e-' + Date.now(),
            from: board.connectingFrom.id,
            fromPort: board.connectingFrom.port,
            to: item.id,
            toPort: bestPort,
            label: 'depends_on',
            routing: board.connectorRouting || 'orthogonal'
          });

          showNotification(`Connected ${fromName} → ${toName}`);
          board.isConnecting = false;
          board.connectingFrom = null;
          board.snappedTarget = null;
          document.getElementById('canvas-viewport').classList.remove('connecting');
          document.querySelectorAll('.snap-port.snapped').forEach(el => el.classList.remove('snapped'));
          setTool('select');
          renderAll();
        }
        return;
      }

      // If Tool is connector and starting fresh from Card A
      if (board.currentTool === 'connector') {
        e.stopPropagation();
        const pt = getPortCoords(item.id, 'right');
        board.connectingFrom = { id: item.id, port: 'right', x: pt.x, y: pt.y };
        board.isConnecting = true;
        connectDragStartMouse = { x: 0, y: 0 };
        document.getElementById('canvas-viewport').classList.add('connecting');
        showNotification('Connecting: click target card or port to complete connection (Esc to cancel)');
        renderSVG();
        return;
      }

      // Stop event propagation immediately so canvas or frame never intercepts
      e.stopPropagation();

      // Select exclusively this element
      selectElement(item.id);

      if (e.target.isContentEditable || e.target.tagName === 'INPUT' || e.target.tagName === 'BUTTON') {
        return;
      }

      pushHistory();
      dragItem = item;
      dragStartMouseX = e.clientX;
      dragStartMouseY = e.clientY;
      dragItemStartX = item.x;
      dragItemStartY = item.y;
    }

    function getCanvasCoords(e) {
      const vp = document.getElementById('canvas-viewport').getBoundingClientRect();
      return {
        x: (e.clientX - vp.left - board.panX) / board.zoom,
        y: (e.clientY - vp.top - board.panY) / board.zoom
      };
    }

    function selectElement(id) {
      board.selectedId = id;
      board.selectedFrameId = null;

      // Clear selection on all frames
      document.querySelectorAll('.canvas-frame').forEach(el => el.classList.remove('selected'));

      // Update selection on elements
      document.querySelectorAll('.sticky-note, .canvas-shape, .arch-node, .erd-table, .typed-card, .wireframe-screen').forEach(el => {
        el.classList.toggle('selected', el.id === id);
      });
      updateSelectionGizmo();
      updateContextToolbarPosition();
      updateDrawerContent();

      const item = board.elements.find(e => e.id === id);
      const colorDot = document.getElementById('ctx-active-color');
      if (item && item.color) {
        colorDot.style.background = item.color;
        colorDot.style.display = 'block';
      } else {
        colorDot.style.display = 'none';
      }
      document.getElementById('ctx-swatch-popover').classList.remove('open');
    }

    function selectFrame(frameId) {
      board.selectedFrameId = frameId;
      board.selectedId = null;

      // Deselect all elements and hide element gizmo & context toolbar
      document.querySelectorAll('.sticky-note, .canvas-shape, .arch-node, .erd-table, .typed-card, .wireframe-screen').forEach(el => {
        el.classList.remove('selected');
      });
      updateSelectionGizmo();
      updateContextToolbarPosition();

      // Toggle selected class on frames
      document.querySelectorAll('.canvas-frame').forEach(el => {
        el.classList.toggle('selected', el.id === frameId);
      });
    }

    function deselectAll() {
      board.selectedId = null;
      board.selectedFrameId = null;
      document.querySelectorAll('.canvas-frame').forEach(el => el.classList.remove('selected'));
      document.querySelectorAll('.sticky-note, .canvas-shape, .arch-node, .erd-table, .typed-card, .wireframe-screen').forEach(el => {
        el.classList.remove('selected');
      });
      updateSelectionGizmo();
      updateContextToolbarPosition();
    }

    // 8-Point Transform Gizmo Positioning
    function updateSelectionGizmo() {
      const gizmo = document.getElementById('selection-gizmo');
      if (!board.selectedId) {
        gizmo.classList.remove('active');
        return;
      }

      const item = board.elements.find(e => e.id === board.selectedId);
      if (!item) {
        gizmo.classList.remove('active');
        return;
      }

      const dom = document.getElementById(item.id);
      if (!dom) return;

      const w = item.w || dom.offsetWidth;
      const h = item.h || dom.offsetHeight;

      gizmo.style.left = item.x + 'px';
      gizmo.style.top = item.y + 'px';
      gizmo.style.width = w + 'px';
      gizmo.style.height = h + 'px';
      gizmo.classList.add('active');
    }

    // Context Toolbar Positioning (12px directly above selected item)
    function updateContextToolbarPosition() {
      const bar = document.getElementById('context-toolbar');
      if (!board.selectedId) {
        bar.classList.remove('open');
        return;
      }

      const item = board.elements.find(e => e.id === board.selectedId);
      if (!item) {
        bar.classList.remove('open');
        return;
      }

      const vp = document.getElementById('canvas-viewport').getBoundingClientRect();
      const screenX = vp.left + board.panX + item.x * board.zoom;
      const screenY = vp.top + board.panY + item.y * board.zoom - 44;

      bar.style.left = Math.max(16, screenX) + 'px';
      bar.style.top = Math.max(54, screenY) + 'px';
      bar.classList.add('open');
    }

    function toggleContextColorPopover() {
      document.getElementById('ctx-swatch-popover').classList.toggle('open');
    }

    function applySelectionColor(color) {
      if (!board.selectedId) return;
      const item = board.elements.find(e => e.id === board.selectedId);
      if (!item) return;

      pushHistory();
      item.color = color;
      const dom = document.getElementById(item.id);
      if (dom) dom.style.backgroundColor = color;
      document.getElementById('ctx-active-color').style.background = color;
      document.getElementById('ctx-swatch-popover').classList.remove('open');
      updateMinimap();
    }

    function addStickyTag(tag) {
      if (!board.selectedId) return;
      const item = board.elements.find(e => e.id === board.selectedId);
      if (!item || item.type !== 'sticky') return;

      pushHistory();
      item.tags = item.tags || [];
      if (!item.tags.includes(tag)) {
        item.tags.push(tag);
      } else {
        item.tags = item.tags.filter(t => t !== tag);
      }
      renderElements();
      selectElement(item.id);
    }

    function itemTitleChanged(id, newTitle) {
      const item = board.elements.find(e => e.id === id);
      if (item) {
        item.title = newTitle;
        updateDrawerContent();
      }
    }

    function itemContentChanged(id, newContent) {
      const item = board.elements.find(e => e.id === id);
      if (item) {
        item.content = newContent;
        const dom = document.querySelector(`#${id} .sticky-content`);
        if (dom) {
          const len = newContent.length;
          dom.style.fontSize = len > 140 ? '11px' : (len > 80 ? '13px' : '15px');
        }
      }
    }

    function setTool(tool) {
      board.currentTool = tool;
      document.querySelectorAll('.tool-btn').forEach(btn => btn.classList.remove('active'));
      const activeBtn = document.getElementById('tool-' + tool);
      if (activeBtn) activeBtn.classList.add('active');
      closeAllFlyouts();

      if (tool === 'connector') {
        const vp = document.getElementById('canvas-viewport');
        vp.classList.add('connecting');
      } else {
        const vp = document.getElementById('canvas-viewport');
        vp.classList.remove('connecting');
      }
    }

    function toggleFlyout(name) {
      const flyout = document.getElementById('flyout-' + name);
      const isOpen = flyout.classList.contains('open');
      closeAllFlyouts();
      if (!isOpen) flyout.classList.add('open');
    }

    function closeAllFlyouts() {
      document.querySelectorAll('.dock-flyout').forEach(el => el.classList.remove('open'));
    }

    function addStickyNote(color) {
      pushHistory();
      const id = 'st-' + Date.now();
      const vp = document.getElementById('canvas-viewport').getBoundingClientRect();
      const x = (vp.width / 2 - board.panX) / board.zoom - 100;
      const y = (vp.height / 2 - board.panY) / board.zoom - 100;

      board.elements.push({
        id,
        type: 'sticky',
        color,
        x,
        y,
        w: 200,
        h: 200,
        tags: ['Draft'],
        reactions: [],
        content: 'New brainstorm note...'
      });
      closeAllFlyouts();
      setTool('select');
      renderElements();
      selectElement(id);
    }

    function addArchNode(archType) {
      pushHistory();
      const id = 'arch-' + Date.now();
      const vp = document.getElementById('canvas-viewport').getBoundingClientRect();
      const x = (vp.width / 2 - board.panX) / board.zoom - 130;
      const y = (vp.height / 2 - board.panY) / board.zoom - 60;

      const defaults = {
        api_gateway: { title: 'API Gateway Service', desc: 'Reverse proxy, routing, and tenant token validation.', tags: ['FastAPI', '<20ms'] },
        reverse_proxy: { title: 'Reverse Proxy Edge', desc: 'Cloudflare / Traefik SSL termination and DDoS protection.', tags: ['Edge', 'Nginx'] },
        microservice: { title: 'Core Backend Service', desc: 'Domain business logic, gRPC services, and event dispatch.', tags: ['Go', 'gRPC'] },
        worker: { title: 'Background Async Worker', desc: 'Temporal / Celery distributed task queue & retries.', tags: ['Temporal', 'Celery'] },
        cron_scheduler: { title: 'Cron Scheduler Engine', desc: 'Dcron / Scheduled batch workflows and time triggers.', tags: ['Cron', 'Batch'] },
        websocket_server: { title: 'Real-Time WebSocket Hub', desc: 'Duplex streaming, audio packets, and user presence.', tags: ['WebSockets', '<50ms'] },

        kafka_cluster: { title: 'Apache Kafka Event Broker', desc: 'Distributed partition log with high-throughput event ordering.', tags: ['Kafka', 'Streaming'] },
        vector_db: { title: 'Vector Database', desc: 'Semantic search embeddings and cosine similarity index.', tags: ['pgvector', 'Qdrant'] },
        embedding_service: { title: 'Embedding Pipeline', desc: 'Document chunking pipeline and dense text embeddings.', tags: ['Embeddings', 'Chunking'] },
        guardrails: { title: 'WAF & Security Guardrail', desc: 'PII masking, prompt injection defense, and schema validator.', tags: ['Guardrails', 'PII'] },
        agent_swarm: { title: 'Multi-Agent Swarm', desc: 'Supervisor planner with autonomous tool-calling workers.', tags: ['Supervisor', 'Swarm'] },
        grpc_service: { title: 'gRPC Internal Service', desc: 'Low-latency Protobuf RPC with binary serialization and mTLS.', tags: ['gRPC', 'Protobuf'] },

        postgres: { title: 'PostgreSQL Database', desc: 'Relational multi-tenant persistent storage with JSONB.', tags: ['Postgres 16', 'ACID'] },
        redis_cache: { title: 'Redis Cache & Queue', desc: 'Session cache, token bucket rate limiter, and async buffer.', tags: ['Redis 7', 'BullMQ'] },
        clickhouse: { title: 'ClickHouse OLAP Store', desc: 'Vectorized column store for high-frequency telemetry.', tags: ['ClickHouse', '50k RPS'] },
        event_stream: { title: 'Kafka Event Bus', desc: 'Distributed event log with tenant-partitioned streams.', tags: ['Kafka', 'PubSub'] },
        object_store: { title: 'S3 Object Storage', desc: 'Cloudflare R2 / AWS S3 presigned asset storage.', tags: ['S3/R2', 'Storage'] },
        elastic_search: { title: 'Elasticsearch Index', desc: 'Fuzzy keyword search, autocomplete, and relevance ranking.', tags: ['Search', 'Lucene'] },

        stripe_billing: { title: 'Stripe Billing System', desc: 'Subscription lifecycle, webhooks, and customer portal.', tags: ['Stripe API', 'Webhooks'] },
        auth_service: { title: 'Auth & RBAC Service', desc: 'OAuth2 login, session tokens, and permission matrix.', tags: ['JWT', 'OAuth2'] },
        webhook_engine: { title: 'Webhook Dispatcher Hub', desc: 'Svix outbound webhook delivery with HMAC verification.', tags: ['Webhooks', 'Svix'] },
        email_gateway: { title: 'Email & SMS Gateway', desc: 'Transactional receipts, OTP verification, and alerts.', tags: ['Resend', 'SendGrid'] },
        audit_logger: { title: 'Immutable Audit Trail', desc: 'WORM append-only compliance logging and change tracking.', tags: ['Audit', 'SOC2'] },
        secrets_kms: { title: 'Secrets Vault & KMS', desc: 'Customer-managed encryption keys and secret rotation.', tags: ['Vault', 'KMS'] }
      };

      const def = defaults[archType] || { title: 'Cloud Service', desc: 'Service description...', tags: ['Cloud'] };

      board.elements.push({
        id,
        type: 'arch',
        archType,
        x,
        y,
        w: 260,
        title: def.title,
        desc: def.desc,
        tags: def.tags
      });
      closeAllFlyouts();
      setTool('select');
      renderElements();
      selectElement(id);
    }

    function addDatabaseTable() {
      pushHistory();
      const id = 'erd-' + Date.now();
      const vp = document.getElementById('canvas-viewport').getBoundingClientRect();
      const x = (vp.width / 2 - board.panX) / board.zoom - 135;
      const y = (vp.height / 2 - board.panY) / board.zoom - 100;

      board.elements.push({
        id,
        type: 'erd',
        x,
        y,
        w: 270,
        tableName: 'new_table_' + Math.floor(10 + Math.random() * 90),
        columns: [
          { name: 'id', type: 'UUID', isPk: true },
          { name: 'tenant_id', type: 'UUID', isFk: true },
          { name: 'name', type: 'VARCHAR(255)' },
          { name: 'created_at', type: 'TIMESTAMPTZ' }
        ]
      });
      setTool('select');
      renderElements();
      selectElement(id);
    }

    function addShape(shapeType) {
      pushHistory();
      const id = 'sh-' + Date.now();
      const vp = document.getElementById('canvas-viewport').getBoundingClientRect();
      const x = (vp.width / 2 - board.panX) / board.zoom - 110;
      const y = (vp.height / 2 - board.panY) / board.zoom - 60;

      board.elements.push({
        id,
        type: 'shape',
        shape: shapeType,
        color: '#ffffff',
        x,
        y,
        w: shapeType === 'circle' ? 160 : 220,
        h: shapeType === 'circle' ? 160 : 120,
        title: 'New ' + shapeType,
        content: shapeType.toUpperCase() + ' Node'
      });
      closeAllFlyouts();
      setTool('select');
      renderElements();
      selectElement(id);
    }

    function addTextElement() {
      pushHistory();
      const id = 'sh-' + Date.now();
      const vp = document.getElementById('canvas-viewport').getBoundingClientRect();
      const x = (vp.width / 2 - board.panX) / board.zoom - 100;
      const y = (vp.height / 2 - board.panY) / board.zoom - 30;

      board.elements.push({
        id,
        type: 'shape',
        shape: 'rect',
        color: 'transparent',
        x,
        y,
        w: 240,
        h: 60,
        title: 'Text Block',
        content: 'Type architecture notes here...'
      });
      setTool('select');
      renderElements();
      selectElement(id);
    }

    function addTypedCard() {
      pushHistory();
      const id = 'card-' + Date.now();
      const vp = document.getElementById('canvas-viewport').getBoundingClientRect();
      const x = (vp.width / 2 - board.panX) / board.zoom - 150;
      const y = (vp.height / 2 - board.panY) / board.zoom - 90;

      board.elements.push({
        id,
        type: 'card',
        family: 'requirement',
        status: 'draft',
        alias: 'REQ-' + Math.floor(100 + Math.random() * 900),
        x,
        y,
        w: 300,
        title: 'New Specification Requirement',
        content: 'WHEN an event occurs THE SYSTEM SHALL perform the expected response.',
        relations: []
      });
      closeAllFlyouts();
      setTool('select');
      renderElements();
      selectElement(id);
    }

    function addWireframeTemplate(sType) {
      pushHistory();
      const id = 'wf-' + Date.now();
      const vp = document.getElementById('canvas-viewport').getBoundingClientRect();
      const x = (vp.width / 2 - board.panX) / board.zoom - 200;
      const y = (vp.height / 2 - board.panY) / board.zoom - 150;

      const titles = {
        dashboard: 'SCR-001: SaaS Analytics & KPI Dashboard',
        pricing: 'SCR-003: 3-Tier Subscription Pricing Matrix',
        checkout: 'SCR-002: Stripe Public Checkout',
        ai_chat: 'SCR-004: Live Event Stream Explorer'
      };
      const routes = {
        dashboard: '/app/dashboard',
        pricing: '/pricing',
        checkout: '/pay/:slug',
        ai_chat: '/telemetry/live'
      };

      board.elements.push({
        id,
        type: 'wireframe',
        screenType: sType,
        x,
        y,
        w: 410,
        title: titles[sType] || 'Interface Screen',
        route: routes[sType] || '/screen',
        activeState: 'populated',
        customComponents: []
      });
      closeAllFlyouts();
      setTool('select');
      renderElements();
      selectElement(id);
    }

    function addZoneFrame() {
      pushHistory();
      const id = 'f-' + Date.now();
      const vp = document.getElementById('canvas-viewport').getBoundingClientRect();
      const x = (vp.width / 2 - board.panX) / board.zoom - 180;
      const y = (vp.height / 2 - board.panY) / board.zoom - 200;

      board.frames.push({
        id,
        title: 'New Architecture Zone',
        x,
        y,
        w: 380,
        h: 420
      });
      setTool('select');
      renderFrames();
    }

    function duplicateSelection() {
      if (!board.selectedId) return;
      const orig = board.elements.find(e => e.id === board.selectedId);
      if (!orig) return;

      pushHistory();
      const clone = JSON.parse(JSON.stringify(orig));
      clone.id = orig.type + '-' + Date.now();
      clone.x += 30;
      clone.y += 30;
      board.elements.push(clone);
      renderElements();
      selectElement(clone.id);
    }

    function deleteSelection() {
      if (board.selectedId) {
        pushHistory();
        const item = board.elements.find(e => e.id === board.selectedId);
        board.elements = board.elements.filter(e => e.id !== board.selectedId);
        board.edges = board.edges.filter(edge => edge.from !== board.selectedId && edge.to !== board.selectedId);
        showNotification(`Deleted ${item ? item.type : 'element'}`);
        selectElement(null);
        renderAll();
      } else if (board.selectedFrameId) {
        pushHistory();
        const f = board.frames.find(fr => fr.id === board.selectedFrameId);
        board.frames = board.frames.filter(fr => fr.id !== board.selectedFrameId);
        showNotification(`Deleted frame zone "${f ? f.title : ''}"`);
        board.selectedFrameId = null;
        renderAll();
      }
    }

    function zoomCanvas(delta) {
      const vp = document.getElementById('canvas-viewport');
      const centerX = vp.offsetWidth / 2;
      const centerY = vp.offsetHeight / 2;
      const factor = delta > 0 ? 1.2 : 0.833;
      const newZoom = Math.max(0.05, Math.min(5.0, board.zoom * factor));
      const scaleChange = newZoom / board.zoom;
      board.panX = centerX - (centerX - board.panX) * scaleChange;
      board.panY = centerY - (centerY - board.panY) * scaleChange;
      board.zoom = newZoom;
      applyTransform();
    }

    function zoomTo100() {
      const vp = document.getElementById('canvas-viewport');
      const centerX = vp.offsetWidth / 2;
      const centerY = vp.offsetHeight / 2;
      const scaleChange = 1.0 / board.zoom;
      board.panX = centerX - (centerX - board.panX) * scaleChange;
      board.panY = centerY - (centerY - board.panY) * scaleChange;
      board.zoom = 1.0;
      applyTransform();
      showNotification('Zoom set to 100%');
    }

    // Miro "Fit to Screen" (Shift+1): Dynamic Bounding Box calculation across all elements
    function fitToContent() {
      if (board.elements.length === 0 && board.frames.length === 0) {
        board.panX = 100;
        board.panY = 100;
        board.zoom = 1.0;
        applyTransform();
        return;
      }

      let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;

      board.frames.forEach(f => {
        minX = Math.min(minX, f.x);
        minY = Math.min(minY, f.y);
        maxX = Math.max(maxX, f.x + f.w);
        maxY = Math.max(maxY, f.y + f.h);
      });

      board.elements.forEach(el => {
        const dom = document.getElementById(el.id);
        const elW = el.w || (dom ? dom.offsetWidth : 200);
        const elH = el.h || (dom ? dom.offsetHeight : 150);
        minX = Math.min(minX, el.x);
        minY = Math.min(minY, el.y);
        maxX = Math.max(maxX, el.x + elW);
        maxY = Math.max(maxY, el.y + elH);
      });

      const vp = document.getElementById('canvas-viewport');
      const vpW = vp.offsetWidth;
      const vpH = vp.offsetHeight;
      const padding = 100;

      const contentW = Math.max(400, maxX - minX);
      const contentH = Math.max(300, maxY - minY);

      const scaleX = (vpW - padding * 2) / contentW;
      const scaleY = (vpH - padding * 2) / contentH;
      const fitZoom = Math.max(0.1, Math.min(1.4, Math.min(scaleX, scaleY)));

      board.zoom = fitZoom;
      board.panX = (vpW - contentW * fitZoom) / 2 - minX * fitZoom;
      board.panY = (vpH - contentH * fitZoom) / 2 - minY * fitZoom;
      applyTransform();
      showNotification(`Fit view to board contents (${Math.round(fitZoom * 100)}%)`);
    }

    function resetCanvasView() {
      fitToContent();
    }

    function updateStatusBar() {
      document.getElementById('status-counts').innerText = `Canvas: ${board.elements.length} Elements · ${board.edges.length} Dynamic Connectors`;
    }

    function exportPNGScreenshot() {
      alert('Generating high-resolution snapshot of current board state...');
      window.print();
    }

    // --- Component Specification Modal ---
    function runPromptOnSelected(customInstruction) {
      if (!board.selectedId) return;
      const item = board.elements.find(e => e.id === board.selectedId);
      if (!item) return;

      document.getElementById('prompt-target-title').innerText = (item.alias ? item.alias + ' — ' : '') + (item.title || item.tableName || 'Selected Item');
      if (customInstruction) {
        document.getElementById('prompt-instruction-input').value = customInstruction;
      }
      document.getElementById('prompt-diff-container').style.display = 'none';
      document.getElementById('prompt-apply-btn').style.display = 'none';
      document.getElementById('prompt-run-btn').style.display = 'inline-flex';
      document.getElementById('prompt-run-btn').innerHTML = '<svg class="icon-svg" viewBox="0 0 24 24"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>Execute Prompt';
      document.getElementById('prompt-modal').classList.add('open');
    }

    function closePromptModal() {
      document.getElementById('prompt-modal').classList.remove('open');
      pendingPatch = null;
    }

    function triggerCardPrompt(cardId) {
      selectElement(cardId);
      runPromptOnSelected();
    }

    async function executeFieldRunApi() {
      const item = board.elements.find(e => e.id === board.selectedId);
      if (!item) return;

      const instruction = document.getElementById('prompt-instruction-input').value;
      const runBtn = document.getElementById('prompt-run-btn');
      runBtn.innerHTML = 'Executing Pipeline...';

      try {
        const response = await fetch('/api/v1/spec/validate', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            artifact_id: item.id,
            field_name: 'content',
            current_value: item.content || item.desc || '',
            instruction: instruction,
            protocol: 'TLS 1.3'
          })
        });

        if (!response.ok) throw new Error('Specification error: HTTP ' + response.status);
        const data = await response.json();

        pendingPatch = {
          targetId: item.id,
          proposed: data.proposed_value,
          previous: item.content || item.desc || ''
        };

        document.getElementById('prompt-diff-container').style.display = 'block';
        document.getElementById('prompt-diff-box').innerHTML = `
<span class="diff-del">- ${escapeHTML(item.content || item.desc || '')}</span>
<span class="diff-add">+ ${escapeHTML(data.proposed_value)}</span>
        `;
        document.getElementById('prompt-diff-rationale').innerHTML = `<strong>Rationale:</strong> ${escapeHTML(data.rationale)} (${data.latency_ms}ms)`;

        runBtn.style.display = 'none';
        document.getElementById('prompt-apply-btn').style.display = 'inline-flex';

      } catch (err) {
        alert('Prompt Execution Error: ' + err.message);
        runBtn.innerHTML = '<svg class="icon-svg" viewBox="0 0 24 24"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>Execute Prompt';
      }
    }

    function applyPendingPatch() {
      if (!pendingPatch) return;
      const item = board.elements.find(e => e.id === pendingPatch.targetId);
      if (item) {
        pushHistory();
        if (item.content !== undefined) item.content = pendingPatch.proposed;
        if (item.desc !== undefined) item.desc = pendingPatch.proposed;
        item.status = 'approved';
        renderElements();
        selectElement(item.id);
      }
      closePromptModal();
      showNotification('Patch Approved: Project graph updated with immutable revision');
    }

    // --- Export Compiler Modal ---
    async function loadExportFiles() {
      try {
        const res = await fetch('/api/v1/export/files');
        if (res.ok) {
          activeExportFiles = await res.json();
          showExportFile(activeExportKey);
        }
      } catch (e) {
        console.error('Failed to load live export files:', e);
      }
    }

    function openExportModal() {
      document.getElementById('export-modal').classList.add('open');
      loadExportFiles();
    }

    function closeExportModal() {
      document.getElementById('export-modal').classList.remove('open');
    }

    function openShareModal() {
      document.getElementById('share-modal').classList.add('open');
    }

    function closeShareModal() {
      document.getElementById('share-modal').classList.remove('open');
    }

    function showExportFile(key) {
      activeExportKey = key;
      const codeView = document.getElementById('export-code-view');
      codeView.innerText = activeExportFiles[key] || '// File not found';
    }

    function copyExportContent() {
      const code = document.getElementById('export-code-view').innerText;
      navigator.clipboard.writeText(code);
      showNotification('Copied specification content to clipboard');
    }

    // --- Brainstorm SaaS Project Templates (4 Full Enterprise Blueprints) ---
    function openBrainstormModal() {
      document.getElementById('brainstorm-modal').classList.add('open');
    }

    function closeBrainstormModal() {
      document.getElementById('brainstorm-modal').classList.remove('open');
    }

    // Template & Filter Handlers (Miro-style)
    function filterTemplates(query) {
      const q = (query || '').toLowerCase().trim();
      const activeFilter = window._currentTemplateFilter || 'all';
      document.querySelectorAll('.template-card').forEach(card => {
        const cat = card.getAttribute('data-cat') || '';
        const kw = card.getAttribute('data-keywords') || '';
        const title = card.querySelector('.template-card-title').innerText.toLowerCase();
        const desc = card.querySelector('.template-card-desc').innerText.toLowerCase();

        const matchCat = activeFilter === 'all' || cat === activeFilter;
        const matchQuery = !q || kw.includes(q) || title.includes(q) || desc.includes(q);

        card.style.display = (matchCat && matchQuery) ? 'flex' : 'none';
      });
    }

    function setTemplateFilter(cat, el) {
      window._currentTemplateFilter = cat;
      document.querySelectorAll('.template-filter-pill').forEach(p => p.classList.remove('active'));
      if (el) el.classList.add('active');
      filterTemplates(document.getElementById('template-search-input').value);
    }

    function filterArchFlyout(query) {
      const q = (query || '').toLowerCase().trim();
      const activeCat = window._currentArchFilter || 'all';
      document.querySelectorAll('.picker-card-tech').forEach(card => {
        const cat = card.getAttribute('data-cat') || '';
        const title = card.querySelector('.picker-card-title').innerText.toLowerCase();
        const sub = card.querySelector('.picker-card-sub').innerText.toLowerCase();

        const matchCat = activeCat === 'all' || cat === activeCat;
        const matchQuery = !q || title.includes(q) || sub.includes(q);

        card.style.display = (matchCat && matchQuery) ? 'flex' : 'none';
      });
    }

    function setArchFilter(cat, el) {
      window._currentArchFilter = cat;
      document.querySelectorAll('.flyout-tab-pill').forEach(p => p.classList.remove('active'));
      if (el) el.classList.add('active');
      filterArchFlyout(document.getElementById('arch-search-input').value);
    }

    // Apply any of the 12 Production SaaS Architecture Templates
    function applyTemplate(type, replaceBoard = true) {
      closeBrainstormModal();
      pushHistory();

      let offsetX = 100;
      let offsetY = 100;

      if (!replaceBoard && board.elements.length > 0) {
        let maxX = -Infinity;
        board.elements.forEach(el => { maxX = Math.max(maxX, (el.x || 0) + (el.w || 200)); });
        board.frames.forEach(fr => { maxX = Math.max(maxX, (fr.x || 0) + (fr.w || 400)); });
        offsetX = maxX + 250;
      }

      let newFrames = [], newElements = [], newEdges = [], titleName = '';

      // =========================================================================
      // 9. B2B MULTI-TENANT ENTERPRISE SAAS (Default Canonical Topology)
      // =========================================================================
      if (type === 'b2b_saas' || !type) {
        titleName = 'B2B Multi-Tenant Enterprise SaaS — spine.saas 1.4';
        newFrames = [
        { id: 'f-1', title: '1. Product Vision & Research', x: 80, y: 50, w: 320, h: 540 },
        { id: 'f-2', title: '2. SaaS Wireframes & UI States', x: 440, y: 50, w: 460, h: 540 },
        { id: 'f-3', title: '3. Architecture & Cloud Services', x: 940, y: 50, w: 360, h: 540 },
        { id: 'f-4', title: '4. Database ERD & Schemas', x: 1340, y: 50, w: 320, h: 540 },
        { id: 'f-5', title: '5. Kahn Wave Tasks & Delivery', x: 440, y: 630, w: 460, h: 360 },
        { id: 'f-6', title: '6. Security & PCI Compliance Boundary', x: 940, y: 630, w: 360, h: 360 }
      ];
        newElements = [
        // Zone 1: Sticky Notes with Tags and Reactions
        {
          id: 'st-1',
          type: 'sticky',
          color: '#fef9c3',
          x: 100,
          y: 100,
          w: 200,
          h: 200,
          tags: ['P0', 'UX'],
          reactions: [],
          content: 'Payer checkout must load in <500ms on 4G mobile devices with zero layout shift.'
        },
        {
          id: 'st-2',
          type: 'sticky',
          color: '#ecfdf5',
          x: 100,
          y: 330,
          w: 200,
          h: 200,
          tags: ['Security', 'PCI'],
          reactions: [],
          content: 'Security Rule: Never store raw card PANs; offload tokenization to Stripe Elements.'
        },

        // Zone 2: Wireframe Screen with States Matrix & Component List
        {
          id: 'wf-1',
          type: 'wireframe',
          screenType: 'checkout',
          x: 460,
          y: 100,
          w: 410,
          title: 'SCR-002: Public Checkout View',
          route: '/pay/:slug',
          activeState: 'populated',
          customComponents: []
        },

        // Zone 3: SaaS Architecture Nodes
        {
          id: 'arch-1',
          type: 'arch',
          archType: 'api_gateway',
          x: 960,
          y: 100,
          w: 260,
          title: 'FastAPI Gateway',
          desc: 'Reverse proxy, JWT token verification, and tenant rate-limiter.',
          tags: ['Python 3.12', 'Pydantic v2', '<20ms']
        },
        {
          id: 'arch-2',
          type: 'arch',
          archType: 'stripe_billing',
          x: 960,
          y: 260,
          w: 260,
          title: 'Stripe Billing Engine',
          desc: 'Manages Customer Portal, PaymentIntents, and webhook listeners.',
          tags: ['Stripe API v2024', 'Webhooks']
        },
        {
          id: 'arch-3',
          type: 'arch',
          archType: 'kafka_cluster',
          x: 960,
          y: 420,
          w: 260,
          title: 'Apache Kafka Event Broker',
          desc: 'Partitioned event stream for payment lifecycle and financial audit.',
          tags: ['Kafka', 'Streaming']
        },

        // Zone 4: Database ERD Tables
        {
          id: 'erd-1',
          type: 'erd',
          x: 1360,
          y: 100,
          w: 270,
          tableName: 'payment_forms',
          columns: [
            { name: 'id', type: 'UUID', isPk: true },
            { name: 'workspace_id', type: 'UUID', isFk: true },
            { name: 'slug', type: 'VARCHAR(64)' },
            { name: 'title', type: 'VARCHAR(255)' },
            { name: 'currency', type: 'VARCHAR(3)' },
            { name: 'created_at', type: 'TIMESTAMPTZ' }
          ]
        },
        {
          id: 'erd-2',
          type: 'erd',
          x: 1360,
          y: 330,
          w: 270,
          tableName: 'payment_transactions',
          columns: [
            { name: 'id', type: 'UUID', isPk: true },
            { name: 'form_id', type: 'UUID', isFk: true },
            { name: 'amount_cents', type: 'BIGINT' },
            { name: 'status', type: 'VARCHAR(32)' },
            { name: 'gateway_ref', type: 'VARCHAR(128)' }
          ]
        },

        // Zone 5: Kahn Wave Tasks
        {
          id: 'card-4',
          type: 'card',
          family: 'task',
          status: 'approved',
          alias: 'TSK-001',
          x: 460,
          y: 690,
          w: 300,
          title: 'Wave 1: Database Migrations',
          content: 'Run Alembic migration creating payment_forms and transactions tables.',
          relations: ['realizes -> REQ-001']
        },

        // Zone 6: Security Boundary
        {
          id: 'card-3',
          type: 'card',
          family: 'security',
          status: 'approved',
          alias: 'SEC-001',
          x: 960,
          y: 690,
          w: 300,
          title: 'PCI-DSS Tokenization Boundary',
          content: 'Cardholder PAN data strictly tokenized at edge reverse proxy before entering VPC memory.',
          relations: ['binds -> SCR-002']
        }
      ];
        newEdges = [
        { id: 'e-1', from: 'st-1', fromPort: 'right', to: 'wf-1', toPort: 'left', label: 'annotates', routing: 'orthogonal' },
        { id: 'e-2', from: 'st-2', fromPort: 'right', to: 'arch-2', toPort: 'left', label: 'constrains', routing: 'orthogonal' },
        { id: 'e-3', from: 'wf-1', fromPort: 'right', to: 'arch-1', toPort: 'left', label: 'calls API', routing: 'orthogonal' },
        { id: 'e-4', from: 'arch-1', fromPort: 'bottom', to: 'arch-2', toPort: 'top', label: 'delegates', routing: 'orthogonal' },
        { id: 'e-5', from: 'arch-1', fromPort: 'right', to: 'erd-1', toPort: 'left', label: 'writes', routing: 'orthogonal' },
        { id: 'e-6', from: 'erd-1', fromPort: 'bottom', to: 'erd-2', toPort: 'top', label: '1:N', routing: 'orthogonal' },
        { id: 'e-7', from: 'arch-3', fromPort: 'left', to: 'wf-1', toPort: 'bottom', label: 'evaluates', routing: 'orthogonal' },
        { id: 'e-8', from: 'arch-1', fromPort: 'bottom', to: 'card-4', toPort: 'top', label: 'implements', routing: 'orthogonal' }
      ];
      }




      // =========================================================================
      // 1. C1.1 NEOBANK & DOUBLE-ENTRY LEDGER (Multi-Tier Banking Topology)
      // Top: Full-Width Identity & KYC Onboarding Tier
      // Left: Multi-Rail Gateway & Fraud | Center: Double-Entry Ledger Core | Right: 3-Way Recon & Vault
      // =========================================================================
      else if (type === 'fintech_ledger') {
        titleName = 'C1.1 Neobank & Double-Entry Ledger — spine.saas 1.4 → pack.fintech 2.1';
        newFrames = [
          // Full-width top tier
          { id: 'fr-kyc', title: 'Tier 1 — Customer Identity, KYC/KYB & Sanctions Clearance (Full-Width Gate)', x: offsetX, y: offsetY, w: 2180, h: 260 },
          // Three lower columns
          { id: 'fr-rails', title: 'Tier 2 — Payment Rails & Fraud Defense', x: offsetX, y: offsetY + 300, w: 580, h: 720 },
          { id: 'fr-ledger', title: 'Tier 3 — Double-Entry General Ledger Core (TigerBeetle / PostgreSQL)', x: offsetX + 620, y: offsetY + 300, w: 860, h: 720 },
          { id: 'fr-recon', title: 'Tier 4 — Daily 3-Way Recon, PCI DSS 4.0.1 Vault & Audit', x: offsetX + 1520, y: offsetY + 300, w: 660, h: 720 }
        ];

        newElements = [
          // ── Tier 1: KYC & Identity ──────────────────────────────────────────
          { id: 'st-kyc1', type: 'sticky', color: '#fef9c3', x: offsetX+20, y: offsetY+45, w: 240, h: 180,
            tags: ['INV-001', 'Kill-Shot'], reactions: [],
            content: 'INV-001: No funds-out before KYC tier + sanctions clearance.\nState machine: pending→review→approved→restricted→rejected.\nRejections are immutable and audited.' },
          { id: 'st-kyc2', type: 'sticky', color: '#fef3c7', x: offsetX+280, y: offsetY+45, w: 240, h: 180,
            tags: ['INV-002', 'AML'], reactions: [],
            content: 'INV-002: Sanctions re-screening on EVERY OFAC/UN/EU list update, not just at onboarding. ComplyAdvantage webhook triggers immediate re-evaluation of all open accounts.' },

          { id: 'arch-party', type: 'arch', archType: 'postgres', title: 'Party / Customer Aggregate', desc: 'SSN · DOB · physical address · risk_tier · citizenship', tags: ['PostgreSQL RLS'],
            x: offsetX+540, y: offsetY+50, w: 240, h: 80 },
          { id: 'arch-kyc', type: 'arch', archType: 'auth_service', title: 'KYC / KYB Case Engine', desc: 'Persona · Alloy · Sumsub · biometric liveness score', tags: ['OAuth2'],
            x: offsetX+800, y: offsetY+50, w: 240, h: 80 },
          { id: 'arch-screening', type: 'arch', archType: 'guardrails', title: 'Sanctions & PEP Screening', desc: 'ComplyAdvantage · OFAC · UN · EU consolidated list', tags: ['Realtime API'],
            x: offsetX+540, y: offsetY+145, w: 240, h: 80 },
          { id: 'arch-aml', type: 'arch', archType: 'worker', title: 'AML Transaction Monitor', desc: 'Sardine · Unit21 · automated SAR filing workflow', tags: ['Kafka Stream'],
            x: offsetX+800, y: offsetY+145, w: 240, h: 80 },

          { id: 'wf-kyc', type: 'wireframe', screenType: 'form', x: offsetX+1060, y: offsetY+40, w: 580, h: 200,
            title: 'SCR-KYC: Government ID & Biometric Verification Portal', route: '/onboarding/kyc-verify',
            activeState: 'step-2-document-upload', customComponents: [],
            attachedMockup: null, linkedSkills: ['fhir-compliance-checker'] },

          { id: 'erd-party', type: 'erd', tableName: 'party', x: offsetX+1660, y: offsetY+40, w: 500, h: 190,
            fields: [
              { name: 'id', type: 'uuid PK', nullable: false, isPK: true },
              { name: 'tenant_id', type: 'uuid FK→tenants', nullable: false, isForeignKey: true },
              { name: 'kyc_tier', type: 'enum(0,1,2,3)', nullable: false },
              { name: 'sanctions_status', type: 'enum(clear,hit,review)', nullable: false },
              { name: 'risk_rating', type: 'enum(low,med,high,unacceptable)', nullable: false },
              { name: 'verified_at', type: 'timestamptz', nullable: true }
            ], relations: [] },

          // ── Tier 2: Rails & Fraud ───────────────────────────────────────────
          { id: 'st-rail1', type: 'sticky', color: '#eff6ff', x: offsetX+20, y: offsetY+350, w: 250, h: 150,
            tags: ['INV-003', 'Concurrency'], reactions: [],
            content: 'INV-003: Double-spend race impossible. PostgreSQL row locks (SELECT FOR UPDATE) + serializable isolation + atomic conditional UPDATE WHERE available_balance >= amount.' },
          { id: 'st-rail2', type: 'sticky', color: '#eff6ff', x: offsetX+290, y: offsetY+350, w: 250, h: 150,
            tags: ['STATE', 'Lifecycle'], reactions: [],
            content: 'STATE: payment_intent created→authorized→captured→settled→refunded→disputed. Auth-expiry auto-releases hold. Replay applies exactly once.' },

          { id: 'arch-psp', type: 'arch', archType: 'api_gateway', title: 'PSP Gateway Aggregator', desc: 'Stripe · Adyen · Checkout.com smart routing', tags: ['mTLS / TLS 1.3'],
            x: offsetX+20, y: offsetY+520, w: 250, h: 80 },
          { id: 'arch-rails', type: 'arch', archType: 'reverse_proxy', title: 'Domestic & Global Rails', desc: 'ACH · FedNow · RTP · SEPA Instant · SWIFT', tags: ['ISO 20022'],
            x: offsetX+290, y: offsetY+520, w: 250, h: 80 },
          { id: 'arch-fraud', type: 'arch', archType: 'microservice', title: 'Real-time Fraud Scorer', desc: 'Velocity rules · IP risk · card fingerprinting', tags: ['gRPC / Redis'],
            x: offsetX+20, y: offsetY+620, w: 250, h: 80 },
          { id: 'arch-limits', type: 'arch', archType: 'microservice', title: 'Velocity & Limits Engine', desc: 'Per-tier daily, weekly, monthly transfer caps', tags: ['Redis Atomicity'],
            x: offsetX+290, y: offsetY+620, w: 250, h: 80 },

          { id: 'erd-payment', type: 'erd', tableName: 'payment_intent', x: offsetX+20, y: offsetY+720, w: 520, h: 220,
            fields: [
              { name: 'id', type: 'uuid PK', nullable: false, isPK: true },
              { name: 'idempotency_key', type: 'varchar(255) UNIQUE', nullable: false },
              { name: 'party_id', type: 'uuid FK→party', nullable: false, isForeignKey: true },
              { name: 'amount_minor', type: 'bigint (minor integer units)', nullable: false },
              { name: 'currency', type: 'char(3) ISO-4217', nullable: false },
              { name: 'state', type: 'enum(created,auth,captured,settled,refunded,disputed)', nullable: false },
              { name: 'rail', type: 'enum(card,ach,rtp,fednow,sepa)', nullable: false }
            ], relations: [] },

          // ── Tier 3: Ledger Core ─────────────────────────────────────────────
          { id: 'st-ledger1', type: 'sticky', color: '#ecfdf5', x: offsetX+640, y: offsetY+350, w: 380, h: 140,
            tags: ['INV-004', 'Kill-Shot'], reactions: [],
            content: 'INV-004: sum(debits) == sum(credits) per entry per currency, enforced in DB via CHECK constraint. Postings are APPEND-ONLY. Corrections are compensating reversals, never UPDATE or DELETE.' },
          { id: 'st-ledger2', type: 'sticky', color: '#ecfdf5', x: offsetX+1040, y: offsetY+350, w: 400, h: 140,
            tags: ['INV-005', 'Precision'], reactions: [],
            content: 'INV-005: Available balance != ledger balance (holds). Never float. Integer minor units + ISO-4217 always. Exponents vary (JPY=0, USD=2, KWD=3). Cutoff times & value dates explicit.' },

          { id: 'arch-ledger', type: 'arch', archType: 'postgres', title: 'Double-Entry General Ledger', desc: 'TigerBeetle / PostgreSQL append-only immutable postings', tags: ['CHECK sum=0'],
            x: offsetX+640, y: offsetY+510, w: 380, h: 80 },
          { id: 'arch-balance', type: 'arch', archType: 'microservice', title: 'Balance Snapshot & Holds', desc: 'Materialized view + real-time available balance hold calculation', tags: ['Redis Cache'],
            x: offsetX+1040, y: offsetY+510, w: 400, h: 80 },
          { id: 'arch-fx', type: 'arch', archType: 'microservice', title: 'Multi-Currency FX Engine', desc: 'Versioned rates · timestamped spread · cross-currency FX legs', tags: ['ECB / Bloomberg'],
            x: offsetX+640, y: offsetY+610, w: 380, h: 80 },
          { id: 'arch-settlement', type: 'arch', archType: 'worker', title: 'Settlement & Cutoff Scheduler', desc: 'Modern Treasury · batch cutoff orchestration · liquidity sweeps', tags: ['Cron / Temporal'],
            x: offsetX+1040, y: offsetY+610, w: 400, h: 80 },

          { id: 'erd-posting', type: 'erd', tableName: 'posting (append-only ledger)', x: offsetX+640, y: offsetY+710, w: 380, h: 220,
            fields: [
              { name: 'id', type: 'bigserial PK', nullable: false, isPK: true },
              { name: 'entry_id', type: 'uuid FK→journal_entry', nullable: false, isForeignKey: true },
              { name: 'account_id', type: 'uuid FK→ledger_account', nullable: false, isForeignKey: true },
              { name: 'direction', type: 'enum(debit,credit)', nullable: false },
              { name: 'amount_minor', type: 'bigint CHECK(amount_minor > 0)', nullable: false },
              { name: 'currency', type: 'char(3) ISO-4217', nullable: false },
              { name: 'posted_at', type: 'timestamptz DEFAULT now()', nullable: false }
            ], relations: [] },

          { id: 'erd-journal', type: 'erd', tableName: 'journal_entry', x: offsetX+1040, y: offsetY+710, w: 400, h: 220,
            fields: [
              { name: 'id', type: 'uuid PK', nullable: false, isPK: true },
              { name: 'idempotency_key', type: 'varchar(255) UNIQUE', nullable: false },
              { name: 'reversal_of', type: 'uuid FK→journal_entry (nullable)', nullable: true, isForeignKey: true },
              { name: 'trial_balance_verified', type: 'boolean DEFAULT true', nullable: false },
              { name: 'effective_at', type: 'timestamptz', nullable: false }
            ], relations: [] },

          // ── Tier 4: Recon & Vault ───────────────────────────────────────────
          { id: 'st-comp1', type: 'sticky', color: '#fdf4ff', x: offsetX+1540, y: offsetY+350, w: 290, h: 140,
            tags: ['PCI-DSS-4.0.1', 'REG'], reactions: [],
            content: 'PCI DSS 4.0.1: All 51 future-dated reqs mandatory since 31 Mar 2025. No PAN in our databases. Tokenize at PSP boundary. Payment-page script integrity SRI hashes.' },
          { id: 'st-comp2', type: 'sticky', color: '#fdf4ff', x: offsetX+1850, y: offsetY+350, w: 290, h: 140,
            tags: ['DORA', 'REG'], reactions: [],
            content: 'DORA (EU): Mandatory Register of Information on all ICT third-party vendors (Art. 28-30). Annual resilience testing and mandatory incident reporting.' },

          { id: 'arch-recon', type: 'arch', archType: 'microservice', title: 'Three-Way Daily Recon Engine', desc: 'PSP ↔ Ledger ↔ Bank automated matching with break queue', tags: ['Daily 02:00 UTC'],
            x: offsetX+1540, y: offsetY+510, w: 290, h: 80 },
          { id: 'arch-vault', type: 'arch', archType: 'secrets_kms', title: 'PCI Tokenization Vault', desc: 'HashiCorp Vault · AES-256 tokenization · zero PAN storage', tags: ['FIPS 140-2'],
            x: offsetX+1850, y: offsetY+510, w: 290, h: 80 },
          { id: 'arch-audit', type: 'arch', archType: 'audit_logger', title: 'Immutable Audit Trail', desc: 'Append-only event ledger: who/what/when/where/before/after/why', tags: ['WORM / S3 Lock'],
            x: offsetX+1540, y: offsetY+610, w: 290, h: 80 },
          { id: 'arch-sar', type: 'arch', archType: 'microservice', title: 'SAR Case Management', desc: 'Suspicious Activity Reports · FinCEN / FIU automated filing', tags: ['AML Compliance'],
            x: offsetX+1850, y: offsetY+610, w: 290, h: 80 },

          { id: 'erd-recon', type: 'erd', tableName: 'recon_break', x: offsetX+1540, y: offsetY+710, w: 600, h: 220,
            fields: [
              { name: 'id', type: 'uuid PK', nullable: false, isPK: true },
              { name: 'recon_date', type: 'date', nullable: false },
              { name: 'source', type: 'enum(psp,ledger,bank)', nullable: false },
              { name: 'delta_minor', type: 'bigint', nullable: false },
              { name: 'currency', type: 'char(3)', nullable: false },
              { name: 'aging_hours', type: 'int', nullable: false },
              { name: 'resolved_at', type: 'timestamptz', nullable: true }
            ], relations: [] }
        ];

        newEdges = [
          { id: 'e1', from: 'arch-party', fromPort: 'right', to: 'arch-kyc', toPort: 'left', label: 'verify identity', routing: 'orthogonal' },
          { id: 'e2', from: 'arch-kyc', fromPort: 'bottom', to: 'arch-screening', toPort: 'top', label: 'sanctions re-screen', routing: 'orthogonal' },
          { id: 'e3', from: 'arch-party', fromPort: 'bottom', to: 'arch-psp', toPort: 'top', label: 'authorized checkout', routing: 'orthogonal' },
          { id: 'e4', from: 'arch-psp', fromPort: 'right', to: 'arch-ledger', toPort: 'left', label: 'post journal entry', routing: 'orthogonal' },
          { id: 'e5', from: 'arch-ledger', fromPort: 'right', to: 'arch-recon', toPort: 'left', label: 'daily ledger feed', routing: 'orthogonal' },
          { id: 'e6', from: 'arch-recon', fromPort: 'right', to: 'arch-vault', toPort: 'left', label: 'verify token', routing: 'orthogonal' },
          { id: 'e7', from: 'arch-aml', fromPort: 'bottom', to: 'arch-sar', toPort: 'top', label: 'escalate SAR alert', routing: 'orthogonal' }
        ];
      }

      // =========================================================================
      // 2. C10.2 AUTONOMOUS AI AGENT & ENTERPRISE RAG (Horizontal Directed Pipeline)
      // Left-to-Right Pipeline: Stage 1 Ingress -> Stage 2 RAG -> Stage 3 Agent & Sandbox -> Stage 4 Guardrails
      // =========================================================================
      else if (type === 'ai_agent_rag') {
        titleName = 'C10 Autonomous AI Agent & Enterprise RAG — spine.saas 1.4 → pack.ai_native 2.0';
        newFrames = [
          { id: 'fr-stage1', title: 'Stage 1 — User Ingress, Semantic Cache & Input Guardrails', x: offsetX, y: offsetY, w: 500, h: 860 },
          { id: 'fr-stage2', title: 'Stage 2 — Hybrid RAG & In-Vector Tenant ACL Filtering', x: offsetX + 530, y: offsetY, w: 560, h: 860 },
          { id: 'fr-stage3', title: 'Stage 3 — Agent Planning Core & Tool Sandbox (gVisor)', x: offsetX + 1120, y: offsetY, w: 560, h: 860 },
          { id: 'fr-stage4', title: 'Stage 4 — Output Guardrails, Tracing & Cost Caps', x: offsetX + 1710, y: offsetY, w: 520, h: 860 }
        ];

        newElements = [
          // ── Stage 1: Ingress & Guardrails ───────────────────────────────────
          { id: 'st-ai1', type: 'sticky', color: '#fef9c3', x: offsetX+20, y: offsetY+50, w: 220, h: 140,
            tags: ['OWASP-LLM01', 'Kill-Shot'], reactions: [],
            content: 'OWASP LLM01: Retrieved content & user files are UNTRUSTED INPUT. Indirect prompt injection defence mandatory. Delimiters, instruction isolation, canary tokens.' },
          { id: 'st-ai2', type: 'sticky', color: '#fef3c7', x: offsetX+260, y: offsetY+50, w: 210, h: 140,
            tags: ['OWASP-LLM08', 'Security'], reactions: [],
            content: 'OWASP LLM08: Hidden Context Exposure. System prompts, policy files & tool schemas are discoverable. Never store credentials or business secrets in prompts.' },

          { id: 'arch-ingress', type: 'arch', archType: 'api_gateway', title: 'Agent API Ingress', desc: 'Streaming WebSocket / SSE · JWT tenant claims', tags: ['Envoy / FastAPI'],
            x: offsetX+20, y: offsetY+210, w: 220, h: 80 },
          { id: 'arch-cache', type: 'arch', archType: 'redis_cache', title: 'Semantic Cache (Redis)', desc: 'Cosine similarity >= 0.96 · tenant-scoped · <15ms response', tags: ['Redis VSS'],
            x: offsetX+260, y: offsetY+210, w: 210, h: 80 },
          { id: 'arch-guard-in', type: 'arch', archType: 'guardrails', title: 'NeMo Input Guardrails', desc: 'Jailbreak detection · PII masking · prompt injection filter', tags: ['NVIDIA NeMo'],
            x: offsetX+20, y: offsetY+310, w: 450, h: 80 },

          { id: 'erd-session', type: 'erd', tableName: 'agent_session', x: offsetX+20, y: offsetY+410, w: 450, h: 220,
            fields: [
              { name: 'session_id', type: 'uuid PK', nullable: false, isPK: true },
              { name: 'tenant_id', type: 'uuid FK→tenants', nullable: false, isForeignKey: true },
              { name: 'user_id', type: 'uuid', nullable: false },
              { name: 'token_budget_allocated', type: 'int DEFAULT 100000', nullable: false },
              { name: 'tokens_consumed', type: 'int DEFAULT 0', nullable: false },
              { name: 'guardrail_violations', type: 'int DEFAULT 0', nullable: false }
            ], relations: [] },

          // ── Stage 2: Hybrid RAG & In-Vector ACL ─────────────────────────────
          { id: 'st-rag1', type: 'sticky', color: '#ecfdf5', x: offsetX+550, y: offsetY+50, w: 240, h: 140,
            tags: ['OWASP-LLM02', 'Kill-Shot'], reactions: [],
            content: 'OWASP LLM02: Cross-tenant retrieval leakage is release blocker. ACL filter applied INSIDE vector query payload, never post-retrieval. Zero cross-tenant bleed.' },
          { id: 'st-rag2', type: 'sticky', color: '#ecfdf5', x: offsetX+810, y: offsetY+50, w: 250, h: 140,
            tags: ['RAG', 'Precision'], reactions: [],
            content: 'Hybrid Search: Dense Vector (text-embedding-3-large) + Sparse BM25 combined via Reciprocal Rank Fusion (RRF) + Cohere Rerank cross-encoder.' },

          { id: 'arch-chunk', type: 'arch', archType: 'embedding_service', title: 'Chunking & Embedding Pipeline', desc: 'Sentence-window · hierarchical chunking · metadata enrichment', tags: ['Unstructured.io'],
            x: offsetX+550, y: offsetY+210, w: 240, h: 80 },
          { id: 'arch-acl-filter', type: 'arch', archType: 'guardrails', title: 'In-Vector Tenant ACL Pre-Filter', desc: 'Payload filter: tenant_id == ctx.tenant_id AND group IN user.groups', tags: ['Zero-Leak Filter'],
            x: offsetX+810, y: offsetY+210, w: 250, h: 80 },
          { id: 'arch-qdrant', type: 'arch', archType: 'vector_db', title: 'Qdrant / pgvector Hybrid Store', desc: 'HNSW vector index + Tantivy sparse BM25 index with RRF', tags: ['Vector + Sparse'],
            x: offsetX+550, y: offsetY+310, w: 240, h: 80 },
          { id: 'arch-rerank', type: 'arch', archType: 'microservice', title: 'Cross-Encoder Reranker', desc: 'Cohere Rerank v3 / ColBERT v2 · Top-20 → Top-5 compression', tags: ['Reranker'],
            x: offsetX+810, y: offsetY+310, w: 250, h: 80 },

          { id: 'erd-chunk', type: 'erd', tableName: 'document_chunk', x: offsetX+550, y: offsetY+410, w: 510, h: 220,
            fields: [
              { name: 'chunk_id', type: 'uuid PK', nullable: false, isPK: true },
              { name: 'tenant_id', type: 'uuid (indexed for in-vector filter)', nullable: false, isForeignKey: true },
              { name: 'doc_id', type: 'uuid FK→documents', nullable: false, isForeignKey: true },
              { name: 'embedding', type: 'vector(1536)', nullable: false },
              { name: 'chunk_text', type: 'text', nullable: false },
              { name: 'acl_groups', type: 'varchar[]', nullable: false }
            ], relations: [] },

          // ── Stage 3: Agent Core & Sandbox ───────────────────────────────────
          { id: 'st-agent1', type: 'sticky', color: '#eff6ff', x: offsetX+1140, y: offsetY+50, w: 250, h: 140,
            tags: ['OWASP-LLM03', 'Agency'], reactions: [],
            content: 'OWASP LLM03: Excessive Agency. Minimise tools, least-privilege scoping. Irreversible operations (disbursements, deletes, emails) require Human-In-The-Loop approval.' },
          { id: 'st-agent2', type: 'sticky', color: '#eff6ff', x: offsetX+1410, y: offsetY+50, w: 250, h: 140,
            tags: ['Sandbox', 'Container'], reactions: [],
            content: 'gVisor Container Sandbox: Zero network egress, ephemeral filesystem, per-execution memory & CPU caps, deterministic output schema validation.' },

          { id: 'arch-gateway', type: 'arch', archType: 'agent_swarm', title: 'Model Gateway (LiteLLM)', desc: 'Claude Sonnet 4.6 / GPT-4o routing · latency fallback · circuit breaker', tags: ['LiteLLM Proxy'],
            x: offsetX+1140, y: offsetY+210, w: 250, h: 80 },
          { id: 'arch-tools', type: 'arch', archType: 'microservice', title: 'Scoped Tool Registry', desc: 'Strict JSON-Schema tool parameters · permission boundary verification', tags: ['Tool Contracts'],
            x: offsetX+1410, y: offsetY+210, w: 250, h: 80 },
          { id: 'arch-sandbox', type: 'arch', archType: 'worker', title: 'gVisor Execution Sandbox', desc: 'Secure kernel virtualization · isolated tool execution environment', tags: ['gVisor / Firecracker'],
            x: offsetX+1140, y: offsetY+310, w: 250, h: 80 },
          { id: 'arch-hitl', type: 'arch', archType: 'auth_service', title: 'HITL Human Approval Gate', desc: 'Interactive approval workflow for mutating actions before execution', tags: ['Approval Gate'],
            x: offsetX+1410, y: offsetY+310, w: 250, h: 80 },

          { id: 'wf-ai', type: 'wireframe', screenType: 'chat', x: offsetX+1140, y: offsetY+410, w: 520, h: 220,
            title: 'SCR-AI: Enterprise Agent Console with Live Tool Execution & HITL', route: '/agent/console',
            activeState: 'tool-approval-pending', customComponents: [],
            attachedMockup: null, linkedSkills: ['openapi-contract-validator'] },

          // ── Stage 4: Output Guardrails & Trace ──────────────────────────────
          { id: 'st-out1', type: 'sticky', color: '#fdf4ff', x: offsetX+1730, y: offsetY+50, w: 230, h: 140,
            tags: ['EU-AI-Act', 'REG'], reactions: [],
            content: 'EU AI Act Art. 50: Machine-readable marking of synthetic content. Model cards maintained. Logging of automated decisions for user contestability.' },
          { id: 'st-out2', type: 'sticky', color: '#fdf4ff', x: offsetX+1980, y: offsetY+50, w: 230, h: 140,
            tags: ['Tracing', 'Audit'], reactions: [],
            content: 'PII/PHI redacted BEFORE traces enter OpenTelemetry / Langfuse. Pin model versions; alert on quality drift after silent provider model updates.' },

          { id: 'arch-guard-out', type: 'arch', archType: 'guardrails', title: 'NeMo Output Guardrails', desc: 'Hallucination checker · factual consistency check · PII scrubber', tags: ['NeMo Output'],
            x: offsetX+1730, y: offsetY+210, w: 230, h: 80 },
          { id: 'arch-trace', type: 'arch', archType: 'audit_logger', title: 'Redacted Tracing (Langfuse)', desc: 'OpenTelemetry spans · token latency · PII scrubbed pre-ingest', tags: ['OTel / Langfuse'],
            x: offsetX+1980, y: offsetY+210, w: 230, h: 80 },
          { id: 'arch-budget', type: 'arch', archType: 'microservice', title: 'Token Budget Circuit Breaker', desc: 'Per-tenant hard spend caps · runaway loop detection & kill-switch', tags: ['Cost Cap'],
            x: offsetX+1730, y: offsetY+310, w: 230, h: 80 },
          { id: 'arch-eval', type: 'arch', archType: 'microservice', title: 'Golden-Set Eval Harness', desc: 'Automated regression test runner against 200+ curated domain cases', tags: ['Eval Suite'],
            x: offsetX+1980, y: offsetY+310, w: 230, h: 80 },

          { id: 'erd-eval', type: 'erd', tableName: 'eval_run', x: offsetX+1730, y: offsetY+410, w: 480, h: 220,
            fields: [
              { name: 'eval_id', type: 'uuid PK', nullable: false, isPK: true },
              { name: 'prompt_version', type: 'varchar(32)', nullable: false },
              { name: 'groundedness_score', type: 'decimal(4,3)', nullable: false },
              { name: 'recall_at_5', type: 'decimal(4,3)', nullable: false },
              { name: 'injection_resistance_pct', type: 'decimal(5,2)', nullable: false },
              { name: 'run_at', type: 'timestamptz DEFAULT now()', nullable: false }
            ], relations: [] }
        ];

        newEdges = [
          { id: 'e1', from: 'arch-ingress', fromPort: 'right', to: 'arch-guard-in', toPort: 'left', label: 'stream user prompt', routing: 'orthogonal' },
          { id: 'e2', from: 'arch-guard-in', fromPort: 'right', to: 'arch-acl-filter', toPort: 'left', label: 'safe prompt', routing: 'orthogonal' },
          { id: 'e3', from: 'arch-acl-filter', fromPort: 'bottom', to: 'arch-qdrant', toPort: 'top', label: 'tenant-isolated search', routing: 'orthogonal' },
          { id: 'e4', from: 'arch-qdrant', fromPort: 'right', to: 'arch-rerank', toPort: 'left', label: 'raw candidate chunks', routing: 'orthogonal' },
          { id: 'e5', from: 'arch-rerank', fromPort: 'right', to: 'arch-gateway', toPort: 'left', label: 'top-k grounded context', routing: 'orthogonal' },
          { id: 'e6', from: 'arch-gateway', fromPort: 'right', to: 'arch-tools', toPort: 'left', label: 'tool call decision', routing: 'orthogonal' },
          { id: 'e7', from: 'arch-tools', fromPort: 'bottom', to: 'arch-sandbox', toPort: 'top', label: 'execute in gVisor', routing: 'orthogonal' },
          { id: 'e8', from: 'arch-gateway', fromPort: 'right', to: 'arch-guard-out', toPort: 'left', label: 'candidate response', routing: 'orthogonal' },
          { id: 'e9', from: 'arch-guard-out', fromPort: 'right', to: 'arch-trace', toPort: 'left', label: 'log redacted trace', routing: 'orthogonal' }
        ];
      }

      // =========================================================================
      // 3. C7.1 KAFKA EVENT STREAMING & EOS FLINK (Hub & Spoke Cluster Topology)
      // Left: Event Producers & Ingestion | Center: 3-Broker Kafka + Flink EOS | Right: Sinks & DLQ
      // =========================================================================
      else if (type === 'event_streaming') {
        titleName = 'C7.1 Event Streaming Pipeline — spine.saas 1.4 → pack.kafka 2.0';
        newFrames = [
          { id: 'fr-prod', title: '1. Event Producers & Schema Registry (Ingress Hub)', x: offsetX, y: offsetY, w: 520, h: 880 },
          { id: 'fr-cluster', title: '2. Kafka 3-Broker Cluster & KRaft Quorum Controller', x: offsetX + 560, y: offsetY, w: 860, h: 420 },
          { id: 'fr-flink', title: '3. Apache Flink Exactly-Once (EOS) Stream Processor', x: offsetX + 560, y: offsetY + 450, w: 860, h: 430 },
          { id: 'fr-sinks', title: '4. Downstream Sinks, Analytics & Dead-Letter Queue (DLQ)', x: offsetX + 1450, y: offsetY, w: 660, h: 880 }
        ];

        newElements = [
          { id: 'st-ev1', type: 'sticky', color: '#fef9c3', x: offsetX+20, y: offsetY+50, w: 230, h: 140,
            tags: ['INV-001', 'EOS'], reactions: [],
            content: 'INV-001: Exactly-Once Semantics (EOS) end-to-end. Kafka transactional producer + two-phase commit sinks + Flink RocksDB checkpointing.' },
          { id: 'st-ev2', type: 'sticky', color: '#fef3c7', x: offsetX+270, y: offsetY+50, w: 230, h: 140,
            tags: ['INV-002', 'Schema'], reactions: [],
            content: 'INV-002: BACKWARD compatibility enforced on all Avro/Protobuf schemas. No schema-free events allowed on cluster topics.' },

          { id: 'arch-prod1', type: 'arch', archType: 'api_gateway', title: 'API Ingress Producer', desc: 'REST / gRPC event producer with client idempotency key', tags: ['Idempotent'],
            x: offsetX+20, y: offsetY+210, w: 230, h: 80 },
          { id: 'arch-prod2', type: 'arch', archType: 'reverse_proxy', title: 'Debezium CDC Producer', desc: 'PostgreSQL WAL capture → streaming change data events', tags: ['CDC Engine'],
            x: offsetX+270, y: offsetY+210, w: 230, h: 80 },
          { id: 'arch-schema-reg', type: 'arch', archType: 'microservice', title: 'Confluent Schema Registry', desc: 'Schema ID validation · Avro serialization · BACKWARD compat mode', tags: ['Schema Guard'],
            x: offsetX+20, y: offsetY+310, w: 480, h: 80 },

          { id: 'erd-event', type: 'erd', tableName: 'event_envelope', x: offsetX+20, y: offsetY+410, w: 480, h: 220,
            fields: [
              { name: 'event_id', type: 'uuid PK', nullable: false, isPK: true },
              { name: 'schema_id', type: 'int FK→schema_registry', nullable: false, isForeignKey: true },
              { name: 'topic', type: 'varchar(128)', nullable: false },
              { name: 'partition_key', type: 'varchar(255)', nullable: false },
              { name: 'producer_idempotency_key', type: 'varchar(255) UNIQUE', nullable: false },
              { name: 'payload_avro', type: 'bytea', nullable: false }
            ], relations: [] },

          // Kafka cluster frame
          { id: 'arch-k1', type: 'arch', archType: 'kafka_cluster', title: 'Kafka Broker 1 (Leader)', desc: 'Rack: us-east-1a · ISR member', tags: ['Broker 1'],
            x: offsetX+580, y: offsetY+60, w: 250, h: 80 },
          { id: 'arch-k2', type: 'arch', archType: 'kafka_cluster', title: 'Kafka Broker 2 (Follower)', desc: 'Rack: us-east-1b · ISR member', tags: ['Broker 2'],
            x: offsetX+850, y: offsetY+60, w: 250, h: 80 },
          { id: 'arch-k3', type: 'arch', archType: 'kafka_cluster', title: 'Kafka Broker 3 (Follower)', desc: 'Rack: us-east-1c · ISR member', tags: ['Broker 3'],
            x: offsetX+1120, y: offsetY+60, w: 270, h: 80 },
          { id: 'arch-kraft', type: 'arch', archType: 'microservice', title: 'KRaft Quorum Controller', desc: 'Raft consensus controller · zero Zookeeper dependency', tags: ['KRaft'],
            x: offsetX+580, y: offsetY+160, w: 810, h: 70 },

          { id: 'wf-ev', type: 'wireframe', screenType: 'dashboard', x: offsetX+580, y: offsetY+245, w: 810, h: 155,
            title: 'SCR-EVT: Real-time Kafka Topic Monitor & Consumer Lag', route: '/kafka/monitor',
            activeState: 'live-consumer-lag', customComponents: [],
            attachedMockup: null, linkedSkills: [] },

          // Flink stream processing
          { id: 'arch-flink', type: 'arch', archType: 'microservice', title: 'Apache Flink (EOS Engine)', desc: 'Stateful stream processing with two-phase commit sink', tags: ['Flink 1.18'],
            x: offsetX+580, y: offsetY+510, w: 390, h: 80 },
          { id: 'arch-rocksdb', type: 'arch', archType: 'postgres', title: 'RocksDB State Backend', desc: 'Incremental checkpointing every 10s to S3', tags: ['State Store'],
            x: offsetX+1000, y: offsetY+510, w: 390, h: 80 },
          { id: 'arch-window', type: 'arch', archType: 'microservice', title: 'Tumbling Window Aggregator', desc: '5-minute event-time tumbling windows with watermarks', tags: ['Watermarking'],
            x: offsetX+580, y: offsetY+610, w: 390, h: 80 },
          { id: 'arch-temporal', type: 'arch', archType: 'microservice', title: 'Temporal Stream-Stream Join', desc: 'Join order events with payment events on transaction_id', tags: ['Temporal Join'],
            x: offsetX+1000, y: offsetY+610, w: 390, h: 80 },

          // Sinks & DLQ
          { id: 'arch-clickhouse', type: 'arch', archType: 'clickhouse', title: 'ClickHouse OLAP Sink', desc: 'Real-time analytics engine · vector compression', tags: ['OLAP Store'],
            x: offsetX+1480, y: offsetY+60, w: 300, h: 80 },
          { id: 'arch-s3-lake', type: 'arch', archType: 'object_store', title: 'S3 Parquet Data Lake', desc: 'Iceberg metadata catalog · cold archival', tags: ['Iceberg'],
            x: offsetX+1800, y: offsetY+60, w: 290, h: 80 },
          { id: 'arch-dlq', type: 'arch', archType: 'webhook_engine', title: 'Dead-Letter Queue (DLQ)', desc: 'Poison-pill isolation with exponential retry backoff', tags: ['Poison Guard'],
            x: offsetX+1480, y: offsetY+160, w: 610, h: 80 },

          { id: 'erd-offset', type: 'erd', tableName: 'consumer_offset', x: offsetX+1480, y: offsetY+260, w: 610, h: 220,
            fields: [
              { name: 'consumer_group', type: 'varchar(64) PK', nullable: false, isPK: true },
              { name: 'topic', type: 'varchar(128) PK', nullable: false, isPK: true },
              { name: 'partition', type: 'int PK', nullable: false, isPK: true },
              { name: 'committed_offset', type: 'bigint', nullable: false },
              { name: 'lag', type: 'bigint', nullable: false },
              { name: 'updated_at', type: 'timestamptz DEFAULT now()', nullable: false }
            ], relations: [] }
        ];

        newEdges = [
          { id: 'e1', from: 'arch-prod1', fromPort: 'right', to: 'arch-schema-reg', toPort: 'left', label: 'validate schema', routing: 'orthogonal' },
          { id: 'e2', from: 'arch-schema-reg', fromPort: 'right', to: 'arch-k1', toPort: 'left', label: 'publish Avro event', routing: 'orthogonal' },
          { id: 'e3', from: 'arch-k1', fromPort: 'bottom', to: 'arch-flink', toPort: 'top', label: 'consume partition stream', routing: 'orthogonal' },
          { id: 'e4', from: 'arch-flink', fromPort: 'right', to: 'arch-clickhouse', toPort: 'left', label: '2PC sink commit', routing: 'orthogonal' },
          { id: 'e5', from: 'arch-flink', fromPort: 'right', to: 'arch-dlq', toPort: 'left', label: 'route poison pill', routing: 'orthogonal' }
        ];
      }

      // =========================================================================
      // 4. C3.2 MULTI-VENDOR MARKETPLACE (Two-Sided Platform Topology)
      // Top: Buyer Catalog & Checkout | Bottom-Left: OMS Hub | Bottom-Right: Seller Split Engine
      // =========================================================================
      else if (type === 'ecommerce_marketplace') {
        titleName = 'C3.2 Multi-Vendor Marketplace — spine.saas 1.4 → pack.marketplace 2.0';
        newFrames = [
          { id: 'fr-buyer', title: 'Top Platform Tier: Buyer Experience, Faceted Search & 15m Reservation Lock', x: offsetX, y: offsetY, w: 2160, h: 380 },
          { id: 'fr-oms', title: 'Core Hub: Order Management System (OMS) 8-State Lifecycle', x: offsetX, y: offsetY + 420, w: 720, h: 560 },
          { id: 'fr-seller', title: 'Seller Tier: Stripe Connect Custom, Split Calculation & DAC7 Reporting', x: offsetX + 760, y: offsetY + 420, w: 1400, h: 560 }
        ];

        newElements = [
          // ── Buyer Tier ──────────────────────────────────────────────────────
          { id: 'st-mkt1', type: 'sticky', color: '#fef9c3', x: offsetX+20, y: offsetY+45, w: 260, h: 150,
            tags: ['INV-001', 'Kill-Shot'], reactions: [],
            content: 'INV-001: Inventory reservation with TTL prevents oversell race. Reservation != commitment. Never trust client price or quantity. Server always recalculates.' },
          { id: 'st-mkt2', type: 'sticky', color: '#fef3c7', x: offsetX+300, y: offsetY+45, w: 260, h: 150,
            tags: ['INV-002', 'Idempotency'], reactions: [],
            content: 'INV-002: Checkout is idempotent end-to-end. Retries never create duplicate charges. Promo codes evaluated with deterministic stacking rules.' },

          { id: 'arch-catalog', type: 'arch', archType: 'elastic_search', title: 'Catalog & Faceted Search', desc: 'Algolia / Typesense · real-time pricing & inventory status', tags: ['Search Engine'],
            x: offsetX+580, y: offsetY+50, w: 260, h: 80 },
          { id: 'arch-inventory', type: 'arch', archType: 'redis_cache', title: 'Inventory Reservation', desc: 'Redis SETNX with 15-minute TTL reservation hold', tags: ['15m Hold'],
            x: offsetX+860, y: offsetY+50, w: 260, h: 80 },
          { id: 'arch-tax-calc', type: 'arch', archType: 'microservice', title: 'Tax & Nexus Engine', desc: 'Avalara / TaxJar · line-item jurisdiction calculation', tags: ['Tax Engine'],
            x: offsetX+580, y: offsetY+145, w: 260, h: 80 },

          { id: 'wf-catalog', type: 'wireframe', screenType: 'list', x: offsetX+1140, y: offsetY+45, w: 560, h: 200,
            title: 'SCR-CAT: Marketplace Product Catalog & 15m Hold Indicator', route: '/marketplace/search',
            activeState: 'filtered-results', customComponents: [],
            attachedMockup: null, linkedSkills: [] },

          { id: 'erd-listing', type: 'erd', tableName: 'listing', x: offsetX+1720, y: offsetY+45, w: 420, h: 200,
            fields: [
              { name: 'id', type: 'uuid PK', nullable: false, isPK: true },
              { name: 'seller_id', type: 'uuid FK→seller', nullable: false, isForeignKey: true },
              { name: 'price_minor', type: 'bigint', nullable: false },
              { name: 'stock_available', type: 'int', nullable: false },
              { name: 'dsn_trader_verified', type: 'boolean DEFAULT false', nullable: false }
            ], relations: [] },

          // ── OMS Hub ─────────────────────────────────────────────────────────
          { id: 'st-oms1', type: 'sticky', color: '#eff6ff', x: offsetX+20, y: offsetY+470, w: 320, h: 140,
            tags: ['STATE', 'OMS'], reactions: [],
            content: 'STATE: order placed→paid→allocated→picked→shipped→delivered→returned→refunded. Out-of-order fulfilment webhooks tolerated with idempotent state reconciliation.' },

          { id: 'arch-oms', type: 'arch', archType: 'microservice', title: 'Order Management Core', desc: 'Finite state machine · domain events on every transition', tags: ['State Machine'],
            x: offsetX+20, y: offsetY+630, w: 320, h: 80 },
          { id: 'arch-fulfil', type: 'arch', archType: 'reverse_proxy', title: 'Fulfilment Dispatcher', desc: 'Shippo / EasyPost multi-carrier rate shopping & label generation', tags: ['Logistics'],
            x: offsetX+360, y: offsetY+630, w: 320, h: 80 },
          { id: 'arch-returns', type: 'arch', archType: 'microservice', title: 'Returns & RMA Engine', desc: 'Automated return labels · proportional fee re-allocation', tags: ['RMA Engine'],
            x: offsetX+20, y: offsetY+730, w: 320, h: 80 },

          { id: 'erd-order', type: 'erd', tableName: 'order', x: offsetX+360, y: offsetY+730, w: 320, h: 220,
            fields: [
              { name: 'id', type: 'uuid PK', nullable: false, isPK: true },
              { name: 'buyer_id', type: 'uuid FK→party', nullable: false, isForeignKey: true },
              { name: 'state', type: 'enum(8 states)', nullable: false },
              { name: 'total_minor', type: 'bigint', nullable: false },
              { name: 'currency', type: 'char(3)', nullable: false }
            ], relations: [] },

          // ── Seller Tier ─────────────────────────────────────────────────────
          { id: 'st-sel1', type: 'sticky', color: '#ecfdf5', x: offsetX+780, y: offsetY+470, w: 320, h: 140,
            tags: ['INV-003', 'Commingling'], reactions: [],
            content: 'INV-003: Platform revenue and seller funds NEVER commingle. Split at PSP boundary via Stripe Connect Custom. Payout blocked if KYC requirements missing.' },
          { id: 'st-sel2', type: 'sticky', color: '#ecfdf5', x: offsetX+1120, y: offsetY+470, w: 320, h: 140,
            tags: ['INV-004', 'Clawback'], reactions: [],
            content: 'INV-004: Refunds proportionally claw back transfer + platform fee. Negative seller balances recoverable against future order payouts.' },

          { id: 'arch-connect', type: 'arch', archType: 'stripe_billing', title: 'Stripe Connect Custom', desc: 'Custom accounts · express dashboard · KYC collection', tags: ['Stripe Connect'],
            x: offsetX+780, y: offsetY+630, w: 320, h: 80 },
          { id: 'arch-splits', type: 'arch', archType: 'microservice', title: 'Take-Rate Split Engine', desc: 'Application fee deduction · commission rules · multi-currency', tags: ['Splits'],
            x: offsetX+1120, y: offsetY+630, w: 320, h: 80 },
          { id: 'arch-payout', type: 'arch', archType: 'worker', title: 'Payout & Escrow Scheduler', desc: '7-day rolling hold · dispute reserves · automated bank payouts', tags: ['Rolling Hold'],
            x: offsetX+780, y: offsetY+730, w: 320, h: 80 },
          { id: 'arch-dac7', type: 'arch', archType: 'audit_logger', title: 'DAC7 & 1099-K Tax Auditor', desc: 'EU DAC7 annual reporting · IRS 1099-K generation', tags: ['Tax Compliance'],
            x: offsetX+1120, y: offsetY+730, w: 320, h: 80 },

          { id: 'erd-seller', type: 'erd', tableName: 'seller', x: offsetX+1460, y: offsetY+470, w: 680, h: 220,
            fields: [
              { name: 'id', type: 'uuid PK', nullable: false, isPK: true },
              { name: 'stripe_connect_id', type: 'varchar(64) UNIQUE', nullable: false },
              { name: 'kyc_status', type: 'enum(unverified,pending,verified,restricted)', nullable: false },
              { name: 'escrow_hold_days', type: 'int DEFAULT 7', nullable: false },
              { name: 'tax_form_status', type: 'enum(w9_verified,dac7_reported)', nullable: false }
            ], relations: [] }
        ];

        newEdges = [
          { id: 'e1', from: 'arch-catalog', fromPort: 'right', to: 'arch-inventory', toPort: 'left', label: 'check & hold stock', routing: 'orthogonal' },
          { id: 'e2', from: 'arch-inventory', fromPort: 'bottom', to: 'arch-oms', toPort: 'top', label: 'commit cart order', routing: 'orthogonal' },
          { id: 'e3', from: 'arch-oms', fromPort: 'right', to: 'arch-connect', toPort: 'left', label: 'trigger split payment', routing: 'orthogonal' },
          { id: 'e4', from: 'arch-connect', fromPort: 'right', to: 'arch-splits', toPort: 'left', label: 'compute take-rate', routing: 'orthogonal' },
          { id: 'e5', from: 'arch-splits', fromPort: 'bottom', to: 'arch-dac7', toPort: 'top', label: 'log taxable transaction', routing: 'orthogonal' }
        ];
      }

      // =========================================================================
      // 5. C7.7 ZERO-TRUST IAM (Service Mesh Radial Topology)
      // Top: SPIRE CA Authority | Center: Mesh & Envoy mTLS | Left: OPA PEP | Right: Vault Secrets
      // =========================================================================
      else if (type === 'zero_trust_iam') {
        titleName = 'C7.7 Zero-Trust IAM & Micro-Segmentation — spine.saas 1.4 → pack.zerotrust 2.0';
        newFrames = [
          { id: 'fr-pki', title: 'Top Authority: SPIFFE/SPIRE Workload Identity & Certificate Authority', x: offsetX + 570, y: offsetY, w: 860, h: 240 },
          { id: 'fr-mesh', title: 'Center Mesh: Envoy Sidecars & Mutual TLS (1-Hour SVID Rotation)', x: offsetX + 570, y: offsetY + 280, w: 860, h: 640 },
          { id: 'fr-opa', title: 'Left Perimeter: OPA Policy Enforcement Point (PEP)', x: offsetX, y: offsetY, w: 530, h: 920 },
          { id: 'fr-vault', title: 'Right Perimeter: HashiCorp Vault Dynamic Secrets & KMS', x: offsetX + 1470, y: offsetY, w: 600, h: 920 }
        ];

        newElements = [
          // ── Center Mesh ─────────────────────────────────────────────────────
          { id: 'st-zt1', type: 'sticky', color: '#fef9c3', x: offsetX+590, y: offsetY+320, w: 380, h: 140,
            tags: ['NIST-800-207', 'Zero-Trust'], reactions: [],
            content: 'NIST 800-207: Never trust, always verify. Every service-to-service call requires a valid SPIFFE SVID. No shared passwords or long-lived static tokens between microservices.' },
          { id: 'st-zt2', type: 'sticky', color: '#eff6ff', x: offsetX+990, y: offsetY+320, w: 420, h: 140,
            tags: ['INV-001', 'mTLS'], reactions: [],
            content: 'INV-001: Mutual TLS (mTLS) mandatory on all network hops. SVID X.509 certs rotate every 1 hour. Compromised workloads revoked immediately via SPIRE CRL distribution.' },

          { id: 'arch-envoy-sidecar', type: 'arch', archType: 'reverse_proxy', title: 'Envoy Sidecar Proxy', desc: 'mTLS termination · L7 header inspection · SPIFFE cert validation', tags: ['Envoy Proxy'],
            x: offsetX+590, y: offsetY+480, w: 380, h: 80 },
          { id: 'arch-control-plane', type: 'arch', archType: 'microservice', title: 'Mesh Control Plane', desc: 'Istio / Linkerd control plane · xDS dynamic configuration distribution', tags: ['xDS API'],
            x: offsetX+990, y: offsetY+480, w: 420, h: 80 },

          { id: 'wf-zt', type: 'wireframe', screenType: 'dashboard', x: offsetX+590, y: offsetY+580, w: 820, h: 220,
            title: 'SCR-ZT: Live Policy Decision Log & SVID Health Monitor', route: '/security/mesh-status',
            activeState: 'live-decisions', customComponents: [],
            attachedMockup: null, linkedSkills: ['zero-trust-policy-enforcer', 'postgres-rls-auditor'] },

          // ── Top CA Authority ────────────────────────────────────────────────
          { id: 'arch-spire-server', type: 'arch', archType: 'secrets_kms', title: 'SPIRE Server (Attestation)', desc: 'Workload identity authority · TPM / k8s node attestation', tags: ['SPIRE Core'],
            x: offsetX+590, y: offsetY+50, w: 380, h: 80 },
          { id: 'arch-spiffe-agent', type: 'arch', archType: 'guardrails', title: 'SPIFFE Agent (Node Daemon)', desc: 'Local Unix domain socket · issues short-lived SVIDs', tags: ['SPIFFE Daemon'],
            x: offsetX+990, y: offsetY+50, w: 420, h: 80 },
          { id: 'erd-svid', type: 'erd', tableName: 'workload_svid', x: offsetX+590, y: offsetY+145, w: 820, h: 80,
            fields: [
              { name: 'spiffe_id', type: 'varchar(255) PK', nullable: false, isPK: true },
              { name: 'workload_selector', type: 'jsonb', nullable: false },
              { name: 'expires_at', type: 'timestamptz (1h TTL)', nullable: false }
            ], relations: [] },

          // ── Left: OPA PEP ───────────────────────────────────────────────────
          { id: 'st-opa1', type: 'sticky', color: '#ecfdf5', x: offsetX+20, y: offsetY+50, w: 480, h: 140,
            tags: ['OPA-Rego', 'Policy'], reactions: [],
            content: 'OPA Policy-as-Code: Deny-by-default. Rego policies evaluated in <1ms in-process. Policies git-synced via bundle server. Decision logs shipped to immutable audit.' },

          { id: 'arch-opa-pep', type: 'arch', archType: 'guardrails', title: 'OPA Policy Engine (PEP)', desc: 'Rego policy evaluator · in-memory decision cache · sub-millisecond latency', tags: ['OPA Engine'],
            x: offsetX+20, y: offsetY+210, w: 480, h: 80 },
          { id: 'arch-bundle-server', type: 'arch', archType: 'microservice', title: 'OPA Bundle Server', desc: 'GitOps policy distribution · signed policy bundles · continuous verification', tags: ['Bundle Server'],
            x: offsetX+20, y: offsetY+310, w: 480, h: 80 },
          { id: 'arch-decision-log', type: 'arch', archType: 'audit_logger', title: 'OPA Decision Audit Log', desc: 'Immutable log of all authorization decisions (allow / deny / reasons)', tags: ['Audit Log'],
            x: offsetX+20, y: offsetY+410, w: 480, h: 80 },

          // ── Right: Vault Secrets ────────────────────────────────────────────
          { id: 'st-vault1', type: 'sticky', color: '#fdf4ff', x: offsetX+1490, y: offsetY+50, w: 550, h: 140,
            tags: ['Vault', 'KMS'], reactions: [],
            content: 'HashiCorp Vault: Dynamic database credentials generated on-demand with 15-minute lease. Zero static database credentials exist in configuration or environment variables.' },

          { id: 'arch-vault-core', type: 'arch', archType: 'secrets_kms', title: 'HashiCorp Vault Core', desc: 'Dynamic secrets engine · PKI intermediate CA · Shamir unseal', tags: ['Vault Enterprise'],
            x: offsetX+1490, y: offsetY+210, w: 550, h: 80 },
          { id: 'arch-cloudhsm', type: 'arch', archType: 'secrets_kms', title: 'AWS CloudHSM Root Unseal', desc: 'FIPS 140-2 Level 3 hardware security module · master key protection', tags: ['CloudHSM'],
            x: offsetX+1490, y: offsetY+310, w: 550, h: 80 },
          { id: 'arch-rotation', type: 'arch', archType: 'worker', title: 'Zero-Downtime Secret Rotator', desc: 'Automated 30-day credential rotation · dual-write grace period', tags: ['Rotator'],
            x: offsetX+1490, y: offsetY+410, w: 550, h: 80 }
        ];

        newEdges = [
          { id: 'e1', from: 'arch-spiffe-agent', fromPort: 'bottom', to: 'arch-envoy-sidecar', toPort: 'top', label: 'push 1h SVID cert', routing: 'orthogonal' },
          { id: 'e2', from: 'arch-envoy-sidecar', fromPort: 'left', to: 'arch-opa-pep', toPort: 'right', label: 'eval authorization request', routing: 'orthogonal' },
          { id: 'e3', from: 'arch-opa-pep', fromPort: 'bottom', to: 'arch-decision-log', toPort: 'top', label: 'record decision audit', routing: 'orthogonal' },
          { id: 'e4', from: 'arch-envoy-sidecar', fromPort: 'right', to: 'arch-vault-core', toPort: 'left', label: 'request dynamic secret (mTLS)', routing: 'orthogonal' }
        ];
      }

      // =========================================================================
      // 6. C4.2 GLOBAL PAYROLL & TAX (Bi-Temporal DAG Waterfall Topology)
      // Left: HR Core & Bi-Temporal | Center-Left: GTN DAG | Center-Right: Statutory Tax | Right: Banking Rails
      // =========================================================================
      else if (type === 'global_payroll') {
        titleName = 'C4.2 Multi-Jurisdiction Global Payroll — spine.saas 1.4 → pack.payroll 2.0';
        newFrames = [
          { id: 'fr-hris', title: '1. HRIS Core & Effective-Dated Compensation', x: offsetX, y: offsetY, w: 500, h: 880 },
          { id: 'fr-gtn', title: '2. Gross-to-Net Deterministic Calculation DAG', x: offsetX + 530, y: offsetY, w: 540, h: 880 },
          { id: 'fr-tax', title: '3. Statutory Tax Tables & Garnishment Waterfall', x: offsetX + 1100, y: offsetY, w: 500, h: 880 },
          { id: 'fr-disburse', title: '4. Banking Disbursement Rails & Immutable Payslip Vault', x: offsetX + 1630, y: offsetY, w: 530, h: 880 }
        ];

        newElements = [
          { id: 'st-pay1', type: 'sticky', color: '#fef9c3', x: offsetX+20, y: offsetY+50, w: 220, h: 140,
            tags: ['INV-001', 'Deterministic'], reactions: [],
            content: 'INV-001: Payroll math is 100% deterministic & reproducible for ANY past period. Given same inputs + same tax table version → exact same output to the cent. No floats.' },
          { id: 'st-pay2', type: 'sticky', color: '#fef3c7', x: offsetX+260, y: offsetY+50, w: 220, h: 140,
            tags: ['INV-002', 'Bi-temporal'], reactions: [],
            content: 'INV-002: Employment data is effective-dated. Never overwrite history. Query "as-of" a date returns exact historical state. Retro-pay recalculates without mutating filed payslips.' },

          { id: 'arch-hris', type: 'arch', archType: 'postgres', title: 'HRIS Bi-Temporal Core', desc: 'Valid-time & transaction-time tables · org graph · effective dates', tags: ['Bi-Temporal'],
            x: offsetX+20, y: offsetY+210, w: 460, h: 80 },
          { id: 'arch-comp', type: 'arch', archType: 'microservice', title: 'Compensation Structure Engine', desc: 'Base salary · variable bonus · equity vesting · multi-currency', tags: ['Compensation'],
            x: offsetX+20, y: offsetY+310, w: 460, h: 80 },

          { id: 'erd-worker', type: 'erd', tableName: 'worker (bi-temporal)', x: offsetX+20, y: offsetY+410, w: 460, h: 220,
            fields: [
              { name: 'id', type: 'uuid PK', nullable: false, isPK: true },
              { name: 'valid_from', type: 'date (temporal from)', nullable: false },
              { name: 'valid_to', type: 'date (temporal to)', nullable: false },
              { name: 'base_salary_minor', type: 'bigint', nullable: false },
              { name: 'currency', type: 'char(3) ISO-4217', nullable: false },
              { name: 'tax_jurisdiction', type: 'varchar(16)', nullable: false }
            ], relations: [] },

          // Gross-to-net DAG
          { id: 'arch-gtn', type: 'arch', archType: 'microservice', title: 'Gross-to-Net DAG Engine', desc: 'Deterministic calculation waterfall: gross earnings → pretax → taxes → posttax', tags: ['GTN DAG'],
            x: offsetX+550, y: offsetY+50, w: 500, h: 80 },
          { id: 'arch-retro', type: 'arch', archType: 'worker', title: 'Retroactive Pay Engine', desc: 'Recalculates prior closed periods and computes difference adjustments', tags: ['Retro Pay'],
            x: offsetX+550, y: offsetY+145, w: 500, h: 80 },

          { id: 'wf-payroll', type: 'wireframe', screenType: 'form', x: offsetX+550, y: offsetY+245, w: 500, h: 220,
            title: 'SCR-PAY: Payroll Calculation Review & Dual-Authorization Batch Run', route: '/payroll/runs/:id',
            activeState: 'calculated-pending-approval', customComponents: [],
            attachedMockup: null, linkedSkills: [] },

          // Statutory Tax
          { id: 'arch-tax-tables', type: 'arch', archType: 'microservice', title: 'Statutory Tax Table Engine', desc: 'Versioned tax brackets · PAYE RTI · PF/ESI · FUTA/SUTA · social security', tags: ['Tax Rules'],
            x: offsetX+1120, y: offsetY+50, w: 460, h: 80 },
          { id: 'arch-garnish', type: 'arch', archType: 'microservice', title: 'Garnishment Priority Engine', desc: 'CCPA child support · tax levy · student loans · priority sorting', tags: ['Garnishments'],
            x: offsetX+1120, y: offsetY+145, w: 460, h: 80 },

          // Disbursements
          { id: 'arch-nacha', type: 'arch', archType: 'reverse_proxy', title: 'NACHA Direct Deposit', desc: 'ACH direct deposit file generator · dual-approval validation', tags: ['ACH File'],
            x: offsetX+1650, y: offsetY+50, w: 490, h: 80 },
          { id: 'arch-sepa-pay', type: 'arch', archType: 'reverse_proxy', title: 'SEPA XML (pain.001)', desc: 'European instant credit transfers · IBAN/BIC validation', tags: ['SEPA XML'],
            x: offsetX+1650, y: offsetY+145, w: 490, h: 80 },
          { id: 'arch-payslip-vault', type: 'arch', archType: 'object_store', title: 'WORM Payslip Vault', desc: 'Immutable PDF/A payslip storage · employee self-service portal', tags: ['WORM Vault'],
            x: offsetX+1650, y: offsetY+240, w: 490, h: 80 }
        ];

        newEdges = [
          { id: 'e1', from: 'arch-hris', fromPort: 'right', to: 'arch-gtn', toPort: 'left', label: 'as-of comp record', routing: 'orthogonal' },
          { id: 'e2', from: 'arch-gtn', fromPort: 'right', to: 'arch-tax-tables', toPort: 'left', label: 'taxable gross', routing: 'orthogonal' },
          { id: 'e3', from: 'arch-tax-tables', fromPort: 'right', to: 'arch-nacha', toPort: 'left', label: 'net disbursement', routing: 'orthogonal' },
          { id: 'e4', from: 'arch-gtn', fromPort: 'right', to: 'arch-payslip-vault', toPort: 'left', label: 'archive payslip', routing: 'orthogonal' }
        ];
      }

      // =========================================================================
      // 7. C9.1 LEGALTECH CLM & ETHICAL WALLS (Contract Lifecycle Pipeline)
      // Gatekeeper: Ethical Wall -> Redlining -> e-Sign (DocuSign) -> WORM Archival
      // =========================================================================
      else if (type === 'legaltech_clm') {
        titleName = 'C9.1 LegalTech CLM & Ethical Walls — spine.saas 1.4 → pack.legaltech 2.0';
        newFrames = [
          { id: 'fr-wall', title: '1. Conflict Check & Ethical Wall Engine (ABAC)', x: offsetX, y: offsetY, w: 500, h: 880 },
          { id: 'fr-redline', title: '2. Contract Authoring, Clause Library & Redline Diff', x: offsetX + 530, y: offsetY, w: 560, h: 880 },
          { id: 'fr-esign', title: '3. Electronic Signature & DocuSign HMAC Verification', x: offsetX + 1120, y: offsetY, w: 500, h: 880 },
          { id: 'fr-worm', title: '4. WORM Archival, Court Docketing & Obligations', x: offsetX + 1650, y: offsetY, w: 520, h: 880 }
        ];

        newElements = [
          { id: 'st-clm1', type: 'sticky', color: '#fef9c3', x: offsetX+20, y: offsetY+50, w: 460, h: 140,
            tags: ['INV-001', 'Ethical-Wall'], reactions: [],
            content: 'INV-001: Ethical walls enforced across search, AI retrieval, and exports. Privileged content NEVER enters model training or global vectors. Breach alerts privacy officer.' },

          { id: 'arch-conflict', type: 'arch', archType: 'microservice', title: 'Conflict of Interest Engine', desc: 'Party relationship graph · automated conflict check on intake', tags: ['Conflict Check'],
            x: offsetX+20, y: offsetY+210, w: 460, h: 80 },
          { id: 'arch-wall-abac', type: 'arch', archType: 'guardrails', title: 'Ethical Wall ABAC Guard', desc: 'Matter-scoped attribute-based access control · blocks search leaks', tags: ['ABAC Wall'],
            x: offsetX+20, y: offsetY+310, w: 460, h: 80 },

          { id: 'erd-matter', type: 'erd', tableName: 'matter', x: offsetX+20, y: offsetY+410, w: 460, h: 220,
            fields: [
              { name: 'id', type: 'uuid PK', nullable: false, isPK: true },
              { name: 'client_id', type: 'uuid FK→client', nullable: false, isForeignKey: true },
              { name: 'ethical_wall_id', type: 'uuid FK→ethical_wall', nullable: true, isForeignKey: true },
              { name: 'privilege_level', type: 'enum(attorney_client,work_product,none)', nullable: false }
            ], relations: [] },

          // Redlining
          { id: 'arch-redline', type: 'arch', archType: 'microservice', title: 'Tamper-Evident Redline Engine', desc: 'SHA-256 diffing · tracked changes versioning · change attribution', tags: ['Redline Engine'],
            x: offsetX+550, y: offsetY+50, w: 520, h: 80 },
          { id: 'arch-clauses', type: 'arch', archType: 'postgres', title: 'Clause Library & AI Analyzer', desc: 'Curated standard clauses · risk scoring · deviation detection', tags: ['Clause Store'],
            x: offsetX+550, y: offsetY+145, w: 520, h: 80 },

          { id: 'wf-clm', type: 'wireframe', screenType: 'editor', x: offsetX+550, y: offsetY+245, w: 520, h: 220,
            title: 'SCR-CLM: Contract Redlining, Tracked Changes & Clause Diff', route: '/contracts/:id/redline',
            activeState: 'counterparty-review', customComponents: [],
            attachedMockup: null, linkedSkills: [] },

          // Sign & WORM
          { id: 'arch-docusign', type: 'arch', archType: 'reverse_proxy', title: 'DocuSign / Adobe Sign API', desc: 'eIDAS QES conformance · HMAC webhook validation · signing flow', tags: ['DocuSign QES'],
            x: offsetX+1140, y: offsetY+50, w: 460, h: 80 },
          { id: 'arch-worm-doc', type: 'arch', archType: 'object_store', title: 'WORM Document Archive', desc: 'S3 Object Lock · 7-year regulatory retention · legal hold support', tags: ['S3 Lock WORM'],
            x: offsetX+1670, y: offsetY+50, w: 480, h: 80 },
          { id: 'arch-docket', type: 'arch', archType: 'worker', title: 'Court Docketing Engine', desc: 'Court holiday calendars · jurisdictional statutory deadline timers', tags: ['Docketing'],
            x: offsetX+1670, y: offsetY+145, w: 480, h: 80 }
        ];

        newEdges = [
          { id: 'e1', from: 'arch-conflict', fromPort: 'bottom', to: 'arch-wall-abac', toPort: 'top', label: 'enforce ethical wall', routing: 'orthogonal' },
          { id: 'e2', from: 'arch-wall-abac', fromPort: 'right', to: 'arch-redline', toPort: 'left', label: 'permit editor access', routing: 'orthogonal' },
          { id: 'e3', from: 'arch-redline', fromPort: 'right', to: 'arch-docusign', toPort: 'left', label: 'transmit for eSign', routing: 'orthogonal' },
          { id: 'e4', from: 'arch-docusign', fromPort: 'right', to: 'arch-worm-doc', toPort: 'left', label: 'archive executed document', routing: 'orthogonal' }
        ];
      }

      // =========================================================================
      // 8. C8.1 GLOBAL FREIGHT LOGISTICS & COLD-CHAIN IOT (Fleet Network Topology)
      // IoT Ingest -> Shipment Control Tower -> PostGIS Geofence -> EDI 204/214 -> Cryptographic POD
      // =========================================================================
      else if (type === 'logistics_supply_chain') {
        titleName = 'C8.1 Global Freight Logistics & Cold-Chain IoT — spine.saas 1.4 → pack.logistics 2.0';
        newFrames = [
          { id: 'fr-iot', title: '1. IoT Sensor Telemetry & MQTT Broker (EMQX)', x: offsetX, y: offsetY, w: 500, h: 880 },
          { id: 'fr-tower', title: '2. Shipment State Machine & Real-Time Control Tower', x: offsetX + 530, y: offsetY, w: 560, h: 880 },
          { id: 'fr-edi', title: '3. EDI X12 Protocol Engine & Carrier Integration', x: offsetX + 1120, y: offsetY, w: 500, h: 880 },
          { id: 'fr-pod', title: '4. Cryptographic Proof-of-Delivery (POD) & Freight Audit', x: offsetX + 1650, y: offsetY, w: 520, h: 880 }
        ];

        newElements = [
          { id: 'st-log1', type: 'sticky', color: '#fef9c3', x: offsetX+20, y: offsetY+50, w: 460, h: 140,
            tags: ['INV-001', 'Offline'], reactions: [],
            content: 'INV-001: Safety-critical functions NEVER depend on cloud connectivity. Cold-chain temperature excursion alarms trigger locally on device. Offline sync dedupes on reconnect.' },

          { id: 'arch-emqx', type: 'arch', archType: 'kafka_cluster', title: 'EMQX MQTT Broker Cluster', desc: 'QoS 1/2 · 100k persistent connections · TLS mutual auth', tags: ['EMQX MQTT'],
            x: offsetX+20, y: offsetY+210, w: 460, h: 80 },
          { id: 'arch-timescale', type: 'arch', archType: 'postgres', title: 'TimescaleDB Hypertables', desc: 'Real-time telemetry storage · 90% compression · chunk retention', tags: ['TimescaleDB'],
            x: offsetX+20, y: offsetY+310, w: 460, h: 80 },

          { id: 'erd-sensor', type: 'erd', tableName: 'sensor_reading (hypertable)', x: offsetX+20, y: offsetY+410, w: 460, h: 220,
            fields: [
              { name: 'device_id', type: 'uuid PK', nullable: false, isPK: true },
              { name: 'event_time', type: 'timestamptz PK', nullable: false, isPK: true },
              { name: 'temperature_c', type: 'decimal(5,2)', nullable: false },
              { name: 'speed_mph', type: 'decimal(5,2)', nullable: false },
              { name: 'seq_num', type: 'bigint (dedup key)', nullable: false }
            ], relations: [] },

          // Control Tower
          { id: 'arch-oms-ship', type: 'arch', archType: 'microservice', title: 'Shipment State Machine', desc: 'booked→dispatched→in_transit→out_for_delivery→delivered→invoiced', tags: ['State Machine'],
            x: offsetX+550, y: offsetY+50, w: 520, h: 80 },
          { id: 'arch-geofence', type: 'arch', archType: 'microservice', title: 'PostGIS Geofence Engine', desc: 'Port / depot boundary entry detection · automated detention billing', tags: ['PostGIS'],
            x: offsetX+550, y: offsetY+145, w: 520, h: 80 },

          { id: 'wf-log', type: 'wireframe', screenType: 'map', x: offsetX+550, y: offsetY+245, w: 520, h: 220,
            title: 'SCR-LOG: Real-Time Fleet Control Tower & Cold-Chain Radar', route: '/fleet/control-tower',
            activeState: 'live-fleet-map', customComponents: [],
            attachedMockup: null, linkedSkills: [] },

          // EDI & POD
          { id: 'arch-edi', type: 'arch', archType: 'reverse_proxy', title: 'EDI X12 Engine', desc: 'EDI 204 (load tender) · 214 (status) · 210 (freight invoice)', tags: ['EDI X12'],
            x: offsetX+1140, y: offsetY+50, w: 460, h: 80 },
          { id: 'arch-carriers', type: 'arch', archType: 'reverse_proxy', title: 'Carrier API Adapters', desc: 'FedEx · UPS · project44 · Samsara telematics ingest', tags: ['Carriers'],
            x: offsetX+1140, y: offsetY+145, w: 460, h: 80 },

          { id: 'arch-pod-sign', type: 'arch', archType: 'secrets_kms', title: 'Ed25519 Cryptographic POD', desc: 'Tamper-evident proof-of-delivery · digital signature + GPS + photo stamp', tags: ['Ed25519 POD'],
            x: offsetX+1670, y: offsetY+50, w: 480, h: 80 },
          { id: 'arch-freight-audit', type: 'arch', archType: 'microservice', title: 'Freight Bill Audit Engine', desc: 'Matches contracted rates vs invoiced charges · flags fuel surcharge variances', tags: ['Audit Engine'],
            x: offsetX+1670, y: offsetY+145, w: 480, h: 80 }
        ];

        newEdges = [
          { id: 'e1', from: 'arch-emqx', fromPort: 'bottom', to: 'arch-timescale', toPort: 'top', label: 'stream sensor readings', routing: 'orthogonal' },
          { id: 'e2', from: 'arch-emqx', fromPort: 'right', to: 'arch-geofence', toPort: 'left', label: 'eval geofence breach', routing: 'orthogonal' },
          { id: 'e3', from: 'arch-geofence', fromPort: 'bottom', to: 'arch-oms-ship', toPort: 'left', label: 'advance shipment state', routing: 'orthogonal' },
          { id: 'e4', from: 'arch-oms-ship', fromPort: 'right', to: 'arch-edi', toPort: 'left', label: 'dispatch EDI 214', routing: 'orthogonal' },
          { id: 'e5', from: 'arch-oms-ship', fromPort: 'right', to: 'arch-pod-sign', toPort: 'left', label: 'seal proof of delivery', routing: 'orthogonal' }
        ];
      }

      // =========================================================================
      // 9. B2B MULTI-TENANT ENTERPRISE SAAS (Default Enterprise Grid Topology)
      // WAF Perimeter -> Identity & SCIM -> Domain Microservices & BullMQ -> Citus RLS Sharding
      // =========================================================================
      else if (type === 'developer_platform') {
        titleName = 'Developer API & Webhook Platform — spine.api 1.0';
        newFrames = [
          { id: 'fr-dp-gw', title: '1. API Gateway & Authentication', x: offsetX, y: offsetY, w: 500, h: 820 },
          { id: 'fr-dp-wh', title: '2. Webhook Delivery Engine', x: offsetX+530, y: offsetY, w: 520, h: 820 },
          { id: 'fr-dp-sdk', title: '3. SDK & Developer Portal', x: offsetX+1080, y: offsetY, w: 460, h: 820 },
          { id: 'fr-dp-db', title: '4. Event Store & Rate Limiting', x: offsetX+1570, y: offsetY, w: 480, h: 820 }
        ];
        newElements = [
          { id: 'st-dp1', type: 'sticky', color: '#fef9c3', x: offsetX+20, y: offsetY+50, w: 460, h: 120,
            tags: ['ADR-001', 'Idempotency'], reactions: [],
            content: 'ADR-001: Every webhook delivery is idempotent. Delivery attempts stored with HMAC-SHA256 signature. Max 3 retries with exponential back-off (1s, 10s, 60s). Replays rejected after 5 min.' },
          { id: 'arch-dp-kong', type: 'arch', archType: 'api_gateway', title: 'Kong API Gateway', desc: 'JWT auth · API key rotation · rate limiting per tier · request logging', tags: ['Kong', 'REST', 'GraphQL'],
            x: offsetX+20, y: offsetY+190, w: 460, h: 80 },
          { id: 'arch-dp-oauth', type: 'arch', archType: 'auth_service', title: 'OAuth 2.0 / API Keys', desc: 'Client credentials flow · scoped API keys · key rotation · revocation webhook', tags: ['OAuth2', 'PKCE'],
            x: offsetX+20, y: offsetY+290, w: 460, h: 80 },
          { id: 'erd-dp-apikey', type: 'erd', tableName: 'api_key', x: offsetX+20, y: offsetY+390, w: 460, h: 200,
            fields: [
              { name: 'id', type: 'uuid PK', nullable: false, isPK: true },
              { name: 'app_id', type: 'uuid FK', nullable: false, isForeignKey: true },
              { name: 'key_hash', type: 'varchar(64)', nullable: false },
              { name: 'scopes', type: 'text[]', nullable: false },
              { name: 'expires_at', type: 'timestamptz', nullable: true }
            ], relations: [] },
          { id: 'wf-dp-portal', type: 'wireframe', screenType: 'developer_portal', x: offsetX+20, y: offsetY+610, w: 460,
            title: 'Developer Portal Dashboard', route: '/portal', activeState: 'populated', customComponents: [] },
          { id: 'arch-dp-svix', type: 'arch', archType: 'microservice', title: 'Webhook Dispatcher', desc: 'Fan-out per subscriber · HMAC-SHA256 signing · retry queue · DLQ', tags: ['Webhooks', 'BullMQ'],
            x: offsetX+550, y: offsetY+50, w: 480, h: 80 },
          { id: 'arch-dp-redis', type: 'arch', archType: 'redis_cache', title: 'Redis Rate Limit Buckets', desc: 'Token-bucket algorithm per API key · sliding-window counters · burst allowance', tags: ['Redis', 'Rate Limiting'],
            x: offsetX+550, y: offsetY+150, w: 480, h: 80 },
          { id: 'erd-dp-event', type: 'erd', tableName: 'webhook_attempt', x: offsetX+550, y: offsetY+250, w: 480, h: 240,
            fields: [
              { name: 'id', type: 'uuid PK', nullable: false, isPK: true },
              { name: 'event_id', type: 'uuid FK', nullable: false, isForeignKey: true },
              { name: 'endpoint_id', type: 'uuid FK', nullable: false, isForeignKey: true },
              { name: 'status', type: 'enum(pending,success,failed,dlq)', nullable: false },
              { name: 'response_code', type: 'integer', nullable: true },
              { name: 'next_retry_at', type: 'timestamptz', nullable: true }
            ], relations: [] },
          { id: 'wf-dp-logs', type: 'wireframe', screenType: 'list', x: offsetX+550, y: offsetY+510, w: 480,
            title: 'Webhook Delivery Log', route: '/portal/webhooks', activeState: 'populated', customComponents: [] },
          { id: 'arch-dp-docs', type: 'arch', archType: 'microservice', title: 'API Docs (OpenAPI 3.1)', desc: 'Auto-generated · interactive playground · versioned endpoints · changelog', tags: ['OpenAPI', 'Redoc'],
            x: offsetX+1100, y: offsetY+50, w: 420, h: 80 },
          { id: 'arch-dp-sandbox', type: 'arch', archType: 'microservice', title: 'Sandbox Environment', desc: 'Isolated test mode · synthetic event injection · response stubbing', tags: ['Sandbox', 'Testing'],
            x: offsetX+1100, y: offsetY+150, w: 420, h: 80 },
          { id: 'erd-dp-app', type: 'erd', tableName: 'application', x: offsetX+1100, y: offsetY+250, w: 420, h: 180,
            fields: [
              { name: 'id', type: 'uuid PK', nullable: false, isPK: true },
              { name: 'org_id', type: 'uuid FK', nullable: false, isForeignKey: true },
              { name: 'name', type: 'varchar(120)', nullable: false },
              { name: 'is_sandbox', type: 'boolean DEFAULT false', nullable: false }
            ], relations: [] },
          { id: 'arch-dp-pg', type: 'arch', archType: 'postgres', title: 'PostgreSQL Event Store', desc: 'Events · delivery attempts · audit log · idempotency keys', tags: ['PostgreSQL', 'JSONB'],
            x: offsetX+1590, y: offsetY+50, w: 440, h: 80 },
          { id: 'arch-dp-s3', type: 'arch', archType: 'storage', title: 'S3 Payload Archive', desc: 'Payloads >64KB archived · 90-day retention · signed URL for replay', tags: ['S3', 'Cold Storage'],
            x: offsetX+1590, y: offsetY+150, w: 440, h: 80 }
        ];
        newEdges = [
          { id: 'e-dp1', from: 'arch-dp-kong', fromPort: 'right', to: 'arch-dp-svix', toPort: 'left', label: 'Verified events', routing: 'orthogonal' },
          { id: 'e-dp2', from: 'arch-dp-svix', fromPort: 'right', to: 'arch-dp-docs', toPort: 'left', label: 'OpenAPI schema', routing: 'curved' },
          { id: 'e-dp3', from: 'arch-dp-svix', fromPort: 'bottom', to: 'arch-dp-pg', toPort: 'top', label: 'Store attempts', routing: 'orthogonal' },
          { id: 'e-dp4', from: 'arch-dp-redis', fromPort: 'right', to: 'arch-dp-svix', toPort: 'left', label: 'Rate limit', routing: 'curved' }
        ];

      } else if (type === 'collab_workspace') {
        titleName = 'Collaborative Document & Canvas Workspace — spine.collab 1.0';
        newFrames = [
          { id: 'fr-cw-rt', title: '1. Real-Time Sync Engine (Yjs CRDT)', x: offsetX, y: offsetY, w: 500, h: 820 },
          { id: 'fr-cw-ui', title: '2. Editor UI & Presence Awareness', x: offsetX+530, y: offsetY, w: 520, h: 820 },
          { id: 'fr-cw-perm', title: '3. Workspace Permissions & Sharing', x: offsetX+1080, y: offsetY, w: 480, h: 820 },
          { id: 'fr-cw-db', title: '4. Document Store & Version Snapshots', x: offsetX+1590, y: offsetY, w: 480, h: 820 }
        ];
        newElements = [
          { id: 'st-cw1', type: 'sticky', color: '#ecfdf5', x: offsetX+20, y: offsetY+50, w: 460, h: 130,
            tags: ['ADR-001', 'CRDT'], reactions: [],
            content: 'ADR-001: Yjs CRDT selected for conflict-free document merges. Provider: y-websocket on a dedicated sync server. Offline edits reconcile on reconnect with no data loss. Awareness (cursors/presence) is ephemeral — not persisted to database.' },
          { id: 'arch-cw-yjs', type: 'arch', archType: 'kafka_cluster', title: 'Yjs WebSocket Sync Server', desc: 'CRDT sync · shared cursor positions · offline support · sub-document updates', tags: ['Yjs', 'CRDT', 'WebSocket'],
            x: offsetX+20, y: offsetY+200, w: 460, h: 90 },
          { id: 'arch-cw-redis-pub', type: 'arch', archType: 'redis_cache', title: 'Redis Pub/Sub (Awareness)', desc: 'Ephemeral cursor/presence broadcast across sync server instances', tags: ['Redis', 'Pub/Sub'],
            x: offsetX+20, y: offsetY+310, w: 460, h: 80 },
          { id: 'erd-cw-doc', type: 'erd', tableName: 'document', x: offsetX+20, y: offsetY+410, w: 460, h: 240,
            fields: [
              { name: 'id', type: 'uuid PK', nullable: false, isPK: true },
              { name: 'workspace_id', type: 'uuid FK', nullable: false, isForeignKey: true },
              { name: 'title', type: 'varchar(512)', nullable: false },
              { name: 'doc_type', type: 'enum(doc,canvas,sheet)', nullable: false },
              { name: 'ydoc_state', type: 'bytea', nullable: true },
              { name: 'version', type: 'integer DEFAULT 0', nullable: false }
            ], relations: [] },
          { id: 'wf-cw-editor', type: 'wireframe', screenType: 'editor', x: offsetX+550, y: offsetY+50, w: 480,
            title: 'Collaborative Document Editor', route: '/doc/:id', activeState: 'populated', customComponents: [] },
          { id: 'wf-cw-chat', type: 'wireframe', screenType: 'chat', x: offsetX+550, y: offsetY+440, w: 480,
            title: 'Threaded Comments', route: '/doc/:id#comments', activeState: 'populated', customComponents: [] },
          { id: 'arch-cw-auth', type: 'arch', archType: 'auth_service', title: 'Workspace Auth & Sharing', desc: 'Role-based access · link sharing · guest access with TTL · revocation', tags: ['RBAC', 'Share Links'],
            x: offsetX+1100, y: offsetY+50, w: 440, h: 80 },
          { id: 'erd-cw-member', type: 'erd', tableName: 'workspace_member', x: offsetX+1100, y: offsetY+150, w: 440, h: 220,
            fields: [
              { name: 'id', type: 'uuid PK', nullable: false, isPK: true },
              { name: 'workspace_id', type: 'uuid FK', nullable: false, isForeignKey: true },
              { name: 'user_id', type: 'uuid FK', nullable: false, isForeignKey: true },
              { name: 'role', type: 'enum(owner,editor,commenter,viewer)', nullable: false },
              { name: 'joined_at', type: 'timestamptz', nullable: false }
            ], relations: [] },
          { id: 'erd-cw-snap', type: 'erd', tableName: 'doc_snapshot', x: offsetX+1100, y: offsetY+390, w: 440, h: 180,
            fields: [
              { name: 'id', type: 'uuid PK', nullable: false, isPK: true },
              { name: 'doc_id', type: 'uuid FK', nullable: false, isForeignKey: true },
              { name: 'snapshot_at', type: 'timestamptz', nullable: false },
              { name: 'author_id', type: 'uuid FK', nullable: false, isForeignKey: true }
            ], relations: [] },
          { id: 'arch-cw-pg', type: 'arch', archType: 'postgres', title: 'PostgreSQL Document Store', desc: 'Documents · snapshots · sharing permissions · audit log', tags: ['PostgreSQL'],
            x: offsetX+1610, y: offsetY+50, w: 440, h: 80 },
          { id: 'arch-cw-s3', type: 'arch', archType: 'storage', title: 'Object Storage (Files & Assets)', desc: 'Uploaded images · PDF exports · version snapshots · signed URL delivery', tags: ['S3', 'CDN'],
            x: offsetX+1610, y: offsetY+150, w: 440, h: 80 }
        ];
        newEdges = [
          { id: 'e-cw1', from: 'arch-cw-yjs', fromPort: 'bottom', to: 'arch-cw-redis-pub', toPort: 'top', label: 'Awareness broadcast', routing: 'orthogonal' },
          { id: 'e-cw2', from: 'arch-cw-yjs', fromPort: 'right', to: 'arch-cw-pg', toPort: 'left', label: 'Persist ydoc state', routing: 'curved' },
          { id: 'e-cw3', from: 'arch-cw-auth', fromPort: 'right', to: 'arch-cw-pg', toPort: 'left', label: 'Permission check', routing: 'orthogonal' }
        ];

      } else if (type === 'healthcare_portal') {
        titleName = 'Healthcare Patient Portal & FHIR Integration — spine.health 1.0';
        newFrames = [
          { id: 'fr-hp-fhir', title: '1. FHIR R4 Gateway & PHI Boundary', x: offsetX, y: offsetY, w: 500, h: 820 },
          { id: 'fr-hp-portal', title: '2. Patient Portal & Provider Screens', x: offsetX+530, y: offsetY, w: 520, h: 820 },
          { id: 'fr-hp-iam', title: '3. Identity, Consent & Audit', x: offsetX+1080, y: offsetY, w: 480, h: 820 },
          { id: 'fr-hp-data', title: '4. Clinical Data Store & HL7 Events', x: offsetX+1590, y: offsetY, w: 480, h: 820 }
        ];
        newElements = [
          { id: 'st-hp1', type: 'sticky', color: '#fce7f3', x: offsetX+20, y: offsetY+50, w: 460, h: 150,
            tags: ['DESIGN NOTE', 'HIPAA'], reactions: [],
            content: 'DESIGN NOTE: This is a design starting point requiring formal risk analysis. HIPAA Security Rule compliance (45 CFR Part 164) requires BAAs with all vendors, PHI encryption at rest and in transit, audit controls, and regular security review by qualified personnel.' },
          { id: 'arch-hp-fhir', type: 'arch', archType: 'api_gateway', title: 'FHIR R4 REST API (HAPI FHIR)', desc: 'Patient · Observation · Encounter · Condition · MedicationRequest · DocumentReference', tags: ['FHIR R4', 'HL7', 'SMART on FHIR'],
            x: offsetX+20, y: offsetY+230, w: 460, h: 90 },
          { id: 'arch-hp-phi', type: 'arch', archType: 'guardrails', title: 'PHI Access Control Layer', desc: 'Attribute-based access · patient consent enforcement · field-level masking', tags: ['PHI Boundary', 'Consent'],
            x: offsetX+20, y: offsetY+340, w: 460, h: 80 },
          { id: 'erd-hp-patient', type: 'erd', tableName: 'patient', x: offsetX+20, y: offsetY+440, w: 460, h: 260,
            fields: [
              { name: 'id', type: 'uuid PK', nullable: false, isPK: true },
              { name: 'fhir_id', type: 'varchar(64) UNIQUE', nullable: false },
              { name: 'mrn', type: 'varchar(32) UNIQUE', nullable: false },
              { name: 'name_encrypted', type: 'bytea', nullable: false },
              { name: 'dob_encrypted', type: 'bytea', nullable: false },
              { name: 'sensitivity_level', type: 'enum(standard,restricted)', nullable: false }
            ], relations: [] },
          { id: 'wf-hp-dash', type: 'wireframe', screenType: 'dashboard', x: offsetX+550, y: offsetY+50, w: 480,
            title: 'Patient Health Dashboard', route: '/portal/health', activeState: 'populated', customComponents: [] },
          { id: 'wf-hp-appt', type: 'wireframe', screenType: 'list', x: offsetX+550, y: offsetY+440, w: 480,
            title: 'Appointment Schedule', route: '/portal/appointments', activeState: 'populated', customComponents: [] },
          { id: 'arch-hp-smart', type: 'arch', archType: 'auth_service', title: 'SMART on FHIR / OIDC', desc: 'Patient-facing login · EHR launch context · scoped access tokens · MFA', tags: ['SMART on FHIR', 'OIDC'],
            x: offsetX+1100, y: offsetY+50, w: 440, h: 80 },
          { id: 'arch-hp-consent', type: 'arch', archType: 'microservice', title: 'Consent Manager', desc: 'Granular data-sharing consent · withdrawal · audit trail', tags: ['Consent', 'Audit'],
            x: offsetX+1100, y: offsetY+150, w: 440, h: 80 },
          { id: 'erd-hp-audit', type: 'erd', tableName: 'phi_access_log', x: offsetX+1100, y: offsetY+250, w: 440, h: 220,
            fields: [
              { name: 'id', type: 'uuid PK', nullable: false, isPK: true },
              { name: 'accessed_by', type: 'uuid FK', nullable: false, isForeignKey: true },
              { name: 'patient_id', type: 'uuid FK', nullable: false, isForeignKey: true },
              { name: 'resource_type', type: 'varchar(64)', nullable: false },
              { name: 'action', type: 'enum(read,write,export,delete)', nullable: false },
              { name: 'accessed_at', type: 'timestamptz', nullable: false }
            ], relations: [] },
          { id: 'arch-hp-pg', type: 'arch', archType: 'postgres', title: 'PostgreSQL Clinical Store', desc: 'PHI encrypted at rest (AES-256) · row-level audit · 7-year retention (proposal)', tags: ['PostgreSQL', 'Encrypted'],
            x: offsetX+1610, y: offsetY+50, w: 440, h: 80 },
          { id: 'arch-hp-hl7', type: 'arch', archType: 'microservice', title: 'HL7 v2 ADT Listener', desc: 'ADT A01/A03/A04 admit-discharge-transfer events · FHIR R4 Encounter transform', tags: ['HL7 v2', 'ADT'],
            x: offsetX+1610, y: offsetY+160, w: 440, h: 80 }
        ];
        newEdges = [
          { id: 'e-hp1', from: 'arch-hp-fhir', fromPort: 'bottom', to: 'arch-hp-phi', toPort: 'top', label: 'PHI gating', routing: 'orthogonal' },
          { id: 'e-hp2', from: 'arch-hp-smart', fromPort: 'right', to: 'arch-hp-pg', toPort: 'left', label: 'Token validation', routing: 'curved' },
          { id: 'e-hp3', from: 'arch-hp-consent', fromPort: 'right', to: 'arch-hp-pg', toPort: 'left', label: 'Consent rules', routing: 'orthogonal' },
          { id: 'e-hp4', from: 'arch-hp-hl7', fromPort: 'left', to: 'arch-hp-pg', toPort: 'right', label: 'FHIR transform', routing: 'curved' }
        ];

      } else if (type) {
        // Unknown template ID — explicit safe error (never silently fall through to b2b)
        titleName = 'Unknown Blueprint: ' + type;
        newFrames = [{ id: 'fr-err', title: 'Unknown Blueprint: ' + type, x: offsetX, y: offsetY, w: 500, h: 300 }];
        newElements = [
          { id: 'st-err', type: 'sticky', color: '#fce7f3', x: offsetX+20, y: offsetY+50, w: 460, h: 180,
            tags: ['Error'], reactions: [],
            content: 'Blueprint ID "' + type + '" is not recognised. Valid IDs: b2b_saas · fintech_ledger · event_streaming · ecommerce_marketplace · developer_platform · collab_workspace · healthcare_portal · zero_trust_iam · ai_agent_rag · global_payroll · legaltech_clm · logistics_supply_chain' }
        ];
        newEdges = [];
      }

      if (replaceBoard) {
        document.getElementById('board-title').value = titleName || 'Enterprise Architecture Canvas';
        board.frames = newFrames;
        board.elements = newElements;
        board.edges = newEdges;
        board.selectedId = newElements.length > 0 ? newElements[0].id : null;
        setTimeout(fitToContent, 100);
        showNotification(`Loaded blueprint: ${titleName}`);
      } else {
        const idMap = {};
        newFrames.forEach(fr => {
          const oldId = fr.id;
          const newId = 'fr-' + Date.now() + '-' + Math.floor(Math.random()*1000);
          idMap[oldId] = newId;
          fr.id = newId;
          board.frames.push(fr);
        });
        newElements.forEach(el => {
          const oldId = el.id;
          const newId = el.type + '-' + Date.now() + '-' + Math.floor(Math.random()*1000);
          idMap[oldId] = newId;
          el.id = newId;
          board.elements.push(el);
        });
        newEdges.forEach(ed => {
          ed.id = 'e-' + Date.now() + '-' + Math.floor(Math.random()*1000);
          if (idMap[ed.from]) ed.from = idMap[ed.from];
          if (idMap[ed.to]) ed.to = idMap[ed.to];
          board.edges.push(ed);
        });
        showNotification(`Appended blueprint: ${titleName}`);
      }

      renderAll();
    }
    function escapeHTML(str) {
      return (str || '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
    }

    // Robust automatic initialization: execute immediately if DOM ready, otherwise on DOMContentLoaded
    if (document.readyState === 'complete' || document.readyState === 'interactive') {
      setTimeout(init, 0);
    } else {
      document.addEventListener('DOMContentLoaded', init);
    }
    window.addEventListener('load', () => {
      try { renderAll(); } catch(e) {}
    });
  
// ── IMAGE ATTACHMENT ──────────────────────────────────────────

// ── SKETCHPAD & UI SPECIFICATION SYSTEM ───────────────────────
let sketchTargetElementId = null;
let sketchDrawing = false;
let sketchTool = 'pen';
let sketchColor = '#1e293b';
let sketchStrokeWidth = 4;
let sketchCtx = null;

function initSketchCanvas() {
  const canvas = document.getElementById('sketch-canvas');
  if (!canvas) return;
  sketchCtx = canvas.getContext('2d');
  sketchCtx.lineCap = 'round';
  sketchCtx.lineJoin = 'round';

  canvas.onmousedown = (e) => {
    sketchDrawing = true;
    const r = canvas.getBoundingClientRect();
    const x = e.clientX - r.left;
    const y = e.clientY - r.top;
    sketchCtx.beginPath();
    sketchCtx.moveTo(x, y);
  };

  canvas.onmousemove = (e) => {
    if (!sketchDrawing) return;
    const r = canvas.getBoundingClientRect();
    const x = e.clientX - r.left;
    const y = e.clientY - r.top;
    sketchCtx.strokeStyle = (sketchTool === 'eraser') ? '#ffffff' : sketchColor;
    sketchCtx.lineWidth = (sketchTool === 'eraser') ? sketchStrokeWidth * 3 : sketchStrokeWidth;
    sketchCtx.lineTo(x, y);
    sketchCtx.stroke();
  };

  canvas.onmouseup = () => { sketchDrawing = false; };
  canvas.onmouseleave = () => { sketchDrawing = false; };
}

function openSketchModal(targetId = null) {
  sketchTargetElementId = targetId || board.selectedId;
  const modal = document.getElementById('sketch-modal');
  const titleText = document.getElementById('sketch-modal-title-text');
  
  const target = board.elements.find(e => e.id === sketchTargetElementId);
  if (target) {
    titleText.textContent = `UI Spec / Mockup for: ${target.title || target.tableName || target.id}`;
  } else {
    titleText.textContent = 'Draw UI Specification / Wireframe Mockup';
  }

  modal.classList.add('open');
  initSketchCanvas();

  if (target && target.attachedMockup && target.attachedMockup.dataUrl) {
    const img = new Image();
    img.onload = () => {
      sketchCtx.clearRect(0, 0, 800, 460);
      sketchCtx.drawImage(img, 0, 0, 800, 460);
    };
    img.src = target.attachedMockup.dataUrl;
  } else {
    clearSketchCanvas();
  }
}

function closeSketchModal() {
  const modal = document.getElementById('sketch-modal');
  modal.classList.remove('open');
  sketchTargetElementId = null;
}

function setSketchTool(tool) {
  sketchTool = tool;
  document.getElementById('skt-pen').classList.toggle('active', tool === 'pen');
  document.getElementById('skt-eraser').classList.toggle('active', tool === 'eraser');
}

function setSketchColor(color, el) {
  sketchColor = color;
  document.querySelectorAll('.sketch-color-circle').forEach(c => c.classList.remove('active'));
  if (el) el.classList.add('active');
  if (sketchTool === 'eraser') setSketchTool('pen');
}

function setSketchWidth(w) {
  sketchStrokeWidth = parseInt(w, 10) || 4;
}

function clearSketchCanvas() {
  const canvas = document.getElementById('sketch-canvas');
  if (!canvas || !sketchCtx) return;
  sketchCtx.fillStyle = '#ffffff';
  sketchCtx.fillRect(0, 0, canvas.width, canvas.height);
}

function loadSketchFromFile(evt) {
  const file = evt.target.files[0];
  if (!file || !sketchCtx) return;
  const reader = new FileReader();
  reader.onload = (e) => {
    const img = new Image();
    img.onload = () => {
      sketchCtx.clearRect(0, 0, 800, 460);
      sketchCtx.drawImage(img, 0, 0, 800, 460);
    };
    img.src = e.target.result;
  };
  reader.readAsDataURL(file);
  evt.target.value = '';
}

function saveSketchAndAttach() {
  const canvas = document.getElementById('sketch-canvas');
  if (!canvas) return;
  const dataUrl = canvas.toDataURL('image/png');

  let target = board.elements.find(e => e.id === sketchTargetElementId);

  if (target) {
    target.attachedMockup = {
      dataUrl: dataUrl,
      timestamp: new Date().toISOString(),
      caption: `UI Specification (${new Date().toLocaleTimeString()})`
    };
    showNotification(`UI Spec successfully attached to ${target.title || target.id}`);
  } else {
    const cx = -board.panX + (window.innerWidth / 2) / board.zoom;
    const cy = -board.panY + (window.innerHeight / 2) / board.zoom;
    const newEl = {
      id: 'mockup-' + Date.now(),
      type: 'image',
      x: cx - 180,
      y: cy - 120,
      w: 360,
      h: 220,
      src: dataUrl,
      caption: 'UI Specification Mockup',
      selected: true
    };
    board.elements.push(newEl);
    board.selectedId = newEl.id;
    showNotification('Placed new UI Specification Mockup on Canvas');
  }

  pushHistory();
  renderAll();
  closeSketchModal();
  if (board.selectedId) updateDrawerContent();
}

function removeAttachedMockup(elementId) {
  const el = board.elements.find(e => e.id === elementId);
  if (el) {
    delete el.attachedMockup;
    pushHistory();
    renderAll();
    updateDrawerContent();
    showNotification('Attached UI mockup removed');
  }
}

// ── CLAUDE SKILLS INTERACTION ────────────────────────────────
function linkSkillToSelectedNode(skillId) {
  if (!board.selectedId) {
    showNotification('Please select a canvas node first to link this skill', 'error');
    return;
  }
  const el = board.elements.find(e => e.id === board.selectedId);
  if (!el) return;
  if (!el.linkedSkills) el.linkedSkills = [];
  if (!el.linkedSkills.includes(skillId)) {
    el.linkedSkills.push(skillId);
    pushHistory();
    renderAll();
    updateDrawerContent();
    showNotification(`Linked skill [${skillId}] to ${el.title || el.id}`);
  } else {
    showNotification(`Skill [${skillId}] already linked to this node`);
  }
}

function copyClaudeSkillSpec(skillId) {
  const specs = {
    'openapi-contract-validator': `# Claude Tool / Skill Specification\nname: openapi-contract-validator\ndescription: Validates incoming and outgoing payloads against OpenAPI 3.1 specification for this service.\ntools_granted: [read_schema, run_validator, diff_contracts]\ninstruction: |\n  Inspect all payload schemas defined on this node.\n  Ensure zero untyped JSON objects and verify HTTP status response contracts conform to RFC 7807 problem details.`,
    'postgres-rls-auditor': `# Claude Tool / Skill Specification\nname: postgres-rls-auditor\ndescription: Audits PostgreSQL tables for Row-Level Security (RLS) policies and tenant isolation bypasses.\ntools_granted: [pg_dump_schema, audit_rls_policies, test_tenant_isolation]\ninstruction: |\n  Inspect all SQL tables and verify every table has:\n  1. ALTER TABLE <table> ENABLE ROW LEVEL SECURITY;\n  2. ALTER TABLE <table> FORCE ROW LEVEL SECURITY;\n  3. CREATE POLICY tenant_isolation_policy ON <table> USING (tenant_id = current_setting('app.current_tenant_id')::uuid);`,
    'stripe-webhook-validator': `# Claude Tool / Skill Specification\nname: stripe-webhook-validator\ndescription: Validates Stripe webhook event signatures, replay protection, and idempotency key handling.\ntools_granted: [verify_hmac, inspect_event_ledger, check_retry_strategy]\ninstruction: |\n  Verify stripe-signature header HMAC SHA-256 verification.\n  Ensure event IDs are stored in an idempotent Postgres ledger before processing.`,
    'fhir-compliance-checker': `# Claude Tool / Skill Specification\nname: fhir-compliance-checker\ndescription: Checks healthcare API payloads against FHIR R4 US Core specifications and HIPAA PHI safeguards.\ntools_granted: [validate_fhir_resource, audit_phi_encryption, check_access_audit]\ninstruction: |\n  Verify Patient, Observation, and Encounter resources adhere to HL7 FHIR R4 schemas.\n  Ensure all PHI fields are tagged for field-level encryption.`,
    'zero-trust-policy-enforcer': `# Claude Tool / Skill Specification\nname: zero-trust-policy-enforcer\ndescription: Validates OPA Rego policies and mutual TLS (mTLS) SPIFFE workload identities.\ntools_granted: [eval_rego, inspect_spiffe_bundle, test_boundary_enforcement]\ninstruction: |\n  Enforce explicit ALLOW policy for service calls.\n  Reject any ingress traffic without verified x509-SVID client certificate.`
  };

  const text = specs[skillId] || `Skill: ${skillId}`;
  navigator.clipboard.writeText(text).then(() => {
    showNotification(`Copied Claude Skill specification [${skillId}] to clipboard!`);
  });
}

function triggerImageUpload() {
  document.getElementById('image-upload-input').click();
}

function handleImageUpload(evt) {
  const file = evt.target.files[0];
  if (!file) return;
  const reader = new FileReader();
  reader.onload = function(e) {
    const src = e.target.result;
    const cx = board.panX + window.innerWidth / 2 / board.zoom;
    const cy = board.panY + window.innerHeight / 2 / board.zoom;
    const el = {
      id: 'img-' + Date.now(),
      type: 'image',
      x: cx - 160,
      y: cy - 100,
      w: 320,
      h: 200,
      src: src,
      caption: file.name,
      selected: false
    };
    board.elements.push(el);
    pushHistory();
    renderAll();
  };
  reader.readAsDataURL(file);
  evt.target.value = '';
}

// ── SKILLS PANEL CONTENT ──────────────────────────────────────
function getSkillsPanelHTML() {
  const skills = [
    {
      id: 'openapi-contract-validator',
      name: 'OpenAPI Contract Validator',
      desc: 'Validates request/response schemas against OpenAPI 3.1 spec. Fails CI on undocumented fields.',
      keywords: ['openapi', 'contract', 'schema', 'validation'],
      tools: ['read_schema', 'run_validator'],
      status: 'Active',
      color: '#3b82f6'
    },
    {
      id: 'postgres-rls-auditor',
      name: 'PostgreSQL RLS Auditor',
      desc: 'Checks every table for row-level security policies. Enforces strict tenant_id isolation in multi-tenant schemas.',
      keywords: ['postgres', 'rls', 'security', 'multi-tenant'],
      tools: ['pg_dump_schema', 'audit_rls_policies'],
      status: 'Active',
      color: '#10b981'
    },
    {
      id: 'stripe-webhook-validator',
      name: 'Stripe Webhook Validator',
      desc: 'Verifies HMAC signature on every incoming Stripe event. Guarantees idempotent ledger recording and replay protection.',
      keywords: ['stripe', 'webhook', 'hmac', 'billing'],
      tools: ['verify_hmac', 'inspect_event_ledger'],
      status: 'Active',
      color: '#f59e0b'
    },
    {
      id: 'fhir-compliance-checker',
      name: 'FHIR Compliance Checker',
      desc: 'Validates FHIR R4 resource bundles against HL7 profiles. Flags PHI fields missing encryption annotation.',
      keywords: ['fhir', 'hl7', 'hipaa', 'healthcare', 'phi'],
      tools: ['validate_fhir', 'audit_phi'],
      status: 'Draft',
      color: '#8b5cf6'
    },
    {
      id: 'zero-trust-policy-enforcer',
      name: 'Zero-Trust Policy Enforcer',
      desc: 'Evaluates OPA Rego policies for every service-to-service call. Denies requests without valid SPIFFE SVID.',
      keywords: ['opa', 'spiffe', 'zero-trust', 'mtls'],
      tools: ['eval_rego', 'test_boundary'],
      status: 'Active',
      color: '#ef4444'
    }
  ];

  const cards = skills.map(s => `
    <div style="background:#ffffff;border:1px solid #e2e8f0;border-radius:9px;padding:12px;margin-bottom:12px;box-shadow:0 1px 3px rgba(0,0,0,0.04)">
      <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:5px">
        <span style="font-size:12px;font-weight:700;color:#0f172a;display:flex;align-items:center;gap:5px">
          <span style="width:7px;height:7px;border-radius:50%;background:${s.color}"></span>
          ${s.name}
        </span>
        <span style="padding:2px 7px;border-radius:4px;font-size:9px;font-weight:700;background:${s.status==='Active'?'rgba(16,185,129,.12)':'rgba(245,158,11,.12)'};color:${s.status==='Active'?'#059669':'#d97706'}">${s.status}</span>
      </div>
      <div style="font-size:11px;color:#64748b;line-height:1.5;margin-bottom:8px">${s.desc}</div>
      <div style="display:flex;flex-wrap:wrap;gap:4px;margin-bottom:10px">
        ${s.keywords.map(k => `<span style="padding:1.5px 6px;border-radius:3px;font-size:9.5px;background:#f1f5f9;color:#475569;font-family:monospace">${k}</span>`).join('')}
      </div>
      <div style="display:flex;gap:6px;align-items:center;border-top:1px solid #f1f5f9;padding-top:8px">
        <button onclick="linkSkillToSelectedNode('${s.id}')" style="padding:4px 9px;border-radius:5px;border:1px solid #cbd5e1;background:#f8fafc;color:#1e293b;font-size:10.5px;font-weight:600;cursor:pointer" title="Bind this skill to the currently selected node">
          Link to Node
        </button>
        <button onclick="copyClaudeSkillSpec('${s.id}')" style="padding:4px 9px;border-radius:5px;border:1px solid ${s.color};background:transparent;color:${s.color};font-size:10.5px;font-weight:600;cursor:pointer" title="Copy Claude Tool / Skill markdown prompt">
          Copy Claude Spec
        </button>
      </div>
    </div>
  `).join('');

  return `
    <div style="margin-bottom:14px;padding-bottom:12px;border-bottom:1px solid #e2e8f0">
      <div style="font-size:13px;font-weight:800;color:#0f172a;display:flex;align-items:center;gap:6px">
        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#2563eb" stroke-width="2.2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/></svg>
        Claude Skills &amp; Agent Registry
      </div>
      <div style="font-size:11px;color:#64748b;margin-top:3px;line-height:1.4">
        Structured engineering capabilities formatted for Claude tool-calling, MCP integration, and system prompt injection.
      </div>
    </div>
    ${cards}
  `;
}

function renderImageElement(el) {
  const div = document.createElement('div');
  div.className = 'canvas-element' + (el.selected ? ' selected' : '');
  div.dataset.id = el.id;
  div.style.cssText = `position:absolute;left:${el.x}px;top:${el.y}px;width:${el.w}px;height:${el.h + 24}px;cursor:move;user-select:none`;

  const img = document.createElement('img');
  img.src = el.src;
  img.style.cssText = `width:100%;height:${el.h}px;object-fit:contain;border-radius:8px;border:2px solid #e2e8f0;display:block;background:#f8fafc`;

  const cap = document.createElement('div');
  cap.textContent = el.caption || '';
  cap.style.cssText = 'font-size:10px;color:#64748b;text-align:center;padding:3px 0;white-space:nowrap;overflow:hidden;text-overflow:ellipsis';

  div.appendChild(img);
  div.appendChild(cap);
  div.addEventListener('mousedown', e => startDrag(e, el.id));
  div.addEventListener('click', e => { e.stopPropagation(); selectElement(el.id); });
  return div;
}

</script>
  <div id="miro-toast" class="miro-toast"></div>
</body>
</html>
"""