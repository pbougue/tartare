web: FLASK_DEBUG=1 FLASK_APP=tartare/api.py flask run
worker: celery  -A tartare.tasks.celery worker
scheduler: celery  -A tartare.tasks.celery beat
