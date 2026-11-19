"""Tests for TSK-090..TSK-100: Export document generators + validators.

Covers:
  - agents_md.py         (TSK-090/091)
  - ide_rules.py         (TSK-092)
  - requirements_doc.py  (TSK-093)
  - design_doc.py        (TSK-094)
  - tasks_doc.py         (TSK-095)
  - openapi.py           (TSK-096)
  - data_model.py        (TSK-097)
  - diagrams.py          (TSK-098)
  - exporters.py         (TSK-099)
  - import_validator.py  (TSK-100)
"""
import pytest
import json

from backend.app.export.agents_md import (
    ProjectContext as AgentsProjectContext,
    generate_agents_md,
    generate_nested_agents,
    generate_claude_md,
)
from backend.app.export.ide_rules import (
    ProjectContext as IDEProjectContext,
    CursorRule,
    CursorRuleType,
    generate_cursor_rules,
    generate_copilot_instructions,
)
from backend.app.export.requirements_doc import (
    Requirement,
    EARSPattern,
    generate_requirements_md,
)
from backend.app.export.design_doc import (
    DecisionArtifact,
    ADRStatus,
    Alternative,
    DesignSection,
    DiagramBlock,
    generate_adr,
    generate_design_md,
)
from backend.app.export.tasks_doc import (
    Task,
    TaskStatus,
    compute_waves,
    generate_tasks_md,
    generate_speckit_profile,
    generate_kiro_specs,
    CyclicDependencyError,
)
from backend.app.export.openapi import (
    APIInfo,
    APIEndpoint,
    HTTPMethod,
    APIParameter,
    APIResponse,
    generate_openapi,
    openapi_to_json,
    validate_openapi,
    assert_valid_openapi,
    OpenAPIValidationError,
)
from backend.app.export.data_model import (
    DataEntity,
    Column,
    ColumnType,
    Index,
    generate_sql_ddl,
    generate_dbml,
    assert_ddl_dbml_parity,
    ParityError,
)
from backend.app.export.diagrams import (
    EREntity,
    ERAttribute,
    ERRelation,
    FlowGraph,
    FlowNode,
    FlowEdge,
    generate_er_diagram,
    generate_flow_diagram,
    validate_mermaid,
    assert_valid_mermaid,
    MermaidValidationError,
    _safe_id,
)
from backend.app.export.exporters import (
    LLMSContext,
    DesignToken,
    SkillPackageExport,
    PromptAssetExport,
    PromptVersionExport,
    generate_llms_txt,
    export_design_tokens,
    export_skill_package,
    export_prompt_asset,
)
from backend.app.export.import_validator import (
    ImportPackage,
    CollisionStrategy,
    validate_import,
    round_trip_check,
    RoundTripError,
)


# ==========================================================================
# TSK-090/091 — agents_md.py
# ==========================================================================

