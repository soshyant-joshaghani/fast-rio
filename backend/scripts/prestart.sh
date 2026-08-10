#!/usr/bin/env bash
set -e
set -x

python app/backend_pre_start.py
alembic -c alembic.ini upgrade head
python app/initial_data.py
