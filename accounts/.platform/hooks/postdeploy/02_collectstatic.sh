#!/bin/bash
set -e
source /var/app/venv/*/bin/activate
python /var/app/current/manage.py collectstatic --noinput
