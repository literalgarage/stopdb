#!/bin/sh

rm -f /tmp/stopdb.sqlite3
./scripts/squashmigrations.sh
uv run python manage.py migrate


export DJANGO_SUPERUSER_USERNAME=admin
# TOP SECRET PASSWORD! haha, no, just kidding, this is fine to check in
# since this will only ever be used in local development
export DJANGO_SUPERUSER_PASSWORD=secret123!
export DJANGO_SUPERUSER_EMAIL=admin@example.com
uv run python manage.py createsuperuser --noinput 

uv run python manage.py import_data data/


