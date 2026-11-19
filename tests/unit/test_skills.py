"""
Tests for EPIC-07 Skills:
  TSK-060: SkillPackage model + content hashing + frontmatter parser
  TSK-061: Skill validator (SK-VAL-01..10)
  TSK-062/063: Trust levels, enable/disable, permission intersection
  TSK-064: Progressive-disclosure loader
  TSK-065: Script sandbox runner
  TSK-066: Install flows
"""
from __future__ import annotations

import io
import zipfile
import pytest


# =============================================================================
# TSK-060: Models
# =============================================================================

from backend.app.skills.models import (
    SkillPackage,
    SkillPackageStatus,
    hash_package_directory,
    parse_skill_frontmatter,
)


_VALID_SKILL_MD = """\
---
name: my-skill
version: 1.0.0
description: A test skill for unit testing.
---

# My Skill

This skill does X.
"""


class TestContentHashing:
    def test_hash_has_sha256_prefix(self):
        h = hash_package_directory({"SKILL.md": "content"})
        assert h.startswith("sha256:")

    def test_same_files_same_hash(self):
        files = {"SKILL.md": "content", "scripts/run.py": "print('hi')"}
        assert hash_package_directory(files) == hash_package_directory(files)

    def test_different_content_different_hash(self):
        h1 = hash_package_directory({"SKILL.md": "v1"})
        h2 = hash_package_directory({"SKILL.md": "v2"})
        assert h1 != h2

    def test_order_independent(self):
        f1 = {"a.txt": "aaa", "b.txt": "bbb"}
        f2 = {"b.txt": "bbb", "a.txt": "aaa"}
        assert hash_package_directory(f1) == hash_package_directory(f2)

    def test_empty_package_hashes(self):
        h = hash_package_directory({})
        assert h.startswith("sha256:")


class TestFrontmatterParser:
    def test_parses_name(self):
        fm = parse_skill_frontmatter(_VALID_SKILL_MD)
        assert fm["name"] == "my-skill"

    def test_parses_version(self):
        fm = parse_skill_frontmatter(_VALID_SKILL_MD)
        assert fm["version"] == "1.0.0"

    def test_parses_description(self):
        fm = parse_skill_frontmatter(_VALID_SKILL_MD)
        assert fm["description"] == "A test skill for unit testing."

    def test_no_frontmatter_returns_empty(self):
        assert parse_skill_frontmatter("# No frontmatter") == {}

    def test_missing_key_not_in_result(self):
        md = "---\nname: skill\n---\n"
        fm = parse_skill_frontmatter(md)
        assert "tools" not in fm


class TestSkillPackageModel:
    def test_draft_is_mutable(self):
        pkg = SkillPackage(
            id="pkg1", name="s", version="1.0.0", description="d",
            content_hash="sha256:abc",
        )
        assert pkg.is_mutable() is True

    def test_published_is_immutable(self):
        pkg = SkillPackage(
            id="pkg1", name="s", version="1.0.0", description="d",
            content_hash="sha256:abc",
        )
        pkg.publish()
        assert pkg.is_mutable() is False
        assert pkg.status == SkillPackageStatus.PUBLISHED

    def test_disable(self):
        pkg = SkillPackage(
            id="pkg1", name="s", version="1.0.0", description="d",
            content_hash="sha256:abc",
        )
        pkg.disable()
        assert pkg.status == SkillPackageStatus.DISABLED


# =============================================================================
# TSK-061: Validator
# =============================================================================

from backend.app.skills.validator import (
    validate_skill_package,
    SkillValidationResult,
)


def _valid_files(**overrides) -> dict[str, str]:
    base = {"SKILL.md": _VALID_SKILL_MD}
    base.update(overrides)
    return base


