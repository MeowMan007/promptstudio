"""
TSK-056: Failure taxonomy + per-operation partial results.

Extends the patch engine with:
  - Documented error codes (taxonomy)
  - PartialResult: per-op status for multi-op patches
  - Helper to convert ValidationResult → PartialResult list

Error code taxonomy (exhaustive list):
  FIELD_LOCKED         — FieldBinding policy blocks write
  COOLDOWN_ACTIVE      — Binding cooldown window still active
  BINDING_NOT_FOUND    — No matching binding in registry
  SCHEMA_VIOLATION     — Output fails OutputContract schema check
  CONTEXT_ERROR        — Context assembly failed
  STALE_BASE           — UPDATE base_revision does not match current
  NOT_FOUND            — Artifact or edge does not exist
  PERM_DENIED          — Caller role insufficient
  APPROVAL_REQUIRED    — High-risk op needs a valid approval token
  INVALID_ID           — Malformed or missing ID
  MISSING_FIELD        — Required field absent
  UNKNOWN_TYPE         — Unrecognised artifact_type
  REF_NOT_FOUND        — Edge endpoint not found in project or patch creates
  AUTO_APPLY_DENIED    — Policy does not permit auto-apply for this caller
  IDEMPOTENT_SKIP      — Patch already applied; returned as a no-op
"""
from __future__ import annotations

import dataclasses as _dc
from dataclasses import dataclass
from enum import Enum
from typing import Any

from backend.app.patches.engine import OperationError, ValidationResult

field = _dc.field


# ---------------------------------------------------------------------------
# Canonical error codes
# ---------------------------------------------------------------------------

class ErrorCode(str, Enum):
    # Binding / field-run errors
    FIELD_LOCKED        = "FIELD_LOCKED"
    COOLDOWN_ACTIVE     = "COOLDOWN_ACTIVE"
    BINDING_NOT_FOUND   = "BINDING_NOT_FOUND"
    SCHEMA_VIOLATION    = "SCHEMA_VIOLATION"
    CONTEXT_ERROR       = "CONTEXT_ERROR"
    AUTO_APPLY_DENIED   = "AUTO_APPLY_DENIED"

    # Patch engine errors
    STALE_BASE          = "STALE_BASE"
    NOT_FOUND           = "NOT_FOUND"
    PERM_DENIED         = "PERM_DENIED"
    APPROVAL_REQUIRED   = "APPROVAL_REQUIRED"
    INVALID_ID          = "INVALID_ID"
    MISSING_FIELD       = "MISSING_FIELD"
    UNKNOWN_TYPE        = "UNKNOWN_TYPE"
    REF_NOT_FOUND       = "REF_NOT_FOUND"
    IDEMPOTENT_SKIP     = "IDEMPOTENT_SKIP"

    # Token errors
    TOKEN_NOT_FOUND     = "TOKEN_NOT_FOUND"
    TOKEN_EXPIRED       = "TOKEN_EXPIRED"
    TOKEN_CONSUMED      = "TOKEN_CONSUMED"


# ---------------------------------------------------------------------------
# Per-operation status (PartialResult)
# ---------------------------------------------------------------------------

class OpStatus(str, Enum):
    OK      = "ok"
    SKIPPED = "skipped"    # idempotent skip or layout-only
    FAILED  = "failed"


@dataclass
class PartialOpResult:
    """Status of one operation within a multi-op patch."""
    operation_index: int
    status: OpStatus
    code: str | None = None
    message: str | None = None
    field_name: str | None = None   # renamed to avoid shadowing 'field' builtin
    detail: dict[str, Any] = field(default_factory=dict)


