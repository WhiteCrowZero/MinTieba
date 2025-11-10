#!/bin/sh
set -e

echo "=== Django: migrate ==="
python manage.py migrate --noinput

echo "=== Django: collectstatic ==="
python manage.py collectstatic --noinput || echo "collectstatic skipped"

echo "=== Gunicorn: start ==="
gunicorn config.wsgi:application \
    --bind 0.0.0.0:8080 \
    --workers 3
