#!/bin/sh

rm -f server/incidents/migrations/0*.py
uv run python manage.py makemigrations incidents