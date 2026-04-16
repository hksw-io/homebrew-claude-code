#!/bin/sh

set -eu

repo_root="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
default_env_file="${XDG_CONFIG_HOME:-$HOME/.config}/claude-code-cask.env"
env_file="${CLAUDE_CODE_CASK_ENV_FILE:-}"

if [ "${1:-}" = "--env-file" ]; then
    if [ $# -lt 2 ]; then
        echo "error: --env-file requires a path" >&2
        exit 1
    fi
    env_file=$2
    shift 2
elif [ -z "$env_file" ] && [ -f "$default_env_file" ]; then
    env_file=$default_env_file
fi

if [ -n "$env_file" ]; then
    if [ ! -f "$env_file" ]; then
        echo "error: environment file not found: $env_file" >&2
        exit 1
    fi

    set -a
    # shellcheck disable=SC1090
    . "$env_file"
    set +a
fi

python3_bin="${PYTHON3:-$(command -v python3)}"

if [ -z "$python3_bin" ]; then
    echo "error: python3 is required" >&2
    exit 1
fi

exec "$python3_bin" "$repo_root/scripts/update_claude_code_cask.py" "$@"
