"""
TSK-059: Model adapter — provider-neutral, schema-constrained, bounded retries.

Provides a single interface for all model calls:
  ModelAdapter.generate(prompt, schema, ...) -> GenerationResult

Supports:
  - Provider-neutral: OpenAI, Anthropic, stub (all same interface)
  - Schema-constrained outputs: validates against JSON schema before returning
  - Bounded retries: retries on schema violations up to max_retries
  - Structured outputs: requests JSON mode / tool-use where available

Acceptance (TSK-059):
  - Provider-neutral (pluggable provider registry).
  - Schema-constrained where supported; validation error triggers retry.
  - Bounded retries (default 3).
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Protocol


# ---------------------------------------------------------------------------
# Provider protocol
# ---------------------------------------------------------------------------

class ModelProvider(Protocol):
    """
    Protocol that every model provider adapter must implement.
    Real providers call their SDK here; stub returns deterministic output.
    """
    name: str

    def complete(
        self,
        messages: list[dict[str, str]],
        *,
        json_mode: bool = False,
        schema: dict[str, Any] | None = None,
        temperature: float = 0.3,
        max_tokens: int = 2048,
    ) -> str:
        """Return raw string completion."""
        ...


# ---------------------------------------------------------------------------
# Stub provider (deterministic, no network)
# ---------------------------------------------------------------------------

class StubProvider:
    """Deterministic stub — returns JSON or plain string based on prompt hash."""
    name = "stub"

    def complete(
        self,
        messages: list[dict[str, str]],
        *,
        json_mode: bool = False,
        schema: dict[str, Any] | None = None,
        temperature: float = 0.3,
        max_tokens: int = 2048,
    ) -> str:
        # Deterministic output from message hash
        content = "".join(m.get("content", "") for m in messages)
        h = hashlib.sha256(content.encode()).hexdigest()[:8]
        schema_type = (schema or {}).get("type", "string")

        if json_mode or schema_type in ("object", "array"):
            if schema_type == "array":
                return json.dumps([f"item-{h[:4]}", f"item-{h[4:8]}"])
            else:
                # Build object from schema required fields if present
                required = (schema or {}).get("required", [])
                obj = {r: f"value-{h[:4]}" for r in required} if required else {"result": f"result-{h}"}
                return json.dumps(obj)
        else:
            return f"[stub response {h}]"


# ---------------------------------------------------------------------------
# Generation result
# ---------------------------------------------------------------------------

@dataclass
class GenerationResult:
    provider: str
    raw_text: str
    parsed: Any                    # None if schema_type is "string"
    schema_valid: bool
    violations: list[str]
    attempts: int
    tokens_used: int               # estimated

    @property
    def value(self) -> Any:
        """The parsed value (or raw string for string schema)."""
        return self.parsed if self.parsed is not None else self.raw_text


# ---------------------------------------------------------------------------
# Schema validator (lightweight)
# ---------------------------------------------------------------------------

def _validate_schema(value: Any, schema: dict[str, Any]) -> list[str]:
    """Return list of violation strings (empty = valid)."""
    violations: list[str] = []
    schema_type = schema.get("type")

    if schema_type == "string" and not isinstance(value, str):
        violations.append(f"expected string, got {type(value).__name__}")
    elif schema_type == "array" and not isinstance(value, list):
        violations.append(f"expected array, got {type(value).__name__}")
    elif schema_type == "object" and not isinstance(value, dict):
        violations.append(f"expected object, got {type(value).__name__}")

    if schema_type in ("object",) and isinstance(value, dict):
        for req in schema.get("required", []):
            if req not in value:
                violations.append(f"required field missing: {req!r}")

    min_len = schema.get("minLength")
    if min_len is not None and isinstance(value, str) and len(value) < min_len:
        violations.append(f"string shorter than minLength {min_len}")

    max_items = schema.get("maxItems")
    if max_items is not None and isinstance(value, list) and len(value) > max_items:
        violations.append(f"array longer than maxItems {max_items}")

    return violations


# ---------------------------------------------------------------------------
# Provider registry
# ---------------------------------------------------------------------------

_PROVIDER_REGISTRY: dict[str, ModelProvider] = {
    "stub": StubProvider(),  # type: ignore[assignment]
}


def register_provider(name: str, provider: ModelProvider) -> None:
    """Register a model provider by name."""
    _PROVIDER_REGISTRY[name] = provider


def get_provider(name: str) -> ModelProvider:
    """Return a registered provider, or raise KeyError."""
    if name not in _PROVIDER_REGISTRY:
        raise KeyError(f"Unknown model provider: {name!r}. Registered: {list(_PROVIDER_REGISTRY)}")
    return _PROVIDER_REGISTRY[name]


# ---------------------------------------------------------------------------
# Model adapter (main entry point)
# ---------------------------------------------------------------------------

class ModelAdapter:
    """
    Provider-neutral model adapter with schema validation and bounded retries.

    Usage:
        adapter = ModelAdapter(provider="stub")
        result = adapter.generate(
            system_prompt="You are a helpful assistant.",
            user_prompt="Write a user story about login.",
            schema={"type": "string"},
        )
        print(result.value)
    """

    def __init__(
        self,
        provider: str = "stub",
        max_retries: int = 3,
        temperature: float = 0.3,
        max_tokens: int = 2048,
    ) -> None:
        self._provider_name = provider
        self._provider = get_provider(provider)
        self.max_retries = max_retries
        self.temperature = temperature
        self.max_tokens = max_tokens

    def generate(
        self,
        *,
        system_prompt: str = "",
        user_prompt: str,
        schema: dict[str, Any] | None = None,
        extra_context: str = "",
    ) -> GenerationResult:
        """
        Call the model and validate output against schema, retrying on violations.

        Parameters
        ----------
        system_prompt: Instructions to the model.
        user_prompt: The user/task prompt.
        schema: JSON schema the output must satisfy.
        extra_context: Additional context appended to user_prompt.

        Returns
        -------
        GenerationResult with schema_valid=True, or last attempt's result
        after max_retries exhausted.
        """
        schema = schema or {}
        schema_type = schema.get("type", "string")
        json_mode = schema_type in ("object", "array")

        messages: list[dict[str, str]] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        full_user = user_prompt
        if extra_context:
            full_user = f"{user_prompt}\n\n---\n{extra_context}"
        messages.append({"role": "user", "content": full_user})

        last_result: GenerationResult | None = None

        for attempt in range(1, self.max_retries + 1):
            raw = self._provider.complete(
                messages,
                json_mode=json_mode,
                schema=schema,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
            )

            # Parse if JSON mode
            parsed: Any = None
            parse_error: str | None = None
            if json_mode:
                try:
                    parsed = json.loads(raw)
                except json.JSONDecodeError as e:
                    parse_error = f"JSON parse error: {e}"

            if parse_error:
                violations = [parse_error]
                schema_valid = False
            else:
                value_to_check = parsed if json_mode else raw
                violations = _validate_schema(value_to_check, schema) if schema else []
                schema_valid = len(violations) == 0

            tokens_used = max(1, len(raw) // 4)
            last_result = GenerationResult(
                provider=self._provider_name,
                raw_text=raw,
                parsed=parsed,
                schema_valid=schema_valid,
                violations=violations,
                attempts=attempt,
                tokens_used=tokens_used,
            )

            if schema_valid:
                return last_result

            # Retry with violation feedback appended
            retry_msg = (
                f"\n\n[Retry {attempt}/{self.max_retries}] Previous output had violations: "
                + "; ".join(violations)
                + ". Please fix and respond with valid output."
            )
            messages.append({"role": "assistant", "content": raw})
            messages.append({"role": "user", "content": retry_msg})

        return last_result  # type: ignore[return-value]

    def switch_provider(self, name: str) -> None:
        """Hot-swap the underlying provider (e.g., fallback on rate-limit)."""
        self._provider = get_provider(name)
        self._provider_name = name
