#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
TAP_REPO = os.environ.get("TAP_REPO", "hksw-io/homebrew-claude-code")
GIT_BRANCH = os.environ.get("GIT_BRANCH", "main")
GH_TOKEN = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
GIT_USER_NAME = os.environ.get("GIT_USER_NAME")
GIT_USER_EMAIL = os.environ.get("GIT_USER_EMAIL")
API_BASE = "https://api.github.com"
RELEASES_BASE_URL = (
    "https://storage.googleapis.com/claude-code-dist-86c565f3-f756-42ad-8dfa-d59b1c096819/claude-code-releases"
)
LATEST_MARKER_URL = f"{RELEASES_BASE_URL}/latest"
REQUIRED_ASSETS = {
    "arm": "darwin-arm64",
    "x86_64": "darwin-x64",
    "arm64_linux": "linux-arm64",
    "x86_64_linux": "linux-x64",
}
VERSION_RE = re.compile(r"^(?P<major>\d+)\.(?P<minor>\d+)\.(?P<patch>\d+)$")
CASK_VERSION_RE = re.compile(r'^\s*version "([^"]+)"', re.MULTILINE)


@dataclass(frozen=True)
class ReleaseInfo:
    version: str
    build_date: str
    sha256: dict[str, str]

    @property
    def tag_name(self) -> str:
        return f"v{self.version}"

    @property
    def cask_token(self) -> str:
        return "claude-code"

    @property
    def cask_path(self) -> Path:
        return REPO_ROOT / "Casks" / "claude-code.rb"

    @property
    def manifest_url(self) -> str:
        return f"{RELEASES_BASE_URL}/{self.version}/manifest.json"

    @property
    def version_key(self) -> tuple[int, int, int]:
        return version_key(self.version)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Mirror Claude Code latest-channel releases into this tap.")
    parser.add_argument("--dry-run", action="store_true", help="Do not write files, commit, push, or create releases.")
    parser.add_argument("--verbose", action="store_true", help="Print extra progress information.")
    return parser.parse_args()


def git(
    *args: str,
    capture_output: bool = True,
    check: bool = True,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    process_env = os.environ.copy()
    if env:
        process_env.update(env)
    return subprocess.run(
        ["git", *args],
        cwd=REPO_ROOT,
        check=check,
        text=True,
        capture_output=capture_output,
        env=process_env,
    )


def log(message: str) -> None:
    print(message, flush=True)


def debug(enabled: bool, message: str) -> None:
    if enabled:
        log(message)


def http_request_json(url: str) -> Any:
    return json.loads(http_request_text(url))


def http_request_text(url: str) -> str:
    headers = {"User-Agent": "hksw-io-homebrew-claude-code-updater"}
    last_error: Exception | None = None
    for attempt in range(5):
        request = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(request) as response:
                return response.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            if exc.code in (403, 408, 429, 500, 502, 503, 504):
                delay = max(1, 2**attempt)
                time.sleep(delay)
                last_error = exc
                continue
            details = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"HTTP request failed: {exc.code} {url}: {details}") from exc
        except urllib.error.URLError as exc:
            delay = max(1, 2**attempt)
            time.sleep(delay)
            last_error = exc
            continue
    raise RuntimeError(f"HTTP request kept failing for {url}") from last_error


def api_request(path: str, token: str | None, method: str = "GET", data: dict[str, Any] | None = None) -> Any:
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "hksw-io-homebrew-claude-code-updater",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"

    body = None
    if data is not None:
        body = json.dumps(data).encode("utf-8")
        headers["Content-Type"] = "application/json"

    last_error: Exception | None = None
    for attempt in range(5):
        request = urllib.request.Request(f"{API_BASE}{path}", headers=headers, method=method, data=body)
        try:
            with urllib.request.urlopen(request) as response:
                payload = response.read()
        except urllib.error.HTTPError as exc:
            if exc.code == 422 and path.startswith(f"/repos/{TAP_REPO}/releases"):
                return {"already_exists": True}
            if exc.code in (403, 408, 429, 500, 502, 503, 504):
                delay = max(1, 2**attempt)
                time.sleep(delay)
                last_error = exc
                continue
            details = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"GitHub API request failed: {exc.code} {path}: {details}") from exc
        else:
            if not payload:
                return None
            return json.loads(payload.decode("utf-8"))
    raise RuntimeError(f"GitHub API request kept failing for {path}") from last_error


