# encoding: utf-8

FUSIO_STOP_MAX_ATTEMPT_NUMBER = 3
# 10 seconds
FUSIO_WAIT_FIXED = 1*1000


#celery tasks aren't deferred, they are executed locally by blocking
CELERY_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

HISTORICAL = {
    'gtfs': 3,
    'direction_config': 2
}
