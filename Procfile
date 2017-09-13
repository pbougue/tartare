web: FLASK_DEBUG=1 FLASK_APP=tartare/api.py flask run
worker: celery  -A tartare.tasks.celery worker -Q tartare -l info
worker_ruspell: celery  -A tartare.tasks.celery worker -Q process_ruspell
scheduler: celery  -A tartare.tasks.celery beat
