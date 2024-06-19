#!/bin/sh

#apply any db changes
python manage.py migrate

#apply any Celery Beat changes by removing all periodic tasks, and letting Celery Beat re-add them later on start
python manage.py shell -c "from voicewake.services import delete_celery_task_from_db; delete_celery_task_from_db();"

#do runserver via while-loop, as it may randomly crash on hot reload, and while-loop will keep trying
python django_runserver.py