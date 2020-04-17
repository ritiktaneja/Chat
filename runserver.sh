#!/bin/sh

# starting the redis server
echo "Starting redis server"
docker run -p 6379:6379 -d redis:5

# running django
echo "Running migrations"
python manage.py migrate
echo "Starting django server"
python manage.py runserver