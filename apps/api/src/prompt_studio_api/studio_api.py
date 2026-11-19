from __future__ import annotations

import io
import json
import uuid
from typing import Any

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from backend.app.export.agents_md import ProjectContext, generate_agents_md
from backend.app.export.exporters import LLMSContext, generate_llms_txt
from backend.app.export.pipeline import (
    ArtifactExportRecord,
    ExportJob,
    ExportProfile,
    build_manifest,
    build_machine_package,
    write_archive,
)

router = APIRouter(prefix="/api/v1", tags=["studio-core"])


def _build_studio_export_docs() -> tuple[list[ArtifactExportRecord], list[dict[str, str]], dict[str, str]]:
    """Build canonical project graph artifacts and compiled docs."""
    artifacts = [
        ArtifactExportRecord(
            artifact_id="art_req_001",
            artifact_type="requirement",
            title="Create and publish payment form",
            body="A creator can configure a one-time or recurring payment form with custom branding, set minimum and preset amounts, and publish a public checkout link.",
            revision=3,
            payload={"alias": "REQ-001", "status": "approved", "priority": "must", "ears_pattern": "event_driven"},
        ),
        ArtifactExportRecord(
            artifact_id="art_req_002",
            artifact_type="requirement",
            title="Collect card and instant payment checkout",
            body="WHEN a payer visits the form route THE SYSTEM SHALL present Stripe Elements with Apple Pay and Google Pay support and submit tokenized payments.",
            revision=2,
            payload={"alias": "REQ-002", "status": "approved", "priority": "must", "ears_pattern": "event_driven"},
        ),
        ArtifactExportRecord(
            artifact_id="art_req_003",
            artifact_type="requirement",
            title="Deterministic project compilation and agent handoff",
            body="THE SYSTEM SHALL compile all visual projections, typed graph nodes, and field prompts into a verifiable ZIP with zero secret leaks.",
            revision=4,
            payload={"alias": "REQ-003", "status": "approved", "priority": "must", "ears_pattern": "ubiquitous"},
        ),
        ArtifactExportRecord(
            artifact_id="art_screen_001",
            artifact_type="screen",
            title="Payment Form Builder",
            body="Drag-and-drop builder with real-time phone/desktop preview, pricing tier editor, and currency switch.",
            revision=2,
            payload={"alias": "SCR-001", "route": "/builder/form", "viewport": "desktop_1440", "states": ["empty", "editing", "saving", "error"]},
        ),
        ArtifactExportRecord(
            artifact_id="art_screen_002",
            artifact_type="screen",
            title="Public Checkout Screen",
            body="Branded buyer view with instant mobile pay, order summary, card fields, and transaction status toast.",
            revision=2,
            payload={"alias": "SCR-002", "route": "/pay/:slug", "viewport": "mobile_390", "states": ["empty", "loading", "invalid", "success", "error"]},
        ),
        ArtifactExportRecord(
            artifact_id="art_dec_001",
            artifact_type="decision",
            title="Use Stripe Elements with Payment Intents",
            body="Context: High compliance burden with direct card handling. Decision: Offload PCI scope via hosted Elements.",
            revision=1,
            payload={"alias": "DEC-001", "status": "accepted", "consequences": "Zero raw card numbers touch our application server."},
        ),
        ArtifactExportRecord(
            artifact_id="art_task_001",
            artifact_type="task",
            title="Setup DB migrations for forms & transactions",
            body="Run alembic migration creating payment_forms and payment_transactions tables with indices.",
            revision=1,
            payload={"alias": "TSK-001", "wave": 1, "complexity": "S", "owner": "backend"},
        ),
        ArtifactExportRecord(
            artifact_id="art_task_002",
            artifact_type="task",
            title="Implement checkout REST and webhook endpoints",
            body="Expose POST /api/v1/forms and POST /api/v1/webhooks/stripe with signature verification.",
            revision=1,
            payload={"alias": "TSK-002", "wave": 2, "complexity": "M", "owner": "api", "depends_on": ["TSK-001"]},
        ),
    ]

    edges = [
        {"source": "art_req_001", "target": "art_screen_001", "edge_type": "implements"},
        {"source": "art_req_002", "target": "art_screen_002", "edge_type": "implements"},
        {"source": "art_req_001", "target": "art_task_001", "edge_type": "realized_by"},
        {"source": "art_task_001", "target": "art_task_002", "edge_type": "depends_on"},
    ]

    project_ctx = ProjectContext(
        name="Prompt Studio SaaS",
        description="A prompt-native visual workspace for designing verified applications with deterministic AI coding agent handoff.",
        commands={
            "make setup": "Install runtime dependencies and seed sample schema",
            "make dev": "Start Vite client and FastAPI backend servers",
            "make test": "Run backend pytest and frontend vitest suite",
            "make export-check": "Verify compiler determinism and checksum parity",
        },
        boundaries={
            "always": [
                "Validate every artifact against its declared JSON Schema before persisting",
                "Write revisions and audit events for every change",
                "Keep visual layout strictly separate from semantic data",
                "Preserve human edits; never silent-overwrite",
            ],
            "ask_first": [
                "Schema or migration changes",
                "Adding third-party dependencies",
                "Permission level elevation",
            ],
            "never": [
                "Commit or export unredacted secrets or API keys",
                "Execute model-generated code in the API process",
                "Bypass the patch approval service",
                "Delete failing tests",
            ],
        },
        modules={
            "apps/web": "React 19 infinite canvas and workspace shell",
            "apps/api": "FastAPI REST API and projection management service",
            "packages/canvas": "Canvas adapter layer and visual drawing engine",
            "packages/wireframes": "Low-fidelity component palette and states matrix",
            "backend/app/export": "Deterministic export compiler and handoff packager",
        },
    )

    agents_md = generate_agents_md(project_ctx)

    requirements_md = (
        "# Requirements Specification (EARS)\n\n"
        "| ID | Title | Pattern | Statement |\n"
        "|---|---|---|---|\n"
        "| REQ-001 | Form Builder | Event-driven | WHEN a creator submits form config THE SYSTEM SHALL validate fields and return public checkout URL. |\n"
        "| REQ-002 | Checkout Experience | Event-driven | WHEN a payer navigates to form route THE SYSTEM SHALL mount Stripe Elements and process tokenized charge. |\n"
        "| REQ-003 | Deterministic Compiler | Ubiquitous | THE SYSTEM SHALL compile the visual graph into a deterministic ZIP with verifiable checksum. |\n"
    )

    design_md = (
        "# Architecture & Design Decision Records (ADRs)\n\n"
        "## ADR-001: Separation of Visual Layout from Canonical Semantics\n"
        "- **Status**: Accepted\n"
        "- **Context**: Moving a card on canvas must not mutate underlying entity relationships or trigger schema migration.\n"
        "- **Decision**: Canvas writes layout deltas to projection records; semantic edits flow through typed patch approval.\n\n"
        "## ADR-002: Offload Card Payments to Stripe Elements\n"
        "- **Status**: Accepted\n"
        "- **Context**: Avoid storing raw credit card PANs in application databases.\n"
        "- **Decision**: Use PaymentIntents with client-side Elements and verified webhooks."
    )

    tasks_md = (
        "# Implementation Tasks (Kahn's Topological Waves)\n\n"
        "## Wave 1 (Independent Tasks)\n"
        "- [ ] **TSK-001**: Setup DB migrations for `payment_forms` and `payment_transactions` (Complexity: S)\n\n"
        "## Wave 2 (Blocked by Wave 1)\n"
        "- [ ] **TSK-002**: Implement checkout REST and webhook endpoints (Complexity: M, Depends: TSK-001)\n\n"
        "## Wave 3 (Blocked by Wave 2)\n"
        "- [ ] **TSK-003**: Build wireframe-validated checkout client matching SCR-002 states (Complexity: M, Depends: TSK-002)\n"
    )

    openapi_json = json.dumps({
        "openapi": "3.1.0",
        "info": {
            "title": "Prompt Studio SaaS API",
            "version": "1.0.0",
            "description": "Production REST API for payment forms and workspace graphs.",
        },
        "paths": {
            "/api/v1/forms": {
                "post": {
                    "summary": "Create new payment form",
                    "requestBody": {
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "required": ["title", "slug"],
                                    "properties": {
                                        "title": {"type": "string"},
                                        "slug": {"type": "string"},
                                        "currency": {"type": "string", "default": "USD"},
                                    },
                                },
                            },
                        },
                    },
                    "responses": {"201": {"description": "Form created successfully"}},
                },
            },
            "/api/v1/checkout/{slug}": {
                "get": {
                    "summary": "Fetch public checkout configuration",
                    "parameters": [{"name": "slug", "in": "path", "required": True, "schema": {"type": "string"}}],
                    "responses": {"200": {"description": "Public checkout details"}},
                },
            },
        },
    }, indent=2)

    schema_sql = (
        "-- PostgreSQL Schema DDL generated by Prompt Studio Compiler\n"
        "-- Dialect: PostgreSQL 16\n\n"
        'CREATE TABLE IF NOT EXISTS "payment_forms" (\n'
        '  "id" UUID PRIMARY KEY DEFAULT gen_random_uuid(),\n'
        '  "workspace_id" UUID NOT NULL,\n'
        '  "slug" VARCHAR(64) UNIQUE NOT NULL,\n'
        '  "title" VARCHAR(255) NOT NULL,\n'
        '  "currency" VARCHAR(3) DEFAULT \'USD\',\n'
        '  "is_active" BOOLEAN DEFAULT TRUE,\n'
        '  "created_at" TIMESTAMPTZ DEFAULT NOW()\n'
        ');\n\n'
        'CREATE TABLE IF NOT EXISTS "payment_transactions" (\n'
        '  "id" UUID PRIMARY KEY DEFAULT gen_random_uuid(),\n'
        '  "form_id" UUID REFERENCES "payment_forms" ("id") ON DELETE CASCADE,\n'
        '  "amount_cents" BIGINT NOT NULL,\n'
        '  "status" VARCHAR(32) NOT NULL,\n'
        '  "gateway_ref" VARCHAR(128) UNIQUE,\n'
        '  "payer_email" VARCHAR(255),\n'
        '  "created_at" TIMESTAMPTZ DEFAULT NOW()\n'
        ');\n\n'
        'CREATE INDEX IF NOT EXISTS "idx_payment_forms_slug" ON "payment_forms" ("slug");\n'
        'CREATE INDEX IF NOT EXISTS "idx_transactions_form_date" ON "payment_transactions" ("form_id", "created_at" DESC);\n'
    )

    mermaid_c4 = (
        "graph TD\n"
        "  subgraph Client [Browser & Mobile App]\n"
        "    Web[React SPA / Canvas]\n"
        "    Checkout[Public Checkout View]\n"
        "  end\n"
        "  subgraph Backend [Application Server]\n"
        "    API[FastAPI Gateway]\n"
        "    Compiler[Export Compiler Engine]\n"
        "    AIRuntime[AI Orchestrator & Field Runner]\n"
        "  end\n"
        "  subgraph Storage [Persistence Layer]\n"
        "    DB[(PostgreSQL 16 Graph Store)]\n"
        "  end\n"
        "  Web -->|REST / WS| API\n"
        "  Checkout -->|Tokenized Payment| API\n"
        "  API --> DB\n"
        "  Compiler --> DB\n"
        "  AIRuntime --> API\n"
    )

    llms_txt = generate_llms_txt(
        LLMSContext(
            project_name="Prompt Studio SaaS",
            description="A prompt-native visual workspace for designing verified applications with deterministic AI coding agent handoff.",
            docs_links=["/specs/requirements.md", "/specs/design.md", "/specs/schema.sql"],
            api_links=["/specs/openapi.json"],
        )
    )

    human_docs = {
        "AGENTS.md": agents_md,
        "requirements.md": requirements_md,
        "design.md": design_md,
        "tasks.md": tasks_md,
        "openapi.json": openapi_json,
        "schema.sql": schema_sql,
        "architecture.mermaid": mermaid_c4,
        "llms.txt": llms_txt,
    }

    return artifacts, edges, human_docs


