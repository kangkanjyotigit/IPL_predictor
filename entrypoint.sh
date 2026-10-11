#!/bin/bash

python manage.py migrate
python manage.py createsuperuser --noinput || true
exec "$@"
