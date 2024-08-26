#!/bin/sh

#apply any db changes
python manage.py migrate

#bind to port 5000
#5 workers for (2 * 2 + 1) core guideline
#use specific --worker-tmp-dir to prevent the chances of blocking a worker when the directory is on a disk-backed file system
    #/dev/shm is mapped to shared memory and should be used for gunicorn heartbeat
    #this will improve performance and avoid random freezes

#default
# sh -c "gunicorn --bind 0.0.0.0:5000 --workers 5 --worker-class gevent --worker-tmp-dir /dev/shm voicewake.wsgi:application"

#debug
#if left omitted, default "--log-file -" logs to STDERR
sh -c "gunicorn --bind 0.0.0.0:5000 --workers 5 --worker-class gevent --worker-tmp-dir /dev/shm voicewake.wsgi:application --log-level debug"