class TestAgentsMd:
    def _project(self, **kwargs):
        defaults = dict(
            name="Prompt Studio",
            description="A prompt-native workspace",
            modules={"apps/web": "Frontend", "apps/api": "Backend"},
            commands={"make test": "Run test suite", "make lint": "Run linter"},
        )
        defaults.update(kwargs)
        return AgentsProjectContext(**defaults)

    def test_root_agents_md_has_six_core_areas(self):
        md = generate_agents_md(self._project())
        for section in ["Overview", "Commands", "Project Structure",
                        "Code Style & Boundaries", "Testing"]:
            assert section in md, f"Missing section: {section}"

    def test_root_agents_md_has_three_tier_boundaries(self):
        md = generate_agents_md(self._project())
        for tier in ["### Always", "### Ask First", "### Never"]:
            assert tier in md

    def test_root_agents_md_is_deterministic(self):
        p = self._project()
        assert generate_agents_md(p) == generate_agents_md(p)

    def test_root_agents_md_checksum_embedded(self):
        md = generate_agents_md(self._project())
        assert "Deterministic checksum:" in md

    def test_root_agents_md_commands_in_table(self):
        p = self._project(commands={"make test": "Run tests"})
        md = generate_agents_md(p)
        assert "`make test`" in md

    def test_root_agents_md_modules_listed(self):
        p = self._project()
        md = generate_agents_md(p)
        assert "apps/web" in md
        assert "apps/api" in md

    def test_root_agents_md_custom_boundaries(self):
        p = self._project(boundaries={
            "always": ["Custom always rule"],
            "ask_first": ["Custom ask rule"],
            "never": ["Custom never rule"],
        })
        md = generate_agents_md(p)
        assert "Custom always rule" in md
        assert "Custom ask rule" in md
        assert "Custom never rule" in md

    def test_root_agents_md_repo_url_included(self):
        p = self._project(repo_url="https://github.com/example/ps")
        md = generate_agents_md(p)
        assert "https://github.com/example/ps" in md

    # --- nested AGENTS.md (TSK-091) ---

    def test_nested_agents_generates_per_module(self):
        p = self._project()
        nested = generate_nested_agents(p)
        assert "apps/web/AGENTS.md" in nested
        assert "apps/api/AGENTS.md" in nested

    def test_nested_agents_has_nearest_wins_note(self):
        p = self._project()
        nested = generate_nested_agents(p)
        for content in nested.values():
            assert "Nearest-wins" in content or "nearest-wins" in content.lower()

    def test_nested_agents_no_contradictions_disclaimer(self):
        p = self._project()
        nested = generate_nested_agents(p)
        for content in nested.values():
            assert "does NOT contradict" in content

    def test_nested_agents_includes_module_rules(self):
        p = self._project()
        nested = generate_nested_agents(
            p, module_rules={"apps/web": ["No server-side code here"]}
        )
        assert "No server-side code here" in nested["apps/web/AGENTS.md"]

    def test_nested_agents_deterministic(self):
        p = self._project()
        assert generate_nested_agents(p) == generate_nested_agents(p)

    def test_claude_md_pointer_content(self):
        md = generate_claude_md()
        assert "AGENTS.md" in md
        assert "canonical" in md.lower() or "pointer" in md.lower() or "read" in md.lower()


# ==========================================================================
# TSK-092 — ide_rules.py
# ==========================================================================

class TestIDERules:
    def _project(self):
        return IDEProjectContext(
            name="Prompt Studio",
            description="A prompt-native workspace",
        )

    def test_cursor_rules_returns_mdc_files(self):
        rules = generate_cursor_rules(self._project())
        assert any(k.endswith(".mdc") for k in rules)

    def test_cursor_rules_paths_under_cursor_dir(self):
        rules = generate_cursor_rules(self._project())
        for path in rules:
            assert path.startswith(".cursor/rules/")

    def test_cursor_always_rule_has_correct_frontmatter(self):
        rules = generate_cursor_rules(self._project())
        always_key = ".cursor/rules/000-core-boundaries.mdc"
        assert always_key in rules
        content = rules[always_key]
        assert "alwaysApply: true" in content

    def test_cursor_auto_attached_has_globs(self):
        rules = generate_cursor_rules(self._project())
        python_key = ".cursor/rules/010-python-style.mdc"
        assert python_key in rules
        content = rules[python_key]
        assert "**/*.py" in content

    def test_cursor_frontmatter_has_description(self):
        rules = generate_cursor_rules(self._project())
        for content in rules.values():
            assert "description:" in content

    def test_cursor_extra_rules_included(self):
        extra = CursorRule(
            name="099-custom",
            rule_type=CursorRuleType.MANUAL,
            description="Custom rule",
            body="Do nothing weird.",
        )
        p = IDEProjectContext(name="X", extra_rules=[extra])
        rules = generate_cursor_rules(p)
        assert ".cursor/rules/099-custom.mdc" in rules
        assert "Do nothing weird." in rules[".cursor/rules/099-custom.mdc"]

    def test_copilot_instructions_has_project_name(self):
        content = generate_copilot_instructions(self._project())
        assert "Prompt Studio" in content

    def test_copilot_instructions_has_boundaries(self):
        content = generate_copilot_instructions(
            IDEProjectContext(
                name="X",
                boundaries={
                    "always": ["Validate first"],
                    "ask_first": ["Schema changes"],
                    "never": ["Commit secrets"],
                }
            )
        )
        assert "Validate first" in content
        assert "Schema changes" in content
        assert "Commit secrets" in content

    def test_copilot_instructions_deterministic(self):
        p = self._project()
        assert generate_copilot_instructions(p) == generate_copilot_instructions(p)

    def test_copilot_includes_commands(self):
        p = IDEProjectContext(name="X", commands={"make test": "Run tests"})
        content = generate_copilot_instructions(p)
        assert "make test" in content


# ==========================================================================
# TSK-093 — requirements_doc.py
# ==========================================================================

