# encoding: utf-8

import os
from datetime import timedelta

from celery.schedules import crontab
from kombu import Exchange, Queue

# URL for the brokker, by default it's the local rabbitmq
# For amqp (rabbitMQ) the syntax is:
# amqp://<user>:<password>@<host>:<port>/<vhost>
# the default vhost is "/" so the URL end with *two* slash
# http://docs.celeryproject.org/en/latest/configuration.html#std:setting-BROKER_URL
BROKER_URL = str(os.getenv('TARTARE_RABBITMQ_HOST', 'amqp://guest:guest@localhost:5672//'))

MONGO_HOST = os.getenv('MONGO_HOST', 'localhost')
MONGO_DATABASE = os.getenv('MONGO_DATABASE', 'tartare')
MONGO_URI = os.getenv('MONGO_URI', 'mongodb://{host}/{database}?connect=false'.format(
    host=MONGO_HOST, database=MONGO_DATABASE
))

CELERY_RESULT_BACKEND = MONGO_URI
CELERY_DEFAULT_QUEUE = 'tartare'
CELERY_DEFAULT_EXCHANGE = 'celery_tartare'
CELERY_DEFAULT_ROUTING_KEY = 'celery'

exchange = Exchange(CELERY_DEFAULT_EXCHANGE)

CELERY_QUEUES = (
    Queue(CELERY_DEFAULT_QUEUE, exchange=exchange, routing_key='celery'),
    Queue('tartare_ruspell', exchange=exchange, routing_key='process.ruspell'),
    Queue('tartare_gtfs2ntfs', exchange=exchange, routing_key='process.gtfs2ntfs'),
)


# configuration of celery, don't edit
CELERY_TASK_SERIALIZER = 'pickle'
CELERY_RESULT_SERIALIZER = 'pickle'
CELERY_ACCEPT_CONTENT = ['pickle', 'json']

# Automatic update every Monday, Tuesday, Wednesday, Thursday at 8pm
CELERYBEAT_SCHEDULE = {
    'automatic-update': {
        'task': 'tartare.tasks.automatic_update',
        'schedule': timedelta(minutes=1),
        'options': {'expires': 25}
    },
    'jobs-purge': {
        'task': 'tartare.tasks.purge_pending_jobs',
        'schedule': crontab(minute=0, hour=19),
        'options': {'expires': 25}
    }
}

RETRY_DELAY_COVERAGE_EXPORT_TRIGGER = int(os.getenv('RETRY_DELAY_COVERAGE_EXPORT_TRIGGER', '10'))
RETRY_DELAY_UNLOCK_CHORD = int(os.getenv('RETRY_DELAY_UNLOCK_CHORD', '10'))
RETRY_NUMBER_WHEN_FAILED_TASK = int(os.getenv('RETRY_NUMBER_WHEN_FAILED_TASK', '1'))
CELERY_TIMEZONE = 'UTC'

# http://docs.celeryproject.org/en/master/configuration.html#std:setting-CELERYBEAT_SCHEDULE_FILENAME
CELERYBEAT_SCHEDULE_FILENAME = '/tmp/celerybeat-schedule'

CELERYD_HIJACK_ROOT_LOGGER = False

TYR_UPLOAD_TIMEOUT = int(os.getenv('TYR_UPLOAD_TIMEOUT', '10'))

FUSIO_STOP_MAX_ATTEMPT_NUMBER = int(os.getenv('FUSIO_STOP_MAX_ATTEMPT_NUMBER', '100'))
# 10 seconds
FUSIO_WAIT_FIXED = 10*1000

DEFAULT_LICENSE_URL = ''
DEFAULT_LICENSE_NAME = 'Private (unspecified)'

PLATFORM = os.getenv('PLATFORM', 'local')

HISTORICAL = 3

SEND_MAIL_ON_FAILURE = False if os.getenv('SEND_MAIL_ON_FAILURE', 'True') == 'False' else True
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