class TestSkillValidator:
    def test_valid_package_passes(self):
        result = validate_skill_package(_valid_files())
        assert result.valid is True
        assert result.failures == []

    # SK-VAL-01
    def test_missing_skill_md_fails(self):
        result = validate_skill_package({"readme.txt": "hi"})
        codes = [f.rule for f in result.failures]
        assert "SK-VAL-01" in codes

    # SK-VAL-02
    def test_invalid_name_fails(self):
        md = _VALID_SKILL_MD.replace("name: my-skill", "name: My SKILL!")
        result = validate_skill_package({"SKILL.md": md})
        codes = [f.rule for f in result.failures]
        assert "SK-VAL-02" in codes

    def test_missing_name_fails(self):
        md = "---\nversion: 1.0.0\ndescription: d\n---\n"
        result = validate_skill_package({"SKILL.md": md})
        codes = [f.rule for f in result.failures]
        assert "SK-VAL-02" in codes

    # SK-VAL-03
    def test_invalid_version_fails(self):
        md = _VALID_SKILL_MD.replace("version: 1.0.0", "version: v1.0")
        result = validate_skill_package({"SKILL.md": md})
        codes = [f.rule for f in result.failures]
        assert "SK-VAL-03" in codes

    # SK-VAL-04
    def test_missing_description_fails(self):
        md = "---\nname: my-skill\nversion: 1.0.0\n---\n"
        result = validate_skill_package({"SKILL.md": md})
        codes = [f.rule for f in result.failures]
        assert "SK-VAL-04" in codes

    # SK-VAL-05
    def test_path_traversal_fails(self):
        result = validate_skill_package(_valid_files(**{"../evil.py": "bad"}))
        codes = [f.rule for f in result.failures]
        assert "SK-VAL-05" in codes

    # SK-VAL-06
    def test_absolute_path_fails(self):
        result = validate_skill_package(_valid_files(**{"/etc/passwd": "root"}))
        codes = [f.rule for f in result.failures]
        assert "SK-VAL-06" in codes

    # SK-VAL-07
    def test_unknown_tool_fails(self):
        md = _VALID_SKILL_MD.replace("---\n\n", "tools: hack_the_planet\n---\n\n")
        md = "---\nname: my-skill\nversion: 1.0.0\ndescription: d\ntools: hack_the_planet\n---\n"
        result = validate_skill_package({"SKILL.md": md})
        codes = [f.rule for f in result.failures]
        assert "SK-VAL-07" in codes

    def test_allowed_tool_passes(self):
        md = "---\nname: my-skill\nversion: 1.0.0\ndescription: d\ntools: read_file\n---\n"
        result = validate_skill_package({"SKILL.md": md})
        assert "SK-VAL-07" not in [f.rule for f in result.failures]

    # SK-VAL-08
    def test_oversized_package_fails(self):
        big = "x" * (11 * 1024 * 1024)
        result = validate_skill_package(_valid_files(**{"big.txt": big}))
        codes = [f.rule for f in result.failures]
        assert "SK-VAL-08" in codes

    # SK-VAL-09
    def test_binary_extension_fails(self):
        result = validate_skill_package(_valid_files(**{"image.png": "fakepng"}))
        codes = [f.rule for f in result.failures]
        assert "SK-VAL-09" in codes

    # SK-VAL-10
    def test_secret_pattern_fails(self):
        result = validate_skill_package(_valid_files(**{"config.py": 'api_key = "sk-abc123def456ghi789jkl"'}))
        codes = [f.rule for f in result.failures]
        assert "SK-VAL-10" in codes

    def test_multiple_failures_returned(self):
        """Should return all failures, not just the first."""
        result = validate_skill_package({"readme.txt": "no skill md, also missing"})
        # At minimum SK-VAL-01 (no SKILL.md) and SK-VAL-02/03/04 (no frontmatter)
        assert len(result.failures) >= 3


# =============================================================================
# TSK-062/063: Trust + permissions
# =============================================================================

from backend.app.skills.trust import (
    TrustLevel,
    SkillPermission,
    SkillRegistry,
    effective_permissions,
)


