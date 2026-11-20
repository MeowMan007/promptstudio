"""Static page HTML for Prompt Studio – Clean Minimalist Light Aesthetic."""

COMMON_CSS = """
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
  <style>
    :root {
      --bg: #f8fafc;
      --surface: #ffffff;
      --surface-subtle: #f1f5f9;
      --border: #e2e8f0;
      --border-strong: #cbd5e1;
      --text: #0f172a;
      --text-muted: #64748b;
      --text-subtle: #94a3b8;
      --blue: #2563eb;
      --blue-hover: #1d4ed8;
      --blue-light: #eff6ff;
      --indigo: #4f46e5;
      --green: #059669;
      --green-light: #ecfdf5;
      --amber: #d97706;
      --amber-light: #fffbeb;
      --red: #dc2626;
      --font: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      --mono: 'JetBrains Mono', ui-monospace, monospace;
      --sh-xs: 0 1px 2px rgba(0,0,0,.04);
      --sh-sm: 0 1px 3px rgba(0,0,0,.06), 0 1px 2px rgba(0,0,0,.04);
      --sh-md: 0 4px 12px rgba(0,0,0,.06), 0 1px 3px rgba(0,0,0,.03);
      --sh-lg: 0 12px 28px rgba(0,0,0,.08), 0 2px 6px rgba(0,0,0,.03);
      --r-sm: 6px;
      --r-md: 10px;
      --r-lg: 14px;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    html, body { font-family: var(--font); background: var(--bg); color: var(--text); line-height: 1.6; }
    a { color: inherit; text-decoration: none; }
    
    /* Topnav */
    .topnav {
      position: sticky; top: 0; z-index: 900;
      height: 56px; padding: 0 28px;
      background: #ffffff;
      border-bottom: 1px solid var(--border);
      display: flex; align-items: center; justify-content: space-between;
    }
    .topnav-logo {
      display: flex; align-items: center; gap: 9px;
      font-size: 15px; font-weight: 800; color: var(--blue);
      letter-spacing: -0.3px; margin-right: 36px;
    }
    .topnav-logo svg { width: 26px; height: 26px; flex-shrink: 0; }
    .topnav-links { display: flex; align-items: center; gap: 4px; flex: 1; }
    .topnav-link {
      padding: 6px 13px; border-radius: var(--r-sm);
      font-size: 13px; font-weight: 500; color: var(--text-muted);
      transition: background 0.15s, color 0.15s;
    }
    .topnav-link:hover { background: var(--surface-subtle); color: var(--text); }
    .topnav-link.active { color: var(--blue); background: var(--blue-light); font-weight: 600; }
    .topnav-actions { display: flex; align-items: center; gap: 8px; }
    .btn {
      display: inline-flex; align-items: center; gap: 6px;
      padding: 7px 16px; border-radius: var(--r-sm);
      font-size: 13px; font-weight: 600; cursor: pointer;
      border: 1.5px solid transparent; transition: all 0.15s; white-space: nowrap;
    }
    .btn-ghost { color: var(--text-muted); border-color: var(--border); background: #ffffff; }
    .btn-ghost:hover { color: var(--text); border-color: var(--blue); background: var(--blue-light); }
    .btn-primary { background: var(--blue); color: #ffffff; border-color: var(--blue); }
    .btn-primary:hover { background: var(--blue-hover); border-color: var(--blue-hover); box-shadow: 0 4px 12px rgba(37,99,235,0.25); }
  </style>
"""

