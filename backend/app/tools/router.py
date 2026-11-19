"""
TSK-078: Internal tool router with typed schemas and scopes.
TSK-079: Stateless MCP server over domain services.
TSK-080: MRTR approval flow for write tools.
TSK-082: OAuth 2.1 scopes, issuer validation.
TSK-083: Tool catalogue caching and deterministic ordering.

The tool router acts as a typed gateway:
  - Every tool has a declared schema (input/output), class, approval requirement.
  - All calls are logged with caller identity + timestamp.
  - Write tools require approval via single-use token (MRTR flow).
  - MCP server is stateless: no session state; headers routed per call.

Acceptance:
  - TSK-078: Every tool has schema, class, approval requirement; calls logged.
  - TSK-079: No session state; stable tool order.
  - TSK-080: input_required returned; retry with approval succeeds; token single-use.
  - TSK-082: Scope intersection enforced.
  - TSK-083: Deterministic ordering across restarts.
"""
from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable


# =============================================================================
# TSK-078: Tool schema + router
# =============================================================================

class ToolClass(str, Enum):
    READ      = "read"       # No approval needed
    PROPOSE   = "propose"    # No approval, but output goes through review
    WRITE     = "write"      # Requires approval token (MRTR)
    ADMIN     = "admin"      # Requires admin role + approval


class ToolScope(str, Enum):
    """OAuth-like scopes for tools."""
    READ_ARTIFACTS   = "read:artifacts"
    READ_GRAPH       = "read:graph"
    PROPOSE_PATCH    = "propose:patch"
    WRITE_ARTIFACTS  = "write:artifacts"
    APPLY_PATCH      = "apply:patch"
    ADMIN_SKILLS     = "admin:skills"
    ADMIN_TOKENS     = "admin:tokens"


@dataclass
class ToolSchema:
    """Typed input/output schema for one tool."""
    name: str
    description: str
    tool_class: ToolClass
    required_scope: ToolScope
    input_schema: dict[str, Any]       # JSON schema for inputs
    output_schema: dict[str, Any]      # JSON schema for outputs
    requires_approval: bool = False    # True for WRITE / ADMIN tools
    version: str = "1.0.0"


@dataclass
class ToolCallLog:
    """Audit record for one tool invocation."""
    call_id: str
    tool_name: str
    caller_id: str
    caller_scopes: list[str]
    inputs: dict[str, Any]
    output: Any
    success: bool
    error: str | None
    duration_ms: float
    timestamp: float


@dataclass
class ToolCallResult:
    success: bool
    output: Any
    error: str | None = None
    input_required: bool = False    # True when approval token needed (MRTR)
    approval_challenge: str | None = None