def fetch_latest_version() -> str:
    version = http_request_text(LATEST_MARKER_URL).strip()
    version_key(version)
    return version


def fetch_release_manifest(version: str) -> dict[str, Any]:
    manifest_url = f"{RELEASES_BASE_URL}/{version}/manifest.json"
    payload = http_request_json(manifest_url)
    assert isinstance(payload, dict)
    return payload


def release_from_manifest(version: str, manifest: dict[str, Any]) -> ReleaseInfo:
    manifest_version = str(manifest.get("version", ""))
    if manifest_version != version:
        raise ValueError(f"Manifest version mismatch: expected {version}, got {manifest_version}")

    build_date = str(manifest.get("buildDate", ""))
    if not build_date:
        raise ValueError(f"Manifest for {version} is missing buildDate")

    platforms = manifest.get("platforms")
    if not isinstance(platforms, dict):
        raise ValueError(f"Manifest for {version} is missing platforms")

    asset_digests: dict[str, str] = {}
    for key, platform_name in REQUIRED_ASSETS.items():
        platform = platforms.get(platform_name)
        if not isinstance(platform, dict):
            raise ValueError(f"Manifest for {version} is missing platform {platform_name}")
        checksum = str(platform.get("checksum", ""))
        if not re.fullmatch(r"[0-9a-f]{64}", checksum):
            raise ValueError(f"Manifest for {version} has invalid checksum for {platform_name}")
        asset_digests[key] = checksum

    return ReleaseInfo(version=version, build_date=build_date, sha256=asset_digests)


def fetch_latest_release() -> ReleaseInfo:
    version = fetch_latest_version()
    manifest = fetch_release_manifest(version)
    return release_from_manifest(version, manifest)


def version_key(version: str) -> tuple[int, int, int]:
    match = VERSION_RE.fullmatch(version)
    if match is None:
        raise ValueError(f"Unsupported Claude Code release version: {version}")
    return (
        int(match.group("major")),
        int(match.group("minor")),
        int(match.group("patch")),
    )


def release_outranks_active(release: ReleaseInfo, active_version: str | None) -> bool:
    if active_version is None:
        return True
    return release.version_key > version_key(active_version)


def read_active_cask_version() -> str | None:
    path = REPO_ROOT / "Casks" / "claude-code.rb"
    if not path.exists():
        return None

    content = path.read_text(encoding="utf-8")
    match = CASK_VERSION_RE.search(content)
    if match is None:
        raise RuntimeError("Could not determine the active claude-code cask version.")

    version = match.group(1)
    version_key(version)
    return version


def select_release_for_sync(existing_tags: set[str]) -> ReleaseInfo | None:
    release = fetch_latest_release()
    if release.tag_name in existing_tags:
        return None
    return release


def render_cask(release: ReleaseInfo) -> str:
    return f"""cask "{release.cask_token}" do
  arch arm: "arm64", intel: "x64"
  os macos: "darwin", linux: "linux"

  version "{release.version}"
  sha256 arm:          "{release.sha256["arm"]}",
         x86_64:       "{release.sha256["x86_64"]}",
         arm64_linux:  "{release.sha256["arm64_linux"]}",
         x86_64_linux: "{release.sha256["x86_64_linux"]}"

  url "{RELEASES_BASE_URL}/#{{version}}/#{{os}}-#{{arch}}/claude",
      verified: "storage.googleapis.com/claude-code-dist-86c565f3-f756-42ad-8dfa-d59b1c096819/claude-code-releases/"
  name "Claude Code"
  desc "Terminal-based AI coding assistant"
  homepage "https://www.anthropic.com/claude-code"

  livecheck do
    url "{LATEST_MARKER_URL}"
    regex(/^v?(\\d+(?:\\.\\d+)+)$/i)
  end

  binary "claude"

  zap trash: [
        "~/.cache/claude",
        "~/.claude.json*",
        "~/.config/claude",
        "~/.local/bin/claude",
        "~/.local/share/claude",
        "~/.local/state/claude",
        "~/Library/Caches/claude-cli-nodejs",
      ],
      rmdir: "~/.claude"
end
"""


