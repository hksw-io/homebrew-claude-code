#!/bin/sh

set -eu

repo_root="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
template="$repo_root/systemd/claude-code-tap-sync.service.in"
timer_template="$repo_root/systemd/claude-code-tap-sync.timer"
env_file="${1:-${XDG_CONFIG_HOME:-$HOME/.config}/claude-code-tap.env}"

if [ "$(id -u)" -ne 0 ]; then
    echo "error: install_systemd_units.sh must run as root" >&2
    exit 1
fi

if [ ! -f "$env_file" ]; then
    echo "error: environment file not found: $env_file" >&2
    exit 1
fi

python3_bin="${PYTHON3:-$(command -v python3)}"
run_user="${CLAUDE_CODE_TAP_USER:-${SUDO_USER:-$(id -un)}}"
run_group="${CLAUDE_CODE_TAP_GROUP:-$(id -gn "$run_user")}"
run_home="${CLAUDE_CODE_TAP_HOME:-}"

if [ -z "$run_home" ]; then
    if command -v getent >/dev/null 2>&1; then
        run_home="$(getent passwd "$run_user" | cut -d: -f6)"
    else
        run_home="$(eval "printf '%s' ~$run_user")"
    fi
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

repo_root_escaped="$(escape_sed_replacement "$repo_root")"
env_file_escaped="$(escape_sed_replacement "$env_file")"
python3_escaped="$(escape_sed_replacement "$python3_bin")"
run_user_escaped="$(escape_sed_replacement "$run_user")"
run_group_escaped="$(escape_sed_replacement "$run_group")"
run_home_escaped="$(escape_sed_replacement "$run_home")"

sed \
    -e "s|__REPO_ROOT__|$repo_root_escaped|g" \
    -e "s|__ENV_FILE__|$env_file_escaped|g" \
    -e "s|__PYTHON3__|$python3_escaped|g" \
    -e "s|__RUN_USER__|$run_user_escaped|g" \
    -e "s|__RUN_GROUP__|$run_group_escaped|g" \
    -e "s|__RUN_HOME__|$run_home_escaped|g" \
    "$template" > /etc/systemd/system/claude-code-tap-sync.service
install -m 0644 "$timer_template" /etc/systemd/system/claude-code-tap-sync.timer

systemctl daemon-reload
systemctl enable --now claude-code-tap-sync.timer

printf '%s\n' "Installed claude-code-tap-sync.timer for $run_user using $env_file"