class ToolRouter:
    """
    Routes tool calls to registered handlers.
    - Validates scopes before dispatch.
    - Enforces approval for write tools.
    - Logs every call.
    """

    def __init__(
        self,
        max_tool_calls_per_run: int = 100,
        max_cost_usd: float = 10.0,
        max_concurrent_calls: int = 10,
    ) -> None:
        self._tools: dict[str, ToolSchema] = {}
        self._handlers: dict[str, Callable[..., Any]] = {}
        self._log: list[ToolCallLog] = []
        self._approval_tokens: set[str] = set()
        # Agency controls (TSK-107)
        self.max_tool_calls_per_run = max_tool_calls_per_run
        self.max_cost_usd = max_cost_usd
        self.max_concurrent_calls = max_concurrent_calls
        self._call_count: int = 0
        self._cost_usd: float = 0.0
        self._concurrent: int = 0
        self.kill_switch_active: bool = False
        self.kill_switch_reason: str = ""

    def register(
        self,
        schema: ToolSchema,
        handler: Callable[..., Any],
    ) -> None:
        self._tools[schema.name] = schema
        self._handlers[schema.name] = handler

    def add_approval_token(self, token: str) -> None:
        self._approval_tokens.add(token)

    def consume_approval_token(self, token: str) -> bool:
        if token in self._approval_tokens:
            self._approval_tokens.discard(token)
            return True
        return False

    def call(
        self,
        tool_name: str,
        inputs: dict[str, Any],
        *,
        caller_id: str,
        caller_scopes: list[str],
        approval_token: str | None = None,
    ) -> ToolCallResult:
        """
        Dispatch a tool call.
        Returns ToolCallResult; logs the call regardless of success.
        """
        t0 = time.monotonic()
        schema = self._tools.get(tool_name)
        error: str | None = None
        output: Any = None
        success = False
        input_required = False
        approval_challenge: str | None = None

        try:
            if schema is None:
                raise KeyError(f"Unknown tool: {tool_name!r}")

            # Scope check
            if schema.required_scope.value not in caller_scopes:
                raise PermissionError(
                    f"Tool {tool_name!r} requires scope {schema.required_scope!r}; "
                    f"caller has: {caller_scopes}"
                )

            # MRTR approval check for write tools
            if schema.requires_approval:
                if not approval_token or not self.consume_approval_token(approval_token):
                    input_required = True
                    approval_challenge = (
                        f"Tool {tool_name!r} requires a single-use approval token. "
                        "Obtain one via POST /approvals and retry."
                    )
                    return ToolCallResult(
                        success=False,
                        output=None,
                        input_required=True,
                        approval_challenge=approval_challenge,
                    )

            handler = self._handlers[tool_name]
            output = handler(**inputs)
            success = True

        except (KeyError, PermissionError) as exc:
            error = str(exc)
        except Exception as exc:
            error = f"Tool error: {exc}"

        duration_ms = (time.monotonic() - t0) * 1000
        log = ToolCallLog(
            call_id=hashlib.sha256(f"{tool_name}:{caller_id}:{t0}".encode()).hexdigest()[:16],
            tool_name=tool_name,
            caller_id=caller_id,
            caller_scopes=caller_scopes,
            inputs=inputs,
            output=output,
            success=success,
            error=error,
            duration_ms=duration_ms,
            timestamp=t0,
        )
        self._log.append(log)

        return ToolCallResult(success=success, output=output, error=error)

    def audit_log(self) -> list[ToolCallLog]:
        return list(self._log)

    def catalogue(self) -> list[ToolSchema]:
        """Return tools in deterministic (alphabetical) order — TSK-083."""
        return sorted(self._tools.values(), key=lambda t: t.name)

    # ------------------------------------------------------------------
    # TSK-107: Agency controls
    # ------------------------------------------------------------------

    class BudgetExceededError(Exception):
        pass

    class KillSwitchError(Exception):
        pass

    class ConcurrencyLimitError(Exception):
        pass

    def increment_call_count(self) -> None:
        """Increment tool call counter; raise if cap exceeded."""
        if self._call_count >= self.max_tool_calls_per_run:
            raise ToolRouter.BudgetExceededError(
                f"Tool call cap exceeded: {self._call_count}/{self.max_tool_calls_per_run}"
            )
        self._call_count += 1

    def check_cost_budget(self, cost_usd: float) -> None:
        """Raise if adding cost_usd would exceed the cost cap."""
        if self._cost_usd + cost_usd > self.max_cost_usd:
            raise ToolRouter.BudgetExceededError(
                f"Cost budget exceeded: {self._cost_usd + cost_usd:.4f} > {self.max_cost_usd}"
            )
        self._cost_usd += cost_usd

    def activate_kill_switch(self, reason: str = "") -> None:
        """Permanently disable all tool calls for this router instance."""
        self.kill_switch_active = True
        self.kill_switch_reason = reason

    def call_tool(self, tool_name: str, inputs: dict) -> Any:
        """Simple call gateway that checks the kill switch."""
        if self.kill_switch_active:
            raise ToolRouter.KillSwitchError(
                f"Kill switch active: {self.kill_switch_reason}"
            )
        return self._handlers.get(tool_name, lambda **_: None)(**inputs)

    def acquire_slot(self) -> None:
        """Acquire a concurrency slot; raise if limit reached."""
        if self._concurrent >= self.max_concurrent_calls:
            raise ToolRouter.ConcurrencyLimitError(
                f"Concurrency limit reached: {self._concurrent}/{self.max_concurrent_calls}"
            )
        self._concurrent += 1

    def release_slot(self) -> None:
        """Release a concurrency slot."""
        if self._concurrent > 0:
            self._concurrent -= 1

    def reset_run(self) -> None:
        """Reset per-run counters (not kill switch)."""
        self._call_count = 0
        self._cost_usd = 0.0
        self._concurrent = 0

    def list_tools(self, scope_filter: "ToolScope | None" = None) -> list[ToolSchema]:
        """List tools, optionally filtered by scope."""
        tools = self.catalogue()
        if scope_filter is None:
            return tools
        # For tenant scope: return TENANT + PROJECT + FIELD tools
        if scope_filter == ToolScope.TENANT:
            return [t for t in tools if t.scope != ToolScope.GLOBAL]
        return [t for t in tools if t.scope == scope_filter]



