#!/usr/bin/env bash
set -e
set -x

export PYTHONPATH="/app/backend:/app/tests/backend"
coverage run -m pytest /app/tests/backend/
coverage report
coverage html --title "${@-coverage}"
