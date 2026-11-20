"""
Canonical Template Registry for Prompt Studio.

Single source of truth for the 12 project starter blueprints,
their catalogue metadata, capabilities, design boundaries, and shared renderers.
All catalogue surfaces (/templates page, in-canvas modal, API) consume this registry.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class TemplateBlueprint:
    id: str
    title: str
    summary: str
    category: str
    category_label: str
    profile: str
    complexity: str
    tags: list[str]
    capabilities: list[str]
    scope_notes: str
    preview_nodes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "summary": self.summary,
            "category": self.category,
            "category_label": self.category_label,
            "profile": self.profile,
            "complexity": self.complexity,
            "tags": list(self.tags),
            "capabilities": list(self.capabilities),
            "scope_notes": self.scope_notes,
            "preview_nodes": list(self.preview_nodes),
        }


TEMPLATES_REGISTRY: list[TemplateBlueprint] = [
    TemplateBlueprint(
        id="b2b_saas",
        title="B2B Multi-Tenant SaaS",
        summary="Multi-tenant application architecture with tenant-scoped identity, PostgreSQL Row-Level Security (RLS) data isolation, subscription lifecycle, and asynchronous background worker queues.",
        category="saas",
        category_label="Core SaaS",
        profile="B2B SaaS Engineering Teams · Enterprise Product Architects",
        complexity="Intermediate",
        tags=["Traefik Gateway", "OIDC / SAML SSO", "PostgreSQL RLS", "Stripe Billing", "BullMQ"],
        capabilities=[
            "Tenant context resolution at API gateway",
            "PostgreSQL Row-Level Security (RLS) tenant isolation",
            "Subscription tier & feature entitlement enforcement",
            "Idempotent webhook ingestion with replay protection",
            "SCIM 2.0 user lifecycle provisioning",
        ],
        scope_notes="Design baseline assumes pooled PostgreSQL with enforced RLS; schema-per-tenant or silo models require architectural migration review.",
        preview_nodes=["Traefik Gateway", "OIDC SSO", "Domain API", "PostgreSQL RLS", "Stripe Billing"],
    ),
    TemplateBlueprint(
        id="fintech_ledger",
        title="Fintech Payment Gateway & Double-Entry Ledger",
        summary="Payment orchestration and merchant ledger platform featuring immutable double-entry journal entries, multi-rail gateway routing, three-way reconciliation, and tokenised cardholder data boundaries.",
        category="fintech",
        category_label="Fintech & Banking",
        profile="Fintech Engineers · Core Banking Architects · Payments Specialists",
        complexity="Advanced",
        tags=["Multi-Rail Gateway", "Double-Entry Engine", "3-Way Reconciliation", "Tokenised CDE Vault"],
        capabilities=[
            "Immutable double-entry ledger with debit/credit balance invariants",
            "Idempotency keys and distributed state machine for payments",
            "Automated 3-way reconciliation (gateway, processor, internal ledger)",
            "Tokenised card data environment boundary (offloading raw PAN storage)",
            "Dispute and chargeback lifecycle management",
        ],
        scope_notes="PCI DSS scope reduction is achieved via processor tokenisation; design does not constitute PCI certification or financial regulatory licensing.",
        preview_nodes=["Multi-Rail Ingress", "Fraud Scorer", "Double-Entry Ledger", "3-Way Recon", "KMS Vault"],
    ),
    TemplateBlueprint(
        id="event_streaming",
        title="Real-Time Event Streaming & Analytics",
        summary="High-volume operational telemetry platform with partition-keyed event ingestion, schema registry governance, stream processing, and dead-letter queue recovery.",
        category="data",
        category_label="Data & Streaming",
        profile="Data Platform Engineers · Telemetry Architects · SRE Teams",
        complexity="Advanced",
        tags=["Apache Kafka", "Apache Flink", "Schema Registry", "ClickHouse OLAP", "Vector / Fluent"],
        capabilities=[
            "Schema evolution governance with backward compatibility validation",
            "Tumbling and sliding window stream aggregations",
            "Partition-keyed ordering semantics and consumer group lag monitoring",
            "Quarantine and replay workflows for poison-pill events",
            "ClickHouse analytical store for sub-second aggregations",
        ],
        scope_notes="Delivery semantics are scoped per partition key; end-to-end exactly-once claims require application-layer idempotent sinks.",
        preview_nodes=["Vector Agent", "Kafka Cluster", "Flink Stream Engine", "ClickHouse OLAP", "DLQ Replay"],
    ),
    TemplateBlueprint(
        id="ecommerce_marketplace",
        title="Multi-Vendor Marketplace & Seller Payouts",
        summary="Multi-vendor commercial platform supporting catalogue management, multi-seller cart order splits, escrow-like hold-and-release payouts, and seller verification.",
        category="ecommerce",
        category_label="E-Commerce",
        profile="Marketplace Platform Teams · E-Commerce Architects",
        complexity="Intermediate",
        tags=["Algolia Search", "Redis Inventory Locks", "Order Orchestrator", "Split Transfers", "Seller Portal"],
        capabilities=[
            "Two-phase stock reservation with automatic expiry",
            "Multi-seller order splitting with independent fulfillment tracks",
            "Direct and transfer payment routing with platform fee splits",
            "Seller onboarding, KYC verification, and payout scheduling",
            "Customer return, dispute, and refund state workflows",
        ],
        scope_notes="Escrow and delayed payouts depend on payment provider capabilities and local licensing; terms subject to legal review.",
        preview_nodes=["Storefront CDN", "Order Orchestrator", "Inventory Lock", "Split Payout Engine", "Seller Ledger"],
    ),
    TemplateBlueprint(
        id="developer_platform",
        title="Developer API & Webhook Platform",
        summary="Public API infrastructure featuring tiered token-bucket rate limiting, scoped API key rotation, interactive documentation, and reliable HMAC-signed webhook delivery.",
        category="dev",
        category_label="Developer Tools",
        profile="Developer Experience Teams · Platform API Engineers",
        complexity="Intermediate",
        tags=["Kong Gateway", "Redis Token Bucket", "OpenAPI 3.1", "Webhook Dispatcher", "Developer Portal"],
        capabilities=[
            "Tiered rate limiting with sliding-window counters in Redis",
            "Scoped API key generation, hashing (SHA-256), and graceful rotation",
            "Webhook delivery with exponential backoff, HMAC-SHA256 signing, and DLQ",
            "Interactive OpenAPI 3.1 playground and code generation scaffolding",
            "Isolated sandbox environment for testing integrations without side effects",
        ],
        scope_notes="Webhook delivery guarantees at-least-once delivery; receiving endpoints must implement idempotent consumption.",
        preview_nodes=["Kong Gateway", "Redis Rate Limiter", "Webhook Dispatcher", "OpenAPI Docs", "Event Store"],
    ),
    TemplateBlueprint(
        id="collab_workspace",
        title="Collaborative Document & Canvas Workspace",
        summary="Multi-user real-time workspace featuring conflict-free replicated data types (CRDTs), ephemeral presence awareness, document snapshots, and workspace permissions.",
        category="saas",
        category_label="Productivity & Collaboration",
        profile="Collaboration Tool Engineers · Canvas Engine Developers",
        complexity="Advanced",
        tags=["Yjs CRDT", "WebSocket Sync", "Redis Pub/Sub", "Presence Awareness", "PostgreSQL Doc Store"],
        capabilities=[
            "Yjs CRDT synchronization for conflict-free concurrent editing",
            "Ephemeral cursor positions and presence awareness via Redis Pub/Sub",
            "Offline edit queuing and automatic reconciliation upon reconnect",
            "Periodic document snapshots and immutable revision history",
            "Role-based workspace and document-level permission controls",
        ],
        scope_notes="Awareness and cursor broadcast are explicitly separated from durable document storage to prevent database bloat.",
        preview_nodes=["WebSocket Gateway", "Yjs Sync Server", "Redis Awareness", "Doc Store", "Snapshot Worker"],
    ),
    TemplateBlueprint(
        id="healthcare_portal",
        title="Healthcare Patient Portal & FHIR Integration",
        summary="Patient engagement portal designed for interoperability with electronic health record (EHR) systems via HL7 FHIR R4 APIs, featuring attribute-based access and audit logging.",
        category="health",
        category_label="Healthcare & Life Sciences",
        profile="HealthTech Architects · Clinical Informatics Engineers",
        complexity="Specialized",
        tags=["FHIR R4 REST API", "SMART on FHIR", "PHI Access Control", "HL7 v2 ADT", "Encrypted Store"],
        capabilities=[
            "HL7 FHIR R4 standard resource models (Patient, Observation, Encounter)",
            "SMART on FHIR OAuth 2.0 authorization and clinical launch workflows",
            "Patient consent verification and field-level sensitive data masking",
            "HL7 v2 ADT event ingestion and transformation to FHIR encounters",
            "Immutable access auditing for Protected Health Information (PHI)",
        ],
        scope_notes="Design provides technical controls for HIPAA Security Rule alignment; requires formal risk assessment and BAA agreements before clinical deployment.",
        preview_nodes=["SMART Ingress", "FHIR R4 Gateway", "PHI Guardrail", "HL7 Listener", "Encrypted Clinical DB"],
    ),
    TemplateBlueprint(
        id="zero_trust_iam",
        title="Zero-Trust Identity & Access Management",
        summary="Enterprise identity governance framework enforcing continuous verification, Open Policy Agent (OPA) fine-grained authorization, device posture scoring, and ephemeral credentials.",
        category="security",
        category_label="Security & Identity",
        profile="Identity Architects · Enterprise Security Engineers",
        complexity="Advanced",
        tags=["OpenID Connect", "SCIM 2.0", "OPA Rego Policy", "Device Posture", "SPIFFE / SPIRE"],
        capabilities=[
            "Continuous trust evaluation combining user identity, device posture, and context",
            "Declarative policy decision point (PDP) using Open Policy Agent (OPA)",
            "Automated SCIM 2.0 provisioning and instant multi-system de-provisioning",
            "Short-lived workload identity issuance via SPIFFE / SPIRE mTLS",
            "Just-in-Time (JIT) privilege elevation with mandatory approval logs",
        ],
        scope_notes="Zero-trust requires holistic organizational implementation; architecture blueprint provides design patterns, not turnkey compliance.",
        preview_nodes=["IdP Federation", "SCIM Provisioner", "OPA Policy Engine", "Device Posture", "SPIFFE CA"],
    ),
    TemplateBlueprint(
        id="ai_agent_rag",
        title="Enterprise AI Agent & RAG Platform",
        summary="Autonomous agent and retrieval-augmented generation platform with pre-retrieval document ACL filtering, semantic vector search, tool guardrails, and execution auditing.",
        category="ai",
        category_label="AI & Agents",
        profile="AI Engineers · Enterprise Search Architects · ML Ops Teams",
        complexity="Advanced",
        tags=["Qdrant Vector DB", "Hybrid Search", "LangGraph Agent", "Guardrails AI", "Trace Log"],
        capabilities=[
            "Tenant and document ACL enforcement prior to model context assembly",
            "Hybrid lexical and vector semantic retrieval with cross-encoder reranking",
            "Autonomous multi-step agent orchestrator with human-in-the-loop approvals",
            "Prompt injection defense and structured schema output validation",
            "End-to-end token attribution, trace logging, and evaluation metrics",
        ],
        scope_notes="Content retrieval is filtered at query time to prevent unauthorized context leakage; model outputs require human sign-off for critical actions.",
        preview_nodes=["Ingestion Pipeline", "Qdrant Vector DB", "LangGraph Agent", "Guardrails Gateway", "Trace Store"],
    ),
    TemplateBlueprint(
        id="global_payroll",
        title="Global Payroll & Tax Engine",
        summary="Deterministic gross-to-net payroll engine supporting versioned jurisdiction rule packs, multi-currency processing, effective-dated contracts, and statutory remittance.",
        category="fintech",
        category_label="Fintech & Payroll",
        profile="Payroll Engineers · Enterprise ERP Architects",
        complexity="Specialized",
        tags=["Gross-to-Net Engine", "Versioned Rule Packs", "Effective Dating", "SEPA / ACH Disburse", "Statutory Audit"],
        capabilities=[
            "Deterministic calculation pipeline with immutable run snapshots",
            "Effective-dated jurisdiction tax rules and localized deduction schedules",
            "Pre-flight payroll preview and anomaly detection exception queue",
            "Multi-rail bank disbursement batch generation (SEPA, BACS, ACH)",
            "Statutory tax filing and General Ledger export formatting",
        ],
        scope_notes="Tax calculations use versioned rule pack approximations; legal and accounting review required per operating jurisdiction.",
        preview_nodes=["Payroll Ingress", "Rule Pack Engine", "Gross-to-Net Runner", "Disbursement Batch", "GL Export"],
    ),
    TemplateBlueprint(
        id="legaltech_clm",
        title="LegalTech Contract Lifecycle Management",
        summary="Enterprise contract management platform covering clause assembly, tracked redlining, multi-tier approval routing, ethical walls, and e-signature envelope tracking.",
        category="saas",
        category_label="LegalTech & Enterprise",
        profile="Legal Operations Engineers · CLM Platform Architects",
        complexity="Intermediate",
        tags=["Clause Library", "Diff / Redline Engine", "Ethical Walls", "DocuSign Adapter", "Obligations Tracker"],
        capabilities=[
            "Approved clause library assembly with deviation risk scoring",
            "Side-by-side version comparison and tracked change redline engine",
            "Ethical wall conflict-of-interest access boundaries between business units",
            "E-signature envelope dispatch, webhook status tracking, and tamper sealing",
            "Post-execution calendar milestone and renewal obligation alerting",
        ],
        scope_notes="AI clause extraction and redlining provide assistive tooling; legal validity and final execution remain subject to licensed counsel.",
        preview_nodes=["Contract Intake", "Clause Library", "Redline Engine", "Ethical Wall Gate", "Signature Vault"],
    ),
    TemplateBlueprint(
        id="logistics_supply_chain",
        title="Logistics & Cold-Chain Supply Chain Platform",
        summary="Global freight visibility platform tracking multi-modal shipments, IoT sensor cold-chain temperature telemetry, EDI X12 transaction sets, and cryptographic proof-of-delivery.",
        category="ops",
        category_label="Supply Chain & IoT",
        profile="Logistics Engineers · IoT Telematics Architects",
        complexity="Advanced",
        tags=["EMQX MQTT", "TimescaleDB", "EDI X12 Engine", "Geofencing", "Ed25519 Cryptographic POD"],
        capabilities=[
            "MQTT telematics ingestion with local offline excursion alarms on device",
            "TimescaleDB hypertable storage for time-series temperature readings",
            "Polygon geofence entry/exit detection and automated shipment milestone advance",
            "EDI X12 protocol processing (204 load tender, 214 status, 210 freight invoice)",
            "Cryptographic proof-of-delivery (POD) with Ed25519 signatures and GPS stamps",
        ],
        scope_notes="Safety-critical cold-chain excursion alarms operate autonomously on edge devices; cloud telemetry provides audit and monitoring.",
        preview_nodes=["EMQX Broker", "TimescaleDB", "Geofence Engine", "EDI X12 Translator", "POD Signer"],
    ),
]

TEMPLATES_BY_ID: dict[str, TemplateBlueprint] = {t.id: t for t in TEMPLATES_REGISTRY}


def get_template(template_id: str) -> TemplateBlueprint | None:
    return TEMPLATES_BY_ID.get(template_id)


def render_templates_page_cards_html() -> str:
    """Renders all 12 cards for the public /templates page."""
    cards_html = []
    for tpl in TEMPLATES_REGISTRY:
        preview_nodes_html = "".join(
            f'<div class="cp-node">{n}</div>' for n in tpl.preview_nodes
        )
        tags_html = "".join(
            f'<span style="display:inline-block;padding:2px 7px;border-radius:4px;font-size:11px;background:#f1f5f9;color:#475569;margin-right:4px;margin-bottom:4px;">{tag}</span>'
            for tag in tpl.tags
        )
        capabilities_html = "".join(
            f"<li style=\"margin-bottom:3px;\">{cap}</li>" for cap in tpl.capabilities[:3]
        )
        card = f"""
    <div class="card" onclick="location.href='/board?template={tpl.id}'">
      <div class="card-preview">
        {preview_nodes_html}
      </div>
      <div class="card-body">
        <div class="card-top">
          <div class="card-title">{tpl.title}</div>
          <span class="card-badge">{tpl.category_label}</span>
        </div>
        <div class="card-desc">{tpl.summary}</div>
        <div style="margin: 6px 0;">
          {tags_html}
        </div>
        <ul style="font-size:12px;color:var(--text-muted);padding-left:16px;margin:4px 0 8px;">
          {capabilities_html}
        </ul>
        <div class="card-meta">
          <span>Complexity: <strong>{tpl.complexity}</strong></span>
          <span>Target: <strong>{tpl.profile.split('·')[0].strip()}</strong></span>
        </div>
      </div>
      <div class="card-footer">
        <span class="card-footer-text">Includes architecture, wireframes, ERD &amp; delivery tasks</span>
        <span class="card-open">Open Blueprint &rarr;</span>
      </div>
    </div>
