# Claude Code Cask Tap

Community-maintained Homebrew tap that tracks Anthropic's latest Claude Code channel.

## Why This Exists

Anthropic's official Homebrew casks distinguish between stable and latest channels. This tap exists for one job: keep a single `claude-code` cask pinned to the live `latest` channel and refresh it automatically every 5 minutes.

This intentionally differs from the official naming:

- `brew install --cask claude-code` from Homebrew installs the official stable cask
- `brew install --cask claude-code@latest` from Homebrew installs Anthropic's official latest-channel cask
- `brew install --cask hksw-io/claude-code-cask/claude-code` installs this tap's latest-channel mirror

## Install

```sh
brew install --cask hksw-io/claude-code-cask/claude-code
```

Upgrade:

```sh
brew upgrade --cask hksw-io/claude-code-cask/claude-code
```

If you want plain `brew upgrade` to include casks that update outside Homebrew/core, set:

```sh
export HOMEBREW_UPGRADE_GREEDY=1
```

## Version Policy

This tap polls Anthropic's `latest` marker every 5 minutes and mirrors whatever version it points to.

The active cask follows a "highest seen wins" policy:

- a newly observed higher version replaces `Casks/claude-code.rb`
- a newly observed lower version is still tagged and released in this repo, but does not downgrade the active cask
- once a higher version has been published here, the tap will not move backward automatically

Example:

- if `latest` moves from `2.1.110` to `2.1.111`, the cask updates to `2.1.111`
- if `latest` later rolls back to `2.1.110`, the repo records that observation but keeps the active cask at `2.1.111`

If you want Anthropic's exact channel behavior, including automatic rollbacks, use the official Homebrew latest-channel cask instead.

## How It Works

This tap polls:

- `https://storage.googleapis.com/claude-code-dist-86c565f3-f756-42ad-8dfa-d59b1c096819/claude-code-releases/latest`
- `https://storage.googleapis.com/claude-code-dist-86c565f3-f756-42ad-8dfa-d59b1c096819/claude-code-releases/<version>/manifest.json`

Each newly observed version:

- creates a matching git tag such as `v2.1.111`
- creates a GitHub Release in `hksw-io/claude-code-cask`
- updates `Casks/claude-code.rb` only if that version outranks the current active version

## Run It Yourself

Clone the repo wherever you want to run the mirror:

```sh
git clone https://github.com/hksw-io/claude-code-cask.git
cd claude-code-cask
```

Create an environment file. The default location is `${XDG_CONFIG_HOME:-$HOME/.config}/claude-code-cask.env`, but every helper script also accepts an explicit path:

```sh
mkdir -p "${XDG_CONFIG_HOME:-$HOME/.config}"
cat > "${XDG_CONFIG_HOME:-$HOME/.config}/claude-code-cask.env" <<'EOF'
GH_TOKEN=...
TAP_REPO=hksw-io/claude-code-cask
GIT_BRANCH=main
GIT_USER_NAME="Your Name"
GIT_USER_EMAIL="you@example.com"
EOF
chmod 600 "${XDG_CONFIG_HOME:-$HOME/.config}/claude-code-cask.env"
```

Run the updater once:

```sh
./scripts/run_update.sh --dry-run --verbose
```

Run the tests:

```sh
python3 -m unittest discover -s tests -v
```

Automate it on Linux with `systemd`:

```sh
sudo ./scripts/install_systemd_units.sh "${XDG_CONFIG_HOME:-$HOME/.config}/claude-code-cask.env"
systemctl status claude-code-cask-sync.timer
systemctl list-timers claude-code-cask-sync.timer
```

Automate it on macOS with `launchd`:

```sh
./scripts/install_launchd_agent.sh "${XDG_CONFIG_HOME:-$HOME/.config}/claude-code-cask.env"
launchctl print "gui/$(id -u)/io.hksw.claude-code-cask-sync"
```

Notes:

- The helper scripts render the scheduler config with your actual clone path, so you do not need to use `/srv/claude-code-cask`.
- `GH_TOKEN` needs permission to create releases and push tags/commits in `hksw-io/claude-code-cask`.
- Set `GIT_USER_NAME` and `GIT_USER_EMAIL` if you want mirrored commits to use a specific identity. If unset, the updater falls back to the repo's local git config.
- The Linux installer defaults to running the timer as the invoking user. Override `CLAUDE_CODE_CASK_USER`, `CLAUDE_CODE_CASK_GROUP`, or `CLAUDE_CODE_CASK_HOME` if you want a dedicated service account.
