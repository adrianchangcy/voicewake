#!/bin/sh

#run these one-off commands when a container starts
#do not automate migrate/collectstatic here, otherwise >1 containers will face race conditions
#for commands that stay alive, e.g. gunicorn and celery beat, run each in separate containers (different folders with its own Dockerfile?)
#tutorial runs gunicorn here, but every Dockerfile has one CMD at the end to run 1 process, so our gunicorn is at root's Dockerfile