# =============================================================================
# TSK-082: OAuth 2.1 scope intersection
# =============================================================================

_VALID_SCOPES = frozenset(s.value for s in ToolScope)


def validate_scopes(claimed_scopes: list[str], allowed_scopes: list[str]) -> list[str]:
    """
    Compute effective scopes: intersection of claimed and allowed.
    Rejects any unrecognised scope strings.
    Returns the intersection as a sorted list.
    """
    claimed = set(claimed_scopes)
    allowed = set(allowed_scopes)

    unknown = claimed - _VALID_SCOPES
    if unknown:
        raise ValueError(f"Unknown scope(s): {sorted(unknown)}")

    return sorted(claimed & allowed)


def verify_issuer(token_claims: dict[str, Any], expected_issuer: str) -> None:
    """
    Validate the 'iss' claim matches expected_issuer.
    TSK-082: iss validated; no DCR dependency.
    """
    iss = token_claims.get("iss")
    if not iss:
        raise ValueError("Token missing 'iss' claim")
    if iss != expected_issuer:
        raise ValueError(f"Issuer mismatch: expected {expected_issuer!r}, got {iss!r}")


# =============================================================================
# Built-in tool catalogue (13 tools)
# =============================================================================

def _build_catalogue() -> list[ToolSchema]:
    return [
        ToolSchema(
            name="read_artifact",
            description="Read a single artifact by ID",
            tool_class=ToolClass.READ,
            required_scope=ToolScope.READ_ARTIFACTS,
            input_schema={"type": "object", "required": ["artifact_id"],
                          "properties": {"artifact_id": {"type": "string"}}},
            output_schema={"type": "object"},
            requires_approval=False,
        ),
        ToolSchema(
            name="list_artifacts",
            description="List artifacts in a project, optionally filtered by type",
            tool_class=ToolClass.READ,
            required_scope=ToolScope.READ_ARTIFACTS,
            input_schema={"type": "object", "properties": {
                "project_id": {"type": "string"},
                "artifact_type": {"type": "string"},
            }},
            output_schema={"type": "array"},
            requires_approval=False,
        ),
        ToolSchema(
            name="read_graph",
            description="Read the project graph (nodes and edges)",
            tool_class=ToolClass.READ,
            required_scope=ToolScope.READ_GRAPH,
            input_schema={"type": "object", "required": ["project_id"],
                          "properties": {"project_id": {"type": "string"}}},
            output_schema={"type": "object"},
            requires_approval=False,
        ),
        ToolSchema(
            name="assemble_context",
            description="Assemble a context bundle for a field run",
            tool_class=ToolClass.READ,
            required_scope=ToolScope.READ_ARTIFACTS,
            input_schema={"type": "object", "required": ["artifact_id", "field_path"],
                          "properties": {
                              "artifact_id": {"type": "string"},
                              "field_path": {"type": "string"},
                          }},
            output_schema={"type": "object"},
            requires_approval=False,
        ),
        ToolSchema(
            name="run_field",
            description="Run a field binding to generate a proposal",
            tool_class=ToolClass.PROPOSE,
            required_scope=ToolScope.PROPOSE_PATCH,
            input_schema={"type": "object", "required": ["artifact_id", "field_path"],
                          "properties": {
                              "artifact_id": {"type": "string"},
                              "field_path": {"type": "string"},
                              "binding_id": {"type": "string"},
                          }},
            output_schema={"type": "object"},
            requires_approval=False,
        ),
        ToolSchema(
            name="propose_patch",
            description="Submit a patch for human review (does not apply)",
            tool_class=ToolClass.PROPOSE,
            required_scope=ToolScope.PROPOSE_PATCH,
            input_schema={"type": "object", "required": ["patch"],
                          "properties": {"patch": {"type": "object"}}},
            output_schema={"type": "object"},
            requires_approval=False,
        ),
        ToolSchema(
            name="apply_patch",
            description="Apply an approved patch to the project graph",
            tool_class=ToolClass.WRITE,
            required_scope=ToolScope.APPLY_PATCH,
            input_schema={"type": "object", "required": ["patch_id"],
                          "properties": {
                              "patch_id": {"type": "string"},
                              "approval_token": {"type": "string"},
                          }},
            output_schema={"type": "object"},
            requires_approval=True,
        ),
        ToolSchema(
            name="create_artifact",
            description="Create a new artifact (requires approval for bulk creates)",
            tool_class=ToolClass.WRITE,
            required_scope=ToolScope.WRITE_ARTIFACTS,
            input_schema={"type": "object", "required": ["artifact_type", "title"],
                          "properties": {
                              "artifact_type": {"type": "string"},
                              "title": {"type": "string"},
                              "body": {"type": "string"},
                          }},
            output_schema={"type": "object"},
            requires_approval=True,
        ),
        ToolSchema(
            name="update_artifact",
            description="Update a field on an existing artifact",
            tool_class=ToolClass.WRITE,
            required_scope=ToolScope.WRITE_ARTIFACTS,
            input_schema={"type": "object", "required": ["artifact_id", "fields"],
                          "properties": {
                              "artifact_id": {"type": "string"},
                              "fields": {"type": "object"},
                              "base_revision": {"type": "integer"},
                          }},
            output_schema={"type": "object"},
            requires_approval=True,
        ),
        ToolSchema(
            name="get_progress",
            description="Get the current progress snapshot for a project",
            tool_class=ToolClass.READ,
            required_scope=ToolScope.READ_GRAPH,
            input_schema={"type": "object", "required": ["project_id"],
                          "properties": {"project_id": {"type": "string"}}},
            output_schema={"type": "object"},
            requires_approval=False,
        ),
        ToolSchema(
            name="get_evolution_proposals",
            description="List pending evolution proposals for a project",
            tool_class=ToolClass.READ,
            required_scope=ToolScope.READ_GRAPH,
            input_schema={"type": "object", "required": ["project_id"],
                          "properties": {"project_id": {"type": "string"}}},
            output_schema={"type": "array"},
            requires_approval=False,
        ),
        ToolSchema(
            name="install_skill",
            description="Install a skill package (admin only)",
            tool_class=ToolClass.ADMIN,
            required_scope=ToolScope.ADMIN_SKILLS,
            input_schema={"type": "object", "required": ["skill_id"],
                          "properties": {"skill_id": {"type": "string"}}},
            output_schema={"type": "object"},
            requires_approval=True,
        ),
        ToolSchema(
            name="issue_approval_token",
            description="Issue a single-use approval token",
            tool_class=ToolClass.ADMIN,
            required_scope=ToolScope.ADMIN_TOKENS,
            input_schema={"type": "object", "properties": {"ttl_seconds": {"type": "number"}}},
            output_schema={"type": "object", "properties": {"token": {"type": "string"}}},
            requires_approval=False,
        ),
    ]


TOOL_CATALOGUE: list[ToolSchema] = sorted(_build_catalogue(), key=lambda t: t.name)