# ---------------------------------------------------------------------------
# 1. LANDING PAGE – Minimalist Light View (Single-Screen / Non-Scrollable)
# ---------------------------------------------------------------------------
LANDING_HTML = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Prompt Studio &ndash; Visual System Architecture Workspace</title>
  {COMMON_CSS}
  <style>
    html, body {{
      height: 100vh; overflow: hidden; background: #ffffff;
    }}
    .stage {{
      position: fixed; top: 56px; left: 0; right: 0; bottom: 0;
      display: grid; grid-template-columns: 1fr 1fr;
    }}
    /* Left Hero Pane */
    .left {{
      display: flex; flex-direction: column; justify-content: center;
      padding: 48px 56px; gap: 24px; position: relative;
      background: #ffffff; border-right: 1px solid var(--border);
    }}
    .badge {{
      display: inline-flex; align-items: center; gap: 7px;
      padding: 4px 12px; border-radius: 20px;
      background: var(--surface-subtle); border: 1px solid var(--border);
      font-size: 11.5px; font-weight: 600; color: var(--text-muted);
      letter-spacing: 0.3px; width: fit-content;
    }}
    .badge-dot {{ width: 6px; height: 6px; border-radius: 50%; background: var(--green); }}
    .hero-title {{
      font-size: 48px; font-weight: 900; line-height: 1.08;
      letter-spacing: -1.6px; color: var(--text);
    }}
    .hero-title span.hl {{ color: var(--blue); }}
    .hero-sub {{
      font-size: 16px; line-height: 1.65; color: var(--text-muted);
      max-width: 440px;
    }}
    .cta-row {{ display: flex; align-items: center; gap: 12px; }}
    .btn-cta {{
      display: inline-flex; align-items: center; gap: 7px;
      padding: 10px 22px; border-radius: 8px;
      font-size: 14px; font-weight: 600; cursor: pointer;
      border: 1.5px solid transparent; transition: all 0.15s;
    }}
    .btn-cta-primary {{
      background: var(--blue); color: #ffffff; border-color: var(--blue);
      box-shadow: 0 4px 14px rgba(37,99,235,0.22);
    }}
    .btn-cta-primary:hover {{ background: var(--blue-hover); transform: translateY(-1px); }}
    .btn-cta-outline {{
      color: var(--text); border-color: var(--border-strong); background: #ffffff;
    }}
    .btn-cta-outline:hover {{ border-color: var(--blue); background: var(--blue-light); color: var(--blue); }}
    
    /* Mascot / wordmark lockup */
    .mascot-lockup {{
      display: flex; align-items: center; gap: 14px;
      margin-top: 4px; padding: 14px 18px;
      background: var(--surface-subtle); border: 1px solid var(--border);
      border-radius: var(--r-md); width: fit-content;
    }}
    .mascot-icon {{
      width: 44px; height: 44px; flex-shrink: 0;
    }}
    .mascot-text {{
      display: flex; flex-direction: column; gap: 2px;
    }}
    .mascot-name {{
      font-size: 13px; font-weight: 800; color: var(--text);
      letter-spacing: -0.3px;
    }}
    .mascot-tagline {{
      font-size: 11px; color: var(--text-subtle); font-family: var(--mono);
      letter-spacing: 0.1px;
    }}

    /* Right Canvas Preview Pane */
    .right {{
      background: var(--bg); position: relative; overflow: hidden;
      display: flex; align-items: center; justify-content: center;
    }}
    .canvas-grid {{
      position: absolute; inset: 0;
      background-image: radial-gradient(circle, #cbd5e1 1px, transparent 1px);
      background-size: 24px 24px; opacity: 0.55;
    }}
    .preview-board {{
      position: relative; z-index: 2; width: 520px;
      display: flex; flex-direction: column; gap: 14px;
    }}
    .pf {{
      background: #ffffff; border: 1px solid var(--border);
      border-radius: 10px; padding: 14px; box-shadow: var(--sh-sm);
    }}
    .pf-label {{
      font-size: 10px; font-weight: 700; letter-spacing: 0.5px; text-transform: uppercase;
      color: var(--text-muted); margin-bottom: 10px; display: flex; align-items: center; gap: 6px;
    }}
    .pf-nodes {{ display: flex; gap: 8px; flex-wrap: wrap; }}
    .p-node {{
      background: #ffffff; border: 1px solid var(--border);
      padding: 7px 12px; border-radius: 7px;
      font-size: 11.5px; font-weight: 600; color: var(--text);
      display: flex; align-items: center; gap: 7px; box-shadow: var(--sh-xs);
    }}
    .p-dot {{ width: 6px; height: 6px; border-radius: 50%; }}
    .p-dot.b {{ background: var(--blue); }}
    .p-dot.g {{ background: var(--green); }}
    .p-dot.a {{ background: var(--amber); }}
    .p-dot.i {{ background: var(--indigo); }}

    .p-edge {{
      display: flex; align-items: center; gap: 8px; padding: 2px 8px;
    }}
    .p-line {{ flex: 1; height: 1px; background: var(--border-strong); }}
    .p-tag {{ font-size: 9.5px; font-weight: 600; color: var(--text-subtle); font-family: var(--mono); }}

    .p-erd {{
      background: #ffffff; border: 1px solid var(--border); border-radius: 7px;
      padding: 8px 12px; font-family: var(--mono); font-size: 10.5px;
      display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-top: 8px;
    }}
    .p-erd-item {{ display: flex; justify-content: space-between; }}
    .p-erd-col {{ color: var(--text); }}
    .p-erd-type {{ color: var(--text-subtle); }}
    .p-erd-pk {{ color: var(--blue); font-weight: 700; }}

    .p-sticky {{
      background: #fef9c3; border: 1px solid #fef08a; border-radius: 8px;
      padding: 10px 14px; font-size: 11px; color: #713f12; line-height: 1.5;
      box-shadow: var(--sh-xs);
    }}
    .p-sticky strong {{ color: #854d0e; font-weight: 700; display: block; margin-bottom: 2px; }}
  </style>
</head>
<body>

<nav class="topnav">
  <div class="topnav-logo">
    <svg viewBox="0 0 26 26" fill="none">
      <rect width="26" height="26" rx="6" fill="#2563eb"/>
      <rect x="5" y="5" width="7" height="7" rx="1.5" fill="#fff"/>
      <rect x="14" y="5" width="7" height="7" rx="1.5" fill="rgba(255,255,255,.5)"/>
      <rect x="5" y="14" width="7" height="7" rx="1.5" fill="rgba(255,255,255,.5)"/>
      <rect x="14" y="14" width="7" height="7" rx="1.5" fill="#fff"/>
    </svg>
    Prompt Studio
  </div>
  <div class="topnav-links">
    <a href="/" class="topnav-link active">Home</a>
    <a href="/templates" class="topnav-link">Templates</a>
    <a href="/guide" class="topnav-link">Docs</a>
    <a href="/pricing" class="topnav-link">Pricing</a>
    <a href="/dashboard" class="topnav-link">Dashboard</a>
  </div>
  <div class="topnav-actions">
    <a href="/login" class="btn btn-ghost">Sign in</a>
    <a href="/board" class="btn btn-primary">
      <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><rect x="3" y="3" width="18" height="18" rx="3"/><line x1="9" y1="3" x2="9" y2="21"/><line x1="3" y1="9" x2="21" y2="9"/></svg>
      Open Canvas
    </a>
  </div>
</nav>

<div class="stage">
  <!-- Left Side: Hero Details -->
  <div class="left">
    <div class="badge">
      <span class="badge-dot"></span>
      Visual System Architecture Workspace
    </div>
    <h1 class="hero-title">
      Design systems<br>that <span class="hl">ship.</span>
    </h1>
    <p class="hero-sub">
      A canvas-first workspace for backend engineers. Map architectures, model typed data schemas,
      and export code-ready specifications without the noise.
    </p>
    <div class="cta-row">
      <a href="/board" class="btn-cta btn-cta-primary">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><rect x="3" y="3" width="18" height="18" rx="3"/><line x1="9" y1="3" x2="9" y2="21"/><line x1="3" y1="9" x2="21" y2="9"/></svg>
        Open Canvas
      </a>
      <a href="/templates" class="btn-cta btn-cta-outline">
        Browse Templates &rarr;
      </a>
    </div>
    <div class="mascot-lockup">
      <svg class="mascot-icon" viewBox="0 0 44 44" fill="none" xmlns="http://www.w3.org/2000/svg">
        <!-- Graph node mascot: nodes + connector arcs -->
        <rect width="44" height="44" rx="10" fill="#f1f5f9"/>
        <!-- Center node -->
        <circle cx="22" cy="22" r="6" fill="#2563eb"/>
        <circle cx="22" cy="22" r="3.5" fill="#fff"/>
        <!-- Top node -->
        <circle cx="22" cy="8" r="4" fill="#0f172a"/>
        <line x1="22" y1="12" x2="22" y2="16" stroke="#94a3b8" stroke-width="1.5"/>
        <!-- Bottom-left node -->
        <circle cx="10" cy="34" r="4" fill="#059669"/>
        <line x1="13.4" y1="31.6" x2="18" y2="27.2" stroke="#94a3b8" stroke-width="1.5"/>
        <!-- Bottom-right node -->
        <circle cx="34" cy="34" r="4" fill="#d97706"/>
        <line x1="30.6" y1="31.6" x2="26" y2="27.2" stroke="#94a3b8" stroke-width="1.5"/>
        <!-- Left node -->
        <circle cx="6" cy="17" r="3" fill="#4f46e5"/>
        <line x1="9" y1="17.8" x2="16" y2="20" stroke="#94a3b8" stroke-width="1.5"/>
        <!-- Right node -->
        <circle cx="38" cy="17" r="3" fill="#2563eb" fill-opacity="0.4"/>
        <line x1="35" y1="17.8" x2="28" y2="20" stroke="#94a3b8" stroke-width="1.5"/>
      </svg>
      <div class="mascot-text">
        <div class="mascot-name">Prompt Studio</div>
        <div class="mascot-tagline">graph-driven &middot; spec-first &middot; deterministic</div>
      </div>
    </div>
  </div>

  <!-- Right Side: Minimalist Architecture Preview -->
  <div class="right">
    <div class="canvas-grid"></div>
    <div class="preview-board">

      <!-- Ingestion Layer -->
      <div class="pf">
        <div class="pf-label"><span class="p-dot b"></span> Ingestion &amp; API Gateway</div>
        <div class="pf-nodes">
          <div class="p-node"><span class="p-dot b"></span>API Gateway (FastAPI)</div>
          <div class="p-node"><span class="p-dot g"></span>Kafka Stream</div>
          <div class="p-node"><span class="p-dot i"></span>gRPC Service</div>
        </div>
      </div>

      <!-- Connector -->
      <div class="p-edge">
        <span class="p-tag">HTTP/2</span>
        <span class="p-line"></span>
        <span class="p-tag">JWT Bearer &bull; RLS Context</span>
        <span class="p-line"></span>
        <span class="p-tag">p99 &lt; 15ms</span>
      </div>

      <!-- Processing & Persistence -->
      <div class="pf">
        <div class="pf-label"><span class="p-dot g"></span> Multi-Tenant Data &amp; Core</div>
        <div class="pf-nodes">
          <div class="p-node"><span class="p-dot g"></span>PostgreSQL (RLS)</div>
          <div class="p-node"><span class="p-dot a"></span>Stripe Billing</div>
          <div class="p-node"><span class="p-dot i"></span>Worker Fleet</div>
        </div>
        <div class="p-erd">
          <div class="p-erd-item"><span class="p-erd-col p-erd-pk">tenants.id</span><span class="p-erd-type">UUID PK</span></div>
          <div class="p-erd-item"><span class="p-erd-col">plan_tier</span><span class="p-erd-type">VARCHAR</span></div>
          <div class="p-erd-item"><span class="p-erd-col p-erd-pk">users.tenant_id</span><span class="p-erd-type">UUID FK</span></div>
          <div class="p-erd-item"><span class="p-erd-col">role</span><span class="p-erd-type">ENUM</span></div>
        </div>
      </div>

      <!-- ADR Sticky -->
      <div class="p-sticky">
        <strong>ADR-001: PostgreSQL Row-Level Security</strong>
        Multi-tenancy isolated at connection checkout via app.current_tenant_id. Zero cross-tenant data leakage.
      </div>

    </div>
  </div>
</div>

</body>
</html>"""

# ---------------------------------------------------------------------------
# 2. TEMPLATES PAGE – Minimalist Light View
# ---------------------------------------------------------------------------
TEMPLATES_HTML = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Architecture Blueprints &ndash; Prompt Studio</title>
  {COMMON_CSS}
  <style>
    .page-header {{ background: #ffffff; border-bottom: 1px solid var(--border); padding: 48px 0 36px; }}
    .container {{ max-width: 1160px; margin: 0 auto; padding: 0 32px; }}
    .page-title {{ font-size: 32px; font-weight: 800; letter-spacing: -0.6px; margin-bottom: 8px; }}
    .page-sub {{ color: var(--text-muted); font-size: 15px; }}
    .filter-bar {{ display: flex; gap: 8px; flex-wrap: wrap; margin-top: 24px; }}
    .filter-pill {{
      padding: 5px 14px; border-radius: 20px; font-size: 12.5px; font-weight: 600;
      border: 1px solid var(--border); background: #ffffff; color: var(--text-muted); cursor: pointer;
      transition: all 0.15s;
    }}
    .filter-pill:hover {{ border-color: var(--blue); color: var(--blue); }}
    .filter-pill.active {{ background: var(--blue); color: #ffffff; border-color: var(--blue); }}

    .grid {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 24px; padding: 40px 0 60px; }}
    @media (max-width: 860px) {{ .grid {{ grid-template-columns: 1fr; }} }}

    .card {{
      background: #ffffff; border: 1px solid var(--border); border-radius: var(--r-lg);
      overflow: hidden; box-shadow: var(--sh-xs); transition: all 0.2s; cursor: pointer;
      display: flex; flex-direction: column;
    }}
    .card:hover {{ box-shadow: var(--sh-md); border-color: var(--blue); transform: translateY(-2px); }}

    .card-preview {{
      height: 140px; background: var(--bg); border-bottom: 1px solid var(--border);
      padding: 16px; display: flex; align-items: center; justify-content: center; gap: 8px; flex-wrap: wrap;
      background-image: radial-gradient(circle, #cbd5e1 1px, transparent 1px); background-size: 20px 20px;
    }}
    .cp-node {{
      background: #ffffff; border: 1px solid var(--border); padding: 5px 11px; border-radius: 6px;
      font-size: 11px; font-weight: 600; color: var(--text); box-shadow: var(--sh-xs);
    }}
    .cp-edge {{ width: 24px; height: 1px; background: var(--border-strong); }}

    .card-body {{ padding: 20px; flex: 1; display: flex; flex-direction: column; gap: 10px; }}
    .card-top {{ display: flex; align-items: flex-start; justify-content: space-between; gap: 10px; }}
    .card-title {{ font-size: 16px; font-weight: 700; }}
    .card-badge {{
      padding: 3px 9px; border-radius: 4px; font-size: 10px; font-weight: 700;
      text-transform: uppercase; letter-spacing: 0.4px; background: var(--blue-light); color: var(--blue);
    }}
    .card-desc {{ font-size: 13px; color: var(--text-muted); line-height: 1.6; }}
    .card-meta {{ display: flex; gap: 14px; font-size: 11.5px; color: var(--text-subtle); margin-top: auto; padding-top: 10px; }}
    .card-meta strong {{ color: var(--text-muted); }}
    .card-footer {{
      padding: 12px 20px; border-top: 1px solid var(--border); background: var(--bg);
      display: flex; align-items: center; justify-content: space-between;
    }}
    .card-footer-text {{ font-size: 11.5px; color: var(--text-subtle); }}
    .card-open {{ font-size: 12.5px; font-weight: 600; color: var(--blue); }}
  </style>
</head>
<body>

<nav class="topnav">
  <div class="topnav-logo">
    <svg viewBox="0 0 26 26" fill="none"><rect width="26" height="26" rx="6" fill="#2563eb"/><rect x="5" y="5" width="7" height="7" rx="1.5" fill="#fff"/><rect x="14" y="5" width="7" height="7" rx="1.5" fill="rgba(255,255,255,.5)"/><rect x="5" y="14" width="7" height="7" rx="1.5" fill="rgba(255,255,255,.5)"/><rect x="14" y="14" width="7" height="7" rx="1.5" fill="#fff"/></svg>
    Prompt Studio
  </div>
  <div class="topnav-links">
    <a href="/" class="topnav-link">Home</a>
    <a href="/templates" class="topnav-link active">Templates</a>
    <a href="/guide" class="topnav-link">Docs</a>
    <a href="/pricing" class="topnav-link">Pricing</a>
    <a href="/dashboard" class="topnav-link">Dashboard</a>
  </div>
  <div class="topnav-actions">
    <a href="/login" class="btn btn-ghost">Sign in</a>
    <a href="/board" class="btn btn-primary">Open Canvas</a>
  </div>
</nav>

<div class="page-header">
  <div class="container">
    <h1 class="page-title">Architecture Blueprints</h1>
    <p class="page-sub">Production-grade, battle-tested system templates ready to edit and export.</p>
    <div class="filter-bar">
      <span class="filter-pill active" data-filter="all">All (12)</span>
      <span class="filter-pill" data-filter="saas">SaaS &amp; Collab</span>
      <span class="filter-pill" data-filter="fintech">Fintech &amp; Commerce</span>
      <span class="filter-pill" data-filter="data">Data &amp; Streaming</span>
      <span class="filter-pill" data-filter="dev">Developer Platform</span>
      <span class="filter-pill" data-filter="security">Security &amp; Healthcare</span>
      <span class="filter-pill" data-filter="ai">AI &amp; Agents</span>
    </div>
  </div>
</div>

<div class="container">
  <div class="grid">

    <div class="card" onclick="location.href='/board?template=b2b_saas'">
      <div class="card-preview">
        <div class="cp-node">Traefik Gateway</div><div class="cp-node">OIDC SSO</div><div class="cp-node">Domain API</div><div class="cp-node">PostgreSQL RLS</div><div class="cp-node">Stripe Billing</div>
      </div>
      <div class="card-body">
        <div class="card-top">
          <div class="card-title">B2B Multi-Tenant SaaS</div>
          <span class="card-badge">Core SaaS</span>
        </div>
        <div class="card-desc">Multi-tenant application architecture with tenant-scoped identity, PostgreSQL Row-Level Security (RLS) data isolation, subscription lifecycle, and asynchronous background worker queues.</div>
        <div style="margin: 6px 0;">
          <span style="display:inline-block;padding:2px 7px;border-radius:4px;font-size:11px;background:#f1f5f9;color:#475569;margin-right:4px;margin-bottom:4px;">Traefik Gateway</span><span style="display:inline-block;padding:2px 7px;border-radius:4px;font-size:11px;background:#f1f5f9;color:#475569;margin-right:4px;margin-bottom:4px;">OIDC / SAML SSO</span><span style="display:inline-block;padding:2px 7px;border-radius:4px;font-size:11px;background:#f1f5f9;color:#475569;margin-right:4px;margin-bottom:4px;">PostgreSQL RLS</span><span style="display:inline-block;padding:2px 7px;border-radius:4px;font-size:11px;background:#f1f5f9;color:#475569;margin-right:4px;margin-bottom:4px;">Stripe Billing</span><span style="display:inline-block;padding:2px 7px;border-radius:4px;font-size:11px;background:#f1f5f9;color:#475569;margin-right:4px;margin-bottom:4px;">BullMQ</span>
        </div>
        <ul style="font-size:12px;color:var(--text-muted);padding-left:16px;margin:4px 0 8px;">
          <li style="margin-bottom:3px;">Tenant context resolution at API gateway</li><li style="margin-bottom:3px;">PostgreSQL Row-Level Security (RLS) tenant isolation</li><li style="margin-bottom:3px;">Subscription tier & feature entitlement enforcement</li>
        </ul>
        <div class="card-meta">
          <span>Complexity: <strong>Intermediate</strong></span>
          <span>Target: <strong>B2B SaaS Engineering Teams</strong></span>
        </div>
      </div>
      <div class="card-footer">
        <span class="card-footer-text">Includes architecture, wireframes, ERD &amp; delivery tasks</span>
        <span class="card-open">Open Blueprint &rarr;</span>
      </div>
    </div>


    <div class="card" onclick="location.href='/board?template=fintech_ledger'">
      <div class="card-preview">
        <div class="cp-node">Multi-Rail Ingress</div><div class="cp-node">Fraud Scorer</div><div class="cp-node">Double-Entry Ledger</div><div class="cp-node">3-Way Recon</div><div class="cp-node">KMS Vault</div>
      </div>
      <div class="card-body">
        <div class="card-top">
          <div class="card-title">Fintech Payment Gateway & Double-Entry Ledger</div>
          <span class="card-badge">Fintech & Banking</span>
        </div>
        <div class="card-desc">Payment orchestration and merchant ledger platform featuring immutable double-entry journal entries, multi-rail gateway routing, three-way reconciliation, and tokenised cardholder data boundaries.</div>
        <div style="margin: 6px 0;">
          <span style="display:inline-block;padding:2px 7px;border-radius:4px;font-size:11px;background:#f1f5f9;color:#475569;margin-right:4px;margin-bottom:4px;">Multi-Rail Gateway</span><span style="display:inline-block;padding:2px 7px;border-radius:4px;font-size:11px;background:#f1f5f9;color:#475569;margin-right:4px;margin-bottom:4px;">Double-Entry Engine</span><span style="display:inline-block;padding:2px 7px;border-radius:4px;font-size:11px;background:#f1f5f9;color:#475569;margin-right:4px;margin-bottom:4px;">3-Way Reconciliation</span><span style="display:inline-block;padding:2px 7px;border-radius:4px;font-size:11px;background:#f1f5f9;color:#475569;margin-right:4px;margin-bottom:4px;">Tokenised CDE Vault</span>
        </div>
        <ul style="font-size:12px;color:var(--text-muted);padding-left:16px;margin:4px 0 8px;">
          <li style="margin-bottom:3px;">Immutable double-entry ledger with debit/credit balance invariants</li><li style="margin-bottom:3px;">Idempotency keys and distributed state machine for payments</li><li style="margin-bottom:3px;">Automated 3-way reconciliation (gateway, processor, internal ledger)</li>
        </ul>
        <div class="card-meta">
          <span>Complexity: <strong>Advanced</strong></span>
          <span>Target: <strong>Fintech Engineers</strong></span>
        </div>
      </div>
      <div class="card-footer">
        <span class="card-footer-text">Includes architecture, wireframes, ERD &amp; delivery tasks</span>
        <span class="card-open">Open Blueprint &rarr;</span>
      </div>
    </div>


    <div class="card" onclick="location.href='/board?template=event_streaming'">
      <div class="card-preview">
        <div class="cp-node">Vector Agent</div><div class="cp-node">Kafka Cluster</div><div class="cp-node">Flink Stream Engine</div><div class="cp-node">ClickHouse OLAP</div><div class="cp-node">DLQ Replay</div>
      </div>
      <div class="card-body">
        <div class="card-top">
          <div class="card-title">Real-Time Event Streaming & Analytics</div>
          <span class="card-badge">Data & Streaming</span>
        </div>
        <div class="card-desc">High-volume operational telemetry platform with partition-keyed event ingestion, schema registry governance, stream processing, and dead-letter queue recovery.</div>
        <div style="margin: 6px 0;">
          <span style="display:inline-block;padding:2px 7px;border-radius:4px;font-size:11px;background:#f1f5f9;color:#475569;margin-right:4px;margin-bottom:4px;">Apache Kafka</span><span style="display:inline-block;padding:2px 7px;border-radius:4px;font-size:11px;background:#f1f5f9;color:#475569;margin-right:4px;margin-bottom:4px;">Apache Flink</span><span style="display:inline-block;padding:2px 7px;border-radius:4px;font-size:11px;background:#f1f5f9;color:#475569;margin-right:4px;margin-bottom:4px;">Schema Registry</span><span style="display:inline-block;padding:2px 7px;border-radius:4px;font-size:11px;background:#f1f5f9;color:#475569;margin-right:4px;margin-bottom:4px;">ClickHouse OLAP</span><span style="display:inline-block;padding:2px 7px;border-radius:4px;font-size:11px;background:#f1f5f9;color:#475569;margin-right:4px;margin-bottom:4px;">Vector / Fluent</span>
        </div>
        <ul style="font-size:12px;color:var(--text-muted);padding-left:16px;margin:4px 0 8px;">
          <li style="margin-bottom:3px;">Schema evolution governance with backward compatibility validation</li><li style="margin-bottom:3px;">Tumbling and sliding window stream aggregations</li><li style="margin-bottom:3px;">Partition-keyed ordering semantics and consumer group lag monitoring</li>
        </ul>
        <div class="card-meta">
          <span>Complexity: <strong>Advanced</strong></span>
          <span>Target: <strong>Data Platform Engineers</strong></span>
        </div>
      </div>
      <div class="card-footer">
        <span class="card-footer-text">Includes architecture, wireframes, ERD &amp; delivery tasks</span>
        <span class="card-open">Open Blueprint &rarr;</span>
      </div>
    </div>


    <div class="card" onclick="location.href='/board?template=ecommerce_marketplace'">
      <div class="card-preview">
        <div class="cp-node">Storefront CDN</div><div class="cp-node">Order Orchestrator</div><div class="cp-node">Inventory Lock</div><div class="cp-node">Split Payout Engine</div><div class="cp-node">Seller Ledger</div>
      </div>
      <div class="card-body">
        <div class="card-top">
          <div class="card-title">Multi-Vendor Marketplace & Seller Payouts</div>
          <span class="card-badge">E-Commerce</span>
        </div>
        <div class="card-desc">Multi-vendor commercial platform supporting catalogue management, multi-seller cart order splits, escrow-like hold-and-release payouts, and seller verification.</div>
        <div style="margin: 6px 0;">
          <span style="display:inline-block;padding:2px 7px;border-radius:4px;font-size:11px;background:#f1f5f9;color:#475569;margin-right:4px;margin-bottom:4px;">Algolia Search</span><span style="display:inline-block;padding:2px 7px;border-radius:4px;font-size:11px;background:#f1f5f9;color:#475569;margin-right:4px;margin-bottom:4px;">Redis Inventory Locks</span><span style="display:inline-block;padding:2px 7px;border-radius:4px;font-size:11px;background:#f1f5f9;color:#475569;margin-right:4px;margin-bottom:4px;">Order Orchestrator</span><span style="display:inline-block;padding:2px 7px;border-radius:4px;font-size:11px;background:#f1f5f9;color:#475569;margin-right:4px;margin-bottom:4px;">Split Transfers</span><span style="display:inline-block;padding:2px 7px;border-radius:4px;font-size:11px;background:#f1f5f9;color:#475569;margin-right:4px;margin-bottom:4px;">Seller Portal</span>
        </div>
        <ul style="font-size:12px;color:var(--text-muted);padding-left:16px;margin:4px 0 8px;">
          <li style="margin-bottom:3px;">Two-phase stock reservation with automatic expiry</li><li style="margin-bottom:3px;">Multi-seller order splitting with independent fulfillment tracks</li><li style="margin-bottom:3px;">Direct and transfer payment routing with platform fee splits</li>
        </ul>
        <div class="card-meta">
          <span>Complexity: <strong>Intermediate</strong></span>
          <span>Target: <strong>Marketplace Platform Teams</strong></span>
        </div>
      </div>
      <div class="card-footer">
        <span class="card-footer-text">Includes architecture, wireframes, ERD &amp; delivery tasks</span>
        <span class="card-open">Open Blueprint &rarr;</span>
      </div>
    </div>


    <div class="card" onclick="location.href='/board?template=developer_platform'">
      <div class="card-preview">
        <div class="cp-node">Kong Gateway</div><div class="cp-node">Redis Rate Limiter</div><div class="cp-node">Webhook Dispatcher</div><div class="cp-node">OpenAPI Docs</div><div class="cp-node">Event Store</div>
      </div>
      <div class="card-body">
        <div class="card-top">
          <div class="card-title">Developer API & Webhook Platform</div>
          <span class="card-badge">Developer Tools</span>
        </div>
        <div class="card-desc">Public API infrastructure featuring tiered token-bucket rate limiting, scoped API key rotation, interactive documentation, and reliable HMAC-signed webhook delivery.</div>
        <div style="margin: 6px 0;">
          <span style="display:inline-block;padding:2px 7px;border-radius:4px;font-size:11px;background:#f1f5f9;color:#475569;margin-right:4px;margin-bottom:4px;">Kong Gateway</span><span style="display:inline-block;padding:2px 7px;border-radius:4px;font-size:11px;background:#f1f5f9;color:#475569;margin-right:4px;margin-bottom:4px;">Redis Token Bucket</span><span style="display:inline-block;padding:2px 7px;border-radius:4px;font-size:11px;background:#f1f5f9;color:#475569;margin-right:4px;margin-bottom:4px;">OpenAPI 3.1</span><span style="display:inline-block;padding:2px 7px;border-radius:4px;font-size:11px;background:#f1f5f9;color:#475569;margin-right:4px;margin-bottom:4px;">Webhook Dispatcher</span><span style="display:inline-block;padding:2px 7px;border-radius:4px;font-size:11px;background:#f1f5f9;color:#475569;margin-right:4px;margin-bottom:4px;">Developer Portal</span>
        </div>
        <ul style="font-size:12px;color:var(--text-muted);padding-left:16px;margin:4px 0 8px;">
          <li style="margin-bottom:3px;">Tiered rate limiting with sliding-window counters in Redis</li><li style="margin-bottom:3px;">Scoped API key generation, hashing (SHA-256), and graceful rotation</li><li style="margin-bottom:3px;">Webhook delivery with exponential backoff, HMAC-SHA256 signing, and DLQ</li>
        </ul>
        <div class="card-meta">
          <span>Complexity: <strong>Intermediate</strong></span>
          <span>Target: <strong>Developer Experience Teams</strong></span>
        </div>
      </div>
      <div class="card-footer">
        <span class="card-footer-text">Includes architecture, wireframes, ERD &amp; delivery tasks</span>
        <span class="card-open">Open Blueprint &rarr;</span>
      </div>
    </div>


    <div class="card" onclick="location.href='/board?template=collab_workspace'">
      <div class="card-preview">
        <div class="cp-node">WebSocket Gateway</div><div class="cp-node">Yjs Sync Server</div><div class="cp-node">Redis Awareness</div><div class="cp-node">Doc Store</div><div class="cp-node">Snapshot Worker</div>
      </div>
      <div class="card-body">
        <div class="card-top">
          <div class="card-title">Collaborative Document & Canvas Workspace</div>
          <span class="card-badge">Productivity & Collaboration</span>
        </div>
        <div class="card-desc">Multi-user real-time workspace featuring conflict-free replicated data types (CRDTs), ephemeral presence awareness, document snapshots, and workspace permissions.</div>
        <div style="margin: 6px 0;">
          <span style="display:inline-block;padding:2px 7px;border-radius:4px;font-size:11px;background:#f1f5f9;color:#475569;margin-right:4px;margin-bottom:4px;">Yjs CRDT</span><span style="display:inline-block;padding:2px 7px;border-radius:4px;font-size:11px;background:#f1f5f9;color:#475569;margin-right:4px;margin-bottom:4px;">WebSocket Sync</span><span style="display:inline-block;padding:2px 7px;border-radius:4px;font-size:11px;background:#f1f5f9;color:#475569;margin-right:4px;margin-bottom:4px;">Redis Pub/Sub</span><span style="display:inline-block;padding:2px 7px;border-radius:4px;font-size:11px;background:#f1f5f9;color:#475569;margin-right:4px;margin-bottom:4px;">Presence Awareness</span><span style="display:inline-block;padding:2px 7px;border-radius:4px;font-size:11px;background:#f1f5f9;color:#475569;margin-right:4px;margin-bottom:4px;">PostgreSQL Doc Store</span>
        </div>
        <ul style="font-size:12px;color:var(--text-muted);padding-left:16px;margin:4px 0 8px;">
          <li style="margin-bottom:3px;">Yjs CRDT synchronization for conflict-free concurrent editing</li><li style="margin-bottom:3px;">Ephemeral cursor positions and presence awareness via Redis Pub/Sub</li><li style="margin-bottom:3px;">Offline edit queuing and automatic reconciliation upon reconnect</li>
        </ul>
        <div class="card-meta">
          <span>Complexity: <strong>Advanced</strong></span>
          <span>Target: <strong>Collaboration Tool Engineers</strong></span>
        </div>
      </div>
      <div class="card-footer">
        <span class="card-footer-text">Includes architecture, wireframes, ERD &amp; delivery tasks</span>
        <span class="card-open">Open Blueprint &rarr;</span>
      </div>
    </div>


    <div class="card" onclick="location.href='/board?template=healthcare_portal'">
      <div class="card-preview">
        <div class="cp-node">SMART Ingress</div><div class="cp-node">FHIR R4 Gateway</div><div class="cp-node">PHI Guardrail</div><div class="cp-node">HL7 Listener</div><div class="cp-node">Encrypted Clinical DB</div>
      </div>
      <div class="card-body">
        <div class="card-top">
          <div class="card-title">Healthcare Patient Portal & FHIR Integration</div>
          <span class="card-badge">Healthcare & Life Sciences</span>
        </div>
        <div class="card-desc">Patient engagement portal designed for interoperability with electronic health record (EHR) systems via HL7 FHIR R4 APIs, featuring attribute-based access and audit logging.</div>
        <div style="margin: 6px 0;">
          <span style="display:inline-block;padding:2px 7px;border-radius:4px;font-size:11px;background:#f1f5f9;color:#475569;margin-right:4px;margin-bottom:4px;">FHIR R4 REST API</span><span style="display:inline-block;padding:2px 7px;border-radius:4px;font-size:11px;background:#f1f5f9;color:#475569;margin-right:4px;margin-bottom:4px;">SMART on FHIR</span><span style="display:inline-block;padding:2px 7px;border-radius:4px;font-size:11px;background:#f1f5f9;color:#475569;margin-right:4px;margin-bottom:4px;">PHI Access Control</span><span style="display:inline-block;padding:2px 7px;border-radius:4px;font-size:11px;background:#f1f5f9;color:#475569;margin-right:4px;margin-bottom:4px;">HL7 v2 ADT</span><span style="display:inline-block;padding:2px 7px;border-radius:4px;font-size:11px;background:#f1f5f9;color:#475569;margin-right:4px;margin-bottom:4px;">Encrypted Store</span>
        </div>
        <ul style="font-size:12px;color:var(--text-muted);padding-left:16px;margin:4px 0 8px;">
          <li style="margin-bottom:3px;">HL7 FHIR R4 standard resource models (Patient, Observation, Encounter)</li><li style="margin-bottom:3px;">SMART on FHIR OAuth 2.0 authorization and clinical launch workflows</li><li style="margin-bottom:3px;">Patient consent verification and field-level sensitive data masking</li>
        </ul>
        <div class="card-meta">
          <span>Complexity: <strong>Specialized</strong></span>
          <span>Target: <strong>HealthTech Architects</strong></span>
        </div>
      </div>
      <div class="card-footer">
        <span class="card-footer-text">Includes architecture, wireframes, ERD &amp; delivery tasks</span>
        <span class="card-open">Open Blueprint &rarr;</span>
      </div>
    </div>


    <div class="card" onclick="location.href='/board?template=zero_trust_iam'">
      <div class="card-preview">
        <div class="cp-node">IdP Federation</div><div class="cp-node">SCIM Provisioner</div><div class="cp-node">OPA Policy Engine</div><div class="cp-node">Device Posture</div><div class="cp-node">SPIFFE CA</div>
      </div>
      <div class="card-body">
        <div class="card-top">
          <div class="card-title">Zero-Trust Identity & Access Management</div>
          <span class="card-badge">Security & Identity</span>
        </div>
        <div class="card-desc">Enterprise identity governance framework enforcing continuous verification, Open Policy Agent (OPA) fine-grained authorization, device posture scoring, and ephemeral credentials.</div>
        <div style="margin: 6px 0;">
          <span style="display:inline-block;padding:2px 7px;border-radius:4px;font-size:11px;background:#f1f5f9;color:#475569;margin-right:4px;margin-bottom:4px;">OpenID Connect</span><span style="display:inline-block;padding:2px 7px;border-radius:4px;font-size:11px;background:#f1f5f9;color:#475569;margin-right:4px;margin-bottom:4px;">SCIM 2.0</span><span style="display:inline-block;padding:2px 7px;border-radius:4px;font-size:11px;background:#f1f5f9;color:#475569;margin-right:4px;margin-bottom:4px;">OPA Rego Policy</span><span style="display:inline-block;padding:2px 7px;border-radius:4px;font-size:11px;background:#f1f5f9;color:#475569;margin-right:4px;margin-bottom:4px;">Device Posture</span><span style="display:inline-block;padding:2px 7px;border-radius:4px;font-size:11px;background:#f1f5f9;color:#475569;margin-right:4px;margin-bottom:4px;">SPIFFE / SPIRE</span>
        </div>
        <ul style="font-size:12px;color:var(--text-muted);padding-left:16px;margin:4px 0 8px;">
          <li style="margin-bottom:3px;">Continuous trust evaluation combining user identity, device posture, and context</li><li style="margin-bottom:3px;">Declarative policy decision point (PDP) using Open Policy Agent (OPA)</li><li style="margin-bottom:3px;">Automated SCIM 2.0 provisioning and instant multi-system de-provisioning</li>
        </ul>
        <div class="card-meta">
          <span>Complexity: <strong>Advanced</strong></span>
          <span>Target: <strong>Identity Architects</strong></span>
        </div>
      </div>
      <div class="card-footer">
        <span class="card-footer-text">Includes architecture, wireframes, ERD &amp; delivery tasks</span>
        <span class="card-open">Open Blueprint &rarr;</span>
      </div>
    </div>


    <div class="card" onclick="location.href='/board?template=ai_agent_rag'">
      <div class="card-preview">
        <div class="cp-node">Ingestion Pipeline</div><div class="cp-node">Qdrant Vector DB</div><div class="cp-node">LangGraph Agent</div><div class="cp-node">Guardrails Gateway</div><div class="cp-node">Trace Store</div>
      </div>
      <div class="card-body">
        <div class="card-top">
          <div class="card-title">Enterprise AI Agent & RAG Platform</div>
          <span class="card-badge">AI & Agents</span>
        </div>
        <div class="card-desc">Autonomous agent and retrieval-augmented generation platform with pre-retrieval document ACL filtering, semantic vector search, tool guardrails, and execution auditing.</div>
        <div style="margin: 6px 0;">
          <span style="display:inline-block;padding:2px 7px;border-radius:4px;font-size:11px;background:#f1f5f9;color:#475569;margin-right:4px;margin-bottom:4px;">Qdrant Vector DB</span><span style="display:inline-block;padding:2px 7px;border-radius:4px;font-size:11px;background:#f1f5f9;color:#475569;margin-right:4px;margin-bottom:4px;">Hybrid Search</span><span style="display:inline-block;padding:2px 7px;border-radius:4px;font-size:11px;background:#f1f5f9;color:#475569;margin-right:4px;margin-bottom:4px;">LangGraph Agent</span><span style="display:inline-block;padding:2px 7px;border-radius:4px;font-size:11px;background:#f1f5f9;color:#475569;margin-right:4px;margin-bottom:4px;">Guardrails AI</span><span style="display:inline-block;padding:2px 7px;border-radius:4px;font-size:11px;background:#f1f5f9;color:#475569;margin-right:4px;margin-bottom:4px;">Trace Log</span>
        </div>
        <ul style="font-size:12px;color:var(--text-muted);padding-left:16px;margin:4px 0 8px;">
          <li style="margin-bottom:3px;">Tenant and document ACL enforcement prior to model context assembly</li><li style="margin-bottom:3px;">Hybrid lexical and vector semantic retrieval with cross-encoder reranking</li><li style="margin-bottom:3px;">Autonomous multi-step agent orchestrator with human-in-the-loop approvals</li>
        </ul>
        <div class="card-meta">
          <span>Complexity: <strong>Advanced</strong></span>
          <span>Target: <strong>AI Engineers</strong></span>
        </div>
      </div>
      <div class="card-footer">
        <span class="card-footer-text">Includes architecture, wireframes, ERD &amp; delivery tasks</span>
        <span class="card-open">Open Blueprint &rarr;</span>
      </div>
    </div>


    <div class="card" onclick="location.href='/board?template=global_payroll'">
      <div class="card-preview">
        <div class="cp-node">Payroll Ingress</div><div class="cp-node">Rule Pack Engine</div><div class="cp-node">Gross-to-Net Runner</div><div class="cp-node">Disbursement Batch</div><div class="cp-node">GL Export</div>
      </div>
      <div class="card-body">
        <div class="card-top">
          <div class="card-title">Global Payroll & Tax Engine</div>
          <span class="card-badge">Fintech & Payroll</span>
        </div>
        <div class="card-desc">Deterministic gross-to-net payroll engine supporting versioned jurisdiction rule packs, multi-currency processing, effective-dated contracts, and statutory remittance.</div>
        <div style="margin: 6px 0;">
          <span style="display:inline-block;padding:2px 7px;border-radius:4px;font-size:11px;background:#f1f5f9;color:#475569;margin-right:4px;margin-bottom:4px;">Gross-to-Net Engine</span><span style="display:inline-block;padding:2px 7px;border-radius:4px;font-size:11px;background:#f1f5f9;color:#475569;margin-right:4px;margin-bottom:4px;">Versioned Rule Packs</span><span style="display:inline-block;padding:2px 7px;border-radius:4px;font-size:11px;background:#f1f5f9;color:#475569;margin-right:4px;margin-bottom:4px;">Effective Dating</span><span style="display:inline-block;padding:2px 7px;border-radius:4px;font-size:11px;background:#f1f5f9;color:#475569;margin-right:4px;margin-bottom:4px;">SEPA / ACH Disburse</span><span style="display:inline-block;padding:2px 7px;border-radius:4px;font-size:11px;background:#f1f5f9;color:#475569;margin-right:4px;margin-bottom:4px;">Statutory Audit</span>
        </div>
        <ul style="font-size:12px;color:var(--text-muted);padding-left:16px;margin:4px 0 8px;">
          <li style="margin-bottom:3px;">Deterministic calculation pipeline with immutable run snapshots</li><li style="margin-bottom:3px;">Effective-dated jurisdiction tax rules and localized deduction schedules</li><li style="margin-bottom:3px;">Pre-flight payroll preview and anomaly detection exception queue</li>
        </ul>
        <div class="card-meta">
          <span>Complexity: <strong>Specialized</strong></span>
          <span>Target: <strong>Payroll Engineers</strong></span>
        </div>
      </div>
      <div class="card-footer">
        <span class="card-footer-text">Includes architecture, wireframes, ERD &amp; delivery tasks</span>
        <span class="card-open">Open Blueprint &rarr;</span>
      </div>
    </div>


    <div class="card" onclick="location.href='/board?template=legaltech_clm'">
      <div class="card-preview">
        <div class="cp-node">Contract Intake</div><div class="cp-node">Clause Library</div><div class="cp-node">Redline Engine</div><div class="cp-node">Ethical Wall Gate</div><div class="cp-node">Signature Vault</div>
      </div>
      <div class="card-body">
        <div class="card-top">
          <div class="card-title">LegalTech Contract Lifecycle Management</div>
          <span class="card-badge">LegalTech & Enterprise</span>
        </div>
        <div class="card-desc">Enterprise contract management platform covering clause assembly, tracked redlining, multi-tier approval routing, ethical walls, and e-signature envelope tracking.</div>
        <div style="margin: 6px 0;">
          <span style="display:inline-block;padding:2px 7px;border-radius:4px;font-size:11px;background:#f1f5f9;color:#475569;margin-right:4px;margin-bottom:4px;">Clause Library</span><span style="display:inline-block;padding:2px 7px;border-radius:4px;font-size:11px;background:#f1f5f9;color:#475569;margin-right:4px;margin-bottom:4px;">Diff / Redline Engine</span><span style="display:inline-block;padding:2px 7px;border-radius:4px;font-size:11px;background:#f1f5f9;color:#475569;margin-right:4px;margin-bottom:4px;">Ethical Walls</span><span style="display:inline-block;padding:2px 7px;border-radius:4px;font-size:11px;background:#f1f5f9;color:#475569;margin-right:4px;margin-bottom:4px;">DocuSign Adapter</span><span style="display:inline-block;padding:2px 7px;border-radius:4px;font-size:11px;background:#f1f5f9;color:#475569;margin-right:4px;margin-bottom:4px;">Obligations Tracker</span>
        </div>
        <ul style="font-size:12px;color:var(--text-muted);padding-left:16px;margin:4px 0 8px;">
          <li style="margin-bottom:3px;">Approved clause library assembly with deviation risk scoring</li><li style="margin-bottom:3px;">Side-by-side version comparison and tracked change redline engine</li><li style="margin-bottom:3px;">Ethical wall conflict-of-interest access boundaries between business units</li>
        </ul>
        <div class="card-meta">
          <span>Complexity: <strong>Intermediate</strong></span>
          <span>Target: <strong>Legal Operations Engineers</strong></span>
        </div>
      </div>
      <div class="card-footer">
        <span class="card-footer-text">Includes architecture, wireframes, ERD &amp; delivery tasks</span>
        <span class="card-open">Open Blueprint &rarr;</span>
      </div>
    </div>


    <div class="card" onclick="location.href='/board?template=logistics_supply_chain'">
      <div class="card-preview">
        <div class="cp-node">EMQX Broker</div><div class="cp-node">TimescaleDB</div><div class="cp-node">Geofence Engine</div><div class="cp-node">EDI X12 Translator</div><div class="cp-node">POD Signer</div>
      </div>
      <div class="card-body">
        <div class="card-top">
          <div class="card-title">Logistics & Cold-Chain Supply Chain Platform</div>
          <span class="card-badge">Supply Chain & IoT</span>
        </div>
        <div class="card-desc">Global freight visibility platform tracking multi-modal shipments, IoT sensor cold-chain temperature telemetry, EDI X12 transaction sets, and cryptographic proof-of-delivery.</div>
        <div style="margin: 6px 0;">
          <span style="display:inline-block;padding:2px 7px;border-radius:4px;font-size:11px;background:#f1f5f9;color:#475569;margin-right:4px;margin-bottom:4px;">EMQX MQTT</span><span style="display:inline-block;padding:2px 7px;border-radius:4px;font-size:11px;background:#f1f5f9;color:#475569;margin-right:4px;margin-bottom:4px;">TimescaleDB</span><span style="display:inline-block;padding:2px 7px;border-radius:4px;font-size:11px;background:#f1f5f9;color:#475569;margin-right:4px;margin-bottom:4px;">EDI X12 Engine</span><span style="display:inline-block;padding:2px 7px;border-radius:4px;font-size:11px;background:#f1f5f9;color:#475569;margin-right:4px;margin-bottom:4px;">Geofencing</span><span style="display:inline-block;padding:2px 7px;border-radius:4px;font-size:11px;background:#f1f5f9;color:#475569;margin-right:4px;margin-bottom:4px;">Ed25519 Cryptographic POD</span>
        </div>
        <ul style="font-size:12px;color:var(--text-muted);padding-left:16px;margin:4px 0 8px;">
          <li style="margin-bottom:3px;">MQTT telematics ingestion with local offline excursion alarms on device</li><li style="margin-bottom:3px;">TimescaleDB hypertable storage for time-series temperature readings</li><li style="margin-bottom:3px;">Polygon geofence entry/exit detection and automated shipment milestone advance</li>
        </ul>
        <div class="card-meta">
          <span>Complexity: <strong>Advanced</strong></span>
          <span>Target: <strong>Logistics Engineers</strong></span>
        </div>
      </div>
      <div class="card-footer">
        <span class="card-footer-text">Includes architecture, wireframes, ERD &amp; delivery tasks</span>
        <span class="card-open">Open Blueprint &rarr;</span>
      </div>
    </div>

  </div>
</div>

<script>
  document.querySelectorAll('.filter-pill').forEach(p => {{
    p.addEventListener('click', () => {{
      document.querySelectorAll('.filter-pill').forEach(x => x.classList.remove('active'));
      p.classList.add('active');
      const f = p.getAttribute('data-filter') || 'all';
      document.querySelectorAll('.card').forEach(card => {{
        const href = card.getAttribute('onclick') || '';
        let show = (f === 'all');
        if (f === 'saas' && (href.includes('b2b_saas') || href.includes('collab_workspace') || href.includes('legaltech_clm'))) show = true;
        if (f === 'fintech' && (href.includes('fintech_ledger') || href.includes('ecommerce_marketplace') || href.includes('global_payroll'))) show = true;
        if (f === 'data' && (href.includes('event_streaming') || href.includes('logistics_supply_chain'))) show = true;
        if (f === 'dev' && href.includes('developer_platform')) show = true;
        if (f === 'security' && (href.includes('zero_trust_iam') || href.includes('healthcare_portal'))) show = true;
        if (f === 'ai' && href.includes('ai_agent_rag')) show = true;
        card.style.display = show ? 'flex' : 'none';
      }});
    }});
  }});
</script>
</body>
</html>"""

# ---------------------------------------------------------------------------
# 3. DOCS / GUIDE PAGE – Minimalist Light View
# ---------------------------------------------------------------------------
DOCS_HTML = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Documentation &ndash; Prompt Studio</title>
  {COMMON_CSS}
  <style>
    .layout {{ display: grid; grid-template-columns: 240px 1fr; min-height: calc(100vh - 56px); }}
    .sidebar {{
      background: #ffffff; border-right: 1px solid var(--border); padding: 24px 0;
      position: sticky; top: 56px; height: calc(100vh - 56px); overflow-y: auto;
    }}
    .sidebar-sec {{ padding: 0 16px 20px; }}
    .sidebar-heading {{
      font-size: 10px; font-weight: 700; letter-spacing: 0.7px; text-transform: uppercase;
      color: var(--text-subtle); margin-bottom: 6px; padding: 0 8px;
    }}
    .sidebar-link {{
      display: block; padding: 6px 10px; border-radius: var(--r-sm);
      font-size: 13px; font-weight: 500; color: var(--text-muted); cursor: pointer; transition: all 0.15s;
    }}
    .sidebar-link:hover {{ color: var(--text); background: var(--surface-subtle); }}
    .sidebar-link.active {{ color: var(--blue); background: var(--blue-light); font-weight: 600; }}

    .content {{ padding: 48px 64px; max-width: 820px; background: #ffffff; }}
    h1 {{ font-size: 32px; font-weight: 800; letter-spacing: -0.6px; margin-bottom: 12px; }}
    h2 {{ font-size: 20px; font-weight: 700; letter-spacing: -0.3px; margin: 36px 0 14px; border-bottom: 1px solid var(--border); padding-bottom: 8px; }}
    p {{ color: var(--text-muted); line-height: 1.75; margin-bottom: 14px; font-size: 14px; }}
    code {{ font-family: var(--mono); font-size: 12px; background: var(--surface-subtle); border: 1px solid var(--border); padding: 2px 6px; border-radius: 4px; color: var(--blue); }}
    pre {{ background: var(--surface-subtle); border: 1px solid var(--border); border-radius: 8px; padding: 18px; margin: 16px 0; overflow-x: auto; }}
    pre code {{ background: none; border: none; padding: 0; color: var(--text); font-size: 12px; line-height: 1.6; }}

    .kbd-table {{ width: 100%; border-collapse: collapse; margin: 16px 0; }}
    .kbd-table th {{ text-align: left; font-size: 11px; font-weight: 700; letter-spacing: 0.5px; text-transform: uppercase; color: var(--text-subtle); padding: 8px 12px; border-bottom: 1px solid var(--border); }}
    .kbd-table td {{ padding: 8px 12px; border-bottom: 1px solid var(--border); font-size: 13px; color: var(--text-muted); }}
    kbd {{ font-family: var(--mono); font-size: 11px; background: #ffffff; border: 1px solid var(--border-strong); border-radius: 4px; padding: 2px 6px; box-shadow: var(--sh-xs); color: var(--text); }}
  </style>
</head>
<body>

<nav class="topnav">
  <div class="topnav-logo">
    <svg viewBox="0 0 26 26" fill="none"><rect width="26" height="26" rx="6" fill="#2563eb"/><rect x="5" y="5" width="7" height="7" rx="1.5" fill="#fff"/><rect x="14" y="5" width="7" height="7" rx="1.5" fill="rgba(255,255,255,.5)"/><rect x="5" y="14" width="7" height="7" rx="1.5" fill="rgba(255,255,255,.5)"/><rect x="14" y="14" width="7" height="7" rx="1.5" fill="#fff"/></svg>
    Prompt Studio
  </div>
  <div class="topnav-links">
    <a href="/" class="topnav-link">Home</a>
    <a href="/templates" class="topnav-link">Templates</a>
    <a href="/guide" class="topnav-link active">Docs</a>
    <a href="/pricing" class="topnav-link">Pricing</a>
    <a href="/dashboard" class="topnav-link">Dashboard</a>
  </div>
  <div class="topnav-actions">
    <a href="/login" class="btn btn-ghost">Sign in</a>
    <a href="/board" class="btn btn-primary">Open Canvas</a>
  </div>
</nav>

<div class="layout">
  <div class="sidebar">
    <div class="sidebar-sec">
      <div class="sidebar-heading">Getting Started</div>
      <a class="sidebar-link active">Introduction</a>
      <a class="sidebar-link">Canvas Basics</a>
      <a class="sidebar-link">Keyboard Shortcuts</a>
      <a class="sidebar-link">Templates</a>
    </div>
    <div class="sidebar-sec">
      <div class="sidebar-heading">Canvas Elements</div>
      <a class="sidebar-link">Architecture Nodes</a>
      <a class="sidebar-link">ERD Tables</a>
      <a class="sidebar-link">Wireframes</a>
      <a class="sidebar-link">Sticky Notes (ADR)</a>
      <a class="sidebar-link">UI Mockup Drawing</a>
      <a class="sidebar-link">Frames &amp; Zones</a>
    </div>
    <div class="sidebar-sec">
      <div class="sidebar-heading">Claude Skills</div>
      <a class="sidebar-link">Skills Registry</a>
      <a class="sidebar-link">Binding Skills to Nodes</a>
      <a class="sidebar-link">Copying Claude Specs</a>
    </div>
    <div class="sidebar-sec">
      <div class="sidebar-heading">Export &amp; Specs</div>
      <a class="sidebar-link">Export to YAML</a>
      <a class="sidebar-link">Export to JSON</a>
      <a class="sidebar-link">ZIP Bundle</a>
    </div>
  </div>

  <div class="content">
    <h1>Prompt Studio Documentation</h1>
    <p>Prompt Studio is a canvas-first visual system design workspace. Create architecture diagrams, database ERD schemas, wireframes, and Architecture Decision Records (ADRs) with zero visual noise.</p>

    <h2>Keyboard Shortcuts</h2>
    <table class="kbd-table">
      <thead><tr><th>Action</th><th>Shortcut</th></tr></thead>
      <tbody>
        <tr><td>Select Tool</td><td><kbd>V</kbd></td></tr>
        <tr><td>Pan Canvas</td><td><kbd>H</kbd> or <kbd>Space</kbd> + drag</td></tr>
        <tr><td>Draw UI Mockup / Attach Image</td><td><kbd>I</kbd></td></tr>
        <tr><td>Add Arch Component</td><td><kbd>A</kbd></td></tr>
        <tr><td>Add ERD Table</td><td><kbd>D</kbd></td></tr>
        <tr><td>Add Sticky Note (ADR)</td><td><kbd>N</kbd></td></tr>
        <tr><td>Connection Line</td><td><kbd>L</kbd></td></tr>
        <tr><td>Templates Modal</td><td><kbd>B</kbd></td></tr>
        <tr><td>Undo / Redo</td><td><kbd>Ctrl+Z</kbd> / <kbd>Ctrl+Y</kbd></td></tr>
      </tbody>
    </table>

    <h2>UI Mockup Specification</h2>
    <p>You can draw UI sketches directly inside Prompt Studio or attach screenshot mockups to any node or wireframe screen. Click the <code>Draw Mockup</code> button in the toolbar or context popover to open the integrated HTML5 sketchpad.</p>

    <h2>Claude Skills &amp; Agent Registry</h2>
    <p>The right context drawer provides a dedicated <strong>Skills</strong> tab formatted for Claude tool calling and Anthropic Model Context Protocol (MCP). Link skills directly to architecture nodes to establish verified implementation boundaries.</p>
  </div>
</div>

</body>
</html>"""

# ---------------------------------------------------------------------------
# 4. PRICING PAGE – Minimalist Light View
# ---------------------------------------------------------------------------
PRICING_HTML = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Pricing &ndash; Prompt Studio</title>
  {COMMON_CSS}
  <style>
    .page {{ max-width: 980px; margin: 0 auto; padding: 60px 32px; }}
    .page-header {{ text-align: center; margin-bottom: 48px; }}
    .page-title {{ font-size: 34px; font-weight: 800; letter-spacing: -0.8px; margin-bottom: 10px; }}
    .page-sub {{ color: var(--text-muted); font-size: 15px; margin-bottom: 24px; }}
    
    .toggle-row {{ display: flex; align-items: center; justify-content: center; gap: 14px; font-size: 13px; font-weight: 600; }}
    .toggle-pill {{
      display: flex; width: 48px; height: 26px; background: var(--blue); border-radius: 14px;
      cursor: pointer; position: relative; transition: background 0.2s;
    }}
    .toggle-pill::after {{
      content: ''; position: absolute; top: 3px; left: 3px; width: 20px; height: 20px;
      border-radius: 50%; background: #ffffff; transition: transform 0.2s;
    }}
    .toggle-pill.annual::after {{ transform: translateX(22px); }}
    .toggle-label {{ color: var(--text-muted); }}
    .toggle-label.active {{ color: var(--text); }}
    .save-tag {{ padding: 2px 7px; border-radius: 4px; background: var(--green-light); color: var(--green); font-size: 11px; font-weight: 700; }}

    .plans {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; margin-top: 36px; }}
    @media (max-width: 820px) {{ .plans {{ grid-template-columns: 1fr; }} }}

    .plan {{
      background: #ffffff; border: 1px solid var(--border); border-radius: var(--r-lg);
      padding: 28px; display: flex; flex-direction: column; gap: 18px; box-shadow: var(--sh-xs); position: relative;
    }}
    .plan.featured {{ border-color: var(--blue); box-shadow: var(--sh-md); }}
    .plan-badge {{
      position: absolute; top: -11px; left: 50%; transform: translateX(-50%);
      padding: 3px 12px; border-radius: 20px; background: var(--blue); color: #ffffff;
      font-size: 10.5px; font-weight: 700; letter-spacing: 0.3px; white-space: nowrap;
    }}
    .plan-name {{ font-size: 13px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px; color: var(--text-muted); }}
    .plan-price {{ display: flex; align-items: baseline; gap: 4px; }}
    .plan-price-num {{ font-size: 38px; font-weight: 900; letter-spacing: -1.2px; }}
    .plan-price-unit {{ font-size: 13.5px; color: var(--text-muted); }}
    .plan-desc {{ font-size: 12.5px; color: var(--text-muted); line-height: 1.5; }}
    
    .plan-cta {{
      display: block; text-align: center; padding: 9px; border-radius: var(--r-sm);
      font-size: 13.5px; font-weight: 600; cursor: pointer; border: 1.5px solid; transition: all 0.15s;
    }}
    .plan-cta-outline {{ border-color: var(--border-strong); color: var(--text); }}
    .plan-cta-outline:hover {{ border-color: var(--blue); background: var(--blue-light); color: var(--blue); }}
    .plan-cta-primary {{ background: var(--blue); color: #ffffff; border-color: var(--blue); }}
    .plan-cta-primary:hover {{ background: var(--blue-hover); }}

    .plan-features {{ display: flex; flex-direction: column; gap: 8px; flex: 1; padding-top: 6px; }}
    .plan-feat {{ display: flex; align-items: center; gap: 8px; font-size: 12.5px; color: var(--text-muted); }}
    .feat-check {{ color: var(--green); font-weight: 700; }}
  </style>
</head>
<body>

<nav class="topnav">
  <div class="topnav-logo">
    <svg viewBox="0 0 26 26" fill="none"><rect width="26" height="26" rx="6" fill="#2563eb"/><rect x="5" y="5" width="7" height="7" rx="1.5" fill="#fff"/><rect x="14" y="5" width="7" height="7" rx="1.5" fill="rgba(255,255,255,.5)"/><rect x="5" y="14" width="7" height="7" rx="1.5" fill="rgba(255,255,255,.5)"/><rect x="14" y="14" width="7" height="7" rx="1.5" fill="#fff"/></svg>
    Prompt Studio
  </div>
  <div class="topnav-links">
    <a href="/" class="topnav-link">Home</a>
    <a href="/templates" class="topnav-link">Templates</a>
    <a href="/guide" class="topnav-link">Docs</a>
    <a href="/pricing" class="topnav-link active">Pricing</a>
    <a href="/dashboard" class="topnav-link">Dashboard</a>
  </div>
  <div class="topnav-actions">
    <a href="/login" class="btn btn-ghost">Sign in</a>
    <a href="/board" class="btn btn-primary">Open Canvas</a>
  </div>
</nav>

<div class="page">
  <div class="page-header">
    <h1 class="page-title">Simple, transparent pricing</h1>
    <p class="page-sub">Start free. Scale when you need it. No per-seat surprises.</p>
    <div class="toggle-row">
      <span class="toggle-label active" id="lbl-monthly">Monthly</span>
      <div class="toggle-pill" id="billing-toggle" onclick="toggleBilling()"></div>
      <span class="toggle-label" id="lbl-annual">Annual <span class="save-tag">Save 20%</span></span>
    </div>
  </div>

  <div class="plans">
    <div class="plan">
      <div class="plan-name">Starter</div>
      <div class="plan-price">
        <span class="plan-price-num" id="price-starter">$0</span>
        <span class="plan-price-unit">/mo</span>
      </div>
      <div class="plan-desc">For individuals exploring system design.</div>
      <a href="/board" class="plan-cta plan-cta-outline">Start Free</a>
      <div class="plan-features">
        <div class="plan-feat"><span class="feat-check">&check;</span> Unlimited canvas boards</div>
        <div class="plan-feat"><span class="feat-check">&check;</span> All 9 architecture blueprints</div>
        <div class="plan-feat"><span class="feat-check">&check;</span> Export to YAML / JSON</div>
        <div class="plan-feat"><span class="feat-check">&check;</span> Draw &amp; attach UI mockups</div>
      </div>
    </div>

    <div class="plan featured">
      <div class="plan-badge">Most Popular</div>
      <div class="plan-name">Pro</div>
      <div class="plan-price">
        <span class="plan-price-num" id="price-pro">$29</span>
        <span class="plan-price-unit">/mo</span>
      </div>
      <div class="plan-desc">For engineering teams building production systems.</div>
      <a href="/dashboard" class="plan-cta plan-cta-primary">Get Pro</a>
      <div class="plan-features">
        <div class="plan-feat"><span class="feat-check">&check;</span> Everything in Starter</div>
        <div class="plan-feat"><span class="feat-check">&check;</span> Claude Skills &amp; Agent Registry</div>
        <div class="plan-feat"><span class="feat-check">&check;</span> Team workspaces (up to 10)</div>
        <div class="plan-feat"><span class="feat-check">&check;</span> Deployment manifest generator</div>
        <div class="plan-feat"><span class="feat-check">&check;</span> Version history &amp; audit trail</div>
      </div>
    </div>

    <div class="plan">
      <div class="plan-name">Enterprise</div>
      <div class="plan-price">
        <span class="plan-price-num">Custom</span>
      </div>
      <div class="plan-desc">For large organizations with compliance requirements.</div>
      <a href="/dashboard" class="plan-cta plan-cta-outline">Contact Us</a>
      <div class="plan-features">
        <div class="plan-feat"><span class="feat-check">&check;</span> Everything in Pro</div>
        <div class="plan-feat"><span class="feat-check">&check;</span> Unlimited team seats</div>
        <div class="plan-feat"><span class="feat-check">&check;</span> SSO / SAML / SCIM</div>
        <div class="plan-feat"><span class="feat-check">&check;</span> 99.99% SLA guarantee</div>
        <div class="plan-feat"><span class="feat-check">&check;</span> Dedicated support</div>
      </div>
    </div>
  </div>
</div>

<script>
  let annual = false;
  function toggleBilling() {{
    annual = !annual;
    document.getElementById('billing-toggle').className = 'toggle-pill' + (annual ? ' annual' : '');
    document.getElementById('lbl-monthly').className = 'toggle-label' + (annual ? '' : ' active');
    document.getElementById('lbl-annual').className = 'toggle-label' + (annual ? ' active' : '');
    document.getElementById('price-starter').textContent = '$0';
    document.getElementById('price-pro').textContent = annual ? '$23' : '$29';
  }}
</script>
</body>
</html>"""

# ---------------------------------------------------------------------------
# 5. DASHBOARD PAGE – Minimalist Light View
# ---------------------------------------------------------------------------
DASHBOARD_HTML = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Dashboard &ndash; Prompt Studio</title>
  {COMMON_CSS}
  <style>
    html, body {{ height: 100vh; overflow: hidden; }}
    .shell {{ display: grid; grid-template-columns: 220px 1fr; height: 100vh; }}
    .sidebar {{ background: #ffffff; border-right: 1px solid var(--border); display: flex; flex-direction: column; }}
    .sidebar-logo {{
      display: flex; align-items: center; gap: 9px; padding: 16px 20px;
      font-size: 15px; font-weight: 800; color: var(--blue); border-bottom: 1px solid var(--border);
    }}
    .sidebar-logo svg {{ width: 24px; height: 24px; }}
    .sidebar-nav {{ flex: 1; padding: 12px 10px; overflow-y: auto; display: flex; flex-direction: column; gap: 2px; }}
    .sidebar-section-label {{
      font-size: 9.5px; font-weight: 700; letter-spacing: 0.7px; text-transform: uppercase;
      color: var(--text-subtle); padding: 12px 10px 6px;
    }}
    .sidebar-item {{
      display: flex; align-items: center; gap: 9px; padding: 8px 10px; border-radius: var(--r-sm);
      font-size: 13px; font-weight: 500; color: var(--text-muted); cursor: pointer; transition: all 0.15s;
    }}
    .sidebar-item:hover {{ color: var(--text); background: var(--surface-subtle); }}
    .sidebar-item.active {{ color: var(--blue); background: var(--blue-light); font-weight: 600; }}
    .sidebar-footer {{ padding: 14px; border-top: 1px solid var(--border); }}
    .user-row {{ display: flex; align-items: center; gap: 10px; padding: 6px; border-radius: var(--r-sm); }}
    .user-avatar {{
      width: 30px; height: 30px; border-radius: 50%; background: var(--blue); color: #ffffff;
      display: flex; align-items: center; justify-content: center; font-size: 11px; font-weight: 700;
    }}
    .user-info {{ flex: 1; min-width: 0; }}
    .user-name {{ font-size: 12.5px; font-weight: 600; }}
    .user-plan {{ font-size: 10.5px; color: var(--text-subtle); }}

    .main {{ display: flex; flex-direction: column; overflow: hidden; background: var(--bg); }}
    .topbar {{
      height: 56px; padding: 0 28px; background: #ffffff; border-bottom: 1px solid var(--border);
      display: flex; align-items: center; justify-content: space-between; flex-shrink: 0;
    }}
    .topbar-title {{ font-size: 16px; font-weight: 700; }}
    .content {{ flex: 1; overflow-y: auto; padding: 28px 32px; display: flex; flex-direction: column; gap: 24px; }}
    
    .stats {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; }}
    .stat {{ background: #ffffff; border: 1px solid var(--border); border-radius: var(--r-md); padding: 18px 20px; box-shadow: var(--sh-xs); }}
    .stat-label {{ font-size: 11px; font-weight: 600; color: var(--text-subtle); text-transform: uppercase; letter-spacing: 0.4px; margin-bottom: 6px; }}
    .stat-value {{ font-size: 26px; font-weight: 800; }}
    
    .boards-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(240px, 1fr)); gap: 14px; margin-top: 12px; }}
    .b-card {{
      background: #ffffff; border: 1px solid var(--border); border-radius: var(--r-md);
      overflow: hidden; cursor: pointer; transition: all 0.15s; box-shadow: var(--sh-xs);
    }}
    .b-card:hover {{ border-color: var(--blue); transform: translateY(-1px); box-shadow: var(--sh-sm); }}
    .b-thumb {{
      height: 95px; background: var(--surface-subtle); border-bottom: 1px solid var(--border);
      padding: 12px; display: flex; align-items: center; justify-content: center; gap: 6px;
    }}
    .b-node {{ background: #ffffff; border: 1px solid var(--border); padding: 3px 8px; border-radius: 4px; font-size: 9.5px; font-weight: 600; }}
    .b-body {{ padding: 12px 14px; }}
    .b-title {{ font-size: 13.5px; font-weight: 700; margin-bottom: 4px; }}
    .b-meta {{ font-size: 11px; color: var(--text-subtle); }}
  </style>
</head>
<body>

<div class="shell">
  <div class="sidebar">
    <div class="sidebar-logo">
      <svg viewBox="0 0 26 26" fill="none"><rect width="26" height="26" rx="6" fill="#2563eb"/><rect x="5" y="5" width="7" height="7" rx="1.5" fill="#fff"/><rect x="14" y="5" width="7" height="7" rx="1.5" fill="rgba(255,255,255,.5)"/><rect x="5" y="14" width="7" height="7" rx="1.5" fill="rgba(255,255,255,.5)"/><rect x="14" y="14" width="7" height="7" rx="1.5" fill="#fff"/></svg>
      Prompt Studio
    </div>
    <div class="sidebar-nav">
      <div class="sidebar-section-label">Workspace</div>
      <a href="/dashboard" class="sidebar-item active">Dashboard</a>
      <a href="/board" class="sidebar-item">Canvas Boards</a>
      <a href="/templates" class="sidebar-item">Templates</a>
      <div class="sidebar-section-label">System</div>
      <a href="/guide" class="sidebar-item">Documentation</a>
      <a href="/pricing" class="sidebar-item">Upgrade</a>
    </div>
    <div class="sidebar-footer">
      <div class="user-row">
        <div class="user-avatar">PS</div>
        <div class="user-info">
          <div class="user-name">Engineering Org</div>
          <div class="user-plan">Starter Plan</div>
        </div>
        <a href="/login" title="Sign out" style="color: var(--text-subtle); font-size: 11.5px; font-weight: 500; text-decoration: none; padding: 4px 6px; border-radius: 4px; border: 1px solid var(--border);">Logout</a>
      </div>
    </div>
  </div>

  <div class="main">
    <div class="topbar">
      <div class="topbar-title">Dashboard</div>
      <div class="topnav-actions">
        <a href="/templates" class="btn btn-ghost">Browse Templates</a>
        <a href="/board" class="btn btn-primary">New Board</a>
      </div>
    </div>
    <div class="content">
      <div class="stats">
        <div class="stat">
          <div class="stat-label">Canvas Boards</div>
          <div class="stat-value">3</div>
        </div>
        <div class="stat">
          <div class="stat-label">Total Nodes</div>
          <div class="stat-value">47</div>
        </div>
        <div class="stat">
          <div class="stat-label">Exports</div>
          <div class="stat-value">12</div>
        </div>
        <div class="stat">
          <div class="stat-label">Active Skills</div>
          <div class="stat-value">5</div>
        </div>
      </div>

      <div>
        <div style="font-size: 14.5px; font-weight: 700;">Recent Architecture Boards</div>
        <div class="boards-grid">
          <a href="/board?template=b2b_saas" class="b-card">
            <div class="b-thumb">
              <div class="b-node">Cloudflare</div>
              <div class="b-node">FastAPI</div>
              <div class="b-node">Stripe</div>
            </div>
            <div class="b-body">
              <div class="b-title">B2B Multi-Tenant SaaS</div>
              <div class="b-meta">Updated 2h ago &bull; 14 nodes</div>
            </div>
          </a>
          <a href="/board?template=event_streaming" class="b-card">
            <div class="b-thumb">
              <div class="b-node">Kafka</div>
              <div class="b-node">Flink</div>
              <div class="b-node">Avro</div>
            </div>
            <div class="b-body">
              <div class="b-title">Event Streaming Pipeline</div>
              <div class="b-meta">Updated 1d ago &bull; 13 nodes</div>
            </div>
          </a>
          <a href="/board?template=zero_trust_iam" class="b-card">
            <div class="b-thumb">
              <div class="b-node">mTLS</div>
              <div class="b-node">SPIFFE</div>
              <div class="b-node">OPA</div>
            </div>
            <div class="b-body">
              <div class="b-title">Zero-Trust IAM</div>
              <div class="b-meta">Updated 3d ago &bull; 14 nodes</div>
            </div>
          </a>
        </div>
      </div>
    </div>
  </div>
</div>

</body>
</html>"""

# ---------------------------------------------------------------------------
# 6. LOGIN PAGE – Authentic Minimalist Developer Authentication
# ---------------------------------------------------------------------------
LOGIN_HTML = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Sign in &ndash; Prompt Studio</title>
  {COMMON_CSS}
  <style>
    html, body {{
      min-height: 100vh;
      background: var(--bg);
      display: flex;
      flex-direction: column;
    }}
    .auth-container {{
      flex: 1;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      padding: 40px 20px;
    }}
    .auth-card {{
      width: 100%;
      max-width: 400px;
      background: #ffffff;
      border: 1px solid var(--border);
      border-radius: var(--r-md);
      box-shadow: var(--sh-sm);
      padding: 32px 36px;
    }}
    .auth-brand {{
      display: flex;
      align-items: center;
      gap: 10px;
      margin-bottom: 24px;
      text-decoration: none;
    }}
    .auth-brand svg {{ width: 28px; height: 28px; }}
    .auth-brand-name {{
      font-size: 16px;
      font-weight: 800;
      color: var(--blue);
      letter-spacing: -0.3px;
    }}
    .auth-title {{
      font-size: 22px;
      font-weight: 800;
      letter-spacing: -0.5px;
      color: var(--text);
      margin-bottom: 6px;
    }}
    .auth-desc {{
      font-size: 13px;
      color: var(--text-muted);
      line-height: 1.5;
      margin-bottom: 24px;
    }}
    .sso-buttons {{
      display: flex;
      flex-direction: column;
      gap: 10px;
      margin-bottom: 20px;
    }}
    .btn-sso-action {{
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 10px;
      width: 100%;
      padding: 9px 16px;
      background: #ffffff;
      border: 1px solid var(--border-strong);
      border-radius: var(--r-sm);
      font-size: 13px;
      font-weight: 600;
      color: var(--text);
      cursor: pointer;
      transition: all 0.15s;
    }}
    .btn-sso-action:hover {{
      background: var(--surface-subtle);
      border-color: var(--blue);
    }}
    .btn-sso-action svg {{ width: 16px; height: 16px; flex-shrink: 0; }}
    .auth-divider {{
      display: flex;
      align-items: center;
      gap: 12px;
      margin: 20px 0;
      color: var(--text-subtle);
      font-size: 11px;
      font-weight: 700;
      letter-spacing: 0.5px;
      text-transform: uppercase;
    }}
    .auth-divider::before, .auth-divider::after {{
      content: '';
      flex: 1;
      height: 1px;
      background: var(--border);
    }}
    .form-group {{
      display: flex;
      flex-direction: column;
      gap: 6px;
      margin-bottom: 16px;
    }}
    .form-label-row {{
      display: flex;
      justify-content: space-between;
      align-items: center;
    }}
    .form-label {{
      font-size: 12.5px;
      font-weight: 600;
      color: var(--text);
    }}
    .form-link {{
      font-size: 12px;
      color: var(--blue);
      text-decoration: none;
      font-weight: 500;
    }}
    .form-link:hover {{ text-decoration: underline; }}
    .form-input {{
      width: 100%;
      padding: 9px 12px;
      background: #ffffff;
      border: 1px solid var(--border);
      border-radius: var(--r-sm);
      font-size: 13.5px;
      color: var(--text);
      font-family: var(--font);
      transition: border-color 0.15s, box-shadow 0.15s;
      outline: none;
    }}
    .form-input:focus {{
      border-color: var(--blue);
      box-shadow: 0 0 0 3px rgba(37,99,235,0.12);
    }}
    .form-check-row {{
      display: flex;
      align-items: center;
      gap: 8px;
      margin-bottom: 20px;
      font-size: 12.5px;
      color: var(--text-muted);
      cursor: pointer;
    }}
    .btn-submit {{
      width: 100%;
      padding: 10px 16px;
      background: var(--blue);
      color: #ffffff;
      border: 1px solid var(--blue);
      border-radius: var(--r-sm);
      font-size: 13.5px;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.15s;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 8px;
    }}
    .btn-submit:hover {{
      background: var(--blue-hover);
      border-color: var(--blue-hover);
      box-shadow: 0 2px 8px rgba(37,99,235,0.25);
    }}
    .demo-bar {{
      margin-top: 18px;
      padding: 10px 12px;
      background: var(--surface-subtle);
      border: 1px dashed var(--border-strong);
      border-radius: var(--r-sm);
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 8px;
    }}
    .demo-bar-text {{
      font-size: 11.5px;
      color: var(--text-muted);
    }}
    .demo-btn {{
      padding: 4px 9px;
      background: #ffffff;
      border: 1px solid var(--border);
      border-radius: 4px;
      font-size: 11px;
      font-weight: 600;
      color: var(--blue);
      cursor: pointer;
      white-space: nowrap;
    }}
    .demo-btn:hover {{ background: var(--blue-light); border-color: var(--blue); }}
    .auth-footer {{
      margin-top: 20px;
      text-align: center;
      font-size: 12.5px;
      color: var(--text-muted);
    }}
    .auth-footer a {{
      color: var(--blue);
      font-weight: 600;
      text-decoration: none;
    }}
    .auth-footer a:hover {{ text-decoration: underline; }}
    .back-home {{
      margin-top: 24px;
      text-align: center;
    }}
    .back-home a {{
      font-size: 12px;
      color: var(--text-subtle);
      text-decoration: none;
      display: inline-flex;
      align-items: center;
      gap: 4px;
    }}
    .back-home a:hover {{ color: var(--text); }}
    .alert-error {{
      background: #fef2f2;
      border: 1px solid #fecaca;
      border-radius: var(--r-sm);
      padding: 9px 12px;
      font-size: 12.5px;
      color: var(--red);
      margin-bottom: 16px;
      display: none;
    }}
    .saml-box {{
      display: none;
      margin-top: 14px;
      padding: 12px;
      background: var(--surface-subtle);
      border: 1px solid var(--border);
      border-radius: var(--r-sm);
    }}
  </style>
</head>
<body>

<div class="auth-container">
  <div class="auth-card">
    <a href="/" class="auth-brand">
      <svg viewBox="0 0 26 26" fill="none">
        <rect width="26" height="26" rx="6" fill="#2563eb"/>
        <rect x="5" y="5" width="7" height="7" rx="1.5" fill="#fff"/>
        <rect x="14" y="5" width="7" height="7" rx="1.5" fill="rgba(255,255,255,.5)"/>
        <rect x="5" y="14" width="7" height="7" rx="1.5" fill="rgba(255,255,255,.5)"/>
        <rect x="14" y="14" width="7" height="7" rx="1.5" fill="#fff"/>
      </svg>
      <span class="auth-brand-name">Prompt Studio</span>
    </a>

    <h1 class="auth-title">Sign in to workspace</h1>
    <p class="auth-desc">Access architecture graphs, typed data models, and prompt compiler specs.</p>

    <div id="auth-alert" class="alert-error"></div>

    <div class="sso-buttons">
      <button type="button" class="btn-sso-action" onclick="loginWithOAuth('github')">
        <svg viewBox="0 0 24 24" fill="currentColor">
          <path fill-rule="evenodd" clip-rule="evenodd" d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.53 1.032 1.53 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z"/>
        </svg>
        Continue with GitHub
      </button>

      <button type="button" class="btn-sso-action" onclick="loginWithOAuth('google')">
        <svg viewBox="0 0 24 24">
          <path fill="#4285F4" d="M23.745 12.27c0-.7-.06-1.4-.19-2.07H12v4.51h6.6c-.29 1.52-1.14 2.82-2.4 3.68v3.05h3.88c2.27-2.09 3.66-5.17 3.66-9.17z"/>
          <path fill="#34A853" d="M12 24c3.24 0 5.95-1.08 7.93-2.91l-3.88-3.05c-1.08.72-2.45 1.16-4.05 1.16-3.12 0-5.77-2.1-6.72-4.93H1.25v3.15C3.26 21.36 7.33 24 12 24z"/>
          <path fill="#FBBC05" d="M5.28 14.27a7.18 7.18 0 010-4.54V6.58H1.25a11.96 11.96 0 000 10.84l4.03-3.15z"/>
          <path fill="#EA4335" d="M12 4.75c1.77 0 3.35.61 4.6 1.8l3.42-3.42C17.95 1.19 15.24 0 12 0 7.33 0 3.26 2.64 1.25 6.58l4.03 3.15c.95-2.83 3.6-4.98 6.72-4.98z"/>
        </svg>
        Continue with Google
      </button>
    </div>

    <div class="auth-divider">Or work email</div>

    <form id="login-form" onsubmit="handleEmailLogin(event)">
      <div class="form-group">
        <label class="form-label" for="login-email">Work Email</label>
        <input type="email" id="login-email" class="form-input" placeholder="name@company.com" required autocomplete="email">
      </div>

      <div class="form-group">
        <div class="form-label-row">
          <label class="form-label" for="login-password">Password</label>
          <a href="#" class="form-link" onclick="handleForgot(event)">Forgot?</a>
        </div>
        <input type="password" id="login-password" class="form-input" placeholder="••••••••••••" required autocomplete="current-password">
      </div>

      <label class="form-check-row">
        <input type="checkbox" id="remember-me" checked>
        <span>Remember this session for 30 days</span>
      </label>

      <button type="submit" id="btn-submit" class="btn-submit">
        <span>Sign In to Workspace</span>
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/></svg>
      </button>
    </form>

    <div class="demo-bar">
      <div class="demo-bar-text"><strong>Reviewer Access:</strong> Use pre-filled credentials</div>
      <button type="button" class="demo-btn" onclick="fillDemoCredentials()">Fill Demo</button>
    </div>

    <div style="margin-top: 14px; text-align: center;">
      <a href="#" onclick="toggleSaml(event)" style="font-size: 11.5px; color: var(--text-muted); text-decoration: none;">&bull; Organization SAML / Okta SSO</a>
    </div>

    <div id="saml-drawer" class="saml-box">
      <div style="font-size: 11.5px; font-weight: 600; margin-bottom: 6px;">Enterprise Workspace Slug</div>
      <div style="display: flex; gap: 6px;">
        <input type="text" id="saml-slug" class="form-input" placeholder="acme" style="font-size: 12px; padding: 6px 8px;">
        <button type="button" class="demo-btn" onclick="loginSaml()">SSO &rarr;</button>
      </div>
    </div>

    <div class="auth-footer">
      Don't have a workspace? <a href="/pricing">Create workspace</a>
    </div>
  </div>

  <div class="back-home">
    <a href="/">&larr; Return to Prompt Studio home</a>
  </div>
</div>

<script>
  function fillDemoCredentials() {{
    document.getElementById('login-email').value = 'architect@promptstudio.dev';
    document.getElementById('login-password').value = 'ProductionPass2026!';
    document.getElementById('login-email').focus();
  }}

  function toggleSaml(e) {{
    e.preventDefault();
    const d = document.getElementById('saml-drawer');
    d.style.display = (d.style.display === 'block') ? 'none' : 'block';
  }}

  function loginSaml() {{
    const slug = document.getElementById('saml-slug').value.trim() || 'default';
    showSuccess('Redirecting to Okta / SAML provider for ' + slug + '...');
    setTimeout(() => {{
      location.href = '/dashboard';
    }}, 600);
  }}

  function loginWithOAuth(provider) {{
    showSuccess('Authenticating via ' + provider + ' OIDC...');
    localStorage.setItem('ps_user', provider + '_architect');
    setTimeout(() => {{
      location.href = '/dashboard';
    }}, 500);
  }}

  function handleForgot(e) {{
    e.preventDefault();
    const email = document.getElementById('login-email').value.trim();
    if (!email) {{
      showError('Please enter your work email address above first.');
      document.getElementById('login-email').focus();
      return;
    }}
    showSuccess('Password recovery link dispatched to ' + email + ' (RFC 9457 token).');
  }}

  function showError(msg) {{
    const a = document.getElementById('auth-alert');
    a.style.display = 'block';
    a.style.background = '#fef2f2';
    a.style.borderColor = '#fecaca';
    a.style.color = '#dc2626';
    a.textContent = msg;
  }}

  function showSuccess(msg) {{
    const a = document.getElementById('auth-alert');
    a.style.display = 'block';
    a.style.background = '#ecfdf5';
    a.style.borderColor = '#a7f3d0';
    a.style.color = '#059669';
    a.textContent = msg;
  }}

  function handleEmailLogin(e) {{
    e.preventDefault();
    const email = document.getElementById('login-email').value.trim();
    const pwd = document.getElementById('login-password').value;
    const btn = document.getElementById('btn-submit');

    if (!email || !pwd) {{
      showError('Please provide both work email and workspace password.');
      return;
    }}
    if (pwd.length < 6) {{
      showError('Password must be at least 6 characters.');
      return;
    }}

    btn.disabled = true;
    btn.innerHTML = '<span>Verifying credentials...</span>';
    localStorage.setItem('ps_user', email);
    localStorage.setItem('ps_authenticated', 'true');

    setTimeout(() => {{
      const params = new URLSearchParams(location.search);
      const target = params.get('redirect') || '/dashboard';
      location.href = target;
    }}, 450);
  }}
</script>

</body>
</html>"""
