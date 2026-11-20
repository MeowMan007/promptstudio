"""
Regression test suite for the 12 Prompt Studio Project Blueprints.
Tests canonical registry, API endpoints, catalogue consistency,
JS generator dispatch, ERD normalization, wireframe screen types,
graph integrity, and absence of unsupported certification claims.
"""
from __future__ import annotations

import json
import re
import subprocess
import tempfile
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from prompt_studio_api.main import create_app
from prompt_studio_api.pages_html import TEMPLATES_HTML
from prompt_studio_api.studio_html import STUDIO_HTML
from prompt_studio_api.templates_registry import (
    TEMPLATES_BY_ID,
    TEMPLATES_REGISTRY,
    get_template,
)

EXPECTED_12_IDS = [
    "b2b_saas",
    "fintech_ledger",
    "event_streaming",
    "ecommerce_marketplace",
    "developer_platform",
    "collab_workspace",
    "healthcare_portal",
    "zero_trust_iam",
    "ai_agent_rag",
    "global_payroll",
    "legaltech_clm",
    "logistics_supply_chain",
]

FORBIDDEN_CERTIFICATION_CLAIMS = [
    r"\bHIPAA\s+certified\b",
    r"\bPCI\s+compliant\b",
    r"\bSOC\s*2\s+Type\s+II\b",
    r"\bFedRAMP\s+ready\b",
    r"\b100%\s+deterministic\b",
    r"\bexactly-once\s+end-to-end\b",
]


class TestCanonicalRegistry:
    """H1. Canonical Template Registry tests."""

    def test_exactly_12_templates_registered(self) -> None:
        assert len(TEMPLATES_REGISTRY) == 12
        assert len(TEMPLATES_BY_ID) == 12

    def test_all_stable_ids_present(self) -> None:
        registered_ids = [t.id for t in TEMPLATES_REGISTRY]
        assert registered_ids == EXPECTED_12_IDS

    def test_metadata_fields_non_empty(self) -> None:
        for tpl in TEMPLATES_REGISTRY:
            assert tpl.id, "ID must not be empty"
            assert tpl.title, f"{tpl.id}: title must not be empty"
            assert tpl.summary, f"{tpl.id}: summary must not be empty"
            assert tpl.category in {"saas", "fintech", "data", "ecommerce", "dev", "health", "security", "ai", "ops"}
            assert tpl.profile, f"{tpl.id}: profile must not be empty"
            assert tpl.complexity in {"Intermediate", "Advanced", "Specialized"}
            assert len(tpl.tags) >= 3, f"{tpl.id}: must have at least 3 technical tags"
            assert len(tpl.capabilities) >= 3, f"{tpl.id}: must have at least 3 capabilities"
            assert tpl.scope_notes, f"{tpl.id}: scope notes must document assumptions"

    def test_no_unsupported_certification_claims_in_registry(self) -> None:
        for tpl in TEMPLATES_REGISTRY:
            full_text = f"{tpl.title} {tpl.summary} {tpl.scope_notes} {' '.join(tpl.capabilities)}"
            for pattern in FORBIDDEN_CERTIFICATION_CLAIMS:
                match = re.search(pattern, full_text, re.IGNORECASE)
                assert not match, f"{tpl.id} contains forbidden claim '{match.group()}'"

    def test_get_template_helper(self) -> None:
        assert get_template("b2b_saas") is not None
        assert get_template("developer_platform") is not None
        assert get_template("collab_workspace") is not None
        assert get_template("healthcare_portal") is not None
        assert get_template("nonexistent_blueprint") is None