class TestTrustLevels:
    def test_untrusted_imported_skill_starts_disabled(self):
        reg = SkillRegistry()
        reg.register("s1", TrustLevel.UNTRUSTED)
        assert reg.is_enabled("s1") is False

    def test_official_skill_starts_enabled(self):
        reg = SkillRegistry()
        reg.register("s1", TrustLevel.OFFICIAL)
        assert reg.is_enabled("s1") is True

    def test_enable_generates_audit_event(self):
        reg = SkillRegistry()
        reg.register("s1", TrustLevel.COMMUNITY)
        event = reg.enable("s1", actor="alice")
        assert event.event_type == "skill_enabled"
        assert event.actor == "alice"
        assert event.skill_id == "s1"

    def test_disable_generates_audit_event(self):
        reg = SkillRegistry()
        reg.register("s1", TrustLevel.OFFICIAL)
        event = reg.disable("s1", actor="bob")
        assert event.event_type == "skill_disabled"

    def test_audit_log_accumulates(self):
        reg = SkillRegistry()
        reg.register("s1", TrustLevel.COMMUNITY)
        reg.enable("s1", "alice")
        reg.disable("s1", "alice")
        assert len(reg.audit_log()) == 2

    def test_trust_change_audited(self):
        reg = SkillRegistry()
        reg.register("s1", TrustLevel.UNTRUSTED)
        event = reg.set_trust("s1", TrustLevel.COMMUNITY, actor="admin")
        assert event.event_type == "trust_changed"
        assert event.detail["from"] == TrustLevel.UNTRUSTED

    def test_enable_unknown_skill_raises(self):
        reg = SkillRegistry()
        with pytest.raises(KeyError):
            reg.enable("ghost", "alice")


class TestPermissionIntersection:
    def test_untrusted_cannot_propose_patch(self):
        perms = effective_permissions(
            TrustLevel.UNTRUSTED,
            {SkillPermission.PROPOSE_PATCH, SkillPermission.READ_ARTIFACTS},
            "editor",
        )
        assert SkillPermission.PROPOSE_PATCH not in perms

    def test_community_can_propose_for_editor(self):
        perms = effective_permissions(
            TrustLevel.COMMUNITY,
            {SkillPermission.PROPOSE_PATCH},
            "editor",
        )
        assert SkillPermission.PROPOSE_PATCH in perms

    def test_viewer_cannot_propose_even_official(self):
        perms = effective_permissions(
            TrustLevel.OFFICIAL,
            {SkillPermission.PROPOSE_PATCH},
            "viewer",
        )
        assert SkillPermission.PROPOSE_PATCH not in perms

    def test_skill_cannot_widen_beyond_caller(self):
        """Editor cannot apply patches — official skill requesting it still can't."""
        perms = effective_permissions(
            TrustLevel.OFFICIAL,
            {SkillPermission.APPLY_PATCH},
            "editor",
        )
        assert SkillPermission.APPLY_PATCH not in perms

    def test_admin_gets_all_official_perms(self):
        perms = effective_permissions(
            TrustLevel.OFFICIAL,
            set(SkillPermission),
            "admin",
        )
        assert SkillPermission.APPLY_PATCH in perms
        assert SkillPermission.RUN_COMMAND in perms


# =============================================================================
# TSK-064: Progressive loader
# =============================================================================

from backend.app.skills.installer import ProgressiveLoader


class TestProgressiveLoader:
    def _make_files(self) -> dict[str, str]:
        return {
            "SKILL.md": _VALID_SKILL_MD,
            "scripts/run.py": "print('hello')",
            "references/guide.md": "# Guide content",
        }

    def test_register_returns_metadata(self):
        loader = ProgressiveLoader()
        meta = loader.register("s1", self._make_files())
        assert meta.name == "my-skill"
        assert meta.version == "1.0.0"

    def test_metadata_includes_manifest(self):
        loader = ProgressiveLoader()
        meta = loader.register("s1", self._make_files())
        assert "SKILL.md" in meta.files_manifest
        assert "scripts/run.py" in meta.files_manifest

    def test_body_not_loaded_until_triggered(self):
        loader = ProgressiveLoader()
        loader.register("s1", self._make_files())
        # Body cache should be empty before trigger
        assert "s1" not in loader._body_cache

    def test_load_body_on_trigger(self):
        loader = ProgressiveLoader()
        loader.register("s1", self._make_files())
        body = loader.load_body("s1")
        assert body is not None
        assert "My Skill" in body.markdown

    def test_body_cached_on_second_call(self):
        loader = ProgressiveLoader()
        loader.register("s1", self._make_files())
        b1 = loader.load_body("s1")
        b2 = loader.load_body("s1")
        assert b1 is b2  # same object (cached)

    def test_load_reference_on_demand(self):
        loader = ProgressiveLoader()
        loader.register("s1", self._make_files())
        ref = loader.load_reference("s1", "references/guide.md")
        assert ref is not None
        assert "Guide content" in ref.content

    def test_reference_cached(self):
        loader = ProgressiveLoader()
        loader.register("s1", self._make_files())
        r1 = loader.load_reference("s1", "references/guide.md")
        r2 = loader.load_reference("s1", "references/guide.md")
        assert r1 is r2

    def test_missing_reference_returns_none(self):
        loader = ProgressiveLoader()
        loader.register("s1", self._make_files())
        assert loader.load_reference("s1", "nonexistent.md") is None