@dataclass
class PartialResult:
    """
    Result of a multi-op patch where individual operations may succeed or fail.
    Use when partial application is allowed (not the default all-or-nothing mode).
    """
    patch_id: str
    overall_success: bool
    op_results: list[PartialOpResult] = field(default_factory=list)
    id_map: dict[str, str] = field(default_factory=dict)

    @property
    def failed_count(self) -> int:
        return sum(1 for r in self.op_results if r.status == OpStatus.FAILED)

    @property
    def succeeded_count(self) -> int:
        return sum(1 for r in self.op_results if r.status == OpStatus.OK)

    def to_dict(self) -> dict[str, Any]:
        return {
            "patch_id": self.patch_id,
            "overall_success": self.overall_success,
            "failed": self.failed_count,
            "succeeded": self.succeeded_count,
            "op_results": [
                {
                    "op_index": r.operation_index,
                    "status": r.status,
                    "code": r.code,
                    "message": r.message,
                    "field": r.field_name,
                }
                for r in self.op_results
            ],
        }


# ---------------------------------------------------------------------------
# Converter: ValidationResult → PartialResult
# ---------------------------------------------------------------------------

def validation_to_partial(
    validation: ValidationResult,
    patch_id: str,
    total_ops: int,
) -> PartialResult:
    """
    Convert a ValidationResult (all-or-nothing) into a PartialResult
    with per-operation status entries.
    """
    # Build a set of failed op indices
    failed_indices: dict[int, OperationError] = {
        e.operation_index: e for e in validation.errors
    }

    op_results: list[PartialOpResult] = []
    for idx in range(total_ops):
        if idx in failed_indices:
            err = failed_indices[idx]
            op_results.append(PartialOpResult(
                operation_index=idx,
                status=OpStatus.FAILED,
                code=err.code,
                message=err.message,
                field_name=err.field,
            ))
        else:
            op_results.append(PartialOpResult(
                operation_index=idx,
                status=OpStatus.OK,
            ))

    # Patch-level errors (operation_index == -1)
    patch_errors = [e for e in validation.errors if e.operation_index == -1]
    if patch_errors:
        # Prepend a synthetic index=-1 entry
        for pe in patch_errors:
            op_results.insert(0, PartialOpResult(
                operation_index=-1,
                status=OpStatus.FAILED,
                code=pe.code,
                message=pe.message,
            ))

    return PartialResult(
        patch_id=patch_id,
        overall_success=validation.valid,
        op_results=op_results,
    )


# ---------------------------------------------------------------------------
# Error description catalogue (for documentation / UI display)
# ---------------------------------------------------------------------------

ERROR_DESCRIPTIONS: dict[str, str] = {
    ErrorCode.FIELD_LOCKED:       "The target field is locked by a binding policy and cannot be written.",
    ErrorCode.COOLDOWN_ACTIVE:    "The binding's cooldown window is still active; retry after the specified delay.",
    ErrorCode.BINDING_NOT_FOUND:  "No matching FieldBinding found for the given artifact type and field path.",
    ErrorCode.SCHEMA_VIOLATION:   "The model's proposal does not satisfy the OutputContract's JSON schema.",
    ErrorCode.CONTEXT_ERROR:      "Context assembly failed; check upstream artifact availability.",
    ErrorCode.AUTO_APPLY_DENIED:  "The caller's role is not permitted to auto-apply this binding's proposal.",
    ErrorCode.STALE_BASE:         "The patch's base_revision does not match the artifact's current revision.",
    ErrorCode.NOT_FOUND:          "The referenced artifact or edge does not exist in the project.",
    ErrorCode.PERM_DENIED:        "The caller's role does not have permission to submit this patch.",
    ErrorCode.APPROVAL_REQUIRED:  "This operation requires a valid single-use approval token (tier-2).",
    ErrorCode.INVALID_ID:         "The provided ID is malformed or missing.",
    ErrorCode.MISSING_FIELD:      "A required field is absent from the operation.",
    ErrorCode.UNKNOWN_TYPE:       "The artifact_type is not recognised.",
    ErrorCode.REF_NOT_FOUND:      "An edge endpoint was not found in the project or the current patch's creates.",
    ErrorCode.IDEMPOTENT_SKIP:    "The patch_id has already been applied; this is a no-op.",
    ErrorCode.TOKEN_NOT_FOUND:    "The provided approval token does not exist in the store.",
    ErrorCode.TOKEN_EXPIRED:      "The approval token has expired.",
    ErrorCode.TOKEN_CONSUMED:     "The approval token has already been consumed (single-use).",
}