def ensure_clean_worktree() -> None:
    status = git("status", "--porcelain", "--untracked-files=no").stdout.strip()
    if status:
        raise RuntimeError("Refusing to run with a dirty working tree.")


def ensure_repo_writable() -> None:
    required_paths = [
        REPO_ROOT / "Casks",
        REPO_ROOT / "Casks" / "claude-code.rb",
        REPO_ROOT / ".git" / "config",
        REPO_ROOT / ".git" / "index",
        REPO_ROOT / ".git" / "objects",
        REPO_ROOT / ".git" / "refs" / "heads" / GIT_BRANCH,
    ]
    unwritable: list[str] = []

    for path in required_paths:
        target = path if path.exists() else path.parent
        if not os.access(target, os.W_OK):
            unwritable.append(str(path))

    if unwritable:
        joined = ", ".join(unwritable)
        raise RuntimeError(
            "Repository is not writable by the current user. "
            f"Fix ownership or permissions for: {joined}"
        )


def git_config_value(key: str) -> str | None:
    result = git("config", "--get", key, check=False)
    if result.returncode != 0:
        return None
    value = result.stdout.strip()
    return value or None


def resolve_git_identity() -> tuple[str, str]:
    name = GIT_USER_NAME or git_config_value("user.name")
    email = GIT_USER_EMAIL or git_config_value("user.email")
    if name is None or email is None:
        raise RuntimeError(
            "Git commit identity is not configured. Set GIT_USER_NAME and GIT_USER_EMAIL or configure git user.name and user.email."
        )
    return name, email


def configure_repo(verbose: bool) -> None:
    git_user_name, git_user_email = resolve_git_identity()
    debug(verbose, f"Using git identity {git_user_name} <{git_user_email}>.")
    git("config", "user.name", git_user_name)
    git("config", "user.email", git_user_email)
    try:
        git("remote", "get-url", "origin")
    except subprocess.CalledProcessError:
        return

    debug(verbose, f"Refreshing {GIT_BRANCH} from origin.")
    git("checkout", GIT_BRANCH)
    git("fetch", "origin", "--tags")
    git("pull", "--ff-only", "origin", GIT_BRANCH)


def existing_upstream_tags() -> set[str]:
    output = git("tag", "--list", "v*").stdout
    return {line.strip() for line in output.splitlines() if line.strip()}


def push_remote_url() -> str:
    return f"https://github.com/{TAP_REPO}.git"


def push_git_env(token: str) -> dict[str, str]:
    return {
        "GIT_ASKPASS": str(REPO_ROOT / "scripts" / "git_askpass.sh"),
        "GIT_TERMINAL_PROMPT": "0",
        "GIT_ASKPASS_USERNAME": "x-access-token",
        "GIT_ASKPASS_PASSWORD": token,
    }


def stage_and_commit(path: Path, release: ReleaseInfo, verbose: bool) -> bool:
    new_content = render_cask(release)
    old_content = path.read_text(encoding="utf-8") if path.exists() else ""
    if old_content == new_content:
        debug(verbose, f"{path.name} already matches {release.tag_name}.")
        return False

    path.write_text(new_content, encoding="utf-8")
    git("add", str(path.relative_to(REPO_ROOT)))
    git("commit", "-m", f"chore(cask): update {release.cask_token} to {release.version}")
    debug(verbose, f"Committed update for {release.tag_name}.")
    return True