# =============================================================================
# TSK-065: Sandbox runner
# =============================================================================

from backend.app.skills.installer import (
    SandboxLimitError,
    SandboxResult,
    run_in_sandbox,
)


class TestSandboxRunner:
    def test_simple_echo_captured(self):
        result = run_in_sandbox('echo hello world')
        assert result.exit_code == 0
        assert result.trusted is False

    def test_oversized_script_raises(self):
        big_script = "x" * (65 * 1024)
        with pytest.raises(SandboxLimitError):
            run_in_sandbox(big_script)

    def test_error_line_in_stderr(self):
        result = run_in_sandbox("# ERROR: something went wrong")
        assert result.exit_code != 0

    def test_output_always_untrusted(self):
        result = run_in_sandbox("echo test")
        assert result.trusted is False


# =============================================================================
# TSK-066: Install flows
# =============================================================================

from backend.app.skills.installer import (
    install_from_folder,
    install_from_paste,
    install_from_zip,
    install_from_git,
    InstallSource,
    InstallPreview,
)


class TestInstallFlows:
    def test_install_from_folder_valid(self):
        preview = install_from_folder({"SKILL.md": _VALID_SKILL_MD})
        assert isinstance(preview, InstallPreview)
        assert preview.can_enable is True
        assert preview.source == InstallSource.FOLDER

    def test_install_from_folder_path_traversal_blocked(self):
        with pytest.raises(ValueError, match="traversal"):
            install_from_folder({"../evil.py": "bad", "SKILL.md": _VALID_SKILL_MD})

    def test_install_from_folder_invalid_package(self):
        preview = install_from_folder({"readme.txt": "no skill"})
        assert preview.can_enable is False
        assert len(preview.validation_errors) > 0

    def test_install_from_paste(self):
        preview = install_from_paste(_VALID_SKILL_MD)
        assert preview.can_enable is True
        assert preview.name == "my-skill"

    def test_install_from_zip(self):
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as zf:
            zf.writestr("my-skill/SKILL.md", _VALID_SKILL_MD)
        zip_bytes = buf.getvalue()
        preview = install_from_zip(zip_bytes)
        assert preview.can_enable is True

    def test_install_from_zip_blocks_traversal(self):
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as zf:
            zf.writestr("../evil.py", "bad")
        zip_bytes = buf.getvalue()
        with pytest.raises(ValueError):
            install_from_zip(zip_bytes)

    def test_install_from_git_requires_https(self):
        with pytest.raises(ValueError, match="HTTPS"):
            install_from_git("ssh://github.com/x/y.git", "abc1234")

    def test_install_from_git_requires_commit_sha(self):
        with pytest.raises(ValueError, match="commit SHA"):
            install_from_git("https://github.com/x/y.git", "main")

    def test_install_from_git_valid_url_and_sha(self):
        preview = install_from_git("https://github.com/x/y.git", "abc1234def5678")
        assert preview.source == InstallSource.GIT
        assert preview.can_enable is False   # no network in sandbox

    def test_content_hash_in_preview(self):
        preview = install_from_folder({"SKILL.md": _VALID_SKILL_MD})
        assert preview.content_hash.startswith("sha256:")
