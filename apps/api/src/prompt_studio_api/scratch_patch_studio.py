"""Patch studio_html.py:
1. Add Image Attachment tool button to left toolbar
2. Add Skills tab to right context drawer
3. Add JS: image element rendering + skills panel content + keyboard shortcut I
"""
import re

src = "apps/api/src/prompt_studio_api/studio_html.py"

with open(src, encoding="utf-8") as f:
    html = f.read()

original_len = len(html)

# ── PATCH 1: Add image upload button after Eraser button (before </div> that closes toolbar)
# Target: the eraser button's closing </button>\n    </div> sequence
IMAGE_TOOL_BTN = """
      <!-- Image Attachment -->
      <button class="tool-btn" id="tool-image" title="Attach Image (I)" onclick="triggerImageUpload()">
        <svg viewBox="0 0 24 24"><rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="8.5" cy="8.5" r="1.5"/><polyline points="21 15 16 10 5 21"/></svg>
        <span class="tooltip">Attach Image (I)</span>
      </button>
      <input type="file" id="image-upload-input" accept="image/*" style="display:none" onchange="handleImageUpload(event)">"""

ERASER_END = """        <span class="tooltip">Eraser (E)</span>
      </button>
    </div>"""

if ERASER_END in html:
    html = html.replace(ERASER_END, f"""        <span class="tooltip">Eraser (E)</span>
      </button>
{IMAGE_TOOL_BTN}
    </div>""", 1)
    print("PATCH 1 OK – image tool button added")
else:
    print("PATCH 1 FAILED – eraser end marker not found")

# ── PATCH 2: Add Skills tab to drawer tab strip (before Audit Trail)
HISTORY_TAB = """      <div class="drawer-tab" data-tab="history" onclick="switchDrawerTab('history')">Audit Trail</div>"""
SKILLS_AND_HISTORY = """      <div class="drawer-tab" data-tab="skills" onclick="switchDrawerTab('skills')">Skills</div>
      <div class="drawer-tab" data-tab="history" onclick="switchDrawerTab('history')">Audit Trail</div>"""

if HISTORY_TAB in html:
    html = html.replace(HISTORY_TAB, SKILLS_AND_HISTORY, 1)
    print("PATCH 2 OK – Skills tab added")
else:
    print("PATCH 2 FAILED – history tab marker not found")

# ── PATCH 3: Add JS functions — image upload + skills panel content
# Insert before closing </script> tag (last one)
JS_ADDITIONS = r"""
// ── IMAGE ATTACHMENT ──────────────────────────────────────────
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
      status: 'Active',
      color: '#3b82f6'
    },
    {
      id: 'postgres-rls-auditor',
      name: 'PostgreSQL RLS Auditor',
      desc: 'Checks every table for row-level security policies. Reports tables missing RLS in multi-tenant schemas.',
      keywords: ['postgres', 'rls', 'security', 'multi-tenant'],
      status: 'Active',
      color: '#10b981'
    },
    {
      id: 'stripe-webhook-validator',
      name: 'Stripe Webhook Validator',
      desc: 'Verifies HMAC signature on every incoming Stripe event. Rejects replayed events older than 5 minutes.',
      keywords: ['stripe', 'webhook', 'hmac', 'billing'],
      status: 'Active',
      color: '#f59e0b'
    },
    {
      id: 'fhir-compliance-checker',
      name: 'FHIR Compliance Checker',
      desc: 'Validates FHIR R4 resource bundles against HL7 profiles. Flags PHI fields missing encryption annotation.',
      keywords: ['fhir', 'hl7', 'hipaa', 'healthcare', 'phi'],
      status: 'Draft',
      color: '#8b5cf6'
    },
    {
      id: 'zero-trust-policy-enforcer',
      name: 'Zero-Trust Policy Enforcer',
      desc: 'Evaluates OPA Rego policies for every service-to-service call. Denies requests without valid SPIFFE SVID.',
      keywords: ['opa', 'spiffe', 'zero-trust', 'mtls'],
      status: 'Active',
      color: '#ef4444'
    }
  ];

  const cards = skills.map(s => `
    <div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:8px;padding:12px;margin-bottom:10px">
      <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:6px">
        <span style="font-size:12px;font-weight:700;color:#0f172a">${s.name}</span>
        <span style="padding:2px 8px;border-radius:4px;font-size:9.5px;font-weight:700;background:${s.status==='Active'?'rgba(16,185,129,.12)':'rgba(245,158,11,.12)'};color:${s.status==='Active'?'#059669':'#d97706'}">${s.status}</span>
      </div>
      <div style="font-size:11.5px;color:#64748b;line-height:1.5;margin-bottom:8px">${s.desc}</div>
      <div style="display:flex;flex-wrap:wrap;gap:4px;margin-bottom:8px">
        ${s.keywords.map(k => `<span style="padding:2px 7px;border-radius:4px;font-size:10px;background:#eff6ff;color:#2563eb;font-family:monospace">${k}</span>`).join('')}
      </div>
      <div style="display:flex;gap:6px">
        <button onclick="console.log('run:${s.id}')" style="padding:4px 10px;border-radius:5px;border:1px solid ${s.color};color:${s.color};background:transparent;font-size:11px;font-weight:600;cursor:pointer">Run</button>
        <button onclick="console.log('view:${s.id}')" style="padding:4px 10px;border-radius:5px;border:1px solid #e2e8f0;color:#64748b;background:transparent;font-size:11px;font-weight:600;cursor:pointer">View</button>
      </div>
    </div>
  `).join('');

  return `
    <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:14px">
      <div>
        <div style="font-size:13px;font-weight:700;color:#0f172a">Skills Registry</div>
        <div style="font-size:11px;color:#94a3b8;margin-top:2px">Structured engineering skills</div>
      </div>
      <button onclick="alert('New skill dialog')" style="padding:5px 11px;border-radius:6px;background:#2563eb;color:#fff;border:none;font-size:11.5px;font-weight:600;cursor:pointer">+ New</button>
    </div>
    ${cards}
  `;
}
"""