def _make_reqs() -> list[Requirement]:
    return [
        Requirement(
            req_id="REQ-001",
            title="System login",
            pattern=EARSPattern.UBIQUITOUS,
            action="authenticate users via OAuth2",
            priority="Must",
            acceptance_criteria=["Login redirects to OAuth provider", "Token stored securely"],
            linked_artifacts=["ART-001"],
            linked_tests=["TST-001"],
        ),
        Requirement(
            req_id="REQ-002",
            title="Session timeout",
            pattern=EARSPattern.EVENT_DRIVEN,
            action="invalidate the session",
            context="the user is idle for 30 minutes",
            priority="Must",
        ),
        Requirement(
            req_id="REQ-003",
            title="Invalid login",
            pattern=EARSPattern.UNWANTED_BEHAVIOR,
            action="display an error and lock the account after 5 attempts",
            context="the user enters incorrect credentials",
        ),
        Requirement(
            req_id="REQ-004",
            title="Admin mode",
            pattern=EARSPattern.STATE_DRIVEN,
            action="show the admin dashboard",
            context="the user has admin role",
        ),
        Requirement(
            req_id="REQ-005",
            title="Dark mode",
            pattern=EARSPattern.OPTIONAL_FEATURE,
            action="render the UI in dark colour scheme",
            context="dark mode",
        ),
    ]


class TestRequirementsDoc:
    def test_all_five_ears_patterns_rendered(self):
        md = generate_requirements_md(_make_reqs(), project_name="PS")
        for heading in [
            "Ubiquitous Requirements",
            "Event-Driven Requirements",
            "Unwanted Behaviour Requirements",
            "State-Driven Requirements",
            "Optional-Feature Requirements",
        ]:
            assert heading in md, f"Missing EARS section: {heading}"

    def test_requirement_ids_appear(self):
        md = generate_requirements_md(_make_reqs())
        for rid in ["REQ-001", "REQ-002", "REQ-003", "REQ-004", "REQ-005"]:
            assert rid in md

    def test_acceptance_criteria_rendered(self):
        md = generate_requirements_md(_make_reqs())
        assert "Login redirects to OAuth provider" in md
        assert "Token stored securely" in md

    def test_traceability_matrix_present(self):
        md = generate_requirements_md(_make_reqs())
        assert "Traceability Matrix" in md
        assert "ART-001" in md
        assert "TST-001" in md

    def test_ears_statement_formatting_ubiquitous(self):
        md = generate_requirements_md(_make_reqs())
        assert "The system shall authenticate users via OAuth2" in md

    def test_ears_statement_formatting_event_driven(self):
        md = generate_requirements_md(_make_reqs())
        assert "the user is idle for 30 minutes" in md
        assert "the system shall" in md.lower()

    def test_deterministic_output(self):
        reqs = _make_reqs()
        assert generate_requirements_md(reqs) == generate_requirements_md(reqs)

    def test_checksum_embedded(self):
        md = generate_requirements_md(_make_reqs())
        assert "checksum" in md


# ==========================================================================
# TSK-094 — design_doc.py
# ==========================================================================

class TestDesignDoc:
    def _decision(self):
        return DecisionArtifact(
            adr_id="ADR-001",
            title="Choose canvas library",
            status=ADRStatus.ACCEPTED,
            context="We need an open-source canvas engine.",
            decision="Excalidraw",
            consequences="MIT licensed, good community.",
            alternatives=[
                Alternative("Excalidraw", pros=["MIT", "Popular"], cons=["React-only"]),
                Alternative("Konva", pros=["Flexible"], cons=["No collaboration"]),
            ],
            tags=["canvas", "frontend"],
        )

    def test_adr_contains_madr_sections(self):
        adr = generate_adr(self._decision())
        for section in ["Context and Problem Statement", "Decision Outcome",
                        "Considered Options", "Pros and Cons"]:
            assert section in adr

    def test_adr_status_uppercased(self):
        adr = generate_adr(self._decision())
        assert "ACCEPTED" in adr

    def test_adr_alternatives_listed(self):
        adr = generate_adr(self._decision())
        assert "Excalidraw" in adr
        assert "Konva" in adr

    def test_adr_pros_cons_markers(self):
        adr = generate_adr(self._decision())
        assert "✅" in adr or "Pros" in adr
        assert "❌" in adr or "Cons" in adr

    def test_adr_deterministic(self):
        d = self._decision()
        assert generate_adr(d) == generate_adr(d)

    def test_adr_superseded_by_shown(self):
        d = self._decision()
        d.superseded_by = "ADR-002"
        adr = generate_adr(d)
        assert "ADR-002" in adr

    def test_design_md_embeds_mermaid_diagrams(self):
        sections = [
            DesignSection(
                title="Architecture",
                content="High-level overview.",
                diagrams=[DiagramBlock("System diagram", "flowchart TD\n  A --> B")],
            )
        ]
        md = generate_design_md(sections, project_name="PS")
        assert "```mermaid" in md
        assert "flowchart TD" in md

    def test_design_md_links_adrs(self):
        sections = [
            DesignSection(
                title="Canvas",
                content="Canvas layer design.",
                linked_adrs=["ADR-001"],
            )
        ]
        decisions = [self._decision()]
        md = generate_design_md(sections, decisions=decisions)
        assert "ADR-001" in md
        assert "Choose canvas library" in md

    def test_design_md_includes_adr_index(self):
        md = generate_design_md([], decisions=[self._decision()])
        assert "Architecture Decisions" in md

    def test_design_md_deterministic(self):
        sections = [DesignSection(title="S", content="C")]
        md1 = generate_design_md(sections, project_name="PS")
        md2 = generate_design_md(sections, project_name="PS")
        assert md1 == md2