class TestTemplatesCatalogueConsistency:
    """Verify in-canvas modal and /templates page match canonical registry."""

    def test_templates_page_contains_all_12_links(self) -> None:
        for tpl_id in EXPECTED_12_IDS:
            assert f"template={tpl_id}" in TEMPLATES_HTML, f"/templates missing link for {tpl_id}"

    def test_in_canvas_modal_contains_all_12_cards(self) -> None:
        for tpl_id in EXPECTED_12_IDS:
            assert f"applyTemplate('{tpl_id}'" in STUDIO_HTML, f"Modal missing applyTemplate for {tpl_id}"

    def test_no_unsupported_claims_in_templates_page(self) -> None:
        for pattern in FORBIDDEN_CERTIFICATION_CLAIMS:
            match = re.search(pattern, TEMPLATES_HTML, re.IGNORECASE)
            assert not match, f"TEMPLATES_HTML contains forbidden claim '{match.group()}'"


class TestAPIEndpoints:
    """Test /api/v1/templates routes."""

    @pytest.fixture
    def client(self) -> TestClient:
        app = create_app()
        return TestClient(app)

    def test_list_templates(self, client: TestClient) -> None:
        resp = client.get("/api/v1/templates")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 12
        ids = [item["id"] for item in data]
        assert ids == EXPECTED_12_IDS

    def test_get_template_by_id(self, client: TestClient) -> None:
        resp = client.get("/api/v1/templates/developer_platform")
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == "developer_platform"
        assert "Developer API" in data["title"]
        assert len(data["capabilities"]) >= 3

    def test_get_template_not_found(self, client: TestClient) -> None:
        resp = client.get("/api/v1/templates/unknown_template_xyz")
        assert resp.status_code == 404


class TestSharedRenderersAndContracts:
    """Part E & H3. ERD normalization & wireframe screen types."""

    def test_erd_renderer_normalizes_columns_and_fields(self) -> None:
        assert "(item.columns || item.fields || [])" in STUDIO_HTML

    def test_erd_renderer_normalizes_pk_and_fk_aliases(self) -> None:
        assert "(col.isPk||col.isPK)" in STUDIO_HTML
        assert "(col.isFk||col.isForeignKey)" in STUDIO_HTML

    def test_wireframe_screen_types_handled(self) -> None:
        required_screen_types = [
            "dashboard", "onboarding", "developer_portal", "vendor_portal",
            "pricing", "ai_chat", "telemetry_stream", "checkout",
            "form", "list", "chat", "editor", "map",
        ]
        for st in required_screen_types:
            assert f"sType === '{st}'" in STUDIO_HTML or f"screenType === '{st}'" in STUDIO_HTML, (
                f"Wireframe screenType '{st}' not explicitly handled in renderer"
            )


