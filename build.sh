#!/usr/bin/env bash
# exit on error
set -o errexit

pip install -r requirements.txt

export DJANGO_SETTINGS_MODULE=config.settings.production

python manage.py collectstatic --noinput
python manage.py migrate
python manage.py create_default_superuser