# ==========================================================================
# TSK-095 — tasks_doc.py
# ==========================================================================

def _make_tasks():
    return [
        Task("T-001", "Bootstrap", status=TaskStatus.DONE),
        Task("T-002", "Schema", depends_on=["T-001"]),
        Task("T-003", "API", depends_on=["T-002"]),
        Task("T-004", "Frontend", depends_on=["T-002"]),
        Task("T-005", "Deploy", depends_on=["T-003", "T-004"]),
    ]


class TestTasksDoc:
    def test_compute_waves_wave_zero_no_deps(self):
        waves = compute_waves(_make_tasks())
        wave0_ids = {t.task_id for t in waves[0]}
        assert "T-001" in wave0_ids

    def test_compute_waves_correct_order(self):
        waves = compute_waves(_make_tasks())
        wave_map = {t.task_id: i for i, wave in enumerate(waves) for t in wave}
        assert wave_map["T-002"] > wave_map["T-001"]
        assert wave_map["T-003"] > wave_map["T-002"]
        assert wave_map["T-005"] > wave_map["T-003"]
        assert wave_map["T-005"] > wave_map["T-004"]

    def test_compute_waves_parallel_in_same_wave(self):
        waves = compute_waves(_make_tasks())
        wave_map = {t.task_id: i for i, wave in enumerate(waves) for t in wave}
        # T-003 and T-004 both depend only on T-002
        assert wave_map["T-003"] == wave_map["T-004"]

    def test_cyclic_dependency_raises(self):
        tasks = [
            Task("A", "A", depends_on=["B"]),
            Task("B", "B", depends_on=["A"]),
        ]
        with pytest.raises(CyclicDependencyError):
            compute_waves(tasks)

    def test_generate_tasks_md_has_wave_headings(self):
        md = generate_tasks_md(_make_tasks())
        assert "Wave 0" in md
        assert "Wave 1" in md

    def test_generate_tasks_md_has_summary(self):
        md = generate_tasks_md(_make_tasks(), project_name="PS")
        assert "1/5 tasks done" in md

    def test_generate_tasks_md_deterministic(self):
        tasks = _make_tasks()
        assert generate_tasks_md(tasks) == generate_tasks_md(tasks)

    def test_speckit_profile_yaml_format(self):
        profile = generate_speckit_profile(_make_tasks(), project_name="PS")
        assert "tasks:" in profile
        assert "id: T-001" in profile

    def test_kiro_specs_one_file_per_task(self):
        specs = generate_kiro_specs(_make_tasks())
        for tid in ["T-001", "T-002", "T-003", "T-004", "T-005"]:
            assert f".kiro/specs/{tid}.md" in specs

    def test_kiro_spec_has_acceptance(self):
        tasks = [Task("T-001", "Bootstrap", acceptance="Must start cleanly")]
        specs = generate_kiro_specs(tasks)
        assert "Must start cleanly" in specs[".kiro/specs/T-001.md"]


# ==========================================================================
# TSK-096 — openapi.py
# ==========================================================================

