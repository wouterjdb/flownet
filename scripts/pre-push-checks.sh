#!/usr/bin/env bash
set -euo pipefail

repo_root="$(git rev-parse --show-toplevel)"

if [[ -n "${VIRTUAL_ENV:-}" ]]; then
    PATH="$VIRTUAL_ENV/bin:$PATH"
elif [[ -x "$repo_root/.venv-py311/bin/black" ]]; then
    PATH="$repo_root/.venv-py311/bin:$PATH"
elif [[ -x "$repo_root/.venv/bin/black" ]]; then
    PATH="$repo_root/.venv/bin:$PATH"
fi
export PATH

check_dir="$(mktemp -d "${TMPDIR:-/tmp}/flownet-pre-push.XXXXXX")"
trap 'rm -rf "$check_dir"' EXIT
git -C "$repo_root" archive HEAD | tar -x -C "$check_dir"
cd "$check_dir"

for tool in black pylint mypy; do
    if ! command -v "$tool" >/dev/null 2>&1; then
        printf 'Missing %s. Install the FlowNet test dependencies first.\n' "$tool" >&2
        exit 1
    fi
done

black --check tests/ src/ setup.py
pylint src/ tests/ setup.py
mypy --ignore-missing-imports src/ setup.py
