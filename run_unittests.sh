#!/usr/bin/env bash
# Discover and run every test under test/unittests.
#
# Must run with cwd=src so model.utility.resource_path can locate resources/,
# and with the project root on PYTHONPATH so `test.unittests.*` resolves to
# the project's package (and not the Python stdlib `test` package).
set -euo pipefail

project_root="$(cd "$(dirname "$0")" && pwd)"
cd "$project_root/src"

PYTHONPATH="${project_root}:.:./proto" "${project_root}/.venv/bin/python3" \
    -m unittest discover -s "${project_root}/test/unittests" -t "${project_root}" -v "$@"
