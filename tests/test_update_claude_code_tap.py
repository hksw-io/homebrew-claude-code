from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path
from unittest import mock


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import update_claude_code_tap as updater  # noqa: E402


class ReleaseParsingTests(unittest.TestCase):
    def make_manifest(self, *, version: str) -> dict:
        platforms = {}
        checksum_chars = iter(["a", "b", "c", "d"])
        for _, platform_name in updater.REQUIRED_ASSETS.items():
            checksum_seed = next(checksum_chars) * 64
            platforms[platform_name] = {
                "binary": "claude",
                "checksum": checksum_seed,
                "size": 123,
            }

        return {
            "version": version,
            "buildDate": "2026-04-16T14:30:47Z",
            "platforms": platforms,
        }

    def test_release_from_manifest_extracts_version_and_digests(self) -> None:
        release = updater.release_from_manifest("2.1.111", self.make_manifest(version="2.1.111"))
        self.assertEqual(release.version, "2.1.111")
        self.assertEqual(release.tag_name, "v2.1.111")
        self.assertEqual(release.cask_token, "claude-code")
        self.assertEqual(sorted(release.sha256), sorted(updater.REQUIRED_ASSETS))

    def test_release_from_manifest_requires_matching_version(self) -> None:
        with self.assertRaisesRegex(ValueError, "Manifest version mismatch"):
            updater.release_from_manifest("2.1.111", self.make_manifest(version="2.1.110"))

    def test_version_key_orders_newer_patch_release_higher(self) -> None:
        self.assertGreater(
            updater.version_key("2.1.111"),
            updater.version_key("2.1.110"),
        )

    def test_release_outranks_active_uses_semver_precedence(self) -> None:
        release = updater.release_from_manifest("2.1.111", self.make_manifest(version="2.1.111"))
        self.assertTrue(updater.release_outranks_active(release, "2.1.110"))
        self.assertFalse(updater.release_outranks_active(release, "2.1.112"))

    def test_render_cask_tracks_latest_marker(self) -> None:
        release = updater.release_from_manifest("2.1.111", self.make_manifest(version="2.1.111"))
        content = updater.render_cask(release)
        self.assertIn('cask "claude-code"', content)
        self.assertIn("/claude-code-releases/#{version}/#{os}-#{arch}/claude", content)
        self.assertIn('/claude-code-releases/latest"', content)
        self.assertNotIn("stable", content)

    def test_select_release_for_sync_returns_none_when_tag_already_exists(self) -> None:
        release = updater.release_from_manifest("2.1.111", self.make_manifest(version="2.1.111"))
        with mock.patch.object(updater, "fetch_latest_release", return_value=release):
            self.assertIsNone(updater.select_release_for_sync({"v2.1.111"}))

    def test_select_release_for_sync_returns_release_when_new_tag_observed(self) -> None:
        release = updater.release_from_manifest("2.1.111", self.make_manifest(version="2.1.111"))
        with mock.patch.object(updater, "fetch_latest_release", return_value=release):
            selected = updater.select_release_for_sync(set())
        self.assertIsNotNone(selected)
        assert selected is not None
        self.assertEqual(selected.tag_name, "v2.1.111")

    def test_push_remote_url_does_not_embed_credentials(self) -> None:
        self.assertEqual(
            updater.push_remote_url(),
            "https://github.com/hksw-io/homebrew-claude-code.git",
        )

    def test_resolve_git_identity_prefers_environment(self) -> None:
        with mock.patch.dict(
            os.environ,
            {
                "GIT_USER_NAME": "Test User",
                "GIT_USER_EMAIL": "test@example.com",
            },
            clear=False,
        ):
            with mock.patch.object(updater, "GIT_USER_NAME", "Test User"):
                with mock.patch.object(updater, "GIT_USER_EMAIL", "test@example.com"):
                    self.assertEqual(
                        updater.resolve_git_identity(),
                        ("Test User", "test@example.com"),
                    )

    def test_resolve_git_identity_falls_back_to_git_config(self) -> None:
        with mock.patch.object(updater, "GIT_USER_NAME", None):
            with mock.patch.object(updater, "GIT_USER_EMAIL", None):
                with mock.patch.object(updater, "git_config_value", side_effect=["Test User", "test@example.com"]):
                    self.assertEqual(
                        updater.resolve_git_identity(),
                        ("Test User", "test@example.com"),
                    )

    def test_resolve_git_identity_requires_complete_identity(self) -> None:
        with mock.patch.object(updater, "GIT_USER_NAME", None):
            with mock.patch.object(updater, "GIT_USER_EMAIL", None):
                with mock.patch.object(updater, "git_config_value", side_effect=[None, None]):
                    with self.assertRaisesRegex(RuntimeError, "Git commit identity is not configured"):
                        updater.resolve_git_identity()

    def test_ensure_repo_writable_passes_when_all_paths_are_writable(self) -> None:
        with mock.patch("os.access", return_value=True):
            updater.ensure_repo_writable()

    def test_ensure_repo_writable_reports_unwritable_paths(self) -> None:
        def fake_access(path: object, mode: int) -> bool:
            return "claude-code.rb" not in str(path) and "refs/heads/main" not in str(path)

        with mock.patch("os.access", side_effect=fake_access):
            with self.assertRaisesRegex(RuntimeError, "Repository is not writable by the current user"):
                updater.ensure_repo_writable()


if __name__ == "__main__":
    unittest.main()
