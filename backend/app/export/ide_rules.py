"""TSK-092: Cursor .mdc rules + GitHub Copilot instructions generator.

Generates IDE-specific rule files for Cursor and GitHub Copilot from project
context (spec sections 22.2, 22.3).

Cursor rules: `.cursor/rules/<name>.mdc` with YAML frontmatter + markdown body.
Copilot:      `.github/copilot-instructions.md`
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class CursorRuleType(str, Enum):
    """Cursor MDC rule types — control when the rule is attached."""
    ALWAYS = "always"          # always attached in context
    AUTO_ATTACHED = "auto"     # attached when matching globs are open
    AGENT_REQUESTED = "agent"  # agent can request this rule
    MANUAL = "manual"          # user must reference it explicitly


@dataclass
class CursorRule:
    """A single Cursor .mdc rule."""
    name: str                            # filename stem (no .mdc)
    rule_type: CursorRuleType
    description: str                     # short description in frontmatter
    body: str                            # markdown rule content
    globs: list[str] = field(default_factory=list)  # for AUTO_ATTACHED


def _mdc_frontmatter(rule: CursorRule) -> str:
    lines = ["---"]
    lines.append(f"description: {rule.description}")
    lines.append(f"globs: {rule.globs!r}" if rule.globs else "globs: []")
    lines.append(f"alwaysApply: {'true' if rule.rule_type == CursorRuleType.ALWAYS else 'false'}")
    lines.append("---")
    return "\n".join(lines)


def _build_rule_file(rule: CursorRule) -> str:
    fm = _mdc_frontmatter(rule)
    return f"{fm}\n\n{rule.body.strip()}\n"


# ---------------------------------------------------------------------------
# Default rules built from project context
# ---------------------------------------------------------------------------

def _default_rules(project_name: str, boundaries: dict[str, list[str]]) -> list[CursorRule]:
    always_items = boundaries.get("always", [
        "Validate before persist",
        "Write revisions and audit events",
        "Keep layout separate from semantics",
        "Preserve user edits",
        "Run verify commands",
    ])
    ask_items = boundaries.get("ask_first", [
        "Schema or migration changes",
        "New dependencies",
        "Permission changes",
    ])
    never_items = boundaries.get("never", [
        "Commit secrets",
        "Execute model-generated code in the API process",
        "Bypass the patch service",
        "Delete failing tests",
    ])

    def bullet(items: list[str]) -> str:
        return "\n".join(f"- {i}" for i in items)

    core = CursorRule(
        name="000-core-boundaries",
        rule_type=CursorRuleType.ALWAYS,
        description=f"Core boundary rules for {project_name}",
        body=(
            f"# Core Boundaries — {project_name}\n\n"
            f"## Always\n\n{bullet(always_items)}\n\n"
            f"## Ask First\n\n{bullet(ask_items)}\n\n"
            f"## Never\n\n{bullet(never_items)}\n"
        ),
    )

    python_rule = CursorRule(
        name="010-python-style",
        rule_type=CursorRuleType.AUTO_ATTACHED,
        description="Python type-hint and Pydantic style rules",
        globs=["**/*.py"],
        body=(
            "# Python Style\n\n"
            "- Use full type hints on all public functions and class attributes.\n"
            "- Use Pydantic models at API/service boundaries; raw dicts are banned there.\n"
            "- Repositories own all SQL; never write raw queries outside `repositories/`.\n"
            "- Async functions must use `asyncio.mode = strict`.\n"
        ),
    )

    ts_rule = CursorRule(
        name="010-typescript-style",
        rule_type=CursorRuleType.AUTO_ATTACHED,
        description="TypeScript strict-mode style rules",
        globs=["**/*.ts", "**/*.tsx"],
        body=(
            "# TypeScript Style\n\n"
            "- Enable `strict: true` in tsconfig.\n"
            "- Never hand-edit generated contract types (packages/contracts).\n"
            "- Canvas engine types stay in packages/canvas — do not leak to apps.\n"
            "- Use named exports; avoid default exports except for React page components.\n"
        ),
    )

    test_rule = CursorRule(
        name="020-testing",
        rule_type=CursorRuleType.AUTO_ATTACHED,
        description="Testing conventions",
        globs=["tests/**", "**/*.test.ts", "**/*.spec.ts"],
        body=(
            "# Testing Conventions\n\n"
            "- pytest for backend; vitest for TypeScript units; playwright for E2E.\n"
            "- Never delete a failing test — fix the code or mark `xfail` with reason.\n"
            "- Contract tests must pass whenever a schema changes.\n"
            "- Use fixtures; never hit real network/DB in unit tests.\n"
        ),
    )

    return [core, python_rule, ts_rule, test_rule]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

@dataclass
class ProjectContext:
    """Minimal project data needed for IDE rule generation."""
    name: str
    description: str = ""
    boundaries: dict[str, list[str]] = field(default_factory=dict)
    extra_rules: list[CursorRule] = field(default_factory=list)
    modules: dict[str, str] = field(default_factory=dict)
    commands: dict[str, str] = field(default_factory=dict)


def generate_cursor_rules(project: ProjectContext) -> dict[str, str]:
    """Generate Cursor .mdc rule files.

    Returns:
        Dict mapping  `.cursor/rules/<name>.mdc`  → file content.
        All content is deterministic (same input → same bytes).
    """
    rules = _default_rules(project.name, project.boundaries)
    rules.extend(project.extra_rules)

    result: dict[str, str] = {}
    for rule in rules:
        content = _build_rule_file(rule)
        result[f".cursor/rules/{rule.name}.mdc"] = content

    return result


def generate_copilot_instructions(project: ProjectContext) -> str:
    """Generate `.github/copilot-instructions.md` content."""
    boundaries = project.boundaries
    always = boundaries.get("always", ["Validate before persist"])
    ask = boundaries.get("ask_first", ["Schema or migration changes"])
    never = boundaries.get("never", ["Commit secrets"])

    def bullet(items: list[str]) -> str:
        return "\n".join(f"- {i}" for i in items)

    command_block = ""
    if project.commands:
        rows = "\n".join(f"| `{k}` | {v} |" for k, v in project.commands.items())
        command_block = f"\n## Commands\n\n| Command | Purpose |\n|---------|----------|\n{rows}\n"

    body = (
        f"# GitHub Copilot Instructions — {project.name}\n\n"
        f"{project.description}\n\n"
        f"---\n\n"
        f"## Boundary Rules\n\n"
        f"### Always\n\n{bullet(always)}\n\n"
        f"### Ask First\n\n{bullet(ask)}\n\n"
        f"### Never\n\n{bullet(never)}\n"
        f"{command_block}\n"
        f"---\n\n"
        f"*Generated by Prompt Studio — do not edit directly.*\n"
    )

    digest = hashlib.sha256(body.encode()).hexdigest()[:16]
    return body + f"\n*checksum: `{digest}`*\n"
