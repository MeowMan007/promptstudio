# Prompt Studio — User Guide

## First Run Tutorial

Welcome to **Prompt Studio** — a prompt-native visual design workspace.

### Step 1: Create your first project

1. Open Prompt Studio and click **New Project**.
2. Enter a project name and description.
3. Click **Create** — you'll see the canvas with an empty artifact graph.

### Step 2: Add your first artifact

1. Click the **+ Add Artifact** button.
2. Choose an artifact type (e.g., Screen, Prompt, Data Entity).
3. Fill in the artifact fields and click **Save**.

### Step 3: Bind a field

1. Select an artifact on the canvas.
2. Click a field's **⚡ Bind** button.
3. Choose a binding from the catalogue (e.g., `gpt_4o_suggest`).
4. Click **Run** to generate a suggestion.

### Step 4: Review and apply changes

1. After a run, the **Field Diff** panel shows proposed changes.
2. Review each change. Click **Apply** to accept or **Reject** to discard.
3. All changes go through the **Patch Engine** — edits are reversible.

### Step 5: Export your project

1. Click **Export** in the top bar.
2. Choose **Full Export (ZIP)**.
3. The ZIP contains:
   - `AGENTS.md` — agent instructions
   - `requirements.md` — EARS requirements
   - `design.md` — design document
   - `tasks.md` — dependency-wave task list
   - `openapi.json` — API specification
   - `llms.txt` — LLM context file
4. Click **Download**.

> [!TIP]
> New users typically reach their first export in under 15 minutes.
> If you get stuck, check the **Demo Project** (File → Open Demo).

---

## Demo Project

A demo project is bundled at `fixtures/demo-project.zip`. Open it via **File → Open Demo**
to explore a complete example with pre-populated artifacts, bindings, and exports.

---

*TSK-114 / spec 5.7*
