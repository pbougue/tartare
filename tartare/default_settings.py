# encoding: utf-8
import logging
import os
from datetime import timedelta

# URL for the brokker, by default it's the local rabbitmq
# For amqp (rabbitMQ) the syntax is:
# amqp://<user>:<password>@<host>:<port>/<vhost>
# the default vhost is "/" so the URL end with *two* slash
# http://docs.celeryproject.org/en/latest/configuration.html#std:setting-BROKER_URL
CELERY_BROKER_URL = str(os.getenv('TARTARE_RABBITMQ_HOST', 'amqp://guest:guest@localhost:5672//'))

CELERY_DEFAULT_QUEUE = 'tartare'

CELERY_DEFAULT_EXCHANGE = 'celery_tartare'

# configuration of celery, don't edit
CELERY_ACCEPT_CONTENT = ['pickle', 'json']

CELERYBEAT_SCHEDULE = {
    'udpate-data-every-n-seconds': {
        'task': 'tartare.tasks.update_data_task',
        'schedule': timedelta(seconds=2),
        'options': {'expires': 25}
    },
}
CELERY_TIMEZONE = 'UTC'

# http://docs.celeryproject.org/en/master/configuration.html#std:setting-CELERYBEAT_SCHEDULE_FILENAME
CELERYBEAT_SCHEDULE_FILENAME = '/tmp/celerybeat-schedule'

CELERYD_HIJACK_ROOT_LOGGER = False

INPUT_DIR = str(os.getenv('TARTARE_INPUT', './input'))
OUTPUT_DIR = str(os.getenv('TARTARE_OUTPUT', './output'))
CURRENT_DATA_DIR = str(os.getenv('TARTARE_CURRENT', './current'))
GRID_CALENDAR_DIR = str(os.path.join(CURRENT_DATA_DIR, 'gridcalendar'))

LOGGER = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'default': {
            'format': '[%(asctime)s] [%(levelname)5s] [%(process)5s] [%(name)25s] %(message)s',
        },
    },
    'handlers': {
        'default': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'default',
        },
    },
    'loggers': {
        '': {
            'handlers': ['default'],
            'level': 'DEBUG',
        },
        'celery': {
            'level': 'INFO',
        },
    }
}