"""
        cards_html.append(card)
    return "\n".join(cards_html)


def render_modal_cards_html() -> str:
    """Renders all 12 cards for the in-canvas modal picker."""
    cards_html = []
    for tpl in TEMPLATES_REGISTRY:
        keywords = f"{tpl.id} {tpl.category} {' '.join(tpl.tags)} {tpl.title}".lower()
        tags_html = "".join(
            f'<span class="template-tech-tag">{tag}</span>' for tag in tpl.tags
        )
        badge_class = f"template-badge-{tpl.category}"
        card = f"""
        <div class="template-card" data-cat="{tpl.category}" data-keywords="{keywords}">
          <div>
            <div class="template-card-top">
              <span class="template-badge {badge_class}">{tpl.category_label}</span>
              <span class="template-spec-pill">{tpl.complexity} &middot; Complete Blueprint</span>
            </div>
            <div class="template-card-title" style="margin-top: 6px;">{tpl.title}</div>
            <div class="template-card-desc">{tpl.summary}</div>
          </div>
          <div>
            <div class="template-tech-tags">
              {tags_html}
            </div>
            <div class="template-card-footer">
              <button class="btn btn-primary" style="flex: 1; justify-content: center;" onclick="applyTemplate('{tpl.id}', true)">Use Blueprint</button>
              <button class="btn" title="Add to current canvas without clearing" onclick="applyTemplate('{tpl.id}', false)">+ Append</button>
            </div>
          </div>
        </div>
"""
        cards_html.append(card)
    return "\n".join(cards_html)
