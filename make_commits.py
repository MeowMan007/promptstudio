import subprocess
import os

def run_git(args):
    res = subprocess.run(["git"] + args, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"FAILED git {' '.join(args)}")
        print("STDERR:", res.stderr)
        print("STDOUT:", res.stdout)
    return res.returncode == 0

def commit(msg, paths):
    for p in paths:
        if os.path.exists(p):
            run_git(["add", p])
    # check if anything staged
    res = subprocess.run(["git", "diff", "--cached", "--name-only"], capture_output=True, text=True)
    if res.stdout.strip():
        run_git(["commit", "-m", msg])
        print(f"Committed: {msg}")
    else:
        print(f"Skipped (no changes): {msg}")

# Commit sequence
commit("chore: project initialization, license, and repository root configs", [
    ".gitignore", ".prettierignore", ".prettierrc.json", "eslint.config.mjs",
    "package.json", "pnpm-workspace.yaml", "pnpm-lock.yaml", "pyproject.toml",
    "uv.lock", "tsconfig.json", "Makefile", ".env.example", "docker-compose.yml",
    "alembic.ini", ".github"
])

commit("docs: architecture specifications, AGENTS.md, and MASTER_PLAN.yaml", [
    "README.md", "AGENTS.md", "MASTER_PLAN.yaml", "docs"
])

commit("feat(schemas): artifact schema v1.0.0 and JSON schema specifications", [
    "schemas"
])

commit("feat(packages): canvas, prompt-spec, wireframes, and export-spec packages", [
    "packages"
])

commit("feat(infra): infrastructure, machine configs, and tooling", [
    "infra", "machine", "tools"
])

commit("feat(database): async PostgreSQL session factory and base repository models", [
    "backend/app/database.py", "backend/app/db"
])

commit("feat(ids): ULID and CUID entity identifier generators with domain prefixes", [
    "backend/app/ids.py", "backend/app/identifiers"
])

commit("feat(identity): OIDC configuration, session management, and AuthSettings", [
    "apps/api/src/prompt_studio_api/identity"
])

commit("feat(errors): RFC 9457 problem details error handling and conventions", [
    "apps/api/src/prompt_studio_api/api_errors.py"
])

commit("feat(workspaces): workspace domain models, repository, and CRUD router", [
    "backend/app/workspaces.py", "apps/api/src/prompt_studio_api/workspaces.py"
])

commit("feat(artifacts): typed project graph artifacts repository and API", [
    "backend/app/artifacts.py", "apps/api/src/prompt_studio_api/artifacts.py"
])

commit("feat(edges): typed graph relationship edges service and router", [
    "backend/app/edges.py", "apps/api/src/prompt_studio_api/edges.py"
])

commit("feat(projections): graph-to-canvas projection pipelines and viewports", [
    "backend/app/projections.py", "apps/api/src/prompt_studio_api/projections.py"
])

commit("feat(queries): topological graph query engine and dependency traversals", [
    "backend/app/graph_queries.py", "apps/api/src/prompt_studio_api/graph_queries.py"
])

commit("feat(validation): schema invariants and semantic validation engine", [
    "backend/app/validation.py", "apps/api/src/prompt_studio_api/validation_api.py"
])

commit("feat(patches): patch taxonomy, taxonomy service, and graph transforms", [
    "backend/app/patches"
])

commit("feat(export): multi-format export pipeline and artifact scanner", [
    "backend/app/export"
])

commit("feat(skills): agent skills loader and Claude tools registry", [
    "backend/app/skills"
])

commit("feat(tools): MCP tool router and external bindings", [
    "backend/app/tools"
])

commit("feat(bindings): field bindings and policy enforcement middleware", [
    "backend/app/bindings"
])

commit("feat(fixtures): golden fixtures, eval suite, and determinism benchmarks", [
    "fixtures", "backend"
])

commit("feat(studio-api): studio REST endpoints and canvas state persistence", [
    "apps/api/src/prompt_studio_api/studio_api.py", "apps/api/src/prompt_studio_api/contracts"
])

commit("feat(tests-contract): contract test suite and schema verification", [
    "tests/contract"
])

# Unit tests excluding test_web_pages.py
unit_files = [os.path.join("tests/unit", f) for f in os.listdir("tests/unit") if f != "test_web_pages.py"] if os.path.exists("tests/unit") else []
commit("feat(tests-unit): unit tests for core domain engines and patch services", unit_files)

commit("feat(tests-misc): integration, e2e, and roundtrip test suites", [
    "tests/e2e", "tests/roundtrip", "tests"
])

commit("feat(pages): public marketing, templates, guide, and dashboard pages", [
    "apps/api/src/prompt_studio_api/pages_html.py"
])

commit("feat(main): FastAPI application bootstrap and comprehensive route wiring", [
    "apps/api/src/prompt_studio_api/main.py", "apps"
])

commit("feat(canvas): enterprise canvas board HTML engine and blueprint topologies", [
    "apps/api/src/prompt_studio_api/studio_html.py"
])

commit("test(web): web page route tests for landing, board, and auth pages", [
    "tests/unit/test_web_pages.py"
])

# Any remaining files
subprocess.run(["git", "add", "."], capture_output=True)
res = subprocess.run(["git", "diff", "--cached", "--name-only"], capture_output=True, text=True)
if res.stdout.strip():
    run_git(["commit", "-m", "chore(release): finalize prompt studio v1.0.0 release for production"])
    print("Committed final remaining files.")

print("\nAll commits created. Commit log count:")
res = subprocess.run(["git", "rev-list", "--count", "HEAD"], capture_output=True, text=True)
print(f"Total commits: {res.stdout.strip()}")