def create_tag(tag_name: str, verbose: bool) -> None:
    git("tag", "-a", tag_name, "-m", f"Mirror Claude Code latest-channel version {tag_name}")
    debug(verbose, f"Created tag {tag_name}.")


def push_updates(tag_name: str, token: str, push_branch: bool, verbose: bool) -> None:
    url = push_remote_url()
    env = push_git_env(token)
    if push_branch:
        git("push", url, f"HEAD:{GIT_BRANCH}", capture_output=False, env=env)
        time.sleep(1)
    git("push", url, f"refs/tags/{tag_name}", capture_output=False, env=env)
    debug(verbose, f"Pushed {tag_name} to GitHub.")


def release_body(release: ReleaseInfo, *, active_version: str, cask_updated: bool) -> str:
    return "\n".join(
        [
            f"Tap mirror of Claude Code latest-channel version `{release.version}`.",
            "",
            f"- Latest marker: {LATEST_MARKER_URL}",
            f"- Manifest: {release.manifest_url}",
            f"- Build date: {release.build_date}",
            f"- Active cask: `{release.cask_token}`",
            f"- Active cask updated: {'yes' if cask_updated else 'no'}",
            f"- Active cask version after sync: `{active_version}`",
        ]
    )


def create_github_release(release: ReleaseInfo, token: str, active_version: str, cask_updated: bool, verbose: bool) -> None:
    payload = {
        "tag_name": release.tag_name,
        "target_commitish": GIT_BRANCH,
        "name": release.version,
        "body": release_body(release, active_version=active_version, cask_updated=cask_updated),
        "draft": False,
        "prerelease": False,
    }
    response = api_request(f"/repos/{TAP_REPO}/releases", token, method="POST", data=payload)
    if isinstance(response, dict) and response.get("already_exists"):
        debug(verbose, f"GitHub Release {release.tag_name} already exists.")
        return
    debug(verbose, f"Created GitHub Release {release.tag_name}.")


def sync_releases(dry_run: bool, verbose: bool) -> int:
    ensure_repo_writable()
    configure_repo(verbose)
    ensure_clean_worktree()

    tags = existing_upstream_tags()
    active_version = read_active_cask_version()
    release = select_release_for_sync(tags)
    if release is None:
        log("No new upstream release markers.")
        return 0

    log(f"Mirroring {release.tag_name}.")
    path = release.cask_path
    changed = False
    cask_updated = False
    should_promote = release_outranks_active(release, active_version)

    if not dry_run:
        if should_promote:
            changed = stage_and_commit(path, release, verbose)
            active_version = release.version
            cask_updated = changed
        else:
            debug(
                verbose,
                f"{release.tag_name} does not outrank active claude-code {active_version}; leaving claude-code.rb unchanged.",
            )
        create_tag(release.tag_name, verbose)

        if GH_TOKEN is None:
            raise RuntimeError("GH_TOKEN or GITHUB_TOKEN is required for push/release operations.")

        push_updates(release.tag_name, GH_TOKEN, push_branch=changed, verbose=verbose)
        if active_version is None:
            raise RuntimeError("No active claude-code version is available after sync.")
        create_github_release(release, GH_TOKEN, active_version, cask_updated, verbose)
    else:
        if should_promote:
            old_content = path.read_text(encoding="utf-8") if path.exists() else ""
            if old_content != render_cask(release):
                changed = True
            active_version = release.version
            cask_updated = changed
            log(f"dry-run: would {'update' if changed else 'reuse'} {path.name}")
        else:
            log(f"dry-run: would keep {path.name} at {active_version}")
        log(f"dry-run: would create tag {release.tag_name}")
        if active_version is None:
            raise RuntimeError("No active claude-code version is available after dry-run planning.")
        log(
            f"dry-run: would create GitHub Release {release.tag_name} "
            f"(active cask updated: {'yes' if cask_updated else 'no'})"
        )

    return 0


def main() -> int:
    args = parse_args()
    try:
        return sync_releases(dry_run=args.dry_run, verbose=args.verbose)
    except Exception as exc:  # noqa: BLE001
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
