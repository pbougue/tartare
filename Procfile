web: FLASK_DEBUG=1 FLASK_APP=tartare/api.py flask run
tartare_worker: celery  -A tartare.tasks.celery worker -Q tartare -l info
worker_ruspell: celery  -A tartare.tasks.celery worker -Q tartare_ruspell -l info
worker_gtfs2ntfs: celery  -A tartare.tasks.celery worker -Q tartare_gtfs2ntfs -l info
scheduler: celery  -A tartare.tasks.celery beat
