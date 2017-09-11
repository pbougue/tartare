web: FLASK_DEBUG=1 FLASK_APP=tartare/api.py flask run
worker: celery  -A tartare.celery worker -Q tartare -l info
scheduler: celery  -A tartare.tasks.celery beat
