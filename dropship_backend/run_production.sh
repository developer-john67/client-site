#!/bin/bash

echo "Starting production setup for dropship_backend..."

cd /home/john/ecommerce/dropship_backend

echo "Installing dependencies..."
pip install -r dropship_backend/requirements.txt

echo "Running migrations..."
python manage.py migrate --noinput

echo "Collecting static files..."
python manage.py collectstatic --noinput --clear

echo "Starting Gunicorn with Uvicorn workers (Guvicon)..."
gunicorn -c dropship_backend/gunicorn.conf.py dropship_backend.asgi:application