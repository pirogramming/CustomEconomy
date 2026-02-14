#!/bin/bash
source /var/app/venv/*/bin/activate
python /var/app/current/manage.py migrate --noinput
