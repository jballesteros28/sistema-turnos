#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt

python manage.py collectstatic --noinput
python manage.py migrate
python manage.py crear_superuser_render
python manage.py crear_usuarios_demo --render-safe
