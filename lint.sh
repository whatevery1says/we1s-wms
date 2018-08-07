#!/usr/bin/env bash

# To install as a local git pre-commit hook:
# mkdir -p .git/hooks; cp lint.sh .git/hooks/pre-commit

# return error if any command errors
set -e
set -o pipefail

echo "[pydocstyle]"
pydocstyle --match-dir='(?!(static|[^\.].*))'

echo "[pycodestyle]"
pycodestyle

echo "[pylint]"
pylint app/
