# encoding: utf-8

import os
from datetime import timedelta
from kombu import Exchange, Queue

# URL for the brokker, by default it's the local rabbitmq
# For amqp (rabbitMQ) the syntax is:
# amqp://<user>:<password>@<host>:<port>/<vhost>
# the default vhost is "/" so the URL end with *two* slash
# http://docs.celeryproject.org/en/latest/configuration.html#std:setting-BROKER_URL
CELERY_BROKER_URL = str(os.getenv('TARTARE_RABBITMQ_HOST', 'amqp://guest:guest@localhost:5672//'))

CELERY_DEFAULT_QUEUE = 'tartare'

CELERY_DEFAULT_EXCHANGE = 'celery_tartare'

# Temporary, to be deleted soon
CELERYD_CONCURRENCY = 1

CELERY_QUEUES = (
    Queue(CELERY_DEFAULT_QUEUE, Exchange(CELERY_DEFAULT_EXCHANGE), routing_key='celery'),
)


# configuration of celery, don't edit
CELERY_ACCEPT_CONTENT = ['pickle', 'json']

CELERYBEAT_SCHEDULE = {
    'automatic-update-every-6-hours': {
        'task': 'tartare.tasks.automatic_update',
        'schedule': timedelta(hours=6),
        'options': {'expires': 25}
    }
}

CELERY_TIMEZONE = 'UTC'

# http://docs.celeryproject.org/en/master/configuration.html#std:setting-CELERYBEAT_SCHEDULE_FILENAME
CELERYBEAT_SCHEDULE_FILENAME = '/tmp/celerybeat-schedule'

CELERYD_HIJACK_ROOT_LOGGER = False

MONGO_HOST = os.getenv('MONGO_HOST', 'localhost')
MONGO_DATABASE = os.getenv('MONGO_DATABASE', 'tartare')
MONGO_URI = os.getenv('MONGO_URI', 'mongodb://{host}/{database}'.format(host=MONGO_HOST, database=MONGO_DATABASE))
TYR_UPLOAD_TIMEOUT = os.getenv('TYR_UPLOAD_TIMEOUT', 10)

FUSIO_STOP_MAX_ATTEMPT_NUMBER = 100
# 10 seconds
FUSIO_WAIT_FIXED = 10*1000

DEFAULT_LICENSE_URL = ''
DEFAULT_LICENSE_NAME = 'Private (unspecified)'

PLATFORM = os.getenv('PLATFORM', 'local')

# GRID_CALENDAR_DIR is just the name of the directory where is a calendar file
# The absolute path is CURRENT_DATA_DIR/grid_calendar
GRID_CALENDAR_DIR = 'grid_calendar'
CALENDAR_FILE = 'export_calendars.zip'

KEEP_HISTORICAL = {
    'gtfs': 3,
    'direction_config': 1
}

MAILER = {
    'smtp': {
        'host': os.getenv('MAILER_SMTP_HOST', 'smtp.canaltp.local'),
        'port': 25,
        'timeout': 1
    },
    'from': os.getenv('MAILER_FROM', 'tartare@canaltp.fr'),
    'to': os.getenv('MAILER_TO', 'charles.beaute@kisio.org'),
    'cc': os.getenv('MAILER_CC') if os.getenv('MAILER_CC') else ''
}

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
            'level': os.getenv('LOGGER_LEVEL', 'DEBUG'),
            'class': 'logging.StreamHandler',
            'formatter': 'default',
        },
    },
    'loggers': {
        '': {
            'handlers': ['default'],
            'level': os.getenv('LOGGER_LEVEL', 'DEBUG')
        },
        'celery': {
            'level': 'INFO'
        },
    }
}
