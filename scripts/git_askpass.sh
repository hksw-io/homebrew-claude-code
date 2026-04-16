#!/bin/sh

set -eu

prompt="${1:-}"

case "$prompt" in
    *Username*)
        printf '%s\n' "${GIT_ASKPASS_USERNAME:-x-access-token}"
        ;;
    *Password*)
        printf '%s\n' "${GIT_ASKPASS_PASSWORD:?GIT_ASKPASS_PASSWORD is required}"
        ;;
    *)
        exit 1
        ;;
esac