def _make_openapi_doc():
    info = APIInfo(title="Prompt Studio API", version="1.0.0")
    endpoints = [
        APIEndpoint(
            path="/projects",
            method=HTTPMethod.GET,
            operation_id="list_projects",
            summary="List all projects",
            tags=["projects"],
            responses=[APIResponse("200", "OK", schema={"type": "array"})],
        ),
        APIEndpoint(
            path="/projects/{project_id}",
            method=HTTPMethod.GET,
            operation_id="get_project",
            parameters=[APIParameter("project_id", "path", required=True)],
            responses=[APIResponse("200", "OK"), APIResponse("404", "Not found")],
        ),
        APIEndpoint(
            path="/projects",
            method=HTTPMethod.POST,
            operation_id="create_project",
            request_body_schema={"type": "object"},
            responses=[APIResponse("201", "Created")],
            is_complete=False,
            todo_note="Implement validation",
        ),
    ]
    return generate_openapi(info, endpoints)


class TestOpenAPI:
    def test_openapi_version_is_31(self):
        doc = _make_openapi_doc()
        assert doc["openapi"] == "3.1.0"

    def test_openapi_has_paths(self):
        doc = _make_openapi_doc()
        assert "/projects" in doc["paths"]
        assert "/projects/{project_id}" in doc["paths"]

    def test_openapi_x_todo_on_incomplete(self):
        doc = _make_openapi_doc()
        post_op = doc["paths"]["/projects"]["post"]
        assert "x-todo" in post_op
        assert "Implement validation" in post_op["x-todo"]

    def test_openapi_no_x_todo_on_complete(self):
        doc = _make_openapi_doc()
        get_op = doc["paths"]["/projects"]["get"]
        assert "x-todo" not in get_op

    def test_openapi_validate_passes(self):
        doc = _make_openapi_doc()
        errors = validate_openapi(doc)
        assert errors == []

    def test_openapi_validate_missing_operation_id(self):
        doc = _make_openapi_doc()
        del doc["paths"]["/projects"]["get"]["operationId"]
        errors = validate_openapi(doc)
        assert any("operationId" in e for e in errors)

    def test_openapi_validate_bad_version(self):
        doc = _make_openapi_doc()
        doc["openapi"] = "2.0.0"
        errors = validate_openapi(doc)
        assert any("3.1." in e for e in errors)

    def test_openapi_validate_path_no_slash(self):
        doc = _make_openapi_doc()
        doc["paths"]["bad_path"] = {}
        errors = validate_openapi(doc)
        assert any("bad_path" in e for e in errors)

    def test_assert_valid_raises_on_invalid(self):
        doc = {"openapi": "2.0", "info": {"title": "X", "version": "1"}, "paths": {}}
        with pytest.raises(OpenAPIValidationError):
            assert_valid_openapi(doc)

    def test_openapi_to_json_deterministic(self):
        doc = _make_openapi_doc()
        j1 = openapi_to_json(doc)
        j2 = openapi_to_json(doc)
        assert j1 == j2
        # Verify it's valid JSON
        parsed = json.loads(j1)
        assert parsed["openapi"] == "3.1.0"


# ==========================================================================
# TSK-097 — data_model.py
# ==========================================================================

def _make_entities():
    return [
        DataEntity(
            table_name="users",
            columns=[
                Column("id", ColumnType.UUID, primary_key=True, default="gen_random_uuid()"),
                Column("email", ColumnType.TEXT, nullable=False, unique=True),
                Column("created_at", ColumnType.TIMESTAMP, nullable=False),
            ],
            indexes=[Index(["email"], unique=True, name="idx_users_email")],
        ),
        DataEntity(
            table_name="projects",
            columns=[
                Column("id", ColumnType.UUID, primary_key=True, default="gen_random_uuid()"),
                Column("owner_id", ColumnType.UUID, nullable=False, references="users.id"),
                Column("name", ColumnType.TEXT, nullable=False),
            ],
        ),
    ]


