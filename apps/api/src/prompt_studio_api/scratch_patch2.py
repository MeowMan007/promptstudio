"""Second-pass patch for studio_html.py:
- Patch 4: Add image type handling in renderElements
- Patch 5: Add skills case in updateDrawerContent
- Patch 6: Add keyboard shortcut I
"""

src = "apps/api/src/prompt_studio_api/studio_html.py"

with open(src, encoding="utf-8") as f:
    html = f.read()

original_len = len(html)

# ── PATCH 4: Add image element handling in renderElements
# Target the querySelector cleanup line + elements.forEach dispatch
OLD_RENDER = "document.querySelectorAll('.sticky-note, .canvas-shape, .arch-node, .erd-table, .typed-card, .wireframe-screen').forEach(el => el.remove());"
NEW_RENDER = "document.querySelectorAll('.sticky-note, .canvas-shape, .arch-node, .erd-table, .typed-card, .wireframe-screen, .image-element').forEach(el => el.remove());"

if OLD_RENDER in html:
    html = html.replace(OLD_RENDER, NEW_RENDER, 1)
    print("PATCH 4a OK – image-element added to cleanup selector")
else:
    print("PATCH 4a FAIL")

# Target the dispatch inside forEach — look for 'item.type === .sticky.'
OLD_DISPATCH = "if (item.type === 'sticky') {"
NEW_DISPATCH = """if (item.type === 'image') {
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
        } else if (item.type === 'sticky') {"""

if OLD_DISPATCH in html:
    html = html.replace(OLD_DISPATCH, NEW_DISPATCH, 1)
    print("PATCH 4b OK – image dispatch added to renderElements")
else:
    print("PATCH 4b FAIL – could not find sticky dispatch")

# ── PATCH 5: Add skills case in updateDrawerContent (before history case)
OLD_HIST = "board.activeDrawerTab === 'history') {"
NEW_HIST = """board.activeDrawerTab === 'skills') {
        title.innerText = 'Skills Registry';
        body.innerHTML = getSkillsPanelHTML();
      } else if (board.activeDrawerTab === 'history') {"""

if OLD_HIST in html:
    html = html.replace(OLD_HIST, NEW_HIST, 1)
    print("PATCH 5 OK – skills case added to updateDrawerContent")
else:
    print("PATCH 5 FAIL")

# ── PATCH 6: Keyboard shortcut I -> triggerImageUpload
# Find the keydown handler — look for setTool('pan') shortcut for H key
OLD_KEY = "if (k === 'h' || k === 'H') { setTool('pan'); return; }"
NEW_KEY = """if (k === 'h' || k === 'H') { setTool('pan'); return; }
    if (k === 'i' || k === 'I') { triggerImageUpload(); return; }"""

if OLD_KEY in html:
    html = html.replace(OLD_KEY, NEW_KEY, 1)
    print("PATCH 6 OK – keyboard I shortcut added")
else:
    # Try alternate: look for 'V' key for select
    OLD_KEY2 = "if (k === 'v' || k === 'V') { setTool('select'); return; }"
    NEW_KEY2 = """if (k === 'v' || k === 'V') { setTool('select'); return; }
    if (k === 'i' || k === 'I') { triggerImageUpload(); return; }"""
    if OLD_KEY2 in html:
        html = html.replace(OLD_KEY2, NEW_KEY2, 1)
        print("PATCH 6 OK (alt V key) – keyboard I shortcut added")
    else:
        print("PATCH 6 SKIP – no matching key handler found")

# Write back
with open(src, 'w', encoding='utf-8') as f:
    f.write(html)

print(f"\nDone. {original_len} -> {len(html)} bytes")
