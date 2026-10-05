#!/usr/bin/env bash
set -euo pipefail

repo_root="$(git rev-parse --show-toplevel)"
cd "$repo_root"

if [[ -n "${VIRTUAL_ENV:-}" ]]; then
    PATH="$VIRTUAL_ENV/bin:$PATH"
elif [[ -x "$repo_root/.venv-py311/bin/black" ]]; then
    PATH="$repo_root/.venv-py311/bin:$PATH"
elif [[ -x "$repo_root/.venv/bin/black" ]]; then
    PATH="$repo_root/.venv/bin:$PATH"
fi
export PATH

for tool in black pylint mypy; do
    if ! command -v "$tool" >/dev/null 2>&1; then
        printf 'Missing %s. Install the FlowNet test dependencies first.\n' "$tool" >&2
        exit 1
    fi
done

black --check tests/ src/ setup.py
pylint src/ tests/ setup.py
mypy --ignore-missing-imports src/ setup.py
