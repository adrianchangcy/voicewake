#!/bin/sh

python manage.py migrate
python django_runserver.py