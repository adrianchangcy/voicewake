#apply any Celery Beat changes by removing all periodic tasks, and letting Celery Beat re-add them later on start
python manage.py shell -c "from voicewake.services import delete_celery_task_from_db; delete_celery_task_from_db();"

#run Celery Beat for the app "voicewake", at log level "info"
sh -c "celery -A voicewake beat -l info"