class TestDataModel:
    def test_sql_ddl_has_create_table(self):
        ddl = generate_sql_ddl(_make_entities())
        assert 'CREATE TABLE IF NOT EXISTS "users"' in ddl
        assert 'CREATE TABLE IF NOT EXISTS "projects"' in ddl

    def test_sql_ddl_primary_key(self):
        ddl = generate_sql_ddl(_make_entities())
        assert "PRIMARY KEY" in ddl

    def test_sql_ddl_not_null(self):
        ddl = generate_sql_ddl(_make_entities())
        assert "NOT NULL" in ddl

    def test_sql_ddl_unique(self):
        ddl = generate_sql_ddl(_make_entities())
        assert "UNIQUE" in ddl

    def test_sql_ddl_foreign_key(self):
        ddl = generate_sql_ddl(_make_entities())
        assert 'REFERENCES "users"' in ddl

    def test_sql_ddl_index(self):
        ddl = generate_sql_ddl(_make_entities())
        assert "CREATE UNIQUE INDEX" in ddl

    def test_sql_ddl_deterministic(self):
        entities = _make_entities()
        assert generate_sql_ddl(entities) == generate_sql_ddl(entities)

    def test_dbml_has_table(self):
        dbml = generate_dbml(_make_entities())
        assert "Table users {" in dbml
        assert "Table projects {" in dbml

    def test_dbml_has_pk(self):
        dbml = generate_dbml(_make_entities())
        assert "pk" in dbml

    def test_dbml_has_ref(self):
        dbml = generate_dbml(_make_entities())
        assert "Ref:" in dbml

    def test_dbml_deterministic(self):
        entities = _make_entities()
        assert generate_dbml(entities) == generate_dbml(entities)

    def test_parity_passes(self):
        entities = _make_entities()
        ddl = generate_sql_ddl(entities)
        dbml = generate_dbml(entities)
        # Should not raise
        assert_ddl_dbml_parity(ddl, dbml)

    def test_parity_fails_on_mismatch(self):
        entities = _make_entities()
        ddl = generate_sql_ddl(entities)
        # Remove a table from DBML by using fewer entities
        dbml = generate_dbml([_make_entities()[0]])
        with pytest.raises(ParityError):
            assert_ddl_dbml_parity(ddl, dbml)


# ==========================================================================
# TSK-098 — diagrams.py
# ==========================================================================

def _make_er():
    entities = [
        EREntity("User", [
            ERAttribute("uuid", "id", is_pk=True),
            ERAttribute("text", "email"),
        ]),
        EREntity("Project", [
            ERAttribute("uuid", "id", is_pk=True),
            ERAttribute("uuid", "owner_id", is_fk=True),
        ]),
    ]
    relations = [ERRelation("User", "Project", "||--o{", "owns")]
    return entities, relations


def _make_flow():
    nodes = [
        FlowNode("start", "Start", shape="stadium"),
        FlowNode("login", "Login Page", shape="rect"),
        FlowNode("dashboard", "Dashboard", shape="rect"),
        FlowNode("error", "Error?", shape="diamond"),
    ]
    edges = [
        FlowEdge("start", "login"),
        FlowEdge("login", "error"),
        FlowEdge("error", "dashboard", label="success"),
        FlowEdge("error", "login", label="retry"),
    ]
    return FlowGraph("Login Flow", nodes, edges, direction="TD")


class TestDiagrams:
    def test_er_diagram_starts_with_erdiagram(self):
        entities, relations = _make_er()
        mmd = generate_er_diagram(entities, relations)
        assert mmd.strip().startswith("erDiagram")

    def test_er_diagram_has_entities(self):
        entities, relations = _make_er()
        mmd = generate_er_diagram(entities, relations)
        assert "user" in mmd.lower()
        assert "project" in mmd.lower()

    def test_er_diagram_has_pk_fk(self):
        entities, relations = _make_er()
        mmd = generate_er_diagram(entities, relations)
        assert "PK" in mmd
        assert "FK" in mmd

    def test_er_diagram_has_relation(self):
        entities, relations = _make_er()
        mmd = generate_er_diagram(entities, relations)
        assert "||--o{" in mmd or "owns" in mmd

    def test_er_diagram_deterministic(self):
        entities, relations = _make_er()
        assert generate_er_diagram(entities, relations) == generate_er_diagram(entities, relations)

    def test_flow_diagram_starts_with_flowchart(self):
        mmd = generate_flow_diagram(_make_flow())
        assert mmd.strip().startswith("flowchart TD")

    def test_flow_diagram_has_nodes(self):
        mmd = generate_flow_diagram(_make_flow())
        assert "Start" in mmd
        assert "Login Page" in mmd

    def test_flow_diagram_has_edges(self):
        mmd = generate_flow_diagram(_make_flow())
        assert "-->" in mmd

    def test_flow_diagram_diamond_shape(self):
        mmd = generate_flow_diagram(_make_flow())
        assert "{" in mmd  # diamond shape

    def test_flow_diagram_deterministic(self):
        g = _make_flow()
        assert generate_flow_diagram(g) == generate_flow_diagram(g)

    def test_safe_id_alphanumeric(self):
        assert _safe_id("My Entity!") == "my_entity"
        assert _safe_id("hello world") == "hello_world"

    def test_validate_mermaid_valid_er(self):
        entities, relations = _make_er()
        mmd = generate_er_diagram(entities, relations)
        assert validate_mermaid(mmd) == []

    def test_validate_mermaid_valid_flow(self):
        mmd = generate_flow_diagram(_make_flow())
        assert validate_mermaid(mmd) == []

    def test_validate_mermaid_unknown_type(self):
        errors = validate_mermaid("gantt\nTask1 : 2024-01-01, 7d")
        assert len(errors) > 0

    def test_validate_mermaid_empty(self):
        errors = validate_mermaid("")
        assert any("Empty" in e for e in errors)

    def test_assert_valid_mermaid_raises(self):
        with pytest.raises(MermaidValidationError):
            assert_valid_mermaid("gantt\nTask1 : 2024-01-01, 7d")


