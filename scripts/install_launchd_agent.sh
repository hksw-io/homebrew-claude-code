#!/bin/sh

set -eu

if [ "$(uname -s)" != "Darwin" ]; then
    echo "error: install_launchd_agent.sh is only supported on macOS" >&2
    exit 1
fi

repo_root="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
template="$repo_root/launchd/io.hksw.claude-code-tap-sync.plist.in"
env_file="${1:-${XDG_CONFIG_HOME:-$HOME/.config}/claude-code-tap.env}"
python3_bin="${PYTHON3:-$(command -v python3)}"
launch_agents_dir="$HOME/Library/LaunchAgents"
logs_dir="$HOME/Library/Logs"
plist_path="$launch_agents_dir/io.hksw.claude-code-tap-sync.plist"
log_file="$logs_dir/io.hksw.claude-code-tap-sync.log"

if [ ! -f "$env_file" ]; then
    echo "error: environment file not found: $env_file" >&2
    exit 1
fi

abspath() {
    target=$1
    dir=$(CDPATH= cd -- "$(dirname -- "$target")" && pwd)
    printf '%s/%s\n' "$dir" "$(basename -- "$target")"
}

escape_sed_replacement() {
    printf '%s' "$1" | sed 's/[|&]/\\&/g'
}

env_file="$(abspath "$env_file")"

mkdir -p "$launch_agents_dir" "$logs_dir"

repo_root_escaped="$(escape_sed_replacement "$repo_root")"
env_file_escaped="$(escape_sed_replacement "$env_file")"
python3_escaped="$(escape_sed_replacement "$python3_bin")"
log_file_escaped="$(escape_sed_replacement "$log_file")"

sed \
    -e "s|__REPO_ROOT__|$repo_root_escaped|g" \
    -e "s|__ENV_FILE__|$env_file_escaped|g" \
    -e "s|__PYTHON3__|$python3_escaped|g" \
    -e "s|__LOG_FILE__|$log_file_escaped|g" \
    "$template" > "$plist_path"

launchctl bootout "gui/$(id -u)" "$plist_path" >/dev/null 2>&1 || true
launchctl bootstrap "gui/$(id -u)" "$plist_path"
launchctl enable "gui/$(id -u)/io.hksw.claude-code-tap-sync"
launchctl kickstart -k "gui/$(id -u)/io.hksw.claude-code-tap-sync"

printf '%s\n' "Installed io.hksw.claude-code-tap-sync via launchd using $env_file"