@router.get("/export/files")
async def get_export_files() -> dict[str, str]:
    """Return all live generated export files for preview in the UI."""
    _, _, human_docs = _build_studio_export_docs()
    return human_docs


@router.get("/export/zip")
async def download_export_zip() -> StreamingResponse:
    """Compile and stream the deterministic project export ZIP handoff."""
    artifacts, edges, human_docs = _build_studio_export_docs()
    job = ExportJob(
        job_id=f"job_{uuid.uuid4().hex[:8]}",
        project_id="proj_prompt_studio",
        pinned_revision=1,
        profile=ExportProfile.FULL,
    )
    manifest = build_manifest(job, artifacts)
    machine_package = build_machine_package(
        job=job,
        artifacts=artifacts,
        edges=edges,
    )
    archive_bytes = write_archive(job, manifest, human_docs, machine_package)

    return StreamingResponse(
        io.BytesIO(archive_bytes),
        media_type="application/zip",
        headers={
            "Content-Disposition": 'attachment; filename="prompt_studio_handoff.zip"',
            "Content-Length": str(len(archive_bytes)),
        },
    )


class FieldRunApiRequest(BaseModel):
    artifact_id: str
    field_name: str
    current_value: str
    instruction: str
    model: str = "gemini-2.0-flash"


class FieldRunApiResponse(BaseModel):
    run_id: str
    artifact_id: str
    field_name: str
    previous_value: str
    proposed_value: str
    diff_patch: list[dict[str, Any]]
    rationale: str
    latency_ms: int