class TestJSExecutionAndGraphIntegrity:
    """Part H2 & H4. Node.js execution of all 12 templates."""

    def test_js_syntax_clean(self) -> None:
        scripts = re.findall(r"<script>(.*?)</script>", STUDIO_HTML, re.DOTALL)
        all_js = "\n".join(scripts)
        with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8") as f:
            f.write(all_js)
            temp_path = f.name
        try:
            result = subprocess.run(["node", "--check", temp_path], capture_output=True, text=True)
            assert result.returncode == 0, f"JS syntax check error: {result.stderr[:400]}"
        finally:
            Path(temp_path).unlink(missing_ok=True)

    def test_js_simulation_all_12_templates(self) -> None:
        """Run Node simulation to test all 12 template generations."""
        sim_script = f"""
const fs = require('fs');

// Mock DOM & Canvas state
global.window = {{ location: {{ search: '' }}, addEventListener: () => {{}} }};
const makeMockEl = () => ({{
  value: '',
  innerText: '',
  innerHTML: '',
  style: {{}},
  dataset: {{}},
  classList: {{ remove: () => {{}}, add: () => {{}}, contains: () => false }},
  getBoundingClientRect: () => ({{ left: 0, top: 0, width: 1200, height: 800, right: 1200, bottom: 800 }}),
  getContext: () => ({{ clearRect: () => {{}}, fillRect: () => {{}}, strokeRect: () => {{}}, beginPath: () => {{}}, moveTo: () => {{}}, lineTo: () => {{}}, stroke: () => {{}}, fill: () => {{}} }}),
  appendChild: () => {{}},
  setAttribute: () => {{}},
  getAttribute: () => '',
  querySelector: makeMockEl,
  querySelectorAll: () => [],
  addEventListener: () => {{}}
}});
global.document = {{
  getElementById: makeMockEl,
  querySelectorAll: () => [],
  addEventListener: () => {{}},
  createElement: makeMockEl,
  createElementNS: makeMockEl
}};
global.showNotification = () => {{}};
global.closeBrainstormModal = () => {{}};
global.pushHistory = () => {{}};
global.fitToContent = () => {{}};
global.updateMinimap = () => {{}};
global.renderAll = () => {{}};

const html = fs.readFileSync('apps/api/src/prompt_studio_api/studio_html.py', 'utf8');
const scriptMatch = html.match(/<script>([\\s\\S]*?)<\\/script>/);
if (!scriptMatch) throw new Error('No script found');

// Eval script with inline verification to access internal board closure
const verifyCode = `
const templates = {repr(EXPECTED_12_IDS)};
const results = {{}};

templates.forEach(t => {{
  board.elements = [];
  board.frames = [];
  board.edges = [];
  applyTemplate(t, true);

  if (board.frames.length < 3) throw new Error(t + ': fewer than 3 frames: ' + board.frames.length);
  if (board.elements.length < 5) throw new Error(t + ': fewer than 5 elements: ' + board.elements.length);
  if (board.edges.length < 2) throw new Error(t + ': fewer than 2 edges: ' + board.edges.length);

  const ids = new Set();
  board.frames.forEach(f => {{
    if (ids.has(f.id)) throw new Error(t + ': duplicate frame ID ' + f.id);
    ids.add(f.id);
  }});
  board.elements.forEach(e => {{
    if (ids.has(e.id)) throw new Error(t + ': duplicate element ID ' + e.id);
    ids.add(e.id);
  }});
  board.edges.forEach(ed => {{
    if (ids.has(ed.id)) throw new Error(t + ': duplicate edge ID ' + ed.id);
    ids.add(ed.id);
  }});

  board.edges.forEach(ed => {{
    if (!ids.has(ed.from)) throw new Error(t + ': edge from ' + ed.from + ' does not exist');
    if (!ids.has(ed.to)) throw new Error(t + ': edge to ' + ed.to + ' does not exist');
  }});

  board.elements.filter(e => e.type === 'erd').forEach(erd => {{
    const cols = erd.columns || erd.fields || [];
    if (cols.length === 0) throw new Error(t + ': ERD ' + erd.id + ' has no columns or fields');
  }});

  results[t] = {{ frames: board.frames.length, elements: board.elements.length, edges: board.edges.length }};
}});

// Test unknown template produces safe error state
board.elements = [];
board.frames = [];
board.edges = [];
applyTemplate('nonexistent_xyz', true);
if (!board.frames[0].title.includes('Unknown Blueprint')) {{
  throw new Error('Unknown template did not produce error state');
}}

console.log(JSON.stringify(results));
`;

eval(scriptMatch[1] + '\\n' + verifyCode);
"""
        with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8") as f:
            f.write(sim_script)
            sim_path = f.name
        try:
            result = subprocess.run(["node", sim_path], capture_output=True, text=True)
            assert result.returncode == 0, f"Node simulation error:\n{result.stderr}\n{result.stdout}"
            sim_data = json.loads(result.stdout.strip())
            assert len(sim_data) == 12
            for tpl_id in EXPECTED_12_IDS:
                assert tpl_id in sim_data
                assert sim_data[tpl_id]["frames"] >= 3
                assert sim_data[tpl_id]["elements"] >= 5
                assert sim_data[tpl_id]["edges"] >= 2
        finally:
            Path(sim_path).unlink(missing_ok=True)