# Also patch renderImageElement and switchDrawerTab to handle skills/image
JS_RENDER_IMAGE = r"""
// ── RENDER IMAGE ELEMENT ─────────────────────────────────────
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
"""

# Find the last </script> and insert before it
last_script_end = html.rfind('</script>')
if last_script_end != -1:
    html = html[:last_script_end] + JS_ADDITIONS + JS_RENDER_IMAGE + '\n' + html[last_script_end:]
    print("PATCH 3 OK – JS functions added")
else:
    print("PATCH 3 FAILED – </script> not found")

# ── PATCH 4: Hook renderElements to handle 'image' type
# Find renderElements function and add image case
IMAGE_CASE = """    if (el.type === 'image') { world.appendChild(renderImageElement(el)); return; }"""

# Find where renderElements dispatches by type (look for 'sticky' type dispatch)
STICKY_DISPATCH = "    if (el.type === 'sticky') {"
if STICKY_DISPATCH in html:
    html = html.replace(STICKY_DISPATCH, IMAGE_CASE + "\n    if (el.type === 'sticky') {", 1)
    print("PATCH 4 OK – image type dispatch added to renderElements")
else:
    print("PATCH 4 FAILED – sticky dispatch not found, trying alternate")
    # Try alternate
    alt = "if (el.type === 'sticky')"
    if alt in html:
        html = html.replace(alt, f"{IMAGE_CASE}\n    {alt}", 1)
        print("PATCH 4 OK (alt) – image type dispatch added")
    else:
        print("PATCH 4 FAILED – no sticky type dispatch found")

# ── PATCH 5: Hook switchDrawerTab to render skills panel
# Find the existing switchDrawerTab function and add skills case
SKILLS_CASE = """    if (tab === 'skills') { body.innerHTML = getSkillsPanelHTML(); return; }"""

# Find history case in switchDrawerTab
HISTORY_CASE_OLD = "    if (tab === 'history') {"
if HISTORY_CASE_OLD in html:
    html = html.replace(HISTORY_CASE_OLD, SKILLS_CASE + "\n    if (tab === 'history') {", 1)
    print("PATCH 5 OK – skills case added to switchDrawerTab")
else:
    print("PATCH 5 FAILED – history case not found in switchDrawerTab")

# ── PATCH 6: Add keyboard shortcut I for image upload
# Find the keydown handler where other shortcuts are set
KEY_I_SHORTCUT = "    if (k === 'i' || k === 'I') { triggerImageUpload(); return; }"
# Find nearby shortcut 't' or 'T' for text
TEXT_SHORTCUT = "if (k === 't' || k === 'T')"
if TEXT_SHORTCUT in html:
    # Find the line and insert after
    idx = html.find(TEXT_SHORTCUT)
    # Find end of that if-block line
    end = html.find('\n', idx)
    html = html[:end+1] + "    " + KEY_I_SHORTCUT + "\n" + html[end+1:]
    print("PATCH 6 OK – keyboard shortcut I added")
else:
    print("PATCH 6 SKIP – text shortcut pattern not found, keyboard I skipped")

# Write back
with open(src, 'w', encoding='utf-8') as f:
    f.write(html)

print(f"\nDone. Original: {original_len} bytes → Patched: {len(html)} bytes")