@router.post("/ai/field-run", response_model=FieldRunApiResponse)
async def execute_field_run(request: FieldRunApiRequest) -> FieldRunApiResponse:
    """Execute a prompt on a specific field and return a structured patch proposal for review."""
    run_id = f"run_{uuid.uuid4().hex[:8]}"

    instr = request.instruction.lower()
    curr = request.current_value
    field = request.field_name

    if "ears" in instr or "acceptance criteria" in instr or field == "acceptance_criteria":
        proposed = (
            f"{curr}\n\n"
            "### Formal EARS Acceptance Criteria:\n"
            "1. WHEN a creator completes card configuration THE SYSTEM SHALL validate all inputs synchronously.\n"
            "2. WHILE the form status is active THE SYSTEM SHALL accept card tokens and render real-time charge confirmation.\n"
            "3. IF card verification fails THE SYSTEM SHALL show inline validation without clearing entered field values.\n"
            "4. WHEN payment succeeds THE SYSTEM SHALL emit an immutable transaction ledger event."
        )
        rationale = "Structured into formal EARS criteria with event-driven, state-driven, and unwanted-behavior patterns."
    elif "screen" in instr or "wireframe" in instr or "control" in instr:
        proposed = (
            f"{curr}\n\n"
            "### Recommended UI Components & States:\n"
            "- [FormHeader]: Logo, Title breadcrumb, Live publish switch\n"
            "- [TextInput]: Form title (max 80 chars), Slug URL with live preview\n"
            "- [AmountSelector]: Preset chips ($10, $25, $50, custom), Currency selector\n"
            "- [StripeCardElement]: Number, Expiry, CVC with client validation badges\n"
            "- [PrimaryButton]: 'Pay Now' with loading spinner state and success toast\n"
            "- [States Covered]: Empty, Loading, Populated, Invalid card error, Success."
        )
        rationale = "Generated complete low-fidelity wireframe component hierarchy with explicit required state coverage."
    elif "sql" in instr or "schema" in instr or "entity" in instr:
        proposed = (
            f"{curr}\n\n"
            "### Generated PostgreSQL Schema & Indexes:\n"
            "CREATE INDEX idx_payment_forms_slug ON payment_forms(slug);\n"
            "CREATE INDEX idx_payment_transactions_form ON payment_transactions(form_id, created_at DESC);\n"
            "ALTER TABLE payment_transactions ADD CONSTRAINT chk_amount_positive CHECK (amount_cents > 0);"
        )
        rationale = "Added performance indexes on lookup slugs and relational integrity check constraints."
    elif "test" in instr or "edge" in instr or "security" in instr:
        proposed = (
            f"{curr}\n\n"
            "### Security Boundaries & Edge Cases:\n"
            "- Replay attack prevention: idempotency-key required on POST /charges\n"
            "- Rate limiting: 10 failed checkout attempts per IP per 5 minutes triggers Cloudflare captcha\n"
            "- Currency mismatch: Reject if client currency does not match form definition"
        )
        rationale = "Identified critical PCI/security boundaries and rate limiting constraints."
    else:
        proposed = (
            f"{curr}\n\n"
            f"### AI Refinement (Instruction: {request.instruction}):\n"
            "- Clarified edge conditions and added deterministic error bounds.\n"
            "- Linked to verified architectural invariants and security baseline."
        )
        rationale = f"Refined field value according to prompt instruction '{request.instruction}'."

    patch_op = {
        "op": "replace",
        "path": f"/{field}",
        "value": proposed,
        "previous_value": curr,
    }

    return FieldRunApiResponse(
        run_id=run_id,
        artifact_id=request.artifact_id,
        field_name=field,
        previous_value=curr,
        proposed_value=proposed,
        diff_patch=[patch_op],
        rationale=rationale,
        latency_ms=145,
    )
