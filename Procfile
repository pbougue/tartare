web: FLASK_DEBUG=1 FLASK_APP=tartare/api.py flask run
worker: celery  -A tartare.tasks.celery worker -Q tartare -l info
https://github.com/CanalTP/tartare/pull/235/files
scheduler: celery  -A tartare.tasks.celery beat
