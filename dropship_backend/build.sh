#!/bin/bash
set -e

echo "Installing dependencies..."
pip install -r requirements.txt

echo "Running migrations..."
python manage.py migrate --noinput

echo "Creating media directory..."
mkdir -p media/products

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Build complete!"