# ==========================================================================
# TSK-099 — exporters.py
# ==========================================================================

class TestExporters:
    def test_llms_txt_has_project_name(self):
        ctx = LLMSContext(
            project_name="Prompt Studio",
            description="A prompt-native workspace",
        )
        txt = generate_llms_txt(ctx)
        assert "# Prompt Studio" in txt
        assert "> A prompt-native workspace" in txt

    def test_llms_txt_has_docs_section(self):
        ctx = LLMSContext(
            project_name="PS",
            description="desc",
            docs_links=["https://docs.example.com"],
        )
        txt = generate_llms_txt(ctx)
        assert "## Docs" in txt
        assert "https://docs.example.com" in txt

    def test_llms_txt_has_api_section(self):
        ctx = LLMSContext(
            project_name="PS",
            description="desc",
            api_links=["https://api.example.com/openapi.json"],
        )
        txt = generate_llms_txt(ctx)
        assert "## API" in txt

    def test_llms_txt_blocked_section(self):
        ctx = LLMSContext(
            project_name="PS",
            description="desc",
            blocked_sections=["Internal docs"],
        )
        txt = generate_llms_txt(ctx)
        assert "## Blocked" in txt
        assert "Internal docs" in txt

    def test_design_tokens_dtcg_format(self):
        tokens = [
            DesignToken("primary", "#0066CC", "color", group="color/brand"),
            DesignToken("spacing-4", "16px", "dimension", group="spacing"),
        ]
        output = export_design_tokens(tokens)
        parsed = json.loads(output)
        assert "color" in parsed
        assert "spacing" in parsed
        # Check DTCG $value/$type structure
        assert "$value" in parsed["color"]["brand"]["primary"]
        assert "$type" in parsed["color"]["brand"]["primary"]

    def test_design_tokens_deterministic(self):
        tokens = [DesignToken("x", "y", "color")]
        assert export_design_tokens(tokens) == export_design_tokens(tokens)

    def test_skill_package_export_manifest(self):
        pkg = SkillPackageExport(
            package_id="skill-001",
            name="My Skill",
            version="1.0.0",
            files={
                "SKILL.md": b"# My Skill\nDoes stuff.",
                "scripts/run.py": b"print('hello')",
            },
        )
        manifest = export_skill_package(pkg)
        assert manifest["package_id"] == "skill-001"
        assert "SKILL.md" in manifest["files"]
        assert "scripts/run.py" in manifest["files"]
        assert "manifest_checksum" in manifest

    def test_skill_package_verbatim_checksums(self):
        content = b"# My Skill"
        pkg = SkillPackageExport("s", "S", "1", {"SKILL.md": content})
        manifest = export_skill_package(pkg)
        import hashlib
        expected = hashlib.sha256(content).hexdigest()
        assert manifest["files"]["SKILL.md"] == expected

    def test_prompt_asset_export_versions(self):
        asset = PromptAssetExport(
            asset_id="prompt-001",
            name="Greeting prompt",
            current_version=2,
            versions=[
                PromptVersionExport(1, "Hello {{name}}", ["name"], "2024-01-01T00:00:00Z"),
                PromptVersionExport(2, "Hi {{name}}!", ["name"], "2024-06-01T00:00:00Z"),
            ],
            tags=["greeting"],
        )
        result = export_prompt_asset(asset)
        assert result["asset_id"] == "prompt-001"
        assert len(result["versions"]) == 2
        assert result["versions"][0]["version"] == 1
        assert "content_hash" in result["versions"][0]
        assert "export_checksum" in result

    def test_prompt_asset_export_deterministic(self):
        asset = PromptAssetExport(
            "p1", "P", 1,
            [PromptVersionExport(1, "Hello", [], "2024-01-01T00:00:00Z")]
        )
        assert export_prompt_asset(asset) == export_prompt_asset(asset)


# ==========================================================================
# TSK-100 — import_validator.py
# ==========================================================================

class TestImportValidator:
    def _pkg(self, **kwargs) -> ImportPackage:
        defaults = dict(
            package_id="pkg-001",
            name="Test Package",
            version="1.0.0",
            artifacts=[{"id": "art-001", "type": "screen"}],
            skills=[{"package_id": "skill-001"}],
            prompts=[{"asset_id": "prompt-001"}],
        )
        defaults.update(kwargs)
        return ImportPackage(**defaults)

    def test_valid_package_passes(self):
        result = validate_import(self._pkg())
        assert result.is_valid
        assert result.errors == []

    def test_missing_package_id_fails(self):
        result = validate_import(self._pkg(package_id=""))
        assert not result.is_valid
        assert any("package_id" in e for e in result.errors)

    def test_missing_name_fails(self):
        result = validate_import(self._pkg(name=""))
        assert not result.is_valid

    def test_missing_version_fails(self):
        result = validate_import(self._pkg(version=""))
        assert not result.is_valid

    def test_artifact_missing_id_fails(self):
        pkg = self._pkg(artifacts=[{"type": "screen"}])
        result = validate_import(pkg)
        assert not result.is_valid
        assert any("artifacts[0]" in e and "'id'" in e for e in result.errors)

    def test_artifact_missing_type_fails(self):
        pkg = self._pkg(artifacts=[{"id": "art-001"}])
        result = validate_import(pkg)
        assert not result.is_valid

    def test_skill_missing_package_id_fails(self):
        pkg = self._pkg(skills=[{"name": "X"}])
        result = validate_import(pkg)
        assert not result.is_valid

    def test_collision_rename_strategy(self):
        pkg = self._pkg()
        result = validate_import(
            pkg,
            existing_ids={"art-001"},
            collision_strategy=CollisionStrategy.RENAME,
        )
        assert result.is_valid
        # art-001 should be renamed
        assert result.id_map["art-001"] != "art-001"
        assert any("renamed" in w for w in result.warnings)

    def test_collision_reject_strategy(self):
        pkg = self._pkg()
        result = validate_import(
            pkg,
            existing_ids={"art-001"},
            collision_strategy=CollisionStrategy.REJECT,
        )
        assert not result.is_valid
        assert any("collision" in e.lower() for e in result.errors)

    def test_collision_overwrite_strategy(self):
        pkg = self._pkg()
        result = validate_import(
            pkg,
            existing_ids={"art-001"},
            collision_strategy=CollisionStrategy.OVERWRITE,
        )
        assert result.is_valid
        assert result.id_map["art-001"] == "art-001"
        assert any("overwrite" in w for w in result.warnings)

    def test_id_map_identity_on_no_collision(self):
        pkg = self._pkg()
        result = validate_import(pkg, existing_ids=set())
        assert result.id_map["art-001"] == "art-001"
        assert result.id_map["skill-001"] == "skill-001"
        assert result.id_map["prompt-001"] == "prompt-001"

    def test_round_trip_check_passes_on_match(self):
        export1 = {"data": "hello", "version": "1"}
        export2 = {"data": "hello", "version": "1"}
        round_trip_check(export1, export2)  # should not raise

    def test_round_trip_check_fails_on_mismatch(self):
        export1 = {"data": "hello"}
        export2 = {"data": "world"}
        with pytest.raises(RoundTripError):
            round_trip_check(export1, export2)

    def test_round_trip_check_ignores_specified_keys(self):
        export1 = {"data": "hello", "exported_at": "2024-01-01"}
        export2 = {"data": "hello", "exported_at": "2025-01-01"}
        # Should pass — exported_at is ignored by default
        round_trip_check(export1, export2)

    def test_round_trip_check_fails_if_not_just_ignored_key(self):
        export1 = {"data": "hello", "exported_at": "2024-01-01"}
        export2 = {"data": "world", "exported_at": "2024-01-01"}
        with pytest.raises(RoundTripError):
            round_trip_check(export1, export2)
